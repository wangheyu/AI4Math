/*
 * test.c — 高斯消去法 / LU 分解 的正确性验证与性能测试
 *
 * 测试矩阵类型:
 *   1. 随机矩阵 (uniform [0,1))
 *   2. Hilbert 矩阵  H_{ij} = 1/(i+j+1)   (经典病态)
 *   3. 对角占优随机矩阵  A = rand + n*I
 *
 * 每个规模测试:
 *   - 高斯消去法 (列主元, 求解)
 *   - LU 分解 (无选主元, 仅分解)
 *   - LU 分解 (列主元, 分解 + 求解)
 *   - 正确性: ||Ax - b|| / ||b||
 */

#include "gauss.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ---------- 矩阵生成 ---------- */

static double rand01(void)
{
    return (double)rand() / (double)RAND_MAX;
}

/* 生成 n×n 随机矩阵 */
static void mat_random(int n, double *A)
{
    for (int i = 0; i < n * n; i++)
        A[i] = rand01();
}

/* Hilbert 矩阵: H[i][j] = 1 / (i+j+1) */
static void mat_hilbert(int n, double *A)
{
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            A[i * n + j] = 1.0 / (i + j + 1);
}

/* 对角占优随机矩阵: 非对角元 rand, 对角元 = 行和 + rand + n */
static void mat_diag_dom(int n, double *A)
{
    for (int i = 0; i < n; i++) {
        double row_sum = 0.0;
        for (int j = 0; j < n; j++) {
            if (i != j) {
                double v = rand01();
                A[i * n + j] = v;
                row_sum += fabs(v);
            }
        }
        A[i * n + i] = row_sum + rand01() + n;  /* 严格对角占优 */
    }
}

/* 生成已知解 x_ref = 1, 计算 b = A * x_ref */
static void make_rhs(int n, const double *A, double *b)
{
    for (int i = 0; i < n; i++) {
        double s = 0.0;
        for (int j = 0; j < n; j++)
            s += A[i * n + j] * 1.0;  /* x_ref[j] = 1 */
        b[i] = s;
    }
}

/* ---------- 误差度量 ---------- */

/* ||Ax - b|| / ||b|| */
static double residual(int n, const double *A, const double *x, const double *b)
{
    double *r = (double *)malloc(n * sizeof(double));
    double nb = 0.0, nr = 0.0;
    for (int i = 0; i < n; i++) {
        double s = 0.0;
        for (int j = 0; j < n; j++)
            s += A[i * n + j] * x[j];
        r[i] = s - b[i];
        nr += r[i] * r[i];
        nb += b[i] * b[i];
    }
    free(r);
    return sqrt(nr) / sqrt(nb);
}

/* ||x - x_ref||_inf */
static double error_linf(int n, const double *x)
{
    double maxe = 0.0;
    for (int i = 0; i < n; i++) {
        double e = fabs(x[i] - 1.0);
        if (e > maxe) maxe = e;
    }
    return maxe;
}

/* ||A - LU||_F / ||A||_F  (验证分解精度) */
static double lu_error(int n, const double *A_orig, const double *LU)
{
    double nA = 0.0, nR = 0.0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            /* 重构 LU 乘积 */
            double s = 0.0;
            int kmax = (i < j) ? i : j;
            for (int k = 0; k <= kmax; k++) {
                double lik = (i > k) ? LU[i * n + k] : (i == k ? 1.0 : 0.0);
                double ukj = (k <= j) ? LU[k * n + j] : 0.0;
                s += lik * ukj;
            }
            double d = s - A_orig[i * n + j];
            nR += d * d;
            nA += A_orig[i * n + j] * A_orig[i * n + j];
        }
    }
    return sqrt(nR) / sqrt(nA);
}

/* ||PA - LU||_F / ||A||_F  (带选主元) */
static double lu_pivot_error(int n, const double *A_orig, const double *LU, const int *piv)
{
    double nA = 0.0, nR = 0.0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            double s = 0.0;
            int kmax = (i < j) ? i : j;
            for (int k = 0; k <= kmax; k++) {
                double lik = (i > k) ? LU[i * n + k] : (i == k ? 1.0 : 0.0);
                double ukj = (k <= j) ? LU[k * n + j] : 0.0;
                s += lik * ukj;
            }
            double d = s - A_orig[piv[i] * n + j];
            nR += d * d;
            nA += A_orig[i * n + j] * A_orig[i * n + j];
        }
    }
    return sqrt(nR) / sqrt(nA);
}

/* ---------- 计时 ---------- */

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* ---------- 测试流程 ---------- */

typedef void (*mat_gen)(int, double *);

static const char *mat_name(mat_gen gen)
{
    if (gen == mat_random)     return "random";
    if (gen == mat_hilbert)    return "hilbert";
    if (gen == mat_diag_dom)   return "diag_dominant";
    return "?";
}

