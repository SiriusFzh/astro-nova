"""从 LLM 知识库导入天文/物理知识到 RAG 向量存储

生成涵盖以下教材核心内容的结构化知识：
  - 基础天文学
  - 天文学新概论
  - 电动力学 (郭硕鸿)
  - 电磁学
  - 天体物理

用法: python scripts/import_knowledge_from_llm.py
"""
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from astro_nova.knowledge.chunker import chunk_document
from astro_nova.knowledge.vector_store import VectorStore, get_store

STORE_NAME = "textbooks"


# ── 知识内容生成 ─────────────────────────────────────────────────────

def knowledge_astrometry() -> str:
    """天体测量学基础"""
    return """# 天体测量学基础

## 天球坐标系
天球是以观测者为中心、半径为无穷大的假想球面。常用的天球坐标系包括：
- 地平坐标系：以观测者所在地平圈为基圈，高度（地平纬度）和方位角为坐标。高度 h 从地平圈向天顶 0°~90°，方位角 A 从北点向东 0°~360°。
- 赤道坐标系：以天赤道为基圈，赤纬 δ 和赤经 α（或时角 H）为坐标。赤纬从天赤道向北正、向南负（-90°~+90°），赤经从春分点向东 0~24h。
- 黄道坐标系：以黄道为基圈，黄纬 β 和黄经 λ 为坐标。黄道是地球公转轨道面在天球上的投影，与天赤道成约 23.5° 的夹角。
- 银道坐标系：以银河系平面为基圈，银纬 b 和银经 l 为坐标，用于研究银河系结构。

## 时间系统
- 恒星时 (Sidereal Time)：以春分点时角为度量，1 恒星日 = 23h56m04s 平太阳时。
- 真太阳时 (Apparent Solar Time)：以太阳视圆面中心时角度量。
- 平太阳时 (Mean Solar Time)：以平太阳（沿天赤道匀速运动的假想太阳）时角度量。
- 协调世界时 (UTC)：基于原子时的国际标准时间系统，与 UT1 差异保持在 ±0.9s。
- 儒略日 (JD)：连续计日系统，起点为公元前 4713 年 1 月 1 日正午。
- 简化儒略日 (MJD) = JD - 2400000.5。

## 岁差与章动
- 岁差 (Precession)：地球自转轴在空间中绕黄道轴缓慢旋进，周期约 26000 年。导致春分点每年西移约 50.3"。
- 章动 (Nutation)：地球自转轴的短周期小幅度摆动，最大振幅约 9.2"，主周期 18.6 年。
- 极移 (Polar Motion)：地球自转轴相对地壳的运动，振幅约 0.3"。
"""


def knowledge_celestial_mechanics() -> str:
    """天体力学基础"""
    return """# 天体力学基础

## 万有引力定律
Newton 万有引力定律：两质点间引力 F = G·m₁·m₂/r²，G = 6.67430(15)×10⁻¹¹ m³·kg⁻¹·s⁻²。

## 开普勒三定律
第一定律（椭圆定律）：行星沿椭圆轨道运动，太阳位于一个焦点。
第二定律（面积定律）：行星与太阳的连线在相等时间内扫过相等面积，即 dA/dt = h/2 = 常数，h 为面积速度。
第三定律（调和定律）：轨道半长轴 a 的立方与周期 T 的平方成正比，即 a³/T² = GM/4π²。

## 二体问题
二体问题可约化为约化质量 μ = m₁m₂/(m₁+m₂) 在中心力场中的运动。轨道方程为 r = p/(1+e·cos f)，其中 p = h²/GM 为半正焦弦（轨道参数），e 为偏心率，f 为真近点角。
轨道根数（六个）：半长轴 a、偏心率 e、轨道倾角 i、升交点黄经 Ω、近星点幅角 ω、过近星点时刻 τ。
能量积分：E = v²/2 - GM/r = -GM/(2a)，E<0 为椭圆轨道，E=0 为抛物线，E>0 为双曲线。

## 限制性三体问题
圆型限制性三体问题 (CRTBP)：两个大质量天体在圆轨道上运动，第三体质量可忽略。存在五个拉格朗日平动点 L1-L5，其中 L1-L3 为共线不稳定点，L4-L5 为三角稳定点（当日星质量比 μ < 0.03852 时）。
希尔月球的希尔半径：r_H ≈ a(1-e)(m/3M)^(1/3)，是卫星稳定轨道的最大范围。

## 摄动理论
二体问题是理想化的。实际天体运动受多种摄动：其他行星引力、非球形引力位、潮汐力、辐射压等。
经典摄动方法：常数变易法（Lagrange 行星方程）、摄动函数展开。
"""


