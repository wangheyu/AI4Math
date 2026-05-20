#include <suitesparse/umfpack.h>
#include <stdio.h>
int main() {
    double info[UMFPACK_INFO];
    double control[UMFPACK_CONTROL];
    umfpack_di_defaults(control);
    printf("SuiteSparse UMFPACK version: %d.%d.%d\n", UMFPACK_MAIN_VERSION, UMFPACK_SUB_VERSION, UMFPACK_SUBSUB_VERSION);
    return 0;
}
