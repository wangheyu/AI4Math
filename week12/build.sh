#!/usr/bin/env bash
#
# build.sh — 顶层编译/清理/测试包装脚本
#
# 用法:
#   ./build.sh           显示帮助
#   ./build.sh build     编译所有子项目 (= make all)
#   ./build.sh test      在每个子目录跑 run_tests.sh
#   ./build.sh pdf       仅编译三份讲义 PDF
#   ./build.sh clean     清理可执行 / 编译产物 (保留实验结果与 PDF)
#   ./build.sh distclean 清除一切, 包括实验结果与 PDF
#   ./build.sh status    列出各子目录关键产物状态
#
# 子项目:
#   gauss_elimination/   直接法 (高斯消去 / LU / AI+MKL)
#   fdm3d/               迭代法 (3D Poisson / GS-SOR / AI+PARDISO / scipy)
#   sparse/              稀疏矩阵存储 (CRS 教学实现)
#

set -u
cd "$(dirname "$0")"

SUBDIRS="gauss_elimination fdm3d sparse"

log()  { printf '\n\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

case "${1:-help}" in
    build|all)
        log "编译所有子项目"
        make all
        ;;
    test)
        log "在每个子目录跑 run_tests.sh"
        make test
        ;;
    pdf)
        log "编译讲义 PDF"
        make pdf
        ;;
    clean)
        log "清理可执行与编译产物 (保留实验结果与 PDF)"
        make clean
        ;;
    distclean)
        log "清除一切 (包括实验结果与 PDF)"
        printf "确认全部清除? [y/N] "
        read -r ans
        if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
            make distclean
        else
            echo "取消"
        fi
        ;;
    status)
        make status
        ;;
    help|-h|--help)
        sed -n '2,21p' "$0"
        ;;
    *)
        die "未知命令: $1 (使用 './build.sh help' 查看用法)"
        ;;
esac
