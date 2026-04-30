# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a university course project from the School of Mathematical Sciences at Zhejiang University — numerical simulations of celestial mechanics systems (Sun-Earth-Moon), comparison against JPL Horizons ephemeris data, and eclipse prediction.

## Key Commands

```bash
# Top-level — orchestrates all subdirectories
make all         # compile week9 and week10 in order
make clean       # clean all subdirectories
make rebuild     # clean + all

# week9 — Report and simulations
cd week9
make pdf         # run Python scripts to generate figures/data, then compile report.tex
make figures     # run only Euler_vs_Verlet.py (generates figures/)
make data        # run only JPL.py (fetches Horizons data and generates output/)
make clean       # remove build/, figures/, output/jpl_compare_output
make rebuild     # clean + all

# week10 — Slides
cd week10
make all         # compile all slide .tex files to PDF
make pdf-make    # compile slide_make.tex only
make pdf-agent   # compile slide_agent.tex only
make pdf-jpl     # compile slide-JPL.tex only
make pdf-skills  # compile slide-skills.tex only
make clean       # remove build/ and generated PDF symlinks
```

## Python Environment

- Python is invoked via `conda run -n Teaching python`, so all scripts expect the `Teaching` conda environment.
- Required packages: `numpy`, `pandas`, `matplotlib`, `astroquery`, `astropy`. Matplotlib is always set to `matplotlib.use("Agg")` (non-interactive backend).
- All Python scripts are self-contained executables (run directly, not imported as modules).

## Project Structure

```
AI4Math/                # Top-level
├── Makefile            # orchestrates subdirectory builds
├── CLAUDE.md
├── week9/              # Main report and simulations
│   ├── report.tex          # LaTeX main file (XeLaTeX)
│   ├── chapters/           # chapter .tex files included by report.tex
│   ├── src/
│   │   ├── Euler_vs_Verlet.py  # 2D circular orbit: Euler vs Velocity-Verlet comparison
│   │   ├── ES_circle.py        # similar 2D orbit experiment with CJK rendering
│   │   ├── JPL.py              # 3D two-body propagation vs JPL Horizons, saves errors to output/
│   │   ├── two_body_realtime.py # Tkinter interactive 2D two-body simulator
│   │   ├── eclipse_predict.py  # N-body Sun-Earth-Moon eclipse predictor with bisection refinement
│   │   └── jpl_forward.py      # monkey-patches astroquery to use a domestic mirror (bypassed GFW)
│   ├── data/               # JSON initial-condition profiles for two_body_realtime.py
│   ├── figures/            # manually-placed images (jpl.png, qian.png)
│   └── output/             # generated CSVs, JSONs, and plots (gitignored)
└── week10/             # Beamer slides for four topics
    ├── slide_make.tex      # slides about the build system (Makefile)
    ├── slide_agent.tex     # slides about AI coding agents
    ├── slide-JPL.tex       # slides about the JPL comparison
    └── slide-skills.tex    # slides about Claude Code Skills (built-in and custom)
```

## Important Patterns

- `jpl_forward.py` must be imported before any JPL Horizons calls — it patches `HorizonsClass._request` to redirect to a domestic mirror (`http://8.216.49.176:18766/api/horizons.api`). All scripts that call `astroquery.jplhorizons` already include `import jpl_forward`.
- `JPL.py` and `eclipse_predict.py` cache Horizons data to avoid repeated queries (JSON caches in `week9/data/`).
- The Makefile sets `MPLCONFIGDIR` to avoid matplotlib user-directory permission issues.
- LaTeX compilation uses `latexmk -xelatex` with `-halt-on-error`.
