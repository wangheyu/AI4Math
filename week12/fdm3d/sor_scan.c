/*
 * sor_scan.c — 扫描 SOR 松弛参数 omega, 寻找最优值
 *
 * 对 N×N×N 网格的 3D Poisson 方程, 理论最优 omega 为:
 *   omega_opt = 2 / (1 + sin(pi * h))
 * 其中 h = 1/(N-1).
 *
 * 本程序对 omega ∈ [1.00, 1.99] 步长 0.05 (再加 omega_opt) 各跑一次 SOR,
 * 记录收敛所需迭代数与耗时, 输出供 plot_solution.py 绘图.
 *
 * 用法: ./sor_scan [N] [max_iter] [tol]
 *   默认 N=64 (扫描快), max_iter=20000, tol=1e-6
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
                f[IDX(i, j, k)] = rhs(i * h, y, z);
                u[IDX(i, j, k)] = 0.0;
            }
        }
    }
}

static double residual(const double *u, const double *f)
{
    double h2 = h * h;
    double res = 0.0;
    for (int k = 1; k < N - 1; k++)
        for (int j = 1; j < N - 1; j++)
            for (int i = 1; i < N - 1; i++) {
                double Au = (6.0 * u[IDX(i, j, k)]
                             - u[IDX(i + 1, j, k)] - u[IDX(i - 1, j, k)]
                             - u[IDX(i, j + 1, k)] - u[IDX(i, j - 1, k)]
                             - u[IDX(i, j, k + 1)] - u[IDX(i, j, k - 1)]) / h2;
                double r = f[IDX(i, j, k)] - Au;
                res += r * r;
            }
    return sqrt(res);
}

/* SOR with given omega, return iter count to reach tol */
static int sor(double *u, const double *f, int max_iter, double tol, double omega)
{
    double h2 = h * h;
    for (int iter = 1; iter <= max_iter; iter++) {
        for (int k = 1; k < N - 1; k++)
            for (int j = 1; j < N - 1; j++)
                for (int i = 1; i < N - 1; i++) {
                    double gs = (u[IDX(i + 1, j, k)] + u[IDX(i - 1, j, k)]
                               + u[IDX(i, j + 1, k)] + u[IDX(i, j - 1, k)]
                               + u[IDX(i, j, k + 1)] + u[IDX(i, j, k - 1)]
                               + h2 * f[IDX(i, j, k)]) / 6.0;
                    u[IDX(i, j, k)] = (1.0 - omega) * u[IDX(i, j, k)] + omega * gs;
                }
        if (iter % 50 == 0) {
            double rnorm = residual(u, f);
            if (rnorm < tol) return iter;
            if (!isfinite(rnorm)) return -1;  /* diverged */
        }
    }
    return max_iter;
}

int main(int argc, char **argv)
{
    int npoints = 64;
    int max_iter = 20000;
    double tol = 1e-6;

    if (argc > 1) npoints = atoi(argv[1]);
    if (argc > 2) max_iter = atoi(argv[2]);
    if (argc > 3) tol = atof(argv[3]);

    N = npoints;
    h = 1.0 / (N - 1);

    double omega_opt = 2.0 / (1.0 + sin(M_PI * h));

    printf("=== SOR omega 扫描 ===\n");
    printf("N = %d, h = %.6f, 理论最优 omega_opt = %.6f\n", N, h, omega_opt);
    printf("max_iter = %d, tol = %e\n\n", max_iter, tol);

    size_t size = (size_t)N * N * N;
    double *u = (double *)calloc(size, sizeof(double));
    double *f = (double *)malloc(size * sizeof(double));
    if (!u || !f) { fprintf(stderr, "malloc failed\n"); return 1; }

    init(u, f);   /* 仅一次: 设置 f, u 初始为 0 */

    FILE *log = fopen("sor_scan.txt", "w");
    if (log) fprintf(log, "# omega  iter  time(s)\n");

    /* 扫描 omega 列表: 粗扫 + 在最优附近细扫 */
    double omegas[64];
    int n_omega = 0;
    for (double w = 1.00; w < 1.95 + 1e-6; w += 0.05) omegas[n_omega++] = w;
    omegas[n_omega++] = omega_opt;   /* 解析最优 */
    omegas[n_omega++] = omega_opt - 0.01;
    omegas[n_omega++] = omega_opt + 0.01;
    omegas[n_omega++] = 1.97;
    omegas[n_omega++] = 1.99;

    printf("%-8s %-8s %-12s %-8s\n", "omega", "iter", "time(s)", "备注");
    printf("-------------------------------------------\n");

    for (int idx = 0; idx < n_omega; idx++) {
        double omega = omegas[idx];
        memset(u, 0, size * sizeof(double));  /* 仅重置 u, f 不变 */

        double t0 = now_sec();
        int iters = sor(u, f, max_iter, tol, omega);
        double t = now_sec() - t0;

        const char *note = "";
        if (fabs(omega - omega_opt) < 1e-6) note = "<- omega_opt";
        else if (iters == max_iter) note = "未收敛";
        else if (iters < 0) { note = "发散"; iters = -1; }

        printf("%-8.4f %-8d %-12.4f %s\n", omega, iters, t, note);
        if (log && iters > 0) fprintf(log, "%.4f %d %.4f\n", omega, iters, t);
    }

    if (log) fclose(log);

    free(u); free(f);
    printf("\nResults written to sor_scan.txt\n");
    return 0;
}
