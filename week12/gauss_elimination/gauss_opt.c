/*
 * gauss_opt.c — 分块 LU 分解 + OpenMP 并行
 *
 * 算法: 右看分块 LU (blocked right-looking), 与 LAPACK dgetrf 思路一致.
 *
 *   for k = 0 : nb : n-1
 *     1. Panel LU  — 对当前列块 A[k:n, k:k+kb] 做无分块 LU (含选主元, 交换整行)
 *     2. dtrsm     — 用 L_top 更新顶部块行: U_right = L_top^{-1} * A_top_right
 *     3. dgemm     — 更新剩余子矩阵: A_bot_right -= A_bot_left * U_right   [OMP 并行]
 *
 * 循环序优化 (dgemm):
 *   采用 s-i-j 序 (rank-1 更新). 对每个 k (s):
 *     for i: C[i][:] -= A[i][s] * B[s][:]
 *   内层 B[s][:] 和 C[i][:] 均 stride-1 连续访问, cache 友好.
 *
 * 编译: gcc -O3 -march=native -fopenmp
 */

#include "gauss_opt.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#define DEFAULT_NB 128

/* ---------- Panel LU (无分块, 含列主元, 只更新 panel 内部) ---------- */
/*
   对 A[k:n, k:k+kb] 做标准 LU.
   行交换作用于全部列 [0..n), 但 rank-1 更新仅限于 panel 内部 [k..k+kb).
   右侧剩余部分由外层 dtrsm/dgemm 负责.
*/
static void panel_lu(int n, double * restrict A, int k, int kb, int * restrict piv)
{
    int kb_end = k + kb;
    for (int j = k; j < kb_end; j++) {
        /* 列主元 */
        int pivot = j;
        double maxv = fabs(A[j * n + j]);
        for (int i = j + 1; i < n; i++) {
            double v = fabs(A[i * n + j]);
            if (v > maxv) { maxv = v; pivot = i; }
        }
        /* 交换整行 + 维护置换向量 */
        if (pivot != j) {
            for (int c = 0; c < n; c++) {
                double tmp = A[j * n + c];
                A[j * n + c] = A[pivot * n + c];
                A[pivot * n + c] = tmp;
            }
            int tmp = piv[j];
            piv[j] = piv[pivot];
            piv[pivot] = tmp;
        }

        double dj = A[j * n + j];

        /* 乘子 (L 因子) */
        for (int i = j + 1; i < n; i++)
            A[i * n + j] /= dj;

        /* 仅在 panel 内更新 */
        for (int i = j + 1; i < n; i++) {
            double factor = A[i * n + j];
            for (int c = j + 1; c < kb_end; c++)
                A[i * n + c] -= factor * A[j * n + c];
        }
    }
}

/* ---------- dtrsm: 解 L_top * X = B, L_top 为单位下三角 ---------- */
/*
   X = L_top^{-1} * B, 其中:
   L_top 为 kb×kb, 存储在 A[k:k+kb, k:k+kb] 的严格下三角
   B 为 A[k:k+kb, k+kb:n], 结果覆盖 B
*/
static void dtrsm_lower(int n, double * restrict A, int k, int kb)
{
    int nrhs = n - k - kb;
    if (nrhs <= 0) return;

    for (int j = k + kb; j < n; j++) {
        for (int i = k; i < k + kb; i++) {
            double sum = A[i * n + j];
            double * restrict Ai = A + i * n;
            for (int s = k; s < i; s++)
                sum -= Ai[s] * A[s * n + j];
            A[i * n + j] = sum;   /* L 单位对角线, 不除 */
        }
    }
}

/* ---------- dgemm: C -= A_panel * B_top (s-i-j 序, OMP 并行) ---------- */
/*
   A_panel: (m × inner),  A[k+kb:n, k:k+kb]   (L 乘子)
   B_top:   (inner × p), A[k:k+kb, k+kb:n]    (U 顶部块行)
   C:       (m × p),     A[k+kb:n, k+kb:n]    (右下子矩阵)

   s-i-j 序: 外层 s (inner 方向), 对每个 s 做 rank-1 更新 C -= a_*s ⊗ b_s*
   线程在 s 循环内并行处理不同行 i, nowait 避免不必要的 barrier.
   每个线程固定处理相同的行范围, 不同 s 之间无数据竞争 (各行独立).
*/
/* 阈值: dgemm 工作量 (flops) 超过此值才启用 OpenMP 并行 */
#define OMP_THRESHOLD 50000000L   /* 50 Mflops ≈ 400M 次内存访问 */

