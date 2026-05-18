# sparse — 稀疏矩阵存储与 CRS 教学实现

子项目 3: 围绕**稀疏矩阵存储格式 CRS** 展开, 提供讲义 + 配套教学级 C 实现 + 单元测试。

## 主题

> **CRS (Compressed Row Storage) 的三数组表达 + 六个核心操作的 C 实现, 与讲义伪代码逐行对应。**

讲义共 16 帧, 不仅介绍 CRS 存储格式, 也展示与迭代法 (`fdm3d/`) 的设计契合关系 (在 `iter_beamer.tex` frame 15a/15b 中引用)。

## 文件清单

### 源码 — C 实现

| 文件 | 行数 | 说明 |
|---|---|---|
| `csr.h` | 80 | `csr_matrix` 结构体 + 6 个函数原型, 与讲义 frame 7-11 对应 |
| `csr.c` | 200 | 完整实现: `csr_init` / `csr_free` / `csr_spmv` / `csr_from_coo` / `csr_forward_sub` / `csr_backward_sub` / `csr_transpose` / `csr_print` |
| `csr_demo.c` | 110 | 端到端示例 (frame 13): 4×4 矩阵, 三条路径 (直接构造 / COO / 转置) 验证 $y=Ax$ |
| `csr_test.c` | 230 | 6 项单元测试套件 (11 个 CHECK) |

### 编译 / 测试 / 讲义

| 文件 | 说明 |
|---|---|
| `Makefile` | 目标: `all`/`csr_demo`/`csr_test`/`pdf`/`demo`/`test`/`clean`/`distclean` |
| `run_tests.sh` | 一键: 编译 + 跑 demo + 跑 test + 编译 PDF (支持 `--no-pdf` / `--code-only`) |
| `sparse_crs_beamer.tex` / `.pdf` | 讲义 (16 帧) |

## CRS 核心 API (csr.h)

| 函数 | 功能 | 对应讲义帧 |
|---|---|---|
| `csr_init(A, m, n, nnz)`  | 分配三数组 | frame 8 |
| `csr_free(A)` | 释放并置 NULL | — |
| `csr_spmv(A, x, y)` | $y = Ax$ 稀疏矩阵向量乘 | frame 7 |
| `csr_from_coo(A, row, col, val)` | COO 三元组构造 CSR (两遍扫描) | frame 9 |
| `csr_forward_sub(L, b, x)` | 前代 $Lx = b$ ($L$ 单位下三角) | frame 10 |
| `csr_backward_sub(U, b, x)` | 回代 $Ux = b$ ($U$ 上三角) | frame 10 |
| `csr_transpose(A, AT)` | 矩阵转置 (CSR↔CSC) | frame 11 |
| `csr_print(A)` | 打印矩阵 (调试用) | — |

## 单元测试覆盖 (csr_test.c)

| 测试 | 验证内容 |
|---|---|
| T1 SpMV | 4×4 矩阵 $y = Ax = [10, 160, 120, 290]$ + 零向量 |
| T2 from_coo | 乱序 COO 输入与直接构造 SpMV 一致 |
| T3 transpose | $(A^T)^T = A$ + $A^T x$ 手算 = $[210, 40, 120, 300]$ |
| T4 forward_sub | 单位下三角 $Lx = b$ 解析解 $[1, 3, -1, 17]$ |
| T5 backward_sub | 一般上三角 $Ux = b$ 解析解 $[5/3, 10/3, 7/3, 1]$ |
| T6 1D Poisson | $n=10$ 三对角矩阵, $A \cdot \mathbf{1} = (1, 0, \ldots, 0, 1)^T$ |

合计 11 个 CHECK, 当前全部通过。

## 编译运行

### 顶层接口 (推荐)
```bash
cd /home/hywang/Claude-working
make all       # 编译三个子项目
make test      # 在每个子目录跑测试
```

### 子目录独立使用
```bash
cd sparse
make all              # 编译 csr_demo + csr_test + 讲义 PDF
make test             # 编译并跑单元测试
make demo             # 编译并跑 demo
./run_tests.sh        # 一键: C 代码 + demo + test + PDF
./run_tests.sh --no-pdf  # 跳过 PDF (无 xelatex 环境)
```

### 单步运行
```bash
make csr_demo && ./csr_demo
make csr_test && ./csr_test
make pdf                 # xelatex 两遍 → sparse_crs_beamer.pdf
```

## 编译依赖

- 仅需 gcc + glibc + libm (C99)
- PDF 编译需要 xelatex + xeCJK + Noto CJK 字体

## 清理

```bash
make clean       # 删除可执行 + .o + LaTeX 临时文件 (保留 PDF)
make distclean   # 清除一切 (包括 PDF)
```

## 与其它子项目的关系

- `iter_beamer.tex` (`fdm3d/`) 的 frame 15a/15b 简要回顾 CRS, 引用本目录的 `sparse_crs_beamer.pdf` 作详解
- `csr_spmv` / `csr_forward_sub` 等函数与 `fdm3d/bench_pardiso.c` 中读取 mat.dat 后的 CRS 操作设计一致 (mat.dat 格式与本目录 `csr_matrix` 兼容)
