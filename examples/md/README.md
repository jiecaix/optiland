# Optiland Examples 文档索引

**更新时间**: 2026-03-21

---

## 📁 文档列表

### 1. [GRIN反射 1D对称采样 - 完整分析](./grin_reflection_1d_symmetric_analysis.md)

**主题**: 渐变折射率介质中的光线反射与色散研究

**包含内容**:
- ✅ 项目概述与核心发现
- ✅ 文件说明（3个主要Python脚本）
- ✅ 生成图片的详细分析
  - `grin_reflection_1d_symmetric.png` (349 KB)
  - `truly_symmetric_samples.png` (~250 KB)
  - `wavelength_distribution_modes.png` (239 KB)
- ✅ 物理原理解释（Drude模型）
- ✅ 代码关键部分（对称性保证）
- ✅ 使用指南（参数调整）
- ✅ 技术细节（RK4积分）
- ✅ 常见问题解答
- ✅ 下一步工作建议

**关键发现**:
- ⭐ 转向点展宽: 2.572 mm（色散效应）
- ⭐ 完美对称性: 相关系数 = 1.000000
- ⭐ 100%反射率: 20/20光线全部反射

**适用场景**:
- 等离子体镜研究
- GRIN光学设计
- 色散效应教学
- 超快光学模拟

---

### 2. [GRIN + Drude 模型问题复核](./grin_drude_reasonableness_review.md)

**主题**: 当前实现的物理一致性和数值稳定性评估

**核心结论**:
- ⚠️ 思路合理，但实现有2个关键问题
- 🔴 **P0**: 梯度公式多了一个 λp⁻² 因子（量纲错误）
- 🟡 **P1**: 倏逝区返回复数折射率，与实数积分器耦合不干净

**建议**:
- 修正后可用于定量研究
- 当前仅适用于定性演示

---

### 3. [GRIN + Drude 证据验证报告](./grin_drude_evidence_analysis.md)

**主题**: 运行验证脚本 `grin_drude_evidence.py` 的详细分析

**验证结果**:

#### Check A: 梯度公式错误 ✅ 证实

| z (mm) | λp(z) | 1/λp²(z) | buggy/correct (实测) | 状态 |
|--------|-------|----------|---------------------|------|
| 0.0    | 0.800 | 1.5625   | 1.562              | ✅ 匹配 |
| 1.0    | 0.750 | 1.7778   | 1.778              | ✅ 匹配 |
| 2.0    | 0.700 | 2.0408   | 2.041              | ✅ 匹配 |
| 3.0    | 0.650 | 2.3669   | 2.367              | ✅ 匹配 |

**数学推导**:
```
错误公式: dn/dz ∝ 1/λp⁵  (多了 λp⁻²)
正确公式: dn/dz ∝ 1/λp³
比值: 错误/正确 = 1/λp²  ← 数据精确验证！
```

#### Check B: 复数泄漏 ✅ 证实

```
z = 3.5 mm: ratio² = 0.953 < 1  → n = 0.218 (实数)  ✓
z = 4.0 mm: ratio² = 1.034 > 1  → n = -1+0j (复数)  ⚠️
                            → dN/ds = 0j (复数)     ⚠️
```

**问题**: 复数折射率泄漏到光线方向导数，破坏几何光学的实数假设

**验证脚本**: `python grin_drude_evidence.py`
**可视化**: `python grin_drude_evidence_visual.py`

**生成图片**:
1. `grin_drude_checkA_gradient_error.png` (583 KB)
   - 6个子图展示梯度公式错误的完整证据
   - 关键：buggy/correct = 1/λp²(z) 柱状图
2. `grin_drude_checkB_complex_leakage.png` (334 KB)
   - 6个子图展示复数折射率泄漏问题
   - 关键：复数n → 复数dN/ds 泄漏路径

**主题**: 渐变折射率介质中的光线反射与色散研究

**包含内容**:
- ✅ 项目概述与核心发现
- ✅ 文件说明（3个主要Python脚本）
- ✅ 生成图片的详细分析
  - `grin_reflection_1d_symmetric.png` (349 KB)
  - `truly_symmetric_samples.png` (~250 KB)
  - `wavelength_distribution_modes.png` (239 KB)
- ✅ 物理原理解释（Drude模型）
- ✅ 代码关键部分（对称性保证）
- ✅ 使用指南（参数调整）
- ✅ 技术细节（RK4积分）
- ✅ 常见问题解答
- ✅ 下一步工作建议

**关键发现**:
- ⭐ 转向点展宽: 2.572 mm（色散效应）
- ⭐ 完美对称性: 相关系数 = 1.000000
- ⭐ 100%反射率: 20/20光线全部反射

