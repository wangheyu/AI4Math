"""
导出 MLP 训练参数为文本格式，供 C 语言推理使用。
----------------------------------------------
从 checkpoints/mnist_mlp.pt 读取 state_dict，
将每层的 weight 和 bias 保存为纯文本文件。
同时从 MNIST 测试集导出若干图像样本。

输出目录:
    params/    — 权重和偏置文本文件
    samples/   — 测试图像样本和标签
"""

import os
import torch
from torchvision import datasets, transforms
from models import MLPClassifier

os.makedirs("params", exist_ok=True)
os.makedirs("samples", exist_ok=True)


def export_params() -> None:
    """加载训练好的 MLP 参数，导出为文本文件。"""
    model = MLPClassifier()
    state = torch.load("checkpoints/mnist_mlp.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(state)

    # 三层 Linear 的参数: net.0=Flatten, net.1=Linear1, net.3=Linear2, net.5=Linear3
    layers = [
        ("layer1", model.net[1]),   # 784 -> 128
        ("layer2", model.net[3]),   # 128 -> 64
        ("layer3", model.net[5]),   # 64 -> 10
    ]

    for name, layer in layers:
        w = layer.weight.data.numpy()  # shape: (out, in)
        b = layer.bias.data.numpy()    # shape: (out,)

        out_dim, in_dim = w.shape
        # 权重: 每行一个输出神经元的权重向量
        with open(f"params/{name}_weight.txt", "w") as f:
            f.write(f"# {name} weight: {out_dim} x {in_dim}\n")
            for i in range(out_dim):
                line = " ".join(f"{w[i, j]:.8g}" for j in range(in_dim))
                f.write(line + "\n")

        # 偏置: 每个输出一个值
        with open(f"params/{name}_bias.txt", "w") as f:
            f.write(f"# {name} bias: {out_dim}\n")
            line = " ".join(f"{b[i]:.8g}" for i in range(out_dim))
            f.write(line + "\n")

        print(f"  params/{name}_weight.txt  ({out_dim} x {in_dim})")
        print(f"  params/{name}_bias.txt    ({out_dim})")

    print(f"\nParameters exported to params/")


def export_samples(n: int = 5) -> None:
    """从 MNIST 测试集导出 n 张图片为文本，同时生成标签文件。"""
    transform = transforms.ToTensor()
    ds = datasets.MNIST(root="datasets", train=False, download=True, transform=transform)

    # 取前 n 张
    for idx in range(n):
        img, label = ds[idx]
        pixels = img.flatten().numpy()  # 784 个 [0,1] 的浮点数

        with open(f"samples/sample_{idx}.txt", "w") as f:
            f.write(f"# MNIST test sample {idx}, label={label}\n")
            for i in range(28):
                row = " ".join(f"{pixels[i * 28 + j]:.4f}" for j in range(28))
                f.write(row + "\n")

        print(f"  samples/sample_{idx}.txt  (label={label})")

    # 同时导出标签文件
    with open("samples/labels.txt", "w") as f:
        for idx in range(n):
            _, label = ds[idx]
            f.write(f"{label}\n")

    print(f"\n{n} samples exported to samples/")


def verify_export() -> None:
    """验证：用 Python 重新加载文本参数并做推理，与原始模型结果对比。"""
    import numpy as np

    # 从文本加载参数
    def load_layer(name, in_dim, out_dim):
        w = np.loadtxt(f"params/{name}_weight.txt", skiprows=1)
        b = np.loadtxt(f"params/{name}_bias.txt", skiprows=1)
        return w, b

    w1, b1 = load_layer("layer1", 784, 128)
    w2, b2 = load_layer("layer2", 128, 64)
    w3, b3 = load_layer("layer3", 64, 10)

    # 加载第一个样本
    pixels = np.loadtxt(f"samples/sample_0.txt", skiprows=1).flatten()

    # Python numpy 前向传播（模拟 C 推理将做的事情）
    def relu(x):
        return np.maximum(0, x)

    h1 = relu(w1 @ pixels + b1)
    h2 = relu(w2 @ h1 + b2)
    logits = w3 @ h2 + b3
    pred = np.argmax(logits)

    # 用 PyTorch 模型做同样的推理
    import torch
    model = MLPClassifier()
    state = torch.load("checkpoints/mnist_mlp.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    with torch.no_grad():
        x = torch.from_numpy(pixels).float().view(1, 1, 28, 28)
        torch_logits = model(x).numpy().flatten()
        torch_pred = torch_logits.argmax()

    # 比较
    logit_diff = np.abs(logits - torch_logits).max()
    print(f"\nVerification on sample_0:")
    print(f"  Numpy pred: {pred},  logits: {logits}")
    print(f"  Torch pred: {torch_pred}, logits: {torch_logits}")
    print(f"  Max logit diff: {logit_diff:.2e}")
    print(f"  Match: {'OK' if pred == torch_pred and logit_diff < 1e-5 else 'FAIL'}")


if __name__ == "__main__":
    print("Exporting MLP parameters...")
    export_params()
    print("\nExporting test samples...")
    export_samples(5)
    print("\nVerifying exported parameters...")
    verify_export()
