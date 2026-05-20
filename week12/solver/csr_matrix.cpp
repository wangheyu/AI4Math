#include "csr_matrix.h"
#include <fstream>
#include <stdexcept>
#include <cmath>
#include <cstring>
#include <cuda_runtime.h>

CsrMatrix CsrMatrix::read(const std::string &path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) throw std::runtime_error("Cannot open " + path);

    int header[4];  // nrows, ncols, nnz, N
    f.read(reinterpret_cast<char*>(header), 4 * sizeof(int));

    CsrMatrix A;
    A.nrows = header[0];
    A.ncols = header[1];
    A.nnz   = header[2];
    A.N     = header[3];

    f.read(reinterpret_cast<char*>(&A.h), sizeof(double));
    f.read(reinterpret_cast<char*>(&A.h2inv), sizeof(double));

    A.val.resize(A.nnz);
    A.col_ind.resize(A.nnz);
    A.row_ptr.resize(A.nrows + 1);

    f.read(reinterpret_cast<char*>(A.val.data()), A.nnz * sizeof(double));
    f.read(reinterpret_cast<char*>(A.col_ind.data()), A.nnz * sizeof(int));
    f.read(reinterpret_cast<char*>(A.row_ptr.data()), (A.nrows + 1) * sizeof(int));

    return A;
}

void CsrMatrix::to_device() {
    if (on_device) return;
    cudaMalloc(&d_val,     nnz * sizeof(double));
    cudaMalloc(&d_col_ind, nnz * sizeof(int));
    cudaMalloc(&d_row_ptr, (nrows + 1) * sizeof(int));
    cudaMemcpy(d_val,     val.data(),     nnz * sizeof(double), cudaMemcpyHostToDevice);
    cudaMemcpy(d_col_ind, col_ind.data(), nnz * sizeof(int),    cudaMemcpyHostToDevice);
    cudaMemcpy(d_row_ptr, row_ptr.data(), (nrows + 1) * sizeof(int), cudaMemcpyHostToDevice);
    on_device = true;
}

void CsrMatrix::free_device() {
    if (d_val)     { cudaFree(d_val); d_val = nullptr; }
    if (d_col_ind) { cudaFree(d_col_ind); d_col_ind = nullptr; }
    if (d_row_ptr) { cudaFree(d_row_ptr); d_row_ptr = nullptr; }
    on_device = false;
}

std::vector<double> CsrMatrix::exact_solution() const {
    int n = N - 2;  // interior points per direction
    std::vector<double> u(nrows);
    for (int i = 0; i < n; i++) {
        double x = (i + 1) * h;
        for (int j = 0; j < n; j++) {
            double y = (j + 1) * h;
            for (int k = 0; k < n; k++) {
                double z = (k + 1) * h;
                int idx = i + n * (j + n * k);
                u[idx] = std::sin(M_PI * x) * std::sin(M_PI * y) * std::sin(M_PI * z);
            }
        }
    }
    return u;
}

std::vector<double> CsrMatrix::rhs() const {
    int n = N - 2;
    double f0 = 3.0 * M_PI * M_PI;
    std::vector<double> b(nrows);
    for (int i = 0; i < n; i++) {
        double x = (i + 1) * h;
        for (int j = 0; j < n; j++) {
            double y = (j + 1) * h;
            for (int k = 0; k < n; k++) {
                double z = (k + 1) * h;
                int idx = i + n * (j + n * k);
                b[idx] = f0 * std::sin(M_PI * x) * std::sin(M_PI * y) * std::sin(M_PI * z);
            }
        }
    }
    return b;
}
