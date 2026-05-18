# 数值计算方法教学

围绕"AI + 计算库 跨越计算软件"这一主线，以**线性方程组求解**为载体展开的教学项目。包含三份独立讲义和与之对应的可运行实验代码。

## 主线问题

> **在以学习和科研为目的的具体计算问题上，能否跨越计算软件 (NumPy/SciPy/Matlab)，通过 AI 直接调用计算库 (MKL/OpenBLAS/Eigen)，获得不低于软件的效率？**

三个子项目分别从**直接法**、**迭代法**、**稀疏矩阵存储**三个角度展开。

## 目录结构

```
Claude-working/
├── README.md                 本文件
├── Makefile                  顶层统一编译/清理入口
├── build.sh                  友好的 shell 包装 (build/test/pdf/clean/...)
├── CLAUDE.md                 项目指南 (给 Claude Code 的上下文)
├── claude-record.md          会话记录历史
│
├── gauss_elimination/        子项目 1: 直接法
│   ├── README.md             子目录说明
│   ├── gauss_beamer.tex      讲义 (20 帧): AI 角色与高斯消去/LU
│   ├── gauss.c / gauss_opt.c 原始 + 分块 OpenMP 优化的 LU
│   ├── bench_mkl.c           AI 调 Intel MKL dgetrf
│   ├── bench_eigen.cpp       Eigen 3.4 PartialPivLU
│   ├── bench_numpy.py        NumPy/SciPy 基线
│   ├── compare.py            5 次 trim-mean 综合对照
│   ├── Makefile / run_tests.sh
│   └── results_*.txt         实验数据
│
├── fdm3d/                    子项目 2: 迭代法 + 大规模稀疏
│   ├── README.md
│   ├── iter_beamer.tex       讲义 (27 帧): 迭代法与稀疏矩阵求解
│   ├── main.c                3D Poisson SOR (stencil)
│   ├── jacobi.c / sor_scan.c
│   ├── bench_pardiso.c       AI 调 MKL PARDISO
│   ├── bench_iter.py         scipy.sparse cg/gmres/spsolve
│   ├── plot_solution.py      matplotlib 可视化
│   ├── write_mat.c / read_mat.c / mat.dat  CRS 矩阵 IO
│   ├── Makefile / run_tests.sh
│   ├── results_*.txt / conv_*.txt
│   └── *.png                 解切片 + 收敛曲线 + omega 扫描
│
└── sparse/                   子项目 3: 稀疏矩阵存储 + CRS 教学实现
    ├── README.md
    ├── sparse_crs_beamer.tex 讲义 (16 帧): 稀疏矩阵与 CRS
    ├── csr.h / csr.c         教学级 CRS 数据结构 + 6 个核心操作
    ├── csr_demo.c            frame 13 端到端示例
    ├── csr_test.c            6 项单元测试 (11 个 CHECK)
    ├── Makefile / run_tests.sh
    └── sparse_crs_beamer.pdf
```

## 三份讲义

| 讲义 | 帧数 | 主题 | 路径 |
|---|---|---|---|
| **高斯消去与 LU 分解** | 20 | 直接法; 单线程 / 多核 / MKL 三版 vs NumPy/SciPy | `gauss_elimination/gauss_beamer.pdf` |
| **迭代法与稀疏矩阵求解** | 27 | 3D Poisson FDM; Jacobi/GS/SOR 最优 omega; AI 调 PARDISO; 可视化 | `fdm3d/iter_beamer.pdf` |
| **稀疏矩阵与 CRS 存储格式** | 16 | CRS 三数组 + SpMV + COO→CSR + 前代/回代/转置 + C 实现 | `sparse/sparse_crs_beamer.pdf` |

## 顶层编译入口

### 方式 A: Makefile

```bash
make all          # 编译三个子项目的所有 C/C++ 程序 + 讲义
make test         # 在每个子目录跑 run_tests.sh
make pdf          # 仅编译讲义 PDF
make clean        # 清理可执行与编译产物 (保留实验结果与 PDF)
make distclean    # 清除一切 (包括实验结果和 PDF)
make status       # 列出各子目录关键产物状态
make help         # 帮助
```

### 方式 B: build.sh (友好接口)

```bash
./build.sh build      # = make all
./build.sh test       # = make test
./build.sh pdf        # = make pdf
./build.sh clean      # = make clean
./build.sh distclean  # = make distclean (有交互式确认)
./build.sh status     # 状态总览
./build.sh help       # 帮助
```

## 子目录独立使用

每个子目录都有独立的 `Makefile` 和 `run_tests.sh`，可单独使用:

```bash
cd gauss_elimination && ./run_tests.sh
cd fdm3d              && ./run_tests.sh
cd sparse             && ./run_tests.sh
```

## 依赖

| 组件 | 用途 | 必需性 |
|---|---|---|
| gcc + glibc + libm                | 基础 C 编译                  | 必需 |
| GCC OpenMP (libgomp)              | `gauss_opt.c` / 多核基准      | 必需 (gauss_elimination, fdm3d) |
| Intel MKL (libmkl\_rt)            | `bench_mkl` / `bench_pardiso` | 可选 (本机用 conda intel-mkl) |
| Eigen 3.4 头文件                  | `bench_eigen.cpp`             | 可选 (`/tmp/eigen-3.4.0/` 缺失则跳过) |
| Python 3 + NumPy + SciPy          | `bench_numpy.py` / `bench_iter.py` / `compare.py` | 必需 (Python 基线) |
| matplotlib                        | `plot_solution.py`            | 可选 (`--no-plot` 跳过) |
| TeX Live (xelatex + xeCJK + Noto CJK) | 编译讲义 PDF              | 可选 (跳过则只有 .tex) |

## 主线论证 (跨三个讲义)

1. **gauss\_beamer**: 直接法上, AI+MKL 的耗时与 NumPy/SciPy (链 MKL) 同数量级, AI 路径反而略快 (无 Python wrapper 开销)。
2. **iter\_beamer**: 大规模稀疏问题中, 直接法 (SuperLU) OOM, 必须用迭代法; AI+C+SOR 与 scipy.cg 同数量级; AI 路径优势是"自由换库 + 算法可控"。
3. **sparse\_crs\_beamer**: CRS 的行布局正是为迭代法的"按行遍历"模式设计的, 两者契合不是巧合。

> **总结 slogan**: 写代码来学习。用库来计算。让 AI 连接两者。
