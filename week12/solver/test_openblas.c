#include <cblas.h>
#include <stdio.h>
int main() {
    double A[4] = {1,2,3,4}, B[4] = {5,6,7,8}, C[4] = {0};
    cblas_dgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, 2,2,2, 1.0, A,2, B,2, 0.0, C,2);
    printf("OpenBLAS dgemm C[0]=%f (expect 19)\n", C[0]);
    return (C[0] > 18 && C[0] < 20) ? 0 : 1;
}
