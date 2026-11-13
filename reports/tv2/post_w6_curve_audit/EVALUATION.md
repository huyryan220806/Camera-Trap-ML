# Bàn giao phép đo checkpoint cố định cho TV3

Mục tiêu là đo cùng checkpoint `R6_attempt01/best_model.pt` epoch 13, seed 43 trên toàn bộ **Train 4.246 ảnh / 4.729 GT crop** và **Validation 600 ảnh / 680 GT crop**. Hai tập dùng cùng pipeline của R6 với `eval()`, `inference_mode()`, FP32 deterministic, AMP và TF32 tắt, không augmentation, crop batch 8. CE là mean crop CE trong từng ảnh rồi mean qua ảnh. Accuracy, macro-F1, macro-precision và macro-recall dùng dự đoán ảnh cha từ argmax của mean vector softmax. Đây là một phép đo chỉ suy luận theo lịch GPU, dùng checkpoint, manifest và class map đã khóa.

Chuẩn bị gói TV3 gốc đã giải nén, vendor DINOv3 đúng commit và data root có `data/processed/comparison_v1`, `data/processed/train_expansion_w6_v1` và các ảnh Train/Validation ở đúng đường dẫn manifest. Có thể dùng bản sao chỉ chứa các đầu vào Train/Validation. Chạy từ checkout TV2 có frozen config, với môi trường đã pin của replay (Python 3.12.10, PyTorch 2.6.0+cu124, torchvision 0.21.0+cu124, Pillow 12.2.0, NumPy 2.5.3, scikit-learn 1.9.0, CUDA 12.4, cuDNN 90100, RTX 4060 Laptop GPU).

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$pythonR6 = 'outputs/tv2_w6/independent_replay_20261106/.venv/Scripts/python.exe'
$packageR6 = 'outputs/tv2_w6/r6_replay_20261110/received'
$dataR6 = 'outputs/tv2_w6/post_w6_curve_audit_20261113/data_root'
$vendorR6 = 'outputs/tv2_w6/independent_replay_20261106/vendor/dinov3'
$stampR6 = Get-Date -Format 'yyyyMMdd-HHmmss'
$evalR6 = 'reports/tv2/post_w6_curve_audit/evaluate_checkpoint.py'

& $pythonR6 $evalR6 --package $packageR6 --data-root $dataR6 --vendor $vendorR6 `
  --output "outputs/tv2_w6/r6_fixed_eval/${stampR6}_preflight" --check-only

# Sau khi xác nhận lịch, điền mã booking, thiết bị và khung giờ thực tế.
$bookingR6 = '<booking ID, device, confirmed time window and timezone>'
& $pythonR6 $evalR6 --package $packageR6 --data-root $dataR6 --vendor $vendorR6 `
  --output "outputs/tv2_w6/r6_fixed_eval/${stampR6}_gpu" --booking $bookingR6
```

- Preflight kiểm SHA-256 của checkpoint, config, mã, manifest, byte ảnh và RGB decode. Nó xuất `input_preflight.json` với count và hash thứ tự ID. Giữ đường dẫn output riêng cho mỗi lượt.
- Lượt GPU chạy hai split trong cùng process, kiểm trạng thái model trước/sau và ghi `checkpoint_eval.json`, `train_predictions.json`, `val_predictions.json`. JSON tổng hợp có thời điểm, runtime, hash đầu vào và dự đoán, thời gian từng split và GPU-giờ của session đo từ trước load model tới sau forward/đối chiếu state. Đồng bộ CUDA tại các mốc đo; kiểm dữ liệu CPU diễn ra trước session. Ghi thời gian thực vào hồ sơ GPU của lượt đánh giá mới và giữ riêng lịch sử attempt.
- Gửi JSON tổng hợp và hai file dự đoán để TV2 đối chiếu. Nếu `val_exact_vs_tv3=false`, giữ evidence để điều tra đầu vào, môi trường và batch; áp dụng chính sách exact đã khóa. Nếu chỉ đủ thời gian chạy tập con Train, tạo phép đo riêng với ID đã khóa, SHA danh sách, count thực tế và nhãn `TRAIN_SUBSET_EVAL`; script hiện tại yêu cầu đủ hai tập.
