# Makefile for 3D Poisson solver benchmarks
# Usage: make all

CXX      := g++
NVCC     := nvcc

CXXFLAGS := -std=c++17 -O3 -march=native -Wall
NVCCFLAGS := -std=c++17 -O3 

# ---- include paths -------------------------------------------------
EIGEN_INC    := /usr/local/include/eigen3
AMGCL_INC    := /usr/local/include
OPENBLAS_INC := /usr/local/include
CUDA_INC     := /usr/local/cuda/include

# ---- library paths -------------------------------------------------
OPENBLAS_LINK := -L/usr/local/lib -lopenblas
CUDA_LIB_PATH := -L/usr/local/cuda/lib64 -L/usr/lib/x86_64-linux-gnu
CUDA_LIBS     := -lcublas -lcusparse -lcudart
CUDA_RUNTIME  := -L/usr/lib/x86_64-linux-gnu -lcudart

# ---- MKL detection -------------------------------------------------
# Search $CONDA_PREFIX first, then the Intel oneAPI default location.
MKL_LIB := $(shell bash -c \
  'if [ -f "$${CONDA_PREFIX}/lib/libmkl_rt.so" ]; then \
       echo "$${CONDA_PREFIX}/lib/libmkl_rt.so"; \
   elif [ -f "/opt/intel/oneapi/mkl/latest/lib/intel64/libmkl_rt.so" ]; then \
       echo "/opt/intel/oneapi/mkl/latest/lib/intel64/libmkl_rt.so"; \
   else \
       echo ""; \
   fi')

ifneq ($(MKL_LIB),)
  MKL_LINK := -L$(dir $(MKL_LIB)) -Wl,-rpath,$(dir $(MKL_LIB)) -lmkl_rt
endif

# ---- common objects (compiled once, reused by all targets) ---------
COMMON_OBJS := csr_matrix.o cg_solver.o eigen_ic.o

# ---- target list ---------------------------------------------------
TARGETS := bench_cpu bench_amgcl bench_gpu
ifneq ($(MKL_LIB),)
  TARGETS += bench_mkl
endif

.PHONY: all clean

all: $(TARGETS)

# ====================================================================
# Common objects
# ====================================================================

csr_matrix.o: csr_matrix.cpp csr_matrix.h
	$(CXX) $(CXXFLAGS) -I$(CUDA_INC) -c -o $@ $<

cg_solver.o: cg_solver.cpp cg_solver.h csr_matrix.h test_common.h eigen_ic.h
	$(CXX) $(CXXFLAGS) -I$(OPENBLAS_INC) -I$(EIGEN_INC) -c -o $@ $<

eigen_ic.o: eigen_ic.cpp eigen_ic.h csr_matrix.h test_common.h
	$(CXX) $(CXXFLAGS) -I$(EIGEN_INC) -c -o $@ $<

# ====================================================================
# CPU benchmark  – tests 1 & 2 (OpenBLAS CG)
# ====================================================================

bench_cpu: bench_cpu.cpp $(COMMON_OBJS) test_common.h
	$(CXX) $(CXXFLAGS) -I$(OPENBLAS_INC) -I$(EIGEN_INC) -o $@ $< \
		$(COMMON_OBJS) $(OPENBLAS_LINK) $(CUDA_RUNTIME) -lm

# ====================================================================
# MKL benchmark  – tests 3 & 4 (same cg_solver.o as bench_cpu)
# ====================================================================

ifneq ($(MKL_LIB),)
bench_mkl: bench_mkl.cpp $(COMMON_OBJS) test_common.h
	$(CXX) $(CXXFLAGS) -I$(EIGEN_INC) -o $@ $< \
		$(COMMON_OBJS) $(MKL_LINK) $(CUDA_RUNTIME) -lm
else
bench_mkl:
	$(warning MKL not found. Checked:)
	$(warning   $$CONDA_PREFIX/lib/libmkl_rt.so)
	$(warning   /opt/intel/oneapi/mkl/latest/lib/intel64/libmkl_rt.so)
	$(warning bench_mkl will be skipped.)
endif

# ====================================================================
# AMGCL benchmark – test 5 (header-only AMGCL + OpenBLAS)
# ====================================================================

bench_amgcl: bench_amgcl.cpp $(COMMON_OBJS) test_common.h
	$(CXX) $(CXXFLAGS) -I$(EIGEN_INC) -I$(AMGCL_INC) -o $@ $< \
		$(COMMON_OBJS) $(OPENBLAS_LINK) $(CUDA_RUNTIME) -lm

# ====================================================================
# GPU benchmarks  – tests 6, 7, 8 (cuBLAS + cuSPARSE + GPU CG)
#   uses gpu_cg.cu instead of cg_solver.o for GPU CG kernels
# ====================================================================

# Eigen IC compiled with nvcc for GPU targets (ABI compatibility with CUDA)
eigen_ic_gpu.o: eigen_ic.cpp eigen_ic.h csr_matrix.h test_common.h
	$(NVCC) $(NVCCFLAGS) -I$(EIGEN_INC) -c -o $@ eigen_ic.cpp

csr_matrix_gpu.o: csr_matrix.cpp csr_matrix.h
	$(NVCC) $(NVCCFLAGS) -I$(CUDA_INC) -c -o $@ csr_matrix.cpp

bench_gpu: bench_gpu.cu gpu_cg.cu csr_matrix_gpu.o eigen_ic_gpu.o test_common.h
	$(NVCC) $(NVCCFLAGS) \
		-I$(CUDA_INC) -I$(OPENBLAS_INC) -I$(EIGEN_INC) \
		-o $@ bench_gpu.cu gpu_cg.cu csr_matrix_gpu.o eigen_ic_gpu.o \
		$(CUDA_LIB_PATH) $(CUDA_LIBS) $(OPENBLAS_LINK) -lm

# ====================================================================
# Clean
# ====================================================================

clean:
	rm -f bench_cpu bench_mkl bench_amgcl bench_gpu *.o
