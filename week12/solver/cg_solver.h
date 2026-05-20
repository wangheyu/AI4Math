#ifndef CG_SOLVER_H
#define CG_SOLVER_H

#include "csr_matrix.h"
#include "eigen_ic.h"
#include "test_common.h"
#include <vector>

// CSR SpMV: y = A * x
void csr_spmv(const CsrMatrix &A, const double *x, double *y);

// CG without preconditioner
CgResult cg_solve_no_precond(
    const CsrMatrix &A, const std::vector<double> &b,
    std::vector<double> &x, const CgParams &params = CgParams{});

// CG with Eigen IC(0) preconditioner
CgResult cg_solve_ic_precond(
    const CsrMatrix &A, const std::vector<double> &b,
    std::vector<double> &x, const EigenICPrecond &ic,
    const CgParams &params = CgParams{});

#endif
