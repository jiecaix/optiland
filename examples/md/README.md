# Optiland Examples 文档索引

**更新时间**: 2025-03-07

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

| Python文件 | 生成图片 | 文档说明 |
|-----------|---------|---------|
| `grin_reflection_1d_symmetric.py` | `grin_reflection_1d_symmetric.png` | ✅ 详细分析 |
| `grin_reflection_1d_symmetric_fixed.py` | `truly_symmetric_samples.png` | ✅ 详细分析 |
| `wavelength_modes_explanation.py` | `wavelength_distribution_modes.png` | ✅ 基本说明 |

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

---

## 💡 下次会话继续工作

### 需要做的任务

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
│   │   ├── grin_reflection_1d_symmetric.py
│   │   ├── grin_reflection_1d_symmetric_fixed.py
│   │   ├── wavelength_modes_explanation.py
│   │   └── *.png (生成的图片)
│   └── md/
│       ├── README.md (本文件)
│       └── grin_reflection_1d_symmetric_analysis.md
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
```

---

**文档索引结束**

*如需详细信息，请查看 `grin_reflection_1d_symmetric_analysis.md`*
