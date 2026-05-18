/*
 * test_opt.c — 对比三种实现: 原始C / 优化C(block+OMP) / NumPy(MKL)
 */

#include "gauss.h"
#include "gauss_opt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

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
        for (int j = 0; j < n; j++)
            s += A[i * n + j] * 1.0;
        b[i] = s;
    }
}

static double residual(int n, const double *A, const double *x, const double *b)
{
    double nr = 0.0, nb = 0.0;
    for (int i = 0; i < n; i++) {
        double s = 0.0;
        for (int j = 0; j < n; j++)
            s += A[i * n + j] * x[j];
        double r = s - b[i];
        nr += r * r;
        nb += b[i] * b[i];
    }
    return sqrt(nr) / sqrt(nb);
}

static void bench_all(int n, int nb)
{
    size_t sz = (size_t)n * n;
    double *A    = (double *)malloc(sz * sizeof(double));
    double *Awrk = (double *)malloc(sz * sizeof(double));
    double *b    = (double *)malloc(n * sizeof(double));
    double *x    = (double *)malloc(n * sizeof(double));
    int    *piv  = (int    *)malloc(n * sizeof(int));

    gen_rand(n, A);
    make_b(n, A, b);

    double flops = 2.0 * n * n * n / 3.0;
    printf("%6d  ", n);

    /* (a) 原始 gauss_solve (lu_decomp_pivot 不单独计时, 直接用求解) */
    memcpy(Awrk, A, sz * sizeof(double));
    double t0 = now_sec();
    int ok = gauss_solve(n, Awrk, b, x);
    double t_orig = now_sec() - t0;
    if (ok == 0)
        printf("%10.4f  %10.1f  ", t_orig, flops / t_orig / 1e6);
    else
        printf("%10s  %10s  ", "FAIL", "—");

    /* (b) 优化版 (仅分解) */
    memcpy(Awrk, A, sz * sizeof(double));
    t0 = now_sec();
    lu_decomp_blocked(n, Awrk, piv, nb);
    double t_block = now_sec() - t0;
    lu_solve_blocked(n, Awrk, piv, b, x);
    double t_total = now_sec() - t0;
    double res = residual(n, A, x, b);
    printf("%10.4f  %10.1f  %10.4f  %10.1f  %10.2e\n",
           t_block, flops / t_block / 1e6,
           t_total, flops / t_total / 1e6,
           res);

    free(A); free(Awrk); free(b); free(x); free(piv);
}

int main(void)
{
    int nthreads = lu_opt_num_threads();
    printf("优化版: ");
#ifdef _OPENMP
    printf("OpenMP enabled, max threads = %d\n", nthreads);
#else
    printf("no OpenMP (serial)\n");
#endif

    int sizes[] = {100, 200, 500, 1000, 2000, 4000};
    int ns = sizeof(sizes) / sizeof(sizes[0]);
    int nb = 128;

    printf("\n对比: 原始 C (O3, 单核)  vs  优化 C (block+OMP, nb=%d)\n\n", nb);
    printf("%6s  %10s  %10s  %10s  %10s  %10s  %10s  %10s\n",
           "n", "orig(s)", "orig GF", "block(s)", "bck GF", "total(s)", "tot GF", "res");
    printf("—————————————————————————————————————————————————————————————————————\n");

    for (int si = 0; si < ns; si++)
        bench_all(sizes[si], nb);

    printf("\n列说明: orig=原始高斯消去; block=优化版分解; total=分解+求解; res=||Ax-b||/||b||\n");
    return 0;
}