def knowledge_stellar_physics() -> str:
    """恒星物理"""
    return """# 恒星物理基础

## 恒星基本参数
- 光度 L：恒星每秒辐射的总能量，单位 erg/s 或 W。太阳光度 L☉ = 3.828×10²⁶ W。
- 有效温度 Teff：由 Stefan-Boltzmann 定律定义，L = 4πR²σTeff⁴，σ = 5.6704×10⁻⁵ erg·cm⁻²·s⁻¹·K⁻⁴。
- 绝对星等 M：天体在 10 pc 处的视星等。太阳绝对视星等 Mv = 4.83。
- 距离模数：m - M = 5 log(d/pc) - 5。
- 光谱型：O-B-A-F-G-K-M（从热到冷），再细分为光度型 I-V（超巨星→主序星）。
- 哈佛光谱分类依据：谱线强度，尤其氢 Balmer 线。

## 恒星结构方程（球对称假设）
- 流体静力学平衡：dP/dr = -Gm(r)ρ/r²
- 质量连续方程：dm/dr = 4πr²ρ
- 能量产生：dL/dr = 4πr²ρ·ε，ε 为产能率（核反应 + 引力收缩）
- 辐射平衡（辐射区）：dT/dr = -3κρL/(64πσr²T³)，κ 为不透明度
- 对流平衡（对流区）：dT/dr = (1-1/γ)·T/P·dP/dr

## 恒星能源
- pp 链（质子-质子链）：在 T~10⁷ K 时主导，总效果 4p → He-4 + 2e⁺ + 2ν_e + 26.73 MeV。太阳能量 99% 来自 pp 链。
- CNO 循环：需要 C、N、O 作为催化剂，在 T>1.5×10⁷ K 时主导；在大质量星（M>1.5M☉）中贡献主要能量。
- 中微子：pp 链和 CNO 循环产生的中微子几乎不与被物质相互作用，直接逸出恒星，携带着核心物理信息。

## 恒星演化
- 主序星阶段（占恒星寿命 ~90%）：核心氢燃烧，质量越大的星主序寿命越短（t_MS ∝ M/L ∝ M⁻²⁵）。
- 红巨星阶段：核心氢耗尽 → 壳层氢燃烧 → 核心收缩升温 → 外层膨胀 → He 点燃（氦闪，在低质量星中）。
- 渐进巨星分支 (AGB)：壳层 He 和 H 交替燃烧，热脉冲，形成 s-过程元素。
- 行星状星云：AGB 星外层抛射形成，中心白矮星 T~10⁵ K 电离星云。
- 超新星：大质量星（M>8M☉）核心坍缩（II 型）或白矮星吸积达 Chandrasekhar 极限（Ia 型）。
- 致密星：白矮星（电子简并压支撑，Chandrasekhar 极限 1.44M☉）、中子星（中子简并压，Tolman-Oppenheimer-Volkoff 极限 ~2-3M☉）、黑洞。
"""


def knowledge_galactic_astronomy() -> str:
    """银河系与星系天文学"""
    return """# 银河系与星系天文学

## 银河系结构
- 银盘：直径约 30 kpc，厚度约 300 pc（薄盘）~ 1 kpc（厚盘）。包含旋臂、星际介质、年轻恒星。
- 银晕：直径约 100 kpc，包含球状星团、年老恒星、暗物质晕。
- 核球：中心约 2 kpc 的椭球结构，包含年老恒星和气态物质。
- 银心：Sgr A*，一个约 4.3×10⁶ M☉ 的超大质量黑洞。
- 太阳位于银盘距银心约 8.34 kpc 处，本地标准静止 (LSR) 速度约 220 km/s。
- 旋臂结构：人马臂、猎户臂（本地臂）、英仙臂、盾牌-半人马臂等。

## 恒星总体性质
- 初始质量函数 (IMF)：Salpeter 函数 ξ(m) ∝ m⁻².³⁵，Kroupa 分段函数（不同质量范围幂指数不同）。
- 恒星计数：通过星族合成模型分析星系演化。
- 星族：Pop I（富金属、年轻、盘族）、Pop II（贫金属、年老、晕族）、Pop III（第一代恒星，尚未直接观测）。

## 星系分类与演化
- Hubble 序列：E（椭圆）→ S0 → Sa/Sb/Sc（旋涡）→ SBa/SBb/SBc（棒旋），以及 Irr（不规则）。
- 椭圆星系：恒星形成早已停止，以年老恒星为主，颜色偏红，主要由暗物质支配动力学。
- 旋涡星系：仍在形成恒星，颜色偏蓝，包含丰富的星际介质。恒星形成率 (SFR) 与气体面密度相关（Kennicutt-Schmidt 定律：Σ_SFR ∝ Σ_gas^¹.⁴）。
- 星系形成的冷暗物质模型 (ΛCDM)：小结构并合形成大结构。星系形成于暗物质晕中。
- 活动星系核 (AGN)：中心超大质量黑洞吸积物质释放引力能。Seyfert 星系、类星体 (Quasar)、射电星系、Blazar 等类型基于观测角度统一。

## 星系团与大尺度结构
- 星系团：包含数十至数千个星系，总质量 10¹⁴-10¹⁵ M☉。富集群中热气体发出 X 射线。
- 暗物质：通过星系旋转曲线、引力透镜、星系团动力学、CMB 各向异性等多方面证据确认。ΛCDM 模型：宇宙约 68% 暗能量、27% 暗物质、5% 重子物质。
- 大尺度结构：纤维状结构、巨洞 (Void)、长城，在 ~100 Mpc 尺度上趋于均匀。
"""


