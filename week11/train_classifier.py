"""
统一分类器训练入口
------------------
支持多个数据集和模型类型，通过命令行参数切换。
用于阶段 4 的多数据集对比实验和泛化讨论。

用法:
    python train_classifier.py --dataset mnist --model mlp
    python train_classifier.py --dataset fashion-mnist --model cnn --epochs 15
    python train_classifier.py --dataset cifar10 --model cnn --lr 5e-4

数据集: mnist, fashion-mnist, kmnist, cifar10
模型:   mlp, cnn
"""

import argparse
import os
import torch
import torch.nn as nn
from tqdm import tqdm

from data import get_loaders, DATASET_INFO
from models import MLPClassifier, CNNClassifier
from utils import accuracy, get_device, set_seed


def build_model(model_type: str, dataset_name: str) -> nn.Module:
    """
    根据模型类型和数据集自动选择参数构造模型。

    MNIST / Fashion-MNIST / KMNIST:
        - MLP: input_dim = 784 (28×28 灰度)
        - CNN: in_channels = 1 (灰度单通道)

    CIFAR-10:
        - MLP: input_dim = 2352 (28×28×3 RGB，已 resize)
        - CNN: in_channels = 3 (RGB 三通道)，且第二层卷积翻倍到 64 通道
    """
    info = DATASET_INFO[dataset_name]
    if model_type == "mlp":
        return MLPClassifier(
            input_dim=info["input_dim"],
            num_classes=info["num_classes"],
        )
    elif model_type == "cnn":
        return CNNClassifier(
            in_channels=info["in_channels"],
            num_classes=info["num_classes"],
        )
    else:
        raise ValueError(f"Unknown model: {model_type}")


def train_one_epoch(
    model, loader, criterion, optimizer, device,
) -> tuple[float, float]:
    """训练一个 epoch。与 mnist_mlp.py / mnist_cnn.py 相同的 5 步循环。"""
    model.train()
    total_loss, total_acc = 0.0, 0.0
    n_batches = len(loader)

    for images, targets in tqdm(loader, desc="train", leave=False):
        images, targets = images.to(device), targets.to(device)
        optimizer.zero_grad()            # 1. 清空梯度
        logits = model(images)           # 2. 前向传播
        loss = criterion(logits, targets)  # 3. 计算损失
        loss.backward()                  # 4. 反向传播
        optimizer.step()                 # 5. 参数更新
        total_loss += loss.item()
        total_acc += accuracy(logits, targets)

    return total_loss / n_batches, total_acc / n_batches


@torch.no_grad()
def evaluate(model, loader, criterion, device) -> tuple[float, float]:
    """评估模型。关闭梯度，仅前向传播。"""
    model.eval()
    total_loss, total_acc = 0.0, 0.0
    n_batches = len(loader)

    for images, targets in loader:
        images, targets = images.to(device), targets.to(device)
        logits = model(images)
        loss = criterion(logits, targets)
        total_loss += loss.item()
        total_acc += accuracy(logits, targets)

    return total_loss / n_batches, total_acc / n_batches


def main():
    # ── 命令行参数 ──
    parser = argparse.ArgumentParser(
        description="统一分类器训练入口 — 多数据集多模型对比实验"
    )
    parser.add_argument(
        "--dataset", type=str, default="mnist",
        choices=["mnist", "fashion-mnist", "kmnist", "cifar10"],
        help="数据集名称 (default: mnist)"
    )
    parser.add_argument(
        "--model", type=str, default="mlp",
        choices=["mlp", "cnn"],
        help="模型类型 (default: mlp)"
    )
    parser.add_argument(
        "--epochs", type=int, default=10,
        help="训练轮数 (default: 10)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=64,
        help="批次大小 (default: 64)"
    )
    parser.add_argument(
        "--lr", type=float, default=1e-3,
        help="学习率 (default: 1e-3)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="随机种子 (default: 42)"
    )
    args = parser.parse_args()

    # ── 初始化 ──
    set_seed(args.seed)
    device = get_device()

    # ── 数据 ──
    train_loader, test_loader = get_loaders(
        args.dataset, batch_size=args.batch_size
    )
    info = DATASET_INFO[args.dataset]

    # ── 模型 ──
    model = build_model(args.model, args.dataset).to(device)
    n_params = sum(p.numel() for p in model.parameters())

    # ── 损失 + 优化器 ──
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # ── 头信息 ──
    print(f"Dataset: {args.dataset} | Model: {args.model} | "
          f"Params: {n_params:,} | Device: {device}")
    print(f"Input: {info['in_channels']}ch × 28×28 → "
          f"MLP input_dim={info['input_dim']} | CNN in_channels={info['in_channels']}")
    print(f"\n{'Epoch':>6}  {'Train Loss':>10}  {'Train Acc':>10}  "
          f"{'Test Loss':>10}  {'Test Acc':>10}")
    print("-" * 55)

    # ── 训练循环 ──
    best_test_acc = 0.0
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        test_loss, test_acc = evaluate(
            model, test_loader, criterion, device
        )
        print(f"{epoch:6d}  {train_loss:10.4f}  {train_acc:10.4f}  "
              f"{test_loss:10.4f}  {test_acc:10.4f}")

        if test_acc > best_test_acc:
            best_test_acc = test_acc

    # ── 最终报告 ──
    gap = train_acc - test_acc
    print(f"\n{'='*55}")
    print(f"  Final:  train_acc={train_acc*100:.2f}%  "
          f"test_acc={test_acc*100:.2f}%  "
          f"best_test_acc={best_test_acc*100:.2f}%  "
          f"gap={gap*100:.2f}%")
    print(f"  Dataset: {args.dataset}  Model: {args.model}  Params: {n_params:,}")
    print(f"{'='*55}")

    # ── 保存 ──
    os.makedirs("checkpoints", exist_ok=True)
    filename = f"checkpoints/{args.dataset}_{args.model}.pt"
    torch.save(model.state_dict(), filename)
    print(f"  Saved to {filename}")


if __name__ == "__main__":
    main()
