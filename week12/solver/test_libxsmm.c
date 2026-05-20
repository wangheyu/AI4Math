#include <libxsmm.h>
#include <libxsmm_macros.h>
#include <stdio.h>
int main() {
    printf("libxsmm version: %d.%d.%d\n",
        LIBXSMM_VERSION_MAJOR, LIBXSMM_VERSION_MINOR, LIBXSMM_VERSION_PATCH);
    return 0;
}
