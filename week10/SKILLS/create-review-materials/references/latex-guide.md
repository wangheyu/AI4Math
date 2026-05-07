# LaTeX 中文数学文档指南

## 文档模板

### 复习提纲 (outline.tex)

```latex
\documentclass[12pt,a4paper]{ctexart}

\usepackage[a4paper,margin=2.6cm]{geometry}
\usepackage{amsmath,amssymb,amsthm,mathtools,bm}
\usepackage{physics}
\usepackage{esint}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage[hypertexnames=false]{hyperref}

\hypersetup{
  colorlinks=true,
  linkcolor=blue,
  urlcolor=blue,
  citecolor=blue
}

% ---- 定理环境 ----
\newtheorem{theorem}{定理}[section]
\newtheorem{definition}[theorem]{定义}
\newtheorem{proposition}[theorem]{命题}
\newtheorem{corollary}[theorem]{推论}
\newtheorem{lemma}[theorem]{引理}
\theoremstyle{remark}
\newtheorem{remark}{注记}[section]
\newtheorem{example}{例}[section]
\theoremstyle{definition}
\newtheorem{method}{方法}[section]

\title{复习提纲}
\author{}
\date{}

\begin{document}

\maketitle

\begin{abstract}
本提纲基于 [资料来源] 整理，涵盖所有核心考点，
包括定义、定理、公式、方法和典型应用。
\end{abstract}

\tableofcontents

% ---- 正文按章节展开 ----

\end{document}
```

### 练习题 (exercises.tex)

```latex
\documentclass[12pt,a4paper]{ctexart}

\usepackage[a4paper,margin=2.6cm]{geometry}
\usepackage{amsmath,amssymb,amsthm,mathtools,bm}
\usepackage{physics}
\usepackage{esint}
\usepackage{booktabs}
\usepackage{enumitem}

\title{复习练习题}
\author{}
\date{}

\begin{document}

\maketitle

% ---- 使用 \section* 分组 ----
\section*{第一章 \quad [章节标题]}

\begin{enumerate}[leftmargin=*,label=\arabic*.]
  \item [题目内容]
  \item ...
\end{enumerate}

\end{document}
```

### 练习题答案 (exercises-answers.tex)

结构与练习题相同，但在每道题后加入 `\textbf{解：}` 段落。答案使用与题目相同的编号。

### 模拟卷 (exam.tex)

```latex
\documentclass[12pt,a4paper]{ctexart}

\usepackage[a4paper,margin=2.6cm]{geometry}
\usepackage{amsmath,amssymb,amsthm,mathtools,bm}
\usepackage{physics}
\usepackage{esint}
\usepackage{booktabs}
\usepackage{enumitem}

\title{模拟试卷}
\author{}
\date{}

\begin{document}

\maketitle

\begin{center}
\textbf{总分：100 分 \quad 考试时间：120 分钟}
\end{center}

\bigskip

% ---- 题型分组，每题标注分值 ----
\section*{一、填空题（每题 X 分，共 XX 分）}
\section*{二、计算题（每题 X 分，共 XX 分）}
\section*{三、证明题（每题 X 分，共 XX 分）}

\end{document}
```

### 模拟卷答案 (exam-answers.tex)

包含试卷原题 + 详细解答，每题前注明分值。答案使用 `\textbf{解：}` 环境展开。

## LaTeX 编写规范

### 数学符号

- 向量：使用 `\vec{v}` 或 `\mathbf{v}`，与资料来源保持一致
- 集合：`\mathbb{R}`, `\mathbb{N}`, `\mathbb{Z}`, `\mathbb{Q}`, `\mathbb{C}`
- 微分：使用 physics 宏包的 `\dd{x}`, `\dv{x}`, `\pdv{x}` 或标准 `dx`, `\frac{dy}{dx}`
- 范数：`\norm{x}`（physics 宏包）或 `\|x\|`
- 内积：`\langle x, y \rangle`
- 极限：`\lim_{x \to 0}`
- 求和/积分：`\sum`, `\int`

### 定理环境使用

```latex
\begin{definition}[函数极限]
设函数 $f$ 在点 $x_0$ 的某个去心邻域内有定义...
\end{definition}

\begin{theorem}[拉格朗日中值定理]
若函数 $f$ 满足...
\end{theorem}

\begin{proof}
由条件可知...
\end{proof}

\begin{remark}
该定理的条件是充分的，但不必要...
\end{remark}
```

### 中文相关

- ctexart 自动处理中文字体和间距
- 数学模式内的中文：`\text{其中}` 
- 中文标点在 ctexart 中自动处理
- 章节标题中可自由使用中文

### 编号体系

- 提纲中保留资料来源的定理/公式编号
- 使用 `\label{thm:xxx}` 和 `\ref{thm:xxx}` 进行引用
- 练习题和模拟卷的公式编号独立于来源资料

### 常见问题

1. `\bm` 用于加粗希腊字母：`\bm{\alpha}`
2. 分段函数用 `\begin{cases}` 
3. 矩阵用 `\begin{pmatrix}` 或 `\begin{bmatrix}`
4. 对齐公式用 `\begin{align}` 或 `\begin{aligned}`
5. 中文顿号在 LaTeX 中直接输入 `、`（ctex 支持）
6. 中文书名号直接输入 `《》`（ctex 支持）
7. 闭曲面积分符号 `\oiint` 需要 `esint` 宏包（Gauss 公式等场景）

## 编译

所有 .tex 源文件位于 `review-src/`，通过项目根目录的 Makefile 统一编译。

```bash
make all                # 编译全部 5 份 PDF 到 review-doc/
make outline            # 仅编译提纲
make clean              # 删除 build/ 和 review-doc/
make rebuild            # clean + all
```

Makefile 内部使用 `latexmk -xelatex -outdir=build -cd` 编译，过程文件全部进入 `build/`，最终 PDF 复制到 `review-doc/`。

## 质量检查清单

编译完成后，打开 PDF 逐项检查：
- [ ] 所有中文字符正确显示（无乱码、无缺失）
- [ ] 数学公式渲染正确（无断裂、无错位）
- [ ] 定理编号连续且正确
- [ ] 页码、目录、交叉引用正确
- [ ] 无 overfull hbox 导致的溢出