def knowledge_cosmology() -> str:
    """宇宙学基础"""
    return """# 宇宙学基础

## 宇宙学原理
宇宙在大尺度上是均匀且各向同性的。描述宇宙膨胀的度量是 Robertson-Walker 度量：ds² = -c²dt² + a(t)²·[dr²/(1-kr²) + r²(dθ²+sin²θ dφ²)]，其中 k=+1（闭合）、0（平坦）、-1（开放）。

## 弗里德曼方程
由 Einstein 场方程在 RW 度量下的解：
- (ȧ/a)² = 8πGρ/3 - kc²/a² + Λ/3 (Friedmann 第一方程)
- ä/a = -4πG(ρ+3P/c²)/3 + Λ/3 (Friedmann 第二方程/加速方程)
定义 Hubble 参数 H = ȧ/a，当前值 H₀ ≈ 67.4 km·s⁻¹·Mpc⁻¹ (Planck 2018)。

## 宇宙组分与演化
各组分密度参数 Ω = ρ/ρ_crit，ρ_crit = 3H²/8πG。
- Ω_Λ ≈ 0.689 (暗能量，ΛCDM 模型)
- Ω_m ≈ 0.311 (物质总和，其中 Ω_b ≈ 0.049 重子物质，Ω_c ≈ 0.262 冷暗物质)
- Ω_r ~ 10⁻⁴ (辐射)
- Ω_k = 1 - Ω_total（曲率参数，观测支持 Ω_k ≈ 0 即平坦宇宙）

宇宙热历史：
- Planck 纪元 (t<10⁻⁴³s)：量子引力效应主导。
- 暴胀 (Inflation, t~10⁻³⁵s)：指数膨胀 10²⁶ 倍以上，解决视界问题、平坦性问题和磁单极问题。
- 核合成 (BBN, t~1s-3min)：质子和中子结合成 D、He-4、Li-7。预测的轻元素丰度与观测高度一致。
- 复合时期/最后散射面 (t~380000yr)：温度降至约 3000K，电子与质子结合形成中性氢，光子退耦。产生宇宙微波背景辐射 (CMB)，温度 T₀ = 2.725K。
- 黑暗时代 → 再电离 (t~4亿年)：第一批恒星和星系形成，电离中性氢。
- 今天的加速膨胀 (t~138亿年，z<0.7)：暗能量主导。

## 标准宇宙学模型 (ΛCDM)
六个基本参数：Ω_bh²、Ω_ch²、H₀、τ（光深）、A_s（原初功率谱振幅）、n_s（谱指数）。
宇宙微波背景各向异性测量（Planck、WMAP）为参数提供了精确约束。

## 距离定义
- 共动距离：χ = c∫(dt/a) = c∫(dz/H(z))
- 光度距离：d_L = (1+z)·χ（平坦宇宙），用于超新星 Ia 测距。
- 角直径距离：d_A = χ/(1+z)
"""


