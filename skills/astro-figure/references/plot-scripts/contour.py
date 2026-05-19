"""
astro-nova / skills / astro-figure / references / plot-scripts / contour.py
等高线/置信区间图模板 — 展示参数空间的后验分布

用法:
    python contour.py data.csv

数据格式:
    CSV: param1, param2  (两列, 所有 MCMC 样本点)
"""
import sys
import numpy as np
import matplotlib.pyplot as plt

plt.style.use("references/figure-styles.mplstyle")


def plot_contour(x, y, output="contour.pdf", levels=[0.68, 0.95, 0.997]):
    """绘制置信区间等高线图"""
    fig, ax = plt.subplots(figsize=(3.25, 3.0))

    # 2D 直方图
    counts, xedges, yedges = np.histogram2d(x, y, bins=50)
    x_centers = (xedges[:-1] + xedges[1:]) / 2
    y_centers = (yedges[:-1] + yedges[1:]) / 2

    # 按密度排序的等值线
    sorted_counts = np.sort(counts.ravel())[::-1]
    cumulative = np.cumsum(sorted_counts) / np.sum(counts)
    contour_levels = []
    for level in levels:
        idx = np.searchsorted(cumulative, level)
        contour_levels.append(sorted_counts[max(idx, 0)])

    X, Y = np.meshgrid(x_centers, y_centers)
    ax.contourf(X.T, Y.T, counts, levels=contour_levels,
                 colors=["#e3f2fd", "#90caf9", "#1565c0"], alpha=0.6)
    ax.contour(X.T, Y.T, counts, levels=contour_levels,
                colors=["#0d47a1"], linewidths=0.8)

    # 最佳拟合值 (中位数)
    x_best, y_best = np.median(x), np.median(y)
    ax.axvline(x_best, color="#bf360c", linestyle="--", linewidth=0.6)
    ax.axhline(y_best, color="#bf360c", linestyle="--", linewidth=0.6)

    ax.set_xlabel("Parameter 1")
    ax.set_ylabel("Parameter 2")

    fig.tight_layout()
    fig.savefig(output)
    print(f"输出: {output}")
    plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    data = np.loadtxt(sys.argv[1], delimiter=",", unpack=True)
    plot_contour(data[0], data[1])
