/* CSV is a view of saved reviews; the original JSON remains authoritative. */
function batchCsv(items) {
  const columns = ['image_id', 'request_id', 'file_name', 'detection_id', 'bbox_x', 'bbox_y', 'bbox_w', 'bbox_h',
    'mode', 'detector', 'detector_hash', 'model', 'model_hash', 'detector_threshold', 'review_threshold',
    'detector_score', 'top1', 'score1', 'top2', 'score2', 'top3', 'score3', 'status', 'error_stage', 'error',
    'review_label', 'review_decision', 'image_outcome', 'operator', 'revision', 'created_utc', 'note'];
  const cell = value => {
    let text = String(value ?? '');
    // Spreadsheet programs may interpret even quoted cells as formulas.
    if (/^[\s\uFEFF]*[=+@-]/u.test(text) || /^[\t\r\n]/u.test(text)) text = "'" + text;
    return '"' + text.replaceAll('"', '""') + '"';
  };
  const rows = [columns];
  for (const item of items) {
    const session = item.session;
    const original = session?.original;
    const data = original?.result || original;
    const classifier = original?.provenance?.classifier;
    const detector = original?.provenance?.detector || data?.pipeline;
    const review = session?.review;
    for (const detection of data?.detections?.length ? data.detections : [null]) {
      const decision = review?.box_reviews.find(box => box.detection_id === detection?.detection_id);
      const row = {
        image_id: data?.image.image_id || item.id, request_id: session?.request_id, file_name: item.name,
        detection_id: detection?.detection_id, mode: data?.pipeline.mode, detector: detector?.detector_id,
        detector_hash: detector?.weights_sha256, model: data?.pipeline.classifier_id,
        model_hash: classifier?.checkpoint_sha256, detector_threshold: data?.pipeline.detector_threshold,
        review_threshold: data?.pipeline.review_threshold, detector_score: detection?.detector_score ?? detection?.score,
        status: data?.status || item.status, error_stage: data?.error?.stage,
        error: data?.error?.message || item.error, review_label: decision?.label,
        review_decision: decision?.decision, image_outcome: review?.image_outcome,
        operator: review?.operator, revision: review?.revision, created_utc: session?.created_utc, note: review?.note,
      };
      ['x', 'y', 'w', 'h'].forEach((axis, index) => { row['bbox_' + axis] = detection?.bbox_xywh[index]; });
      for (let index = 0; index < 3; index++) {
        row['top' + (index + 1)] = detection?.top_k?.[index]?.label;
        row['score' + (index + 1)] = detection?.top_k?.[index]?.score;
      }
      rows.push(columns.map(column => row[column]));
    }
  }
  return '\uFEFF' + rows.map(row => row.map(cell).join(',')).join('\r\n') + '\r\n';
}
if (typeof module !== 'undefined') module.exports = {batchCsv};

