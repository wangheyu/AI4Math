"""
潜在空间可视化 + Linear Probe 评估
-----------------------------------
加载训练好的 Autoencoder encoder，可视化 latent space 结构，
并用线性分类器评估无监督表征的质量。

产出:
    results/latent_space_2d.png        — 2D latent space 散点图
    results/linear_probe_compare.png   — Linear Probe 准确率对比柱状图
"""
import os
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

from data import get_loaders, DATASET_INFO
from models import Autoencoder
from utils import get_device, set_seed

os.makedirs("results", exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

FASHION_CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
                   "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]

LATENT_DIM = 32
BATCH_SIZE = 256
SEED = 42

set_seed(SEED)
device = get_device()

# ── 加载数据 ──
info = DATASET_INFO["fashion-mnist"]
_, test_loader = get_loaders("fashion-mnist", batch_size=BATCH_SIZE)

# ── 加载训练好的 AE ──
model = Autoencoder(input_dim=info["input_dim"], latent_dim=LATENT_DIM).to(device)
model.load_state_dict(torch.load("checkpoints/autoencoder.pt", map_location=device, weights_only=True))
model.eval()
print(f"Loaded autoencoder (latent_dim={LATENT_DIM})")


# ── 提取 latent features ──
@torch.no_grad()
def extract_features(model, loader, device):
    features, labels = [], []
    for images, lbls in tqdm(loader, desc="extract"):
        z = model.encode(images.to(device))
        features.append(z.cpu().numpy())
        labels.append(lbls.numpy())
    return np.concatenate(features), np.concatenate(labels)


print("Extracting AE latent features ...")
X_ae, y_true = extract_features(model, test_loader, device)
print(f"  AE features: {X_ae.shape}")

# ── PCA features (baseline) ──
print("Computing PCA baseline features ...")
all_images, _ = [], []
for images, lbls in test_loader:
    all_images.append(images.flatten(1).numpy())
X_raw = np.concatenate(all_images)
# Standardize before PCA
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)
pca = PCA(n_components=LATENT_DIM, random_state=SEED)
X_pca = pca.fit_transform(X_scaled)
print(f"  PCA features: {X_pca.shape}  (variance retained: {pca.explained_variance_ratio_.sum():.2%})")


# ── 2D latent space 可视化 ──
def plot_latent_2d(X, y, title, fname, method="pca"):
    if X.shape[1] > 2:
        reducer = PCA(n_components=2, random_state=SEED)
        X2d = reducer.fit_transform(X)
        subtitle = f" (reduced via PCA from {X.shape[1]}D, {method} features)"
    else:
        X2d = X
        subtitle = ""

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    for i in range(10):
        mask = y == i
        ax.scatter(X2d[mask, 0], X2d[mask, 1], c=[colors[i]], label=FASHION_CLASSES[i],
                   s=2, alpha=0.5, rasterized=True)
    ax.set_title(title + subtitle, fontsize=10)
    ax.legend(markerscale=6, fontsize=7, ncol=2, loc="lower right")
    fig.tight_layout()
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✓ {fname}")


plot_latent_2d(X_pca, y_true, "PCA Features (32D)", "results/latent_space_pca.png", method="PCA")
plot_latent_2d(X_ae, y_true, "Autoencoder Latent Space (32D)", "results/latent_space_ae.png", method="AE")


# ── Linear Probe ──
def linear_probe(X_train, y_train, X_test, y_test, name):
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    clf = LogisticRegression(max_iter=2000, random_state=SEED)
    clf.fit(X_train_s, y_train)
    acc = clf.score(X_test_s, y_test)
    print(f"  {name:25s}: {acc:.2%}")
    return acc


# ── 收集训练集特征（单次遍历，features + labels 对齐） ──
print("Collecting training set features (single pass) ...")
X_train_pca_list, X_train_ae_list, y_train_list = [], [], []
train_loader, _ = get_loaders("fashion-mnist", batch_size=BATCH_SIZE)

@torch.no_grad()
def extract_batch_ae(model, images, device):
    return model.encode(images.to(device)).cpu().numpy()

for images, lbls in tqdm(train_loader, desc="train features"):
    X_train_pca_list.append(images.flatten(1).numpy())
    X_train_ae_list.append(extract_batch_ae(model, images, device))
    y_train_list.append(lbls.numpy())

X_train_raw = np.concatenate(X_train_pca_list)
X_train_ae = np.concatenate(X_train_ae_list)
y_train = np.concatenate(y_train_list)

# ── PCA features（在训练集上 fit，测试集上 transform） ──
scaler_full = StandardScaler()
X_train_scaled = scaler_full.fit_transform(X_train_raw)
X_test_scaled = scaler_full.transform(X_raw)
pca_full = PCA(n_components=LATENT_DIM, random_state=SEED)
X_train_pca = pca_full.fit_transform(X_train_scaled)
X_test_pca = pca_full.transform(X_test_scaled)

print("\nLinear Probe Results (latent_dim=32, logistic regression):")
print("-" * 50)
results = {}
results["PCA (32D)"] = linear_probe(X_train_pca, y_train, X_test_pca, y_true, "PCA (32D)")
results["AE (32D)"]  = linear_probe(X_train_ae, y_train, X_ae, y_true, "AE (32D)")

# ── 对比柱状图 ──
fig, ax = plt.subplots(figsize=(6, 4))
names = list(results.keys())
accs = [results[n] * 100 for n in names]
bars = ax.bar(names, accs, color=["#4472C4", "#ED7D31"], width=0.4)
ax.set_ylabel("Linear Probe Accuracy (%)")
ax.set_title("Unsupervised Representation Quality — Linear Probe")
ax.set_ylim(0, max(accs) + 10)
for bar, acc in zip(bars, accs):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
            f"{acc:.1f}%", ha="center", fontsize=11, fontweight="bold")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("results/linear_probe_compare.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/linear_probe_compare.png")

print(f"\n{'='*50}")
for name, acc in results.items():
    print(f"  {name:25s}: {acc:.2%}")
print(f"{'='*50}")
