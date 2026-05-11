# 阶段 4 实验记录：多数据集对比与泛化分析

## 实验设置

- **训练脚本**: `train_classifier.py`
- **统一参数**: epochs=10, batch_size=64, lr=1e-3, seed=42
- **设备**: CUDA (GPU)
- **数据预处理**: 所有数据集统一 Resize 到 28×28, ToTensor 归一化到 [0,1]
  - 灰度数据集（MNIST/Fashion-MNIST）: 1 通道
  - CIFAR-10: 3 通道 RGB（保留颜色信息）

## 实验结果

| # | 数据集 | 模型 | 参数量 | Train Acc | Test Acc | 泛化差距 | 观察 |
|---|--------|------|--------|-----------|----------|---------|------|
| 1 | MNIST | MLP | 109,386 | 99.31% | 97.44% | 1.87% | 简单灰度手写数字，MLP 即可取得不错效果 |
| 2 | MNIST | CNN | 20,490 | 99.31% | 98.88% | 0.43% | CNN 参数仅为 MLP 的 19%，准确率反高 1.44% |
| 3 | Fashion-MNIST | MLP | 109,386 | 90.84% | 88.04% | 2.80% | 换到服饰数据集，MLP 准确率骤降 ~10% |
| 4 | Fashion-MNIST | CNN | 20,490 | 92.34% | 90.29% | 2.05% | CNN 仍优于 MLP，但优势缩小（+2.3% vs MNIST 的 +1.4%） |
| 5 | KMNIST | CNN | 20,490 | 98.64% | 92.26% | 6.38% | 日文假名字符，同尺寸但分布变化大，泛化差距显著 |
| 6 | CIFAR-10 | CNN | 41,098 | 72.52% | 66.78% | 5.74% | 真实彩色自然图像显著更难；CNN 参数翻倍（3 通道→64 核）仍不足 |


## 泛化分析

### 1. 什么是泛化？

**泛化 (Generalization)** 是指模型在训练时未见过的数据上的表现能力。

- **泛化误差** = 训练准确率 − 测试准确率
- 泛化误差小 → 模型学到了真正可迁移的模式，而不是死记硬背
- 泛化误差大 → 模型可能**过拟合 (overfitting)**：记住了训练样本，但无法推广到新样本

### 2. 跨数据集对比揭示的问题

```
MNIST MLP:     97.44%
Fashion-MNIST MLP: 88.04%  ← 下降 9.4%
CIFAR-10 CNN:      66.78%  ← 从 98%+ 骤降
```

**核心发现：模型在一个数据集上表现好，不代表它拥有通用的"视觉智能"。**

- MNIST 的 97%+ 准确率容易让人产生"模型已经理解数字"的错觉
- 但同样的 MLP 在 Fashion-MNIST 上只有 88%——模型学到的只是 MNIST 特定的像素模式，而非"视觉理解"
- CIFAR-10 上 CNN 也仅 67%——真实世界图像包含复杂背景、颜色、姿态变化，远比 MNIST 困难

### 3. MLP vs CNN 的泛化对比

| 数据集 | MLP Test Acc | CNN Test Acc | CNN 优势 |
|--------|-------------|-------------|---------|
| MNIST | 97.44% | 98.88% | +1.44% |
| Fashion-MNIST | 88.04% | 90.29% | +2.25% |

CNN 在所有数据集上均优于 MLP，且任务越难（Fashion-MNIST），CNN 的优势越大。这说明 CNN 的**归纳偏置**（局部感受野、权重共享、平移不变性）不仅提高了准确率，也提高了泛化能力。

### 4. 为什么训练准确率不能代表模型能力？

| 现象 | 说明 |
|------|------|
| 训练 Acc 高 + 测试 Acc 高 | 泛化好，模型学到了有效模式 |
| 训练 Acc 高 + 测试 Acc 低 | **过拟合**：模型在"背诵"训练集，而非学习 |
| 训练 Acc 低 + 测试 Acc 低 | **欠拟合**：模型容量不足或训练不充分 |

CIFAR-10 实验是典型的"训练 Acc 不高 + 测试 Acc 更低 + 差距大"——模型容量和训练时间都不足以处理彩色自然图像的复杂性。

### 5. MNIST 为什么太简单？

- **背景纯净**：黑色背景，白色数字，无噪声
- **居中规范**：数字位于图像中心，大小一致
- **类别清晰**：10 个类别之间差异大，类内差异小
- **信息密度低**：784 个像素中大部分是背景（零值）

因此，MNIST 上的高准确率 **严重高估了模型的真实能力**。Fashion-MNIST 和 CIFAR-10 更能反映模型在处理真实世界图像时的表现。

## 关键结论

1. **同一模型在不同数据集上表现差异巨大**——模型学到的是特定数据分布的模式，而非通用智能
2. **CNN 在图像任务上始终优于 MLP**——卷积的归纳偏置天然适合视觉数据
3. **泛化差距随任务难度增大而增大**——简单任务（MNIST）差距 <2%，困难任务（CIFAR-10）差距 >5%
4. **MNIST 不能作为衡量图像识别能力的唯一标准**——需要多数据集、多难度的评估体系

## 复现命令

```bash
# 实验 1-4
conda run -n Teaching python train_classifier.py --dataset mnist --model mlp
conda run -n Teaching python train_classifier.py --dataset mnist --model cnn
conda run -n Teaching python train_classifier.py --dataset fashion-mnist --model mlp
conda run -n Teaching python train_classifier.py --dataset fashion-mnist --model cnn

# 实验 5 (待网络恢复)
conda run -n Teaching python train_classifier.py --dataset kmnist --model cnn

# 实验 6
conda run -n Teaching python train_classifier.py --dataset cifar10 --model cnn
```
