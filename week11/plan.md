# Week 11 Plan: MNIST, CNN, C Inference, Generalization, and Unsupervised Learning

## 目标

本周项目以 MNIST 为主线，先用 PyTorch 跑通最小的监督学习流程，再逐步引入 CNN、参数导出与 C 语言推理、数据集扩展与泛化讨论，最后过渡到 Fashion-MNIST 上的无监督学习。

核心目标不是只得到高准确率，而是让学生理解：

- 数据、模型、损失函数、优化器、训练、推理之间的关系
- MLP 和 CNN 在图像任务上的差异
- Python 训练和 C 语言推理之间如何通过参数文件连接；正式实现先用 MLP，CNN 推理只作为展示或扩展
- 泛化能力为什么不是训练集准确率
- 无监督学习如何在没有标签的情况下学习数据结构

## 阶段 1：MNIST + PyTorch MLP 基线

### 1.1 实现目标

先实现一个不含 CNN 的 MNIST 手写数字识别项目，使用全连接神经网络，也就是 MLP。

建议文件：

- `mnist_mlp.py`：训练、验证、测试 MLP
- `models.py`：定义 MLP 模型，后续 CNN 可复用
- `data.py`：封装 MNIST 数据加载
- `utils.py`：设备选择、随机种子、准确率计算、保存模型等工具函数

### 1.2 实现步骤

1. 使用 `torchvision.datasets.MNIST` 下载并加载数据。
2. 使用 `transforms.ToTensor()` 把图像转成 `[1, 28, 28]` 张量。
3. 使用 `DataLoader` 构造训练集和测试集迭代器。
4. 定义 MLP：
   - 输入层：`28 * 28 = 784`
   - 隐藏层：例如 `784 -> 128 -> 64`
   - 输出层：`64 -> 10`
5. 使用 `CrossEntropyLoss` 作为分类损失。
6. 使用 `Adam` 或 `SGD` 优化参数。
7. 编写训练循环：
   - 前向传播
   - 计算损失
   - `optimizer.zero_grad()`
   - `loss.backward()`
   - `optimizer.step()`
8. 编写测试循环：
   - 使用 `model.eval()`
   - 使用 `torch.no_grad()`
   - 统计 accuracy
9. 保存训练好的模型参数到 `checkpoints/mnist_mlp.pt`。

### 1.3 讲解重点

- 图像如何变成张量
- 标签 `0-9` 如何对应分类问题
- batch 的含义
- 模型参数是什么
- 前向传播、损失函数、反向传播、梯度下降分别在做什么
- 为什么训练阶段和测试阶段要分开
- `model.train()` 和 `model.eval()` 的区别

### 1.4 预期结果

MLP 在 MNIST 上应能达到约 97%-98% 测试准确率。这个结果足以说明：即使不使用 CNN，简单全连接网络也可以在 MNIST 上取得不错表现。

## 阶段 2：MNIST + CNN 版本

### 2.1 实现目标

在已经跑通 MLP 的基础上，引入 CNN 版本，展示卷积结构为什么更适合图像。

建议文件：

- `mnist_cnn.py`：训练、验证、测试 CNN
- `models.py`：新增 `CNNClassifier`

### 2.2 实现步骤

1. 复用阶段 1 的数据加载逻辑。
2. 定义 CNN：
   - `Conv2d(1, 16, kernel_size=3, padding=1)`
   - `ReLU`
   - `MaxPool2d(2)`
   - `Conv2d(16, 32, kernel_size=3, padding=1)`
   - `ReLU`
   - `MaxPool2d(2)`
   - flatten
   - 全连接输出到 10 类
3. 复用训练和测试循环，尽量保持代码结构与 MLP 一致。
4. 保存训练好的参数到 `checkpoints/mnist_cnn.pt`。
5. 对比 MLP 和 CNN 的：
   - 参数量
   - 测试准确率
   - 收敛速度
   - 对图像结构的利用方式

### 2.3 讲解重点

- 卷积核是什么
- 局部感受野
- 权重共享
- feature map 的含义
- pooling 的作用
- 为什么 CNN 比 MLP 更适合图像
- flatten 前后的张量形状如何变化

### 2.4 预期结果

CNN 在 MNIST 上应达到约 98%-99% 测试准确率。重点不是准确率提升多少，而是借此说明 CNN 利用了图像的二维局部结构。

## 阶段 3：数据、模型、参数、推理的关系，以及 C 语言推理

### 3.1 实现目标

以 MNIST 项目为模板，明确区分：

- 数据：输入图像和标签
- 模型结构：网络层如何连接
- 参数：训练后得到的权重和偏置
- 推理：固定参数后，对新输入计算输出类别

然后导出阶段 1 训练好的 MLP 参数，实现 C 语言推理。CNN 参数导出和 C 版 CNN 推理不作为主线要求，只作为课堂展示或扩展材料。

建议文件：

