#!/usr/bin/env bash
#
# run_tests.sh — sparse 目录的 CSR 教学代码与讲义一键复现
#
# 用法:
#   ./run_tests.sh             # 编译 C 代码 + 跑 demo + 跑 test + 编译 PDF
#   ./run_tests.sh --no-pdf    # 跳过 PDF (无 xelatex 环境时)
#   ./run_tests.sh --code-only # 仅 C 代码 (跳过 PDF)
#

set -u
cd "$(dirname "$0")"

NO_PDF=0
for arg in "$@"; do
    case "$arg" in
        --no-pdf|--code-only) NO_PDF=1 ;;
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) echo "未知参数: $arg" >&2; exit 2 ;;
    esac
done

log()  { printf '\n\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

#-----------------------------------------------------------------------------
# Step 1: 编译 C 代码 (csr.o, csr_demo, csr_test)
#-----------------------------------------------------------------------------
log "Step 1/4: 编译 C 代码"
make csr_demo csr_test || die "C 代码编译失败"

#-----------------------------------------------------------------------------
# Step 2: 跑 demo (frame 13 端到端示例)
#-----------------------------------------------------------------------------
log "Step 2/4: 跑 csr_demo (frame 13 端到端示例)"
./csr_demo
demo_exit=$?
if [ $demo_exit -ne 0 ]; then
    warn "csr_demo 返回 $demo_exit (验证失败)"
fi

#-----------------------------------------------------------------------------
# Step 3: 跑单元测试 (T1-T6)
#-----------------------------------------------------------------------------
log "Step 3/4: 跑 csr_test (6 项单元测试)"
./csr_test
test_exit=$?
if [ $test_exit -ne 0 ]; then
    warn "csr_test 返回 $test_exit (存在失败用例)"
fi

#-----------------------------------------------------------------------------
# Step 4: 编译 PDF (可跳过)
#-----------------------------------------------------------------------------
if [ "$NO_PDF" -eq 0 ]; then
    log "Step 4/4: 编译 sparse_crs_beamer.pdf (xelatex 两遍)"
    if command -v xelatex >/dev/null; then
        make pdf 2>&1 | tail -5
    else
        warn "xelatex 不可用, 跳过 PDF 编译"
    fi
else
    log "Step 4/4: SKIP (--no-pdf 模式)"
fi

#-----------------------------------------------------------------------------
# 总结
#-----------------------------------------------------------------------------
echo
log "完成. 产物清单:"
ls -lh csr_demo csr_test sparse_crs_beamer.pdf 2>/dev/null \
    | awk '{printf "  %-30s %s\n",$9,$5}'

echo
total_exit=$((demo_exit + test_exit))
if [ $total_exit -eq 0 ]; then
    echo -e "\033[1;32m全部通过.\033[0m"
    exit 0
else
    echo -e "\033[1;31m存在失败 (demo=$demo_exit, test=$test_exit).\033[0m"
    exit 1
fi
