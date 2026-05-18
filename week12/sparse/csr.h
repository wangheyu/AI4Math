/*
 * csr.h — 教学级 CRS (Compressed Row Storage) 稀疏矩阵实现
 *
 * 本头文件配套 sparse_crs_beamer.tex 讲义, 提供六个核心操作:
 *   1. csr_init / csr_free        — 创建 / 释放矩阵
 *   2. csr_spmv                   — 稀疏矩阵向量乘 y = A x  (frame 7)
 *   3. csr_from_coo               — 从 COO 三元组构造 CSR   (frame 9)
 *   4. csr_forward_sub            — 前代 L x = b (单位下三角) (frame 10)
 *   5. csr_backward_sub           — 回代 U x = b (上三角)     (frame 10)
 *   6. csr_transpose              — 矩阵转置 A^T              (frame 11)
 *
 * 设计目标: 易读 > 极致性能. 代码每行直接对应讲义伪代码.
 */

#ifndef CSR_H
#define CSR_H

#include <stddef.h>

/* CSR 稀疏矩阵结构体 (frame 8) */
typedef struct {
    int     m;        /* 行数                              */
    int     n;        /* 列数                              */
    int     nnz;      /* 非零元总数                        */
    double *val;      /* 非零元数值, 长度 nnz, 按行排列    */
    int    *col_ind;  /* 每个非零元的列号, 长度 nnz        */
    int    *row_ptr;  /* 行偏移, 长度 m+1, row_ptr[m]=nnz  */
} csr_matrix;

/* ----- 内存管理 ----- */

/* 分配三数组; 不初始化 val/col_ind 内容, row_ptr 置零 */
void csr_init(csr_matrix *A, int m, int n, int nnz);

/* 释放三数组并把指针置 NULL */
void csr_free(csr_matrix *A);

/* ----- 核心操作 ----- */

/* SpMV: y = A * x  (frame 7)
 *   y 长度 m, x 长度 n. y 由调用者分配, 函数内置零并写入. */
void csr_spmv(const csr_matrix *A,
              const double *x, double *y);

/* 从 COO 三元组构造 CSR  (frame 9)
 *   先用 csr_init(&A, m, n, nnz) 分配, 再调用本函数填充.
 *   coo_row/col/val 长度均为 nnz, 可任意顺序. */
void csr_from_coo(csr_matrix *A,
                  const int *coo_row,
                  const int *coo_col,
                  const double *coo_val);

/* 前代求解 L * x = b  (frame 10)
 *   假设 L 为单位下三角 (对角恒为 1, 仅存严格下三角部分).
 *   若 col_ind[k] >= i 的项视为对角/上三角, 忽略. */
void csr_forward_sub(const csr_matrix *L,
                     const double *b, double *x);

/* 回代求解 U * x = b  (frame 10)
 *   假设 U 为一般上三角 (对角元必须在 col_ind 中显式存在). */
void csr_backward_sub(const csr_matrix *U,
                      const double *b, double *x);

/* 矩阵转置: AT = A^T  (frame 11)
 *   AT 由本函数内部 csr_init, 调用方需在用完后 csr_free(AT). */
void csr_transpose(const csr_matrix *A, csr_matrix *AT);

/* ----- 辅助 ----- */

/* 打印矩阵 (按行列出非零元), 仅供小矩阵调试 */
void csr_print(const csr_matrix *A);

#endif /* CSR_H */
