"""
MNIST 手写数字识别 —— CNN 训练与测试脚本
------------------------------------------
对比 MLP，CNN 利用卷积核保留图像的二维空间结构，
通过局部感受野和权重共享，用更少参数达到更高准确率。

运行方式:
    python mnist_cnn.py

预期结果:
    10 个 epoch 后测试准确率约 98%-99%，参数量约 2 万（vs MLP 的 11 万）。
"""

import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from data import get_mnist_loaders
from models import CNNClassifier
from utils import accuracy, get_device, save_checkpoint, set_seed


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    """训练一个 epoch，与 MLP 版本完全相同的 5 步循环。"""
    model.train()
    total_loss = 0.0
    total_acc = 0.0
    n_batches = len(loader)

    for images, targets in tqdm(loader, desc="train", leave=False):
        images, targets = images.to(device), targets.to(device)
        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        total_acc += accuracy(logits, targets)

    return total_loss / n_batches, total_acc / n_batches


@torch.no_grad()
def evaluate(
    model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device
) -> tuple[float, float]:
    """评估模型，与 MLP 版本完全相同。"""
    model.eval()
    total_loss = 0.0
    total_acc = 0.0
    n_batches = len(loader)

    for images, targets in loader:
        images, targets = images.to(device), targets.to(device)
        logits = model(images)
        loss = criterion(logits, targets)
        total_loss += loss.item()
        total_acc += accuracy(logits, targets)

    return total_loss / n_batches, total_acc / n_batches


def main() -> None:
    set_seed(42)
    device = get_device()
    print(f"Using device: {device}")

    batch_size = 64
    lr = 1e-3
    epochs = 10

    train_loader, test_loader = get_mnist_loaders(batch_size=batch_size)
    model = CNNClassifier().to(device)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {n_params:,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    print(f"\n{'Epoch':>6}  {'Train Loss':>10}  {'Train Acc':>10}  "
          f"{'Test Loss':>10}  {'Test Acc':>10}")
    print("-" * 55)

    for epoch in range(1, epochs + 1):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        test_loss, test_acc = evaluate(
            model, test_loader, criterion, device
        )
        print(f"{epoch:6d}  {train_loss:10.4f}  {train_acc:10.4f}  "
              f"{test_loss:10.4f}  {test_acc:10.4f}")

    os.makedirs("checkpoints", exist_ok=True)
    save_checkpoint(model, "checkpoints/mnist_cnn.pt")
    print(f"\nCheckpoint saved to checkpoints/mnist_cnn.pt")
    print(f"Final test accuracy: {test_acc * 100:.2f}%")


if __name__ == "__main__":
    main()
