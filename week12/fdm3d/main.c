#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define IDX(i, j, k) ((i) + N * ((j) + N * (k)))

static int N;
static double h;

static double u_exact(double x, double y, double z)
{
    return sin(M_PI * x) * sin(M_PI * y) * sin(M_PI * z);
}

static double rhs(double x, double y, double z)
{
    return 3.0 * M_PI * M_PI * sin(M_PI * x) * sin(M_PI * y) * sin(M_PI * z);
}

/* initialize f at all grid points and set boundary values for u */
static void init(double *u, double *f)
{
    for (int k = 0; k < N; k++) {
        double z = k * h;
        for (int j = 0; j < N; j++) {
            double y = j * h;
            for (int i = 0; i < N; i++) {
                double x = i * h;
                int idx = IDX(i, j, k);
                f[idx] = rhs(x, y, z);
                if (i == 0 || i == N - 1 || j == 0 || j == N - 1 || k == 0 || k == N - 1)
                    u[idx] = 0.0;
                else
                    u[idx] = 0.0; /* initial guess */
            }
        }
    }
}

/* compute residual r = f - A*u, return L2 norm */
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

/* Gauss-Seidel with SOR. Returns number of iterations performed. */
static int solve(double *u, const double *f, int max_iter, double tol, double omega, FILE *log)
{
    double h2 = h * h;
    for (int iter = 1; iter <= max_iter; iter++) {
        for (int k = 1; k < N - 1; k++) {
            for (int j = 1; j < N - 1; j++) {
                for (int i = 1; i < N - 1; i++) {
                    double gs = (u[IDX(i + 1, j, k)] + u[IDX(i - 1, j, k)]
                                 + u[IDX(i, j + 1, k)] + u[IDX(i, j - 1, k)]
                                 + u[IDX(i, j, k + 1)] + u[IDX(i, j, k - 1)]
                                 + h2 * f[IDX(i, j, k)]) / 6.0;
                    u[IDX(i, j, k)] = (1.0 - omega) * u[IDX(i, j, k)] + omega * gs;
                }
            }
        }

        double rnorm = residual(u, f);
        if (iter % 50 == 0 || iter == 1) {
            if (iter % 200 == 0 || iter == 1)
                printf("  iter %6d  |r| = %12.6e\n", iter, rnorm);
            if (log) fprintf(log, "%d %.6e\n", iter, rnorm);
        }
        if (rnorm < tol) {
            printf("  converged at iter %d, |r| = %12.6e\n", iter, rnorm);
            if (log) fprintf(log, "%d %.6e\n", iter, rnorm);
            return iter;
        }
    }
    printf("  warning: did not converge within %d iterations\n", max_iter);
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
                double exact = u_exact(x, y, z);
                double err = fabs(u[IDX(i, j, k)] - exact);
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
    int npoints = 64;
    int max_iter = 30000;
    double tol = 1e-6;
    double omega = 1.0;

    if (argc > 1) npoints = atoi(argv[1]);
    if (argc > 2) omega = atof(argv[2]);
    if (argc > 3) max_iter = atoi(argv[3]);
    if (argc > 4) tol = atof(argv[4]);

    N = npoints;
    h = 1.0 / (N - 1);

    printf("3D Poisson equation on unit cube, N = %d, h = %.6f\n", N, h);
    printf("omega = %.3f, max_iter = %d, tol = %e\n\n", omega, max_iter, tol);

    /* 1D contiguous array of size N^3 */
    size_t size = (size_t)N * N * N;
    double *u = (double *)malloc(size * sizeof(double));
    double *f = (double *)malloc(size * sizeof(double));
    if (!u || !f) { fprintf(stderr, "malloc failed\n"); return 1; }

    init(u, f);

    printf("Initial residual |r| = %12.6e\n", residual(u, f));
    printf("Solving with Gauss-Seidel (SOR ω=%.2f)...\n", omega);

    /* 选择日志文件名: omega=1 → conv_gs.txt; else → conv_sor.txt */
    const char *logname = (fabs(omega - 1.0) < 1e-6) ? "conv_gs.txt" : "conv_sor.txt";
    FILE *log = fopen(logname, "w");

    int iters = solve(u, f, max_iter, tol, omega, log);
    if (log) fclose(log);
    printf("\nDone in %d iterations. Conv log -> %s\n\n", iters, logname);

    printf("Error against exact solution u = sin(πx)sin(πy)sin(πz):\n");
    errors(u);

    free(u);
    free(f);
    return 0;
}
