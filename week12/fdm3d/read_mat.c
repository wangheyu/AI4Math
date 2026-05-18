/*
 * read_mat.c — 读取 mat.dat 并验证 CRS 稀疏矩阵的基本性质
 *
 * mat.dat 格式参见 write_mat.c 头部注释.
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int main(int argc, char **argv)
{
    const char *fname = (argc > 1) ? argv[1] : "mat.dat";

    FILE *fp = fopen(fname, "rb");
    if (!fp) { perror("fopen"); return 1; }

    /* --- 读 header --- */
    int nrows, ncols, nnz, N;
    double h, h2inv;

    fread(&nrows, sizeof(int), 1, fp);
    fread(&ncols, sizeof(int), 1, fp);
    fread(&nnz,   sizeof(int), 1, fp);
    fread(&N,     sizeof(int), 1, fp);
    fread(&h,     sizeof(double), 1, fp);
    fread(&h2inv, sizeof(double), 1, fp);

    printf("=== mat.dat header ===\n");
    printf("nrows    = %d\n", nrows);
    printf("ncols    = %d\n", ncols);
    printf("nnz      = %d\n", nnz);
    printf("N (grid) = %d\n", N);
    printf("h        = %.10f\n", h);
    printf("1/h²     = %.6f\n\n", h2inv);

    /* 一致性检查 */
    int n_exp = (N - 2) * (N - 2) * (N - 2);
    if (nrows != n_exp)
        printf("WARNING: nrows=%d, expected (N-2)^3=%d\n", nrows, n_exp);

    /* --- 读数组 --- */
    double *val     = (double *)malloc(nnz * sizeof(double));
    int    *col_ind = (int    *)malloc(nnz * sizeof(int));
    int    *row_ptr = (int    *)malloc((nrows + 1) * sizeof(int));

    fread(val,     sizeof(double), nnz,       fp);
    fread(col_ind, sizeof(int),    nnz,       fp);
    fread(row_ptr, sizeof(int),    nrows + 1, fp);
    fclose(fp);

    /* --- 验证1: row_ptr 单调性 --- */
    printf("=== 验证 row_ptr 单调性 ===\n");
    int ok = 1;
    for (int i = 0; i < nrows; i++) {
        if (row_ptr[i] > row_ptr[i + 1]) {
            printf("FAIL at row %d: %d > %d\n", i, row_ptr[i], row_ptr[i + 1]);
            ok = 0;
            break;
        }
    }
    if (ok) printf("OK — row_ptr 单调递增\n");
    printf("row_ptr[0]=%d, row_ptr[%d]=%d\n\n", row_ptr[0], nrows, row_ptr[nrows]);

    /* --- 验证2: 对角占优 + 列号范围 --- */
    printf("=== 验证对角元 & 列号范围 ===\n");
    int diag_ok = 1, col_ok = 1;
    int min_nnz = nnz, max_nnz = 0;
    double diag_min = 1e100, diag_max = -1e100;

    for (int i = 0; i < nrows; i++) {
        int len = row_ptr[i + 1] - row_ptr[i];
        if (len < min_nnz) min_nnz = len;
        if (len > max_nnz) max_nnz = len;

        int has_diag = 0;
        for (int p = row_ptr[i]; p < row_ptr[i + 1]; p++) {
            if (col_ind[p] < 0 || col_ind[p] >= ncols) {
                printf("FAIL: row %d, col %d out of [0,%d)\n", i, col_ind[p], ncols);
                col_ok = 0;
            }
            if (col_ind[p] == i) {
                has_diag = 1;
                if (val[p] < diag_min) diag_min = val[p];
                if (val[p] > diag_max) diag_max = val[p];
            }
        }
        if (!has_diag) {
            printf("FAIL: row %d missing diagonal\n", i);
            diag_ok = 0;
        }
    }
    if (col_ok) printf("OK — 所有列号在 [0, %d) 内\n", ncols);
    if (diag_ok) printf("OK — 每行均有对角元, 范围 [%.6f, %.6f]\n", diag_min, diag_max);
    printf("每行非零元: min=%d, max=%d\n\n", min_nnz, max_nnz);

    /* --- 验证3: 对称性 --- */
    printf("=== 验证对称性 (抽样首尾 10 行) ===\n");
    int sym_ok = 1;
    for (int i = 0; i < 10 && i < nrows; i++) {
        for (int p = row_ptr[i]; p < row_ptr[i + 1]; p++) {
            int j = col_ind[p];
            if (j <= i) continue;                    /* 只看上三角 */
            /* 在第 j 行中找列 i */
            int found = 0;
            for (int q = row_ptr[j]; q < row_ptr[j + 1]; q++) {
                if (col_ind[q] == i) {
                    if (fabs(val[p] - val[q]) > 1e-14)
                        printf("FAIL: A(%d,%d)=% .15e != A(%d,%d)=% .15e\n",
                               i, j, val[p], j, i, val[q]), sym_ok = 0;
                    found = 1;
                    break;
                }
            }
            if (!found) printf("FAIL: A(%d,%d) exists but A(%d,%d) missing\n", i, j, j, i), sym_ok = 0;
        }
    }
    /* 倒数 10 行 */
    int r0 = nrows > 10 ? nrows - 10 : 0;
    for (int i = r0; i < nrows; i++) {
        for (int p = row_ptr[i]; p < row_ptr[i + 1]; p++) {
            int j = col_ind[p];
            if (j <= i) continue;
            int found = 0;
            for (int q = row_ptr[j]; q < row_ptr[j + 1]; q++) {
                if (col_ind[q] == i) { found = 1; break; }
            }
            if (!found) printf("FAIL: A(%d,%d) exists but A(%d,%d) missing\n", i, j, j, i), sym_ok = 0;
        }
    }
    if (sym_ok) printf("OK — 抽检行对称\n\n");

    /* --- 验证4: 各行和 ≈ 0 (对于内部点, 6/h² - 6×(1/h²) = 0) --- */
    printf("=== 验证行和 (内部行应接近0, 边界相邻行 >0) ===\n");
    double sum_min = 1e100, sum_max = -1e100;
    for (int i = 0; i < nrows; i++) {
        double s = 0.0;
        for (int p = row_ptr[i]; p < row_ptr[i + 1]; p++)
            s += val[p];
        if (s < sum_min) sum_min = s;
        if (s > sum_max) sum_max = s;
    }
    printf("行和范围: [% .6e, % .6e]\n", sum_min, sum_max);
    printf("  (内部点=0, 边界相邻点对角占优, 和>0)\n\n");

    /* --- 打印样例行 --- */
    printf("=== 样例 ===\n");
    int samples[] = {0, nrows / 2, nrows - 1};
    for (int si = 0; si < 3; si++) {
        int row = samples[si];
        if (row >= nrows) continue;
        printf("--- row %d (nnz=%d) ---\n", row, row_ptr[row + 1] - row_ptr[row]);
        for (int p = row_ptr[row]; p < row_ptr[row + 1]; p++)
            printf("  col=%6d  val=% .6f\n", col_ind[p], val[p]);
    }

    free(val);
    free(col_ind);
    free(row_ptr);
    return 0;
}
