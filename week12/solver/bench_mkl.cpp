#include "csr_matrix.h"
#include "cg_solver.h"
#include "eigen_ic.h"
#include "test_common.h"
#include <iostream>

int main(int argc, char **argv) {
    std::string mat_path = (argc > 1) ? argv[1] : "../fdm3d/mat.dat";
    std::cout << "=== MKL CG Benchmarks ===" << std::endl;
    CsrMatrix A = CsrMatrix::read(mat_path);
    std::cout << "Matrix: " << A.nrows << " unknowns, " << A.nnz << " nnz" << std::endl;
    auto b = std::vector<double>(A.nrows, 1.0);
    CgParams params;
    params.max_iter = 10000; params.tol = 1e-8;

    std::vector<CgResult> results;
    std::vector<std::string> names;

    {   // Test 3: no precond
        auto x = std::vector<double>(A.nrows, 0.0);
        results.push_back(cg_solve_no_precond(A, b, x, params));
        names.push_back("MKL CG");
    }
    {   // Test 4: IC(0)
        EigenICPrecond ic(A);
        auto x = std::vector<double>(A.nrows, 0.0);
        results.push_back(cg_solve_ic_precond(A, b, x, ic, params));
        names.push_back("MKL IC(0) CG");
    }

    print_table(results, names);
    return 0;
}
