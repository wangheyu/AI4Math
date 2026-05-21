#!/usr/bin/env python3
"""
plot_solution.py — matplotlib 可视化

产出三张 PNG:
  1. solution_slice.png   — 3D Poisson 解在 z=0.5 平面的等高线
  2. convergence.png      — Jacobi vs SOR(omega=1) vs SOR(omega_opt) 收敛曲线
  3. sor_omega.png        — SOR omega 扫描 (Iteration vs omega)

数据来源: bench_iter.py 计算的解 + conv_jacobi.txt / sor_scan.txt
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import os


def plot_solution_slice():
    """读取 mat.dat 并用 scipy.sparse + spsolve 求解, 画中间切片."""
    import scipy.sparse as sp, scipy.sparse.linalg as spla
    print("[1] solution_slice.png ...")

    # 读 mat.dat 头 (4 int32 + 2 double = 32 字节)
    with open("mat.dat", "rb") as f:
        head = np.frombuffer(f.read(32),
            dtype=np.dtype([("nrows","<i4"),("ncols","<i4"),
                            ("nnz","<i4"),("N","<i4"),
                            ("h","<f8"),("h2inv","<f8")]))
        nrows = int(head["nrows"][0]); nnz = int(head["nnz"][0])
        N = int(head["N"][0]); h = float(head["h"][0])
        val     = np.frombuffer(f.read(nnz*8),       dtype="<f8").copy()
        col_ind = np.frombuffer(f.read(nnz*4),       dtype="<i4").copy()
        row_ptr = np.frombuffer(f.read((nrows+1)*4), dtype="<i4").copy()

    A = sp.csr_matrix((val, col_ind.astype(np.int32),
                       row_ptr.astype(np.int32)),
                      shape=(nrows, nrows))

    # 构造 b
    n = N - 2
    xs = np.arange(1, n+1) * h
    XX, YY, ZZ = np.meshgrid(xs, xs, xs, indexing='ij')
    u_exact = np.sin(np.pi * XX) * np.sin(np.pi * YY) * np.sin(np.pi * ZZ)
    u_exact_flat = u_exact.transpose(2, 1, 0).ravel()
    b = A @ u_exact_flat

    # 求解 (spsolve 在 970299 维矩阵 OOM, 改用 CG; 因 b = A*u_exact, CG 一步收敛)
    print("   CG (b 为 A 的特征向量, 一步收敛) ...")
    x, info = spla.cg(A, b, rtol=1e-10, atol=0.0, maxiter=200)

    # reshape 回 3D (k, j, i)
    sol3d = x.reshape(n, n, n).transpose(2, 1, 0)  # (i, j, k)

    # 中间 z 切片
    k_mid = n // 2
    slice_xy = sol3d[:, :, k_mid]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    im0 = axes[0].contourf(XX[:, :, k_mid], YY[:, :, k_mid], slice_xy, 20, cmap="viridis")
    axes[0].set_title(f"Numerical solution u(x,y,z={k_mid*h:.2f})")
    axes[0].set_xlabel("x"); axes[0].set_ylabel("y"); axes[0].set_aspect("equal")
    plt.colorbar(im0, ax=axes[0])

    exact_slice = u_exact[:, :, k_mid]
    err = np.abs(slice_xy - exact_slice)
    im1 = axes[1].contourf(XX[:, :, k_mid], YY[:, :, k_mid], err, 20, cmap="Reds")
    axes[1].set_title(f"|u - u_exact|, max = {err.max():.2e}")
    axes[1].set_xlabel("x"); axes[1].set_ylabel("y"); axes[1].set_aspect("equal")
    plt.colorbar(im1, ax=axes[1])

    plt.tight_layout()
    plt.savefig("solution_slice.png", dpi=120)
    plt.close()
    print(f"   solution_slice.png saved (N={N}, z-slice at k={k_mid})")


def plot_convergence():
    """读 conv_jacobi.txt / conv_gs.txt / conv_sor.txt 画收敛曲线."""
    print("[2] convergence.png ...")

    fig, ax = plt.subplots(figsize=(8, 5))
    has_any = False
    for fname, label, style in [
        ("conv_jacobi.txt", "Jacobi (ω=1, separate update)", "C0-"),
        ("conv_gs.txt",     "Gauss-Seidel (ω=1)",            "C1--"),
        ("conv_sor.txt",    "SOR (ω ≈ ω_opt)",               "C2-."),
    ]:
        if not os.path.exists(fname):
            print(f"   skip {fname} (not found)")
            continue
        data = np.loadtxt(fname)
        if data.ndim == 1:
            data = data.reshape(1, -1)
        if len(data) == 0:
            continue
        ax.semilogy(data[:, 0], data[:, 1], style, label=label, linewidth=1.5)
        has_any = True

    if not has_any:
        print("   no convergence data found, skipping")
        plt.close()
        return

    ax.set_xlabel("Iteration")
    ax.set_ylabel("||residual||_2")
    ax.set_title("Iterative methods convergence")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig("convergence.png", dpi=120)
    plt.close()
    print("   convergence.png saved")


def plot_sor_scan():
    """读 sor_scan.txt 画 omega vs iter 曲线."""
    print("[3] sor_omega.png ...")
    if not os.path.exists("sor_scan.txt"):
        print("   sor_scan.txt missing, skip")
        return
    data = np.loadtxt("sor_scan.txt")
    if data.ndim == 1 or len(data) < 2:
        print("   too few rows, skip")
        return
    # 按 omega 排序: sor_scan.c 先均匀扫描再追加精细点, 原始顺序有折返
    order = np.argsort(data[:, 0])
    omegas = data[order, 0]
    iters  = data[order, 1]

    # 找最优 omega: 经验最优 (最少迭代)
    i_min = int(np.argmin(iters))
    omega_emp = omegas[i_min]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(omegas, iters, "o-", color="C2", markersize=5)
    ax.axvline(omega_emp, color="C3", linestyle="--", alpha=0.6,
               label=f"empirical opt $\\omega$={omega_emp:.3f} (iter={int(iters[i_min])})")

    # 标解析最优 (假设 N=64 → h=1/63)
    # 实际从数据无法推 N, 仅作示意
    ax.set_xlabel(r"$\omega$ (relaxation parameter)")
    ax.set_ylabel("Iterations to converge")
    ax.set_title("SOR omega scan")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("sor_omega.png", dpi=120)
    plt.close()
    print(f"   sor_omega.png saved (实测最优 ω={omega_emp:.3f})")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--skip-solve", action="store_true",
                   help="跳过 solution_slice (耗时大)")
    args = p.parse_args()

    if not args.skip_solve:
        try:
            plot_solution_slice()
        except Exception as e:
            print(f"   plot_solution_slice failed: {e}")
    plot_convergence()
    plot_sor_scan()
    print("\nDone.")
