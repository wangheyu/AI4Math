CC = gcc
CFLAGS = -O3 -march=native -Wall -Wextra
OMPFLAGS = -fopenmp
LDFLAGS = -lm

OBJS = gauss.o
TARGETS = test test_opt bench_mkl bench_eigen
EIGEN_DIR = /tmp/eigen-3.4.0
MKL_HOME = $(CONDA_PREFIX)

.PHONY: all clean distclean

all: $(TARGETS)

gauss.o: gauss.c gauss.h
	$(CC) $(CFLAGS) -c -o $@ $<

gauss_opt.o: gauss_opt.c gauss_opt.h
	$(CC) $(CFLAGS) $(OMPFLAGS) -c -o $@ $<

test: test.c $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

test_opt: test_opt.c gauss_opt.o gauss.o
	$(CC) $(CFLAGS) $(OMPFLAGS) -o $@ $^ $(LDFLAGS)

bench_mkl: bench_mkl.c gauss.o gauss_opt.o
	$(CC) $(CFLAGS) $(OMPFLAGS) -o $@ $^ -L$(MKL_HOME)/lib -Wl,-rpath,$(MKL_HOME)/lib -lmkl_rt -lm -ldl

bench_eigen: bench_eigen.cpp
	g++ -O3 -march=native -fopenmp -I$(EIGEN_DIR) -o $@ $< -lm

## clean: 只删除可执行 / 编译产物, 保留所有实验结果与日志
clean:
	rm -f $(TARGETS) bench_eigen *.o

## distclean: 同时清除实验结果 (慎用)
distclean: clean
	rm -f results_*.txt numpy_backend.txt missfont.log texput.log
