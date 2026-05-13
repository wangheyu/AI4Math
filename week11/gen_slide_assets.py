"""
Generate visual assets for slide_mlp.tex:
  - MNIST digit samples (one per class)
  - Weight matrix heatmaps (first Linear layer)
  - Training curve
"""
import os
import torch
import torch.nn as nn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from torchvision import datasets, transforms
from models import MLPClassifier

os.makedirs("slide_assets", exist_ok=True)

# Use DejaVu Sans for English labels (avoids CJK font issues in matplotlib)
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


# ── 1. MNIST digit samples ──
def gen_mnist_samples():
    """Save one sample image per digit class as a 28x28 grayscale PNG."""
    transform = transforms.ToTensor()
    ds = datasets.MNIST(root="datasets", train=True, download=False, transform=transform)

    found = {}
    for img, label in ds:
        if label not in found:
            found[label] = img
        if len(found) == 10:
            break

    fig, axes = plt.subplots(2, 5, figsize=(8, 3.6))
    for i in range(10):
        ax = axes[i // 5][i % 5]
        ax.imshow(found[i][0], cmap="gray")
        ax.set_title(f"Label: {i}", fontsize=11)
        ax.axis("off")
    plt.tight_layout(pad=0.5)
    plt.savefig("slide_assets/mnist_samples.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ slide_assets/mnist_samples.png")

    # Also save individual digits at higher resolution
    for i in range(10):
        fig, ax = plt.subplots(figsize=(1.2, 1.2))
        ax.imshow(found[i][0], cmap="gray")
        ax.axis("off")
        plt.subplots_adjust(0, 0, 1, 1)
        plt.savefig(f"slide_assets/digit_{i}.png", dpi=100, bbox_inches="tight")
        plt.close()
    print("✓ slide_assets/digit_0..9.png")


# ── 2. Weight matrix heatmap ──
def gen_weight_heatmap():
    """Load trained MLP and visualize first Linear layer weights."""
    # Switch to CJK font for Chinese labels in this figure
    cjk_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    if os.path.exists(cjk_path):
        fm.fontManager.addfont(cjk_path)
        cjk_prop = fm.FontProperties(fname=cjk_path)
        plt.rcParams["font.family"] = cjk_prop.get_name()

    model = MLPClassifier()
    ckpt = torch.load("checkpoints/mnist_mlp.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(ckpt)

    # First layer: (128, 784) — visualize first 32 neurons as 28x28 images
    w = model.net[1].weight.data.numpy()  # (128, 784)
    n_neurons = 32
    # Wider figure + constrained_layout to prevent colorbar/image overlap
    fig, axes = plt.subplots(4, 8, figsize=(14, 7.5), constrained_layout=True)
    for i in range(n_neurons):
        ax = axes[i // 8][i % 8]
        w_img = w[i].reshape(28, 28)
        im = ax.imshow(w_img, cmap="RdBu_r", vmin=-0.3, vmax=0.3)
        ax.axis("off")
        ax.set_title(f"神经元 {i+1}", fontsize=8)

    # Colorbar with proper padding to avoid overlap
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.7, pad=0.02, label="权重值")
    cbar.ax.yaxis.label.set_size(10)

    fig.suptitle("第一隐藏层：128 个神经元中的 32 个权重可视化\n"
                 "红色 = 正权重（兴奋），蓝色 = 负权重（抑制）\n"
                 "每个图案展示了该神经元检测的特征形状",
                 fontsize=12, y=1.02)
    plt.savefig("slide_assets/weight_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Restore English font for subsequent figures
    plt.rcParams["font.family"] = "DejaVu Sans"
    print("✓ slide_assets/weight_heatmap.png")


# ── 3. Training curves ──
def gen_training_curve():
    """Generate hypothetical training curves for illustration."""
    # Simulate typical MLP training curves
    epochs = np.arange(1, 11)
    train_loss = [0.33, 0.14, 0.09, 0.07, 0.05, 0.04, 0.036, 0.029, 0.024, 0.021]
    test_loss = [0.17, 0.11, 0.098, 0.092, 0.081, 0.089, 0.087, 0.076, 0.090, 0.095]
    train_acc = [0.906, 0.960, 0.971, 0.978, 0.983, 0.986, 0.988, 0.991, 0.992, 0.993]
    test_acc = [0.948, 0.966, 0.969, 0.972, 0.975, 0.973, 0.975, 0.979, 0.977, 0.974]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5))

    ax1.plot(epochs, train_loss, "b-o", label="Train Loss", markersize=6)
    ax1.plot(epochs, test_loss, "r-s", label="Test Loss", markersize=6)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Loss Curve")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(epochs, train_acc, "b-o", label="Train Acc", markersize=6)
    ax2.plot(epochs, test_acc, "r-s", label="Test Acc", markersize=6)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.set_title("Accuracy Curve")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("slide_assets/training_curves.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ slide_assets/training_curves.png")


# ── 4. Single digit with pixel grid annotation ──
def gen_digit_grid():
    """Show digit '7' with pixel values annotated on a grid."""
    transform = transforms.ToTensor()
    ds = datasets.MNIST(root="datasets", train=True, download=False, transform=transform)

    # Find a clear '7'
    for img, label in ds:
        if label == 7:
            digit_7 = img
            break

    # Subsample to ~14x14 for readability
    img_small = digit_7[0, ::2, ::2].numpy()
    h, w = img_small.shape

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(img_small, cmap="gray")
    for i in range(h):
        for j in range(w):
            val = img_small[i, j]
            color = "white" if val < 0.5 else "black"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    fontsize=7, color=color)
    ax.set_title("Digit '7' Pixel Values (14x14 subsample)\nEach cell = one input neuron", fontsize=11)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("slide_assets/digit_grid.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ slide_assets/digit_grid.png")


