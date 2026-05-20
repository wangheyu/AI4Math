#include <amgcl/amg.hpp>
#include <amgcl/backend/builtin.hpp>
#include <amgcl/make_solver.hpp>
#include <amgcl/solver/cg.hpp>
#include <amgcl/coarsening/smoothed_aggregation.hpp>
#include <amgcl/relaxation/spai0.hpp>
#include <amgcl/adapter/crs_tuple.hpp>
#include "csr_matrix.h"
#include "test_common.h"
#include <iostream>

int main(int argc, char **argv) {
    std::string mat_path = (argc > 1) ? argv[1] : "../fdm3d/mat.dat";
    std::cout << "=== AMGCL CPU AMG CG ===" << std::endl;
    CsrMatrix A = CsrMatrix::read(mat_path);
    std::cout << "Matrix: " << A.nrows << " unknowns, " << A.nnz << " nnz" << std::endl;

    auto b = std::vector<double>(A.nrows, 1.0);

    typedef amgcl::backend::builtin<double> Backend;
    typedef amgcl::make_solver<
        amgcl::amg<Backend, amgcl::coarsening::smoothed_aggregation, amgcl::relaxation::spai0>,
        amgcl::solver::cg<Backend>
    > Solver;

    Solver::params prm;
    prm.solver.maxiter = 10000;
    prm.solver.tol     = 1e-8;

    auto ptr_r = amgcl::make_iterator_range(A.row_ptr.data(), A.row_ptr.data() + A.nrows + 1);
    auto col_r = amgcl::make_iterator_range(A.col_ind.data(), A.col_ind.data() + A.nnz);
    auto val_r = amgcl::make_iterator_range(A.val.data(),     A.val.data()     + A.nnz);
    auto A_amg = std::tie(A.nrows, ptr_r, col_r, val_r);

    CgResult res;
    double t0 = now_ms();
    Solver solve(A_amg, prm);
    res.setup_time_ms = now_ms() - t0;

    std::cout << solve << std::endl;

    auto x = std::vector<double>(A.nrows, 0.0);

    t0 = now_ms();
    auto [iters, resid] = solve(b, x);
    res.solve_time_ms = now_ms() - t0;
    res.iterations = iters;
    res.final_residual = resid;

    print_table({res}, {"AMGCL CPU AMG CG"});
    return 0;
}
