#ifndef TEST_COMMON_H
#define TEST_COMMON_H

#include <string>
#include <vector>
#include <chrono>
#include <iostream>
#include <iomanip>
#include <functional>

struct CgParams {
    int    max_iter  = 10000;
    double tol       = 1e-8;
    bool   verbose   = false;
};

struct CgResult {
    int    iterations;
    double final_residual;
    double setup_time_ms;
    double solve_time_ms;

    double total_time_ms() const { return setup_time_ms + solve_time_ms; }
    bool   converged()     const { return iterations < 50000; }
};

// High-res timer
inline double now_ms() {
    namespace cr = std::chrono;
    return cr::duration<double, std::milli>(cr::high_resolution_clock::now()
                                            .time_since_epoch()).count();
}

// Print comparison table
inline void print_table(const std::vector<CgResult> &res,
                        const std::vector<std::string> &names)
{
    std::cout << std::endl;
    std::cout << std::left << std::setw(28) << "Test"
              << std::right << std::setw(8)  << "Iters"
              << std::setw(14) << "|r|"
              << std::setw(12) << "Setup(ms)"
              << std::setw(12) << "Solve(ms)"
              << std::setw(12) << "Total(ms)"
              << std::endl;
    std::cout << std::string(86, '-') << std::endl;

    for (size_t i = 0; i < res.size(); i++) {
        std::cout << std::left  << std::setw(28) << names[i]
                  << std::right << std::setw(8)  << res[i].iterations
                  << std::scientific << std::setprecision(3)
                  << std::setw(14) << res[i].final_residual
                  << std::fixed << std::setprecision(1)
                  << std::setw(12) << res[i].setup_time_ms
                  << std::setw(12) << res[i].solve_time_ms
                  << std::setw(12) << res[i].total_time_ms()
                  << std::endl;
    }
    std::cout << std::string(86, '-') << std::endl;
}

#endif
