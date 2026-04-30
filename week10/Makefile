SHELL := /bin/bash

LATEXMK ?= latexmk
BUILD  := build

SLIDE_MAKE   := slide_make.tex
SLIDE_AGENT  := slide_agent.tex
SLIDE_JPL    := slide-JPL.tex
SLIDE_SKILL  := slide-skills.tex
SLIDES       := $(SLIDE_MAKE) $(SLIDE_AGENT) $(SLIDE_JPL) $(SLIDE_SKILL)

PDFS := $(SLIDES:.tex=.pdf)

.PHONY: all pdf-make pdf-agent pdf-jpl pdf-skills clean rebuild

all: pdf-make pdf-agent pdf-jpl pdf-skills

pdf-make: $(SLIDE_MAKE)
	mkdir -p $(BUILD)
	$(LATEXMK) -xelatex -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error $<
	ln -sf $(BUILD)/$(SLIDE_MAKE:.tex=.pdf) $(SLIDE_MAKE:.tex=.pdf)

pdf-agent: $(SLIDE_AGENT)
	mkdir -p $(BUILD)
	$(LATEXMK) -xelatex -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error $<
	ln -sf $(BUILD)/$(SLIDE_AGENT:.tex=.pdf) $(SLIDE_AGENT:.tex=.pdf)

pdf-jpl: $(SLIDE_JPL)
	mkdir -p $(BUILD)
	$(LATEXMK) -xelatex -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error $<
	ln -sf $(BUILD)/$(SLIDE_JPL:.tex=.pdf) $(SLIDE_JPL:.tex=.pdf)

pdf-skills: $(SLIDE_SKILL)
	mkdir -p $(BUILD)
	$(LATEXMK) -xelatex -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error $<
	ln -sf $(BUILD)/$(SLIDE_SKILL:.tex=.pdf) $(SLIDE_SKILL:.tex=.pdf)

clean:
	rm -rf $(BUILD) $(PDFS)

rebuild: clean all
