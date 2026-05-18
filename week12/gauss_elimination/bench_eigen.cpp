/*
 * bench_eigen.cpp — Eigen 3.4.0 LU 分解 + 求解性能测试
 *
 * Eigen 是 C++ 模板头文件库, 无需链接 BLAS/LAPACK.
 * 编译器自动内联展开表达式模板, 生成高度优化的 SIMD 代码.
 *
 * 编译 (需 -I 指向 Eigen 头文件):
 *   g++ -O3 -march=native -fopenmp -I/tmp/eigen-3.4.0 \
 *       -o bench_eigen bench_eigen.cpp -lm
 */

#include <Eigen/Dense>
#include <Eigen/LU>
#include <iostream>
#include <iomanip>
#include <chrono>
#include <random>
#include <cmath>

using namespace Eigen;
using namespace std;
using namespace std::chrono;

static double now_sec()
{
    return duration<double>(steady_clock::now().time_since_epoch()).count();
}

int main()
{
    int sizes[] = {100, 200, 500, 1000, 2000, 4000};

    cout << "Eigen 3.4.0 — PartialPivLU (列主元 LU 分解 + 求解)" << endl;
#ifdef _OPENMP
    cout << "OpenMP enabled" << endl;
#endif
    cout << endl;
    cout << setw(6) << "n"
         << setw(12) << "factor(s)" << setw(12) << "solve(s)"
         << setw(12) << "total(s)" << setw(12) << "GFLOPS" << endl;
    cout << "----------------------------------------------------------" << endl;

    for (int si = 0; si < 6; si++) {
        int n = sizes[si];
        double flops = 2.0 * n * n * n / 3.0 + 2.0 * n * n;

        MatrixXd A(n, n);
        VectorXd b(n), x(n);

        /* 生成随机矩阵 (同 C 版 seed) */
        mt19937 rng(42);
        uniform_real_distribution<double> dist(0.0, 1.0);
        for (int i = 0; i < n; i++) {
            double row_sum = 0.0;
            for (int j = 0; j < n; j++) {
                A(i, j) = dist(rng);
                row_sum += A(i, j);
            }
            b(i) = row_sum;  /* x_ref = [1,1,...,1] */
        }

        /* ——— 分解 ——— */
        double t0 = now_sec();
        PartialPivLU<MatrixXd> lu(A);
        double t_factor = now_sec() - t0;

        /* ——— 求解 ——— */
        t0 = now_sec();
        x = lu.solve(b);
        double t_solve = now_sec() - t0;

        double t_total = t_factor + t_solve;
        double gf = flops / t_total / 1e6;

        cout << setw(6) << n
             << setw(12) << fixed << setprecision(4) << t_factor
             << setw(12) << fixed << setprecision(4) << t_solve
             << setw(12) << fixed << setprecision(4) << t_total
             << setw(12) << fixed << setprecision(1) << gf << endl;

        /* 验证精度 (n ≤ 500 时检查) */
        if (n <= 500) {
            double err = (x - VectorXd::Ones(n)).norm() / sqrt(n);
            if (err > 1e-10)
                cout << "  WARNING: n=" << n << " error=" << scientific << err << endl;
        }
    }

    cout << "\nEigen 特点:" << endl;
    cout << "  纯头文件 — 无需链接 BLAS/LAPACK, #include 即可用." << endl;
    cout << "  表达式模板 — 编译期优化, 消除临时矩阵." << endl;
    cout << "  PartialPivLU — 列主元 LU, 类似 LAPACK dgetrf." << endl;
    cout << "  -fopenmp  — 启用多线程加速矩阵乘法." << endl;
    return 0;
}
