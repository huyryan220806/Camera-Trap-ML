#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
CameraTrapML – Kiểm tra Môi trường & GPU
==============================================================================
Mã công việc : W1-02  (Tuần 1 – TV2)
Mô tả        : Script tự động kiểm tra phiên bản Python, PyTorch, Torchvision,
                CUDA, tính khả dụng của GPU và chạy thử phép tính trên GPU.
                Kết quả được in ra màn hình và ghi vào file `gpu_env_report.txt`.
Cách chạy     : python check_environment.py
==============================================================================
"""

import sys
import platform
import datetime
import io
from pathlib import Path

# ---------------------------------------------------------------------------
# Hằng số
# ---------------------------------------------------------------------------
REPORT_FILE = Path(__file__).resolve().parent / "gpu_env_report.txt"
MATRIX_SIZE = 2048  # Kích thước ma trận dùng để benchmark GPU
SEPARATOR = "=" * 72


# ---------------------------------------------------------------------------
# Tiện ích ghi log đồng thời ra console và buffer
# ---------------------------------------------------------------------------
class DualLogger:
    """Ghi đồng thời ra stdout và một StringIO buffer."""

    def __init__(self):
        self._buffer = io.StringIO()

    def log(self, msg: str = "") -> None:
        """In một dòng ra console và lưu vào buffer."""
        print(msg)
        self._buffer.write(msg + "\n")

    def get_text(self) -> str:
        return self._buffer.getvalue()


# ---------------------------------------------------------------------------
# Các hàm kiểm tra
# ---------------------------------------------------------------------------
def check_python(logger: DualLogger) -> None:
    """Kiểm tra phiên bản Python và hệ điều hành."""
    logger.log(SEPARATOR)
    logger.log("1. THÔNG TIN PYTHON & HỆ ĐIỀU HÀNH")
    logger.log(SEPARATOR)
    logger.log(f"  Python version  : {sys.version}")
    logger.log(f"  Platform        : {platform.platform()}")
    logger.log(f"  Architecture    : {platform.machine()}")
    logger.log()


def check_pytorch(logger: DualLogger) -> bool:
    """Kiểm tra PyTorch, Torchvision và CUDA runtime.

    Returns:
        True nếu import thành công, False nếu thiếu thư viện.
    """
    logger.log(SEPARATOR)
    logger.log("2. PYTORCH & CUDA")
    logger.log(SEPARATOR)

    try:
        import torch
    except ImportError:
        logger.log("  [LỖI] Không tìm thấy PyTorch. Hãy cài đặt: pip install torch")
        return False

    logger.log(f"  PyTorch version : {torch.__version__}")

    # Torchvision (không bắt buộc để kiểm tra GPU nhưng cần cho dự án)
    try:
        import torchvision
        logger.log(f"  Torchvision ver : {torchvision.__version__}")
    except ImportError:
        logger.log("  [CẢNH BÁO] Torchvision chưa được cài đặt.")

    # CUDA runtime
    logger.log(f"  CUDA available  : {torch.cuda.is_available()}")
    logger.log(f"  CUDA version    : {torch.version.cuda or 'N/A'}")
    logger.log(f"  cuDNN version   : {torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else 'N/A'}")
    logger.log(f"  cuDNN enabled   : {torch.backends.cudnn.enabled}")
    logger.log()
    return True


def check_gpu_details(logger: DualLogger) -> bool:
    """In thông tin chi tiết từng GPU và kiểm tra VRAM.

    Returns:
        True nếu có ít nhất 1 GPU khả dụng.
    """
    import torch

    logger.log(SEPARATOR)
    logger.log("3. THÔNG TIN GPU")
    logger.log(SEPARATOR)

    if not torch.cuda.is_available():
        logger.log("  [CẢNH BÁO] Không phát hiện GPU CUDA nào. Sẽ chạy trên CPU.")
        logger.log()
        return False

    num_gpus = torch.cuda.device_count()
    logger.log(f"  Số GPU phát hiện: {num_gpus}")

    for i in range(num_gpus):
        props = torch.cuda.get_device_properties(i)
        vram_total_gb = props.total_mem / (1024 ** 3)
        vram_free_mb = torch.cuda.mem_get_info(i)[0] / (1024 ** 2)
        vram_total_mb = torch.cuda.mem_get_info(i)[1] / (1024 ** 2)
        logger.log(f"\n  --- GPU {i} ---")
        logger.log(f"  Tên             : {props.name}")
        logger.log(f"  Compute Cap.    : {props.major}.{props.minor}")
        logger.log(f"  VRAM tổng       : {vram_total_gb:.2f} GB")
        logger.log(f"  VRAM khả dụng   : {vram_free_mb:.0f} MB / {vram_total_mb:.0f} MB")
        logger.log(f"  Số SM           : {props.multi_processor_count}")

    logger.log()
    return True


def run_gpu_smoke_test(logger: DualLogger) -> None:
    """Tạo tensor dummy, đẩy lên GPU và chạy phép nhân ma trận.

    Mục đích: đảm bảo pipeline CUDA → cuDNN hoạt động trơn tru.
    """
    import torch

    logger.log(SEPARATOR)
    logger.log("4. SMOKE TEST – PHÉP TÍNH TRÊN GPU")
    logger.log(SEPARATOR)

    if not torch.cuda.is_available():
        logger.log("  Bỏ qua (không có GPU).")
        logger.log()
        return

    device = torch.device("cuda:0")
    logger.log(f"  Device sử dụng  : {device}")
    logger.log(f"  Kích thước ma trận : {MATRIX_SIZE} x {MATRIX_SIZE}")

    try:
        # Tạo hai ma trận ngẫu nhiên trên GPU
        a = torch.randn(MATRIX_SIZE, MATRIX_SIZE, device=device)
        b = torch.randn(MATRIX_SIZE, MATRIX_SIZE, device=device)

        # Đồng bộ trước khi đo thời gian
        torch.cuda.synchronize()
        start = datetime.datetime.now()

        # Phép nhân ma trận (dùng cuBLAS bên dưới)
        c = torch.mm(a, b)

        torch.cuda.synchronize()
        elapsed = (datetime.datetime.now() - start).total_seconds()

        logger.log(f"  Kết quả shape   : {c.shape}")
        logger.log(f"  Giá trị mẫu    : c[0,0] = {c[0, 0].item():.6f}")
        logger.log(f"  Thời gian       : {elapsed:.4f} s")
        logger.log("  [OK] GPU Smoke Test THÀNH CÔNG ✓")

        # Giải phóng bộ nhớ
        del a, b, c
        torch.cuda.empty_cache()

    except Exception as exc:
        logger.log(f"  [LỖI] GPU Smoke Test THẤT BẠI: {exc}")

    logger.log()


def check_optional_packages(logger: DualLogger) -> None:
    """Kiểm tra nhanh các thư viện phụ trợ quan trọng."""
    logger.log(SEPARATOR)
    logger.log("5. THƯ VIỆN PHỤ TRỢ")
    logger.log(SEPARATOR)

    packages = [
        "numpy", "pandas", "sklearn", "matplotlib",
        "seaborn", "tqdm", "PIL", "yaml",
    ]

    for pkg_name in packages:
        try:
            mod = __import__(pkg_name)
            ver = getattr(mod, "__version__", "installed")
            logger.log(f"  {pkg_name:<16s} : {ver}")
        except ImportError:
            logger.log(f"  {pkg_name:<16s} : [CHƯA CÀI]")

    logger.log()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    logger = DualLogger()

    logger.log()
    logger.log(SEPARATOR)
    logger.log("  CameraTrapML – BÁO CÁO MÔI TRƯỜNG & GPU")
    logger.log(f"  Thời gian : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log(SEPARATOR)
    logger.log()

    # 1. Python & OS
    check_python(logger)

    # 2. PyTorch & CUDA
    pytorch_ok = check_pytorch(logger)

    if pytorch_ok:
        # 3. GPU details
        check_gpu_details(logger)

        # 4. Smoke test
        run_gpu_smoke_test(logger)

    # 5. Thư viện phụ trợ
    check_optional_packages(logger)

    # --- Tổng kết ---
    logger.log(SEPARATOR)
    logger.log("KẾT LUẬN")
    logger.log(SEPARATOR)
    if pytorch_ok:
        import torch
        if torch.cuda.is_available():
            logger.log("  ✓ Môi trường SẴN SÀNG cho huấn luyện trên GPU.")
        else:
            logger.log("  ⚠ PyTorch hoạt động nhưng KHÔNG có GPU. Chỉ chạy được trên CPU.")
    else:
        logger.log("  ✗ Thiếu PyTorch. Vui lòng cài đặt trước khi tiếp tục.")
    logger.log()

    # --- Ghi file report ---
    REPORT_FILE.write_text(logger.get_text(), encoding="utf-8")
    print(f"[INFO] Báo cáo đã được ghi vào: {REPORT_FILE}")


if __name__ == "__main__":
    main()
