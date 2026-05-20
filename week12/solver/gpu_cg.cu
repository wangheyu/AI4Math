#include "gpu_cg.h"
#include <cmath>

GpuContext::GpuContext() { cusparseCreate(&cusparse_handle); cublasCreate(&cublas_handle); }
GpuContext::~GpuContext() { cublasDestroy(cublas_handle); cusparseDestroy(cusparse_handle); }

// Allocate and copy CSR to device, create cusparse descriptor
static void copy_csr_to_device(const CsrMatrix &A,
    int *&d_rp, int *&d_ci, double *&d_v, cusparseSpMatDescr_t &desc,
    cusparseHandle_t h)
{
    cudaMalloc(&d_rp, (A.nrows+1)*sizeof(int));
    cudaMalloc(&d_ci, A.nnz*sizeof(int));
    cudaMalloc(&d_v,  A.nnz*sizeof(double));
    cudaMemcpy(d_rp, A.row_ptr.data(), (A.nrows+1)*sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_ci, A.col_ind.data(), A.nnz*sizeof(int),    cudaMemcpyHostToDevice);
    cudaMemcpy(d_v,  A.val.data(),     A.nnz*sizeof(double), cudaMemcpyHostToDevice);
    cusparseCreateCsr(&desc, A.nrows, A.ncols, A.nnz,
        d_rp, d_ci, d_v, CUSPARSE_INDEX_32I, CUSPARSE_INDEX_32I,
        CUSPARSE_INDEX_BASE_ZERO, CUDA_R_64F);
}

// Allocate and copy DnVec
static cusparseDnVecDescr_t make_dnvec(int n, double *d, cusparseHandle_t) {
    cusparseDnVecDescr_t desc; cusparseCreateDnVec(&desc, n, d, CUDA_R_64F); return desc;
}

// Allocate device vector
static double *dalloc(int n) { double *p; cudaMalloc(&p, n*sizeof(double)); return p; }

