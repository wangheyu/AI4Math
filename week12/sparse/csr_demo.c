/*
 * csr_demo.c — 讲义 frame 13 完整端到端示例
 *
 * 构造稀疏矩阵
 *   A = ┌ 10   0   0   0 ┐
 *       │  0  20   0  30 │
 *       │  0   0  40   0 │
 *       └ 50   0   0  60 ┘
 *
 * 用向量 x = [1, 2, 3, 4]^T 测试 SpMV, 期望 y = [10, 160, 120, 290]^T.
 *
 * 演示三条路径:
 *   (a) 直接构造 CSR (手工填三数组)
 *   (b) 通过 COO 构造 CSR (csr_from_coo)
 *   (c) 计算 A^T 并演示 A^T x
 */

#include "csr.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int main(void)
{
    const int m = 4, n = 4, nnz = 6;
    const double expected[] = {10.0, 160.0, 120.0, 290.0};
    double x[] = {1, 2, 3, 4};
    double y[4];

    printf("======================================================\n");
    printf(" CSR demo  —  frame 13 端到端示例\n");
    printf("======================================================\n\n");

    /* ---- 路径 (a): 直接构造 CSR ---- */
    printf("[a] 直接构造 CSR (手填三数组):\n");
    csr_matrix A_direct;
    csr_init(&A_direct, m, n, nnz);
    {
        double val[]     = {10, 20, 30, 40, 50, 60};
        int    col_ind[] = { 0,  1,  3,  2,  0,  3};
        int    row_ptr[] = { 0,  1,  3,  4,  6};  /* 长度 m+1 = 5 */
        for (int k = 0; k < nnz; k++) {
            A_direct.val[k]     = val[k];
            A_direct.col_ind[k] = col_ind[k];
        }
        for (int i = 0; i <= m; i++) A_direct.row_ptr[i] = row_ptr[i];
    }
    csr_print(&A_direct);

    csr_spmv(&A_direct, x, y);
    printf("\n  y = A * x = [%.0f, %.0f, %.0f, %.0f]\n", y[0], y[1], y[2], y[3]);
    printf("  expected  = [%.0f, %.0f, %.0f, %.0f]\n",
           expected[0], expected[1], expected[2], expected[3]);

    int ok_a = 1;
    for (int i = 0; i < m; i++)
        if (fabs(y[i] - expected[i]) > 1e-12) ok_a = 0;
    printf("  %s\n\n", ok_a ? "OK (a)" : "FAIL (a)");

    /* ---- 路径 (b): 通过 COO 构造 CSR ---- */
    printf("[b] 通过 COO 三元组构造 (顺序乱序混合):\n");

    /* COO 故意打乱顺序, 检验排序逻辑 */
    int    coo_row[] = {3, 0, 1, 2, 1, 3};
    int    coo_col[] = {3, 0, 1, 2, 3, 0};
    double coo_val[] = {60, 10, 20, 40, 30, 50};

    csr_matrix A_coo;
    csr_init(&A_coo, m, n, nnz);
    csr_from_coo(&A_coo, coo_row, coo_col, coo_val);
    csr_print(&A_coo);

    csr_spmv(&A_coo, x, y);
    printf("\n  y = A * x = [%.0f, %.0f, %.0f, %.0f]\n", y[0], y[1], y[2], y[3]);

    int ok_b = 1;
    for (int i = 0; i < m; i++)
        if (fabs(y[i] - expected[i]) > 1e-12) ok_b = 0;
    printf("  %s\n\n", ok_b ? "OK (b)" : "FAIL (b)");

    /* ---- 路径 (c): 转置 + SpMV ---- */
    printf("[c] 转置 A^T 并演示 A^T * x:\n");
    csr_matrix AT;
    csr_transpose(&A_direct, &AT);
    csr_print(&AT);

    /* A^T 形状为 4x4 同维 */
    double yT[4];
    csr_spmv(&AT, x, yT);
    /* 期望: A^T x, 手算 A^T = [10,0,0,50; 0,20,0,0; 0,0,40,0; 0,30,0,60]
       A^T * [1,2,3,4] = [10+200, 40, 120, 60+240] = [210, 40, 120, 300] */
    double expected_T[] = {210, 40, 120, 300};
    printf("\n  A^T * x = [%.0f, %.0f, %.0f, %.0f]\n", yT[0], yT[1], yT[2], yT[3]);
    printf("  expected = [%.0f, %.0f, %.0f, %.0f]\n",
           expected_T[0], expected_T[1], expected_T[2], expected_T[3]);

    int ok_c = 1;
    for (int i = 0; i < m; i++)
        if (fabs(yT[i] - expected_T[i]) > 1e-12) ok_c = 0;
    printf("  %s\n", ok_c ? "OK (c)" : "FAIL (c)");

    csr_free(&A_direct);
    csr_free(&A_coo);
    csr_free(&AT);

    printf("\n======================================================\n");
    int all_ok = ok_a && ok_b && ok_c;
    printf(" demo %s\n", all_ok ? "全部通过" : "存在失败");
    printf("======================================================\n");
    return all_ok ? 0 : 1;
}
