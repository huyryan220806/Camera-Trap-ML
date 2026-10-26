/* Local-only demo. Mock output is never silently substituted for inference. */
const $ = (id) => document.getElementById(id);
let input = null, mode = 'megadetector', result = null, working = false, generation = 0;
const icons = () => window.lucide?.createIcons();
function clearResult() {
  window.clearReviewSession?.();
  result = null; $('boxes').replaceChildren(); $('json').textContent = '{}';
  $('results').innerHTML = '<tr><td colspan="4" class="muted">Chưa có dữ liệu phân tích</td></tr>';
  $('status').textContent = 'Chưa có kết quả.'; $('status').className = '';
  $('timing').textContent = 'Chưa chạy'; $('export').disabled = true;
  $('classifier-state').textContent = $('classifier').value === 'none' ? 'Không dùng' : `${$('classifier').value} · Chưa chạy`;
  $('cache-state').textContent = 'Chưa dùng';
}
function setBusy(value) {
  working = value; $('busy').hidden = !value;
  for (const el of document.querySelectorAll('.controls button,.controls select,.controls input,#reset,#review-panel button,#review-panel select,#review-panel input,#review-panel textarea')) el.disabled = value;
  $('run').disabled = value || !input;
  if (!value && !$('review-panel').hidden) selectReviewBox();
}
function preview(url) {
  $('preview').src = url; $('image-frame').hidden = false; $('empty').hidden = true;
}
function showError(message) { $('status').textContent = message; $('status').className = 'error'; }
function chooseDetection(detectionId) {
  if (!detectionId) return;
  if (window.selectReviewDetection) window.selectReviewDetection(detectionId);
  else {
    for (const row of $('results').querySelectorAll('[data-detection-id]')) row.classList.toggle('selected-row', row.dataset.detectionId === detectionId);
    for (const box of $('boxes').children) box.classList.toggle('selected-box', box.dataset.detectionId === detectionId);
  }
}
function setMode(next) {
  mode = next; clearResult();
  for (const button of document.querySelectorAll('[data-mode]')) {
    const selected = button.dataset.mode === mode;
    button.classList.toggle('selected', selected); button.setAttribute('aria-pressed', String(selected));
  }
  $('mock-settings').hidden = mode !== 'mock';
  $('mode-badge').textContent = mode === 'mock' ? 'GIẢ LẬP · KHÔNG PHẢI SUY LUẬN' : 'MEGADETECTOR · MDv5a.0.1';
  $('mode-badge').classList.toggle('mock', mode === 'mock');
}
async function acceptFile(file) {
  if (!file || working) return;
  const current = ++generation; input = null; clearResult(); $('run').disabled = true;
  $('sample').value = ''; $('file-name').textContent = file.name;
  $('image-frame').hidden = true; $('empty').hidden = false; $('dimensions').textContent = '—';
  if (file.size > 16 * 1024 * 1024) return showError('Ảnh vượt giới hạn 16 MiB.');
  try {
    const data = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsDataURL(file); });
    if (current !== generation) return;
    input = {file_name: file.name, image_base64: data.substring(data.indexOf(',') + 1)};
    preview(data); $('run').disabled = false;
  } catch { showError('Không đọc được file ảnh.'); }
}
function render(data, classification) {
  result = classification || data; $('json').textContent = JSON.stringify(result, null, 2); $('export').disabled = false;
  $('dimensions').textContent = data.image.width ? `${data.image.width} × ${data.image.height}` : '—';
  $('timing').textContent = `${(data.elapsed_ms / 1000).toFixed(2)} s · ${data.pipeline.mode === 'mock' ? 'Giả lập' : 'CPU'}`;
  $('status').className = data.status === 'error' ? 'error'
    : data.status === 'needs_review' ? 'needs-review'
    : data.status === 'no_detection' ? 'no-detection'
    : data.status === 'ok' || data.status === 'detected' ? 'ok' : '';
  const prefix = data.pipeline.mode === 'mock' ? 'KẾT QUẢ GIẢ LẬP. ' : '';
  const text = data.status === 'error' ? data.error.message : data.status === 'no_detection'
    ? 'Chưa phát hiện động vật đạt ngưỡng. Không đồng nghĩa ảnh trống.'
    : classification ? `${data.detections.length} vùng động vật · ${data.pipeline.classifier_id}. ${data.needs_review ? 'Cần kiểm tra lại dự đoán.' : 'Điểm đạt ngưỡng demo; không thay thế xác nhận loài.'}`
    : `${data.detections.length} vùng động vật. Chưa có dự đoán loài; cần kiểm tra.`;
  $('status').textContent = prefix + text;
  const metadata = classification?.provenance.classifier;
  $('classifier-state').textContent = metadata ? `${metadata.classifier_id} · ${metadata.checkpoint_sha256.slice(0, 8)}`
    : classification ? (data.pipeline.mode === 'mock' ? 'Giả lập · Không nạp model' : 'Chưa chạy classifier') : 'Không dùng';
  $('cache-state').textContent = metadata ? `${metadata.cache_hit ? 'Tái sử dụng' : 'Nạp mới'} · ${metadata.model_load_count} lần nạp` : 'Chưa dùng';
  $('results').replaceChildren(); $('boxes').replaceChildren();
  if (!data.detections.length) $('results').innerHTML = '<tr><td colspan="4" class="muted">Không có box được chấp nhận</td></tr>';
  for (const [index, detection] of data.detections.entries()) {
    const row = document.createElement('tr');
    row.dataset.detectionId = detection.detection_id;
    row.tabIndex = 0;
    row.setAttribute('aria-label', `Chọn vùng ${index + 1} để duyệt`);
    row.onclick = () => chooseDetection(detection.detection_id);
    row.onkeydown = (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); chooseDetection(detection.detection_id); } };
    const score = detection.detector_score ?? detection.score;
    const number = document.createElement('td'), numberBadge = document.createElement('span');
    numberBadge.className = 'region-index'; numberBadge.textContent = String(index + 1).padStart(2, '0'); number.append(numberBadge); row.append(number);
    const detector = document.createElement('td'), detectorValue = document.createElement('span');
    detectorValue.className = 'score-value'; detectorValue.textContent = score.toFixed(3); detector.append(detectorValue); row.append(detector);
    const species = document.createElement('td');
    if (detection.top_k) {
      const list = document.createElement('ol'); list.className = 'predictions';
      for (const prediction of detection.top_k) {
        const item = document.createElement('li'), label = document.createElement('span'), value = document.createElement('strong');
        label.textContent = prediction.label.replaceAll('_', ' '); value.textContent = prediction.score.toFixed(3);
        item.append(label, value); list.append(item);
      }
      species.append(list);
    } else species.textContent = 'Chưa phân loại';
    row.append(species);
    const state = document.createElement('td'), stateChip = document.createElement('span');
    const needsReview = !detection.top_k || detection.top_k[0].score < data.pipeline.review_threshold;
    stateChip.className = 'state-chip' + (needsReview ? ' review' : '');
    stateChip.textContent = needsReview ? 'Cần xem' : 'Đạt ngưỡng'; state.append(stateChip);
    row.append(state);
    $('results').append(row);
    const box = document.createElement('div'), [x, y, w, h] = detection.bbox_xywh;
    box.className = 'box' + (data.pipeline.mode === 'mock' ? ' mock' : '');
    box.dataset.detectionId = detection.detection_id;
    box.tabIndex = 0; box.setAttribute('role', 'button'); box.setAttribute('aria-label', `Chọn vùng ${index + 1} để duyệt`);
    box.onclick = () => chooseDetection(detection.detection_id);
    box.onkeydown = (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); chooseDetection(detection.detection_id); } };
    Object.assign(box.style, {left: `${100 * x / data.image.width}%`, top: `${100 * y / data.image.height}%`, width: `${100 * w / data.image.width}%`, height: `${100 * h / data.image.height}%`});
    const label = document.createElement('span'); label.textContent = String(index + 1).padStart(2, '0'); box.append(label); $('boxes').append(box);
  }
}
$('upload').onclick = () => $('file').click();
$('file').onchange = () => acceptFile($('file').files[0]);
$('sample').onchange = () => {
  ++generation; clearResult();
  input = $('sample').value === '' ? null : {sample_id: $('sample').value};
  $('file-name').textContent = input ? $('sample').selectedOptions[0].text : 'Chưa chọn ảnh';
  $('run').disabled = !input; $('dimensions').textContent = '—';
  if (input) preview(`/api/sample/${input.sample_id}`);
  else { $('image-frame').hidden = true; $('empty').hidden = false; }
};
for (const button of document.querySelectorAll('[data-mode]')) button.onclick = () => setMode(button.dataset.mode);
$('threshold').oninput = () => { $('threshold-value').textContent = Number($('threshold').value).toFixed(2); clearResult(); };
$('scenario').onchange = clearResult;
$('classifier').onchange = () => {
  clearResult();
  const id = $('classifier').value;
  $('classification-settings').hidden = id === 'none';
  $('crop-warning').hidden = id === 'none' || id === 'B2';
  $('crop-warning').textContent = `${id} học trên toàn ảnh. Kết quả trên crop chỉ để thử luồng tích hợp.`;
};
$('review-threshold').oninput = () => { $('review-value').textContent = Number($('review-threshold').value).toFixed(2); clearResult(); };
$('show-boxes').onchange = () => { $('boxes').hidden = !$('show-boxes').checked; };
$('reset').onclick = () => {
  ++generation; input = null; clearResult(); $('sample').value = ''; $('file').value = '';
  $('file-name').textContent = 'Chưa chọn ảnh'; $('dimensions').textContent = '—';
  $('image-frame').hidden = true; $('empty').hidden = false; $('empty').querySelector('p').textContent = 'Chưa có ảnh'; $('run').disabled = true;
};
$('run').onclick = async () => {
  if (!input || working) return;
  clearResult(); setBusy(true);
  try {
    const response = await fetch('/api/analyze', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({...input, mode, threshold: Number($('threshold').value), scenario: $('scenario').value,
        classifier: $('classifier').value, review_threshold: Number($('review-threshold').value)})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Không kết nối được máy chủ.');
    if (data.preview) preview(data.preview);
    else { $('image-frame').hidden = true; $('empty').hidden = false; }
    render(data.result, data.classification);
    if (data.review_session) renderReviewSession(data.review_session);
  } catch (error) { showError(error.message); }
  finally { setBusy(false); }
};
$('export').onclick = () => {
  if (!result) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], {type: 'application/json'}));
  const a = document.createElement('a'); a.href = url; a.download = `inference-${result.result?.request_id || result.request_id}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
};
for (const event of ['dragenter', 'dragover']) $('stage').addEventListener(event, (e) => { e.preventDefault(); if (!working) $('stage').classList.add('dragover'); });
for (const event of ['dragleave', 'drop']) $('stage').addEventListener(event, (e) => { e.preventDefault(); $('stage').classList.remove('dragover'); if (event === 'drop') acceptFile(e.dataTransfer.files[0]); });
async function initialize() {
  icons(); setMode('megadetector');
  try {
    const response = await fetch('/api/config'); if (!response.ok) throw new Error();
    const config = await response.json();
    for (const option of $('classifier').options) {
      const entry = config.classifiers?.[option.value];
      if (!entry) continue;
      option.disabled = !(entry.enabled && entry.checkpoint_present);
      option.textContent = `${option.value} · ${entry.enabled ? (entry.checkpoint_present ? 'Checkpoint có sẵn' : 'Thiếu checkpoint') : 'Chưa bàn giao'}`;
    }
    $('runtime').textContent = config.package_version ? `MD ${config.package_version}` : 'Chưa cài đặt';
    window.demoClassNames = config.class_names || [];
    window.configureReviewLabels?.(window.demoClassNames);
    $('classifier').onchange();
    $('server-state').textContent = config.weights_present ? 'Weights có sẵn · Máy chủ sẵn sàng' : 'Chưa có weights · Giả lập sẵn sàng';
    for (const sample of config.samples) { const option = document.createElement('option'); option.value = sample.id; option.textContent = `${sample.name} · ${sample.file_name}`; $('sample').append(option); }
    if (config.samples.length) { $('sample').value = config.samples[0].id; $('sample').onchange(); }
  } catch { $('server-state').textContent = 'Mất kết nối máy chủ'; showError('Không kết nối được máy chủ.'); }
}
initialize();
