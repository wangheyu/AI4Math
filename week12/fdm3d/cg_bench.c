/*
 * cg_bench.c — CG 求解器三路对比: 手写 CSR SpMV vs MKL IE SpBLAS
 *
 * 读 mat.dat → 随机 RHS → CG 迭代 → 对比迭代数 / 耗时 / 残差
 *
 * 两路 C:
 *   (1) hand: csr_spmv() 手写循环 + 手写 dot/axpy/scal
 *   (2) mkl:  mkl_sparse_d_mv() + cblas_ddot/daxpy/dscal/dnrm2
 *
 * 编译: 见 Makefile (需要 -I$(MKL_INCLUDE) -lmkl_rt)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include "mkl_spblas.h"
#include "mkl_cblas.h"

/* ============================================================
 * 计时
 * ============================================================ */
static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* ============================================================
 * 读取 mat.dat
 * ============================================================ */
static int load_mat(const char *fname,
                    int *nrows, int *nnz, int *Ngrid, double *h,
                    double **val, int **col_ind, int **row_ptr)
{
    FILE *fp = fopen(fname, "rb");
    if (!fp) { perror("fopen mat.dat"); return -1; }
    int ncols; double h2inv;
    fread(nrows, sizeof(int), 1, fp);
    fread(&ncols, sizeof(int), 1, fp);
    fread(nnz,   sizeof(int), 1, fp);
    fread(Ngrid, sizeof(int), 1, fp);
    fread(h,     sizeof(double), 1, fp);
    fread(&h2inv, sizeof(double), 1, fp);
    *val     = (double *)malloc(*nnz * sizeof(double));
    *col_ind = (int    *)malloc(*nnz * sizeof(int));
    *row_ptr = (int    *)malloc((*nrows + 1) * sizeof(int));
    fread(*val,     sizeof(double), *nnz, fp);
    fread(*col_ind, sizeof(int),    *nnz, fp);
    fread(*row_ptr, sizeof(int),    *nrows + 1, fp);
    fclose(fp);
    return 0;
}

/* ============================================================
 * 手写 CSR SpMV: y = A * x
 * ============================================================ */
typedef struct {
    int nrows;
    int *row_ptr, *col_ind;
    double *val;
} csr_ctx;

static void hand_spmv(void *ctx, const double *x, double *y)
{
    csr_ctx *A = (csr_ctx *)ctx;
    for (int i = 0; i < A->nrows; i++) {
        double sum = 0.0;
        for (int k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++)
            sum += A->val[k] * x[A->col_ind[k]];
        y[i] = sum;
    }
}

/* ============================================================
 * 手写向量运算
 * ============================================================ */
static double hand_dot(int n, const double *x, const double *y)
{
    double s = 0.0;
    for (int i = 0; i < n; i++) s += x[i] * y[i];
    return s;
}

static void hand_axpy(int n, double a, const double *x, double *y)
{
    for (int i = 0; i < n; i++) y[i] += a * x[i];
}

static void hand_scal(int n, double a, double *x)
{
    for (int i = 0; i < n; i++) x[i] *= a;
}

static double hand_nrm2(int n, const double *x)
{
    return sqrt(hand_dot(n, x, x));
}

/* ============================================================
 * MKL SpMV wrapper + CBLAS wrappers
 *
 *   CBLAS 函数带 stride 参数, 与我们 CG 中的 dot_t/axpy_t 等签名不兼容,
 *   因此用 thin wrapper 适配, 避免函数指针强转导致的 ABI 问题.
 * ============================================================ */
static void mkl_spmv_wrap(void *ctx, const double *x, double *y)
{
    sparse_matrix_t A = (sparse_matrix_t)ctx;
    struct matrix_descr descr;
    descr.type = SPARSE_MATRIX_TYPE_GENERAL;
    descr.mode = SPARSE_FILL_MODE_FULL;
    descr.diag = SPARSE_DIAG_NON_UNIT;
    mkl_sparse_d_mv(SPARSE_OPERATION_NON_TRANSPOSE, 1.0, A, descr, x, 0.0, y);
}

static double mkl_dot(int n, const double *x, const double *y)
{
    return cblas_ddot(n, x, 1, y, 1);
}

static void mkl_axpy(int n, double a, const double *x, double *y)
{
    cblas_daxpy(n, a, x, 1, y, 1);
}

static void mkl_scal(int n, double a, double *x)
{
    cblas_dscal(n, a, x, 1);
}

static double mkl_nrm2(int n, const double *x)
{
    return cblas_dnrm2(n, x, 1);
}

/* ============================================================
 * 通用 CG 求解器
 *
 *   传入函数指针实现 SpMV + 向量运算, 统一 CG 算法逻辑.
 *   x 初始为求解起点 (通常置零), 函数内会原地更新.
 *
 *   返回: 迭代次数. out_res 写入最终残差, out_time 写入耗时 (不含 optimize).
 * ============================================================ */
