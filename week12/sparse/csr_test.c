/*
 * csr_test.c — CSR 实现的单元测试
 *
 * 测试覆盖:
 *   T1. csr_spmv        — y = A * x 在 4x4 例上
 *   T2. csr_from_coo    — 乱序 COO 构造结果与直接构造一致
 *   T3. csr_transpose   — (A^T)^T 与 A 在同一行序下一致
 *   T4. csr_forward_sub — 单位下三角解析解验证
 *   T5. csr_backward_sub — 上三角解析解验证
 *   T6. spmv + 大矩阵   — 10x10 三对角 Poisson 1D 矩阵
 */

#include "csr.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int n_pass = 0, n_fail = 0;

#define CHECK(cond, msg) do {                                  \
    if (cond) { printf("  [PASS] %s\n", msg); n_pass++; }      \
    else      { printf("  [FAIL] %s\n", msg); n_fail++; }      \
} while (0)

static int close_to(double a, double b) {
    return fabs(a - b) < 1e-10;
}

static int vec_eq(const double *a, const double *b, int n) {
    for (int i = 0; i < n; i++)
        if (!close_to(a[i], b[i])) return 0;
    return 1;
}

/* ---------- T1: SpMV 基础 ---------- */
static void test_spmv(void)
{
    printf("\n[T1] csr_spmv: 4x4 矩阵, y = A * x\n");
    const int m = 4, n = 4, nnz = 6;
    csr_matrix A;
    csr_init(&A, m, n, nnz);
    double val[]     = {10, 20, 30, 40, 50, 60};
    int    col_ind[] = { 0,  1,  3,  2,  0,  3};
    int    row_ptr[] = { 0,  1,  3,  4,  6};
    memcpy(A.val, val, nnz * sizeof(double));
    memcpy(A.col_ind, col_ind, nnz * sizeof(int));
    memcpy(A.row_ptr, row_ptr, (m + 1) * sizeof(int));

    double x[] = {1, 2, 3, 4}, y[4];
    double expected[] = {10, 160, 120, 290};

    csr_spmv(&A, x, y);
    CHECK(vec_eq(y, expected, m), "y = A x");

    /* 零向量 */
    double xz[] = {0, 0, 0, 0}, yz[4];
    csr_spmv(&A, xz, yz);
    double exp_zero[] = {0, 0, 0, 0};
    CHECK(vec_eq(yz, exp_zero, m), "y = A * 0 = 0");

    csr_free(&A);
}

/* ---------- T2: COO -> CSR 等价性 ---------- */
static void test_from_coo(void)
{
    printf("\n[T2] csr_from_coo: 乱序 COO 与直接构造一致\n");
    const int m = 4, n = 4, nnz = 6;

    /* 直接构造 */
    csr_matrix A_ref;
    csr_init(&A_ref, m, n, nnz);
    double ref_val[]     = {10, 20, 30, 40, 50, 60};
    int    ref_col[]     = { 0,  1,  3,  2,  0,  3};
    int    ref_rp[]      = { 0,  1,  3,  4,  6};
    memcpy(A_ref.val, ref_val, nnz * sizeof(double));
    memcpy(A_ref.col_ind, ref_col, nnz * sizeof(int));
    memcpy(A_ref.row_ptr, ref_rp, (m + 1) * sizeof(int));

    /* 通过 COO 构造 (乱序输入) */
    int    coo_r[] = {3, 0, 1, 2, 1, 3};
    int    coo_c[] = {3, 0, 1, 2, 3, 0};
    double coo_v[] = {60, 10, 20, 40, 30, 50};

    csr_matrix A_coo;
    csr_init(&A_coo, m, n, nnz);
    csr_from_coo(&A_coo, coo_r, coo_c, coo_v);

    /* row_ptr 必须一致 */
    int rp_ok = 1;
    for (int i = 0; i <= m; i++)
        if (A_coo.row_ptr[i] != A_ref.row_ptr[i]) rp_ok = 0;
    CHECK(rp_ok, "row_ptr 一致");

    /* SpMV 结果应一致 (注意: COO 同行内顺序可能不同, 但 SpMV 结果与顺序无关) */
    double x[] = {1, 2, 3, 4}, y_ref[4], y_coo[4];
    csr_spmv(&A_ref, x, y_ref);
    csr_spmv(&A_coo, x, y_coo);
    CHECK(vec_eq(y_ref, y_coo, m), "SpMV 结果一致");

    csr_free(&A_ref);
    csr_free(&A_coo);
}