def knowledge_electromagnetism() -> str:
    """电磁学基础"""
    return """# 电磁学基础

## 静电场
- Coulomb 定律：F = (1/4πε₀)·q₁q₂/r²，ε₀ = 8.854187817×10⁻¹² F/m。
- 电场强度 E = F/q₀，点电荷电场 E = q/(4πε₀r²)·ê_r。
- 高斯定理：∮ E·dS = q/ε₀，微分形式 ∇·E = ρ/ε₀。
- 电势：V = ∫ E·dl（电位差），点电荷电势 V = q/(4πε₀r)。
- 泊松方程和拉普拉斯方程：∇²V = -ρ/ε₀，∇²V = 0（无电荷区）。
- 电偶极子：偶极矩 p = q·d，电势 V = p·r/(4πε₀r³)，电场 E = (1/4πε₀)[3(p·r̂)r̂-p]/r³。
- 导体：内部电场为零，电荷分布在表面；静电屏蔽。
- 电容：C = Q/V，平行板电容 C = ε₀S/d。
- 静电能：W = (1/2)∫ρV dV = (ε₀/2)∫E² dV（电场能量密度 u_E = ε₀E²/2）。

## 静磁场
- Biot-Savart 定律：dB = (μ₀/4π)·Idl×r̂/r²，μ₀ = 4π×10⁻⁷ N/A²。
- 安培环路定理：∮ B·dl = μ₀I，微分形式 ∇×B = μ₀J。
- 磁通量：Φ = ∫ B·dS。
- 磁矢势：B = ∇×A，规范变换 A→A+∇ψ。
- 磁偶极子：磁矩 m = I·S·n̂，磁场 B = (μ₀/4π)[3(m·r̂)r̂-m]/r³。
- 磁介质：磁化强度 M，H = B/μ₀-M，B = μH = μ₀μ_rH。
- 磁场能量密度：u_B = B²/2μ₀。

## 电磁感应
- Faraday 感应定律：ε = -dΦ/dt，微分形式 ∇×E = -∂B/∂t。
- 楞次定律：感应电流方向阻碍磁通量变化。
- 自感：L = Φ/I，自感电动势 ε_L = -L·dI/dt。
- 互感：M，ε₁ = -M·dI₂/dt。
- 磁场能量：W_m = (1/2)LI² = ∫(B²/2μ)dV。
- RLC 电路：振荡频率 ω = 1/√(LC)，阻尼特征。

## 麦克斯韦方程组
微分形式：
(1) ∇·D = ρ_f （高斯定理，电场）
(2) ∇·B = 0 （无磁单极）
(3) ∇×E = -∂B/∂t （Faraday 定律）
(4) ∇×H = J_f + ∂D/∂t （安培环路定理 + 位移电流）

积分形式：
(1) ∮ D·dS = ∫ρ_f dV
(2) ∮ B·dS = 0
(3) ∮ E·dl = -∫(∂B/∂t)·dS
(4) ∮ H·dl = ∫(J_f + ∂D/∂t)·dS

本构关系：D = εE（线性介质），B = μH，J = σE。
位移电流 ∂D/∂t 保证了电荷守恒，是电磁波存在的关键。

## 电磁波
- 波动方程：∇²E = με·∂²E/∂t²，∇²B = με·∂²B/∂t²。
- 波速 v = 1/√(με)，真空中光速 c = 1/√(μ₀ε₀)。
- 平面电磁波：E = E₀cos(k·r-ωt)，B = (k×E)/ω，E⊥B⊥k。
- Poynting 矢量：S = E×H，能量流密度。
- 能流密度平均：⟨S⟩ = (1/2)Re(E×H*)，⟨S⟩ = (1/2)ε₀cE₀²（真空）。
- 电磁波谱：无线电波 (>1mm)、微波 (1mm-0.1mm)、红外 (0.1mm-0.7μm)、可见光 (400-700nm)、紫外 (10-400nm)、X 射线 (0.01-10nm)、γ 射线 (<0.01nm)。
"""


