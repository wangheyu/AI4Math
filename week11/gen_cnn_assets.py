"""Generate CNN visual assets for slides."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

cjk_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(cjk_path)
cjk = fm.FontProperties(fname=cjk_path)

# ── 1. Convolution operation visualization ──
def gen_conv_viz():
    """Show a 3x3 kernel sliding over a 5x5 input, producing a 3x3 output."""
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.5))

    # Input: 5x5 with a vertical edge pattern
    inp = np.array([
        [0,0,1,1,0],
        [0,0,1,1,0],
        [0,0,1,1,0],
        [0,0,1,1,0],
        [0,0,1,1,0],
    ], dtype=float)

    # Kernel: vertical edge detector
    kernel = np.array([
        [-1, 0, 1],
        [-1, 0, 1],
        [-1, 0, 1],
    ], dtype=float)

    # Positions to show
    positions = [(0,0), (0,1), (0,2)]

    for idx, (r, c) in enumerate(positions):
        ax = axes[idx]
        # Show input
        ax.imshow(inp, cmap="gray_r", vmin=0, vmax=1)
        # Highlight kernel window
        rect = plt.Rectangle((c-0.5, r-0.5), 3, 3, fill=False, edgecolor="red", linewidth=2.5)
        ax.add_patch(rect)
        # Compute convolution at this position
        val = np.sum(inp[r:r+3, c:c+3] * kernel)
        ax.set_title(f"位置 ({r},{c})\n卷积结果={val:.0f}", fontproperties=cjk, fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])

    # 4th: kernel
    ax = axes[3]
    ax.imshow(kernel, cmap="RdBu_r", vmin=-1, vmax=1)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{kernel[i,j]:.0f}", ha="center", va="center", fontsize=11,
                    color="white" if abs(kernel[i,j]) > 0.5 else "black")
    ax.set_title("卷积核（边缘检测）", fontproperties=cjk, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])

    fig.suptitle("卷积操作演示：3×3 核在 5×5 图上滑动，每次计算点积", fontproperties=cjk, fontsize=13)
    plt.tight_layout()
    plt.savefig("slide_assets/conv_demo.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  conv_demo.png")


# ── 2. CNN architecture shape flow ──
def gen_cnn_shapes():
    """Show tensor shapes through CNN layers."""
    fig, ax = plt.subplots(figsize=(13, 3))

    layers = [
        ("输入\n[1,28,28]", 0),
        ("Conv1\n16@28×28", 1),
        ("Pool1\n16@14×14", 2),
        ("Conv2\n32@14×14", 3),
        ("Pool2\n32@7×7", 4),
        ("Flatten\n1568", 5),
        ("Linear\n10类输出", 6),
    ]

    colors = ["#E8F0FF", "#B8D0FF", "#88B0FF", "#60A0FF", "#4090E0", "#3070C0", "#2050A0"]

    for i, (label, pos) in enumerate(layers):
        rect = plt.Rectangle((pos * 1.5, 0), 1.2, 2, fill=True, facecolor=colors[i],
                             edgecolor="black", linewidth=1.5, alpha=0.85)
        ax.add_patch(rect)
        ax.text(pos * 1.5 + 0.6, 1, label, ha="center", va="center",
                fontproperties=cjk, fontsize=9)

        if i < len(layers) - 1:
            ax.annotate("", xy=(pos * 1.5 + 1.2, 1), xytext=(pos * 1.5 + 1.5, 1),
                        arrowprops=dict(arrowstyle="->", color="red", lw=2))

    ax.set_xlim(-0.2, 11)
    ax.set_ylim(-0.3, 2.3)
    ax.axis("off")
    ax.set_title("CNN 张量形状变化：28×28 灰度图 → 7×7×32 特征图 → 10 类输出",
                 fontproperties=cjk, fontsize=13)
    plt.tight_layout()
    plt.savefig("slide_assets/cnn_shapes.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  cnn_shapes.png")


# ── 3. MLP vs CNN comparison bar chart ──
def gen_mlp_cnn_compare():
    """Compare MLP and CNN on params and accuracy."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))

    # Parameters
    models = ["MLP", "CNN"]
    params = [109386, 20490]
    colors_bar = ["#4080C0", "#40A060"]
    ax1.bar(models, params, color=colors_bar, edgecolor="black")
    ax1.set_title("参数量对比", fontproperties=cjk, fontsize=12)
    ax1.set_ylabel("参数个数", fontproperties=cjk)
    for i, v in enumerate(params):
        ax1.text(i, v + 2000, f"{v:,}", ha="center", fontproperties=cjk, fontsize=11, fontweight="bold")

    # Accuracy
    acc = [97.44, 98.88]
    ax2.bar(models, acc, color=colors_bar, edgecolor="black")
    ax2.set_title("测试准确率对比", fontproperties=cjk, fontsize=12)
    ax2.set_ylabel("准确率 (%)", fontproperties=cjk)
    ax2.set_ylim(96, 100)
    for i, v in enumerate(acc):
        ax2.text(i, v + 0.05, f"{v:.2f}%", ha="center", fontproperties=cjk, fontsize=11, fontweight="bold")

    fig.suptitle("MLP vs CNN：参数少 81%，准确率反而更高", fontproperties=cjk, fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig("slide_assets/mlp_cnn_compare.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  mlp_cnn_compare.png")


# ── 4. Kernel weight visualization (first CNN layer) ──
def gen_cnn_kernels():
    """Visualize the 16 kernels of the first Conv2d layer."""
    import torch
    import sys
    sys.path.insert(0, "/home/hywang/Projects/AI4Math/week11")
    from models import CNNClassifier

    model = CNNClassifier()
    ckpt = torch.load("checkpoints/mnist_cnn.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(ckpt)

    # First conv layer: (16, 1, 3, 3)
    kernels = model.net[0].weight.data.numpy()

    fig, axes = plt.subplots(2, 8, figsize=(12, 3.8))
    for i in range(16):
        ax = axes[i // 8][i % 8]
        k = kernels[i, 0]  # shape (3, 3)
        im = ax.imshow(k, cmap="RdBu_r", vmin=-0.5, vmax=0.5)
        for r in range(3):
            for c in range(3):
                ax.text(c, r, f"{k[r,c]:.2f}", ha="center", va="center", fontsize=6,
                        color="white" if abs(k[r,c]) > 0.3 else "black")
        ax.set_title(f"核{i+1}", fontproperties=cjk, fontsize=7)
        ax.set_xticks([])
        ax.set_yticks([])

    cbar = fig.colorbar(im, ax=axes, shrink=0.7)
    cbar.ax.set_ylabel("权重值", fontproperties=cjk, fontsize=9)
    fig.suptitle("第一卷积层：16 个 3×3 卷积核（训练自动学到的边缘/纹理检测器）",
                 fontproperties=cjk, fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig("slide_assets/cnn_kernels.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  cnn_kernels.png")


# ── Run ──
if __name__ == "__main__":
    gen_conv_viz()
    gen_cnn_shapes()
    gen_mlp_cnn_compare()
    gen_cnn_kernels()
    print("\nAll CNN assets generated.")