**适用场景**:
- 等离子体镜研究
- GRIN光学设计
- 色散效应教学
- 超快光学模拟

---


### 4. [Adjoint Nonlinear Ray Tracing 可视化构建总方案](./adjoint_nonlinear_ray_tracing_visualization_master_plan.md)

**主题**: 基于参考论文配图与 `ArjunTeh/AdjointNonlinearRayTracing` 仓库，为 Optiland 规划体介质、轨迹、梯度与优化过程的可视化建设路线。

**包含内容**:
- ✅ 当前 Optiland 与参考工作的能力映射
- ✅ 体介质场可视化 / 轨迹记录 / benchmark 的模块建议
- ✅ P0 / P1 / P2 图像优先级与实施阶段划分
- ✅ 伴随法、autograd、finite difference 的对照落地建议
- ✅ 下一步最值得先做的 4 个具体任务

**适用场景**:
- 体介质可视化规划
- GRIN / Drude 研究型实验整理
- 可微光线追迹路线设计
- 伴随优化工作流落地

---

## 🚀 快速开始

### 第一步: 了解项目

1. 阅读 `grin_reflection_1d_symmetric_analysis.md`
2. 查看生成的图片
3. 理解物理原理

### 第二步: 运行代码

```bash
cd /home/hxt/optiland/examples/examples

# 主模拟
python grin_reflection_1d_symmetric.py

# 对称性验证
python grin_reflection_1d_symmetric_fixed.py --visualize-only

# 波长分布模式
python wavelength_modes_explanation.py
```

### 第三步: 修改参数

参考文档中的"参数调整"部分，自定义你的模拟。

---

## 📊 主要文件对照表

| Python文件 | 生成图片 | 文档说明 | 验证状态 |
|-----------|---------|---------|----------|
| `grin_reflection_1d_symmetric.py` | `grin_reflection_1d_symmetric.png` | ✅ 详细分析 | ⚠️ 有bug |
| `grin_reflection_1d_symmetric_fixed.py` | `truly_symmetric_samples.png` | ✅ 详细分析 | ✓ 正常 |
| `wavelength_modes_explanation.py` | `wavelength_distribution_modes.png` | ✅ 基本说明 | ✓ 正常 |
| `grin_drude_evidence.py` | (控制台输出) | ✅ 证据验证 | ✓ 验证通过 |
| `grin_drude_evidence_visual.py` | 2张可视化图片 | ✅ 证据验证 | ✓ 验证通过 |

**验证脚本说明**:

1. **文本验证** (`grin_drude_evidence.py`):
   - 轻量级、无外部依赖
   - 运行时间 < 1秒
   - 输出清晰的数值证据

2. **可视化验证** (`grin_drude_evidence_visual.py`):
   - 生成2张PNG图片（共917 KB）
   - 每张图包含6个子图，从多角度验证
   - 需要numpy和matplotlib
   - 运行命令（需先加载模块）:
     ```bash
     module load miniconda3/3.13
     python grin_drude_evidence_visual.py
     ```

---

## 🔍 关键概念

### 1. 对称性保证

```python
# 正确方法: 镜像波长
positive_wavelengths = np.random.normal(0, 1, half_samples)
wavelengths = np.concatenate([
    positive_wavelengths[::-1],  # 负侧
    positive_wavelengths         # 正侧
])
```

**结果**: 相关系数 = 1.0（完美对称）

### 2. Drude色散模型

```python
n(λ, z) = √(1 - λ²/λp²(z))

其中:
  λ = 光波长
  λp(z) = λp₀ + λp₁·z = 0.8 - 0.05·z
```

**效果**: 不同波长有不同穿透深度

### 3. 转向点展宽

```
短波长（蓝光）: z_turn ≈ 3.1 mm
长波长（红光）: z_turn ≈ 5.6 mm
展宽: Δz = 2.57 mm
```

**意义**: 色散效应的量化指标

### ⚠️ 4. 已知问题（待修正）

#### 问题1: 梯度公式量纲错误

```python
# 当前实现 (错误)
dn/dz ∝ 1/λp⁵

# 正确公式
dn/dz ∝ 1/λp³

# 误差因子
错误/正确 = 1/λp²(z)
```

**验证**: 运行 `python grin_drude_evidence.py`
**证据**: `buggy/correct` 列精确等于 `1/λp²(z)`

#### 问题2: 倏逝区复数泄漏

```python
# 当前实现
if ratio² >= 1:
    return -1+0j  # 复数折射率

# 问题: dN/ds = (1/n) * ... → 复数导数
# 泄漏到光线传播方程，破坏实数假设
```

**验证**: z ≥ 4.0 mm 时 `dN/ds = 0j`
**影响**: 数值稳定性问题，物理概念混乱

---

## 💡 下次会话继续工作