def knowledge_electrodynamics() -> str:
    """电动力学 (郭硕鸿)"""
    return """# 电动力学（郭硕鸿）

## 第一章：电磁现象的普遍规律
- 电荷守恒定律：∇·J + ∂ρ/∂t = 0。
- Maxwell 方程组作为电磁场的基本方程，真空中光速 c = 299792458 m/s。
- 介质中的 Maxwell 方程组：引入极化 P 和磁化 M，通过 D = ε₀E+P、H = B/μ₀-M 简化。
- 电磁场边值关系：(D₂-D₁)·n = σ_f，(B₂-B₁)·n = 0，n×(E₂-E₁)=0，n×(H₂-H₁)=α_f。
- 静电场是有源无旋场（∇·E = ρ/ε₀，∇×E=0），静磁场是无源有旋场（∇·B=0，∇×B=μ₀J）。
- 电磁场能量守恒：∂u/∂t + ∇·S = -J·E，其中 u = (E·D+B·H)/2 为场能密度，S = E×H 为能流密度。
- 电磁场动量密度：g = D×B = S/c²（真空中）。

## 第二章：静电场
- 泊松方程 ∇²φ = -ρ/ε₀，拉普拉斯方程 ∇²φ=0（无电荷区）。
- 唯一性定理：给定边界条件，静电场解唯一。
- 镜像法：用虚设电荷代替边界感应电荷。点电荷在接地导体球前：q' = -qa/d，球心距 b = a²/d。
- 分离变量法：球坐标下解 (r,θ,φ) = Σ(A_l r^l + B_l r^{-l-1})P_l_m(cosθ)e^{imφ}。
- 电多极矩展开：φ(x) = (1/4πε₀)[Q/r + p·x/r³ + (1/2)ΣQ_ij x_i x_j/r⁵ + ...]。
  电荷 Q = ∫ρdV，电偶极矩 p = ∫xρdV，电四极矩 Q_ij = ∫(3x_i x_j - r²δ_ij)ρdV。

## 第三章：静磁场
- 矢势 A 满足 ∇²A = -μ₀J（Coulomb 规范 ∇·A=0）。
- 磁偶极矩 m = (1/2)∫x'×J(x')dV'，矢势 A(x) = μ₀m×x/(4πr³)。
- 磁标势：无电流区 ∇×H=0，可引入磁标势 φ_m，H = -∇φ_m。
- 磁多极矩展开类似电多极矩。

## 第四章：电磁波的传播
- 定态波动方程（Helmholtz 方程）：∇²E + k²E=0，k=ω√(με)。
- 平面电磁波在介质界面的反射和折射：Fresnel 公式，Brewster 角、全反射。
- 波导：矩形波导截止频率 ω_c = π√((m/a)²+(n/b)²)/√(με)。TE_mn 和 TM_mn 模。
- 谐振腔：谐振频率 ω_mnp = πc√((m/L₁)²+(n/L₂)²+(p/L₃)²)。
- 电磁波在等离子体中的传播：ω² = ω_p² + c²k²，等离子体频率 ω_p = √(n_e e²/ε₀ m_e)。

## 第五章：电磁波的辐射
- 达朗贝尔方程（Lorenz 规范 ∇·A + με∂φ/∂t=0）：□A = -μ₀J，□φ = -ρ/ε₀。□ = ∇²-με∂²/∂t² 为波动算符。
- 推迟势：A(x,t) = (μ₀/4π)∫J(x',t-|x-x'|/c)/|x-x'| dV'，φ 类似。
- 电偶极辐射：E = (μ₀/4π)(p̈×n)×n/(c²r)，B = (μ₀/4π)p̈×n/(cr)。
  辐射功率 P = μ₀p̈²/(6πc)（Larmor 公式）。
- 电四极辐射和磁偶极辐射较电偶极辐射弱 (v/c)² 量级。

## 第六章：狭义相对论
- 相对论基本原理：相对性原理（物理定律在一切惯性系中形式相同）+ 光速不变原理。
- Lorentz 变换：x' = γ(x-vt)，t' = γ(t-vx/c²)，γ = 1/√(1-v²/c²)。
- 闵可夫斯基四维时空：间隔 ds² = c²dt²-dx²-dy²-dz²。
- 四维矢量：x^μ = (ct, x, y, z)，四维速度 U^μ = dx^μ/dτ，四维动量 p^μ = m₀U^μ = (E/c, p)。
- 质能关系：E = mc² = m₀c²/√(1-v²/c²)，静能 E₀ = m₀c²，动能 T = (γ-1)m₀c²。
- 电磁场张量 F^μν，Maxwell 方程可写为协变形式 ∂_μ F^μν = μ₀J^ν 和 ∂_μ F̃^μν = 0。
- 相对论力学：d²x^μ/dτ² = (q/m₀)F^μ_ν dx^ν/dτ（带电粒子在电磁场中运动）。
"""


