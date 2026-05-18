/*
 * write_mat.c — 生成 3D Poisson 方程在单位立方体上的稀疏矩阵 (CRS 格式) 并写入 mat.dat
 *
 * ============================================================================
 * mat.dat 二进制存储格式 (CRS: Compressed Row Storage)
 * ============================================================================
 *
 * 所有整数均为 int32 (little-endian)，所有浮点数为 double (IEEE 754, little-endian)
 *
 * ┌──────────┬──────────┬─────────────────────────────────────────────────┐
 * │ 偏移     │ 类型     │ 内容                                            │
 * ├──────────┼──────────┼─────────────────────────────────────────────────┤
 * │ 0        │ int32    │ nrows   — 矩阵行数 (= 未知数个数)                │
 * │ 4        │ int32    │ ncols   — 矩阵列数 (= nrows, 方阵)              │
 * │ 8        │ int32    │ nnz     — 非零元总数                            │
 * │ 12       │ int32    │ N       — 原始网格每方向点数 (含边界)            │
 * │ 16       │ double   │ h       — 网格宽度 h = 1/(N-1)                  │
 * │ 24       │ double   │ h2inv   — 1/h², 用于与纯模板矩阵互转            │
 * ├──────────┼──────────┼─────────────────────────────────────────────────┤
 * │ 32       │ double[] │ val     — 非零元数值, 长度 nnz, 每项 8 字节     │
 * │ 32+8*nnz │ int32[]  │ col_ind — 各非零元对应的列号, 长度 nnz, 每项 4B │
 * │ …        │ int32[]  │ row_ptr — 行指针, 长度 nrows+1, 每项 4 字节     │
 * └──────────┴──────────┴─────────────────────────────────────────────────┘
 *
 * row_ptr[i] 给出第 i 行在 val/col_ind 中的起始位置,
 * 第 i 行的非零元位于 val[row_ptr[i]] … val[row_ptr[i+1]-1].
 *
 * 矩阵 A 对应方程:
 *   (6u_{i,j,k} - u_{i+1,j,k} - u_{i-1,j,k} - u_{i,j+1,k} - u_{i,j-1,k}
 *                - u_{i,j,k+1} - u_{i,j,k-1}) / h² = f_{i,j,k}
 *
 * 未知数仅包含内部点 (i,j,k=1..N-2), 共 (N-2)³ 个.
 * 排序: lexicographic — 最内层为 i, 中间为 j, 最外层为 k.
 *
 * 固定边界条件 (Dirichlet u=0) 已消去, 边界相邻的内部点在该方向无对应非零元.
 * 对角元恒为 6/h², 每存在一个内部邻居即有一个 -1/h² 的非对角元.
 * 矩阵对称正定, 每行最多 7 个非零元.
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

/* --- 网格 → 未知量编号 --- */

static inline int n_interior(int N) { return N - 2; }

/* 将原始坐标 (i,j,k) 映射到未知量索引 (0-based).
   i,j,k 范围 1..N-2 (内部点) */
static inline int row_index(int i, int j, int k, int n)
{
    return (i - 1) + n * ((j - 1) + n * (k - 1));
}