/* ---------- T3: 转置 ---------- */
static void test_transpose(void)
{
    printf("\n[T3] csr_transpose: (A^T)^T == A\n");
    const int m = 4, n = 4, nnz = 6;
    csr_matrix A;
    csr_init(&A, m, n, nnz);
    double val[]     = {10, 20, 30, 40, 50, 60};
    int    col_ind[] = { 0,  1,  3,  2,  0,  3};
    int    row_ptr[] = { 0,  1,  3,  4,  6};
    memcpy(A.val, val, nnz * sizeof(double));
    memcpy(A.col_ind, col_ind, nnz * sizeof(int));
    memcpy(A.row_ptr, row_ptr, (m + 1) * sizeof(int));

    csr_matrix AT, ATT;
    csr_transpose(&A, &AT);
    csr_transpose(&AT, &ATT);

    /* 形状一致 */
    CHECK(ATT.m == A.m && ATT.n == A.n && ATT.nnz == A.nnz, "shape");

    /* SpMV 结果应一致 (col_ind 顺序未必, 但乘积一致) */
    double x[] = {1, 2, 3, 4}, y_orig[4], y_tt[4];
    csr_spmv(&A,   x, y_orig);
    csr_spmv(&ATT, x, y_tt);
    CHECK(vec_eq(y_orig, y_tt, m), "(A^T)^T * x == A * x");

    /* A^T * x 手算 = [210, 40, 120, 300] */
    double y_t[4];
    csr_spmv(&AT, x, y_t);
    double expected_T[] = {210, 40, 120, 300};
    CHECK(vec_eq(y_t, expected_T, m), "A^T * x");

    csr_free(&A);
    csr_free(&AT);
    csr_free(&ATT);
}

/* ---------- T4: 前代 ---------- */
static void test_forward_sub(void)
{
    printf("\n[T4] csr_forward_sub: 解 L x = b (L 单位下三角)\n");
    /*
     * L = ┌ 1   0   0   0 ┐    b = [1, 5, 14, 30]
     *     │ 2   1   0   0 │
     *     │ 3   4   1   0 │
     *     └ 4   5   6   1 ┘
     * 仅存严格下三角 (单位 L 默认对角=1, 不存)
     * x_0 = 1
     * x_1 = 5 - 2*1 = 3
     * x_2 = 14 - 3*1 - 4*3 = -1
     * x_3 = 30 - 4*1 - 5*3 - 6*(-1) = 30 - 4 - 15 + 6 = 17
     */
    const int m = 4, nnz = 6;  /* 仅严格下三角 6 个元 */
    csr_matrix L;
    csr_init(&L, m, m, nnz);
    /* 行 0: 空; 行 1: (0,2); 行 2: (0,3),(1,4); 行 3: (0,4),(1,5),(2,6) */
    double val[]     = {2, 3, 4, 4, 5, 6};
    int    col_ind[] = {0, 0, 1, 0, 1, 2};
    int    row_ptr[] = {0, 0, 1, 3, 6};
    memcpy(L.val, val, nnz * sizeof(double));
    memcpy(L.col_ind, col_ind, nnz * sizeof(int));
    memcpy(L.row_ptr, row_ptr, (m + 1) * sizeof(int));

    double b[] = {1, 5, 14, 30};
    double x[4];
    csr_forward_sub(&L, b, x);

    double expected[] = {1, 3, -1, 17};
    CHECK(vec_eq(x, expected, m), "前代解");

    csr_free(&L);
}