def knowledge_observational_astronomy() -> str:
    """天文观测方法"""
    return """# 天文观测方法

## 光学望远镜
- 折射望远镜：使用透镜组聚集光线。优点是对准稳定性好；缺点有色差、大物镜制造困难。
- 反射望远镜：使用主镜（抛物面/球面）聚集光线。无球差（抛物面）、无 chromatic aberration、造价较低。
  - Newton 式：平面副镜反射到镜筒侧。
  - Cassegrain 式：双曲面副镜，光束通过主镜中心孔，等效焦距长。
  - Ritchey-Chrétien 式：双曲面主镜+双曲面副镜，消除球差和彗差，现代大型望远镜标准设计。
- 折反射望远镜（Schmidt、Maksutov）：加入改正板消除球差，视场大。
- 现代大型望远镜：Keck (10m, 分段镜面)、VLT (8.2m×4)、Subaru (8.2m)、Gemini (8.1m×2)、Hobby-Eberly (9.2m)、LBT (8.4m×2)。
- 极大望远镜 (ELT)：即将建成的 E-ELT (39.3m)、TMT (30m)、GMT (24.5m)。

## 射电天文
- 射电望远镜：抛物面天线接收天体射电辐射。噪声温度是灵敏度关键指标。
- 干涉测量：多天线组合实现高角分辨率。VLA（27 天线，角分辨率 0.04"）、ALMA（66 天线，亚毫米波段，分辨率 0.005"）、VLBI（洲际基线，分辨率 < 1mas）。
- 综合孔径技术：Ryle 发明，通过 Earth 旋转改变基线投影实现 uv 平面覆盖。

## 高能天体物理观测
- X 射线望远镜：掠入射反射镜聚焦。Chandra（0.2" 分辨率）、XMM-Newton、eROSITA、NICER。
- γ 射线望远镜：Fermi/LAT (20MeV-300GeV)、Cherenkov 望远镜 (HESS、MAGIC、LHAASO、CTA)。
- 空间天文台：Hubble (光学/紫外)、JWST (红外，6.5m 分段镜)、TESS（系外行星巡天）、Gaia（天体测量，20 亿颗星，精度 24μas）。

## 探测器
- CCD（电荷耦合器件）：量子效率高（>90%）、线性响应好、宽动态范围。
- CMOS：现代天文常用，读出速度快，多用于巡天项目（如 LSST 的 3.2 亿像素相机）。
- 像元尺寸与视场：口径 D 的望远镜衍射极限分辨角 θ = 1.22λ/D，CCD 像元大小应匹配采样定理（每个分辨元至少 2 像素）。

## 光谱观测
- 棱镜光谱仪：色散率小，现已少用。
- 光栅光谱仪：刻线光栅或全息光栅。角色散 dθ/dλ = m/(d·cosθ)，m 为级次，d 为刻线间距。
- 阶梯光栅 (Echelle)：高色散（R = λ/Δλ 可达 10⁵），与交叉色散结合一次曝光覆盖宽波段。
- 纤维光谱：多目标同时观测（如 LAMOST 4000 光纤、SDSS 1000 光纤）。
- 积分场单元 (IFU)：获得目标二维空间每点的光谱。

## 测光系统
- Johnson-Morgan UBV 系统：U (365nm)、B (445nm)、V (551nm)。
- 扩展：RI 红外 (Kron-Cousins R,I)、近红外 JHK (1.2/1.6/2.2μm)。
- SDSS 五波段 ugriz (354/477/623/763/913nm)。
- 大气消光矫正：m = m₀ + k·X，X 为大气质量，k 为消光系数。
"""


def knowledge_solar_system() -> str:
    """太阳系天体"""
    return """# 太阳系

## 太阳
- 光谱型 G2V，质量 1.989×10³⁰ kg，半径 6.957×10⁵ km，光度 3.828×10²⁶ W。
- 有效表面温度 5778 K，中心温度 ~1.57×10⁷ K，密度 ~150 g/cm³。
- 太阳结构：核心（核反应区）、辐射层（不透明度主导）、对流层（太阳表面的对流运动）、光球（有效温度面 500nm 连续谱）、色球（温度 10⁴-10⁵K）、过渡区、日冕（~10⁶K 高温等离子体）。
- 太阳活动：11 年活动周期（太阳黑子数 Schwabe 周期），22 年磁周期（Hale 定律）。
- 太阳风：从日冕向行星际空间连续流出的等离子体流，速度约 300-800 km/s。
- 耀斑：太阳大气中的剧烈爆发，释放能量 ~10³² erg。

## 行星
- 类地行星（水星、金星、地球、火星）：较小、高密度、固态表面、金属核。
- 类木行星（木星、土星、天王星、海王星）：大气厚重、液态或气态主体、环系统、多卫星、低密度。
- 矮行星：冥王星、阋神星、鸟神星、妊神星、谷神星（IAU 2006 年定义）。
- 小行星带：位于火星木星之间，总质量约月球的 4%。
- Kuiper 带：海王星轨道外的冰质小天体带（30-50 AU），冥王星是其一部分。
- Oort 云：包围太阳系的球形彗星云，距太阳约 20000-200000 AU，长周期彗星起源。

## 系外行星
- 发现方法：径向速度法（恒星 wobble，首次 1995 年 51 Peg b）、凌星法（Kepler 任务已发现数千颗，光度下降 ΔF/F = (R_p/R_*)²）、直接成像（HR 8799 四颗行星）、微引力透镜、天体测量。
- 热木星 (Hot Jupiter)：质量接近木星但轨道周期仅数天，受恒星辐照极强。
- 宜居带 (Habitable Zone)：行星表面温度允许液态水存在的轨道范围。取决于恒星光度。
- 行星大气表征：凌星透射光谱（JWST 观测系外行星大气成分 H₂O、CO₂、CH₄ 等）。
"""