int main(void)
{
    int N = 101;
    double h = 1.0 / (N - 1);
    double h2inv = 1.0 / (h * h);

    int n = n_interior(N);          /* 每方向内部点数 */
    int nrows = n * n * n;          /* = (N-2)³ */
    int ncols = nrows;
    printf("N = %d, interior = %d, unknowns = %d\n", N, n, nrows);

    /* --- 第一遍: 统计 nnz --- */
    int *row_nnz = (int *)calloc(nrows, sizeof(int));

    for (int k = 1; k <= n; k++) {
        for (int j = 1; j <= n; j++) {
            for (int i = 1; i <= n; i++) {
                int row = row_index(i, j, k, n);
                int cnt = 1; /* diagonal */
                if (i > 1) cnt++;   /* left neighbor */
                if (i < n) cnt++;   /* right neighbor */
                if (j > 1) cnt++;   /* front neighbor */
                if (j < n) cnt++;   /* back neighbor */
                if (k > 1) cnt++;   /* bottom neighbor */
                if (k < n) cnt++;   /* top neighbor */
                row_nnz[row] = cnt;
            }
        }
    }

    /* build row_ptr via prefix sum */
    int *row_ptr = (int *)malloc((nrows + 1) * sizeof(int));
    row_ptr[0] = 0;
    for (int i = 0; i < nrows; i++)
        row_ptr[i + 1] = row_ptr[i] + row_nnz[i];

    int nnz = row_ptr[nrows];
    printf("nnz = %d (%.2f MB for values)\n", nnz,
           (double)nnz * sizeof(double) / (1024 * 1024));

    /* --- 第二遍: 填充 val 和 col_ind --- */
    double *val     = (double *)malloc(nnz * sizeof(double));
    int    *col_ind = (int    *)malloc(nnz * sizeof(int));

    /* 重置 row_nnz 用作当前行写入偏移 */
    memset(row_nnz, 0, nrows * sizeof(int));

    for (int k = 1; k <= n; k++) {
        for (int j = 1; j <= n; j++) {
            for (int i = 1; i <= n; i++) {
                int row   = row_index(i, j, k, n);
                int pos   = row_ptr[row] + row_nnz[row];

                /* diagonal */
                val[pos]     = 6.0 * h2inv;
                col_ind[pos] = row;
                pos++;
                row_nnz[row]++;

                /* x-direction neighbors */
                if (i > 1) {
                    val[pos]     = -h2inv;
                    col_ind[pos] = row_index(i - 1, j, k, n);
                    pos++;
                    row_nnz[row]++;
                }
                if (i < n) {
                    val[pos]     = -h2inv;
                    col_ind[pos] = row_index(i + 1, j, k, n);
                    pos++;
                    row_nnz[row]++;
                }

                /* y-direction neighbors */
                if (j > 1) {
                    val[pos]     = -h2inv;
                    col_ind[pos] = row_index(i, j - 1, k, n);
                    pos++;
                    row_nnz[row]++;
                }
                if (j < n) {
                    val[pos]     = -h2inv;
                    col_ind[pos] = row_index(i, j + 1, k, n);
                    pos++;
                    row_nnz[row]++;
                }

                /* z-direction neighbors */
                if (k > 1) {
                    val[pos]     = -h2inv;
                    col_ind[pos] = row_index(i, j, k - 1, n);
                    pos++;
                    row_nnz[row]++;
                }
                if (k < n) {
                    val[pos]     = -h2inv;
                    col_ind[pos] = row_index(i, j, k + 1, n);
                    pos++;
                    row_nnz[row]++;
                }
            }
        }
    }

    free(row_nnz);

    /* --- 写入 mat.dat --- */
    FILE *fp = fopen("mat.dat", "wb");
    if (!fp) { perror("fopen"); return 1; }

    fwrite(&nrows, sizeof(int), 1, fp);
    fwrite(&ncols, sizeof(int), 1, fp);
    fwrite(&nnz,   sizeof(int), 1, fp);
    fwrite(&N,     sizeof(int), 1, fp);
    fwrite(&h,     sizeof(double), 1, fp);
    fwrite(&h2inv, sizeof(double), 1, fp);

    fwrite(val,     sizeof(double), nnz,       fp);
    fwrite(col_ind, sizeof(int),    nnz,       fp);
    fwrite(row_ptr, sizeof(int),    nrows + 1, fp);

    fclose(fp);

    /* 文件大小汇总 */
    long fsize = 6 * (long)sizeof(int) + 2 * (long)sizeof(double)
                 + (long)nnz * sizeof(double)
                 + (long)nnz * sizeof(int)
                 + (long)(nrows + 1) * sizeof(int);
    printf("\nmat.dat written (%.2f MB)\n", fsize / (1024.0 * 1024));
    printf("  header:    6×int32 + 2×double = %zu B\n",
           6 * sizeof(int) + 2 * sizeof(double));
    printf("  val:       %d × double = %.2f MB\n", nnz,
           nnz * sizeof(double) / (1024.0 * 1024));
    printf("  col_ind:   %d × int32  = %.2f MB\n", nnz,
           nnz * sizeof(int) / (1024.0 * 1024));
    printf("  row_ptr:   %d × int32  = %.2f MB\n", nrows + 1,
           (nrows + 1) * sizeof(int) / (1024.0 * 1024));
    printf("  nrows = %d, nnz/row ≈ %.3f\n", nrows,
           (double)nnz / nrows);

    /* 抽查第一条和最后一条记录 */
    printf("\n--- row 0 sample ---\n");
    for (int p = row_ptr[0]; p < row_ptr[1]; p++)
        printf("  col=%6d  val=% .8f\n", col_ind[p], val[p]);
    printf("--- row %d sample ---\n", nrows - 1);
    for (int p = row_ptr[nrows - 1]; p < row_ptr[nrows]; p++)
        printf("  col=%6d  val=% .8f\n", col_ind[p], val[p]);

    free(val);
    free(col_ind);
    free(row_ptr);
    return 0;
}
