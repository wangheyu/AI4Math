#ifndef GAUSS_H
#define GAUSS_H

/* 高斯消去法求解 Ax = b (列主元), 内部复制 A 到工作矩阵, 解存入 x.
   返回 0 成功, -1 奇异.
   注: 原矩阵 A 和右端 b 均不被修改. */
int gauss_solve(int n, double *A, double *b, double *x);

/* LU 分解 (Doolittle, 无选主元), A 原位存储 L 和 U:
   A 的上三角部分 = U (含对角线),
   A 的严格下三角部分 = L (单位对角线不存储).
   返回 0 成功, -1 遇到零主元. */
int lu_decomp(int n, double *A);

/* 选主元的 LU 分解: PA = LU.
   piv[0..n-1] 记录行置换, piv[i] = 第 i 行被换到的新行号.
   A 原位存储 L, U 同上.
   返回 0 成功, -1 奇异. */
int lu_decomp_pivot(int n, double *A, int *piv);

/* 已知 LU + piv, 求解 Ax = b.
   x 和 b 可为同一数组 (原地求解). */
void lu_solve(int n, const double *LU, const int *piv, const double *b, double *x);

/* 前代: 解 Ly = Pb */
void forward_subst(int n, const double *LU, const int *piv, const double *b, double *y);

/* 回代: 解 Ux = y */
void backward_subst(int n, const double *LU, const double *y, double *x);

#endif
