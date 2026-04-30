---
name: beamer-overflow
description: >
  Checks LaTeX beamer slides for page overflow (overfull boxes, frame text
  shrink), diagnoses which frames are problematic, and applies targeted fixes.
  Use whenever the user mentions "屏幕溢出", "页面溢出", "溢出检查", "beamer
  overflow", or asks to check/fix beamer slides for layout problems. Also use
  after creating or editing beamer .tex files, or when the user asks "检查一下
  beamer 有没有溢出" or similar.
allowed-tools: [Bash, Read, Edit, Write, Grep, Glob]
---

# Beamer Overflow Checker

Check LaTeX beamer slides for overflow problems and fix them automatically.

## Workflow

### Step 1: Identify the target file

If the user specifies a `.tex` file, use it. Otherwise, look for beamer `.tex`
files in the current project — search for `\documentclass.*beamer` to find them.
If there are multiple, ask which one(s) to check.

### Step 2: Find the build command

Check the project's Makefile or CLAUDE.md for the compilation command. Prefer
`latexmk -xelatex` as it handles multi-pass correctly. If no command is
documented, use:

```bash
latexmk -xelatex -outdir=build -interaction=nonstopmode -halt-on-error <file>.tex
```

Run this from the directory containing the `.tex` file.

### Step 3: Parse the log for overflow warnings

Read `<build-dir>/<filename>.log` and extract these patterns:

| Pattern | Meaning |
|---|---|
| `Class beamer Warning: Frame text is shrunk by a factor of (\d+\.?\d*) percent` | Frame too tall, beamer auto-shrunk content |
| `Overfull \\vbox \((\d+\.?\d*)pt too high\) detected at line (\d+)` | Frame exceeds page height by N pt |
| `Overfull \\hbox \((\d+\.?\d*)pt too wide\) .* at lines (\d+)--(\d+)` | Content wider than line width |

### Step 4: Map line numbers to frames

For each warning, find which frame contains the reported line number. Search the
`.tex` file for `\begin{frame}` / `\end{frame}` boundaries. Report findings to
the user as a table:

```
| Frame | Line Range | Issue | Severity |
|---|---|---|---|
| "三级加载机制" | 136-161 | vbox 14.7pt overfull | Minor |
| "创建过程" | 363-393 | Shrunk 39% | Severe |
```

Severity thresholds:
- **Severe**: shrink > 20%, vbox > 30pt, or any hbox > 10pt
- **Moderate**: shrink 10-20%, vbox 10-30pt
- **Minor**: shrink < 10%, vbox < 10pt

### Step 5: Apply fixes (from most severe to least)

Fix frames in order of severity. After each fix, recompile to check the effect.

**Technique A: Reduce vertical spacing (for vbox/shrink)**
- Shrink `\vspace{0.Xcm}` → `\vspace{0.Ycm}` (halve it)
- Reduce `\setlength\itemsep{Xpt}` → smaller value
- Remove `\addlinespace` from tabular environments
- Remove unnecessary `\\` line breaks

**Technique B: Reduce font sizes (for vbox/shrink)**
- `\large` → `\normalsize` or `\small`
- `\small` → `\footnotesize` in lstlisting
- `\footnotesize` in wide tables

**Technique C: Compact text content (for vbox/shrink)**
- Merge multi-line bullet items into single lines
- Shorten lstlisting code samples (keep only representative lines)
- Merge `\begin{alertblock}...\end{alertblock}` into inline `\textbf{}` text
- Combine adjacent `\begin{block}...\end{block}` with less spacing

**Technique D: Fix horizontal overflow (for hbox)**
- Replace `\;\longrightarrow\;` or `$\;\longrightarrow\;$` with `$\to$` or `$\rightarrow$`
- Shorten text in `\texttt{}` and inline code
- Remove or abbreviate long URL / path strings

**Technique E: Last resort (only if A-D insufficient)**
- Add `shrink` option to frame: `\begin{frame}[shrink]` or `\begin{frame}[shrink=15]`
- Split the frame into two frames if content is essential

### Step 6: Iterate until clean

Target: zero severe warnings, and moderate warnings reduced to minor.
The goal is NOT zero warnings — beamer theme templates often produce minor
hbox overflows that are invisible in the PDF output.

Acceptable residual state:
- Shrink < 15% on a few frames
- vbox < 10pt
- hbox < 6pt from beamer theme elements (not from user content)

### Step 7: Report results

Summarize before/after in a compact table:

```
| Frame | Before | After |
|---|---|---|
| "创建过程" | Shrunk 39% | Clean |
| "工作机制" | vbox 63pt | Shrunk 10% |
| "对比" | vbox 47pt | Clean |
```

## Anti-patterns

- Do NOT blindly delete content — always prefer compressing spacing first
- Do NOT change `[fragile]` frames to non-fragile without checking for verbatim content
- Do NOT remove `shrink` from frames that had severe overflow without fixing the root cause first
- Do NOT modify `.tex` files without reading them first via the Read tool
- Do NOT apply the same fix to every frame — diagnose each one individually

## Example interaction

User: "检查 week10/slide-skills.tex 有没有页面溢出"

1. Read the file or Makefile to find the compile command
2. Run `make pdf-skills` (or equivalent)
3. Parse `build/slide-skills.log` for warnings
4. Report: "发现 5 帧缩水(最高 39%)、4 帧 vbox 溢出(最高 47pt)"
5. Start fixing from the most severe frame
6. After each fix batch, recompile and report progress
7. Final report: "已修复所有严重问题，剩余 3 帧缩水 < 15%，1 个主题 hbox 可忽略"
