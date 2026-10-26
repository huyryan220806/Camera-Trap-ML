/* Human decisions never replace the immutable inference result. */
let reviewSession = null, reviewDraft = [], reviewNames = [];
function setReviewStatus(message, state = '') {
  $('review-status').textContent = message;
  $('review-status').className = state;
}
function clearReviewSession() {
  reviewSession = null; reviewDraft = [];
  $('review-panel').hidden = true;
  setReviewStatus('');
}
function configureReviewLabels(names) {
  reviewNames = names;
  while ($('review-label').options.length > 3) $('review-label').remove(3);
  for (const name of names) {
    const option = document.createElement('option'); option.value = name;
    option.textContent = name.replaceAll('_', ' '); $('review-label').append(option);
  }
}
function reviewResult() { return reviewSession.original.result || reviewSession.original; }
function selectReviewBox() {
  const box = reviewDraft.find(b => b.detection_id === $('review-box').value);
  $('review-label').disabled = !box;
  $('review-label').value = box ? box.label || (box.decision === 'pending' ? '' : box.decision) : '';
  for (const el of $('boxes').children) el.classList.toggle('selected-box', el.dataset.detectionId === box?.detection_id);
  for (const row of $('results').querySelectorAll('[data-detection-id]')) row.classList.toggle('selected-row', row.dataset.detectionId === box?.detection_id);
}
function selectReviewDetection(detectionId) {
  if (!reviewSession) return;
  let option = Array.from($('review-box').options).find(item => item.value === detectionId);
  if (!option && $('review-only').checked) {
    $('review-only').checked = false;
    populateReviewBoxes();
    option = Array.from($('review-box').options).find(item => item.value === detectionId);
  }
  if (!option) return;
  $('review-box').value = detectionId;
  selectReviewBox();
  $('review-label').focus({preventScroll: true});
}
window.selectReviewDetection = selectReviewDetection;
function populateReviewBoxes() {
  const old = $('review-box').value;
  $('review-box').replaceChildren();
  const data = reviewResult();
  data.detections.forEach((d, i) => {
    const low = !d.top_k || d.top_k[0].score < data.pipeline.review_threshold;
    if ($('review-only').checked && !low) return;
    const option = document.createElement('option'); option.value = d.detection_id;
    option.textContent = `${String(i + 1).padStart(2, '0')} · ${low ? 'Cần kiểm tra' : 'Đạt ngưỡng điểm'}`;
    $('review-box').append(option);
  });
  if (!$('review-box').options.length) {
    const option = document.createElement('option'); option.value = ''; option.textContent = 'Không có vùng'; $('review-box').append(option);
  } else if (Array.from($('review-box').options).some(o => o.value === old)) $('review-box').value = old;
  selectReviewBox();
}
function renderReviewSession(session) {
  reviewSession = session; reviewDraft = structuredClone(session.review.box_reviews);
  result = session; $('json').textContent = JSON.stringify(session, null, 2);
  $('review-panel').hidden = false;
  $('reviewer').value = session.review.operator || localStorage.getItem('camera-trap-reviewer') || '';
  $('review-note').value = session.review.note;
  $('image-outcome').value = session.review.image_outcome;
  $('review-revision').textContent = `Bản ${session.review.revision}`;
  setReviewStatus(session.review.revision ? 'Đã lưu trên máy' : 'Chưa lưu bản duyệt', session.review.revision ? 'saved' : '');
  const rt = session.runtime;
  $('review-runtime').textContent = `${rt.cpu || 'CPU'} · RAM ${rt.ram_gib ?? '—'} GiB · ${rt.torch_threads ?? '—'} threads · Lô ảnh ${rt.image_batch_size}, detector ${rt.detector_batch_size}, crop tối đa ${rt.classifier_max_crop_batch_size}`;
  populateReviewBoxes();
}
$('review-box').onchange = selectReviewBox;
$('review-only').onchange = populateReviewBoxes;
$('review-label').onchange = () => {
  const box = reviewDraft.find(b => b.detection_id === $('review-box').value);
  if (!box) return;
  const value = $('review-label').value;
  const original = reviewResult().detections.find(d => d.detection_id === box.detection_id);
  box.label = reviewNames.includes(value) ? value : null;
  box.decision = box.label ? (original.top_k?.[0]?.label === value ? 'confirmed' : 'corrected') : value || 'pending';
  setReviewStatus('Có thay đổi chưa lưu', 'dirty');
};
for (const id of ['reviewer', 'review-note', 'image-outcome']) $(id).addEventListener('input', () => setReviewStatus('Có thay đổi chưa lưu', 'dirty'));
async function updateReview(save) {
  if (!reviewSession || working) return;
  const requestId = reviewSession.request_id;
  setBusy(true);
  try {
    const response = await fetch(save ? '/api/review' : `/api/review/${requestId}`, save ? {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({request_id: requestId, revision: reviewSession.review.revision,
        operator: $('reviewer').value, note: $('review-note').value,
        image_outcome: $('image-outcome').value, box_reviews: reviewDraft})
    } : {});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Không lưu được bản duyệt.');
    if (reviewSession?.request_id !== requestId) return;
    localStorage.setItem('camera-trap-reviewer', data.review.operator);
    renderReviewSession(data);
  } catch (error) { setReviewStatus(error.message, 'error'); }
  finally { setBusy(false); if (reviewSession) selectReviewBox(); }
}
$('save-review').onclick = () => updateReview(true);
$('reload-review').onclick = () => updateReview(false);
if (window.demoClassNames) configureReviewLabels(window.demoClassNames);
