SHELL := /bin/bash

PYTHON ?= conda run -n Teaching python
LATEXMK ?= latexmk
REPORT := report.tex
BUILD_DIR := build
MPLCONFIGDIR := $(CURDIR)/build/mplconfig

export MPLCONFIGDIR

FIGURE_OUTPUTS := \
	figures/circle_orbit_comparison.png \
	figures/conservation_errors_h1e-02.png \
	figures/conservation_errors_h1e-03.png

JPL_OUTPUTS := \
	output/jpl_compare_output/sun_embary_compare.csv \
	output/jpl_compare_output/sun_embary_compare_summary.json \
	output/jpl_compare_output/sun_embary_compare_errors.png

.PHONY: all pdf figures data clean rebuild

all: pdf

pdf: $(FIGURE_OUTPUTS) $(JPL_OUTPUTS)
	mkdir -p $(BUILD_DIR)/chapters
	$(LATEXMK) -xelatex -outdir=$(BUILD_DIR) -interaction=nonstopmode -halt-on-error $(REPORT)
	ln -sf $(BUILD_DIR)/$(REPORT:.tex=.pdf) $(REPORT:.tex=.pdf)

$(FIGURE_OUTPUTS) &: src/Euler_vs_Verlet.py
	mkdir -p $(MPLCONFIGDIR) figures
	$(PYTHON) $<

$(JPL_OUTPUTS) &: src/JPL.py
	mkdir -p $(MPLCONFIGDIR) output/jpl_compare_output
	$(PYTHON) $<

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(REPORT:.tex=.pdf)
	rm -f $(REPORT:.tex=.aux) $(REPORT:.tex=.out) $(REPORT:.tex=.toc) $(REPORT:.tex=.lof) $(REPORT:.tex=.lot) $(REPORT:.tex=.bbl) $(REPORT:.tex=.blg) $(REPORT:.tex=.log)
	rm -f $(FIGURE_OUTPUTS)
	rm -rf output/jpl_compare_output

rebuild: clean all

figures: $(FIGURE_OUTPUTS)

data: $(JPL_OUTPUTS)
