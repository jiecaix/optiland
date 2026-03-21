# Optiland 可视化构建总方案：面向 *Adjoint Nonlinear Ray Tracing* 的渐变介质与伴随工作流

**编写时间**: 2026-03-21  
**状态**: 总体方案 / 第一版  
**目标**: 基于论文配图与参考实现 `ArjunTeh/AdjointNonlinearRayTracing`，为 Optiland 规划一套“可看、可算、可验证、可扩展”的可视化构建路线。

---

## 1. 背景与目标

从给定图片可以看出，参考工作并不只是“把光线画出来”，而是围绕 **非线性光线追迹 + 可微优化 + 伴随梯度验证** 建立了一整套研究型可视化链路，至少包含以下四类图像：

1. **介质中的轨迹图**：展示光线如何在空间变折射率场中弯曲、聚焦或回折。  
2. **折射率场 / 梯度场图**：展示 GRIN 或其他体介质中的标量场与导数场。  
3. **优化过程图**：展示 loss、梯度、参数场如何随迭代变化。  
4. **方法对比图**：对比 finite differences、reverse-mode AD、adjoint state method 的速度、误差与稳定性。

而 Optiland 当前已经具备以下基础能力：

- 具备 **2D Matplotlib** 与 **3D VTK** 的系统级可视化框架；
- 具备 **GradientMaterial + GRINPropagation** 的渐变介质表达与 RK4 光线传播；
- 具备 **PyTorch backend / differentiable wrappers** 的可微优化入口；
- 已经有一批围绕 **GRIN / Drude / 对称采样** 的实验脚本和中文分析文档。

因此，当前最合理的目标不是“从零重写一套 AdjointNonlinearRayTracing”，而是：

> 在 Optiland 现有架构上，增量式补齐 **体介质可视化、轨迹记录、梯度验证、优化过程面板、研究复现实验** 五个层级，先做出可演示版本，再推进到研究级版本。

---

## 2. 参考仓库给我们的关键信号

参考仓库 `ArjunTeh/AdjointNonlinearRayTracing` 与配图透露出几个非常明确的设计重点：

### 2.1 核心问题不是传统透镜，而是“体介质中的射线动力学”

参考实现强调的是 **inhomogeneous media**，即折射率随空间变化的介质。它的核心对象不是单个表面折射，而是：

- 体内连续传播；
- 路径对介质参数敏感；
- 目标函数对整条轨迹敏感；
- 梯度不能只靠表面处的局部导数。

这与 Optiland 当前 `GradientMaterial` + `GRINPropagation` 的方向是一致的，但还缺少“研究级展示层”。

### 2.2 配图中的亮点在“对比验证”而不是“单张漂亮图”

图片里最有价值的部分包括：

- 有限差分、反向自动微分、伴随方法的 **并列对照图**；
- 相对误差热图；
- 轨迹、loss 曲线、梯度对比、参数场重建等 **成组图板**；
- 对 **arc-length parameterization** 与可逆性问题的强调。

这说明如果 Optiland 要做“对标式可视化”，重点不是再补一张静态 layout 图，而是建立：

- **实验脚本标准化**；
- **轨迹/梯度/log 自动落盘**；
- **可复现实验图板生成器**；
- **误差基准与性能基准**。

### 2.3 参考实现是“研究原型”，Optiland 需要的是“平台化落地”

参考仓库是以论文实验为中心组织的；而 Optiland 是一个更通用的光学平台。  
所以移植思路应该是：

- 保留参考工作的 **实验结构**；
- 但实现方式要服从 Optiland 的 **Material / Propagation / Visualization / Optimization** 分层；
- 让新增能力可以继续服务于其他体介质、自由曲面、机器学习优化案例。

---

## 3. Optiland 当前能力盘点

### 3.1 已有能力

当前代码库中已经有足够好的起点：

- `optiland/materials/gradient_material.py`：已支持位置相关折射率与解析梯度；
- `optiland/propagation/grin.py`：已支持 GRIN 介质中的 RK4 传播；
- `optiland/visualization/system/optic_viewer.py`：已能做 2D 系统与光线显示；
- `optiland/visualization/system/optic_viewer_3d.py`：已能做 3D VTK 可视化；
- `optiland/ml/wrappers.py`：已打通 PyTorch 模块化优化入口；
- `docs/gallery/differentiable_ray_tracing.rst` 与 Tutorial 1f：已具备“可微光线追迹”对外叙事。

### 3.2 当前短板

如果要达到论文配图那种研究表达能力，当前缺口主要有六个：

