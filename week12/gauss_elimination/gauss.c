#include "gauss.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define TOL 1e-15

/* ---------- 通用工具 ---------- */

static inline void swap_rows(int n, double *A, int r1, int r2)
{
    if (r1 == r2) return;
    for (int j = 0; j < n; j++) {
        double tmp = A[r1 * n + j];
        A[r1 * n + j] = A[r2 * n + j];
        A[r2 * n + j] = tmp;
    }
}

static inline void swap_double(double *a, double *b)
{
    double t = *a; *a = *b; *b = t;
}

/* ---------- 高斯消去法 (列主元, 求解 Ax=b) ---------- */
/*
   算法: kij 型右看 (right-looking)
   对 k = 0..n-2:
     选列主元 → 必要时交换行
     对 i = k+1..n-1:
       factor = A[i][k] / A[k][k]
       对 j = k+1..n-1: A[i][j] -= factor * A[k][j]
       b[i] -= factor * b[k]

   复杂度: 消去 ~2n³/3 flops, 回代 ~n² flops.
   内层 j 循环为连续访问 (row-major), cache 友好.
*/
int gauss_solve(int n, double * restrict A, double * restrict b, double * restrict x)
{
    /* 复制 A 到工作矩阵, b 复制到 x */
    double * restrict U = (double *)malloc((size_t)n * n * sizeof(double));
    if (!U) return -2;
    memcpy(U, A, (size_t)n * n * sizeof(double));
    memcpy(x, b, n * sizeof(double));

    for (int k = 0; k < n - 1; k++) {
        /* --- 列主元 --- */
        int pivot = k;
        double maxv = fabs(U[k * n + k]);
        for (int i = k + 1; i < n; i++) {
            double v = fabs(U[i * n + k]);
            if (v > maxv) { maxv = v; pivot = i; }
        }
        if (maxv < TOL) { free(U); return -1; }

        if (pivot != k) {
            swap_rows(n, U, k, pivot);
            swap_double(&x[k], &x[pivot]);
        }

        /* --- 消去 --- */
        double * restrict Uk = U + k * n;        /* 第 k 行基地址 */
        double dk = Uk[k];
        for (int i = k + 1; i < n; i++) {
            double factor = U[i * n + k] / dk;
            U[i * n + k] = factor;                /* 存储 L */
            double * restrict Ui = U + i * n;
            for (int j = k + 1; j < n; j++)
                Ui[j] -= factor * Uk[j];
            x[i] -= factor * x[k];
        }
    }

    if (fabs(U[(n - 1) * n + (n - 1)]) < TOL) { free(U); return -1; }

    /* --- 回代 --- */
    for (int i = n - 1; i >= 0; i--) {
        double s = x[i];
        double * restrict Ui = U + i * n;
        for (int j = i + 1; j < n; j++)
            s -= Ui[j] * x[j];
        x[i] = s / Ui[i];
    }

    free(U);
    return 0;
}

/* ---------- LU 分解 (Doolittle, 无选主元, 右看算法) ---------- */
/*
   与高斯消去等价 (不含 RHS 操作). 矩阵 A 原位覆盖:
     U 存放在上三角 (含对角线)
     L 存放在严格下三角 (单位对角线, 隐含)
   复杂度: ~2n³/3 flops.
*/
int lu_decomp(int n, double * restrict A)
{
    for (int k = 0; k < n; k++) {
        double pivot = A[k * n + k];
        if (fabs(pivot) < TOL) return -1;

        /* 对 k 以下各行计算乘子, 更新子矩阵 */
        double * restrict Uk = A + k * n;
        for (int i = k + 1; i < n; i++) {
            double factor = A[i * n + k] / pivot;
            A[i * n + k] = factor;                /* L[i][k] */
            double * restrict Ui = A + i * n;
            for (int j = k + 1; j < n; j++)
                Ui[j] -= factor * Uk[j];
        }
    }
    return 0;
}

/* ---------- 列主元 LU 分解 (PA = LU) ---------- */
/*
   piv[] 含义: 行 i 在置换后位于 piv[i].
   形式: 设 P 为置换矩阵, 则 P*A = L*U.
   求解 Ax=b 时: 先解 Ly=Pb, 再解 Ux=y.
*/
int lu_decomp_pivot(int n, double * restrict A, int * restrict piv)
{
    for (int i = 0; i < n; i++) piv[i] = i;

    for (int k = 0; k < n; k++) {
        /* --- 列主元 --- */
        int pivot = k;
        double maxv = fabs(A[k * n + k]);
        for (int i = k + 1; i < n; i++) {
            double v = fabs(A[i * n + k]);
            if (v > maxv) { maxv = v; pivot = i; }
        }
        if (maxv < TOL) return -1;

        if (pivot != k) {
            int tmpi = piv[k]; piv[k] = piv[pivot]; piv[pivot] = tmpi;
            swap_rows(n, A, k, pivot);
        }

        /* --- 消去 (同 lu_decomp 逻辑) --- */
        double * restrict Uk = A + k * n;
        double dk = Uk[k];
        for (int i = k + 1; i < n; i++) {
            double factor = A[i * n + k] / dk;
            A[i * n + k] = factor;
            double * restrict Ui = A + i * n;
            for (int j = k + 1; j < n; j++)
                Ui[j] -= factor * Uk[j];
        }
    }
    return 0;
}

/* ---------- 前代: Ly = Pb ---------- */
void forward_subst(int n, const double * restrict LU,
                   const int * restrict piv,
                   const double * restrict b, double * restrict y)
{
    /* 先对 b 施加置换 P, 存于 y */
    for (int i = 0; i < n; i++)
        y[i] = b[piv[i]];

    /* 解 Ly = (Pb) */
    for (int i = 0; i < n; i++) {
        double s = y[i];
        const double * restrict LUi = LU + i * n;
        for (int j = 0; j < i; j++)
            s -= LUi[j] * y[j];
        y[i] = s;  /* L 单位对角线, 不除 */
    }
}

/* ---------- 回代: Ux = y ---------- */
void backward_subst(int n, const double * restrict LU,
                    const double * restrict y, double * restrict x)
{
    for (int i = n - 1; i >= 0; i--) {
        double s = y[i];
        const double * restrict LUi = LU + i * n;
        for (int j = i + 1; j < n; j++)
            s -= LUi[j] * x[j];
        x[i] = s / LUi[i];
    }
}

/* ---------- 使用 LU + piv 求解 Ax = b ---------- */
void lu_solve(int n, const double * restrict LU,
              const int * restrict piv,
              const double * restrict b, double * restrict x)
{
    double *y = (double *)malloc(n * sizeof(double));
    forward_subst(n, LU, piv, b, y);
    backward_subst(n, LU, y, x);
    free(y);
}