def knowledge_astronomical_tools() -> str:
    """天文常用工具和数据处理"""
    return """# 天文数据处理与常用工具

## 主流的 Python 天文学包
- Astropy：核心天文库，提供坐标变换（astropy.coordinates）、时间处理（Time）、FITS 文件操作（astropy.io.fits）、单位系统（astropy.units）、物理常数（astropy.constants）、宇宙学计算（astropy.cosmology）、模型拟合（astropy.modeling）、表格操作（astropy.table）。
- Sunpy：太阳物理数据分析专用。
- Photutils：测光工具（源检测、孔径测光、PSF 测光）。
- Specutils：光谱分析工具。
- Astroquery：查询天文数据库（SIMBAD、VizieR、ADS、NED、MAST、IRSA 等）。

## IRAF 和 PyRAF
IRAF（Image Reduction and Analysis Facility）曾是天文数据处理的行业标准，现已被 Python 生态取代。

## SExtractor
源提取工具（Source Extractor），从天文图像检测和测量天体，提供星等、半光半径、椭率等参数。

## CASA
用于射电/毫米波干涉数据处理（ALMA、VLA 的官方处理软件）。

## 天文坐标变换常用公式
- 地平坐标→时角坐标：sin δ = sin φ sin h + cos φ cos h cos A，cos δ sin H = -cos h sin A
- 时角→赤经：α = T_s - H（T_s 为恒星时）
- J2000.0 到当前历元：考虑岁差矩阵旋转 (P 矩阵)
- FK4 到 FK5（B1950.0 → J2000.0）：处理系统差

## FITS 文件标准
- Flexible Image Transport System：天文数据标准格式。
- 头 (Header) 含天空坐标 WCS（World Coordinate System）、观测元数据。
- 数据可包含多维数组（影像、光谱立方体、事件列表）。
- BZERO/BSCALE 参数用于数据压缩（整数存储，浮点还原 data = BSCALE·FITS_data + BZERO）。

## 常见数据处理步骤
- 偏压 (Bias)：零秒曝光读取噪声，减法矫正。
- 暗流 (Dark current)：长时间曝光的暗像，减法消除。
- 平场 (Flat-field)：响应不均性，除法矫正。
- 宇宙射线去除：多帧组合或 LACosmic 算法。
- 天体测量定标：匹配已知星表（Gaia、UCAC4），求解 WCS。
- 测光定标：观测标准星，求解零点 ZP，m = -2.5 log(counts) + ZP。
- 光谱定标：通过已知谱线（HeNeAr 灯）建立像素-波长关系。
"""


