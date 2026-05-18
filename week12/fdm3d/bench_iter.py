#!/usr/bin/env python3
"""
bench_iter.py — scipy.sparse 路径对比 (计算软件路径基线)

读 mat.dat (CRS 二进制) → 构造 scipy.sparse.csr_matrix → 调用:
  - scipy.sparse.linalg.spsolve     (直接法, SuperLU 后端)
  - scipy.sparse.linalg.cg          (共轭梯度, 对称正定)
  - scipy.sparse.linalg.gmres       (一般迭代)

记录每种方法的迭代数 / 耗时 / 误差.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import time, sys


def load_mat(fname="mat.dat"):
    """读取 fdm3d/write_mat.c 写入的 CRS 二进制文件.
    Header: 4×int32 (nrows, ncols, nnz, N) + 2×double (h, h2inv) = 32 字节."""
    with open(fname, "rb") as f:
        head_bytes = f.read(32)
        arr = np.frombuffer(head_bytes,
                            dtype=np.dtype([("nrows","<i4"),("ncols","<i4"),
                                            ("nnz","<i4"),("N","<i4"),
                                            ("h","<f8"),("h2inv","<f8")]))
        nrows = int(arr["nrows"][0]); ncols = int(arr["ncols"][0])
        nnz   = int(arr["nnz"][0]);   N     = int(arr["N"][0])
        h     = float(arr["h"][0])

        val     = np.frombuffer(f.read(nnz * 8),       dtype="<f8").copy()
        col_ind = np.frombuffer(f.read(nnz * 4),       dtype="<i4").copy()
        row_ptr = np.frombuffer(f.read((nrows+1) * 4), dtype="<i4").copy()

    A = sp.csr_matrix((val, col_ind.astype(np.int32),
                       row_ptr.astype(np.int32)),
                      shape=(nrows, ncols))
    return A, nrows, N, h


def make_b(A, N, h):
    """构造右端 b = A * u_exact, u_exact = sin(πx)sin(πy)sin(πz)."""
    n = N - 2
    xs = np.arange(1, n + 1) * h
    XX, YY, ZZ = np.meshgrid(xs, xs, xs, indexing='ij')
    u_exact = (np.sin(np.pi * XX) * np.sin(np.pi * YY) * np.sin(np.pi * ZZ))
    u_exact_flat = u_exact.transpose(2, 1, 0).ravel()  # 与 C 端 lexicographic (i 最内, k 最外) 对齐
    b = A @ u_exact_flat
    return b, u_exact_flat


def errors(x, u_exact):
    """L2/sqrt(n) 与 L_inf 误差."""
    diff = np.abs(x - u_exact)
    return float(np.sqrt(np.mean(diff**2))), float(diff.max())


def bench():
    print("=== scipy.sparse 路径对比 (mat.dat) ===\n")
    print("读取 mat.dat ...")
    t0 = time.perf_counter()
    A, nrows, N, h = load_mat("mat.dat")
    print(f"  loaded in {time.perf_counter()-t0:.2f} s")
    print(f"  矩阵: {nrows}×{nrows}, nnz = {A.nnz}, N (grid) = {N}\n")

    print("构造 b = A*u_exact (u_exact = sin(πx)sin(πy)sin(πz)) ...")
    b, u_exact = make_b(A, N, h)
    print(f"  ||b|| = {np.linalg.norm(b):.4e}")
    print(f"  注: u_exact 是 A 的近似特征向量 — Krylov 方法可能极快收敛")
    print(f"  额外用随机右端项 b_rand 检验一般情形\n")

    # 构造随机右端项 (与 A 的特征结构无关)
    rng = np.random.default_rng(42)
    b_rand = rng.standard_normal(nrows)
    b_rand_norm = float(np.linalg.norm(b_rand))
    print(f"  ||b_rand|| = {b_rand_norm:.4e}\n")

    results = []

    # ---- spsolve (direct, SuperLU) ----
    # 在 970299×970299 矩阵上, SuperLU 的 LU 填充导致 OOM (实测被 Linux killer 终止)
    # 这正是讲义"直接法不可行"论点的实证. 跳过, 仅记录该结果.
    print("-> scipy.sparse.linalg.spsolve (直接法, SuperLU)")
    print("   SKIP: 970299^2 矩阵 LU 填充 OOM (>32 GB 内存),"
          " 直接法在大规模稀疏问题不可行 — 这是讲义论点的实证.\n")
    results.append(("spsolve", "OOM", None, None, None))

    # ---- CG with b = A*u_exact ----
    print("-> CG, b = A*u_exact (特殊右端项)")
    t0 = time.perf_counter()
    x, info = spla.cg(A, b, rtol=1e-8, atol=0.0, maxiter=5000)
    t = time.perf_counter() - t0
    l2, linf = errors(x, u_exact)
    print(f"   time = {t:.3f} s   info = {info}   "
          f"L2/sqrt(n) = {l2:.3e}\n")
    results.append(("cg(sinx)", t, "—", l2, linf))

    # ---- CG with random b ----
    print("-> CG, b = random (常规右端项, 跟踪收敛历史)")
    iters = {"n": 0, "hist": []}
    def cb_cg(xk):
        iters["n"] += 1
        if iters["n"] % 10 == 0 or iters["n"] == 1:
            r = b_rand - A @ xk
            iters["hist"].append((iters["n"], float(np.linalg.norm(r))))
    t0 = time.perf_counter()
    x_r, info_r = spla.cg(A, b_rand, rtol=1e-8, atol=0.0, maxiter=5000,
                          callback=cb_cg)
    t_r = time.perf_counter() - t0
    res_final = float(np.linalg.norm(b_rand - A @ x_r))
    conv = "converged" if info_r == 0 else f"info={info_r}"
    print(f"   iter ≈ {iters['n']:5d}  time = {t_r:.3f} s  {conv}")
    print(f"   final ||r|| = {res_final:.3e}\n")
    results.append(("cg(rand)", t_r, iters["n"], res_final / b_rand_norm, None))
    with open("conv_cg.txt", "w") as f:
        for it, rn in iters["hist"]:
            f.write(f"{it} {rn:.6e}\n")

    # ---- GMRES with random b ----
    print("-> GMRES, b = random")
    iters = {"n": 0, "hist": []}
    def cb_gm(rk):
        iters["n"] += 1
        iters["hist"].append((iters["n"], float(rk)))
    t0 = time.perf_counter()
    x_r, info_r = spla.gmres(A, b_rand, rtol=1e-8, atol=0.0, maxiter=5000,
                             restart=50, callback=cb_gm,
                             callback_type='pr_norm')
    t_r = time.perf_counter() - t0
    res_final = float(np.linalg.norm(b_rand - A @ x_r))
    conv = "converged" if info_r == 0 else f"info={info_r}"
    print(f"   iter ≈ {iters['n']:5d}  time = {t_r:.3f} s  {conv}")
    print(f"   final ||r|| = {res_final:.3e}\n")
    results.append(("gmres(rand)", t_r, iters["n"], res_final / b_rand_norm, None))
    with open("conv_gmres.txt", "w") as f:
        for it, rn in iters["hist"]:
            f.write(f"{it} {rn:.6e}\n")

    # ---- 写汇总 ----
    with open("results_scipy_summary.txt", "w") as f:
        f.write("# method  time(s)  iter  L2/sqrt(n)  L_inf\n")
        for name, t, it, l2, linf in results:
            if t == "OOM":
                f.write(f"{name}  OOM  -  -  -\n")
            elif t is None:
                f.write(f"{name}  FAILED\n")
            else:
                linf_s = f"{linf:.3e}" if linf is not None else "—"
                f.write(f"{name}  {t:.4f}  {it if it else '-'}  {l2:.3e}  {linf_s}\n")
    print("写入 results_scipy_summary.txt")

    return A, b, u_exact


if __name__ == "__main__":
    bench()
