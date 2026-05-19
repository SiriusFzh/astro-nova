"""
astro-nova / skills / astro-figure / references / plot-scripts / SED.py
SED (光谱能量分布) 模板 — X: log10(频率/Hz), Y: log10(流量密度)

用法:
    python SED.py data.csv

数据格式:
    CSV: log_nu, log_f_nu, log_f_err(optional)
"""
import sys
import numpy as np
import matplotlib.pyplot as plt

plt.style.use("references/figure-styles.mplstyle")


def plot_sed(log_nu, log_f_nu, log_f_err=None, output="SED.pdf"):
    """绘制 SED 图"""
    fig, ax = plt.subplots(figsize=(3.25, 2.5))

    if log_f_err is not None:
        ax.errorbar(log_nu, log_f_nu, yerr=log_f_err,
                     fmt="o", capsize=1.5, capthick=0.5,
                     markersize=4, color="#1565c0")
    else:
        ax.plot(log_nu, log_f_nu, "o", markersize=4, color="#1565c0")

    ax.set_xlabel(r"log($\nu$ / Hz)")
    ax.set_ylabel(r"log($F_\nu$ / Jy)")
    ax.set_xlim(log_nu.min(), log_nu.max())

    fig.tight_layout()
    fig.savefig(output)
    print(f"输出: {output}")
    plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    data = np.loadtxt(sys.argv[1], delimiter=",", unpack=True)
    ncols = data.shape[0]

    if ncols == 2:
        plot_sed(data[0], data[1])
    elif ncols >= 3:
        plot_sed(data[0], data[1], log_f_err=data[2])
    else:
        print("数据列数不足", file=sys.stderr)
        sys.exit(1)
