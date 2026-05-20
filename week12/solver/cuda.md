# CUDA 12.4 + AMGCL 编译环境笔记

**机器**: Intel i7-6800K (Broadwell-E, AVX2, 无AVX-512), GTX 1080 Ti (Pascal, CC 6.1)
**OS**: Debian, gcc 14.2.0, CUDA 12.4, CMake 3.31.6

## 已安装的库及路径

| 库 | 版本 | lib路径 | include路径 |
|---|---|---|---|
| OpenBLAS | 0.3.29 | `/usr/local/lib/libopenblas.so` | `/usr/local/include/` |
| Eigen | 3.4.0 | header-only | `/usr/local/include/eigen3/` |
| SuiteSparse | 7.10.1 | `/usr/local/lib/libumfpack.so` 等 | `/usr/local/include/suitesparse/` |
| libxsmm | 1.17.3808 | `/usr/local/lib/libxsmm.so` | `/usr/local/include/` |
| AMGCL | 1.4.8 | header-only | `/usr/local/include/amgcl/` |

## 关键编译注意事项

### 1. 必须使用 nvcc 编译调用 `amgcl/backend/cuda.hpp` 的代码

系统 `libthrust-dev` (v2.3.2) 与 CUDA 12.4 的 CUB 后端不兼容（Debian 将
Thrust/CUB/libcu++ 统一锁定在 2.3.2）。用 `g++` 编译会在 `thrust::for_each`
等处触发：
```
static assertion failed: unimplemented for this system
```
根因是旧版 Thrust 的 `cuda_cub` 执行策略无法调度 CUDA 12 的 CUB。

**调研过的方案**：
| 方案 | 结果 |
|---|---|
| 升级 Thrust/CUB 到 CCCL 2.5.0 | ❌ 需要同步升级 libcu++，与系统 CUDA 12.4 包 `allocator_traits` 接口不兼容 |
| 卸载 Debian CUDA 包换 NVIDIA 官方 runfile | 理论可行，但风险高，未执行 |
| **使用 nvcc 编译** | ✅ 已验证通过，nvcc 内置 CUDA 运行时正确调度 Thrust |

结论：当前环境用 **nvcc** 编译是唯一可行方案。g++ 仅用于非 CUDA 代码。

### 2. AMGCL 版本升级 (1.4.3 → 1.4.8)

AMGCL v1.4.8 原生支持 CUDA 12 的 cuSPARSE API：
- 使用 `cusparseSpSV_destroyDescr` 替代 `cusparseDestroyCsrsv2Info`
- 使用 `cusparseSpMV` + `cusparseCreateCsr` 替代 `cusparseCsrmvEx`
- `csrsv2Info_t` 相关代码在 `#if CUDART_VERSION >= 11000` 的 `#else` 分支，不会被编译

之前的 v1.4.3 补丁已不再需要。

## 编译命令速查

### OpenBLAS
```
gcc -o test_openblas test_openblas.c -lopenblas -lm
```

### Eigen
```
g++ -O2 -o test_eigen test_eigen.cpp -I/usr/local/include/eigen3
```

### SuiteSparse (UMFPACK)
```
gcc -o test_suitesparse test_suitesparse.c \
    -I/usr/local/include/suitesparse -lumfpack -lsuitesparseconfig -lopenblas -lm
```

### libxsmm
```
gcc -o test_libxsmm test_libxsmm.c -lxsmm -lm
```

### AMGCL (CPU backend)
```
g++ -std=c++17 -O2 -o test_amgcl test_amgcl.cpp -I/usr/local/include
```

### AMGCL (CUDA header check, nvcc 编译)
```
nvcc -std=c++17 -O2 -x cu -o test_amgcl_cuda_header test_amgcl_cuda_header.cpp \
    -I/usr/local/include -I/usr/local/cuda/include -I/usr/include
```

### AMGCL (CUDA 后端完整求解器)
```
nvcc -std=c++17 -O2 -x cu -o test_amgcl_cuda_solve test_amgcl_cuda_solve.cpp \
    -I/usr/local/include -I/usr/local/cuda/include -I/usr/include \
    -L/usr/local/cuda/lib64 -L/usr/lib/x86_64-linux-gnu \
    -lcusparse -lcudart -lopenblas
```

### AMGCL (CUDA 后端，g++ 不可用，仅示意)
```
# 以下用 g++ 编译会失败，仅作参考用途
g++ -std=c++17 -O2 -o test_amgcl_cuda test_amgcl_cuda_header.cpp \
    -I/usr/local/include -I/usr/local/cuda/include -I/usr/include \
    -L/usr/local/cuda/lib64 -L/usr/lib/x86_64-linux-gnu \
    -lcusparse -lcudart
```

## 编译选项选用规则

| 选项 | 适用场景 | 原因 |
|---|---|---|
| `-x cu` | 编译 `.cpp` 文件时 | 强制 nvcc 以 CUDA 模式编译，确保 Thrust 后端正确调度 |
| `-I/usr/local/cuda/include` | 需要 CUDA 头文件时 | CUDA 12.4 nvidia-cuda-toolkit 将头文件装在此处 |
| `-lcusparse -lcudart` | 链接 CUDA 库时 | cuSPARSE 提供稀疏矩阵运算，cudart 提供 CUDA runtime |
| `-lopenblas` | AMGCL 链接时 | AMGCL 的 builtin 后端间接依赖 BLAS |

## 硬件相关的 OpenBLAS 编译选项

```
make -j12 DYNAMIC_ARCH=1 TARGET=HASWELL USE_OPENMP=1
```
- `DYNAMIC_ARCH=1`: 运行时自动选择最优内核（跳过不支持的 AVX-512）
- `TARGET=HASWELL`: i7-6800K Broadwell-E 兼容 Haswell 指令集
- `USE_OPENMP=1`: 启用多线程

## AMGCL cuSPARSE API 映射 (供维护参考)

| 旧 API (CUDA 11) | 新 API (CUDA 12) |
|---|---|
| `cusparseCsrmvEx(_bufferSize)` | `cusparseSpMV(_bufferSize)` |
| `cusparseCreateMatDescr` | `cusparseCreateCsr` (SpMat) |
| `csrsv2Info_t` | `cusparseSpSVDescr_t` |
| `cusparseDestroyCsrsv2Info` | `cusparseSpSV_destroyDescr` |
| `CUSPARSE_ALG_MERGE_PATH` | `CUSPARSE_SPMV_ALG_DEFAULT` |
| `cusparseDcsrmv` / `cusparseScsrmv` | `cusparseSpMV` (统一入口) |
