# AlphaGo / AlphaZero 论文资料

本目录收集了 DeepMind 围绕 AlphaGo、AlphaGo Zero、AlphaZero 的论文 PDF、补充材料和配套数据。它是一个文献与数据资料夹，不是完整的训练代码仓库。

## 文件总览

| 文件 | 内容 | 说明 |
| --- | --- | --- |
| `nature16961.pdf` | *Mastering the game of Go with deep neural networks and tree search* | Nature 2016，AlphaGo 早期论文，介绍策略网络、价值网络与 MCTS 结合的方法。DOI: `10.1038/nature16961` |
| `nature24270.pdf` | *Mastering the game of Go without human knowledge* | Nature 2017，AlphaGo Zero 论文，介绍不依赖人类棋谱、仅通过自我对弈训练的围棋系统。DOI: `10.1038/nature24270` |
| `AlphaZero.pdf` | *A general reinforcement learning algorithm that masters chess, shogi, and Go through self-play* | Science 2018，AlphaZero 论文，将 AlphaGo Zero 思路推广到国际象棋、将棋和围棋。DOI: `10.1126/science.aar6404` |
| `aar6404-silver-sm.pdf` | Science 2018 补充材料 | 对 `AlphaZero.pdf` 的方法、实验设置、补充图表和表格做更详细说明。 |
| `aar6404_datas1.zip` | Science 2018 Data S1 | `AlphaZero.pdf` 的配套数据压缩包，包含 Elo 数据、开局频率、伪代码和棋谱。 |

## 建议阅读顺序

1. `nature16961.pdf`：了解 AlphaGo 的基本架构，包括监督学习策略网络、强化学习策略网络、价值网络和搜索。
2. `nature24270.pdf`：阅读 AlphaGo Zero 如何去掉人类棋谱监督，只通过自我对弈完成训练。
3. `AlphaZero.pdf`：阅读 AlphaZero 如何把同一套强化学习与搜索框架扩展到国际象棋、将棋和围棋。
4. `aar6404-silver-sm.pdf` 与 `aar6404_datas1.zip`：查看 Science 2018 论文的实验细节、伪代码、Elo 曲线数据和棋谱数据。

## `aar6404_datas1.zip` 内容

压缩包内共有 106 个文件，主要包括：

| 路径 | 内容 |
| --- | --- |
| `pseudocode.py` | AlphaZero 算法伪代码，覆盖配置、自我对弈、MCTS、回放缓冲区和训练循环。该文件用于论文说明，不是可直接运行的完整实现。 |
| `figure1_elos.json` | 训练过程中 chess、shogi、go 的 Elo 变化数据。 |
| `figure3_chess_opening_frequency.json` | 国际象棋开局频率随训练变化的数据。 |
| `figure3_shogi_opening_frequency.json` | 将棋开局频率随训练变化的数据。 |
| `alphazero_vs_stockfish.pgn` | AlphaZero 与 Stockfish 8 的国际象棋对局，PGN 格式。 |
| `alphazero_vs_stockfish_tcec_positions.pgn` | 从 TCEC 开局局面出发的 AlphaZero 与 Stockfish 对局，PGN 格式。 |
| `shogi_games/1.csa` 到 `shogi_games/100.csa` | AlphaZero 与 elmo 的将棋对局，CSA 格式。 |

常用查看命令：

```bash
unzip -l aar6404_datas1.zip
unzip aar6404_datas1.zip -d data_s1
```

## 使用说明

- PDF 文件可直接使用任意 PDF 阅读器打开。
- PGN 文件可用常见国际象棋数据库或棋谱软件打开。
- CSA 文件可用支持 CSA 格式的将棋工具打开。
- `pseudocode.py` 是论文伪代码，包含若干占位函数和游戏相关接口，不包含完整棋类规则、网络结构实现或训练所需基础设施。
- 本目录没有模型权重、训练数据集或可复现实验所需的完整工程代码。

## 版权与引用

这些 PDF 和数据文件归原作者、出版方或数据提供方所有。若在论文、报告或代码注释中使用，请引用对应原文及 DOI。