if (typeof document !== 'undefined') {
  let batchItems = [], batchActive = null, batchRunning = false, batchExporting = false, batchStop = false;
  window.isBatchLocked = () => batchRunning || batchExporting;
  window.detachBatchView = () => { rememberBatchView(); batchActive = null; drawBatchQueue(); };
  const statusNames = {pending: 'Chờ', running: 'Đang chạy', ok: 'Đạt ngưỡng', needs_review: 'Cần kiểm tra',
    no_detection: 'Không phát hiện', detected: 'Chỉ detector', error: 'Lỗi', request_error: 'Lỗi yêu cầu'};

  function rememberBatchView() {
    if (!batchActive) return;
    batchActive.view = {result, session: reviewSession, draft: structuredClone(reviewDraft),
      reviewer: $('reviewer').value, note: $('review-note').value, outcome: $('image-outcome').value,
      box: $('review-box').value, only: $('review-only').checked, status: $('review-status').textContent,
      statusClass: $('review-status').className, preview: $('image-frame').hidden ? null : $('preview').getAttribute('src'), input};
  }

  function drawBatchQueue() {
    $('batch-queue').replaceChildren();
    for (const item of batchItems) {
      const li = document.createElement('li'), button = document.createElement('button');
      button.type = 'button'; button.textContent = `${item.name} · ${statusNames[item.status] || item.status}`;
      button.setAttribute('aria-current', String(item === batchActive));
      button.disabled = batchRunning || batchExporting || working || !item.view;
      button.onclick = () => openBatchItem(item);
      li.append(button); $('batch-queue').append(li);
    }
  }

  function syncBatchControls() {
    $('batch-run').disabled = working || batchRunning || batchExporting || !batchItems.some(item => item.status === 'pending');
    $('batch-stop').disabled = !batchRunning || batchStop;
    $('batch-files').disabled = working || batchRunning || batchExporting;
    const empty = !batchItems.some(item => item.session || item.status === 'request_error');
    $('batch-csv').disabled = working || batchRunning || batchExporting || empty;
    $('batch-json').disabled = $('batch-csv').disabled;
    if (batchRunning || batchExporting) {
      for (const el of document.querySelectorAll('.controls button,.controls select,.controls input,#reset,#review-panel button,#review-panel select,#review-panel input,#review-panel textarea,#export')) el.disabled = true;
      $('batch-stop').disabled = !batchRunning || batchStop;
    }
    drawBatchQueue();
  }
  window.syncBatchControls = syncBatchControls;

  function openBatchItem(item) {
    if (working || batchRunning || batchExporting || !item.view) return;
    rememberBatchView(); batchActive = item;
    const view = item.view;
    clearResult(); input = view.input;
    $('file-name').textContent = item.name; $('sample').value = '';
    if (view.preview) preview(view.preview);
    else { $('image-frame').hidden = true; $('empty').hidden = false; }
    if (view.session) {
      const original = view.session.original;
      const data = original.result || original;
      setMode(data.pipeline.mode === 'mock' ? 'mock' : 'megadetector');
      $('classifier').value = original.provenance?.requested_classifier || 'none';
      $('classification-settings').hidden = $('classifier').value === 'none';
      $('crop-warning').hidden = !['B0', 'B1'].includes($('classifier').value);
      $('threshold').value = data.pipeline.detector_threshold;
      $('threshold-value').textContent = Number($('threshold').value).toFixed(2);
      if (data.pipeline.review_threshold !== undefined) {
        $('review-threshold').value = data.pipeline.review_threshold;
        $('review-value').textContent = Number($('review-threshold').value).toFixed(2);
      }
      render(original.result || original, original.result ? original : null);
      renderReviewSession(view.session);
      reviewDraft = structuredClone(view.draft);
      $('reviewer').value = view.reviewer; $('review-note').value = view.note;
      $('image-outcome').value = view.outcome; $('review-only').checked = view.only;
      populateReviewBoxes(); $('review-box').value = view.box; selectReviewBox();
      setReviewStatus(view.status, view.statusClass);
    } else showError(item.error);
    $('run').disabled = !input;
    syncBatchControls();
  }

  // Capture the selected batch item's draft before an ordinary single-image action.
  for (const id of ['upload', 'file', 'sample', 'reset', 'threshold', 'scenario', 'classifier', 'review-threshold']) {
    $(id).addEventListener(id === 'threshold' || id === 'review-threshold' ? 'input' : id === 'upload' || id === 'reset' ? 'click' : 'change', () => {
      if (!batchRunning) { rememberBatchView(); batchActive = null; drawBatchQueue(); }
    }, true);
  }
  for (const button of document.querySelectorAll('[data-mode]')) button.addEventListener('click', () => {
    if (!batchRunning) window.detachBatchView();
  }, true);

  $('batch-files').onchange = () => {
    const files = Array.from($('batch-files').files);
    if (files.length > 10) {
      $('batch-status').textContent = 'Tối đa 10 ảnh/lô. Hãy chọn lại; lô hiện có được giữ nguyên.';
      $('batch-files').value = ''; return;
    }
    if (batchItems.length && !window.confirm('Thay danh sách lô trong tab này? Hãy tải JSON/CSV trước nếu cần giữ kết quả. Phiên đã lưu trên máy chủ vẫn được giữ.')) {
      $('batch-files').value = ''; return;
    }
    rememberBatchView(); batchActive = null;
    batchItems = files.map(file => ({id: crypto.randomUUID(), file, name: file.name, status: 'pending', session: null, view: null}));
    $('batch-status').textContent = `${files.length}/10 ảnh · xử lý tuần tự; tối đa 24 MP/ảnh.`;
    syncBatchControls();
  };
  $('batch-stop').onclick = () => { batchStop = true; $('batch-status').textContent = 'Sẽ dừng sau ảnh hiện tại. Các ảnh chờ có thể chạy tiếp.'; syncBatchControls(); };

  $('batch-run').onclick = async () => {
    if (working || batchRunning || batchExporting) return;
    rememberBatchView(); ++generation; batchRunning = true; batchStop = false;
    const options = {mode, threshold: Number($('threshold').value), scenario: $('scenario').value,
      classifier: $('classifier').value, review_threshold: Number($('review-threshold').value)};
    syncBatchControls();
    try {
      for (const item of batchItems.filter(entry => entry.status === 'pending')) {
        if (batchStop) break;
        batchActive = item; item.status = 'running';
        $('batch-status').textContent = `Đang xử lý ${item.name}`;
        clearResult(); input = null; $('file-name').textContent = item.name; $('sample').value = '';
        $('image-frame').hidden = true; $('empty').hidden = false; $('dimensions').textContent = '—';
        setBusy(true);
        try {
          if (item.file.size > 16 * 1024 * 1024) throw new Error('Ảnh vượt giới hạn 16 MiB.');
          const dataUrl = await new Promise((resolve, reject) => {
            const reader = new FileReader(); reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(new Error('Không đọc được file ảnh.')); reader.readAsDataURL(item.file);
          });
          const response = await fetch('/api/analyze', {method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({...options, file_name: item.name, image_base64: dataUrl.slice(dataUrl.indexOf(',') + 1)})});
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
          if (!data.review_session) throw new Error('Máy chủ không trả phiên duyệt.');
          if (data.preview) preview(data.preview);
          render(data.result, data.classification); renderReviewSession(data.review_session);
          item.session = data.review_session; item.status = data.result.status;
        } catch (error) {
          item.status = 'request_error'; item.error = error.message; showError(error.message);
        } finally {
          rememberBatchView(); setBusy(false);
        }
      }
    } finally {
      batchRunning = false; setBusy(false);
      const waiting = batchItems.filter(item => item.status === 'pending').length;
      $('batch-status').textContent = `${batchItems.length - waiting}/${batchItems.length} ảnh đã xử lý · ${waiting} chờ. Bản nháp giữ riêng từng ảnh; xuất dùng phiên đã lưu.`;
      syncBatchControls();
    }
  };

  async function exportBatch(csv) {
    if (working || batchRunning || batchExporting) return;
    rememberBatchView(); batchExporting = true; syncBatchControls();
    try {
      const saved = [];
      for (const item of batchItems) {
        if (item.session) {
          const response = await fetch(`/api/review/${item.session.request_id}`);
          if (!response.ok) throw new Error(`Không đọc được bản đã lưu của ${item.name}; hãy thử lại.`);
          const session = await response.json();
          saved.push({id: item.id, name: item.name, status: item.status, session});
        } else saved.push({id: item.id, name: item.name, status: item.status, error: item.error || ''});
      }
      const body = csv ? batchCsv(saved) : JSON.stringify({schema_version: 'batch-demo-1.0',
        exported_utc: new Date().toISOString(), review_source: 'server_saved', items: saved}, null, 2);
      const url = URL.createObjectURL(new Blob([body], {type: csv ? 'text/csv;charset=utf-8' : 'application/json'}));
      const link = document.createElement('a'); link.href = url; link.download = `camera-trap-batch.${csv ? 'csv' : 'json'}`;
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      $('batch-status').textContent = 'Đã xuất phiên đã lưu. Thay đổi chưa lưu trong form không nằm trong tệp xuất.';
    } catch (error) { $('batch-status').textContent = error.message; }
    finally { batchExporting = false; setBusy(false); }
  }
  $('batch-csv').onclick = () => exportBatch(true);
  $('batch-json').onclick = () => exportBatch(false);
  syncBatchControls();
}