def knowledge_stellar_atmospheres() -> str:
    """恒星大气与谱线形成"""
    return """# 恒星大气与谱线形成

## 辐射转移
- 辐射转移方程：dI_ν/dτ_ν = S_ν - I_ν，其中 τ_ν 为光深，S_ν = j_ν/α_ν 为源函数。
- 局部热动平衡 (LTE)：S_ν = B_ν(T)（Planck 函数），恒星大气中常用的近似。
- Eddington-Barbier 近似：I_ν(μ=0) ≈ S_ν(τ_ν=μ)，边缘处的出射辐射强度近似等于光深 τ=μ 处的源函数。
- 连续谱形成：主要来自 H⁻ 吸收（太阳型恒星）、束缚-自由跃迁和自由-自由跃迁（H、He、金属）。

## 谱线形成机理
- 原子能级：量子数 n（主量子数）、l（角动量）、s（自旋）、j（总角动量 = l+s）。精细结构（自旋-轨道耦合），超精细结构（核自旋）。
- 谱线轮廓：自然展宽（Lorentz，寿命不确定）、热运动展宽（Doppler，Gaussian，Δλ_D/λ = v_th/c）、压力展宽（van der Waals、Stark）、压致展宽（Holtsmark）。
- Voigt 轮廓：Gaussian（Doppler）和 Lorentz（自然+压力）的卷积。线心由 Doppler 展宽主导，线翼由压力展宽主导。
- Boltzmann 公式：N_u/N_l = (g_u/g_l)exp(-ΔE/kT)，激发态和基态的粒子数比。
- Saha 电离方程：N_{i+1}/N_i = (2Z_{i+1}/n_e Z_i)(2πm_e kT/h²)^{3/2} exp(-χ_i/kT)，电离度取决于温度和电子密度。
- 电离-激发综合：通过 Boltzmann + Saha + 化学丰度计算各能级布居，决定谱线强度。

## MK 光谱分类物理基础
O 型：He II 吸收线（电离氦），H 线弱。T_eff > 30000K。
B 型：He I 中性氦线最强，H 线增强。T_eff 10000-30000K。
A 型：H 线 (Balmer) 最强，Ca II H&K 出现。T_eff 7500-10000K。
F 型：Ca II H&K 强，金属线开始明显。T_eff 6000-7500K。
G 型：Ca II H&K 很强，Fe I 等金属线丰富。T_eff 5200-6000K（太阳）。
K 型：分子带 (TiO) 出现，金属线主导。T_eff 3900-5200K。
M 型：TiO 分子带极强，连续谱变红。T_eff < 3900K。

## 恒星化学丰度测定
- 等效宽度 W_λ = ∫(1-F_λ/F_c)dλ，测量谱线总吸收量。
- 生长曲线 (Curve of Growth)：log(W_λ/λ) 与 log(N_f_λ) 的关系。分为线性区（W ∝ N）、平坦区（Doppler core 饱和）、阻尼区（W ∝ √N）。
- 丰度符号：A(Fe)=log(N_Fe/N_H)+12，[Fe/H]=log(N_Fe/N_H)-log(N_Fe/N_H)_☉。
"""
# 汇总所有知识模块
KNOWLEDGE_MODULES = [
    ("基础天文学_天体测量学", knowledge_astrometry),
    ("基础天文学_天体力学", knowledge_celestial_mechanics),
    ("基础天文学_恒星物理", knowledge_stellar_physics),
    ("天文学新概论_星系宇宙学", knowledge_galactic_astronomy),
    ("天文学新概论_宇宙学", knowledge_cosmology),
    ("天文学新概论_太阳系", knowledge_solar_system),
    ("天文学新概论_实测天体物理", knowledge_observational_astronomy),
    ("天文学新概论_数据处理", knowledge_astronomical_tools),
    ("电磁学", knowledge_electromagnetism),
    ("电动力学_郭硕鸿", knowledge_electrodynamics),
    ("恒星大气", knowledge_stellar_atmospheres),
]


def import_module(book_name: str, content_fn) -> int:
    """生成并导入一个知识模块"""
    text = content_fn()
    if not text.strip():
        return 0

    # 按章节分割再分块
    chunks = chunk_document(text, doc_id=book_name, metadata={
        "source": book_name,
        "type": "llm_knowledge",
    })

    store = get_store(STORE_NAME)
    chunk_count = 0
    for i, chunk in enumerate(chunks):
        if len(chunk) < 30:
            continue
        doc_id = f"{book_name}_chunk{i:04d}"
        store.add_document(
            content=chunk,
            source=book_name,
            metadata={"source": book_name, "type": "llm_knowledge", "chunk": i},
            doc_id=doc_id,
        )
        chunk_count += 1

    return chunk_count


def main():
    print("=" * 60)
    print("LLM 知识库 → 向量存储导入")
    print("=" * 60)

    # 先清空旧数据
    store = get_store(STORE_NAME)
    old_count = store.count()
    print(f"现有知识库 '{STORE_NAME}': {old_count} 个文档")
    overwrite = input("是否重新导入? (y/N): ").strip().lower()
    if overwrite == "y":
        store.clear()
        print("已清空旧数据")

    total_chunks = 0
    t0 = time.time()

    for book_name, content_fn in KNOWLEDGE_MODULES:
        print(f"\n  生成: {book_name}...", end=" ", flush=True)
        try:
            n = import_module(book_name, content_fn)
            total_chunks += n
            print(f"√ {n} 个文档块")
        except Exception as e:
            print(f"✗ {e}")

    # 同时写入 seed 目录，供打包分发
    seed_dir = os.path.join(os.path.dirname(__file__), "..", "astro_nova", "knowledge", "seed")
    os.makedirs(seed_dir, exist_ok=True)
    src = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       "astro_nova", "knowledge", "data", f"{STORE_NAME}.json")
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(seed_dir, f"{STORE_NAME}.json"))
        print(f"  [seed] 已同步到 seed 目录")

    elapsed = time.time() - t0
    final_count = store.count()
    print(f"\n{'='*60}")
    print(f"完成! 总计 {total_chunks} 个文档块 → '{STORE_NAME}'")
    print(f"知识库现有 {final_count} 个文档")
    print(f"耗时 {elapsed:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
