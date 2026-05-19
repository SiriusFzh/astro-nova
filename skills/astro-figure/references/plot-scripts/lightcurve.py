"""
astro-nova / skills / astro-figure / references / plot-scripts / lightcurve.py
光变曲线模板 — X: 时间 (MJD), Y: 流量/星等

用法:
    python lightcurve.py data.csv

数据格式:
    CSV 至少两列: time, flux
    可选第三列: flux_err
"""
import sys
import numpy as np
import matplotlib.pyplot as plt

plt.style.use("references/figure-styles.mplstyle")


def plot_lightcurve(time, flux, flux_err=None, output="lightcurve.pdf"):
    """绘制光变曲线"""
    fig, ax = plt.subplots(figsize=(3.25, 2.5))

    if flux_err is not None:
        ax.errorbar(time, flux, yerr=flux_err,
                     fmt="o", capsize=1.5, capthick=0.5,
                     markersize=3, linewidth=0.5, ecolor="gray")
    else:
        ax.plot(time, flux, "o", markersize=3)

    ax.set_xlabel(r"Time [MJD]")
    ax.set_ylabel(r"Flux")
    ax.set_xlim(time.min(), time.max())

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
        plot_lightcurve(data[0], data[1])
    elif data.shape[0] >= 3:
        plot_lightcurve(data[0], data[1], flux_err=data[2])
    else:
        print("数据列数不足", file=sys.stderr)
        sys.exit(1)
