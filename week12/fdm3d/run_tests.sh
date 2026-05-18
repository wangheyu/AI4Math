#!/usr/bin/env bash
#
# run_tests.sh — fdm3d 数值实验一键复现脚本
#
# 用法:
#   ./run_tests.sh            # 编译 + 跑全部测试 + 生成 PNG
#   ./run_tests.sh --no-plot  # 不生成 PNG (无 matplotlib 环境时)
#   ./run_tests.sh --quick    # 仅跑小规模 (跳过 N=101 大矩阵)
#
# 结果文件命名:
#   results_jacobi.txt     — Jacobi N=64 完整输出
#   results_gs.txt         — Gauss-Seidel N=64 (omega=1.0)
#   results_sor.txt        — SOR N=64 (omega≈omega_opt)
#   results_sor_scan.txt   — SOR 参数扫描 (omega 1.0..1.99)
#   results_scipy.txt      — scipy.sparse.linalg 路径 (cg/gmres/spsolve)
#   results_pardiso.txt    — MKL PARDISO (本机环境可能不可跑, 仅占位)
#   conv_*.txt             — 各方法的收敛历史 (用于 plot_solution.py)
#   solution_slice.png     — 解的中间切片
#   convergence.png        — 三种迭代法收敛曲线
#   sor_omega.png          — SOR omega 扫描结果
#
# 退出码: 任一关键步骤失败即退出.

set -u
cd "$(dirname "$0")"

NO_PLOT=0
QUICK=0
for arg in "$@"; do
    case "$arg" in
        --no-plot) NO_PLOT=1 ;;
        --quick)   QUICK=1 ;;
        -h|--help)
            sed -n '2,20p' "$0" ; exit 0 ;;
        *) echo "未知参数: $arg" >&2; exit 2 ;;
    esac
done

log() { printf '\n\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

#------------------------------------------------------------------------------
# 1. 编译所有可执行
#------------------------------------------------------------------------------
log "Step 1/6: 编译 (make all)"
make all || die "编译失败"

#------------------------------------------------------------------------------
# 2. 生成 mat.dat (N=101 CRS 稀疏矩阵, 80 MB) — 若不存在则生成
#------------------------------------------------------------------------------
if [ ! -f mat.dat ]; then
    log "Step 2/6: 生成 mat.dat (N=101 Poisson CRS)"
    ./write_mat || die "write_mat 失败"
else
    log "Step 2/6: mat.dat 已存在 (跳过, 删除后重跑可重新生成)"
fi

#------------------------------------------------------------------------------
# 3. 小规模迭代收敛对比 (N=64)
#------------------------------------------------------------------------------
log "Step 3/6: Jacobi / GS / SOR 收敛对比 (N=64)"
./jacobi 64 20000 1e-6 2>&1 | tee results_jacobi.txt
./fdm3d  64 1.0   30000 1e-6 2>&1 | tee results_gs.txt
./fdm3d  64 1.9   30000 1e-6 2>&1 | tee results_sor.txt

#------------------------------------------------------------------------------
# 4. SOR omega 扫描 (N=64)
#------------------------------------------------------------------------------
log "Step 4/6: SOR omega 扫描 (N=64, 寻找经验最优)"
./sor_scan 64 5000 1e-6 2>&1 | tee results_sor_scan.txt

#------------------------------------------------------------------------------
# 5. 大规模 N=101 实验 (scipy + PARDISO)
#------------------------------------------------------------------------------
if [ "$QUICK" -eq 0 ]; then
    log "Step 5/6: scipy.sparse 路径 (cg/gmres on N=101 mat.dat)"
    python3 -u bench_iter.py 2>&1 | tee results_scipy.txt || \
        warn "bench_iter.py 部分失败 (可能 OOM, 见 results_scipy.txt)"

    log "Step 5b/6: MKL PARDISO (本机环境 conda+MKL+OpenMP 冲突, 可能 segfault)"
    timeout 60 ./bench_pardiso > results_pardiso.txt 2>&1 || \
        warn "bench_pardiso 异常或超时 (60s), 见 results_pardiso.txt"
else
    log "Step 5/6: SKIP (--quick 模式, 不跑 N=101 大规模)"
fi

#------------------------------------------------------------------------------
# 6. 可视化
#------------------------------------------------------------------------------
if [ "$NO_PLOT" -eq 0 ]; then
    log "Step 6/6: 生成 PNG (solution_slice / convergence / sor_omega)"
    if command -v python3 >/dev/null && python3 -c "import matplotlib" 2>/dev/null; then
        python3 -u plot_solution.py 2>&1 | grep -v "UserWarning\|Glyph\|missing font" || true
    else
        warn "matplotlib 不可用, 跳过 PNG 生成"
    fi
else
    log "Step 6/6: SKIP (--no-plot 模式)"
fi

#------------------------------------------------------------------------------
# 结果总览
#------------------------------------------------------------------------------
log "完成. 文件清单:"
ls -lh results_*.txt conv_*.txt *.png mat.dat 2>/dev/null \
    | awk 'BEGIN{printf "  %-30s %s\n","FILE","SIZE"} {printf "  %-30s %s\n",$9,$5}'

echo
echo "关键指标 (从 results 提取):"
echo "  Jacobi N=64:  $(grep -E 'Iterations:|converged' results_jacobi.txt 2>/dev/null | head -1)"
echo "  GS     N=64:  $(grep 'converged' results_gs.txt 2>/dev/null | head -1)"
echo "  SOR    N=64:  $(grep 'converged' results_sor.txt 2>/dev/null | head -1)"
echo "  最优 ω:        $(grep '<- omega_opt' results_sor_scan.txt 2>/dev/null | head -1)"
echo
echo "下一步: xelatex iter_beamer.tex && xelatex iter_beamer.tex"
