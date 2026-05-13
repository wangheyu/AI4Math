"""
PCA 降维 + K-means 聚类 — 无监督学习 baseline
-----------------------------------------------
用经典方法探索 Fashion-MNIST 数据结构，不使用任何标签训练。

产出:
    results/pca_fashion_2d.png       — 2D PCA 散点图（真标签着色）
    results/pca_variance.png         — 累计解释方差曲线
    results/kmeans_confusion.png     — K-means 聚类 vs 真标签混淆矩阵
"""
import os
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from tqdm import tqdm

os.makedirs("results", exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

FASHION_CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
                   "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]

# ── 加载数据（不使用标签训练） ──
transform = transforms.ToTensor()
train_ds = datasets.FashionMNIST(root="datasets", train=True, download=False, transform=transform)
test_ds  = datasets.FashionMNIST(root="datasets", train=False, download=False, transform=transform)
train_loader = DataLoader(train_ds, batch_size=256, shuffle=False)
test_loader  = DataLoader(test_ds, batch_size=256, shuffle=False)


def gather_data(loader):
    """收集全部数据的 images 和 labels 为 numpy。"""
    images, labels = [], []
    for imgs, lbls in tqdm(loader, desc="gather"):
        images.append(imgs.flatten(1).numpy())
        labels.append(lbls.numpy())
    return np.concatenate(images), np.concatenate(labels)


print("Gathering test data ...")
X, y_true = gather_data(test_loader)

# ── 1. PCA ──
print("Running PCA (32D) ...")
pca32 = PCA(n_components=32, random_state=42)
X_pca32 = pca32.fit_transform(X)

print("Running PCA (2D for visualization) ...")
pca2 = PCA(n_components=2, random_state=42)
X_pca2 = pca2.fit_transform(X)

# ── 2D PCA 散点图 ──
fig, ax = plt.subplots(figsize=(8, 6))
colors = plt.cm.tab10(np.linspace(0, 1, 10))
for i in range(10):
    mask = y_true == i
    ax.scatter(X_pca2[mask, 0], X_pca2[mask, 1], c=[colors[i]], label=FASHION_CLASSES[i],
               s=2, alpha=0.5, rasterized=True)
ax.set_title("Fashion-MNIST — PCA 2D (colored by true labels for evaluation only)",
             fontsize=10)
ax.set_xlabel(f"PC1 ({pca2.explained_variance_ratio_[0]:.1%})")
ax.set_ylabel(f"PC2 ({pca2.explained_variance_ratio_[1]:.1%})")
ax.legend(markerscale=6, fontsize=7, ncol=2, loc="lower right")
fig.tight_layout()
fig.savefig("results/pca_fashion_2d.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ results/pca_fashion_2d.png")

# ── 累计解释方差 ──
fig, ax = plt.subplots(figsize=(6, 4))
cumsum = np.cumsum(pca32.explained_variance_ratio_)
ax.plot(range(1, 33), cumsum, "b-o", markersize=3)
ax.axhline(y=cumsum[1], color="gray", linestyle="--", alpha=0.5, label=f"2D: {cumsum[1]:.1%}")
ax.axhline(y=cumsum[31], color="gray", linestyle="--", alpha=0.5, label=f"32D: {cumsum[31]:.1%}")
ax.set_xlabel("Number of PCA components")
ax.set_ylabel("Cumulative explained variance ratio")
ax.set_title("Fashion-MNIST PCA — Cumulative Explained Variance")
ax.legend(fontsize=9)
ax.set_ylim(0, 1.02)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("results/pca_variance.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"✓ results/pca_variance.png  (2D: {cumsum[1]:.1%}, 32D: {cumsum[31]:.1%})")

# ── 2. K-means ──
def run_kmeans(data, name, n_clusters=10):
    print(f"K-means (k=10) on {name} ...")
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    y_pred = km.fit_predict(data)
    nmi = normalized_mutual_info_score(y_true, y_pred)
    ari = adjusted_rand_score(y_true, y_pred)
    print(f"  NMI={nmi:.4f}  ARI={ari:.4f}")
    return y_pred, nmi, ari

# K-means on raw pixels
y_km_pixel, nmi_pixel, ari_pixel = run_kmeans(X, "raw pixels (784D)")

# K-means on 32D PCA
y_km_pca, nmi_pca, ari_pca = run_kmeans(X_pca32, "PCA features (32D)")

# ── 混淆矩阵（K-means vs true labels） ──
def plot_kmeans_confusion(y_pred, nmi, ari, title, fname):
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_true, y_pred, normalize="true")

    fig, ax = plt.subplots(figsize=(6, 5.5))
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
    for i in range(10):
        for j in range(10):
            ax.text(j, i, f"{cm[i,j]:.2f}", ha="center", va="center",
                    fontsize=6, color="white" if cm[i, j] > 0.5 else "black")
    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    ax.set_xticklabels(range(10))
    ax.set_yticklabels(FASHION_CLASSES, fontsize=7)
    ax.set_xlabel("K-means cluster")
    ax.set_ylabel("True class")
    ax.set_title(f"{title}\nNMI={nmi:.3f}  ARI={ari:.3f}", fontsize=10)
    plt.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✓ {fname}")

plot_kmeans_confusion(y_km_pixel, nmi_pixel, ari_pixel,
                      "K-means on raw pixels (784D)", "results/kmeans_confusion_pixel.png")
plot_kmeans_confusion(y_km_pca, nmi_pca, ari_pca,
                      "K-means on PCA features (32D)", "results/kmeans_confusion_pca.png")

print(f"\n{'='*50}")
print(f"  PCA 2D  variance: {pca2.explained_variance_ratio_.sum():.2%}")
print(f"  PCA 32D variance: {pca32.explained_variance_ratio_.sum():.2%}")
print(f"  K-means (pixels): NMI={nmi_pixel:.4f}  ARI={ari_pixel:.4f}")
print(f"  K-means (PCA 32D): NMI={nmi_pca:.4f}  ARI={ari_pca:.4f}")
print(f"{'='*50}")
