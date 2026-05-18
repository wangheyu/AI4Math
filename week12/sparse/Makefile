## sparse/Makefile — 编译 csr_demo + csr_test, 以及讲义 PDF
##
## 目标:
##   make all         — 编译 csr_demo, csr_test, 生成 sparse_crs_beamer.pdf
##   make csr_demo    — 仅编译 demo
##   make csr_test    — 仅编译 test
##   make pdf         — 仅编译讲义 (xelatex 两遍)
##   make clean       — 删除可执行 / .o (保留实验结果与 PDF)
##   make distclean   — 清除一切, 包括 PDF 和编译产物

CC      = gcc
CFLAGS  = -O2 -Wall -Wextra -std=c99
LDFLAGS = -lm

LATEX   = xelatex
LATEXFLAGS = -interaction=nonstopmode

C_OBJS  = csr.o
TARGETS = csr_demo csr_test
PDF     = sparse_crs_beamer.pdf

.PHONY: all pdf clean distclean test demo

all: $(TARGETS) pdf

## ----- C 编译 -----

csr.o: csr.c csr.h
	$(CC) $(CFLAGS) -c -o $@ $<

csr_demo: csr_demo.c $(C_OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

csr_test: csr_test.c $(C_OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

## ----- 讲义 -----

pdf: $(PDF)

$(PDF): sparse_crs_beamer.tex
	$(LATEX) $(LATEXFLAGS) $<
	$(LATEX) $(LATEXFLAGS) $<

## ----- 快捷目标 -----

demo: csr_demo
	./csr_demo

test: csr_test
	./csr_test

## ----- 清理 -----

clean:
	rm -f $(TARGETS) *.o \
	      sparse_crs_beamer.aux sparse_crs_beamer.log sparse_crs_beamer.nav \
	      sparse_crs_beamer.out sparse_crs_beamer.snm sparse_crs_beamer.toc \
	      sparse_crs_beamer.vrb

distclean: clean
	rm -f $(PDF)