- `export_mlp_params.py`：导出 MLP 参数
- `mnist_mlp_infer.c`：C 语言 MLP 推理
- `export_cnn_params.py`：导出 CNN 参数，展示或扩展用
- `mnist_cnn_infer.c`：C 语言 CNN 推理，展示或扩展用
- `params/`：保存导出的文本或二进制参数
- `samples/`：保存若干 MNIST 测试样本

### 3.2 实现步骤

1. 在 Python 中加载训练好的 `.pt` 参数文件。
2. 从 `state_dict` 中取出每一层的 weight 和 bias。
3. 先导出 MLP 参数，建议使用简单文本格式，便于课堂检查：
   - 每层权重矩阵尺寸
   - 每层 bias 向量
   - 按行保存浮点数
4. 从 MNIST 测试集中导出若干图像样本到文本文件：
   - 图像像素归一化到 `[0, 1]`
   - 标签单独保存用于验证
5. 在 C 中实现 MLP 前向传播：
   - 读取输入图像
   - 读取权重和 bias
   - 实现矩阵向量乘法
   - 实现 ReLU
   - 实现 argmax
6. 用 C 推理同一张测试图片，并与 Python 推理结果对齐。
7. 课堂展示 CNN 推理的实现差异，但不要求完整手写。展示重点包括：
   - `conv2d`
   - `relu`
   - `maxpool2d`
   - `linear`
   - `argmax`
   - 多通道数组下标、padding、stride 带来的复杂度

### 3.3 讲解重点

- 训练和推理的区别
- 推理阶段不需要梯度
- `.pt` 文件本质上保存的是参数，不是“智能”本身
- 同一组参数可以在 Python、C 或其他语言里运行
- 深度学习框架帮助我们训练，但前向计算本身只是数值计算
- 为什么 C 推理适合说明模型部署

### 3.4 建议取舍

C 语言推理的正式任务只实现 MLP。MLP 的前向传播就是矩阵向量乘法、bias、ReLU 和 argmax，最适合说明“训练完成后，模型就是固定参数加确定性数值计算”。

CNN 的 C 推理只作为展示或扩展。原因是 CNN 会引入卷积窗口、多通道循环、padding、stride 和 pooling，下标管理会占用大量课堂时间，容易让重点从“理解推理”偏到“调 C 数组”。课堂上可以展示 CNN 推理伪代码或关键函数，但不把它作为必须完成的代码任务。

## 阶段 4：扩展数据集，并讨论泛化

### 4.1 实现目标

从 MNIST 扩展到 Fashion-MNIST、KMNIST 或 CIFAR-10，用同样的训练框架观察模型表现变化，并引出“泛化”的概念。

建议文件：

- `train_classifier.py`：统一训练入口，支持不同数据集和模型
- `experiments.md`：记录实验结果

### 4.2 实现步骤

1. 把数据集名称做成参数，例如：
   - `--dataset mnist`
   - `--dataset fashion-mnist`
   - `--dataset kmnist`
   - `--dataset cifar10`
2. 把模型类型做成参数，例如：
   - `--model mlp`
   - `--model cnn`
3. 在 MNIST 上训练 MLP 和 CNN，记录 train/test accuracy。
4. 在 Fashion-MNIST 上训练同样结构，记录结果。
5. 在 KMNIST 上重复实验。
6. 如果引入 CIFAR-10，需要调整输入通道为 3，并说明 MLP 对彩色自然图像表现较差。
7. 比较不同数据集上的结果：
   - 训练集准确率高，测试集准确率也高：泛化较好
   - 训练集准确率高，测试集准确率低：过拟合
   - 换一个数据集后准确率明显下降：说明模型学到的不是普遍“视觉智能”

### 4.3 讲解重点

- 什么是训练集、测试集、验证集
- 什么是泛化误差
- 为什么训练集准确率不能代表模型能力
- 数据分布变化会影响模型表现
- MNIST 太简单，不能代表真实图像识别任务
- Fashion-MNIST 为什么比 MNIST 更适合展示泛化问题

### 4.4 推荐实验表

| 数据集 | 模型 | 训练准确率 | 测试准确率 | 观察 |
|---|---|---:|---:|---|
| MNIST | MLP |  |  | 简单基线 |
| MNIST | CNN |  |  | 图像结构带来提升 |
| Fashion-MNIST | MLP |  |  | 任务更难 |
| Fashion-MNIST | CNN |  |  | CNN 优势更明显 |
| KMNIST | CNN |  |  | 同尺寸但分布变化 |
| CIFAR-10 | CNN |  |  | 真实彩色图像更难 |

## 阶段 5：Fashion-MNIST 上的无监督学习

### 5.1 实现目标

使用 Fashion-MNIST 介绍无监督学习。选择 Fashion-MNIST 是因为它比 MNIST 更难，PCA、聚类和自编码器之间的差异更明显。

建议文件：

- `pca_kmeans.py`：PCA 降维和 K-means 聚类
- `autoencoder.py`：MLP Autoencoder
- `denoising_autoencoder.py`：去噪自编码器
- `vae.py`：变分自编码器，可作为进阶
- `visualize_latent.py`：可视化潜在空间

