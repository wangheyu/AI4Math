#!/usr/bin/env bash
#
# run_tests.sh — gauss_elimination 数值实验一键复现脚本
#
# 用法:
#   ./run_tests.sh            # 编译 + 跑所有 benchmark
#   ./run_tests.sh --no-eigen # 跳过 Eigen (头文件不在本机时)
#   ./run_tests.sh --no-numpy # 跳过 Python 基线
#
# 结果文件:
#   results_c.txt       — bench_mkl: 原始 C / 优化 C / MKL 三路, n=100..4000
#   results_numpy.txt   — bench_numpy.py: NumPy.solve / SciPy.lu_factor, n=100..4000
#   results_compare.txt — compare.py: 5 次 trim-mean 综合对照 + 单线程隔离
#   numpy_backend.txt   — numpy.show_config() 输出, 确认后端
#

set -u
cd "$(dirname "$0")"

NO_EIGEN=0
NO_NUMPY=0
for arg in "$@"; do
    case "$arg" in
        --no-eigen) NO_EIGEN=1 ;;
        --no-numpy) NO_NUMPY=1 ;;
        -h|--help)
            sed -n '2,15p' "$0" ; exit 0 ;;
        *) echo "未知参数: $arg" >&2; exit 2 ;;
    esac
done

# Python: 优先使用 conda Teaching 环境, 否则回退到系统 python3
if command -v conda &>/dev/null && conda env list 2>/dev/null | grep -q Teaching; then
    PYTHON="conda run -n Teaching python3"
else
    PYTHON="python3"
fi

log() { printf '\n\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

#------------------------------------------------------------------------------
# 1. 编译 (test / test_opt / bench_mkl / bench_eigen)
#------------------------------------------------------------------------------
log "Step 1/5: 编译"
if [ "$NO_EIGEN" -eq 1 ]; then
    log "  跳过 Eigen 目标"
    make test test_opt bench_mkl || die "编译失败"
else
    make all 2>&1 || warn "Eigen 编译失败 (头文件缺失?), 继续其它目标"
    make test test_opt bench_mkl || die "核心目标编译失败"
fi

#------------------------------------------------------------------------------
# 2. 正确性测试
#------------------------------------------------------------------------------
log "Step 2/5: 正确性测试 (test / test_opt)"
./test     | tail -5
./test_opt | tail -5

#------------------------------------------------------------------------------
# 3. 主基准: bench_mkl (原始 C / 优化 C / MKL)
#------------------------------------------------------------------------------
log "Step 3/5: bench_mkl — 三路对比 (n=100..4000)"
./bench_mkl 2>&1 | tee results_c.txt

#------------------------------------------------------------------------------
# 4. Eigen 基线 (可选)
#------------------------------------------------------------------------------
if [ "$NO_EIGEN" -eq 0 ] && [ -x ./bench_eigen ]; then
    log "Step 4a/5: bench_eigen — Eigen 3.4 PartialPivLU 基线"
    ./bench_eigen 2>&1 | tee results_eigen.txt
else
    log "Step 4a/5: SKIP Eigen"
fi

#------------------------------------------------------------------------------
# 5. Python 基线 (NumPy / SciPy / 综合对照)
#------------------------------------------------------------------------------
if [ "$NO_NUMPY" -eq 0 ]; then
    log "Step 5a/5: bench_numpy.py — NumPy.solve / SciPy.lu / SciPy.lu_factor"
    $PYTHON -u bench_numpy.py 2>&1 | tee results_numpy.txt || \
        warn "bench_numpy.py 失败 (检查 scipy 是否已装)"

    log "Step 5b/5: compare.py — 5 次 trim-mean + 单线程隔离对比"
    $PYTHON -u compare.py 2>&1 | tee results_compare.txt || \
        warn "compare.py 失败"

    log "Step 5c/5: 确认 NumPy 后端 (numpy.show_config)"
    $PYTHON -c "import numpy; numpy.show_config()" 2>&1 | tee numpy_backend.txt | head -20
else
    log "Step 5/5: SKIP Python 基线"
fi

#------------------------------------------------------------------------------
# 结果总览
#------------------------------------------------------------------------------
log "完成. 结果文件:"
ls -lh results_*.txt numpy_backend.txt 2>/dev/null \
    | awk '{printf "  %-30s %s\n",$9,$5}'

echo
echo "关键指标 (n=2000):"
echo "  bench_mkl (n=2000):  $(grep '^  2000' results_c.txt 2>/dev/null | head -1)"
echo "  NumPy   (n=2000):    $(grep '^  2000' results_numpy.txt 2>/dev/null | head -1)"
echo
echo "下一步: xelatex gauss_beamer.tex && xelatex gauss_beamer.tex"
