#include <amgcl/amg.hpp>
#include <amgcl/backend/cuda.hpp>
#include <amgcl/make_solver.hpp>
#include <amgcl/solver/cg.hpp>
#include <amgcl/coarsening/smoothed_aggregation.hpp>
#include <amgcl/relaxation/spai0.hpp>
#include <amgcl/adapter/crs_tuple.hpp>
#include "csr_matrix.h"
#include "eigen_ic.h"
#include "gpu_cg.h"
#include "test_common.h"
#include <iostream>

int main(int argc, char **argv) {
    std::string mat_path = (argc > 1) ? argv[1] : "../fdm3d/mat.dat";
    CsrMatrix A = CsrMatrix::read(mat_path);
    std::cout << "=== GPU CG Benchmarks ===" << std::endl;
    std::cout << "Matrix: " << A.nrows << " unknowns, " << A.nnz << " nnz" << std::endl;
    auto b = std::vector<double>(A.nrows, 1.0);
    CgParams params; params.max_iter = 10000; params.tol = 1e-8;

    std::vector<CgResult> results;
    std::vector<std::string> names;

    // Test 6: AMGCL CUDA AMG CG
    {
        cusparseHandle_t h; cusparseCreate(&h);
        typedef amgcl::backend::cuda<double> Backend;
        typedef amgcl::make_solver<
            amgcl::amg<Backend, amgcl::coarsening::smoothed_aggregation, amgcl::relaxation::spai0>,
            amgcl::solver::cg<Backend>> Solver;
        Backend::params bprm; bprm.cusparse_handle = h;
        Solver::params prm; prm.solver.maxiter = 10000; prm.solver.tol = 1e-8;

        CgResult res;
        double t0 = now_ms();
        auto ptr_r = amgcl::make_iterator_range(A.row_ptr.data(), A.row_ptr.data()+A.nrows+1);
        auto col_r = amgcl::make_iterator_range(A.col_ind.data(), A.col_ind.data()+A.nnz);
        auto val_r = amgcl::make_iterator_range(A.val.data(), A.val.data()+A.nnz);
        Solver solve(std::tie(A.nrows, ptr_r, col_r, val_r), prm, bprm);
        res.setup_time_ms = now_ms() - t0;
        std::cout << solve << std::endl;

        thrust::device_vector<double> d_b(b), d_x(A.nrows, 0.0);
        t0 = now_ms();
        auto [iters, resid] = solve(d_b, d_x);
        res.solve_time_ms = now_ms() - t0;
        res.iterations = iters; res.final_residual = resid;
        results.push_back(res); names.push_back("AMGCL CUDA AMG CG");
        cusparseDestroy(h);
    }

    // Test 7: cuBLAS CG
    {
        GpuContext ctx;
        std::cout << "Running cuBLAS CG..." << std::endl;
        auto x = std::vector<double>(A.nrows, 0.0);
        results.push_back(gpu_cg_solve_no_precond(A, b, x, params, ctx));
        names.push_back("cuBLAS CG");
    }

    // Test 8: cuBLAS IC(0) CG
    {
        GpuContext ctx;
        std::cout << "Running cuBLAS IC(0) CG..." << std::endl;
        EigenICPrecond ic(A);
        auto x = std::vector<double>(A.nrows, 0.0);
        results.push_back(gpu_cg_solve_ic(A, ic, b, x, params, ctx));
        names.push_back("cuBLAS IC(0) CG");
    }

    print_table(results, names);
    return 0;
}
