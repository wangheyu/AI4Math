"""
工具函数模块
-----------
提供设备选择、随机种子、准确率计算和模型保存等通用功能。
这些函数会在训练、测试、参数导出等各个阶段被复用。
"""

import random
import torch
import numpy as np


def get_device() -> torch.device:
    """
    自动选择可用的计算设备。

    PyTorch 中张量和模型必须放在同一设备上才能计算。
    优先使用 GPU (cuda)，GPU 不可用时退回到 CPU。
    GPU 通过大规模并行加速矩阵运算，是深度学习训练的关键硬件。
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def set_seed(seed: int = 42) -> None:
    """
    固定所有随机数种子，保证实验结果可复现。

    深度学习中有多处随机性来源：
    - Python 标准库 random：影响数据打乱等
    - NumPy 随机：影响数据预处理等
    - PyTorch 随机：影响权重初始化、dropout 等
    - CUDA 随机：GPU 上的并行计算也有随机性

    固定种子后，同样的代码和数据会产生相同结果，
    这对调试和科研可复现至关重要。
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    """
    计算分类准确率。

    参数:
        logits: 模型原始输出，形状为 (batch_size, num_classes)
                每行是该样本属于各类别的"分数"（未经 softmax）
        targets: 真实标签，形状为 (batch_size,)，每个元素是 0-9 的类别索引

    返回:
        float: 该批次中预测正确的比例，范围 [0, 1]

    原理:
        argmax(dim=1) 取每行最大值的位置作为预测类别，
        与真实标签比较后取平均即得准确率。
    """
    preds = logits.argmax(dim=1)
    return (preds == targets).float().mean().item()


def save_checkpoint(model: torch.nn.Module, path: str) -> None:
    """
    保存模型参数到文件。

    只保存 state_dict（各层的权重和偏置），不保存模型结构代码。
    这样做的好处：
    - 文件更小（只含数值，不含代码）
    - 跨语言可用（Python 训练的权重可以被 C 语言读取）
    - 这正是阶段 3 "参数导出与 C 推理"的基础

    参数:
        model: 训练好的 PyTorch 模型
        path: 保存路径，如 'checkpoints/mnist_mlp.pt'
    """
    torch.save(model.state_dict(), path)
