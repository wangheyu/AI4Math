# 基于 Jupyter、PyVista、VTK 的计算模拟三维渲染与可视化

## 1. 目标与定位

本提纲面向数值模拟结果展示，主线采用 **Jupyter + PyVista**。目标是把求解器输出的数据稳定转换为可检查、可交互、可复现的三维图像和动画。重点不是图形学底层算法，而是建立一条从模拟数组到 notebook 展示成果的工程流程。

适用对象包括：

- 3D Poisson、热传导、波动方程等标量场模拟。
- 流体、电磁、梯度场等向量场模拟。
- 有限元、有限体积、非结构网格等复杂几何结果。
- 课堂演示、论文插图、项目报告、批量参数对比。

## 2. 推荐工作流

```text
数值求解器
  -> NumPy / HDF5 / CSV / 原始二进制
  -> Jupyter notebook / Python 转换脚本
  -> PyVista 数据对象
  -> notebook 交互切片、等值面、glyph、体渲染
  -> VTK 数据文件与 PNG / MP4 / GIF / 报告插图
  -> 可选：ParaView 打开 .pvd/.vti 做桌面端检查
```

推荐把求解器和可视化解耦：求解器只负责输出物理量，notebook 或可视化脚本负责转换格式、控制颜色范围、相机和导出。

## 3. 数据模型与文件格式

### 3.1 常见数据集类型

| 模拟数据 | 推荐 VTK 类型 | 常见扩展名 | 说明 |
|----------|---------------|------------|------|
| 均匀三维数组 | `ImageData` | `.vti` | 适合规则笛卡尔网格上的温度、压力、密度 |
| 规则但坐标可变网格 | `StructuredGrid` | `.vts` | 适合曲线坐标、变形网格 |
| 三角面、边界面、粒子轨迹 | `PolyData` | `.vtp` | 适合曲面、线、点云 |
| 有限元/非结构网格 | `UnstructuredGrid` | `.vtu` | 适合四面体、六面体、混合单元 |
| 时间序列索引 | `ParaView Data` | `.pvd` | 管理多个时间步文件 |

### 3.2 字段设计

- `point data`：定义在节点上的量，例如温度、速度、位移。
- `cell data`：定义在单元上的量，例如材料编号、单元误差、有限体积通量。
- 标量场命名应包含物理含义，例如 `pressure`、`temperature`、`vorticity`。
- 向量场使用三分量数组，例如 `velocity = (u, v, w)`。

## 4. Python + VTK/PyVista 渲染管线

VTK 的核心管线为：

```text
DataSet -> Filter -> Mapper -> Actor -> Renderer -> RenderWindow
```

实际项目中建议使用 PyVista 作为高层接口：

- 读写 VTK 文件更简洁。
- 与 NumPy 数组互操作方便。
- 内置切片、等值面、glyph、流线、体渲染等方法。
- 可以离屏渲染，适合服务器和批量出图。

需要精细控制底层渲染对象、定制 VTK filter 或嵌入应用时，再直接使用原生 `vtk`。

## 5. 标量场展示方法

常用方法：

- 切片：展示体数据内部结构，适合压力、温度、误差场。
- 等值面：展示满足 `f(x,y,z)=c` 的三维结构。
- 体渲染：展示连续密度、浓度或医学图像。
- 投影和最大值投影：适合快速概览整体分布。

实践要求：

- 同一组对比图必须固定色标范围。
- 色条应标注物理量和单位。
- 正负量使用发散色图，非负量使用连续色图。
- 对异常值先做数值检查，不要只靠调整颜色掩盖问题。

## 6. 向量场展示方法

常用方法：

- glyph 箭头：展示稀疏采样后的方向和大小。
- 流线：展示稳态流场结构。
- 粒子轨迹：展示非稳态输运过程。
- 颜色编码：用颜色表示速度大小、涡量或压力。

实践要求：

- 对三维向量场先降采样，避免箭头过密。
- 箭头长度和颜色不要同时无控制地自动缩放。
- 流线入口点应说明来源，例如边界面、切片平面或随机种子。

## 7. 时间序列与动画

时间相关模拟建议输出：

```text
result_0000.vti
result_0001.vti
result_0002.vti
result.pvd
```