CgResult gpu_cg_solve_no_precond(
    const CsrMatrix &A, const std::vector<double> &b,
    std::vector<double> &x, const CgParams &params, GpuContext &ctx)
{
    const int n = A.nrows;
    CgResult res; res.setup_time_ms = 0;
    double one=1, zero=0, mone=-1;

    // Copy A to device
    int *d_rp, *d_ci; double *d_v; cusparseSpMatDescr_t matA;
    copy_csr_to_device(A, d_rp, d_ci, d_v, matA, ctx.cusparse_handle);

    // Allocate vectors
    double *dx=dalloc(n), *db=dalloc(n), *dr=dalloc(n), *dp=dalloc(n), *dap=dalloc(n);
    cudaMemcpy(db, b.data(), n*8, cudaMemcpyHostToDevice);
    cudaMemcpy(dx, x.data(), n*8, cudaMemcpyHostToDevice);

    auto vx=make_dnvec(n,dx,0), vr=make_dnvec(n,dr,0), vp=make_dnvec(n,dp,0), vap=make_dnvec(n,dap,0);

    // SpMV buffer
    size_t sbuf; void *dbuf;
    cusparseSpMV_bufferSize(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
        &one, matA, vx, &zero, vap, CUDA_R_64F, CUSPARSE_SPMV_ALG_DEFAULT, &sbuf);
    cudaMalloc(&dbuf, sbuf);

    // r0 = b - A*x0
    cusparseSpMV(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
        &one, matA, vx, &zero, vap, CUDA_R_64F, CUSPARSE_SPMV_ALG_DEFAULT, dbuf);
    cublasDcopy(ctx.cublas_handle, n, db, 1, dr, 1);
    cublasDaxpy(ctx.cublas_handle, n, &mone, dap, 1, dr, 1);
    cublasDcopy(ctx.cublas_handle, n, dr, 1, dp, 1);

    double rho_old; cublasDdot(ctx.cublas_handle, n, dr, 1, dr, 1, &rho_old);
    double bnorm;   cublasDnrm2(ctx.cublas_handle, n, db, 1, &bnorm);
    double tol_s = params.tol * bnorm;

    cudaEvent_t start, stop; cudaEventCreate(&start); cudaEventCreate(&stop);
    cudaEventRecord(start, 0);

    int iter;
    for (iter = 0; iter < params.max_iter; iter++) {
        cusparseSpMV(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
            &one, matA, vp, &zero, vap, CUDA_R_64F, CUSPARSE_SPMV_ALG_DEFAULT, dbuf);
        double pAp; cublasDdot(ctx.cublas_handle, n, dp, 1, dap, 1, &pAp);
        double alpha = rho_old / pAp;
        cublasDaxpy(ctx.cublas_handle, n, &alpha, dp, 1, dx, 1);
        double na = -alpha; cublasDaxpy(ctx.cublas_handle, n, &na, dap, 1, dr, 1);
        double rho_new; cublasDdot(ctx.cublas_handle, n, dr, 1, dr, 1, &rho_new);
        if (std::sqrt(rho_new) < tol_s) { iter++; break; }
        double beta = rho_new / rho_old;
        cublasDscal(ctx.cublas_handle, n, &beta, dp, 1);
        cublasDaxpy(ctx.cublas_handle, n, &one, dr, 1, dp, 1);
        rho_old = rho_new;
    }

    cudaEventRecord(stop, 0); cudaEventSynchronize(stop);
    float ems; cudaEventElapsedTime(&ems, start, stop);
    res.solve_time_ms = ems; res.iterations = iter;

    double rf; cublasDdot(ctx.cublas_handle, n, dr, 1, dr, 1, &rf);
    res.final_residual = std::sqrt(rf);
    cudaMemcpy(x.data(), dx, n*8, cudaMemcpyDeviceToHost);

    // Cleanup
    cudaEventDestroy(start); cudaEventDestroy(stop);
    cudaFree(dbuf);
    cusparseDestroyDnVec(vx); cusparseDestroyDnVec(vr); cusparseDestroyDnVec(vp); cusparseDestroyDnVec(vap);
    cusparseDestroySpMat(matA);
    cudaFree(dx); cudaFree(db); cudaFree(dr); cudaFree(dp); cudaFree(dap);
    cudaFree(d_rp); cudaFree(d_ci); cudaFree(d_v);
    return res;
}

