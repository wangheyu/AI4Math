"""Generate sample grid images for Fashion-MNIST, KMNIST, and CIFAR-10 for slides."""
import os
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from torchvision import datasets, transforms

os.makedirs("slide_assets", exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

# Class names for each dataset
FASHION_CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
                   "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]

KMNIST_CLASSES = [u"お", u"き", u"す", u"つ", u"な",
                  u"は", u"ま", u"や", u"れ", u"を"]
# Romaji labels for KMNIST for readability
KMNIST_ROM = ["o", "ki", "su", "tsu", "na", "ha", "ma", "ya", "re", "wo"]

CIFAR10_CLASSES = ["airplane", "auto", "bird", "cat", "deer",
                   "dog", "frog", "horse", "ship", "truck"]


def gen_dataset_samples(dataset_name, class_names, out_name, root="datasets",
                        train=True, resize=None):
    """Save a 2x5 grid of one sample per class."""
    transform_list = []
    if resize:
        transform_list.append(transforms.Resize(resize))
    transform_list.append(transforms.ToTensor())
    transform = transforms.Compose(transform_list)

    dataset_cls = getattr(datasets, dataset_name)
    ds = dataset_cls(root=root, train=train, download=False, transform=transform)

    found = {}
    for img, label in ds:
        if label not in found:
            found[label] = img
        if len(found) == 10:
            break

    fig, axes = plt.subplots(2, 5, figsize=(10, 4.5))
    for i in range(10):
        ax = axes[i // 5][i % 5]
        img_tensor = found[i]
        if img_tensor.shape[0] == 1:
            ax.imshow(img_tensor[0], cmap="gray")
        else:
            ax.imshow(img_tensor.permute(1, 2, 0))
        label_text = class_names[i] if class_names else str(i)
        ax.set_title(f"{label_text}", fontsize=10)
        ax.axis("off")
    plt.tight_layout(pad=0.8)
    plt.savefig(f"slide_assets/{out_name}", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✓ slide_assets/{out_name}")


def gen_combined_samples():
    """Generate one row per dataset (4 rows, 10 classes each) as a combined overview."""
    datasets_info = [
        ("MNIST", datasets.MNIST, None, False, [str(i) for i in range(10)]),
        ("FashionMNIST", datasets.FashionMNIST, None, False, FASHION_CLASSES),
        ("KMNIST", datasets.KMNIST, None, False, KMNIST_ROM),
        ("CIFAR10", datasets.CIFAR10, (28, 28), False, CIFAR10_CLASSES),
    ]

    fig, axes = plt.subplots(4, 10, figsize=(18, 6.5))
    for row_idx, (ds_name, ds_cls, resize, train, labels) in enumerate(datasets_info):
        transform_list = []
        if resize:
            transform_list.append(transforms.Resize(resize))
        transform_list.append(transforms.ToTensor())
        transform = transforms.Compose(transform_list)

        ds = ds_cls(root="datasets", train=train, download=False, transform=transform)
        found = {}
        for img, label in ds:
            if label not in found:
                found[label] = img
            if len(found) == 10:
                break

        for col_idx in range(10):
            ax = axes[row_idx][col_idx]
            img_tensor = found.get(col_idx)
            if img_tensor is None:
                ax.axis("off")
                continue
            if img_tensor.shape[0] == 1:
                ax.imshow(img_tensor[0], cmap="gray")
            else:
                ax.imshow(img_tensor.permute(1, 2, 0))
            if row_idx == 0:
                ax.set_title(labels[col_idx], fontsize=6)
            if col_idx == 0:
                ax.set_ylabel(ds_name, fontsize=8, fontweight="bold")
            ax.set_xticks([])
            ax.set_yticks([])

    plt.subplots_adjust(wspace=0.12, hspace=0.2)
    plt.savefig("slide_assets/all_datasets_overview.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ slide_assets/all_datasets_overview.png")


if __name__ == "__main__":
    gen_dataset_samples("FashionMNIST", FASHION_CLASSES, "fashion_mnist_samples.png")
    gen_dataset_samples("KMNIST", KMNIST_ROM, "kmnist_samples.png")
    gen_dataset_samples("CIFAR10", CIFAR10_CLASSES, "cifar10_samples.png", resize=(28, 28))
    gen_combined_samples()
    print("\nAll dataset sample images generated in slide_assets/")
