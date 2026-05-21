# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

数值计算方法教学 workspace，包含两个 C 语言数值项目及配套 LaTeX beamer 演示文稿。

## Build commands

**gauss_elimination/** (高斯消去 / LU 分解):
```bash
cd gauss_elimination && make          # 构建所有目标 (test, test_opt, bench_mkl, bench_eigen)
make test && ./test                   # 基础 LU 分解测试
make test_opt && ./test_opt           # 分块 + OpenMP 优化版测试
make bench_mkl && ./bench_mkl 2000    # 基准对比 (n=2000): 原始 C vs 优化 C vs MKL
```

**fdm3d/** (3D 有限差分 Poisson 求解):
```bash
cd fdm3d && make              # 构建 fdm3d, write_mat, read_mat
./write_mat                   # 生成 N=101 的 CRS 稀疏矩阵 → mat.dat (二进制)
./fdm3d                       # SOR/Gauss-Seidel 迭代求解 3D Poisson 方程
```

**LaTeX beamer 编译:**
```bash
xelatex gauss_elimination/gauss_beamer.tex  # 高斯消去法 slides
xelatex fdm3d/iter_beamer.tex              # 迭代法 Poisson 求解 slides
xelatex sparse/sparse_crs_beamer.tex       # 稀疏矩阵 + CRS 格式 slides
```
编译依赖: TeX Live (beamer, xeCJK, listings, tikz), Noto CJK 字体.

## Architecture

### gauss_elimination/ — 两种 LU 分解实现 + 多路基准测试

- **`gauss.c/h`** — 基准实现: kij 右看算法, 列主元, 单核, row-major 存储
  - `gauss_solve()`: 高斯消去求解 Ax=b (覆盖 A)
  - `lu_decomp()` / `lu_decomp_pivot()`: 无/有选主元 LU 分解
  - `lu_solve()` → `forward_subst()` + `backward_subst()`: 前代/回代
- **`gauss_opt.c/h`** — 优化实现: 分块右看 LU + OpenMP 并行 (块大小 nb=128)
  - `lu_decomp_blocked()`: panel LU → dtrsm → dgemm 三级
  - s-i-j 循环序保证内层 stride-1 访存
- **`test.c`**, **`test_opt.c`** — 正确性测试 (随机矩阵 + 已知解验证)
- **`bench_mkl.c`** — 三路对比: 原始 C (单核) vs 优化 C (OMP) vs MKL `dgetrf`
- **`bench_eigen.cpp`** — C++ 对比: Eigen 3.4 `PartialPivLU` (纯头文件, 零链接)
- **`bench_numpy.py`** / **`compare.py`** — Python 参考实现与结果交叉验证

**关键实现细节:** 矩阵均为 `double*` 一维数组, row-major 存储; LU 原位覆盖, L 的严格下三角存乘子, U 在上三角+对角线.

### fdm3d/ — 3D 单位立方体 Poisson 方程 FDM

- **`main.c`** — Gauss-Seidel / SOR 迭代求解 $-\Delta u = f$, 7-点 stencil, Dirichlet BC
  - `IDX(i,j,k)` 宏: 3D → 1D row-major 索引
  - 解 $u(x,y,z)=\sin\pi x \sin\pi y \sin\pi z$, 右端 $f=3\pi^2 u$
- **`write_mat.c`** — 生成稀疏矩阵的 CRS 二进制文件 (`mat.dat`)
  - 文件头: 3×int (m, n, nnz) + 3 个数组 (val double[nnz], col_ind int[nnz], row_ptr int[m+1])
- **`read_mat.c`** — 读取并打印 `mat.dat` 的 CRS 三数组

### visualization/ — AI + OpenGL 科学计算可视化

- **`fluidsim.c/h`** — Stam Stable Fluids 2D 流体求解器: 半拉格朗日平流, GS 扩散, SOR Poisson 投影
  - 投影步求解 2D Poisson 方程 (5-点 stencil → SOR), 与 fdm3d/ 的 3D 7-点 stencil 同框架
  - `fluidsim_export_frame()` 导出二进制帧供 Python 对比
- **`visdemo_x11.c`** — X11+GLX 交互式可视化: OpenGL real-time 渲染, 鼠标添加染料/速度
  - 编译: `gcc -O3 fluidsim.c visdemo_x11.c -lX11 -lGL -lm`
- **`visdemo_headless.c`** — EGL headless 渲染: pbuffer → PPM/FFmpeg 管道
  - 编译: `gcc -O3 fluidsim.c visdemo_headless.c -lEGL -lGL -lm`
- **`compare_anim.py`** — Python+matplotlib 对比基线: 读 C solver 帧数据, 渲染, 对比耗时
- **`record_video.sh`** — headless → FFmpeg 生成 `fluid_sim.mp4`
- **`fluid_beamer.tex`** — Beamer slides (18 frames)

```bash
cd visualization && make          # 编译 visdemo_x11, visdemo_headless
./visdemo_x11 128                # X11 交互式 demo
./visdemo_headless 128 300       # EGL headless, 生成 frame_*.ppm
./visdemo_headless 128 300 - | ffmpeg ...  # 管道模式 → MP4
./run_tests.sh                   # 一键测试
```

### Beamer slides

- `sparse/sparse_crs_beamer.tex` — 稀疏矩阵存储格式, 以 CRS 为例, 含 C 实现 (15 frames)
- `gauss_elimination/gauss_beamer.tex` — 高斯消去法与 LU 分解 (23 frames)
- `fdm3d/iter_beamer.tex` — 迭代法 Poisson 求解 (28 frames)
- `visualization/fluid_beamer.tex` — AI + OpenGL 流体可视化 (18 frames)
- 模板: Copenhagen theme, 16:9, xeCJK (Noto CJK 字体), 使用 `[fragile]` 标记含 lstlisting 的帧

## Notes

- 所有 C 代码编译标志: `gcc -O3 -march=native -Wall -Wextra`
- `bench_mkl` 需 Intel MKL 运行时 (`-lmkl_rt`), 路径通过 `$(CONDA_PREFIX)/lib` 查找
- `bench_eigen` 需 Eigen 3.4 头文件, 路径 `/tmp/eigen-3.4.0`
- 用户交流偏好中文
