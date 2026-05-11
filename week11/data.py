"""
数据加载模块
-----------
封装数据集的下载、预处理和批量化加载。
- get_mnist_loaders(): 仅 MNIST（保持向后兼容）
- get_loaders():       统一入口，支持 MNIST / Fashion-MNIST / KMNIST / CIFAR-10
"""

import os
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# ── 数据集元信息 ──
# 记录每个数据集的输入形状，供 models.py 自动选择参数
DATASET_INFO = {
    "mnist":         {"in_channels": 1, "input_dim": 784,  "num_classes": 10},
    "fashion-mnist": {"in_channels": 1, "input_dim": 784,  "num_classes": 10},
    "kmnist":        {"in_channels": 1, "input_dim": 784,  "num_classes": 10},
    "cifar10":       {"in_channels": 3, "input_dim": 2352, "num_classes": 10},
    # CIFAR-10 原始 32×32×3，resize 到 28×28 后: 28×28×3 = 2352
}


def get_mnist_loaders(
    root: str = "datasets",
    batch_size: int = 64,
    num_workers: int = 0,
) -> tuple[DataLoader, DataLoader]:
    """
    构造 MNIST 数据集的训练和测试 DataLoader（保持向后兼容）。

    MNIST 数据集:
        - 70,000 张 28×28 灰度手写数字图片
        - 训练集 60,000 张，测试集 10,000 张
        - 标签为 0-9 共 10 个类别
        - 每张图片只有一个通道（灰度），像素值原始范围 [0, 255]

    DataLoader 的作用:
        - 将数据集分成若干 batch（批次），每次喂给模型一个 batch
        - 训练集 shuffle=True：每轮打乱顺序，防止模型记住数据顺序
        - 测试集 shuffle=False：保持顺序，确保每次评估结果可比较

    参数:
        root: 数据集存储目录，首次使用会自动下载
        batch_size: 每批样本数，64 是常用选择
                    - 太小：训练不稳定，GPU 利用率低
                    - 太大：可能超出显存，梯度更新不够频繁
        num_workers: 数据加载的并行进程数，0 表示主进程加载

    返回:
        (train_loader, test_loader): 训练集和测试集的 DataLoader
    """
    # transforms.ToTensor() 做了两件事：
    # 1. 将 PIL Image (H×W) 或 numpy 数组转为 PyTorch 张量 (C×H×W)
    # 2. 将像素值从 [0, 255] 归一化到 [0.0, 1.0]
    #    归一化让数值落在较小范围，有助于梯度下降的数值稳定性
    transform = transforms.ToTensor()

    # 加载训练集：train=True 表示取前 60,000 张
    train_data = datasets.MNIST(
        root=root, train=True, download=True, transform=transform
    )
    # 加载测试集：train=False 表示取后 10,000 张
    test_data = datasets.MNIST(
        root=root, train=False, download=True, transform=transform
    )

    # 构造 DataLoader
    # 训练集需要 shuffle：每次 epoch 随机打乱，让模型看到不同的 batch 组合
    train_loader = DataLoader(
        train_data, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    # 测试集不 shuffle：评估不需要打乱，保证每次结果一致
    test_loader = DataLoader(
        test_data, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )

    return train_loader, test_loader


def get_loaders(
    dataset_name: str,
    root: str = "datasets",
    batch_size: int = 64,
    num_workers: int = 0,
) -> tuple[DataLoader, DataLoader]:
    """
    统一数据加载入口，支持四个数据集。

    支持的 dataset_name:
        - "mnist":          MNIST 手写数字           (28×28, 1 通道灰度)
        - "fashion-mnist":  Fashion-MNIST 服饰       (28×28, 1 通道灰度)
        - "kmnist":         Kuzushiji-MNIST 日文假名 (28×28, 1 通道灰度)
        - "cifar10":        CIFAR-10 自然图像        (32×32→resize→28×28, 3 通道 RGB)

    对于 CIFAR-10:
        - 原始尺寸 32×32，Resize 到 28×28（与其他数据集统一尺寸）
        - 保留 3 通道 RGB（转为灰度会丢失颜色信息）
        - 因此 MLP 输入维度为 28×28×3 = 2352，而非 784
        - CNN 输入通道数为 3 而非 1

    参数:
        dataset_name: 数据集名称，见上方列表
        root:         数据集根目录
        batch_size:   每批样本数
        num_workers:  并行加载进程数

    返回:
        (train_loader, test_loader): 训练集和测试集的 DataLoader
    """
    dataset_name = dataset_name.lower()

    # ── 选取数据集类 ──
    dataset_map = {
        "mnist": datasets.MNIST,
        "fashion-mnist": datasets.FashionMNIST,
        "kmnist": datasets.KMNIST,
        "cifar10": datasets.CIFAR10,
    }
    if dataset_name not in dataset_map:
        raise ValueError(
            f"Unknown dataset: {dataset_name}. "
            f"Choose from: {list(dataset_map.keys())}"
        )

    # ── 预处理 ──
    # CIFAR-10 需要额外 Resize（32×32 → 28×28），其他数据集仅 ToTensor
    if dataset_name == "cifar10":
        # CIFAR-10 是 32×32 RGB 自然图像（飞机/汽车/鸟/猫等）
        # Resize 到 28×28 与 MNIST 系列统一尺寸，保留 3 通道
        transform = transforms.Compose([
            transforms.Resize((28, 28)),
            transforms.ToTensor(),
        ])
    else:
        # MNIST / Fashion-MNIST / KMNIST 已是 28×28 灰度图
        transform = transforms.ToTensor()

    # ── 加载 ──
    dataset_cls = dataset_map[dataset_name]

    # 检查原始数据是否已存在（避免已缓存时仍尝试下载导致网络超时）
    raw_dir = os.path.join(root, dataset_cls.__name__, "raw")
    need_download = not os.path.isdir(raw_dir) or len(os.listdir(raw_dir)) == 0

    train_data = dataset_cls(
        root=root, train=True, download=need_download, transform=transform
    )
    test_data = dataset_cls(
        root=root, train=False, download=need_download, transform=transform
    )

    # ── 构造 DataLoader ──
    train_loader = DataLoader(
        train_data, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    test_loader = DataLoader(
        test_data, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )

    return train_loader, test_loader