### 🔴 P0 - 必须修正（Bug修复）

- [ ] **修正梯度公式** (最重要)
  - 当前: `dn/dz ∝ 1/λp⁵` (错误)
  - 应为: `dn/dz ∝ 1/λp³` (正确)
  - 影响: 所有波长和位置都系统性偏差
  - 参考: `grin_drude_evidence_analysis.md` Check A

- [ ] **修正倏逝区处理**
  - 当前: 返回复数 `n = -1+0j`
  - 应为: 返回实数下限或显式触发反射
  - 影响: 复数泄漏到光线传播方程
  - 参考: `grin_drude_evidence_analysis.md` Check B

### 🟡 P1 - 强烈建议（代码改进）

- [ ] 增加一致性检查
  - λp₁ = 0 时梯度应为零
  - 解析 vs 数值梯度误差 < 1e-4

- [ ] 重新运行修正后的模拟
  - 对比修正前后的转向点位置
  - 验证色散效应是否更明显
  - 更新文档中的数值结果

### 🟢 P2 - 功能扩展（新功能）

- [ ] 扩展到2D/3D GRIN介质
- [ ] 实现其他色散模型（Sellmeier, Cauchy）
- [ ] 增加更多光线（100+）进行统计分析
- [ ] 参数扫描（入射角、波长范围）
- [ ] 时域分析（超短脉冲）

### 代码改进方向

- [ ] 自适应步长RK4
- [ ] 并行计算加速
- [ ] GPU加速
- [ ] 交互式可视化

### 数据分析

- [ ] 转向点分布直方图
- [ ] 色散参数拟合
- [ ] 理论vs数值对比

---

## 📝 备注

### 环境信息

- Python 3.9+
- numpy, scipy, matplotlib
- optiland (本地版本)

### 文件位置

```
/home/hxt/optiland/
├── examples/
│   ├── examples/
│   │   ├── grin_reflection_1d_symmetric.py (主模拟，有bug)
│   │   ├── grin_reflection_1d_symmetric_fixed.py (对称性验证)
│   │   ├── wavelength_modes_explanation.py (波长模式说明)
│   │   ├── grin_drude_evidence.py (证据验证-文本版)
│   │   ├── grin_drude_evidence_visual.py (证据验证-可视化版)
│   │   ├── grin_drude_checkA_gradient_error.png (583 KB) ⭐
│   │   ├── grin_drude_checkB_complex_leakage.png (334 KB) ⭐
│   │   └── *.png (其他生成的图片)
│   └── md/
│       ├── README.md (本文件)
│       ├── grin_reflection_1d_symmetric_analysis.md (项目分析)
│       ├── grin_drude_reasonableness_review.md (问题复核)
│       └── grin_drude_evidence_analysis.md (证据验证，含可视化解读)
```

### 重要提示

1. **对称性是关键**: 确保对称位置有相同波长
2. **标准正态分布**: 使用z分数（均值=0）概念更清晰
3. **Drude模型参数**: λp₀=0.8, λp₁=-0.05 适合演示
4. **转向点展宽**: 2.57 mm是色散的核心证据

---

## 🎯 快速参考

### 常用命令

```bash
# 查看所有Python文件
ls -la /home/hxt/optiland/examples/examples/*.py

# 查看所有生成的图片
ls -la /home/hxt/optiland/examples/examples/*.png

# 阅读完整文档
cat /home/hxt/optiland/examples/md/grin_reflection_1d_symmetric_analysis.md
```

### 关键数字

```
- 光线数量: 20
- 波长范围: 0.438 - 0.608 µm
- 空间范围: -3.0 到 +3.0 mm
- 平均转向点: 4.392 mm
- 转向点展宽: 2.572 mm ⭐
- 反射率: 100%
- 对称性: 相关系数 1.000000
- 梯度误差: 1/λp² (已验证)
```

### 快速修正参考

#### 修正1: 梯度公式

```python
# 在 DispersiveGradientMaterial._calculate_n() 中

# 当前 (错误)
ratio_sq = (wavelength / lambda_p) ** 2
dn_dz = factor * lambda_p1 * ratio_sq / (lambda_p**3 * sqrt(1-ratio_sq))

# 应改为 (正确)
dn_dz = factor * lambda_p1 * (wavelength**2) / (lambda_p**3 * sqrt(1-ratio_sq))
```

#### 修正2: 倏逝区处理

```python
# 在 ratio_squared >= 1 时

# 当前 (返回复数)
return -1.0 + 0j

# 应改为 (返回实数下限)
n_floor = 0.001  # 或其他小正数
return n_floor
# 同时在积分器中触发显式反射逻辑
```

---

**文档索引结束**

*如需详细信息，请查看 `grin_reflection_1d_symmetric_analysis.md`*
