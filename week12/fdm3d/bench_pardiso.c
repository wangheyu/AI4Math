/*
 * bench_pardiso.c — AI 调 MKL PARDISO 求解 fdm3d 稀疏矩阵
 *
 * MKL PARDISO 是 Intel oneAPI Math Kernel Library 提供的多线程稀疏直接求解器,
 * 内部用 nested dissection 减少 LU 填充, 适合对称正定 / 一般稀疏矩阵.
 *
 * 本程序: 读 mat.dat → 构造 b = A * u_exact → 调 PARDISO 求解 → 验证误差.
 *
 * 注意 MKL PARDISO 的列索引为 1-based (Fortran 约定), 需要把 CRS 的 0-based
 * row_ptr/col_ind 增 1 后再传入.
 *
 * 编译: 见 Makefile (-lmkl_rt -ldl)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* MKL PARDISO Fortran 接口声明 */
extern void pardiso_(void *pt, int *maxfct, int *mnum, int *mtype,
                     int *phase, int *n, double *a, int *ia, int *ja,
                     int *perm, int *nrhs, int *iparm, int *msglvl,
                     double *b, double *x, int *error);

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static int load_mat(const char *fname,
                    int *nrows, int *nnz, int *Ngrid, double *h,
                    double **val, int **col_ind, int **row_ptr)
{
    FILE *fp = fopen(fname, "rb");
    if (!fp) { perror("fopen mat.dat"); return -1; }
    int ncols;
    double h2inv;
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

int main(void)
{
    setbuf(stdout, NULL);  /* 不缓冲 */
    const char *fname = "mat.dat";

    int nrows, nnz, Ngrid;
    double h;
    double *val;
    int *col_ind, *row_ptr;
    if (load_mat(fname, &nrows, &nnz, &Ngrid, &h, &val, &col_ind, &row_ptr) != 0)
        return 1;

    printf("=== MKL PARDISO 直接求解 ===\n");
    printf("矩阵: %d × %d, nnz = %d (Poisson FDM, N=%d)\n", nrows, nrows, nnz, Ngrid);
    printf("内存: %.1f MB (val) + %.1f MB (col_ind) + %.1f MB (row_ptr)\n\n",
           nnz * 8.0 / 1e6, nnz * 4.0 / 1e6, (nrows + 1) * 4.0 / 1e6);

    printf("[debug] allocating ia/ja ...\n");
    /* MKL PARDISO 用 1-based 索引 */
    int *ia = (int *)malloc((nrows + 1) * sizeof(int));
    int *ja = (int *)malloc(nnz * sizeof(int));
    if (!ia || !ja) { fprintf(stderr, "alloc ia/ja failed\n"); return 1; }
    printf("[debug] converting to 1-based ...\n");
    for (int i = 0; i <= nrows; i++) ia[i] = row_ptr[i] + 1;
    for (int i = 0; i < nnz; i++)    ja[i] = col_ind[i] + 1;
    printf("[debug] done\n");

    /* 构造 b = A * u_exact, u_exact[idx] = sin(πx)sin(πy)sin(πz) */
    int n = Ngrid - 2;  /* 内部点 / 方向 */
    double *u_exact = (double *)malloc(nrows * sizeof(double));
    double *b       = (double *)malloc(nrows * sizeof(double));
    double *x       = (double *)malloc(nrows * sizeof(double));
    for (int k = 0; k < n; k++) {
        double zc = (k + 1) * h;
        for (int j = 0; j < n; j++) {
            double yc = (j + 1) * h;
            for (int i = 0; i < n; i++) {
                double xc = (i + 1) * h;
                int idx = i + n * (j + n * k);
                u_exact[idx] = sin(M_PI * xc) * sin(M_PI * yc) * sin(M_PI * zc);
            }
        }
    }
    /* b = A * u_exact (SpMV) */
    for (int i = 0; i < nrows; i++) {
        double s = 0.0;
        for (int p = row_ptr[i]; p < row_ptr[i + 1]; p++)
            s += val[p] * u_exact[col_ind[p]];
        b[i] = s;
    }

    /* PARDISO 配置 */
    void *pt[64] = {0};                 /* internal pointer */
    int iparm[64] = {0};
    int maxfct = 1, mnum = 1, mtype = 11; /* 11 = 实非对称 (接受完整矩阵) */
    int phase, msglvl = 1, error = 0;
    int nrhs = 1;
    int *perm = NULL;

    /* iparm[0]=0: 使用默认设置. 余下参数 PARDISO 自动填充 */
    iparm[0] = 0;

    printf("[debug] calling PARDISO phase 11 (analyze) ...\n");
    /* phase 11: 符号分析 */
    phase = 11;
    double t0 = now_sec();
    pardiso_(pt, &maxfct, &mnum, &mtype, &phase, &nrows, val, ia, ja,
             perm, &nrhs, iparm, &msglvl, b, x, &error);
    double t_analyze = now_sec() - t0;
    if (error) { fprintf(stderr, "PARDISO analyze error %d\n", error); return 1; }
    printf("Phase 11 (符号分析):      %8.3f s    nnz(L+U) = %d\n", t_analyze, iparm[17]);

    /* phase 22: 数值因式分解 */
    phase = 22;
    t0 = now_sec();
    pardiso_(pt, &maxfct, &mnum, &mtype, &phase, &nrows, val, ia, ja,
             perm, &nrhs, iparm, &msglvl, b, x, &error);
    double t_factor = now_sec() - t0;
    if (error) { fprintf(stderr, "PARDISO factor error %d\n", error); return 1; }
    printf("Phase 22 (数值因式分解):  %8.3f s    Mflops    = %d\n", t_factor, iparm[18]);

    /* phase 33: 回代求解 */
    phase = 33;
    t0 = now_sec();
    pardiso_(pt, &maxfct, &mnum, &mtype, &phase, &nrows, val, ia, ja,
             perm, &nrhs, iparm, &msglvl, b, x, &error);
    double t_solve = now_sec() - t0;
    if (error) { fprintf(stderr, "PARDISO solve error %d\n", error); return 1; }
    printf("Phase 33 (回代):          %8.3f s\n", t_solve);
    printf("总耗时 (analyze+factor+solve): %.3f s\n\n", t_analyze + t_factor + t_solve);

    /* 误差: ||x - u_exact||_2 / sqrt(n) 及 ||·||_inf */
    double l2 = 0.0, linf = 0.0;
    for (int i = 0; i < nrows; i++) {
        double e = fabs(x[i] - u_exact[i]);
        l2 += e * e;
        if (e > linf) linf = e;
    }
    l2 = sqrt(l2 / nrows);
    printf("误差 vs u_exact:\n");
    printf("  L2 / sqrt(n) = %.6e\n", l2);
    printf("  L_inf        = %.6e\n", linf);

    /* phase -1: 释放 PARDISO 内部内存 */
    phase = -1;
    pardiso_(pt, &maxfct, &mnum, &mtype, &phase, &nrows, val, ia, ja,
             perm, &nrhs, iparm, &msglvl, b, x, &error);

    free(val); free(col_ind); free(row_ptr);
    free(ia); free(ja);
    free(u_exact); free(b); free(x);
    return 0;
}
