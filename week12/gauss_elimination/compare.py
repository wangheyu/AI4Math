#!/usr/bin/env python3
"""C (手写单核) vs NumPy/MKL 性能对比."""

import numpy as np
import time, os, sys, subprocess
from scipy.linalg import lu_factor, lu_solve

def timed(fn, n_trials=5, warmup_n=300):
    """运行 fn() trials 次, 去掉最快最慢各1次取平均."""
    np.random.seed(42)
    times = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    times.sort()
    return sum(times[1:-1]) / (len(times) - 2)  # trimmed mean

def main():
    sizes = [100, 200, 500, 1000, 2000]

    # C 实测数据 (gcc -O3, 单核): (solve_time, factor_time)
    c = {
        100:  (0.0002,  0.0001),
        200:  (0.0009,  0.0007),
        500:  (0.0224,  0.0180),
        1000: (0.2149,  0.1466),
        2000: (2.9667,  2.9517),
    }

    ncpu = os.cpu_count()
    print(f"环境: {ncpu} cores, NumPy 链接 MKL 2023.1, C 用 gcc -O3 -march=native (单核)")
    print()

    # ---- 对比1: 仅 LU 分解 ----
    print("=" * 75)
    print("  (a) LU 分解 (factor only)")
    print("=" * 75)
    print(f"{'n':>6}  {'C (s)':>9}  {'MKL (s)':>9}  {'speedup':>8}  "
          f"{'C Gflops':>9}  {'MKL Gflops':>10}")
    print("-" * 65)

    for n in sizes:
        _, ct = c[n]
        flops = 2.0 * n**3 / 3.0

        np.random.seed(42)
        A = np.random.rand(n, n)

        # warmup
        _ = lu_factor(np.random.rand(min(n,300), min(n,300)))

        def fn():
            return lu_factor(A)

        t_mkl = timed(fn, n_trials=5)

        speedup = ct / t_mkl
        cgf = flops / ct / 1e6
        mgf = flops / t_mkl / 1e6
        print(f"{n:6d}  {ct:9.4f}  {t_mkl:9.4f}  {speedup:7.1f}x  "
              f"{cgf:9.1f}  {mgf:10.1f}")

    # ---- 对比2: 完整求解 ----
    print()
    print("=" * 75)
    print("  (b) 完整求解 (factor + substitution)")
    print("=" * 75)
    print(f"{'n':>6}  {'C (s)':>9}  {'MKL (s)':>9}  {'speedup':>8}  "
          f"{'C Gflops':>9}  {'MKL Gflops':>10}")
    print("-" * 65)

    for n in sizes:
        ct_solve, _ = c[n]
        flops = 2.0 * n**3 / 3.0 + 2.0 * n**2

        np.random.seed(42)
        A = np.random.rand(n, n)
        b = A @ np.ones(n)

        _ = lu_factor(np.random.rand(min(n,300), min(n,300)))

        def fn():
            lu, piv = lu_factor(A)
            return lu_solve((lu, piv), b)

        t_mkl = timed(fn, n_trials=5)

        speedup = ct_solve / t_mkl
        cgf = flops / ct_solve / 1e6
        mgf = flops / t_mkl / 1e6
        print(f"{n:6d}  {ct_solve:9.4f}  {t_mkl:9.4f}  {speedup:7.1f}x  "
              f"{cgf:9.1f}  {mgf:10.1f}")

    # ---- 对比3: 隔离并行 vs 算法加速 ----
    print()
    print("=" * 75)
    print("  (c) 单线程 MKL (隔离算法加速) — n=2000")
    print("=" * 75)

    # 通过子进程确保 MKL_NUM_THREADS=1 生效
    code_st = """
import numpy as np; from scipy.linalg import lu_factor, lu_solve
import time
np.random.seed(42)
A = np.random.rand(2000, 2000)
b = A @ np.ones(2000)
# warmup
_ = lu_factor(np.random.rand(300,300))
# timed
times = []
for _ in range(5):
    t0 = time.perf_counter()
    lu, piv = lu_factor(A)
    x = lu_solve((lu, piv), b)
    times.append(time.perf_counter() - t0)
times.sort()
t = sum(times[1:-1]) / 3
print(f"{t:.5f}")
"""
    env1 = os.environ.copy()
    env1['MKL_NUM_THREADS'] = '1'
    env1['OMP_NUM_THREADS'] = '1'
    env1['OPENBLAS_NUM_THREADS'] = '1'

    # 并行
    code_mt = code_st  # same but without thread limit

    r1 = subprocess.run([sys.executable, '-c', code_st], env=env1,
                        capture_output=True, text=True)
    r2 = subprocess.run([sys.executable, '-c', code_mt],
                        capture_output=True, text=True)

    try:
        t_st = float(r1.stdout.strip())
        t_mt = float(r2.stdout.strip())
    except:
        t_st = t_mt = 0

    flops = 2.0 * 2000**3 / 3.0 + 2.0 * 2000**2

    print(f"{'':>15}  {'time':>9}  {'Gflops':>9}  {'vs C':>7}")
    print(f"  {'C (单核手写)':>13}  {c[2000][0]:9.4f}  {flops/c[2000][0]/1e6:9.1f}  {'1.0x':>7}")
    print(f"  {'MKL 单核':>13}  {t_st:9.4f}  {flops/t_st/1e6:9.1f}  {c[2000][0]/t_st:6.1f}x")
    print(f"  {'MKL {0}核'.format(ncpu):>13}  {t_mt:9.4f}  {flops/t_mt/1e6:9.1f}  {c[2000][0]/t_mt:6.1f}x")

    bt = flops / t_st / 1e6 if t_st > 0 else 0
    mt = flops / t_mt / 1e6 if t_mt > 0 else 0
    print(f"\n  算法加速 (blocking+SIMD): {c[2000][0]/t_st:.1f}x")
    print(f"  并行加速 ({ncpu}核):        {t_st/t_mt:.1f}x")
    print(f"  总加速比:                  {c[2000][0]/t_mt:.1f}x")

if __name__ == '__main__':
    main()
