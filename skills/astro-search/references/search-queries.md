# astro-search 常用搜索模板

## 按天体/现象搜索

```
"neutron star mergers" AND "gravitational waves"
"black hole accretion" AND "AGN feedback"
"exoplanet atmosphere" AND "transmission spectroscopy"
"galaxy formation" AND "simulation"
"stellar evolution" AND "massive stars"
"solar flares" AND "magnetic reconnection"
"dark matter" AND "halo"
"cosmic microwave background" AND "primordial"
```

## 按方法/技术搜索

```
"radiative transfer" AND "simulation"
"N-body simulation" AND "galaxy"
"Markov chain Monte Carlo" AND "exoplanet"
"machine learning" AND "galaxy classification"
"adaptive optics" AND "exoplanet imaging"
"asteroseismology" AND "stellar interior"
"spectral fitting" AND "AGN"
```

## 按分类搜索

```
cat:astro-ph.HE AND "gamma-ray burst"
cat:astro-ph.IM AND "instrumentation"
cat:astro-ph.EP AND "habitable zone"
cat:astro-ph.CO AND "dark energy"
cat:astro-ph.SR AND "solar dynamo"
cat:astro-ph.GA AND "Milky Way structure"
cat:gr-qc AND "gravitational wave"
```

## 综合搜索

```
"gravitational wave" AND "electromagnetic counterpart" AND cat:astro-ph.HE
"transient" AND "neutron star" AND (cat:astro-ph.HE OR cat:astro-ph.SR)
```

## 用户自定义研究方向模板

用户提供研究方向的自然语言描述，AI 自动提取关键词和分类。
