TEX      = xelatex
TEXFLAGS = -interaction=nonstopmode -output-directory=build
BIB      = biber
TARGET   = report.pdf
SRC      = report.tex
BIBFILE  = Qian.bib

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SRC) $(BIBFILE) | build
	$(TEX) $(TEXFLAGS) $<
	ln -sf ../$(BIBFILE) build/
	cd build && $(BIB) report
	$(TEX) $(TEXFLAGS) $<
	$(TEX) $(TEXFLAGS) $< && cp build/$@ $@

build:
	mkdir -p $@

clean:
	rm -rf build $(TARGET)
