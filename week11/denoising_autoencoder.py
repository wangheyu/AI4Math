"""
Denoising Autoencoder — 从噪声中重构干净图像
---------------------------------------------
训练时输入 = 原图 + 高斯噪声，目标 = 干净原图。
迫使 encoder 学习忽略噪声、捕捉本质结构的鲁棒表征。

复用 Autoencoder 模型结构，仅改变训练方式。

产出:
    checkpoints/denoising_ae.pt      — 模型参数
    results/dae_denoise.png          — 噪声输入 / 去噪输出 / 原图对比
    results/dae_train_loss.png       — 训练/测试 loss 曲线
"""
import os
import torch
import torch.nn as nn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tqdm import tqdm

from data import get_loaders, DATASET_INFO
from models import Autoencoder
from utils import get_device, set_seed

os.makedirs("results", exist_ok=True)
os.makedirs("checkpoints", exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

LATENT_DIM = 32
BATCH_SIZE = 64
EPOCHS = 30
LR = 1e-3
NOISE_STD = 0.3
SEED = 42

set_seed(SEED)
device = get_device()
print(f"Device: {device}")
print(f"Noise std: {NOISE_STD}")

# ── 数据 ──
info = DATASET_INFO["fashion-mnist"]
train_loader, test_loader = get_loaders("fashion-mnist", batch_size=BATCH_SIZE)

# ── 模型 ──
model = Autoencoder(input_dim=info["input_dim"], latent_dim=LATENT_DIM).to(device)
print(f"Autoencoder: latent_dim={LATENT_DIM}")

criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode="min", patience=3, factor=0.5
)


def add_noise(images):
    noise = torch.randn_like(images) * NOISE_STD
    return torch.clamp(images + noise, 0, 1)


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    for images, _ in tqdm(loader, desc="train", leave=False):
        images = images.to(device)
        noisy = add_noise(images)           # 加噪声输入
        optimizer.zero_grad()
        recon, _ = model(noisy)
        loss = criterion(recon, images.flatten(1))  # 目标是干净原图
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    for images, _ in loader:
        images = images.to(device)
        noisy = add_noise(images)
        recon, _ = model(noisy)
        loss = criterion(recon, images.flatten(1))
        total_loss += loss.item()
    return total_loss / len(loader)


# ── 训练 ──
train_losses, test_losses = [], []
best_loss = float("inf")

print(f"\n{'Epoch':>6}  {'Train Loss':>12}  {'Test Loss':>12}")
print("-" * 32)

for epoch in range(1, EPOCHS + 1):
    train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
    test_loss = evaluate(model, test_loader, criterion, device)
    scheduler.step(test_loss)

    train_losses.append(train_loss)
    test_losses.append(test_loss)

    marker = ""
    if test_loss < best_loss:
        best_loss = test_loss
        torch.save(model.state_dict(), "checkpoints/denoising_ae.pt")
        marker = " *"

    print(f"{epoch:6d}  {train_loss:12.6f}  {test_loss:12.6f}{marker}")

print(f"\n Best test loss: {best_loss:.6f}")
print(f" Saved: checkpoints/denoising_ae.pt")

# ── Loss 曲线 ──
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(range(1, EPOCHS + 1), train_losses, "b-", label="Train")
ax.plot(range(1, EPOCHS + 1), test_losses, "r-", label="Test")
ax.set_xlabel("Epoch")
ax.set_ylabel("MSE Loss")
ax.set_title(f"Denoising AE Training (noise std={NOISE_STD}, latent_dim={LATENT_DIM})")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("results/dae_train_loss.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/dae_train_loss.png")

# ── 去噪对比图 ──
model.load_state_dict(torch.load("checkpoints/denoising_ae.pt", weights_only=True))
model.eval()

images, _ = next(iter(test_loader))
images = images[:10].to(device)
noisy_images = add_noise(images)

with torch.no_grad():
    recon, _ = model(noisy_images)

def to_np(t):
    return t.cpu().view(-1, 28, 28).numpy()

noisy_np = to_np(noisy_images)
recon_np = to_np(recon)
orig_np = to_np(images)

fig, axes = plt.subplots(3, 10, figsize=(12, 4.5))
for i in range(10):
    axes[0, i].imshow(noisy_np[i], cmap="gray")
    axes[0, i].axis("off")
    axes[1, i].imshow(recon_np[i], cmap="gray")
    axes[1, i].axis("off")
    axes[2, i].imshow(orig_np[i], cmap="gray")
    axes[2, i].axis("off")
axes[0, 0].set_ylabel("Noisy", fontsize=10)
axes[1, 0].set_ylabel("Denoised", fontsize=10)
axes[2, 0].set_ylabel("Original", fontsize=10)
fig.suptitle(f"Denoising Autoencoder (noise std={NOISE_STD})", fontsize=11, y=1.01)
fig.tight_layout()
fig.savefig("results/dae_denoise.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/dae_denoise.png")

print(f"\n{'='*50}")
print(f"  Denoising AE training complete")
print(f"   noise_std={NOISE_STD}  latent_dim={LATENT_DIM}")
print(f"   best test loss={best_loss:.6f}")
print(f"{'='*50}")
