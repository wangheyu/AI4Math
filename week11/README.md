# Week 11: MNIST 手写数字识别 —— 从 MLP 到 C 推理

## 环境要求

- Python 3 + PyTorch + torchvision（在 `Teaching` conda 环境中）
- GCC（编译 C 推理程序）
- LaTeX（编译教学幻灯片，可选）

```bash
# 安装 PyTorch（如果尚未安装）
pip install torch torchvision

# 下载数据集
bash download_datasets.sh datasets
```

## 项目结构

```
week11/
├── README.md                   # 本文件
├── plan.md                     # 5 阶段计划
├── slide_mlp.tex / .pdf        # 教学幻灯片（27 页）
├── sampling.md                 # 手写采样工具文档
│
├── data.py                     # [库] MNIST 数据加载
├── models.py                   # [库] MLP + CNN 模型定义
├── utils.py                    # [库] 工具函数
│
├── mnist_mlp.py                # 阶段1: MLP 训练/测试
├── mnist_cnn.py                # 阶段2: CNN 训练/测试
│
├── export_mlp_params.py        # 阶段3: 参数导出
├── mnist_mlp_infer.c           # 阶段3: C 语言推理
│
├── sampling.py                 # 交互式手写数字采样
│
├── gen_slide_assets.py         # [辅助] 生成幻灯片素材(MLP)
├── gen_cnn_assets.py           # [辅助] 生成幻灯片素材(CNN)
├── download_datasets.sh        # [辅助] 下载数据集
│
├── checkpoints/                # 训练好的模型参数
├── datasets/                   # MNIST 等数据集
├── params/                     # 导出的文本格式参数
├── samples/                    # 测试样本和手写数字
├── slide_assets/               # 幻灯片插图
└── build/                      # LaTeX 编译中间文件
```

---

## 程序使用说明

### 1. `mnist_mlp.py` — MLP 训练

**功能**：训练一个三层全连接网络（784→128→64→10），在 MNIST 上达到 ~97% 测试准确率。

```bash
conda run -n Teaching python mnist_mlp.py
```

**输入**：`datasets/MNIST`（自动下载）  
**输出**：`checkpoints/mnist_mlp.pt`（109,386 个参数）  
**耗时**：约 1—2 分钟（GPU）  
**依赖**：`data.py`, `models.py`, `utils.py`

---

### 2. `mnist_cnn.py` — CNN 训练

**功能**：训练一个卷积神经网络（2×Conv+Pool → FC），用更少参数（20K vs 109K）达到更高准确率（~99% vs ~97%）。

```bash
conda run -n Teaching python mnist_cnn.py
```

**输入**：`datasets/MNIST`  
**输出**：`checkpoints/mnist_cnn.pt`（20,490 个参数）  
**耗时**：约 2—3 分钟（GPU）  
**依赖**：`data.py`, `models.py`, `utils.py`

---

### 3. `export_mlp_params.py` — 参数导出

**功能**：将 MLP 模型的权重和偏置导出为纯文本，同时导出测试样本。导出的文本可供 C 程序直接读取。

```bash
conda run -n Teaching python export_mlp_params.py
```

**输入**：`checkpoints/mnist_mlp.pt`  
**输出**：
- `params/layer1_weight.txt`（128×784）, `layer1_bias.txt`（128）
- `params/layer2_weight.txt`（64×128）, `layer2_bias.txt`（64）
- `params/layer3_weight.txt`（10×64）, `layer3_bias.txt`（10）
- `samples/sample_0.txt` … `sample_4.txt`（5 张 28×28 测试图片）
- `samples/labels.txt`（对应标签）

**同时自动验证**：用 numpy 重做前向传播，与 PyTorch 结果对比（误差 < 10⁻⁶）。

**依赖**：`models.py`

---

### 4. `mnist_mlp_infer.c` — C 语言推理

**功能**：用纯 C 语言实现 MLP 前向传播（矩阵乘向量 + 偏置 + ReLU + argmax），读取 Python 导出的参数，对输入图片做推理。

