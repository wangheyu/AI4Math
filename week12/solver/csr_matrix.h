#ifndef CSR_MATRIX_H
#define CSR_MATRIX_H

#include <string>
#include <vector>

struct CsrMatrix {
    int nrows, ncols, nnz;
    int N;          // original grid points per direction (including boundary)
    double h;       // grid spacing h = 1/(N-1)
    double h2inv;   // 1/h^2

    // CSR storage (CPU)
    std::vector<double> val;
    std::vector<int>    col_ind;
    std::vector<int>    row_ptr;

    // GPU pointers (allocated on demand)
    double *d_val     = nullptr;
    int    *d_col_ind = nullptr;
    int    *d_row_ptr = nullptr;
    bool    on_device = false;

    // Read from binary mat.dat (written by fdm3d/write_mat)
    static CsrMatrix read(const std::string &path);

    // Transfer CSR data to GPU (cudaMalloc + cudaMemcpy)
    void to_device();
    void free_device();

    // Exact solution for -Δu = 3π² sin(πx)sin(πy)sin(πz)
    std::vector<double> exact_solution() const;

    // RHS: f = 3π² sin(πx)sin(πy)sin(πz)
    std::vector<double> rhs() const;
};

#endif
