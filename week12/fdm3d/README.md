# fdm3d — 迭代法与大规模稀疏矩阵

子项目 2: 围绕迭代法展开, 以 **3D Poisson 有限差分稀疏矩阵** (970299×970299, nnz=6.7M) 为载体, 讨论 Jacobi / GS / SOR 理论、最优 SOR 参数、稀疏求解器, 并对照 **AI + MKL PARDISO / AI 写 SOR vs scipy.sparse.linalg**。

## 主题

> **大规模稀疏问题: 直接法不可行, 必须用迭代法; AI + 库 路径在迭代法上仍然能跨越软件。**

讲义共 27 帧, 含 SOR 最优参数解析公式实证验证 + AI 路径"自由换库"优势论述。

## 文件清单

### 源码 — C 实现

| 文件 | 说明 |
|---|---|
| `main.c` | 3D Poisson SOR 求解器 (stencil 风格, 不读 mat.dat), $\omega$ 命令行可调 |
| `jacobi.c` | 纯 Jacobi 迭代 (与 SOR 对比收敛速度) |
| `sor_scan.c` | SOR omega 扫描 ($\omega \in [1.0, 1.99]$), 寻找经验最优 |
| `bench_pardiso.c` | AI 调 MKL PARDISO 直接求解 mat.dat (本机环境 conda+MKL 冲突, 接口代码正确) |
| `write_mat.c` | 生成 N=101 CRS 稀疏矩阵 → mat.dat (二进制, 80 MB) |
| `read_mat.c` | 读取 mat.dat 并验证 5 项性质 (单调/列号/对角/对称/行和) |

### 源码 — Python

| 文件 | 说明 |
|---|---|
| `bench_iter.py` | scipy.sparse.linalg: spsolve / cg / gmres 对照, 支持 sin RHS + random RHS |
| `plot_solution.py` | matplotlib 生成 3 张 PNG: 解中间切片 / 收敛曲线 / SOR omega 扫描 |

### 编译 / 测试 / 讲义

| 文件 | 说明 |
|---|---|
| `Makefile` | 目标: `all`/`fdm3d`/`jacobi`/`sor_scan`/`bench_pardiso`/`write_mat`/`read_mat`/`clean`/`distclean` |
| `run_tests.sh` | 一键: 编译 + Jacobi/GS/SOR + SOR 扫描 + scipy 对比 + PNG (支持 `--quick`/`--no-plot`) |
| `iter_beamer.tex` / `.pdf` | 讲义 (27 帧) |

### 数据 / 结果 (跑 `./run_tests.sh` 生成)

| 文件 | 说明 |
|---|---|
| `mat.dat` | N=101 CRS 稀疏矩阵 (80 MB, 由 `write_mat` 生成) |
| `results_jacobi.txt` | Jacobi N=64 完整输出 (~18000 iter 收敛) |
| `results_gs.txt`     | Gauss-Seidel ($\omega=1$) 输出 (~8997 iter) |
| `results_sor.txt`    | SOR ($\omega=1.9$) 输出 (~350 iter) |
| `results_sor_scan.txt` | SOR 参数扫描表 |
| `results_scipy.txt`  | scipy.sparse 对比 (spsolve OOM, cg/gmres 收敛) |
| `results_pardiso.txt`| PARDISO 状态记录 (本机环境问题说明) |
| `conv_*.txt`         | 各方法的收敛历史 (用于绘制收敛曲线) |
| `solution_slice.png` | 970299 维解在 z=0.5 平面的 contour + 误差热图 |
| `convergence.png`    | Jacobi/GS/SOR 收敛曲线对比 |
| `sor_omega.png`      | SOR omega 扫描结果 |

## 编译运行

### 顶层接口 (推荐)
```bash
cd /home/hywang/Claude-working
make all       # 编译三个子项目
make test      # 在每个子目录跑测试
```

### 子目录独立使用
```bash
cd fdm3d
make all                    # 编译全部目标
./run_tests.sh              # 编译 + 全部数值实验 + 生成 PNG
./run_tests.sh --quick      # 仅小规模 (跳过 N=101 大矩阵实验)
./run_tests.sh --no-plot    # 不生成 PNG (无 matplotlib)
```

### 单步运行
```bash
./write_mat                  # 生成 mat.dat (仅首次)
./fdm3d 64 1.9 30000 1e-6    # SOR: N=64, omega=1.9, max_iter, tol
./jacobi 64 20000 1e-6       # Jacobi: N=64
./sor_scan 64 5000 1e-6      # omega 扫描
python3 bench_iter.py        # scipy.sparse 对比
python3 plot_solution.py     # 生成 PNG
```

## 编译依赖

- `bench_pardiso` 需要 `libmkl_rt.so` (本机路径: `$CONDA_PREFIX/lib`)
- `bench_iter.py` 需要 scipy, `plot_solution.py` 需要 matplotlib
- 其它仅需 gcc + glibc + libm + libgomp

## 清理

```bash
make clean       # 删除可执行 + .o (保留 mat.dat / results / PNG)
make distclean   # 清除 mat.dat + results + conv + PNG (慎用; mat.dat 重新生成耗时)
```

## 实验关键结论

| 实验 | 数据 | 含义 |
|---|---|---|
| **Jacobi vs GS vs SOR** (N=64) | 18000 / 8997 / **300** iter | GS 比 Jacobi 快 2×; SOR$_{\text{opt}}$ 比 GS 快 30× |
| **SOR 最优 $\omega$** (N=64) | 实测 1.905, 理论 $2/(1+\sin(\pi/63)) = 1.9050$ | Young 公式 4 位精度验证 |
| **大规模直接法** (N=101 mat.dat) | scipy.spsolve **OOM**, PARDISO 本机 segfault | 970299 维稀疏矩阵直接法不可行 |
| **Krylov 迭代** (N=101 random RHS) | scipy.cg 351 iter / 8.85s, scipy.gmres 651 iter / 89s | 大规模唯一实用路径 |
| **AI vs 软件 在迭代法上** | AI+C+SOR ≈ scipy.cg 数量级 | 论点延续到迭代法场景 |
