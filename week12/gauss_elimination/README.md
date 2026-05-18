# gauss_elimination — 直接法 (高斯消去 / LU 分解)

子项目 1: 围绕直接法展开, 展示**AI + MKL/Eigen/OpenBLAS vs NumPy/SciPy** 在稠密 LU 分解上的性能对照。

## 主题

> **AI 直接调用计算库, 能否获得不低于 NumPy/SciPy 的性能?**

讲义共 20 帧, 通过三版 C 实现 (单线程 → 分块+OMP → MKL) 与 NumPy/SciPy 基线的对照来论证。

## 文件清单

### 源码 — C/C++ 实现

| 文件 | 说明 |
|---|---|
| `gauss.c` / `gauss.h` | 基线 LU 分解: kij 右看算法 + 列主元, 单核 row-major |
| `gauss_opt.c` / `gauss_opt.h` | 优化版: 分块 LU (nb=128) + OpenMP + s-i-j stride-1 dgemm |
| `bench_mkl.c` | AI 调 Intel MKL: 直接用 `extern void dgetrf_`, 无头文件依赖 |
| `bench_eigen.cpp` | Eigen 3.4 `PartialPivLU` 基线 (纯头文件 C++ 库) |
| `test.c` / `test_opt.c` | 正确性测试: 随机矩阵 + 已知解验证 |

### 源码 — Python 基线

| 文件 | 说明 |
|---|---|
| `bench_numpy.py` | NumPy.solve / SciPy.lu / SciPy.lu_factor, n=100..4000 |
| `compare.py` | 5 次 trim-mean 综合对照 (C vs MKL 单线程 vs MKL 16 核) |

### 编译 / 测试 / 讲义

| 文件 | 说明 |
|---|---|
| `Makefile` | 目标: `all`/`test`/`test_opt`/`bench_mkl`/`bench_eigen`/`clean`/`distclean` |
| `run_tests.sh` | 一键: 编译 + 跑 bench_mkl + bench_numpy + compare + numpy.show_config |
| `gauss_beamer.tex` / `.pdf` | 讲义 (20 帧) |

### 实验结果 (跑 `./run_tests.sh` 生成)

| 文件 | 说明 |
|---|---|
| `results_c.txt` | bench_mkl 输出: 原始 C / 优化 C / MKL 三路 n=100..4000 |
| `results_numpy.txt` | bench_numpy.py 输出: NumPy.solve / SciPy.lu_factor |
| `results_compare.txt` | compare.py 输出: 5 次 trim-mean + 单线程隔离 |
| `numpy_backend.txt` | `numpy.show_config()` 后端确认 (本机: MKL 2023.1) |

## 编译运行

### 顶层接口 (推荐)
```bash
cd /home/hywang/Claude-working
make all       # 编译三个子项目
make test      # 在每个子目录跑测试
```

### 子目录独立使用
```bash
cd gauss_elimination
make all                    # 编译 test, test_opt, bench_mkl (Eigen 可选)
make all --no-eigen         # 跳过 Eigen
./run_tests.sh              # 编译 + 跑全部基准
./run_tests.sh --no-eigen   # Eigen 头文件缺失时
./run_tests.sh --no-numpy   # 跳过 Python 基线
```

### 单步运行
```bash
./bench_mkl                  # 三路对比
python3 bench_numpy.py       # NumPy/SciPy 基线
python3 compare.py           # trim-mean 综合
```

## 编译依赖

- `bench_mkl` 需要 `libmkl_rt.so` (本机路径: `$CONDA_PREFIX/lib`)
- `bench_eigen` 需要 Eigen 3.4 头文件 (路径 `/tmp/eigen-3.4.0/`)
- 其它仅需 gcc + glibc + libm + libgomp

## 清理

```bash
make clean       # 删除可执行 + .o, 保留实验结果
make distclean   # 清除实验结果 + 日志 (慎用)
```

## 实验关键结论 (frame 13)

| n    | 原始 C (s) | 优化 C (s) | AI+MKL (s) | NumPy.solve (s) | SciPy.lu_factor (s) |
|------|-----------|-----------|-----------|-----------------|---------------------|
| 2000 | 2.8549    | 1.3653    | **0.1128**| 0.2551          | 0.2838              |
| 4000 | 23.715    | 12.621    | **0.7829**| 1.884           | 1.457               |

> **AI+MKL 反而比 NumPy/SciPy 略快** — 无 Python wrapper 开销, 与 scipy 同源 MKL。
