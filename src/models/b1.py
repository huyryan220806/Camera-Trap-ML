"""ResNet18 full fine-tuning, initialized independently of B0."""

from torch import nn
from torchvision.models import ResNet18_Weights, resnet18


def build_b1(num_classes: int, *, pretrained: bool = True) -> nn.Module:
    if type(num_classes) is not int or num_classes < 2:
        raise ValueError("B1 requires at least two classes")
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1 if pretrained else None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    for parameter in model.parameters():
        parameter.requires_grad_(True)
    return model
