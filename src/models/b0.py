"""Frozen ImageNet ResNet18 with only its last linear layer trainable."""

from torch import nn
from torchvision.models import ResNet18_Weights, resnet18


def build_b0(num_classes: int, *, pretrained: bool = True) -> nn.Module:
    if num_classes < 2:
        raise ValueError("B0 requires at least two classes")
    model = resnet18(weights=ResNet18_Weights.DEFAULT if pretrained else None)
    in_features = model.fc.in_features
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.fc = nn.Linear(in_features, num_classes)
    trainable = {name for name, parameter in model.named_parameters() if parameter.requires_grad}
    if trainable != {"fc.weight", "fc.bias"}:
        raise RuntimeError(f"Unexpected trainable parameters: {sorted(trainable)}")
    return model


def parameter_counts(model: nn.Module) -> dict[str, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total": total, "trainable": trainable, "frozen": total - trainable}