1. **缺少体介质场可视化器**  
   目前更偏“系统布局视图”，缺少 `n(x,y,z)`、`∇n`、速度场、折射率切片热图等统一接口。

2. **缺少轨迹历史记录标准对象**  
   `GRINPropagation` 目前重点是把光线推进到出口，但没有标准化地输出每一步状态历史。

3. **缺少梯度验证实验基准**  
   目前有 PyTorch 可微入口，但缺少“有限差分 vs autograd vs 伴随”的统一 benchmark。

4. **缺少伴随法专用抽象层**  
   现在是 autograd 友好，但还没有显式的 adjoint-state workflow 抽象。

5. **缺少论文风格图板生成器**  
   图像生成主要还停留在脚本级拼图，缺少固定版式、自动命名、自动输出统计摘要。

6. **缺少研究案例目录化管理**  
   目前 GRIN/Drude 例子很有价值，但尚未提升为“可复现研究 casebook”。

---

## 4. 总体建设思路

建议把这项工作拆成 **一个内核、两条链路、三个阶段**。

### 4.1 一个内核：体介质可视化数据模型

先定义一个统一的数据层，而不是直接写散乱脚本。

建议新增一个类似 `VolumeVisualizationDataset` 或 `RayTrajectoryRecord` 的概念，负责承载：

- 介质采样网格：`x/y/z grid`；
- 标量场：`n`、`loss density`、`relative error`；
- 向量场：`grad_n`、`ray_direction`、`adjoint variables`；
- 轨迹历史：每条 ray 在每个 step 的 `x,y,z,L,M,N,opd,...`；
- 优化历史：iteration、loss、gradient norm、timing、constraint metrics。

一旦这个数据层稳定，后面无论是 Matplotlib 还是 VTK，2D 还是 3D，静态图还是动画图，都能复用。

### 4.2 两条链路

#### A. 研究展示链路

面向论文图、报告图、教程图：

- 切片热图；
- 轨迹叠加图；
- 梯度对比图；
- 误差热图；
- 优化迭代图；
- 多方法对比图板。

#### B. 开发调试链路

面向数值问题定位：

- 单步积分轨迹检查；
- 活跃 ray 掩码变化；
- 边界 overshoot 检查；
- 复数泄漏 / NaN / 非物理解报警；
- autograd 图是否断裂的诊断信息。

### 4.3 三个阶段

- **阶段 1：看得见** —— 先把场和轨迹稳定画出来；
- **阶段 2：比得清** —— 再做梯度/误差/性能对比；
- **阶段 3：可优化** —— 最后接入伴随或半伴随优化工作流。

---

## 5. 推荐的模块拆分

建议不要把所有逻辑继续堆在单个 example 脚本里，而是新增以下逻辑层。

### 5.1 材料与传播层

#### 模块 A：体介质采样器

建议新增：

- `optiland/visualization/volume/sampler.py`
- 输入：material、采样范围、分辨率、波长；
- 输出：折射率场、梯度场、有效掩码。

它的职责是把 `GradientMaterial.get_index_and_gradient()` 变成统一的 2D/3D 栅格采样结果。

#### 模块 B：轨迹记录器

建议新增：

- `optiland/propagation/trajectory.py` 或 `optiland/rays/trajectory.py`

职责：

- 在 GRIN RK4 积分每一步记录状态；
- 支持稀疏记录（每 N 步记录一次）；
- 支持只记录被选中的 ray；
- 支持导出为 NumPy / pandas / JSON 友好的格式。

这将是后续所有“论文配图型轨迹图”的基础。

### 5.2 可视化层

#### 模块 C：2D 体场查看器

建议新增：

- `optiland/visualization/volume/field_viewer.py`

能力：

- `n(x,z)` / `n(y,z)` 切片热图；
- `dn/dx, dn/dz, |∇n|` 热图；
- 等值线 + 轨迹叠加；
- turning point / caustic / target marker 标注。

#### 模块 D：3D 体场查看器

建议新增：

- `optiland/visualization/volume/field_viewer_3d.py`

能力：

- 体切片；
- iso-surface；
- ray tube / streamline；
- 3D target / sensor / source geometry overlay。

如果初期 VTK 工作量偏大，可以先只做 2D 切片和 3D 轨迹线框。

#### 模块 E：论文图板生成器

建议新增：

- `optiland/visualization/report/adjoint_panels.py`

能力：

- 一次性生成 2×2、2×3、1×4 等固定版式图板；
- 自带统一标题、色条、统计角标；
- 自动输出 PNG + SVG；
- 自动写出对应的 markdown 摘要。

