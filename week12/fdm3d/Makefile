CC = gcc
CFLAGS = -O3 -march=native -Wall -Wextra
LDFLAGS = -lm
MKL_HOME = $(CONDA_PREFIX)

TARGETS = fdm3d write_mat read_mat jacobi sor_scan bench_pardiso

.PHONY: all clean distclean

all: $(TARGETS)

fdm3d: main.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

write_mat: write_mat.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

read_mat: read_mat.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

jacobi: jacobi.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

sor_scan: sor_scan.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

bench_pardiso: bench_pardiso.c
	$(CC) $(CFLAGS) -fopenmp -o $@ $< \
	    -L$(MKL_HOME)/lib -Wl,-rpath,$(MKL_HOME)/lib \
	    -lmkl_rt -lm -ldl

## clean: 只删除可执行 / 编译产物, 保留所有实验数据与图
clean:
	rm -f $(TARGETS) *.o

## distclean: 同时清除矩阵数据 / 实验日志 / 收敛历史 / PNG (慎用)
distclean: clean
	rm -f mat.dat conv_*.txt sor_scan.txt results_*.txt \
	      solution_slice.png convergence.png sor_omega.png