typedef void  (*spmv_t)(void *ctx, const double *x, double *y);
typedef double (*dot_t)(int n, const double *x, const double *y);
typedef void  (*axpy_t)(int n, double a, const double *x, double *y);
typedef void  (*scal_t)(int n, double a, double *x);
typedef double (*nrm2_t)(int n, const double *x);

typedef struct {
    spmv_t spmv;  void *spmv_ctx;
    dot_t  dot;
    axpy_t axpy;
    scal_t scal;
    nrm2_t nrm2;
} cg_backend;

static int cg_solve(int n, const cg_backend *b,
                    const double *bvec, double *x,
                    int max_iter, double tol,
                    double *out_res, double *out_time)
{
    double *r  = (double *)malloc(n * sizeof(double));
    double *p  = (double *)malloc(n * sizeof(double));
    double *Ap = (double *)malloc(n * sizeof(double));

    /* r = b, p = r, x = 0 */
    memcpy(r, bvec, n * sizeof(double));
    memcpy(p, bvec, n * sizeof(double));
    memset(x, 0, n * sizeof(double));

    double rtr = b->dot(n, r, r);
    double bnorm = sqrt(rtr);
    double tol_scaled = tol * bnorm;

    double t0 = now_sec();
    int iter;
    for (iter = 1; iter <= max_iter; iter++) {
        /* Ap = A * p */
        b->spmv(b->spmv_ctx, p, Ap);

        /* α = r'r / p'Ap */
        double ptAp = b->dot(n, p, Ap);
        double alpha = rtr / ptAp;

        /* x += α * p */
        b->axpy(n,  alpha, p, x);

        /* r -= α * Ap */
        b->axpy(n, -alpha, Ap, r);

        /* convergence check */
        double rnorm = b->nrm2(n, r);
        if (iter % 50 == 0 || iter == 1) {
            printf("    iter %5d  |r| = %12.6e\n", iter, rnorm);
        }
        if (rnorm < tol_scaled) {
            printf("    converged at iter %d, |r| = %12.6e\n", iter, rnorm);
            *out_res = rnorm / bnorm;
            *out_time = now_sec() - t0;
            free(r); free(p); free(Ap);
            return iter;
        }

        /* β = r'r_new / r'r_old */
        double rtr_new = b->dot(n, r, r);
        double beta = rtr_new / rtr;
        rtr = rtr_new;

        /* p = r + β * p  (先缩放 p, 再加 r) */
        b->scal(n, beta, p);
        b->axpy(n, 1.0, r, p);
    }

    *out_res = b->nrm2(n, r) / bnorm;
    *out_time = now_sec() - t0;
    free(r); free(p); free(Ap);
    printf("    max_iter reached, |r| = %12.6e\n", *out_res * bnorm);
    return max_iter;
}

/* ============================================================
 * 退出码
 * ============================================================ */
static void die(const char *msg) {
    fprintf(stderr, "FATAL: %s\n", msg);
    exit(1);
}

/* ============================================================
 * main
 * ============================================================ */
