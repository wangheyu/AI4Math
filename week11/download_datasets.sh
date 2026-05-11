#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-datasets}"
CURL_ARGS=(-L --fail --connect-timeout 20 --speed-limit 1024 --speed-time 30 --retry 2 --retry-delay 2)

download() {
  local url="$1"
  local dest="$2"

  mkdir -p "$(dirname "$dest")"
  if [ -s "$dest" ]; then
    echo "exists: $dest"
    return
  fi

  echo "download: $url"
  curl "${CURL_ARGS[@]}" -o "$dest" "$url"
}

download_mnist_like() {
  local name="$1"
  local base_url="$2"
  local dir="$ROOT/$name/raw"

  download "$base_url/train-images-idx3-ubyte.gz" "$dir/train-images-idx3-ubyte.gz"
  download "$base_url/train-labels-idx1-ubyte.gz" "$dir/train-labels-idx1-ubyte.gz"
  download "$base_url/t10k-images-idx3-ubyte.gz" "$dir/t10k-images-idx3-ubyte.gz"
  download "$base_url/t10k-labels-idx1-ubyte.gz" "$dir/t10k-labels-idx1-ubyte.gz"

  gzip -dkf "$dir"/*.gz
}

download_mnist_like "MNIST" "https://storage.googleapis.com/cvdf-datasets/mnist"
download_mnist_like "FashionMNIST" "https://github.com/zalandoresearch/fashion-mnist/raw/master/data/fashion"

echo "download: KMNIST parquet fallback from Hugging Face"
mkdir -p "$ROOT/KMNIST/parquet"
download "https://huggingface.co/datasets/tanganke/kmnist/resolve/main/kmnist/train-00000-of-00001.parquet" "$ROOT/KMNIST/parquet/train-00000-of-00001.parquet"
download "https://huggingface.co/datasets/tanganke/kmnist/resolve/main/kmnist/test-00000-of-00001.parquet" "$ROOT/KMNIST/parquet/test-00000-of-00001.parquet"

download "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz" "$ROOT/CIFAR10/cifar-10-python.tar.gz"
tar -xzf "$ROOT/CIFAR10/cifar-10-python.tar.gz" -C "$ROOT/CIFAR10"

echo
echo "Downloaded datasets under: $ROOT"
find "$ROOT" -maxdepth 3 -type f -printf "%p\t%k KB\n" | sort
