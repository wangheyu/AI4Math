# Week 13: Python 三维可视化

本目录整理 Python 科学绘图、Jupyter + PyVista 三维渲染、VTK 数据导出与可选 ParaView 后处理相关材料。

当前主线是 **Jupyter + PyVista**：在 notebook 中完成数据生成、三维交互查看、截图导出和动画准备。ParaView 只作为可选桌面工具，用于在有图形界面时检查 `.pvd/.vti` 文件。

## 主要材料

| 文件 | 说明 |
|------|------|
| `environment.yml` | Conda 环境，包含 `vtk`、`pyvista`、`trame`、`meshio` 等三维可视化依赖 |
| `python_plotting_jupyterlab_beamer.tex` | Python 绘图与 JupyterLab 讲义 |
| `multivariable_calculus_visuals_vtk.ipynb` | 使用原生 VTK 绘制曲面、等高线和离屏 PNG |
| `pyvista_animation_examples.py` | 使用 PyVista 生成曲面动画 |
| `three_dimensional_visualization_outline.md` | 三维科学可视化教学提纲 |
| `opendx_to_pyvista.py` | 将本目录 OpenDX 样例数据转换为 PyVista/VTK 数据对象 |
| `opendx_jupyter_pyvista_cases.ipynb` | Jupyter + PyVista 主 notebook：四个带滑块交互的 OpenDX 三维可视化案例 |
| `opendx_colorado_dash.py` | 非 Jupyter 的 Dash + Plotly Colorado 地形实时交互 Web app |
| `opendx_data/` | OpenDX 教学样例数据：地形、电子密度、气象场、MRI |
| `simulation_visualization_jupyter_pyvista.ipynb` | Jupyter + PyVista 主线示例：生成模拟数据、交互切片、等值面和截图 |
| `simulation_visualization_vtk_paraview.md` | 面向计算模拟结果展示的 Jupyter/PyVista/VTK 实践提纲，ParaView 为可选工具 |
| `simulation_visualization_demo.py` | 生成三维模拟数据、写出 VTK 时间序列、渲染截图的最小示例 |

## 快速运行

```bash
conda env create -f environment.yml
conda activate ai4math-vis

python simulation_visualization_demo.py --output-dir outputs/simulation_demo
jupyter lab opendx_jupyter_pyvista_cases.ipynb
jupyter lab simulation_visualization_jupyter_pyvista.ipynb
```

生成结果包括：

- `poisson_demo_*.vti`：每个时间步的三维规则网格数据。
- `poisson_demo.pvd`：ParaView 可直接打开的时间序列索引。
- `poisson_slice.png`：离屏渲染截图。
- `poisson_isosurface.png`：等值面渲染截图。

## 主线选择

后续课程和项目展示优先采用 Jupyter + PyVista：

- notebook 中保留文字、公式、代码、图像和交互视图，便于讲解和复现。
- PyVista 直接读取/写出 VTK 文件，仍然兼容 ParaView。
- 离屏渲染可以在没有桌面的环境中生成 PNG。
- 参数扫描和批量出图可以直接复用 Python 科学计算代码。

## OpenDX 四案例

`opendx_jupyter_pyvista_cases.ipynb` 使用 `opendx_data/` 中的真实样例数据：

- `colorado.tiff` + `colorado_elev.vit`：地形照片贴到三维高程表面，可调高度缩放。
- `watermolecule.dx`：水分子电子密度等值面，可调等值面阈值和透明度。
- `cloudwater.dx` + `wind.dx`：云水标量场叠加风场 glyph，可调云水阈值、箭头密度和箭头长度。
- `MRI.data` + `mri.general`：MRI 医学体数据切片，可调 `x/y/z` 切片位置和灰度窗宽。

## Dash + Plotly 地形展示

不使用 Jupyter 时，可以直接启动 Dash app：

```bash
conda activate ai4math-vis
python opendx_colorado_dash.py
```

然后打开 `http://127.0.0.1:8050`。该 app 使用 Plotly `go.Surface` 展示 Colorado 地形，支持高度缩放、采样分辨率、颜色模式、光源位置、材质光照和相机位置实时调整。

快捷键：

- `[` / `]`：降低/提高地形高度缩放。
- `1`、`2`、`4`、`5`、`8`：切换采样步长，`1` 是原始 `400 x 400` 分辨率。
- `c`：切换影像灰度和高程色图。
- `w/a/s/d/q/e`：调整光源位置。
- 方向键和 `PageUp` / `PageDown`：调整相机位置。
- `r`：重置参数。
- `h`：显示/隐藏快捷键说明。

## ParaView 说明

本目录的脚本只依赖 `environment.yml` 中的 VTK/PyVista，不要求 ParaView GUI 能在当前终端环境启动。

如果运行 `paraview` 出现 `could not connect to display`、`Could not load the Qt platform plugin "xcb"` 或 MPI/PMIx socket 错误，通常表示当前会话没有可用桌面显示或系统级 ParaView 受运行环境限制。此时仍可先用 Python 生成 `.vti/.pvd` 和截图，再在本机桌面版 ParaView 中打开 `poisson_demo.pvd`。