```bash
# 编译
gcc -o mnist_mlp_infer mnist_mlp_infer.c -lm -O2

# 运行（需要先运行 export_mlp_params.py 导出参数）
./mnist_mlp_infer samples/sample_0.txt
# 输出: Prediction: 7
```

**输入**：`params/` 中的 6 个参数文件 + 一个 28×28 文本格式图片  
**输出**：终端显示预测类别和各类别 logits  
**依赖**：需先运行 `export_mlp_params.py`

---

### 5. `sampling.py` — 交互式手写采样

**功能**：用鼠标在画布上写数字，生成 28×28 灰度图。支持实时 MLP 预测。

```bash
conda run -n Teaching python sampling.py
```

**操作**：

| 按键/操作 | 功能 |
|-----------|------|
| 左键拖拽 | 书写 |
| 右键拖拽 | 擦除 |
| 滚轮 | 调笔刷大小 |
| `c` | 清空画布 |
| `s` | 保存 PNG（自动编号） |
| `t` | 保存文本（兼容 C 推理） |
| `p` | MLP 模型实时预测 |
| `q` | 退出 |

**输出**：`samples/drawn_000.png`, `drawn_000.txt`, …（自动递增编号）  
**依赖**：需先运行 `mnist_mlp.py`（预测功能需要 `checkpoints/mnist_mlp.pt`）  
**注意**：需要图形界面（X11/Wayland），WSL 用户需配置 X Server。详见 `sampling.md`。

---

### 6. 辅助脚本

| 脚本 | 功能 | 命令 |
|------|------|------|
| `download_datasets.sh` | 下载 MNIST / Fashion-MNIST / KMNIST / CIFAR-10 | `bash download_datasets.sh datasets` |
| `gen_slide_assets.py` | 生成 MLP 教学插图（softmax、交叉熵、梯度下降等） | `conda run -n Teaching python gen_slide_assets.py` |
| `gen_cnn_assets.py` | 生成 CNN 教学插图（卷积演示、核可视化、对比图） | `conda run -n Teaching python gen_cnn_assets.py` |

---

### 7. 幻灯片

```bash
# 编译
latexmk -xelatex -outdir=build -halt-on-error slide_mlp.tex

# 或直接查看预编译版本
# slide_mlp.pdf (27 页)
```

---

## 典型工作流

### 从头开始

```bash
# 1. 下载数据
bash download_datasets.sh datasets

# 2. 训练 MLP
conda run -n Teaching python mnist_mlp.py

# 3. 训练 CNN
conda run -n Teaching python mnist_cnn.py

# 4. 导出参数 + C 推理验证
conda run -n Teaching python export_mlp_params.py
gcc -o mnist_mlp_infer mnist_mlp_infer.c -lm -O2
./mnist_mlp_infer samples/sample_0.txt

# 5. 手写数字交互测试
conda run -n Teaching python sampling.py
```

### 快速测试已有模型

```bash
# 用 C 推理测试手写数字
./mnist_mlp_infer samples/drawn_000.txt

# 或在 Python 中加载模型推理
conda run -n Teaching python -c "
import torch
from models import MLPClassifier
model = MLPClassifier()
model.load_state_dict(torch.load('checkpoints/mnist_mlp.pt'))
model.eval()
# ... 加载图片并推理
"
```

---

## 各阶段对应关系

| 阶段 | 主题 | 主要文件 |
|------|------|---------|
| 1 | MLP 基线 | `mnist_mlp.py`, `data.py`, `models.py`, `utils.py` |
| 2 | CNN 版本 | `mnist_cnn.py`, `models.py` (CNNClassifier) |
| 3 | C 推理 | `export_mlp_params.py`, `mnist_mlp_infer.c` |
| 4 | 泛化（待完成） | `train_classifier.py` |
| 5 | 无监督（待完成） | `pca_kmeans.py`, `autoencoder.py`, … |

详见 `plan.md`。