static void test_matrix(int n, mat_gen gen)
{
    printf("\n===== %s matrix, n = %d =====\n", mat_name(gen), n);

    double *A     = (double *)malloc((size_t)n * n * sizeof(double));
    double *A_lu  = (double *)malloc((size_t)n * n * sizeof(double));
    double *A_wrk = (double *)malloc((size_t)n * n * sizeof(double));
    double *b     = (double *)malloc(n * sizeof(double));
    double *x     = (double *)malloc(n * sizeof(double));

    gen(n, A);
    make_rhs(n, A, b);

    /* --- 1) 高斯消去法 (列主元, 求解) --- */
    memcpy(A_wrk, A, (size_t)n * n * sizeof(double));
    double t0 = now_sec();
    int ret = gauss_solve(n, A_wrk, b, x);
    double t1 = now_sec();

    if (ret == 0) {
        printf("  [Gauss solve]   time=%8.4f s  res=%10.3e  err_inf=%10.3e\n",
               t1 - t0, residual(n, A, x, b), error_linf(n, x));
    } else {
        printf("  [Gauss solve]   FAILED (singular)\n");
    }

    /* --- 2) LU 分解 (无选主元, 仅分解) --- */
    memcpy(A_lu, A, (size_t)n * n * sizeof(double));
    t0 = now_sec();
    ret = lu_decomp(n, A_lu);
    t1 = now_sec();

    if (ret == 0) {
        double err = lu_error(n, A, A_lu);
        printf("  [LU no pivot]   time=%8.4f s  ||A-LU||/||A||=%10.3e\n",
               t1 - t0, err);
    } else {
        printf("  [LU no pivot]   FAILED (zero pivot)\n");
    }

    /* --- 3) LU 分解 (列主元, 分解 + 求解) --- */
    memcpy(A_lu, A, (size_t)n * n * sizeof(double));
    int *piv = (int *)malloc(n * sizeof(int));
    t0 = now_sec();
    ret = lu_decomp_pivot(n, A_lu, piv);
    double t_lu = now_sec();
    if (ret == 0) {
        lu_solve(n, A_lu, piv, b, x);
        double t2 = now_sec();
        double err = lu_pivot_error(n, A, A_lu, piv);
        printf("  [LU w/ pivot]   time=%8.4f s (decomp=%8.4f)  ||PA-LU||/||A||=%10.3e  res=%10.3e\n",
               t2 - t0, t_lu - t0, err, residual(n, A, x, b));
    } else {
        printf("  [LU w/ pivot]   FAILED (singular)\n");
    }
    free(piv);

    free(A); free(A_lu); free(A_wrk); free(b); free(x);
}

/* ---------- 规模性能对比 (仅随机矩阵) ---------- */

static void benchmark_sizes(void)
{
    int sizes[] = {100, 200, 500, 1000, 2000};
    int ns = sizeof(sizes) / sizeof(sizes[0]);

    printf("\n\n========== 性能对比 (随机矩阵, 不同规模) ==========\n");
    printf("%6s  %12s  %12s  %12s  %14s\n",
           "n", "Gauss solve", "LU no piv", "LU + piv", "mflops(LU+piv)");

    for (int si = 0; si < ns; si++) {
        int n = sizes[si];
        size_t sz = (size_t)n * n;
        double *A  = (double *)malloc(sz * sizeof(double));
        double *A2 = (double *)malloc(sz * sizeof(double));
        double *b  = (double *)malloc(n * sizeof(double));
        double *x  = (double *)malloc(n * sizeof(double));
        int    *piv = (int *)malloc(n * sizeof(int));

        mat_random(n, A);
        make_rhs(n, A, b);

        /* Gauss solve */
        memcpy(A2, A, sz * sizeof(double));
        double t0 = now_sec();
        gauss_solve(n, A2, b, x);
        double t_gs = now_sec() - t0;

        /* LU no pivot */
        memcpy(A2, A, sz * sizeof(double));
        t0 = now_sec();
        int ok_lu = lu_decomp(n, A2);
        double t_lu = now_sec() - t0;
        if (ok_lu != 0) t_lu = -1.0;

        /* LU + pivot */
        memcpy(A2, A, sz * sizeof(double));
        t0 = now_sec();
        lu_decomp_pivot(n, A2, piv);
        lu_solve(n, A2, piv, b, x);
        double t_lup = now_sec() - t0;

        /* 理论 flops: ~2n³/3 for LU */
        double flops = 2.0 * n * n * n / 3.0;
        double mflops = flops / (t_lup > 0 ? t_lup : 1.0) / 1e6;

        printf("%6d  %12.4f  %12.4f  %12.4f  %14.1f\n",
               n, t_gs, t_lu, t_lup, mflops);

        free(A); free(A2); free(b); free(x); free(piv);
    }
}

/* ---------- main ---------- */

int main(void)
{
    srand(42);

    /* 小矩阵: 正确性验证 */
    int small[] = {10, 20};
    mat_gen gens[] = {mat_random, mat_hilbert, mat_diag_dom};
    int ng = sizeof(gens) / sizeof(gens[0]);

    for (int gi = 0; gi < ng; gi++)
        for (int si = 0; si < 2; si++)
            test_matrix(small[si], gens[gi]);

    /* 大矩阵: 性能测试 */
    benchmark_sizes();

    printf("\nDone.\n");
    return 0;
}