其中 `.pvd` 记录每个文件对应的时间值，ParaView 打开 `.pvd` 后即可使用时间轴播放。

动画制作原则：

- 固定相机位置。
- 固定色标范围。
- 固定窗口分辨率。
- 固定光照和背景。
- 文件名包含物理量、参数和时间步。

## 8. Jupyter + PyVista 交互式展示

Jupyter 是后续主界面，适合把说明、公式、代码、图像和交互视图放在同一个文档中。推荐流程：

1. 在 notebook 中读取 NumPy 数组或 VTK 文件。
2. 用 PyVista 构造 `ImageData`、`StructuredGrid` 或 `UnstructuredGrid`。
3. 用 `slice_orthogonal`、`contour`、`glyph`、`streamlines` 等方法做后处理。
4. 用 `Plotter.show()` 在 notebook 中交互查看。
5. 用 `screenshot()` 固定相机和色标后导出报告图片。
6. 把数据另存为 `.vti/.vtu/.pvd`，保留与 ParaView 兼容的出口。

推荐 notebook 后端：

```python
import pyvista as pv

pv.set_jupyter_backend("trame")
```

如果当前浏览器或服务器不支持交互后端，可以使用离屏渲染：

```python
p = pv.Plotter(off_screen=True)
p.add_mesh(mesh)
p.screenshot("figure.png")
```

## 9. ParaView 可选后处理

ParaView 不作为主线，但适合在有桌面环境时快速探索和调试 VTK 文件。推荐流程：

1. 打开 `.pvd`、`.vti`、`.vts` 或 `.vtu` 文件。
2. 在 `Pipeline Browser` 中添加 filter。
3. 使用 `Coloring` 选择物理字段。
4. 固定色标范围并显示 color bar。
5. 调整相机、透明度、坐标轴和注释。
6. 保存 `.pvsm` state 文件，保证下次可复现。

常用 filter：

- `Slice`：切开体数据。
- `Clip`：裁剪几何。
- `Contour`：提取等值面。
- `Threshold`：按数值范围筛选区域。
- `Glyph`：绘制向量箭头。
- `Stream Tracer`：绘制流线。
- `Calculator`：派生新物理量。
- `Warp By Vector`：展示位移变形。

注意：ParaView 是 Qt 桌面程序，通常需要本地桌面、X11 转发、VNC 或 Wayland/X11 会话。若在服务器、容器或受限终端中出现 `could not connect to display`、`xcb` 插件错误或 MPI/PMIx socket 错误，不影响 VTK 文件本身；可以继续用 PyVista 离屏渲染，或把 `.pvd/.vti` 结果复制到有桌面环境的机器上用 ParaView 打开。

## 10. 自动化与批量渲染

批量渲染优先使用 Python + PyVista：

- Jupyter notebook：适合教学演示和逐步调参。
- Python 脚本：适合批量生成图片、视频和 VTK 时间序列。
- ParaView trace / `pvpython`：仅在必须复用 ParaView 桌面 pipeline 时使用。

自动化脚本应把以下参数显式写入代码：

- 输入数据路径。
- 输出目录。
- 物理字段名。
- 色标范围。
- 相机位置。
- 图片分辨率。
- 时间步范围。

## 11. 示例项目设计

建议使用一个三维 Poisson 或热传导示例贯穿全流程：

- 用 NumPy 生成规则三维网格。
- 构造一个随时间变化的标量场。
- 写出 `.vti` 时间步和 `.pvd` 索引。
- 在 Jupyter 中用 PyVista 渲染切片和等值面。
- 可选：用 ParaView 打开 `.pvd`，检查时间序列和 filter 效果。
- 保存 notebook、VTK 文件和最终截图。

本目录中的 `simulation_visualization_jupyter_pyvista.ipynb` 和 `simulation_visualization_demo.py` 实现了这一最小闭环。

## 12. 验收标准

完成本主题后，应能做到：

- 将 NumPy 三维数组转换为 ParaView 可读的 VTK 文件。
- 在 Jupyter 中用 PyVista 渲染带坐标轴、色条、标题的三维视图。
- 在 notebook 中完成切片、等值面、阈值或 glyph 操作。
- 对时间序列结果生成 `.pvd` 并播放动画。
- 使用固定相机和固定色标复现同一张图。