int main(int argc, char **argv)
{
    const char *fname = (argc > 1) ? argv[1] : "mat.dat";

    setbuf(stdout, NULL);

    /* ---- 1. 加载 mat.dat ---- */
    printf("=== CG 三路对比 (C paths) ===\n\n");
    printf("加载 %s ...\n", fname);

    int nrows, nnz, Ngrid; double h;
    double *val; int *col_ind, *row_ptr;
    if (load_mat(fname, &nrows, &nnz, &Ngrid, &h,
                 &val, &col_ind, &row_ptr) != 0)
        die("load_mat failed");

    printf("  矩阵: %d x %d, nnz = %d (Poisson N=%d)\n\n",
           nrows, nrows, nnz, Ngrid);

    /* ---- 2. 构造随机 RHS ---- */
    double *b = (double *)malloc(nrows * sizeof(double));
    double *x = (double *)malloc(nrows * sizeof(double));

    srand(42);
    for (int i = 0; i < nrows; i++)
        b[i] = (double)rand() / RAND_MAX - 0.5;  /* [-0.5, 0.5) */

    double bnorm = 0.0;
    for (int i = 0; i < nrows; i++) bnorm += b[i] * b[i];
    bnorm = sqrt(bnorm);
    printf("  ||b|| = %.6e\n", bnorm);

    /* 保存 RHS 供 Python 对比脚本读取 */
    {
        FILE *frhs = fopen("rhs.dat", "wb");
        if (frhs) {
            fwrite(&nrows, sizeof(int), 1, frhs);
            fwrite(b, sizeof(double), nrows, frhs);
            fclose(frhs);
            printf("  RHS saved to rhs.dat\n");
        }
    }
    printf("\n");

    int max_iter = 5000;
    double tol = 1e-8;

    /* ============================================================
     * 路 1: 手写 C CSR SpMV + 手写向量运算
     * ============================================================ */
    printf("--- (1) CG + hand-coded CSR SpMV ---\n");

    csr_ctx hand_ctx = {nrows, row_ptr, col_ind, val};

    cg_backend hand_be = {
        .spmv = hand_spmv, .spmv_ctx = &hand_ctx,
        .dot  = hand_dot,
        .axpy = hand_axpy,
        .scal = hand_scal,
        .nrm2 = hand_nrm2,
    };
    memset(x, 0, nrows * sizeof(double));
    double res1, t1;
    int it1 = cg_solve(nrows, &hand_be, b, x, max_iter, tol, &res1, &t1);

    printf("  结果: %d iter, %.3f s,  rel-res = %.3e\n\n", it1, t1, res1);

    /* ============================================================
     * 路 2: MKL IE SpBLAS + CBLAS 向量运算
     * ============================================================ */
    printf("--- (2) CG + MKL IE SpBLAS ---\n");

    /* 2a. 创建 MKL 稀疏句柄 */
    sparse_matrix_t A_mkl = NULL;
    /* rows_end[i] = row_ptr[i+1] */
    MKL_INT *rows_end = (MKL_INT *)malloc(nrows * sizeof(MKL_INT));
    for (int i = 0; i < nrows; i++)
        rows_end[i] = (MKL_INT)row_ptr[i + 1];

    sparse_status_t status;
    double t_opt = 0.0;

    status = mkl_sparse_d_create_csr(
        &A_mkl, SPARSE_INDEX_BASE_ZERO,
        nrows, nrows,
        row_ptr, rows_end, col_ind, val);
    if (status != SPARSE_STATUS_SUCCESS)
        die("mkl_sparse_d_create_csr failed");
    printf("  handle created\n");

    /* 2b. 设置优化提示 */
    struct matrix_descr descr_mkl;
    descr_mkl.type = SPARSE_MATRIX_TYPE_GENERAL;
    descr_mkl.mode = SPARSE_FILL_MODE_FULL;
    descr_mkl.diag = SPARSE_DIAG_NON_UNIT;

    mkl_sparse_set_mv_hint(A_mkl, SPARSE_OPERATION_NON_TRANSPOSE,
                           descr_mkl, max_iter);
    mkl_sparse_set_memory_hint(A_mkl, SPARSE_MEMORY_AGGRESSIVE);

    /* 2c. optimize (单独计时) */
    printf("  optimizing ...");
    double t0 = now_sec();
    status = mkl_sparse_optimize(A_mkl);
    t_opt = now_sec() - t0;
    if (status != SPARSE_STATUS_SUCCESS)
        die("mkl_sparse_optimize failed");
    printf(" %.3f s\n", t_opt);

    /* 2d. CG 求解 */
    cg_backend mkl_be = {
        .spmv = mkl_spmv_wrap, .spmv_ctx = (void *)A_mkl,
        .dot  = mkl_dot,
        .axpy = mkl_axpy,
        .scal = mkl_scal,
        .nrm2 = mkl_nrm2,
    };
    memset(x, 0, nrows * sizeof(double));
    double res2, t2;
    int it2 = cg_solve(nrows, &mkl_be, b, x, max_iter, tol, &res2, &t2);

    printf("  结果: %d iter, %.3f s,  rel-res = %.3e\n", it2, t2, res2);
    printf("  optimize: %.3f s, solve: %.3f s, total: %.3f s\n\n",
           t_opt, t2, t_opt + t2);

    /* 2e. 释放 MKL 句柄 */
    mkl_sparse_destroy(A_mkl);
    free(rows_end);

    /* ============================================================
     * 汇总
     * ============================================================ */
    printf("========== 汇总 ==========\n");
    printf("%-20s  %6s  %10s  %12s\n", "backend", "iter", "time(s)", "rel-res");
    printf("----------------------------------------------------\n");
    printf("%-20s  %6d  %10.3f  %12.3e\n", "C hand CSR",  it1, t1, res1);
    printf("%-20s  %6d  %10.3f  %12.3e\n",
           "C MKL SpBLAS (solve)", it2, t2, res2);
    printf("%-20s  %6s  %10.3f  %12s\n",
           "C MKL SpBLAS (optimize)", "—", t_opt, "—");
    printf("%-20s  %6s  %10.3f  %12s\n",
           "C MKL SpBLAS (total)", "—", t_opt + t2, "—");
    printf("\nspeedup (hand/MKL solve): %.2fx\n", t1 / t2);

    /* ---- 清理 ---- */
    free(val); free(col_ind); free(row_ptr);
    free(b); free(x);
    return 0;
}
