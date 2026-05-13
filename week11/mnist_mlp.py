"""
MNIST 手写数字识别 —— MLP 训练与测试脚本
------------------------------------------
本脚本完整演示了一个监督学习项目的核心流程:
    1. 加载数据
    2. 构建模型
    3. 定义损失函数和优化器
    4. 训练循环（前向传播 → 计算损失 → 反向传播 → 参数更新）
    5. 测试循环（评估泛化能力）
    6. 保存模型参数

运行方式:
    python mnist_mlp.py

预期结果:
    10 个 epoch 后测试准确率约 97%-98%
"""

import os
import torch  #pytorch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm  # 进度条库，让训练过程可视化

from data import get_mnist_loaders
from models import MLPClassifier
from utils import accuracy, get_device, save_checkpoint, set_seed


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    """
    执行一个 epoch 的训练。

    一个 epoch 意味着模型"看"完整个训练集一次。
    每个 epoch 包含若干 batch，每个 batch 执行一次参数更新。

    训练循环的 5 个核心步骤:
        1. optimizer.zero_grad(): 清空上一轮累积的梯度
           （PyTorch 默认累加梯度，不清零会导致梯度叠加）
        2. model(images): 前向传播，输入图像，输出预测分数
           数据依次经过 Flatten → Linear → ReLU → Linear → ReLU → Linear
        3. criterion(logits, targets): 计算损失
           CrossEntropyLoss = softmax + 负对数似然
           损失值衡量"预测和真实标签差多远"
        4. loss.backward(): 反向传播
           从损失开始，沿计算图反向计算每个参数的梯度 ∂L/∂w
           这是自动求导 (autograd) 的核心
        5. optimizer.step(): 参数更新
           根据梯度调整参数: w_new = w_old - lr * ∂L/∂w
           Adam 在此基础上加入动量和自适应学习率

    参数:
        model: 待训练的模型
        loader: 训练集 DataLoader
        criterion: 损失函数
        optimizer: 优化器
        device: CPU 或 CUDA

    返回:
        (平均损失, 平均准确率)
    """
    # model.train() 设置模型为训练模式
    # 对 MLP 影响不大，但对包含 Dropout、BatchNorm 的模型至关重要:
    #   - Dropout 在训练时随机丢弃神经元，测试时关闭
    #   - BatchNorm 在训练时用批次统计量，测试时用全局统计量
    model.train()
    total_loss = 0.0
    total_acc = 0.0
    n_batches = len(loader)

    # 遍历每个 batch
    for images, targets in tqdm(loader, desc="train", leave=False):
        # 将数据移到指定设备（GPU 或 CPU），模型和数据必须在同一设备
        images, targets = images.to(device), targets.to(device)

        # ---- 训练核心 5 步 ----
        # 1. 清空梯度（防止梯度在不同 batch 间累积）
        optimizer.zero_grad()
        # 2. 前向传播：输入 → 模型 → 输出预测分数
        logits = model(images)
        # 3. 计算损失：比较预测分数与真实标签
        loss = criterion(logits, targets)
        # 4. 反向传播：自动计算每个参数的梯度
        loss.backward()
        # 5. 更新参数：沿梯度负方向移动一小步
        optimizer.step()

        # 记录本轮损失和准确率（用于后续统计）
        total_loss += loss.item()
        total_acc += accuracy(logits, targets)

    return total_loss / n_batches, total_acc / n_batches


# @torch.no_grad() 装饰器：测试阶段关闭梯度计算
# 推理时不需要梯度，关闭后可以:
#   - 节省显存（不保存中间激活值）
#   - 加速计算（不构建计算图）
@torch.no_grad()
def evaluate(
    model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device
) -> tuple[float, float]:
    """
    在给定数据集上评估模型性能。

    与训练循环的关键区别:
        - model.eval(): 切换到评估模式
        - torch.no_grad(): 关闭自动求导
        - 没有 optimizer.zero_grad() / loss.backward() / optimizer.step()
          评估阶段只做前向传播，不更新参数

    这体现了"训练"和"推理"的本质区别:
        - 训练: 前向 + 反向 + 参数更新（学习）
        - 推理: 仅前向（使用已学到的参数做预测）

    参数:
        model: 待评估的模型
        loader: 测试集 DataLoader
        criterion: 损失函数
        device: CPU 或 CUDA

    返回:
        (平均损失, 平均准确率)
    """
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
    """
    主函数：串联数据、模型、训练、评估、保存的完整流程。
    """
    # 固定随机种子，保证每次运行结果可复现
    set_seed(42)
    # 自动选择 GPU 或 CPU
    device = get_device()
    print(f"Using device: {device}")

    # ---- 超参数 ----
    # 超参数是训练前人为设定的参数，不同于模型参数（权重、偏置）
    # 它们控制训练过程本身，通常需要通过实验调优
    batch_size = 64   # 每批 64 张图片
    lr = 1e-3         # 学习率：控制参数更新的步长
                       #   太大 → 训练不稳定，损失震荡甚至发散
                       #   太小 → 收敛太慢，可能陷入局部最优
    epochs = 10       # 训练轮数：整个数据集遍历的次数

    # ---- 加载数据 ----
    train_loader, test_loader = get_mnist_loaders(batch_size=batch_size)

    # ---- 构建模型 ----
    # 将模型移到 GPU：模型的参数和缓冲区会被复制到 GPU 显存
    model = MLPClassifier().to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {n_params:,}")

    # ---- 损失函数 ----
    # CrossEntropyLoss 内部流程:
    #   1. 对 logits 做 softmax → 转为概率分布
    #   2. 取正确类别对应概率的负对数 → -log(p_correct)
    #   3. 对整个 batch 取平均
    # 直观理解：正确类别的概率越高，损失越小
    criterion = nn.CrossEntropyLoss()

    # ---- 优化器 ----
    # Adam (Adaptive Moment Estimation):
    #   - 结合了 Momentum（用历史梯度方向平滑更新）和 RMSprop（自适应学习率）
    #   - 每个参数有独立的自适应学习率，适合大多数任务
    #   - 是 SGD 的改进版，收敛更快，对学习率不那么敏感
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # ---- 训练与评估循环 ----
    # 打印表头
    print(f"\n{'Epoch':>6}  {'Train Loss':>10}  {'Train Acc':>10}  "
          f"{'Test Loss':>10}  {'Test Acc':>10}")
    print("-" * 55)

    for epoch in range(1, epochs + 1):
        # 训练一个 epoch：遍历全部训练数据，更新参数
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        # 在每个 epoch 结束后评估测试集
        # 这样可以看到模型在"没见过的数据"上的表现变化
        test_loss, test_acc = evaluate(
            model, test_loader, criterion, device
        )
        print(f"{epoch:6d}  {train_loss:10.4f}  {train_acc:10.4f}  "
              f"{test_loss:10.4f}  {test_acc:10.4f}")

    # ---- 保存模型 ----
    # 创建 checkpoints 目录（如果不存在）
    os.makedirs("checkpoints", exist_ok=True)
    # 保存模型的 state_dict（只含权重和偏置，不含结构）
    # 后续阶段会从 .pt 文件读取参数，导出为文本格式供 C 语言推理使用
    save_checkpoint(model, "checkpoints/mnist_mlp.pt")
    print(f"\nCheckpoint saved to checkpoints/mnist_mlp.pt")
    print(f"Final test accuracy: {test_acc * 100:.2f}%")


if __name__ == "__main__":
    main()