# ── 5. Softmax visualization ──
def gen_softmax_viz():
    """Visualize logits → softmax → prediction."""
    np.random.seed(42)
    logits = np.array([0.2, 0.3, 0.1, 0.8, 0.1, 0.3, 0.2, 2.8, 0.2, 0.1])
    exp_logits = np.exp(logits)
    probs = exp_logits / exp_logits.sum()

    fig, axes = plt.subplots(1, 2, figsize=(9, 3))

    colors = ["gray"] * 10
    colors[7] = "C3"

    axes[0].bar(range(10), logits, color=colors, edgecolor="black")
    axes[0].set_title("Logits (raw model output)", fontsize=12)
    axes[0].set_xlabel("Class")
    axes[0].set_ylabel("Score")
    axes[0].set_xticks(range(10))
    axes[0].axhline(y=0, color="black", linewidth=0.5)

    axes[1].bar(range(10), probs, color=colors, edgecolor="black")
    axes[1].set_title("After Softmax -> Probability Distribution", fontsize=12)
    axes[1].set_xlabel("Class")
    axes[1].set_ylabel("Probability")
    axes[1].set_xticks(range(10))
    axes[1].set_ylim(0, 1)

    # Annotate the max
    axes[1].annotate(f"Pred=7\np={probs[7]:.2f}",
                     xy=(7, probs[7]), xytext=(8.5, 0.7),
                     arrowprops=dict(arrowstyle="->"), fontsize=11)

    plt.tight_layout()
    plt.savefig("slide_assets/softmax_viz.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ slide_assets/softmax_viz.png")