static void dgemm_sij(int n, double * restrict A, int k, int kb)
{
    int m = n - k - kb;
    int p = n - k - kb;
    int inner = kb;
    if (m <= 0 || p <= 0) return;

    double * restrict C       = A + (k + kb) * n + (k + kb);
    double * restrict A_panel = A + (k + kb) * n + k;
    double * restrict B_top   = A + k * n + (k + kb);

    long workload = (long)m * p * inner * 2;  /* flops */

    if (workload > OMP_THRESHOLD) {
        /* 并行路径: s-i-j 序, 线程在 s 循环内分 i 方向 */
        #pragma omp parallel
        {
            for (int s = 0; s < inner; s++) {
                const double * restrict Bs = B_top + s * n;
                #pragma omp for schedule(static) nowait
                for (int i = 0; i < m; i++) {
                    double aik = A_panel[i * n + s];
                    if (aik != 0.0) {
                        double * restrict Ci = C + i * n;
                        #pragma omp simd
                        for (int j = 0; j < p; j++)
                            Ci[j] -= aik * Bs[j];
                    }
                }
            }
        }
    } else {
        /* 串行路径: 同上算法, 免去 OpenMP 开销 */
        for (int s = 0; s < inner; s++) {
            const double * restrict Bs = B_top + s * n;
            for (int i = 0; i < m; i++) {
                double aik = A_panel[i * n + s];
                if (aik != 0.0) {
                    double * restrict Ci = C + i * n;
                    #pragma omp simd
                    for (int j = 0; j < p; j++)
                        Ci[j] -= aik * Bs[j];
                }
            }
        }
    }
}

/* ---------- 公开接口 ---------- */

/* 对外接口: 需要原始 unblocked LU 作为小矩阵回退 */
int lu_decomp_pivot(int n, double *A, int *piv);  /* from gauss.c */

int lu_decomp_blocked(int n, double * restrict A, int * restrict piv, int nb)
{
    if (nb <= 0) nb = DEFAULT_NB;

    /* 小矩阵直接走无分块路径, 避免分块和 OpenMP 开销 */
    if (n < 500)
        return lu_decomp_pivot(n, A, piv);

    for (int i = 0; i < n; i++) piv[i] = i;

    for (int k = 0; k < n; k += nb) {
        int kb = (k + nb < n) ? nb : (n - k);

        panel_lu(n, A, k, kb, piv);       /* 1. 面板分解 */
        if (k + kb < n) {
            dtrsm_lower(n, A, k, kb);     /* 2. 顶部块行 */
            dgemm_sij(n, A, k, kb);       /* 3. 子矩阵更新 (主要计算量, OMP 并行) */
        }
    }
    return 0;
}

/* ---------- 基于 LU 的求解 (串行前代/回代) ---------- */

static void forward_subst(int n, const double * restrict LU,
                          const int * restrict piv,
                          const double * restrict b, double * restrict y)
{
    for (int i = 0; i < n; i++) y[i] = b[piv[i]];

    for (int i = 0; i < n; i++) {
        double s = y[i];
        const double * restrict LUi = LU + i * n;
        for (int j = 0; j < i; j++)
            s -= LUi[j] * y[j];
        y[i] = s;
    }
}

static void backward_subst(int n, const double * restrict LU,
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

void lu_solve_blocked(int n, const double * restrict LU,
                      const int * restrict piv,
                      const double * restrict b, double * restrict x)
{
    double *y = (double *)malloc(n * sizeof(double));
    forward_subst(n, LU, piv, b, y);
    backward_subst(n, LU, y, x);
    free(y);
}

int lu_opt_num_threads(void)
{
#ifdef _OPENMP
    return omp_get_max_threads();
#else
    return 0;
#endif
}
