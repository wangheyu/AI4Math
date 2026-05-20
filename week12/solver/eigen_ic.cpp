#include "eigen_ic.h"
#include "test_common.h"
#include <cstring>

EigenICPrecond::EigenICPrecond(const CsrMatrix &A_in) {
    n_ = A_in.nrows;
    double t0 = now_ms();

    // Count lower-triangle nnz per column
    std::vector<int> col_counts(n_, 0);
    for (int i = 0; i < n_; i++)
        for (int p = A_in.row_ptr[i]; p < A_in.row_ptr[i + 1]; p++)
            if (A_in.col_ind[p] <= i) col_counts[A_in.col_ind[p]]++;

    // Build ColMajor sparse (lower triangle)
    Eigen::SparseMatrix<double, Eigen::ColMajor> Ae(n_, n_);
    int *outer = Ae.outerIndexPtr();
    outer[0] = 0;
    for (int j = 0; j < n_; j++) outer[j+1] = outer[j] + col_counts[j];
    Ae.resizeNonZeros(outer[n_]);
    int *inner = Ae.innerIndexPtr();
    double *vals = Ae.valuePtr();
    std::vector<int> cur(n_, 0);
    for (int i = 0; i < n_; i++) {
        for (int p = A_in.row_ptr[i]; p < A_in.row_ptr[i + 1]; p++) {
            int j = A_in.col_ind[p];
            if (j <= i) {
                int pos = outer[j] + cur[j]++;
                inner[pos] = i;
                vals[pos]  = A_in.val[p];
            }
        }
    }
    Ae.makeCompressed();

    // IC(0) factorization
    ic_.setInitialShift(1e-4);
    ic_.compute(Ae);

    // Extract L+D for GPU transfer
    D_.resize(n_);
    const auto &scaling = ic_.scalingS();
    for (int i = 0; i < n_; i++) D_[i] = scaling[i];

    // Extract L in CSR (unit diagonal implied, store as 1.0)
    const auto &L = ic_.matrixL();
    L_row_ptr_.resize(n_ + 1, 0);
    for (int col = 0; col < L.outerSize(); col++) {
        for (Eigen::SparseMatrix<double,Eigen::ColMajor,int>::InnerIterator it(L, col); it; ++it)
            L_row_ptr_[static_cast<int>(it.row()) + 1]++;
    }
    for (int i = 0; i < n_; i++) L_row_ptr_[i + 1] += L_row_ptr_[i];
    int nnz_L = L_row_ptr_[n_];
    L_val_.resize(nnz_L);
    L_col_ind_.resize(nnz_L);
    std::vector<int> row_cur = L_row_ptr_;
    for (int col = 0; col < L.outerSize(); col++) {
        for (Eigen::SparseMatrix<double,Eigen::ColMajor,int>::InnerIterator it(L, col); it; ++it) {
            int row = static_cast<int>(it.row());
            int pos = row_cur[row]++;
            L_val_[pos]     = (row == col) ? 1.0 : it.value();
            L_col_ind_[pos] = static_cast<int>(it.col());
        }
    }

    setup_time_ms_ = now_ms() - t0;
}

void EigenICPrecond::apply(const double *r, double *z) const {
    // Use Eigen's internal solve — verified correct
    Eigen::Map<const Eigen::VectorXd> r_map(r, n_);
    Eigen::Map<Eigen::VectorXd>       z_map(z, n_);
    z_map = ic_.solve(r_map);
}
