# AI4Math

浙江大学数学科学学院 — 人工智能与数学软件课程项目

## 概览

本仓库涵盖六个教学模块，从 C 语言编程、数值计算方法，到深度学习、AI 辅助开发工具和科学仿真，围绕"**用代码学习，用库计算，让 AI 连接两者**"的主线展开。

## 目录

| 模块 | 主题 | 内容 |
|------|------|------|
| **week3** | C 语言与编译基础 | BMP 位图生成、静态/共享库、Doxygen 文档 |
| **week9** | 天体力学数值仿真 | 二体/三体问题、Euler vs Verlet、JPL 星历对比、日食预测 |
| **week10** | AI 辅助开发工具 | Makefile 构建系统、Agent Coding、Claude Code Skills |
| **week11** | MNIST 手写数字识别 | MLP→CNN→C 推理→多数据集泛化→无监督学习 (AE/DAE/VAE) |
| **week12** | 数值计算方法 | LU 分解、3D Poisson 迭代求解、稀疏矩阵 CRS、求解器基准测试、流体可视化 |
| **final_project** | 期末课题 | 钱学森航天著作报告、弯曲空间引力仿真 |

## 快速开始

```bash
# 克隆仓库
git clone <repo-url>
cd AI4Math

# 编译所有讲义和源码
make all

# 各模块独立使用
cd week3  && xelatex slide.tex            # C 语言教学幻灯片
cd week9  && make pdf                      # 天体力学报告
cd week10 && make all                      # AI 工具幻灯片
cd week11 && bash download_datasets.sh datasets && conda run -n Teaching python mnist_mlp.py
cd week12 && ./build.sh build && ./build.sh test
cd final_project/Qian && make all          # 期末论文
```

## 环境要求

- **Python**: `Teaching` conda 环境 (`numpy`, `pandas`, `matplotlib`, `scipy`, `astroquery`)
- **PyTorch**: week11 需要 (`pip install torch torchvision`)
- **LaTeX**: XeLaTeX + xeCJK + Noto CJK 字体（编译讲义和报告）
- **GCC**: week3/week12 C 代码编译 (`gcc -O3 -march=native`)
- **Intel MKL / Eigen**: week12 可选依赖（用于高性能基准测试）

## 许可证

MIT License — 详见 [LICENSE](LICENSE)
