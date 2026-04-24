# Week 9 Project: Sun-Earth System Analysis and Simulation

本文件夹是一个关于“日地系统的理论分析与数值模拟”的课程/报告项目。下面只列出建议提交到 git 的源文件和配置文件，不包含编译产物、运行输出和代码生成的图片。

## 目录结构

```text
.
├── report.tex
├── chapters/
├── qian.bib
├── README.md
├── data/
├── .latexmkrc
└── src/
```

## 报告文件

| 文件 | 功能 |
| --- | --- |
| `report.tex` | LaTeX 主文件。负责文档结构、宏包、标题和章节引入。 |
| `chapters/chap01.tex` | 第一章正文，内容是日地系统理论分析。 |
| `chapters/chap02.tex` | 第二章正文，内容是日地系统数值模拟。 |
| `chapters/appendix.tex` | 附录正文，内容是 JPL、Horizons 和 `astroquery` 的介绍。 |
| `qian.bib` | BibTeX 参考文献数据库，保存报告中引用的书籍、论文、JPL 页面和软件文档。 |
| `.latexmkrc` | `latexmk` 的本地配置，定义编译输出目录。 |

## Python 源码与参数文件

`src/` 目录保存数值模拟程序和可导入的初始条件配置。

| 文件 | 功能 |
| --- | --- |
| `src/ES_circle.py` | 二维无量纲圆轨道实验脚本，包含 Euler 和 Velocity-Verlet 积分、能量/角动量计算与误差评估。 |
| `src/Euler_vs_Verlet.py` | 二维圆轨道数值对比脚本，包含两种积分方法的实现与实验逻辑。 |
| `src/JPL.py` | 三维 JPL Horizons 对比脚本，包含状态向量获取、数值传播与误差计算逻辑。 |
| `src/two_body_realtime.py` | Tkinter 实时二维双体模拟器，支持手动输入参数或导入 JSON profile。 |

## 数据文件

`data/` 目录保存可复用的 JSON 初始条件配置。

| 文件 | 功能 |
| --- | --- |
| `data/circle.json` | `two_body_realtime.py` 可导入的等质量近圆轨道初值配置。 |
| `data/sun_earth.json` | 日地系统圆轨道近似初值配置，单位为 kg、km、km/s 和 s。 |
| `data/real_sun_earth.json` | 更接近真实历元的二维日地初值配置。 |

## 图片文件

`figures/` 目录保存报告中使用的图片。这里只列出不是由代码自动生成的图片。

| 文件 | 功能 |
| --- | --- |
| `figures/jpl.png` | 附录中使用的 JPL 早期团队相关图片。 |
| `figures/qian.png` | 附录中使用的钱学森相关图片。 |
