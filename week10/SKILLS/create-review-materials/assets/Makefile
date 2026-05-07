SHELL := /bin/bash
LATEXMK ?= latexmk
BUILD  := build
DOC   := review-doc
SRC   := review-src

TEXS := $(SRC)/outline.tex \
        $(SRC)/exercises.tex \
        $(SRC)/exercises-answers.tex \
        $(SRC)/exam.tex \
        $(SRC)/exam-answers.tex
PDFS := $(TEXS:$(SRC)/%.tex=$(DOC)/%.pdf)

.PHONY: all outline exercises exercises-answers exam exam-answers clean rebuild

all: outline exercises exercises-answers exam exam-answers

outline: $(DOC)/outline.pdf
exercises: $(DOC)/exercises.pdf
exercises-answers: $(DOC)/exercises-answers.pdf
exam: $(DOC)/exam.pdf
exam-answers: $(DOC)/exam-answers.pdf

$(DOC)/%.pdf: $(SRC)/%.tex
	mkdir -p $(BUILD) $(DOC)
	$(LATEXMK) -xelatex -outdir=../$(BUILD) -interaction=nonstopmode -halt-on-error -cd $<
	mv $(BUILD)/$*.pdf $(DOC)/$*.pdf

clean:
	rm -rf $(BUILD) $(DOC)

rebuild: clean all
