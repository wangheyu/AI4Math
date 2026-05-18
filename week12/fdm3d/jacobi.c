/*
 * jacobi.c — 3D Poisson 方程的 Jacobi 迭代求解
 *
 * 与 main.c (Gauss-Seidel + SOR) 对比: Jacobi 是最简单的迭代法
 * 每步需保留旧解 u_old, 用 u_old 计算所有 u_new, 然后整体替换.
 *
 * 用法: ./jacobi [N] [max_iter] [tol]
 *   默认 N=101 (与 mat.dat 一致), max_iter=200000, tol=1e-6
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define IDX(i, j, k) ((i) + N * ((j) + N * (k)))

static int N;
static double h;

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static double u_exact(double x, double y, double z)
{
    return sin(M_PI * x) * sin(M_PI * y) * sin(M_PI * z);
}

static double rhs(double x, double y, double z)
{
    return 3.0 * M_PI * M_PI * sin(M_PI * x) * sin(M_PI * y) * sin(M_PI * z);
}

static void init(double *u, double *f)
{
    for (int k = 0; k < N; k++) {
        double z = k * h;
        for (int j = 0; j < N; j++) {
            double y = j * h;
            for (int i = 0; i < N; i++) {
                double x = i * h;
                f[IDX(i, j, k)] = rhs(x, y, z);
                u[IDX(i, j, k)] = 0.0;
            }
        }
    }
}

static double residual(const double *u, const double *f)
{
    double h2 = h * h;
    double res = 0.0;
    for (int k = 1; k < N - 1; k++) {
        for (int j = 1; j < N - 1; j++) {
            for (int i = 1; i < N - 1; i++) {
                double Au = (6.0 * u[IDX(i, j, k)]
                             - u[IDX(i + 1, j, k)] - u[IDX(i - 1, j, k)]
                             - u[IDX(i, j + 1, k)] - u[IDX(i, j - 1, k)]
                             - u[IDX(i, j, k + 1)] - u[IDX(i, j, k - 1)]) / h2;
                double r = f[IDX(i, j, k)] - Au;
                res += r * r;
            }
        }
    }
    return sqrt(res);
}

/* Jacobi: u_new[i] = (f[i]*h^2 + sum_邻居 u_old[i]) / 6
 * 需保留 u_old, 整步并行更新 */
static int jacobi(double *u, double *u_new, const double *f,
                  int max_iter, double tol, FILE *log)
{
    double h2 = h * h;
    int iter;
    for (iter = 1; iter <= max_iter; iter++) {
        for (int k = 1; k < N - 1; k++) {
            for (int j = 1; j < N - 1; j++) {
                for (int i = 1; i < N - 1; i++) {
                    u_new[IDX(i, j, k)] =
                        (u[IDX(i + 1, j, k)] + u[IDX(i - 1, j, k)]
                       + u[IDX(i, j + 1, k)] + u[IDX(i, j - 1, k)]
                       + u[IDX(i, j, k + 1)] + u[IDX(i, j, k - 1)]
                       + h2 * f[IDX(i, j, k)]) / 6.0;
                }
            }
        }
        /* 整体替换 — Jacobi 的关键 */
        for (int k = 1; k < N - 1; k++)
            for (int j = 1; j < N - 1; j++)
                for (int i = 1; i < N - 1; i++)
                    u[IDX(i, j, k)] = u_new[IDX(i, j, k)];

        if (iter % 500 == 0 || iter == 1) {
            double rnorm = residual(u, f);
            printf("  iter %6d  |r| = %12.6e\n", iter, rnorm);
            if (log) fprintf(log, "%d %.6e\n", iter, rnorm);
            if (rnorm < tol) {
                printf("  converged at iter %d, |r| = %12.6e\n", iter, rnorm);
                return iter;
            }
        }
    }
    double rnorm = residual(u, f);
    printf("  reached max_iter %d, |r| = %12.6e\n", max_iter, rnorm);
    return max_iter;
}

static void errors(const double *u)
{
    double l2 = 0.0, linf = 0.0;
    for (int k = 0; k < N; k++) {
        double z = k * h;
        for (int j = 0; j < N; j++) {
            double y = j * h;
            for (int i = 0; i < N; i++) {
                double x = i * h;
                double err = fabs(u[IDX(i, j, k)] - u_exact(x, y, z));
                l2 += err * err;
                if (err > linf) linf = err;
            }
        }
    }
    l2 = sqrt(l2) / (N * N * N);
    printf("  L2 error   = %12.6e\n", l2);
    printf("  Linf error = %12.6e\n", linf);
}

int main(int argc, char **argv)
{
    int npoints = 101;
    int max_iter = 200000;
    double tol = 1e-6;

    if (argc > 1) npoints = atoi(argv[1]);
    if (argc > 2) max_iter = atoi(argv[2]);
    if (argc > 3) tol = atof(argv[3]);

    N = npoints;
    h = 1.0 / (N - 1);

    printf("=== Jacobi 迭代 ===\n");
    printf("N = %d, h = %.6f, unknowns = %d\n", N, h, (N - 2) * (N - 2) * (N - 2));
    printf("max_iter = %d, tol = %e\n\n", max_iter, tol);

    size_t size = (size_t)N * N * N;
    double *u     = (double *)calloc(size, sizeof(double));
    double *u_new = (double *)calloc(size, sizeof(double));
    double *f     = (double *)malloc(size * sizeof(double));
    if (!u || !u_new || !f) { fprintf(stderr, "malloc failed\n"); return 1; }

    init(u, f);
    printf("Initial |r| = %12.6e\n\n", residual(u, f));

    FILE *log = fopen("conv_jacobi.txt", "w");

    double t0 = now_sec();
    int iters = jacobi(u, u_new, f, max_iter, tol, log);
    double t = now_sec() - t0;

    if (log) fclose(log);

    printf("\nIterations: %d\n", iters);
    printf("Time:       %.3f s\n", t);
    printf("Time/iter:  %.3f ms\n", t * 1000 / iters);
    errors(u);

    free(u); free(u_new); free(f);
    return 0;
}
