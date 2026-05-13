"""
MLP Autoencoder — Fashion-MNIST 无监督重构
-------------------------------------------
不使用任何标签，通过重构任务训练 encoder-decoder 结构。

在 Fashion-MNIST 上训练 MLP Autoencoder，encoder 将 784 维压到 latent_dim，
decoder 从 latent 重构回 784 维。loss = MSE(原图, 重构图)。

产出:
    checkpoints/autoencoder.pt        — 模型参数
    results/ae_reconstruct.png        — 原图 vs 重构图对比
    results/ae_train_loss.png         — 训练/测试 loss 曲线
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
SEED = 42

set_seed(SEED)
device = get_device()
print(f"Device: {device}")

# ── 数据 ──
info = DATASET_INFO["fashion-mnist"]
train_loader, test_loader = get_loaders("fashion-mnist", batch_size=BATCH_SIZE)

# ── 模型 ──
model = Autoencoder(input_dim=info["input_dim"], latent_dim=LATENT_DIM).to(device)
n_params = sum(p.numel() for p in model.parameters())
print(f"Autoencoder: input={model.input_dim}, latent={model.latent_dim}, params={n_params:,}")

criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode="min", patience=3, factor=0.5
)


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    for images, _ in tqdm(loader, desc="train", leave=False):
        images = images.to(device)
        optimizer.zero_grad()
        recon, _ = model(images)
        loss = criterion(recon, images.flatten(1))
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
        recon, _ = model(images)
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
        torch.save(model.state_dict(), "checkpoints/autoencoder.pt")
        marker = " *"

    print(f"{epoch:6d}  {train_loss:12.6f}  {test_loss:12.6f}{marker}")

print(f"\n Best test loss: {best_loss:.6f}")
print(f" Saved: checkpoints/autoencoder.pt")

# ── Loss 曲线 ──
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(range(1, EPOCHS + 1), train_losses, "b-", label="Train")
ax.plot(range(1, EPOCHS + 1), test_losses, "r-", label="Test")
ax.set_xlabel("Epoch")
ax.set_ylabel("MSE Loss")
ax.set_title(f"Autoencoder Training (latent_dim={LATENT_DIM})")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("results/ae_train_loss.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/ae_train_loss.png")

# ── 重构对比图 ──
model.load_state_dict(torch.load("checkpoints/autoencoder.pt", weights_only=True))
model.eval()

images, _ = next(iter(test_loader))
images = images[:10].to(device)

with torch.no_grad():
    recon, z = model(images)

images_np = images.cpu().view(-1, 28, 28).numpy()
recon_np = recon.cpu().view(-1, 28, 28).numpy()

fig, axes = plt.subplots(2, 10, figsize=(12, 3))
for i in range(10):
    axes[0, i].imshow(images_np[i], cmap="gray")
    axes[0, i].axis("off")
    axes[1, i].imshow(recon_np[i], cmap="gray")
    axes[1, i].axis("off")
axes[0, 0].set_ylabel("Original", fontsize=10)
axes[1, 0].set_ylabel("Recon", fontsize=10)
fig.suptitle(f"Autoencoder Reconstruction (latent_dim={LATENT_DIM})", fontsize=11, y=1.01)
fig.tight_layout()
fig.savefig("results/ae_reconstruct.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/ae_reconstruct.png")

print(f"\n{'='*50}")
print(f"  Autoencoder training complete")
print(f"   latent_dim={LATENT_DIM}  params={n_params:,}")
print(f"   best test loss={best_loss:.6f}")
print(f"{'='*50}")
