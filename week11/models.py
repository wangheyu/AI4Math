"""
模型定义模块
-----------
MLPClassifier / CNNClassifier — 监督学习分类器
Autoencoder / VAE           — 无监督学习模型
"""

import torch
import torch.nn as nn


class MLPClassifier(nn.Module):
    """
    多层感知机 (Multilayer Perceptron, MLP) 分类器。

    网络结构:
        输入层: input_dim 个神经元  (默认 784 = 28×28×1)
        隐藏层1: 128 个神经元 + ReLU 激活
        隐藏层2: 64 个神经元  + ReLU 激活
        输出层: num_classes 个神经元 (默认 10)

    MNIST 参数量: 109,386
        - Linear(784→128): 784×128 + 128 = 100,480
        - Linear(128→64):  128×64  + 64  =   8,256
        - Linear(64→10):   64×10   + 10  =     650

    CIFAR-10 参数量 (input_dim=2352):
        - Linear(2352→128): 2352×128 + 128 = 301,184
        - 总计约 310K

    参数:
        input_dim:   输入维度，默认 784（28×28 灰度图）
                     CIFAR-10 应设为 2352（28×28×3 RGB）
        num_classes: 输出类别数，默认 10
    """

    def __init__(self, input_dim: int = 784, num_classes: int = 10) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.num_classes = num_classes

        self.net = nn.Sequential(
            # Flatten: 将图像张量展平为一维向量
            # MNIST:   (batch, 1, 28, 28)  → (batch, 784)
            # CIFAR10: (batch, 3, 28, 28)  → (batch, 2352)
            nn.Flatten(),

            # 第一隐藏层: input_dim → 128
            nn.Linear(input_dim, 128),
            nn.ReLU(),

            # 第二隐藏层: 128 → 64
            nn.Linear(128, 64),
            nn.ReLU(),

            # 输出层: 64 → num_classes
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        """
        前向传播：输入图像张量，输出各类别的预测分数。

        参数:
            x: 输入张量，形状 (batch_size, 1, 28, 28)
        返回:
            logits: 原始分数，形状 (batch_size, 10)
        """
        return self.net(x)


class CNNClassifier(nn.Module):
    """
    CNN 分类器。

    网络结构:
        Conv2d(in_channels→16, 3×3, padding=1) → 28×28×16
        ReLU → MaxPool2d(2) → 14×14×16
        Conv2d(16→32, 3×3, padding=1) → 14×14×32
        ReLU → MaxPool2d(2) → 7×7×32
        Flatten → 7×7×32 = 1568 (或 7×7×64 = 3136)
        Linear(?, num_classes)

    MNIST 参数量: ~20,490 (in_channels=1)
        - Conv1: 1×16×3×3 + 16 = 160
        - Conv2: 16×32×3×3 + 32 = 4,640
        - Linear: 1568×10 + 10 = 15,690

    CIFAR-10 参数量: ~21,066 (in_channels=3)
        - Conv1: 3×16×3×3 + 16 = 448
        - Conv2: 16×32×3×3 + 32 = 4,640
        - Linear: 1568×10 + 10 = 15,690  (flatten dim 不变)
        - 仅第一层卷积多了 288 个参数

    参数:
        in_channels: 输入通道数，默认 1（灰度图），CIFAR-10 应设为 3（RGB）
        num_classes: 输出类别数，默认 10

    与 MLP 的核心区别:
        - MLP: 将图像视为独立像素，丢弃空间结构
        - CNN: 保留二维结构，用卷积核扫描局部区域
        - 卷积 = 权重共享的局部特征检测器
        - Pooling = 降采样，增大感受野，提供平移不变性
    """

    def __init__(self, in_channels: int = 1, num_classes: int = 10) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes

        # 经过两次 MaxPool2d(2)，空间尺寸从 28→14→7
        # 第二层卷积固定输出 32 通道（可改为 64 以增强 CIFAR-10 表达能力）
        conv2_out = 64 if in_channels == 3 else 32
        # CIFAR-10 三通道图像更复杂，增加卷积核数量有助于提取更多特征
        flat_dim = conv2_out * 7 * 7

        self.net = nn.Sequential(
            # 第一个卷积块: in_channels → 16
            # padding=1 保持 28×28 尺寸不变
            nn.Conv2d(in_channels, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 28×28 → 14×14

            # 第二个卷积块: 16 → conv2_out
            nn.Conv2d(16, conv2_out, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 14×14 → 7×7

            # Flatten + 全连接输出
            nn.Flatten(),
            nn.Linear(flat_dim, num_classes),
        )

    def forward(self, x):
        return self.net(x)


class Autoencoder(nn.Module):
    """
    MLP Autoencoder — 无监督重构模型。

    Encoder: input_dim → 256 → 64 → latent_dim
    Decoder: latent_dim → 64 → 256 → input_dim

    Fashion-MNIST: input_dim=784 (28×28 灰度), latent_dim 默认 32

    训练时不需要标签，loss = MSE(input, output)。
    """

    def __init__(self, input_dim: int = 784, latent_dim: int = 32) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim

        self.encoder = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim),
        )

        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 256),
            nn.ReLU(),
            nn.Linear(256, input_dim),
            nn.Sigmoid(),  # 输出归一化到 [0,1]，匹配 ToTensor 范围
        )

    def forward(self, x):
        z = self.encoder(x)
        recon = self.decoder(z)
        return recon, z

    def encode(self, x):
        return self.encoder(x)


class VAE(nn.Module):
    """
    Variational Autoencoder — 生成模型。

    Encoder 输出 mu 和 logvar（各 latent_dim 维），
    通过重参数化技巧采样 z = mu + eps * exp(logvar/2)。

    Loss = MSE(recon, x) + beta * KL( N(mu, sigma^2) || N(0,I) )
    """

    def __init__(self, input_dim: int = 784, latent_dim: int = 32) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # shared encoder trunk
        self.encoder_trunk = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 64),
            nn.ReLU(),
        )
        self.fc_mu = nn.Linear(64, latent_dim)
        self.fc_logvar = nn.Linear(64, latent_dim)

        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 256),
            nn.ReLU(),
            nn.Linear(256, input_dim),
            nn.Sigmoid(),
        )

    def encode(self, x):
        h = self.encoder_trunk(x)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decoder(z)
        return recon, mu, logvar

    def sample(self, num_samples: int, device):
        """从标准正态分布采样 z，解码生成新图片。"""
        z = torch.randn(num_samples, self.latent_dim, device=device)
        return self.decoder(z)
