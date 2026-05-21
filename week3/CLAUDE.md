# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Week 3 of a university course — C language, BMP bitmap file format, compilation (static/shared libraries), and Doxygen documentation. The Beamer slide `slide.tex` is the course lecture; the C code demonstrates the concepts.

## Build Commands

```bash
# Compile the bitmap test (yellow 320x240 BMP)
gcc -I include src/bitmap.c src/bitmap_test_y.c -o test

# Compile the gradient test (256x256 BMP)
gcc -I include src/bitmap.c src/bitmap_test_change.c -o test

# Compile the multi-generator demo (gradient/stripes/checkerboard/shapes)
gcc -I include src/bmp.c -o main

# Compile the hello example
gcc -I include src/hello.c src/add.c src/main_hello.c -o hello

# Static library from bitmap
gcc -I include -c src/bitmap.c -o bitmap.o
ar rcs libbitmap.a bitmap.o
gcc -I include src/bitmap_test_y.c ./libbitmap.a -o test

# Shared library from bitmap
gcc -I include -fPIC -c src/bitmap.c -o bitmap_pic.o
gcc -shared bitmap_pic.o -o libbitmap.so
gcc -I include src/bitmap_test_y.c -L. -lbitmap -Wl,-rpath=. -o test

# Doxygen
doxygen Doxyfile

# Compile the Beamer slide
xelatex slide.tex
```

## Code Architecture

There are two independent code groups:

**hello group** — illustrates multi-file C structure:
- `include/hello.h` — macro `MSG` and `add()` declaration
- `include/add.h` — duplicate of hello.h
- `src/hello.c` / `src/add.c` — both define `int add(int a, int b) { return a + b; }` (duplicates)
- `src/main_hello.c` — prints MSG, calls add(2,3)

**bitmap group** — 24-bit uncompressed BMP generation:
- `include/bitmap.h` — `BITMAPFILEHEADER`, `BITMAPINFOHEADER` packed structs, `build_bmp()` declaration
- `src/bitmap.c` — `build_bmp()` implementation (writes BMP with 4-byte row padding, bottom-up row order)
- `src/bmp.c` — alternative BMP implementation with generators (gradient, stripes, checkerboard, shapes), uses negative `biHeight` for top-down order
- `src/bitmap_test_y.c` — test: generates yellow BMP via `build_bmp()`
- `src/bitmap_test_change.c` — test: generates gradient BMP via `build_bmp()`
- `figures/` — generated BMP output files
- `commented/` — Doxygen-annotated copy of bitmap code
- `temp/` — Doxygen build output

Pixel format: 3 bytes per pixel, BGR order (not RGB). `(0,255,255)` = yellow (B=0, G=255, R=255).

## Key Notes

- Both `build_bmp()` in bitmap.c and `createBMP24()` in bmp.c write 24-bit uncompressed BMP. They handle row padding differently: bitmap.c iterates bottom-up for positive `biHeight`; bmp.c uses negative `biHeight` for top-down storage.
- `build_bmp()` returns negative error codes (-1 param, -2 file open, -3 file write).
- The `__attribute__((packed))` on BMP structs is GCC-specific and critical for correct binary layout.
- `hello.h` and `add.h` are identical; `hello.c` and `add.c` are identical — likely remnants of separate compilation demos.
- The Beamer slide `slide.tex` covers all five code topics and serves as the main deliverable.
