/*
 * bench_mkl.c — 对比: 手写C vs MKL C接口 vs MKL Fortran接口
 *
 * MKL 提供两种 C 可调用的接口:
 *   1. LAPACKE (C 接口) — LAPACKE_dgetrf(LAPACK_ROW_MAJOR, ...)
 *      需要 mkl_lapacke.h, 头文件版本须与 .so 版本匹配.
 *   2. Fortran 接口     — dgetrf_(&m, &n, A, &lda, ipiv, &info)
 *      仅需手动声明, 无头文件依赖, 跨版本兼容.
 *
 * 本文件同时展示两种接口, 实际运行使用 Fortran 接口 (与 MKL 版本无关).
 *
 * 编译: 见 Makefile
 */

#include "gauss.h"
#include "gauss_opt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ——— MKL Fortran 接口 (列主元 LU, 期望 column-major 布局) ——— */
/* 注意: 传入矩阵必须按 column-major 存储 (Fortran 约定).
   C 代码中的 row-major 矩阵需先转置才能正确求解. */
extern void dgetrf_(int *m, int *n, double *a, int *lda, int *ipiv, int *info);
extern void dgetrs_(char *trans, int *n, int *nrhs, double *a, int *lda,
                    int *ipiv, double *b, int *ldb, int *info);

/*
 * LAPACKE C 接口 (如需使用, 安装匹配版本的 mkl-include):
 *
 *   #include "mkl_lapacke.h"
 *   LAPACKE_dgetrf(LAPACK_ROW_MAJOR, m, n, A, lda, ipiv);
 *   LAPACKE_dgetrs(LAPACK_ROW_MAJOR, 'N', n, nrhs, A, lda, ipiv, b, ldb);
 *
 * 优点: LAPACK_ROW_MAJOR 直接接受 C row-major 矩阵, 无需转置.
 *       lapack_int 自动匹配 32/64 位, 返回值直接返回.
 * 前提: 头文件版本须与 .so 匹配 (如 mkl-include 2023 + mkl 2023).
 */

/* ——— 工具 ——— */

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static void gen_rand(int n, double *A)
{
    srand(42);
    for (int i = 0; i < n * n; i++)
        A[i] = (double)rand() / RAND_MAX;
}

static void make_b(int n, const double *A, double *b)
{
    for (int i = 0; i < n; i++) {
        double s = 0.0;
        for (int j = 0; j < n; j++) s += A[i * n + j];
        b[i] = s;
    }
}

int main(void)
{
    int sizes[] = {100, 200, 500, 1000, 2000, 4000};
    int ns = sizeof(sizes) / sizeof(sizes[0]);

    printf("MKL 链接: libmkl_rt.so (Intel MKL 2023.1)\n");
    printf("接口: Fortran (dgetrf_ / dgetrs_), 无头文件依赖\n\n");

    printf("%6s  %10s  %10s  %10s  %10s  %10s  %10s\n",
           "n", "origC(s)", "optC(s)", "MKL(s)", "MKL(GF)", "v优化C", "v原始C");
    printf("-------------------------------------------------------------------\n");

    for (int si = 0; si < ns; si++) {
        int n = sizes[si];
        size_t sz = (size_t)n * n;
        double *A    = (double *)malloc(sz * sizeof(double));
        double *Awrk = (double *)malloc(sz * sizeof(double));
        double *b    = (double *)malloc(n * sizeof(double));
        double *x    = (double *)malloc(n * sizeof(double));
        int    *ipiv = (int    *)malloc(n * sizeof(int));

        gen_rand(n, A);
        make_b(n, A, b);
        double flops = 2.0 * n * n * n / 3.0 + 2.0 * n * n;

        /* ——— 原始 C (单核 kij) ——— */
        memcpy(Awrk, A, sz * sizeof(double));
        double t0 = now_sec();
        gauss_solve(n, Awrk, b, x);
        double t_orig = now_sec() - t0;

        /* ——— 优化 C (分块 + OpenMP) ——— */
        int *piv_int = (int *)malloc(n * sizeof(int));
        memcpy(Awrk, A, sz * sizeof(double));
        t0 = now_sec();
        lu_decomp_blocked(n, Awrk, piv_int, 128);
        lu_solve_blocked(n, Awrk, piv_int, b, x);
        double t_opt = now_sec() - t0;
        free(piv_int);

        /* ——— MKL (Fortran 接口, 需要 column-major 布局) ——— */
        /* 将 row-major 的 A 转置为 column-major 副本, 使 MKL 看到正确的矩阵 */
        double *A_col = (double *)malloc(sz * sizeof(double));
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                A_col[j * n + i] = A[i * n + j];
        memcpy(x, b, n * sizeof(double));
        int info, nrhs = 1; char trans = 'N';
        t0 = now_sec();
        dgetrf_(&n, &n, A_col, &n, ipiv, &info);
        dgetrs_(&trans, &n, &nrhs, A_col, &n, ipiv, x, &n, &info);
        double t_mkl = now_sec() - t0;
        free(A_col);

        double gf_mkl = flops / t_mkl / 1e6;
        double vs_opt = t_opt / t_mkl;
        double vs_orig = t_orig / t_mkl;

        printf("%6d  %10.4f  %10.4f  %10.4f  %10.1f  %9.1fx  %9.1fx\n",
               n, t_orig, t_opt, t_mkl, gf_mkl, vs_opt, vs_orig);

        free(A); free(Awrk); free(b); free(x); free(ipiv);
    }

    printf("\n接口对比:\n");
    printf("  Fortran: dgetrf_(&n, &n, A, &n, ipiv, &info);          // 全部传指针\n");
    printf("  LAPACKE: LAPACKE_dgetrf(LAPACK_ROW_MAJOR, n,n, A,n, ipiv);\n");
    printf("  性能相同, 仅接口风格差异. Fortran 接口无头文件依赖, 更易移植.\n");
    return 0;
}