### 5.3 优化与验证层

#### 模块 F：梯度基准框架

建议新增：

- `optiland/optimization/benchmarks/gradient_benchmarks.py`

三种模式：

1. finite difference；
2. reverse-mode autograd（当前 PyTorch 路线）；
3. adjoint / semi-adjoint（新路线）。

输出统一的：

- 梯度向量；
- 计算时间；
- 相对误差；
- 峰值显存 / 内存（如果可测）；
- 成功率与异常统计。

#### 模块 G：研究案例脚本

建议新增 `examples/examples/adjoint_nonlinear_ray_tracing/` 目录，按案例拆分：

- `case01_luneburg_forward.py`
- `case02_gradient_check.py`
- `case03_adjoint_vs_autograd.py`
- `case04_arc_length_parameterization.py`
- `case05_inverse_design_demo.py`

这样后续可以逐步向参考仓库的实验靠拢，而不会污染通用 API。

---

## 6. 建议优先复现的图像类型

建议按“投入最小、价值最高”的顺序来做。

### P0：先做这些

#### 图 1：GRIN 折射率切片 + 光线轨迹叠加图

目标：快速形成与论文最接近的“核心视觉”。

内容：

- 背景：`n(x,z)` 或 `n(y,z)` 热图；
- 前景：多条 ray trajectory；
- 标注：源位置、目标面、转向点、边界。

价值：

- 一图同时表达“介质场 + 路径动力学”；
- 能立刻暴露轨迹积分、边界条件、采样分辨率问题。

#### 图 2：`|∇n|` / `dn/dz` / `dn/dx` 对比图

目标：把当前 GRIN/Drude 相关实现中的梯度合理性问题可视化标准化。

内容：

- 正确公式 vs 当前实现；
- 实部/虚部分离；
- cutoff 区域高亮。

#### 图 3：trajectory history 调试图

目标：用于数值调试，而不是对外展示。

内容：

- step index vs z；
- step size vs iteration；
- direction cosine vs path length；
- active mask count vs iteration。

### P1：第二批

#### 图 4：finite difference / autograd / adjoint 三联图

内容：

- 左：有限差分梯度结果；
- 中：reverse-mode AD；
- 右：adjoint；
- 附图：relative error。

这类图是对标参考工作最关键的科研表达之一。

#### 图 5：优化过程图板

内容：

- loss 曲线；
- gradient norm 曲线；
- 参数场快照（初始/中期/最终）；
- 输出图像或 target mismatch 图。

### P2：第三批

#### 图 6：arc-length parameterization 对比图

内容：

- conventional parameterization；
- arc-length parameterization；
- loss landscape 对比；
- gradient corruption / instability 热图。

这是论文配图中“研究味”最浓的一部分，但实现门槛更高，建议放到后期。

---

## 7. 推荐实施顺序

### 阶段 1：两周左右的最小可演示版本（MVP）

**目标**：在 Optiland 中做出第一张“像论文图”的图板。

#### 交付物

1. 轨迹记录功能（先支持 GRINPropagation）；
2. 2D 体场采样器；
3. 折射率切片 + 轨迹叠加图；
4. 1 个独立 example；
5. 1 篇中文说明文档。

#### 验收标准

- 能稳定画出 10~100 条 ray 的历史轨迹；
- 能输出 `n` 与 `|∇n|` 的切片热图；
- 图像可重复生成；
- 能在现有 GRIN 示例基础上运行。

### 阶段 2：方法对比与验证

**目标**：建立“可验证”链路。

#### 交付物

1. gradient benchmark 脚本；
2. finite difference 与 autograd 对比图；
3. relative error 热图；
4. 统一实验配置文件；
5. 自动输出结果摘要表。

#### 验收标准

- 在至少一个简单案例上，FD 与 autograd 梯度趋势一致；
- 能量化误差与运行时间；
- 图板生成无需人工拼图。

### 阶段 3：伴随法与逆设计案例

**目标**：建立真正对标参考仓库的研究案例。

#### 交付物

1. adjoint / semi-adjoint 求导原型；
2. inverse design demo；
3. arc-length parameterization 实验；
4. 论文风格完整复现实验包。

#### 验收标准

- 在参数量上升时，adjoint 路线相对 FD 明显更有优势；
- 能复现至少一组参考风格图；
- 能在文档中解释误差来源与稳定性边界。

---

## 8. 与 Optiland 现有架构的映射关系

建议按下表对接，而不是绕开现有框架重写。