CgResult gpu_cg_solve_ic(
    const CsrMatrix &A, const EigenICPrecond &ic,
    const std::vector<double> &b, std::vector<double> &x,
    const CgParams &params, GpuContext &ctx)
{
    const int n = A.nrows, nnzL = ic.L_row_ptr()[n];
    CgResult res; res.setup_time_ms = ic.setup_time_ms();
    double one=1, zero=0, mone=-1;

    // Copy A to device
    int *d_rp, *d_ci; double *d_v; cusparseSpMatDescr_t matA;
    copy_csr_to_device(A, d_rp, d_ci, d_v, matA, ctx.cusparse_handle);

    // Copy L to device (unit diagonal implied: stored as 1.0)
    int *d_Lrp, *d_Lci; double *d_Lv;
    cudaMalloc(&d_Lrp, (n+1)*sizeof(int));
    cudaMalloc(&d_Lci, nnzL*sizeof(int));
    cudaMalloc(&d_Lv,  nnzL*sizeof(double));
    cudaMemcpy(d_Lrp, ic.L_row_ptr().data(), (n+1)*sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_Lci, ic.L_col_ind().data(), nnzL*sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_Lv,  ic.L_val().data(),     nnzL*sizeof(double), cudaMemcpyHostToDevice);

    cusparseSpMatDescr_t matL;
    cusparseCreateCsr(&matL, n, n, nnzL, d_Lrp, d_Lci, d_Lv,
        CUSPARSE_INDEX_32I, CUSPARSE_INDEX_32I,
        CUSPARSE_INDEX_BASE_ZERO, CUDA_R_64F);
    cusparseFillMode_t fm = CUSPARSE_FILL_MODE_LOWER;
    cusparseDiagType_t dt = CUSPARSE_DIAG_TYPE_NON_UNIT;
    cusparseSpMatSetAttribute(matL, CUSPARSE_SPMAT_FILL_MODE, &fm, sizeof(fm));
    cusparseSpMatSetAttribute(matL, CUSPARSE_SPMAT_DIAG_TYPE, &dt, sizeof(dt));

    // Allocate all vectors
    double *dx=dalloc(n), *db=dalloc(n), *dr=dalloc(n), *dz=dalloc(n);
    double *dp=dalloc(n), *dap=dalloc(n), *dy=dalloc(n);
    cudaMemcpy(db, b.data(), n*8, cudaMemcpyHostToDevice);
    cudaMemcpy(dx, x.data(), n*8, cudaMemcpyHostToDevice);

    auto vx=make_dnvec(n,dx,0), vr=make_dnvec(n,dr,0), vz=make_dnvec(n,dz,0);
    auto vp=make_dnvec(n,dp,0), vap=make_dnvec(n,dap,0), vy=make_dnvec(n,dy,0);

    // SpMV buffer
    size_t sbuf; void *dbuf;
    cusparseSpMV_bufferSize(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
        &one, matA, vx, &zero, vap, CUDA_R_64F, CUSPARSE_SPMV_ALG_DEFAULT, &sbuf);
    cudaMalloc(&dbuf, sbuf);

    // SpSV descriptor + buffer for L (forward) and L^T (backward)
    // Pre-analyze with actual vector descriptors (important: not nullptr!)
    cusparseSpSVDescr_t spsv_fwd, spsv_bwd;
    cusparseSpSV_createDescr(&spsv_fwd);
    cusparseSpSV_createDescr(&spsv_bwd);
    size_t sbuf_fwd, sbuf_bwd;
    cusparseSpSV_bufferSize(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
        &one, matL, vr, vy, CUDA_R_64F, CUSPARSE_SPSV_ALG_DEFAULT, spsv_fwd, &sbuf_fwd);
    cusparseSpSV_bufferSize(ctx.cusparse_handle, CUSPARSE_OPERATION_TRANSPOSE,
        &one, matL, vy, vr, CUDA_R_64F, CUSPARSE_SPSV_ALG_DEFAULT, spsv_bwd, &sbuf_bwd);
    void *dfwd, *dbwd;
    cudaMalloc(&dfwd, sbuf_fwd); cudaMalloc(&dbwd, sbuf_bwd);
    cusparseSpSV_analysis(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
        &one, matL, vr, vy, CUDA_R_64F, CUSPARSE_SPSV_ALG_DEFAULT, spsv_fwd, dfwd);
    cusparseSpSV_analysis(ctx.cusparse_handle, CUSPARSE_OPERATION_TRANSPOSE,
        &one, matL, vy, vr, CUDA_R_64F, CUSPARSE_SPSV_ALG_DEFAULT, spsv_bwd, dbwd);

    // r0 = b - A*x0
    cusparseSpMV(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
        &one, matA, vx, &zero, vap, CUDA_R_64F, CUSPARSE_SPMV_ALG_DEFAULT, dbuf);
    cublasDcopy(ctx.cublas_handle, n, db, 1, dr, 1);
    cublasDaxpy(ctx.cublas_handle, n, &mone, dap, 1, dr, 1);

    // z0 = M^{-1} * r0 = L^{-T} * D^{-1} * L^{-1} * r0
    // Pre-allocate D inverse on host (used per-iteration via cudaMemcpy)
    std::vector<double> D_inv(n);
    for (int i = 0; i < n; i++) D_inv[i] = 1.0 / ic.D()[i];
    std::vector<double> y_host(n); // temp for D scaling

    cusparseSpSV_solve(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
        &one, matL, vr, vy, CUDA_R_64F, CUSPARSE_SPSV_ALG_DEFAULT, spsv_fwd);
    cudaMemcpy(y_host.data(), dy, n*8, cudaMemcpyDeviceToHost);
    for (int i = 0; i < n; i++) y_host[i] *= D_inv[i];
    cudaMemcpy(dy, y_host.data(), n*8, cudaMemcpyHostToDevice);
    cusparseSpSV_solve(ctx.cusparse_handle, CUSPARSE_OPERATION_TRANSPOSE,
        &one, matL, vy, vz, CUDA_R_64F, CUSPARSE_SPSV_ALG_DEFAULT, spsv_bwd);

    cublasDcopy(ctx.cublas_handle, n, dz, 1, dp, 1);
    double rho_old; cublasDdot(ctx.cublas_handle, n, dr, 1, dz, 1, &rho_old);
    double bnorm;   cublasDnrm2(ctx.cublas_handle, n, db, 1, &bnorm);
    double tol_s = params.tol * bnorm;

    cudaEvent_t start, stop; cudaEventCreate(&start); cudaEventCreate(&stop);
    cudaEventRecord(start, 0);

    int iter;
    for (iter = 0; iter < params.max_iter; iter++) {
        cusparseSpMV(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
            &one, matA, vp, &zero, vap, CUDA_R_64F, CUSPARSE_SPMV_ALG_DEFAULT, dbuf);
        double pAp; cublasDdot(ctx.cublas_handle, n, dp, 1, dap, 1, &pAp);
        double alpha = rho_old / pAp;
        cublasDaxpy(ctx.cublas_handle, n, &alpha, dp, 1, dx, 1);
        double na = -alpha; cublasDaxpy(ctx.cublas_handle, n, &na, dap, 1, dr, 1);

        // z = M^{-1} * r
        cusparseSpSV_solve(ctx.cusparse_handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
            &one, matL, vr, vy, CUDA_R_64F, CUSPARSE_SPSV_ALG_DEFAULT, spsv_fwd);
        cudaMemcpy(y_host.data(), dy, n*8, cudaMemcpyDeviceToHost);
        for (int i = 0; i < n; i++) y_host[i] *= D_inv[i];
        cudaMemcpy(dy, y_host.data(), n*8, cudaMemcpyHostToDevice);
        cusparseSpSV_solve(ctx.cusparse_handle, CUSPARSE_OPERATION_TRANSPOSE,
            &one, matL, vy, vz, CUDA_R_64F, CUSPARSE_SPSV_ALG_DEFAULT, spsv_bwd);

        double rho_new; cublasDdot(ctx.cublas_handle, n, dr, 1, dz, 1, &rho_new);
        double r_l2; cublasDnrm2(ctx.cublas_handle, n, dr, 1, &r_l2);
        if (r_l2 < tol_s) { iter++; break; }
        double beta = rho_new / rho_old;
        cublasDscal(ctx.cublas_handle, n, &beta, dp, 1);
        cublasDaxpy(ctx.cublas_handle, n, &one, dz, 1, dp, 1);
        rho_old = rho_new;
    }

    cudaEventRecord(stop, 0); cudaEventSynchronize(stop);
    float ems; cudaEventElapsedTime(&ems, start, stop);
    res.solve_time_ms = ems; res.iterations = iter;

    double rf; cublasDdot(ctx.cublas_handle, n, dr, 1, dr, 1, &rf);
    res.final_residual = std::sqrt(rf);
    cudaMemcpy(x.data(), dx, n*8, cudaMemcpyDeviceToHost);

    // Cleanup
    cudaEventDestroy(start); cudaEventDestroy(stop);
    cudaFree(dbuf);
    cudaFree(dfwd); cudaFree(dbwd);
    cusparseSpSV_destroyDescr(spsv_fwd);
    cusparseSpSV_destroyDescr(spsv_bwd);
    cusparseDestroyDnVec(vx); cusparseDestroyDnVec(vr); cusparseDestroyDnVec(vz);
    cusparseDestroyDnVec(vp); cusparseDestroyDnVec(vap); cusparseDestroyDnVec(vy);
    cusparseDestroySpMat(matA); cusparseDestroySpMat(matL);
    cudaFree(d_Lrp); cudaFree(d_Lci); cudaFree(d_Lv);
    cudaFree(dx); cudaFree(db); cudaFree(dr); cudaFree(dz);
    cudaFree(dp); cudaFree(dap); cudaFree(dy);
    cudaFree(d_rp); cudaFree(d_ci); cudaFree(d_v);
    return res;
}