/* ---------- T5: 回代 ---------- */
static void test_backward_sub(void)
{
    printf("\n[T5] csr_backward_sub: 解 U x = b (U 上三角)\n");
    /*
     * U = ┌ 2   1   1   1 ┐    b = [10, 10, 9, 4]
     *     │ 0   2   1   1 │
     *     │ 0   0   3   2 │
     *     └ 0   0   0   4 ┘
     * x_3 = 4 / 4 = 1
     * x_2 = (9 - 2*1) / 3 = 7/3
     * x_1 = (10 - 1*(7/3) - 1*1) / 2 = (10 - 7/3 - 1) / 2 = (20/3)/2 = 10/3
     * x_0 = (10 - 1*(10/3) - 1*(7/3) - 1*1) / 2 = (10 - 17/3 - 1) / 2 = (10/3)/2 = 5/3
     */
    const int m = 4, nnz = 10;  /* 4+3+2+1 = 10 个上三角元 */
    csr_matrix U;
    csr_init(&U, m, m, nnz);
    double val[]     = {2, 1, 1, 1,  2, 1, 1,  3, 2,  4};
    int    col_ind[] = {0, 1, 2, 3,  1, 2, 3,  2, 3,  3};
    int    row_ptr[] = {0,           4,        7,     9, 10};
    memcpy(U.val, val, nnz * sizeof(double));
    memcpy(U.col_ind, col_ind, nnz * sizeof(int));
    memcpy(U.row_ptr, row_ptr, (m + 1) * sizeof(int));

    double b[] = {10, 10, 9, 4};
    double x[4];
    csr_backward_sub(&U, b, x);

    double expected[] = {5.0/3.0, 10.0/3.0, 7.0/3.0, 1.0};
    CHECK(vec_eq(x, expected, m), "回代解");

    csr_free(&U);
}

/* ---------- T6: 大一点的稀疏矩阵 (1D Poisson) ---------- */
static void test_poisson_1d(void)
{
    printf("\n[T6] 1D Poisson 三对角 (n=10): SpMV 性质验证\n");
    /*
     * A_ii = 2, A_{i,i+1} = A_{i+1,i} = -1, n=10
     * 用 x = (1, 1, ..., 1)^T, 则 A*x = (1, 0, 0, ..., 0, 1)^T
     */
    const int n = 10;
    int nnz = 0;
    for (int i = 0; i < n; i++) {
        nnz++;                       /* diag */
        if (i > 0)     nnz++;        /* left */
        if (i < n - 1) nnz++;        /* right */
    }
    csr_matrix A;
    csr_init(&A, n, n, nnz);

    int pos = 0;
    A.row_ptr[0] = 0;
    for (int i = 0; i < n; i++) {
        if (i > 0) {
            A.val[pos] = -1.0;  A.col_ind[pos] = i - 1;  pos++;
        }
        A.val[pos] = 2.0;   A.col_ind[pos] = i;     pos++;
        if (i < n - 1) {
            A.val[pos] = -1.0;  A.col_ind[pos] = i + 1;  pos++;
        }
        A.row_ptr[i + 1] = pos;
    }
    CHECK(pos == nnz, "nnz 计数正确");

    double x[10], y[10];
    for (int i = 0; i < n; i++) x[i] = 1.0;
    csr_spmv(&A, x, y);

    double expected[10] = {1, 0, 0, 0, 0, 0, 0, 0, 0, 1};
    CHECK(vec_eq(y, expected, n), "A x = (1,0,...,0,1)^T");

    csr_free(&A);
}

int main(void)
{
    printf("======================================================\n");
    printf(" CSR 单元测试套件\n");
    printf("======================================================\n");

    test_spmv();
    test_from_coo();
    test_transpose();
    test_forward_sub();
    test_backward_sub();
    test_poisson_1d();

    printf("\n======================================================\n");
    printf(" 通过: %d   失败: %d\n", n_pass, n_fail);
    printf("======================================================\n");

    return n_fail == 0 ? 0 : 1;
}