| 目标能力 | 优先复用的 Optiland 模块 | 建议新增内容 |
|---|---|---|
| 体介质折射率表达 | `materials/gradient_material.py` | 支持更通用的 callable / grid / neural field 介质 |
| 体介质传播 | `propagation/grin.py` | 轨迹记录、调试钩子、事件回调 |
| 2D 轨迹图 | `visualization/system/optic_viewer.py` | volume overlay + trajectory artist |
| 3D 交互图 | `visualization/system/optic_viewer_3d.py` | volume slice / iso-surface / ray tube |
| PyTorch 可微优化 | `ml/wrappers.py` | gradient benchmark 与实验包装层 |
| 对外文档 | `docs/gallery/differentiable_ray_tracing.rst` | 新增体介质 / 伴随专栏 |
| 中文实验沉淀 | `examples/md/` | 新 casebook 与研究记录 |

---

## 9. 主要技术风险

### 9.1 数值参数化风险

参考配图反复强调参数化问题，这意味着：

- 如果路径参数选得不对，梯度会污染；
- 如果积分状态变量不一致，autograd 与真实物理导数会偏离；
- 如果边界反射/折返处理不平滑，梯度会不稳定。

### 9.2 复数折射率与几何光线假设冲突

你当前已有 GRIN + Drude 的分析文档已经指出：

- cutoff 区域可能进入复数折射率；
- 这会与当前基于实数几何光线的积分器冲突。

因此在总方案中应明确：

- **第一阶段先只做实值、平滑、可导的体介质案例**；
- Drude 等复杂模型作为第二阶段的“问题驱动案例”，而不是一开始就当主路径。

### 9.3 伴随法不宜一开始就深度入侵主干 API

建议先做：

- 实验性模块；
- 研究案例级别接口；
- benchmark 对照；

待接口稳定后，再考虑把伴随法抽象成主干能力。

---

## 10. 我建议的第一步落地任务

如果接下来要真正开始“构建”，最优先建议做下面 4 项：

### Task 1：给 `GRINPropagation` 增加可选轨迹记录

目标：不改变默认行为，但允许 example 中打开 `record_history=True`。  
这是后续所有图像的基础。

### Task 2：做一个 `FieldSliceViewer`

目标：给 `GradientMaterial` 输出：

- `n(x,z)`；
- `dn/dx`；
- `dn/dz`；
- `|∇n|`。

### Task 3：做一个“折射率切片 + 轨迹叠加”示例

建议文件名：

- `examples/examples/grin_field_and_trajectory_panel.py`

输出：

- 一张 2×2 图板；
- 作为整个可视化构建路线的第一个里程碑。

### Task 4：做一个基线 benchmark 脚本

先不用上伴随法，只做：

- finite difference；
- PyTorch autograd；

把统一输入、统一输出、统一计时框架搭起来，后面再把 adjoint 塞进去。

---

## 11. 最终建议：先做“研究演示层”，再做“伴随求导内核”

这项工作的一个常见误区，是一上来就想把 adjoint method 全部实现完。  
但结合当前 Optiland 的成熟度，我更建议倒过来：

1. 先补齐 **体介质可视化 + 轨迹记录 + benchmark 脚手架**；
2. 再做 **autograd 对照实验**；
3. 最后再接 **adjoint / arc-length parameterization**。

原因很简单：

- 没有稳定图像，就很难定位数值问题；
- 没有统一 benchmark，就很难判断新方法是否真的更优；
- 没有研究案例目录，后续成果很难沉淀到 Optiland 平台中。

所以，**第一阶段的成功标准不是“实现了伴随法”，而是“Optiland 已经能系统地展示体介质中的轨迹、场、梯度与误差”。**

---

## 12. 建议后续文档产物

建议把后续工作沉淀成 4 类文档：

1. **实施日志**：每次改动记录现象、参数、图片；
2. **数值问题手册**：记录 NaN、复数泄漏、梯度爆炸等问题；
3. **案例文档**：每个 case 一页，输入/输出/图板固定；
4. **开发者指南**：最终把稳定模块写入 `docs/developers_guide/`。

---

## 13. 一句话版本

> 这次“可视化构建”的最佳路线，不是直接把参考仓库逐文件搬进 Optiland，而是围绕 Optiland 现有的 **GRIN 传播、可微后端、2D/3D 可视化框架**，先建立“体介质场 + 轨迹历史 + 梯度 benchmark + 论文图板生成”的平台能力，再逐步逼近参考论文中的 adjoint 工作流。

