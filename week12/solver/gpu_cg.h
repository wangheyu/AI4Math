#ifndef GPU_CG_H
#define GPU_CG_H
#include "csr_matrix.h"
#include "eigen_ic.h"
#include "test_common.h"
#include <cuda_runtime.h>
#include <cusparse.h>
#include <cublas_v2.h>

struct GpuContext {
    cusparseHandle_t cusparse_handle;
    cublasHandle_t   cublas_handle;
    GpuContext();
    ~GpuContext();
};

// GPU CG with NO preconditioner (pure cublas + cusparse SpMV)
CgResult gpu_cg_solve_no_precond(
    const CsrMatrix &A_cpu,
    const std::vector<double> &b_cpu,
    std::vector<double> &x_cpu,
    const CgParams &params,
    GpuContext &ctx);

// GPU CG with IC(0) preconditioner (L on GPU, cusparse SpSV for triangular solve)
CgResult gpu_cg_solve_ic(
    const CsrMatrix &A_cpu,
    const EigenICPrecond &ic,
    const std::vector<double> &b_cpu,
    std::vector<double> &x_cpu,
    const CgParams &params,
    GpuContext &ctx);
#endif
