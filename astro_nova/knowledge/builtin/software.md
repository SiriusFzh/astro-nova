# 天文科研软件使用规范 (2025)

## IRAF (Image Reduction and Analysis Facility)
- **管理方:** NOIRLab, 最新版 v2.18.1 (2025)
- **用途:** 光学/红外图像与光谱处理
- **安装:** iraf.noirlab.edu
- **启动命令:** irafcl (新), 旧版 cl 仍可用
- **64位支持:** 原生支持, 速度提升达 20 倍; 支持 Apple Silicon (M1/M2)
- **Python 接口:** PyRAF v2.2.1 (Python 3.8) 已捆绑
- **文档:** noirlab.edu/science/documents
- **趋势:** IRAF 使用量在下降, 新项目推荐 Astropy/Python; 但遗留数据 (Gemini/NOAO) 仍需 IRAF
- **替代品:** DRAGONS (NOIRLab 开发中)

## SAOImageDS9
- **用途:** 天文 FITS 图像查看与分析 (事实标准)
- **最新版:** 8.6+
- **功能:** FITS 图像/数据立方/多扩展显示, WCS 坐标, 3D 渲染, 轮廓叠加
- **脚本控制:** XPA 协议 (命令行控制), SAMP 协议 (跨软件通信)
- **命令行示例:**
  - `ds9 -mecube foo.fits` — 打开多扩展 FITS 作为 3D 数据立方
  - `ds9 image.fits -log -cmap bb -scale limits 0 100`
- **互操作:** 通过 SAMP 与 TOPCAT、Aladin 通信 — 在 TOPCAT 中选择源即可在 DS9 高亮
- **集成:** 与 CIAO 4.18 (Chandra X-ray) 捆绑
- **参考:** ds9.si.edu, cxc.harvard.edu/ciao/ahelp/ds9.html

## TOPCAT (Tool for OPerations on Catalogues And Tables)
- **用途:** 星表/表格数据可视化与分析
- **最新版:** 4.10-5 (2025年9月)
- **启动:** `topcat` 或 `java -jar topcat-full.jar`
- **数据格式:** FITS, VOTable, CSV, Parquet, IPAC, ECSV, HAPI, Feather, GBIN, SQL
- **核心功能:** 表格查看/编辑, 多维度绘图, 空间/非空间交叉匹配, 锥形搜索, TAP 查询
- **重要新特性 (v4.10):** 全局变量 + 滑块交互, asinh/symlog 坐标轴
- **互操作:** SAMP 协议连接 DS9/Aladin
- **大规模数据:** 支持数百万行; 使用 -Xmx 参数增加 JVM 内存
- **手册:** star.bristol.ac.uk/~mbt/topcat/sun253/
- **姊妹工具:** STILTS (命令行版 TOPCAT)

## CASA (Common Astronomy Software Applications)
- **用途:** ALMA 和 VLA 射电干涉数据处理 (标准工具)
- **最新版:** 6.6.6 (2025)
- **安装:** casa.nrao.edu
- **文档:** casaguides.nrao.edu, casadocs.readthedocs.io
- **流水线阶段:**
  1. hifv_importdata — 注册测量集, 自动识别谱线窗口
  2. hifv_hanning — Hanning 平滑 (RFI/脉泽线)
  3. 校准 — 标记, 增益校准, 带通, 流量定标
  4. 成像 — tclean + auto-multithresh 掩模 + 自校准
  5. 分析 — 图像分析, 谱线成像, 羽化 (feathering)
- **新功能 (6.6.6):** 自动掩模 (auto-multithresh), ALMA Cycle 12 流水线处理
- **可视化:** CARTA 为推荐工具 (CASA 旧版 viewer 已弃用)
- **自校准:** Peak/RMS > 3√(N-3)√(t_int/t_sol)
- **ngVLA 支持:** 6.7.0 新增 ngVLA 模拟 (214 × 18m 天线, ~1300km 基线)

## 互操作标准
- **SAMP:** 桌面天文软件间通信标准 (DS9 ↔ TOPCAT ↔ Aladin)
- **FITS:** 天文数据通用格式 (Flexible Image Transport System)
- **VOTable:** IVOA 标准表格格式
- **XPA:** DS9 的控制协议 (命令行/脚本)
- **IVOA 协议:** TAP, Cone Search, SIA, SSA, DataLink

## 现代趋势 (2025)
- IRAF → DRAGONS / Astropy (光学/NIR 数据处理)
- CASA viewer → CARTA (射电数据可视化)
- Python 成为天文数据分析的主流语言 (Astropy 生态)
- SAMP 取代手动文件交换
