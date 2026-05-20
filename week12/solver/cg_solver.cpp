#include "cg_solver.h"
#include <cblas.h>
#include <cstring>
#include <cmath>

void csr_spmv(const CsrMatrix &A, const double *x, double *y) {
    const int n = A.nrows;
    for (int i = 0; i < n; i++) {
        double s = 0.0;
        for (int p = A.row_ptr[i]; p < A.row_ptr[i + 1]; p++)
            s += A.val[p] * x[A.col_ind[p]];
        y[i] = s;
    }
}

CgResult cg_solve_no_precond(
    const CsrMatrix &A,
    const std::vector<double> &b,
    std::vector<double> &x,
    const CgParams &params)
{
    const int n = A.nrows;
    std::vector<double> r(n), p(n), Ap(n);

    csr_spmv(A, x.data(), r.data());
    for (int i = 0; i < n; i++) r[i] = b[i] - r[i];
    std::memcpy(p.data(), r.data(), n * sizeof(double));

    double rho_old = cblas_ddot(n, r.data(), 1, r.data(), 1);
    double bnorm = cblas_dnrm2(n, b.data(), 1);
    double tol_scaled = params.tol * bnorm;

    CgResult res;
    res.setup_time_ms = 0;

    double t0 = now_ms();
    int iter;
    for (iter = 0; iter < params.max_iter; iter++) {
        csr_spmv(A, p.data(), Ap.data());
        double pAp = cblas_ddot(n, p.data(), 1, Ap.data(), 1);
        double alpha = rho_old / pAp;

        cblas_daxpy(n,  alpha, p.data(), 1, x.data(), 1);
        cblas_daxpy(n, -alpha, Ap.data(), 1, r.data(), 1);

        double rho_new = cblas_ddot(n, r.data(), 1, r.data(), 1);
        double rnorm = std::sqrt(rho_new);

        if (rnorm < tol_scaled) { iter++; break; }

        double beta = rho_new / rho_old;
        for (int i = 0; i < n; i++) p[i] = r[i] + beta * p[i];
        rho_old = rho_new;
    }
    res.solve_time_ms = now_ms() - t0;
    res.iterations = iter;
    res.final_residual = std::sqrt(cblas_ddot(n, r.data(), 1, r.data(), 1));
    return res;
}

CgResult cg_solve_ic_precond(
    const CsrMatrix &A,
    const std::vector<double> &b,
    std::vector<double> &x,
    const EigenICPrecond &ic,
    const CgParams &params)
{
    const int n = A.nrows;
    std::vector<double> r(n), z(n), p(n), Ap(n);

    csr_spmv(A, x.data(), r.data());
    for (int i = 0; i < n; i++) r[i] = b[i] - r[i];

    ic.apply(r.data(), z.data());
    std::memcpy(p.data(), z.data(), n * sizeof(double));

    double rho_old = cblas_ddot(n, r.data(), 1, z.data(), 1);
    double bnorm = cblas_dnrm2(n, b.data(), 1);
    double tol_scaled = params.tol * bnorm;

    CgResult res;
    res.setup_time_ms = ic.setup_time_ms();

    double t0 = now_ms();
    int iter;
    for (iter = 0; iter < params.max_iter; iter++) {
        csr_spmv(A, p.data(), Ap.data());
        double pAp = cblas_ddot(n, p.data(), 1, Ap.data(), 1);
        double alpha = rho_old / pAp;

        cblas_daxpy(n,  alpha, p.data(), 1, x.data(), 1);
        cblas_daxpy(n, -alpha, Ap.data(), 1, r.data(), 1);

        ic.apply(r.data(), z.data());

        double rho_new = cblas_ddot(n, r.data(), 1, z.data(), 1);
        // Use L2 norm of true residual for convergence check (more robust)
        double r_l2 = cblas_dnrm2(n, r.data(), 1);

        if (r_l2 < tol_scaled) { iter++; break; }

        double beta = rho_new / rho_old;
        for (int i = 0; i < n; i++) p[i] = z[i] + beta * p[i];
        rho_old = rho_new;
    }
    res.solve_time_ms = now_ms() - t0;
    res.iterations = iter;
    res.final_residual = std::sqrt(cblas_ddot(n, r.data(), 1, r.data(), 1));
    return res;
}
