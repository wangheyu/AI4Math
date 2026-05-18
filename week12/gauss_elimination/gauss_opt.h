#ifndef GAUSS_OPT_H
#define GAUSS_OPT_H

/* 优化的 LU 分解:
   - 分块右看算法 (blocked right-looking), 提升 cache 命中
   - OpenMP 多线程并行 (dgemm 部分)
   - s-i-j 循环序 (rank-1 更新), 内存连续访问

   nb: 块大小, 0 表示使用默认值 (128). */

/* PA = LU, A 原位覆盖, piv 记录行置换. */
int lu_decomp_blocked(int n, double *A, int *piv, int nb);

/* 使用已有的 LU + piv 求解 Ax = b, x 可与 b 共用内存. */
void lu_solve_blocked(int n, const double *LU, const int *piv,
                      const double *b, double *x);

/* 获取 OpenMP 使用的线程数 (用于输出). 0=未编译 OpenMP. */
int lu_opt_num_threads(void);

#endif
