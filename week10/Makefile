SHELL := /bin/bash

LATEXMK ?= latexmk
SLIDE   := slide.tex
BUILD   := build

.PHONY: all pdf clean rebuild

all: pdf

pdf:
	mkdir -p $(BUILD)
	$(LATEXMK) -xelatex -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error $(SLIDE)
	ln -sf $(BUILD)/$(SLIDE:.tex=.pdf) $(SLIDE:.tex=.pdf)

clean:
	rm -rf $(BUILD) $(SLIDE:.tex=.pdf)

rebuild: clean all
