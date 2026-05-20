#include <amgcl/amg.hpp>
#include <amgcl/backend/cuda.hpp>
#include <amgcl/make_solver.hpp>
#include <amgcl/solver/cg.hpp>
#include <amgcl/coarsening/smoothed_aggregation.hpp>
#include <amgcl/relaxation/spai0.hpp>
#include <amgcl/adapter/crs_tuple.hpp>

#include <cmath>
#include <iostream>
#include <vector>

#include <cuda_runtime.h>
#include <cusparse.h>
#include <thrust/copy.h>
#include <thrust/device_vector.h>
#include <thrust/host_vector.h>

// Assemble 1D Poisson matrix: tridiagonal [ -1  2  -1 ]
auto poisson1d(int n) {
    std::vector<int>    ptr(n + 1);
    std::vector<int>    col(3 * n - 2);
    std::vector<double> val(3 * n - 2);

    ptr[0] = 0;
    int idx = 0;
    for (int i = 0; i < n; ++i) {
        if (i > 0) { col[idx] = i - 1; val[idx] = -1.0; ++idx; }
        col[idx] = i;     val[idx] =  2.0; ++idx;
        if (i < n - 1) { col[idx] = i + 1; val[idx] = -1.0; ++idx; }
        ptr[i + 1] = idx;
    }
    return std::make_tuple(ptr, col, val);
}

int main() {
    const int n = 1000;

    std::cout << "=== AMGCL CUDA Backend Solve Test ===" << std::endl;
    std::cout << "System: " << n << "x" << n << " Poisson 1D" << std::endl;

    // 1. Assemble matrix on host
    std::vector<int>    ptr, col;
    std::vector<double> val;
    std::tie(ptr, col, val) = poisson1d(n);
    std::cout << "  nnz: " << ptr[n] << std::endl;

    // 2. RHS and initial guess on device
    thrust::device_vector<double> rhs(n, 1.0);
    thrust::device_vector<double> x(n, 0.0);

    // 3. Create cuSPARSE handle
    cusparseHandle_t cusparse_handle;
    cusparseCreate(&cusparse_handle);

    // 4. Setup AMG solver with CUDA backend
    typedef amgcl::backend::cuda<double> Backend;
    typedef amgcl::make_solver<
        amgcl::amg<Backend, amgcl::coarsening::smoothed_aggregation, amgcl::relaxation::spai0>,
        amgcl::solver::cg<Backend>
    > Solver;

    Backend::params bprm;
    bprm.cusparse_handle = cusparse_handle;

    Solver::params prm;
    prm.solver.maxiter = 500;
    prm.solver.tol     = 1e-8;

    std::cout << "Building AMG preconditioner on GPU..." << std::endl;
    auto A = std::tie(n, ptr, col, val);
    Solver solve(A, prm, bprm);
    std::cout << solve << std::endl;

    // 5. Solve
    std::cout << "Solving on GPU..." << std::endl;
    auto [iters, resid] = solve(rhs, x);

    std::cout << "  Iterations:      " << iters << std::endl;
    std::cout << "  Residual (||r||): " << resid << std::endl;

    // 6. Copy result back to host, verify against analytical solution
    thrust::host_vector<double> x_host = x;

    // Analytical: u_i = i*(n+1-i)/2 for discrete system (-u_{i-1}+2u_i-u_{i+1})=1
    double max_err = 0.0;
    for (int i = 0; i < n; ++i) {
        double expected = 0.5 * (i + 1) * (n - i);
        double err = std::abs(x_host[i] - expected);
        if (err > max_err) max_err = err;
    }
    std::cout << "  Max error vs analytical: " << max_err << std::endl;

    cusparseDestroy(cusparse_handle);

    bool pass = (iters <= 50) && (resid < 1e-6) && (max_err < 1e-3);
    std::cout << std::endl << "[" << (pass ? "PASS" : "FAIL") << "] AMGCL CUDA backend" << std::endl;
    return pass ? 0 : 1;
}
