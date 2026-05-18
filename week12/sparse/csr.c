/*
 * csr.c — 教学级 CRS 稀疏矩阵实现
 *
 * 每个函数对应 sparse_crs_beamer.tex 中的伪代码片段, 补全为可编译可测试的版本.
 */

#include "csr.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================ */
/* 内存管理                                                      */
/* ============================================================ */

void csr_init(csr_matrix *A, int m, int n, int nnz)
{
    A->m = m;
    A->n = n;
    A->nnz = nnz;
    A->val     = (double *)malloc((size_t)nnz * sizeof(double));
    A->col_ind = (int    *)malloc((size_t)nnz * sizeof(int));
    A->row_ptr = (int    *)calloc((size_t)m + 1, sizeof(int));
    if (!A->val || !A->col_ind || !A->row_ptr) {
        fprintf(stderr, "csr_init: 内存分配失败 (m=%d, nnz=%d)\n", m, nnz);
        exit(1);
    }
}

void csr_free(csr_matrix *A)
{
    free(A->val);
    free(A->col_ind);
    free(A->row_ptr);
    A->val = NULL;
    A->col_ind = NULL;
    A->row_ptr = NULL;
    A->m = A->n = A->nnz = 0;
}

/* ============================================================ */
/* SpMV: y = A * x   (frame 7 完整实现)                          */
/* ============================================================ */

void csr_spmv(const csr_matrix *A,
              const double *x, double *y)
{
    for (int i = 0; i < A->m; i++) {
        double sum = 0.0;
        for (int k = A->row_ptr[i]; k < A->row_ptr[i+1]; k++) {
            sum += A->val[k] * x[A->col_ind[k]];
        }
        y[i] = sum;
    }
}

/* ============================================================ */
/* COO -> CSR  (frame 9 完整实现, 两遍扫描 O(m + nnz))            */
/* ============================================================ */

void csr_from_coo(csr_matrix *A,
                  const int *coo_row,
                  const int *coo_col,
                  const double *coo_val)
{
    int m   = A->m;
    int nnz = A->nnz;

    /* Pass 1: 统计每行非零元个数 (临时存在 row_ptr[i+1]) */
    for (int i = 0; i <= m; i++) A->row_ptr[i] = 0;
    for (int k = 0; k < nnz; k++) {
        int r = coo_row[k];
        A->row_ptr[r + 1]++;
    }

    /* 前缀和: row_ptr[i] = 累积偏移 */
    for (int i = 1; i <= m; i++) {
        A->row_ptr[i] += A->row_ptr[i - 1];
    }

    /* Pass 2: scatter (counter 追踪每行已写入位置) */
    int *counter = (int *)calloc((size_t)m, sizeof(int));
    if (!counter) { fprintf(stderr, "csr_from_coo: counter 分配失败\n"); exit(1); }

    for (int k = 0; k < nnz; k++) {
        int r = coo_row[k];
        int dest = A->row_ptr[r] + counter[r];
        A->val[dest]     = coo_val[k];
        A->col_ind[dest] = coo_col[k];
        counter[r]++;
    }
    free(counter);
}

/* ============================================================ */
/* 前代: 解 L * x = b   (frame 10)                               */
/*   L 单位下三角: 对角恒为 1, 仅存严格下三角部分.               */
/*   x_i = b_i - Σ_{j<i} L_{ij} * x_j                            */
/* ============================================================ */

void csr_forward_sub(const csr_matrix *L,
                     const double *b, double *x)
{
    for (int i = 0; i < L->m; i++) {
        double sum = b[i];
        for (int k = L->row_ptr[i]; k < L->row_ptr[i+1]; k++) {
            int j = L->col_ind[k];
            if (j < i) sum -= L->val[k] * x[j];
            /* j == i 是对角 (=1), 跳过 */
            /* j > i 是上三角项 (应不存在), 跳过 */
        }
        x[i] = sum;
    }
}

/* ============================================================ */
/* 回代: 解 U * x = b   (frame 10)                               */
/*   U 一般上三角: 对角元必须在 val 中显式存在.                  */
/*   x_i = (b_i - Σ_{j>i} U_{ij} * x_j) / U_{ii}                 */
/* ============================================================ */

void csr_backward_sub(const csr_matrix *U,
                      const double *b, double *x)
{
    for (int i = U->m - 1; i >= 0; i--) {
        double sum = b[i];
        double diag = 0.0;
        for (int k = U->row_ptr[i]; k < U->row_ptr[i+1]; k++) {
            int j = U->col_ind[k];
            if (j == i)     diag = U->val[k];
            else if (j > i) sum -= U->val[k] * x[j];
            /* j < i 应不存在 */
        }
        if (diag == 0.0) {
            fprintf(stderr, "csr_backward_sub: 第 %d 行对角元为 0 或缺失\n", i);
            exit(1);
        }
        x[i] = sum / diag;
    }
}

/* ============================================================ */
/* 转置: AT = A^T   (frame 11 完整实现)                          */
/*   思路: A^T 第 j 行 = A 第 j 列, 再用 count + 前缀和 + scatter */
/* ============================================================ */

void csr_transpose(const csr_matrix *A, csr_matrix *AT)
{
    /* 维度反转 */
    csr_init(AT, A->n, A->m, A->nnz);

    /* Pass 1: 统计 AT 每行 (即 A 每列) 非零元个数 */
    for (int k = 0; k < A->nnz; k++) {
        int j = A->col_ind[k];
        AT->row_ptr[j + 1]++;
    }
    for (int i = 1; i <= AT->m; i++) {
        AT->row_ptr[i] += AT->row_ptr[i - 1];
    }

    /* Pass 2: scatter (按 A 的行顺序遍历) */
    int *counter = (int *)calloc((size_t)AT->m, sizeof(int));
    if (!counter) { fprintf(stderr, "csr_transpose: counter 分配失败\n"); exit(1); }

    for (int i = 0; i < A->m; i++) {
        for (int k = A->row_ptr[i]; k < A->row_ptr[i+1]; k++) {
            int j = A->col_ind[k];
            int dest = AT->row_ptr[j] + counter[j];
            AT->val[dest]     = A->val[k];
            AT->col_ind[dest] = i;     /* 原行号变为新列号 */
            counter[j]++;
        }
    }
    free(counter);
}

/* ============================================================ */
/* 打印 (仅小矩阵调试用)                                         */
/* ============================================================ */

void csr_print(const csr_matrix *A)
{
    printf("CSR matrix: %d x %d, nnz = %d\n", A->m, A->n, A->nnz);
    printf("  row_ptr = [");
    for (int i = 0; i <= A->m; i++)
        printf("%d%s", A->row_ptr[i], i < A->m ? ", " : "");
    printf("]\n  col_ind = [");
    for (int k = 0; k < A->nnz; k++)
        printf("%d%s", A->col_ind[k], k < A->nnz - 1 ? ", " : "");
    printf("]\n  val     = [");
    for (int k = 0; k < A->nnz; k++)
        printf("%g%s", A->val[k], k < A->nnz - 1 ? ", " : "");
    printf("]\n");

    /* 按行展开非零元 */
    for (int i = 0; i < A->m; i++) {
        printf("  row %d:", i);
        for (int k = A->row_ptr[i]; k < A->row_ptr[i+1]; k++)
            printf("  (col=%d, val=%g)", A->col_ind[k], A->val[k]);
        printf("\n");
    }
}
