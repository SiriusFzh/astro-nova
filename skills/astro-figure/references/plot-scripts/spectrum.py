"""
astro-nova / skills / astro-figure / references / plot-scripts / spectrum.py
光谱图模板 — X: 波长/频率/能量, Y: 流量/通量密度

用法:
    python spectrum.py data.csv

数据格式:
    CSV 至少两列: wavelength, flux
    可选第三列: flux_err (误差)
"""
import sys
import numpy as np
import matplotlib.pyplot as plt

# ── 应用样式 ──────────────────────────────────────────────────────────
plt.style.use("references/figure-styles.mplstyle")


def plot_spectrum(wavelength, flux, flux_err=None, output="spectrum.pdf"):
    """绘制光谱图"""
    fig, ax = plt.subplots(figsize=(3.25, 2.5))

    if flux_err is not None:
        ax.errorbar(wavelength, flux, yerr=flux_err,
                     fmt="-", capsize=1.5, capthick=0.5,
                     linewidth=0.8, markersize=2)
    else:
        ax.plot(wavelength, flux, linewidth=0.8)

    ax.set_xlabel(r"Wavelength [\AA]")
    ax.set_ylabel(r"Flux [erg s$^{-1}$ cm$^{-2}$ \AA$^{-1}$]")
    ax.set_xlim(wavelength.min(), wavelength.max())

    fig.tight_layout()
    fig.savefig(output)
    print(f"输出: {output}")
    plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    data = np.loadtxt(sys.argv[1], delimiter=",", unpack=True)
    if data.shape[0] == 2:
        plot_spectrum(data[0], data[1])
    elif data.shape[0] >= 3:
        plot_spectrum(data[0], data[1], flux_err=data[2])
    else:
        print("数据列数不足", file=sys.stderr)
        sys.exit(1)
