"""
Variational Autoencoder — 从重构走向生成
------------------------------------------
Encoder 输出 mu 和 logvar，通过重参数化采样 z。
Loss = MSE(recon, x) + beta * KL( N(mu, sigma^2) || N(0,I) )

训练完成后，从 N(0,I) 采样 z 即可生成新图片。

产出:
    checkpoints/vae.pt              — 模型参数
    results/vae_reconstruct.png     — 原图 vs VAE 重构图
    results/vae_generate.png        — 从 N(0,I) 随机生成
    results/vae_latent_interp.png   — latent space 线性插值
    results/vae_train_loss.png      — 训练/测试 loss 曲线
"""
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tqdm import tqdm

from data import get_loaders, DATASET_INFO
from models import VAE
from utils import get_device, set_seed

os.makedirs("results", exist_ok=True)
os.makedirs("checkpoints", exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

LATENT_DIM = 32
BATCH_SIZE = 64
EPOCHS = 30
LR = 1e-3
BETA = 0.1
SEED = 42

set_seed(SEED)
device = get_device()
print(f"Device: {device}")

# ── 数据 ──
info = DATASET_INFO["fashion-mnist"]
train_loader, test_loader = get_loaders("fashion-mnist", batch_size=BATCH_SIZE)

# ── 模型 ──
model = VAE(input_dim=info["input_dim"], latent_dim=LATENT_DIM).to(device)
n_params = sum(p.numel() for p in model.parameters())
print(f"VAE: input={model.input_dim}, latent={model.latent_dim}, beta={BETA}, params={n_params:,}")


def vae_loss(recon, images, mu, logvar, beta=BETA):
    recon_loss = F.mse_loss(recon, images.flatten(1), reduction="sum") / images.size(0)
    kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_loss + beta * kl_loss, recon_loss.item(), kl_loss.item()


optimizer = torch.optim.Adam(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode="min", patience=3, factor=0.5
)


def train_one_epoch(model, loader, optimizer, device):
    model.train()
    total_loss, total_recon, total_kl = 0.0, 0.0, 0.0
    for images, _ in tqdm(loader, desc="train", leave=False):
        images = images.to(device)
        optimizer.zero_grad()
        recon, mu, logvar = model(images)
        loss, recon_v, kl_v = vae_loss(recon, images, mu, logvar)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        total_recon += recon_v
        total_kl += kl_v
    n = len(loader)
    return total_loss / n, total_recon / n, total_kl / n


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    total_loss, total_recon, total_kl = 0.0, 0.0, 0.0
    for images, _ in loader:
        images = images.to(device)
        recon, mu, logvar = model(images)
        loss, recon_v, kl_v = vae_loss(recon, images, mu, logvar)
        total_loss += loss.item()
        total_recon += recon_v
        total_kl += kl_v
    n = len(loader)
    return total_loss / n, total_recon / n, total_kl / n


# ── 训练 ──
train_losses, test_losses = [], []
best_loss = float("inf")

print(f"\n{'Epoch':>6}  {'Train Total':>12}  {'Train Recon':>12}  {'Train KL':>10}  "
      f"{'Test Total':>12}  {'Test Recon':>12}  {'Test KL':>10}")
print("-" * 74)

for epoch in range(1, EPOCHS + 1):
    train_loss, train_recon, train_kl = train_one_epoch(model, train_loader, optimizer, device)
    test_loss, test_recon, test_kl = evaluate(model, test_loader, device)
    scheduler.step(test_loss)

    train_losses.append(train_loss)
    test_losses.append(test_loss)

    marker = ""
    if test_loss < best_loss:
        best_loss = test_loss
        torch.save(model.state_dict(), "checkpoints/vae.pt")
        marker = " *"

    print(f"{epoch:6d}  {train_loss:12.4f}  {train_recon:12.4f}  {train_kl:10.4f}  "
          f"{test_loss:12.4f}  {test_recon:12.4f}  {test_kl:10.4f}{marker}")

print(f"\n Best test loss: {best_loss:.4f}")
print(f" Saved: checkpoints/vae.pt")

# ── Loss 曲线 ──
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(range(1, EPOCHS + 1), train_losses, "b-", label="Train Total")
ax.plot(range(1, EPOCHS + 1), test_losses, "r-", label="Test Total")
ax.set_xlabel("Epoch")
ax.set_ylabel("Loss")
ax.set_title(f"VAE Training (latent_dim={LATENT_DIM}, beta={BETA})")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("results/vae_train_loss.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/vae_train_loss.png")

# ── 重构对比 ──
model.load_state_dict(torch.load("checkpoints/vae.pt", map_location=device, weights_only=True))
model.eval()

images, _ = next(iter(test_loader))
images = images[:10].to(device)

with torch.no_grad():
    recon, _, _ = model(images)

images_np = images.cpu().view(-1, 28, 28).numpy()
recon_np = recon.cpu().view(-1, 28, 28).numpy()

fig, axes = plt.subplots(2, 10, figsize=(12, 3))
for i in range(10):
    axes[0, i].imshow(images_np[i], cmap="gray")
    axes[0, i].axis("off")
    axes[1, i].imshow(recon_np[i], cmap="gray")
    axes[1, i].axis("off")
axes[0, 0].set_ylabel("Original", fontsize=10)
axes[1, 0].set_ylabel("VAE Recon", fontsize=10)
fig.suptitle(f"VAE Reconstruction (latent_dim={LATENT_DIM})", fontsize=11, y=1.01)
fig.tight_layout()
fig.savefig("results/vae_reconstruct.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/vae_reconstruct.png")

# ── 从 N(0,I) 生成 ──
with torch.no_grad():
    samples = model.sample(10, device).cpu().view(-1, 28, 28).numpy()

fig, axes = plt.subplots(1, 10, figsize=(12, 1.5))
for i in range(10):
    axes[i].imshow(samples[i], cmap="gray")
    axes[i].axis("off")
fig.suptitle("VAE Generated Samples (from N(0,1))", fontsize=11, y=1.05)
fig.tight_layout()
fig.savefig("results/vae_generate.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/vae_generate.png")

# ── Latent space 插值 ──
img_a, img_b = images[0:1], images[1:2]

with torch.no_grad():
    mu_a, _ = model.encode(img_a)
    mu_b, _ = model.encode(img_b)

    interp_images = []
    for alpha in np.linspace(0, 1, 10):
        z = (1 - alpha) * mu_a + alpha * mu_b
        interp = model.decoder(z).view(28, 28).cpu().numpy()
        interp_images.append(interp)

fig, axes = plt.subplots(1, 12, figsize=(14, 1.6))
axes[0].imshow(img_a.cpu().view(28, 28).numpy(), cmap="gray")
axes[0].set_title("A", fontsize=8)
axes[0].axis("off")
for i, img in enumerate(interp_images):
    axes[i + 1].imshow(img, cmap="gray")
    axes[i + 1].axis("off")
axes[11].imshow(img_b.cpu().view(28, 28).numpy(), cmap="gray")
axes[11].set_title("B", fontsize=8)
axes[11].axis("off")
fig.suptitle("VAE Latent Space Interpolation", fontsize=11, y=1.05)
fig.tight_layout()
fig.savefig("results/vae_latent_interp.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/vae_latent_interp.png")

print(f"\n{'='*50}")
print(f"  VAE training complete")
print(f"   latent_dim={LATENT_DIM}  beta={BETA}  params={n_params:,}")
print(f"   best test loss={best_loss:.4f}")
print(f"{'='*50}")