### 5.2 实现步骤

1. 加载 Fashion-MNIST，但训练时不使用标签。
2. 实现 PCA baseline：
   - 将图像展平为 784 维向量
   - PCA 降到 2 维或 32 维
   - 用真实标签着色，仅用于可视化和评估
3. 实现 K-means：
   - 在原始像素上聚类
   - 在 PCA 特征上聚类
   - 对比聚类效果
4. 实现 MLP Autoencoder：
   - encoder：`784 -> 256 -> 64 -> latent`
   - decoder：`latent -> 64 -> 256 -> 784`
   - loss：重构误差，例如 MSE 或 BCE
5. 可视化 autoencoder 的结果：
   - 原图 vs 重构图
   - 2D latent space
   - 不同类别在 latent space 中是否自然分开
6. 实现 Denoising Autoencoder：
   - 输入加噪声图像
   - 输出重构干净图像
   - 讨论正则化和鲁棒性
7. 若时间允许，实现 VAE：
   - encoder 输出 `mu` 和 `logvar`
   - 使用重参数化技巧采样
   - loss 包含 reconstruction loss 和 KL divergence
   - 从标准正态分布采样生成新图片
8. 用 linear probe 评估表征：
   - 冻结 encoder
   - 用少量标签训练线性分类器
   - 比较 PCA 特征、普通 AE 特征、去噪 AE 特征

### 5.3 讲解重点

- 无监督学习不是没有目标，而是没有人工标签
- PCA 是线性降维
- Autoencoder 是非线性降维
- 重构任务为什么能迫使模型学习压缩表示
- latent space 的含义
- 去噪任务如何让特征更鲁棒
- VAE 如何从重构模型走向生成模型
- 为什么评估无监督学习需要额外设计指标

### 5.4 推荐实验表

| 方法 | 是否使用标签训练 | 表征维度 | 可视化效果 | Linear probe accuracy |
|---|---|---:|---|---:|
| PCA | 否 | 2 / 32 |  |  |
| K-means on pixels | 否 | 784 |  |  |
| K-means on PCA | 否 | 32 |  |  |
| MLP Autoencoder | 否 | 2 / 32 |  |  |
| Denoising Autoencoder | 否 | 2 / 32 |  |  |
| VAE | 否 | 2 / 32 |  |  |

## 推荐项目结构

```text
week11/
├── plan.md
├── data.py
├── models.py
├── utils.py
├── mnist_mlp.py
├── mnist_cnn.py
├── train_classifier.py
├── export_mlp_params.py
├── export_cnn_params.py          # 展示或扩展
├── mnist_mlp_infer.c
├── mnist_cnn_infer.c             # 展示或扩展
├── pca_kmeans.py
├── autoencoder.py
├── denoising_autoencoder.py
├── vae.py
├── visualize_latent.py
├── checkpoints/
├── params/
├── samples/
└── results/
```

## 建议执行顺序

1. 先写 `data.py`、`models.py`、`utils.py`，建立可复用骨架。
2. 完成 `mnist_mlp.py`，确认 MNIST MLP 能训练和测试。
3. 完成 `mnist_cnn.py`，对比 MLP 和 CNN。
4. 完成 `export_mlp_params.py` 和 `mnist_mlp_infer.c`，打通 Python 训练到 C 推理。
5. 简要展示 CNN 推理如果用 C 实现会多出哪些结构，不要求完整实现。
6. 把训练脚本整理成 `train_classifier.py`，支持多个数据集。
7. 跑 MNIST、Fashion-MNIST、KMNIST 的对比实验，用结果讨论泛化。
8. 完成 `pca_kmeans.py`，建立无监督学习 baseline。
9. 完成 `autoencoder.py` 和 `visualize_latent.py`。
10. 增加 `denoising_autoencoder.py`。
11. 时间允许时实现 `vae.py`。

## 最小可交付版本

如果时间有限，优先完成以下内容：

1. MNIST MLP 训练和测试
2. MNIST CNN 训练和测试
3. MLP 参数导出和 C 推理
4. Fashion-MNIST 上 MLP/CNN 对比，用于讨论泛化
5. Fashion-MNIST Autoencoder 重构和 latent space 可视化

这个版本已经能完整覆盖监督学习、模型结构、参数部署、泛化和无监督学习五个核心主题。CNN 的 C 推理不属于最小可交付版本，只在讲解中作为展示材料出现。

## 课堂讲解主线

建议用以下叙事串联：

1. MNIST 给我们一个干净的小图像分类问题。
2. MLP 说明神经网络的基本训练流程。
3. CNN 说明模型结构应该利用数据结构。
4. 参数导出和 C 推理说明训练完成后，模型就是一组固定参数加一段前向计算。
5. 扩展到 Fashion-MNIST/KMNIST/CIFAR-10 后，说明模型在一个数据集上表现好，不代表在所有数据上都好，这就是泛化问题。
6. 无监督学习进一步问：如果没有标签，模型还能不能学到有用的数据结构？
