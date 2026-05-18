#!/usr/bin/env python3
"""对比 C (手写) 与 NumPy (LAPACK) 的 LU 分解 / 求解性能."""

import numpy as np
import time

def bench(size):
    n = size
    np.random.seed(42)
    A = np.random.rand(n, n)
    b = A @ np.ones(n)

    # --- np.linalg.solve (内部调用 LAPACK dgesv: LU+选主元+求解) ---
    t0 = time.perf_counter()
    x = np.linalg.solve(A, b)
    t_solve = time.perf_counter() - t0

    # --- scipy LU (仅分解) ---
    from scipy.linalg import lu
    t0 = time.perf_counter()
    P, L, U = lu(A)
    t_lu = time.perf_counter() - t0

    # --- 纯分解: scipy.linalg.lu_factor ---
    from scipy.linalg import lu_factor
    t0 = time.perf_counter()
    lu_piv = lu_factor(A)
    t_factor = time.perf_counter() - t0

    # 理论 flops: 2/3 n^3 (分解) + 2 n^2 (求解)
    flops_lu = 2.0 * n**3 / 3.0
    flops_solve = 2.0 * n**2

    return {
        'n': n,
        't_solve': t_solve,   'mflops_solve': (flops_lu + flops_solve) / t_solve / 1e6,
        't_lu': t_lu,         'mflops_lu': flops_lu / t_lu / 1e6,
        't_factor': t_factor, 'mflops_factor': flops_lu / t_factor / 1e6,
    }

def main():
    sizes = [100, 200, 500, 1000, 2000]
    print(f"{'n':>6}  {'solve(s)':>10}  {'GFLOPS':>8}  {'lu(s)':>10}  {'GFLOPS':>8}  {'factor(s)':>10}  {'GFLOPS':>8}")
    print("-" * 78)
    for n in sizes:
        r = bench(n)
        print(f"{r['n']:6d}  {r['t_solve']:10.4f}  {r['mflops_solve']/1000:8.1f}  "
              f"{r['t_lu']:10.4f}  {r['mflops_lu']/1000:8.1f}  "
              f"{r['t_factor']:10.4f}  {r['mflops_factor']/1000:8.1f}")

    # 大矩阵 (4000)
    print("\n--- 更大规模 ---")
    for n in [4000]:
        r = bench(n)
        print(f"n={n}:  solve {r['t_solve']:.3f}s ({r['mflops_solve']/1000:.1f} GFLOPS),  "
              f"factor {r['t_factor']:.3f}s ({r['mflops_factor']/1000:.1f} GFLOPS)")

if __name__ == '__main__':
    main()