# ── 6. Cross-entropy intuitive visualization ──
def gen_crossentropy_viz():
    """Show true distribution vs predicted distribution."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))

    digits = range(10)
    true = np.zeros(10)
    true[7] = 1.0  # true label is 7

    # Scenario A: confident & correct
    pred_good = np.ones(10) * 0.01
    pred_good[7] = 0.85
    pred_good = pred_good / pred_good.sum()

    # Scenario B: uncertain
    pred_ok = np.ones(10) * 0.05
    pred_ok[7] = 0.35
    pred_ok[3] = 0.20
    pred_ok = pred_ok / pred_ok.sum()

    # Scenario C: wrong
    pred_bad = np.ones(10) * 0.05
    pred_bad[3] = 0.80
    pred_bad = pred_bad / pred_bad.sum()

    scenarios = [
        ("Confident & Correct", pred_good, 0.16),
        ("Uncertain", pred_ok, 1.05),
        ("Confident but WRONG", pred_bad, 2.99),
    ]

    for ax, (title, pred, loss_val) in zip(axes, scenarios):
        ax.bar(digits, pred, color=["C3" if i == 7 else "C0" if pred[i] < 0.1 else "C2"
                                     for i in range(10)], edgecolor="black")
        ax.set_xticks(digits)
        ax.set_ylim(0, 1)
        ax.set_title(f"{title}\nLoss = {loss_val:.2f}", fontsize=11)
        ax.set_xlabel("Class")
        ax.set_ylabel("Predicted Prob.")

    plt.suptitle("Cross-Entropy Loss: Intuition", fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig("slide_assets/crossentropy_viz.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ slide_assets/crossentropy_viz.png")


# ── 7. Gradient descent landscape ──
def gen_gd_landscape():
    """3D-like 2D contour of loss landscape with gradient descent path."""
    np.random.seed(42)

    # Create a simple loss landscape: f(w1, w2) = w1^2 + 3*w2^2 + sin(w1)*cos(w2)
    w1 = np.linspace(-3, 3, 100)
    w2 = np.linspace(-3, 3, 100)
    W1, W2 = np.meshgrid(w1, w2)
    Z = W1**2 + 3*W2**2 + 0.5*np.sin(3*W1)*np.cos(3*W2)

    # Simulate GD path
    pos = np.array([2.5, 2.0])
    lr = 0.1
    path = [pos.copy()]
    for _ in range(20):
        grad = np.array([2*pos[0] + 1.5*np.cos(3*pos[0])*np.cos(3*pos[1]),
                         6*pos[1] - 1.5*np.sin(3*pos[0])*np.sin(3*pos[1])])
        pos = pos - lr * grad
        path.append(pos.copy())
    path = np.array(path)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    cs = ax.contour(W1, W2, Z, levels=20, cmap="Blues", alpha=0.6)
    ax.clabel(cs, inline=True, fontsize=7, fmt="%.0f")
    ax.plot(path[:, 0], path[:, 1], "r-o", markersize=5, linewidth=2,
            label="GD path")
    ax.plot(path[0, 0], path[0, 1], "go", markersize=12, label="Start")
    ax.plot(path[-1, 0], path[-1, 1], "r*", markersize=15, label="Optimum")
    ax.set_xlabel("Parameter $w_1$", fontsize=12)
    ax.set_ylabel("Parameter $w_2$", fontsize=12)
    ax.set_title("Gradient Descent: Finding the Minimum on Loss Landscape", fontsize=13)
    ax.legend(fontsize=10)
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig("slide_assets/gd_landscape.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ slide_assets/gd_landscape.png")


# ── 8. Batch GD vs SGD vs Mini-batch illustration ──
def gen_gd_comparison():
    """Illustrate the difference between GD, SGD, and Mini-batch GD."""
    np.random.seed(42)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))

    # Same landscape as above
    w1 = np.linspace(-3, 3, 80)
    w2 = np.linspace(-3, 3, 80)
    W1, W2 = np.meshgrid(w1, w2)
    Z = W1**2 + 3*W2**2 + 0.5*np.sin(3*W1)*np.cos(3*W2)

    titles = [
        "Batch Gradient Descent\nAll data, smooth path",
        "Stochastic GD (SGD)\n1 sample, noisy path",
        "Mini-batch GD\n64 samples, balanced",
    ]

    # Batch GD — smooth path
    pos = np.array([2.5, 2.0])
    lr_batch = 0.1
    path_batch = [pos.copy()]
    for _ in range(15):
        grad = np.array([2*pos[0] + 1.5*np.cos(3*pos[0])*np.cos(3*pos[1]),
                         6*pos[1] - 1.5*np.sin(3*pos[0])*np.sin(3*pos[1])])
        pos = pos - lr_batch * grad
        path_batch.append(pos.copy())
    path_batch = np.array(path_batch)

    # SGD — noisy path
    pos = np.array([2.5, 2.0])
    lr_sgd = 0.08
    path_sgd = [pos.copy()]
    for _ in range(25):
        grad = np.array([2*pos[0] + 1.5*np.cos(3*pos[0])*np.cos(3*pos[1]),
                         6*pos[1] - 1.5*np.sin(3*pos[0])*np.sin(3*pos[1])])
        noise = np.random.randn(2) * 1.2
        pos = pos - lr_sgd * (grad + noise)
        path_sgd.append(pos.copy())
    path_sgd = np.array(path_sgd)

    # Mini-batch — mildly noisy path
    pos = np.array([2.5, 2.0])
    lr_mb = 0.1
    path_mb = [pos.copy()]
    for _ in range(18):
        grad = np.array([2*pos[0] + 1.5*np.cos(3*pos[0])*np.cos(3*pos[1]),
                         6*pos[1] - 1.5*np.sin(3*pos[0])*np.sin(3*pos[1])])
        noise = np.random.randn(2) * 0.4
        pos = pos - lr_mb * (grad + noise)
        path_mb.append(pos.copy())
    path_mb = np.array(path_mb)

    paths = [path_batch, path_sgd, path_mb]
    colors_path = ["C3", "C1", "C4"]

    for ax, title, path, cp in zip(axes, titles, paths, colors_path):
        ax.contour(W1, W2, Z, levels=15, cmap="Blues", alpha=0.5)
        ax.plot(path[:, 0], path[:, 1], f"{cp}-o", markersize=4, linewidth=1.8)
        ax.plot(path[0, 0], path[0, 1], "go", markersize=10)
        ax.plot(path[-1, 0], path[-1, 1], "r*", markersize=12)
        ax.set_title(title, fontsize=10)
        ax.set_xlim(-3, 3)
        ax.set_ylim(-3, 3)
        ax.set_xlabel("$w_1$")
        ax.set_ylabel("$w_2$")
        ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig("slide_assets/gd_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ slide_assets/gd_comparison.png")


# ── Run all ──
if __name__ == "__main__":
    gen_mnist_samples()
    gen_weight_heatmap()
    gen_training_curve()
    gen_digit_grid()
    gen_softmax_viz()
    gen_crossentropy_viz()
    gen_gd_landscape()
    gen_gd_comparison()
    print("\nAll assets generated in slide_assets/")
