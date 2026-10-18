"""TV3 - Tuần 3: B2 Crop Classifier Model Architecture.

Backbone mặc định: ResNet-18 (phù hợp với baseline B1 của TV2, cùng ngân sách tính toán).
Có thể tùy chọn ResNet-50 hoặc MobileNetV3 qua cấu hình.
Hỗ trợ:
- Fine-tuning pretrained weights ImageNet
- Thay classification head cho 8 lớp động vật SWG
- Dự đoán xác suất lớp (predict_proba)
- Lưu / khôi phục checkpoint đầy đủ (model, optimizer, epoch, metrics, config)
"""

from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torchvision import models


class B2CropClassifier(nn.Module):
    """Mô hình phân loại động vật trên vùng cắt (crop classifier B2)."""

    # Protocol B2 (W3_PROTOCOL_AGREEMENT_2026-10-18): dùng IMAGENET1K_V1 cho resnet18
    SUPPORTED_BACKBONES = {
        "resnet18": (models.resnet18, models.ResNet18_Weights.IMAGENET1K_V1),
        "resnet50": (models.resnet50, models.ResNet50_Weights.IMAGENET1K_V1),
        "mobilenet_v3_small": (models.mobilenet_v3_small, models.MobileNet_V3_Small_Weights.DEFAULT),
        "mobilenet_v3_large": (models.mobilenet_v3_large, models.MobileNet_V3_Large_Weights.DEFAULT),
    }

    def __init__(
        self,
        num_classes: int = 8,
        backbone_name: str = "resnet18",
        pretrained: bool = True,
        dropout_p: float = 0.0,  # Protocol: không dropout
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.backbone_name = backbone_name.lower()

        if self.backbone_name not in self.SUPPORTED_BACKBONES:
            raise ValueError(
                f"Backbone '{self.backbone_name}' không được hỗ trợ. "
                f"Chọn một trong: {list(self.SUPPORTED_BACKBONES.keys())}"
            )

        model_fn, default_weights = self.SUPPORTED_BACKBONES[self.backbone_name]
        weights = default_weights if pretrained else None
        base_model = model_fn(weights=weights)

        if self.backbone_name.startswith("resnet"):
            in_features = base_model.fc.in_features
            base_model.fc = nn.Identity()
            self.backbone = base_model
            self.classifier = nn.Sequential(
                nn.Dropout(p=dropout_p),
                nn.Linear(in_features, num_classes),
            )
        elif self.backbone_name.startswith("mobilenet"):
            in_features = base_model.classifier[0].in_features
            base_model.classifier = nn.Identity()
            self.backbone = base_model
            self.classifier = nn.Sequential(
                nn.Dropout(p=dropout_p),
                nn.Linear(in_features, num_classes),
            )
        else:
            raise NotImplementedError(f"Chưa hỗ trợ head cho backbone: {self.backbone_name}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Trả về logits chưa qua softmax, shape (batch_size, num_classes)."""
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Trả về xác suất softmax, shape (batch_size, num_classes)."""
        logits = self.forward(x)
        return torch.softmax(logits, dim=-1)


def save_checkpoint(
    model: nn.Module,
    path: str | Path,
    epoch: int,
    optimizer: torch.optim.Optimizer | None = None,
    scheduler: Any | None = None,
    val_metrics: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> None:
    """Lưu checkpoint mô hình kèm siêu tham số và kết quả đánh giá."""
    save_path = Path(path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict() if optimizer else None,
        "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
        "val_metrics": val_metrics or {},
        "config": config or {},
    }
    torch.save(payload, save_path)


def load_checkpoint(
    model: nn.Module,
    path: str | Path,
    optimizer: torch.optim.Optimizer | None = None,
    map_location: str | torch.device = "cpu",
) -> dict[str, Any]:
    """Khôi phục trạng thái mô hình từ checkpoint."""
    checkpoint_path = Path(path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Không tìm thấy checkpoint tại: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location=map_location, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer and checkpoint.get("optimizer_state_dict"):
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint
