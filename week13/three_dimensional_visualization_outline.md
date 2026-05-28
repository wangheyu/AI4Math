# 三维科学可视化教学提纲：Jupyter + PyVista + VTK

## 1. 教学目标

本模块面向计算模拟结果展示，目标是让学生掌握从数值数据到三维可视化成果的完整流程：

- 理解三维科学可视化中的数据类型、网格类型和可视化映射。
- 理解 VTK 的数据模型和渲染管线。
- 掌握在 Python/Jupyter 中用 PyVista 调用 VTK 能力的方法。
- 用真实 OpenDX 样例完成四个可复现案例：地形、分子电子密度、气象场、MRI 体数据。

主线工具为 **Jupyter + PyVista**。ParaView 只作为可选桌面工具，不作为课程运行前提。

## 2. 三维可视化基本概念

### 2.1 数据对象

- 标量场：每个空间点对应一个数值，例如温度、压力、密度、高程、电子密度。
- 向量场：每个空间点对应一个向量，例如速度、风场、力场、梯度。
- 点数据：数据定义在网格节点上。
- 单元数据：数据定义在网格单元上。

### 2.2 网格类型

- 规则网格：坐标轴均匀排列，适合 MRI、规则三维数组、体数据。
- 结构网格：拓扑规则，但坐标可变形，适合地形面、曲线坐标网格。
- 非结构网格：任意连接关系，适合有限元四面体/六面体网格。
- PolyData：点、线、面数据，适合曲面、轨迹、边界。

### 2.3 常用可视化映射

- 切片：查看三维体数据内部结构。
- 等值面：显示 `f(x,y,z)=c` 的三维曲面。
- 体渲染：用颜色和透明度表达整个体数据。
- Glyph：用箭头、圆锥、球等符号表达向量或点属性。
- 流线：展示向量场中的积分轨迹。
- 纹理贴图：把二维图像贴到三维几何上。
- Rubber sheet：用高程值把二维平面抬升为三维地形。

## 3. VTK 简介

VTK 是科学可视化领域常用的底层工具包。它提供数据结构、过滤器、映射器和渲染系统，是 ParaView 和 PyVista 的基础。

### 3.1 VTK 数据模型

- `vtkImageData`：规则体数据。
- `vtkStructuredGrid`：结构网格。
- `vtkPolyData`：点、线、三角面、多边形。
- `vtkUnstructuredGrid`：非结构网格。

### 3.2 VTK 渲染管线

```text
DataSet -> Filter -> Mapper -> Actor -> Renderer -> RenderWindow
```

- DataSet 保存坐标、连接关系和物理字段。
- Filter 对数据做切片、等值面、阈值、流线等处理。
- Mapper 把数据映射到颜色和几何。
- Actor 是场景中的可见对象。
- Renderer 管理相机、光照、背景和最终画面。

### 3.3 VTK 文件格式

- `.vti`：规则体数据。
- `.vts`：结构网格。
- `.vtp`：PolyData 曲面/点线数据。
- `.vtu`：非结构网格。
- `.pvd`：时间序列索引。

## 4. Python 调用 VTK 接口

### 4.1 原生 VTK

原生 `vtk` 接口接近 C++ 对象模型，适合讲解底层管线和做精细控制，但代码较长。典型步骤是创建数据对象、filter、mapper、actor、renderer 和 render window。

### 4.2 PyVista

PyVista 是 VTK 的 Python 高层接口，更适合课程和 notebook：

- 与 NumPy 数组互操作直接。
- 一行即可完成切片、等值面、glyph、体渲染等操作。
- 支持 Jupyter 交互后端。
- 能读写 VTK 文件，保留与 ParaView 的兼容性。

课程代码优先使用 PyVista；需要解释底层机制时回到 VTK 管线。

## 5. 案例 1：Colorado 地形照片 + 高程

### 数据

```text
week13/opendx_data/colorado.tiff
week13/opendx_data/colorado_elev.vit
week13/opendx_data/colo_elev.general
```

### 目标

- 读取二维地形照片。
- 读取 400 x 400 高程数据。
- 构造三维结构网格表面。
- 把照片作为 texture 贴到高程表面。

### 教学点

- 二维影像和高程场的配准。
- `StructuredGrid`。
- texture coordinates。
- 地形 surface warping。

### 预期结果

生成一个可旋转的三维地形表面，表面颜色来自原始 `colorado.tiff`，几何高度来自 `colorado_elev.vit`。展示时使用滑块动态调整高度缩放。

## 6. 案例 2：水分子电子密度等值面

### 数据

```text
week13/opendx_data/watermolecule.dx
```

### 目标

- 解析 OpenDX 规则三维标量场。
- 构造 PyVista `StructuredGrid`。
- 用等值面显示电子密度分布。
- 调整等值面阈值、颜色和透明度。

### 教学点

- 三维标量场。
- 等值面提取。
- 标量范围和阈值选择。
- 分子电子云的视觉表达。

### 预期结果

显示一个由多个电子密度等值面构成的三维电子云图。展示时使用滑块动态调整等值面阈值和透明度。

## 7. 案例 3：气象模拟：云水 + 风场

### 数据

```text
week13/opendx_data/cloudwater.dx
week13/opendx_data/wind.dx
```

### 目标

- 读取云水标量场。
- 读取三维风场向量。
- 用切片或等值面显示云水分布。
- 用 glyph 或 streamlines 显示风场。
- 叠加标量场和向量场。

### 教学点

- 多物理量联合展示。
- 标量场与向量场同网格对齐。
- glyph 降采样。
- 流线种子点。

### 预期结果

在同一个三维场景中显示云水结构和风场方向，说明气象模拟数据如何转化为可解释图像。展示时使用滑块动态调整云水阈值、风场采样密度、箭头长度和云水透明度。

## 8. 案例 4：MRI 医学体数据

### 数据

```text
week13/opendx_data/MRI.data
week13/opendx_data/mri.general
```

### 目标

- 读取 128 x 128 x 16 的 unsigned short 体数据。
- 构造 PyVista `ImageData`。
- 显示三个正交切片。
- 尝试体渲染并调整透明度映射。

### 教学点

- 医学体数据。
- `ImageData` 的 origin、spacing、dimensions。
- 正交切片。
- volume rendering 和 opacity transfer function。

### 预期结果

生成 MRI 三维数据的切片视图，可用于说明体数据的内部结构展示方法。展示时使用滑块动态调整 `x/y/z` 三个方向的切片位置和灰度显示窗口。

## 9. 最终产物

- `opendx_to_pyvista.py`：OpenDX 样例数据到 PyVista 数据对象的转换工具。
- `opendx_jupyter_pyvista_cases.ipynb`：四个带滑块动态交互的案例主 notebook。
- `opendx_data/`：复制到课程目录下的样例数据。

## 10. 验收标准

- notebook 能从 `week13/opendx_data` 读取全部四组数据。
- 每个案例至少生成一个带参数控件的可交互三维视图。
- 每个案例能离屏导出一张 PNG。
- 所有可视化都包含清晰的字段名、颜色映射和相机设置。
- 不依赖 ParaView GUI。
