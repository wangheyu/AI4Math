#ifndef EIGEN_IC_H
#define EIGEN_IC_H

#include "csr_matrix.h"
#include <vector>
#include <Eigen/Sparse>
#include <Eigen/Dense>
#include <Eigen/src/IterativeLinearSolvers/IncompleteCholesky.h>

class EigenICPrecond {
public:
    explicit EigenICPrecond(const CsrMatrix &A);

    // Apply M^{-1}: z = M^{-1} * r  (handles L*D*L^T)
    void apply(const double *r, double *z) const;

    // L in CSR (unit-diagonal implied) + D scaling
    const std::vector<double>& L_val()     const { return L_val_; }
    const std::vector<int>&    L_col_ind() const { return L_col_ind_; }
    const std::vector<int>&    L_row_ptr() const { return L_row_ptr_; }
    const std::vector<double>& D()         const { return D_; }

    double setup_time_ms() const { return setup_time_ms_; }

private:
    int n_;
    double setup_time_ms_;
    std::vector<double> L_val_, D_;
    std::vector<int>    L_col_ind_, L_row_ptr_;
    mutable std::vector<double> work_;

    // Eigen IC object, kept alive for solve
    using ICType = Eigen::IncompleteCholesky<double, Eigen::Lower, Eigen::NaturalOrdering<int>>;
    ICType ic_;
};

#endif
