import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates


def chart(r, bmk, rf):

    # Copy to avoid modifying original data
    r = r.copy()
    bmk = bmk.copy()
    rf = rf.copy()

    # FORCE all indices to datetime so they can align correctly
    r.index = pd.to_datetime(r.index)
    bmk.index = pd.to_datetime(bmk.index)
    rf.index = pd.to_datetime(rf.index)

    # Align data
    idx = r.index.intersection(bmk.index).intersection(rf.index)

    # Safety check: If no common dates found, stop to prevent the crash
    if len(idx) == 0:
        print("Error: No common dates found between Portfolio, Benchmark, and Risk-Free Rate.")
        print(f"Portfolio range: {r.index.min()} to {r.index.max()}")
        print(f"Benchmark range: {bmk.index.min()} to {bmk.index.max()}")
        return

    r = r.loc[idx]
    bmk = bmk.loc[idx]
    rf = rf.loc[idx]

    # cumulative returns
    cum_p = (1 + r).cumprod() - 1
    cum_b = (1 + bmk).cumprod() - 1
    spread = cum_p - cum_b

    # active monthly
    active_m = r - bmk

    # stats
    total_p = (1 + r).prod() - 1
    total_b = (1 + bmk).prod() - 1

    mean_p = r.mean()
    mean_active = active_m.mean()
    min_p = r.min()
    max_p = r.max()

    std_p = r.std()
    downside = r[r < 0]
    semi_var = (downside ** 2).mean()

    te_m = active_m.std()

    excess_p = r - rf
    sharpe = (excess_p.mean() / r.std()) * np.sqrt(12)

    # Jensen alpha and beta
    y = excess_p
    X = (bmk - rf).to_frame("bench")
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    alpha_m = model.params["const"]
    beta = model.params["bench"]
    alpha_ann = (1 + alpha_m) ** 12 - 1

    active_ann = mean_active * 12
    te_ann = te_m * np.sqrt(12)
    info_ratio = active_ann / te_ann

    corr = r.corr(bmk)

    # Up and down capture
    up_mask = bmk > 0
    down_mask = bmk < 0

    up_capture = np.nan
    down_capture = np.nan

    if up_mask.any():
        up_p = (1 + r[up_mask]).prod() - 1
        up_b = (1 + bmk[up_mask]).prod() - 1
        if up_b != 0:
            up_capture = up_p / up_b

    if down_mask.any():
        down_p = (1 + r[down_mask]).prod() - 1
        down_b = (1 + bmk[down_mask]).prod() - 1
        if down_b != 0:
            down_capture = down_p / down_b

    up_cap_str = "   N/A"
    down_cap_str = "   N/A"
    if not np.isnan(up_capture):
        up_cap_str = f"{up_capture*100:8.2f}"
    if not np.isnan(down_capture):
        down_cap_str = f"{down_capture*100:8.2f}"

    # Theme
    bg = "#000000"
    panel_bg = "#000000"
    fg = "#e6e6e6"
    grid_c = "#333333"
    orange = "#ff9f1a"
    white = "#ffffff"
    green = "#00c853"
    red = "#ff1744"
    spine_c = "#666666"

    # layout
    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor(bg)

    gs = GridSpec(
        3,
        2,
        width_ratios=[4, 1.6],
        height_ratios=[2.2, 1.6, 1.6],
        hspace=0.35,
        wspace=0.2,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)
    ax3 = fig.add_subplot(gs[2, 0], sharex=ax1)
    axs = fig.add_subplot(gs[:, 1])
    axs.axis("off")

    # x axis, one major tick per year, labels only on bottom
    year_loc = mdates.YearLocator()
    year_fmt = mdates.DateFormatter("%Y")

    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor(panel_bg)
        ax.grid(True, axis="y", color=grid_c, alpha=0.6)
        ax.tick_params(colors=fg)
        for s in ax.spines.values():
            s.set_color(spine_c)
        ax.title.set_color(fg)
        ax.yaxis.label.set_color(fg)
        ax.xaxis.label.set_color(fg)

        ax.xaxis.set_major_locator(year_loc)
        ax.xaxis.set_major_formatter(year_fmt)

    ax1.tick_params(labelbottom=True)
    ax2.tick_params(labelbottom=True)
    ax3.tick_params(labelbottom=True, rotation=0)

    # top, cumulative
    ax1.plot(cum_p.index, cum_p * 100, label="Screen", color=orange, linewidth=2)
    ax1.plot(cum_b.index, cum_b * 100, label="SPX", color=white, linewidth=1.8)
    ax1.set_title("Cumulative Return (%)")
    leg = ax1.legend(loc="upper left", frameon=True)
    leg.get_frame().set_facecolor(panel_bg)
    leg.get_frame().set_edgecolor(spine_c)
    for t in leg.get_texts():
        t.set_color(fg)

    # middle, spread
    spread_pct = spread * 100

    ax2.fill_between(
        spread_pct.index,
        0,
        spread_pct,
        where=spread_pct >= 0,
        interpolate=True,
        color=green,
        alpha=0.35,
    )

    ax2.fill_between(
        spread_pct.index,
        0,
        spread_pct,
        where=spread_pct < 0,
        interpolate=True,
        color=red,
        alpha=0.35,
    )

    ax2.plot(spread_pct.index, spread_pct, color=white, linewidth=1)
    ax2.axhline(0, linewidth=1, color=white, alpha=0.8)
    ax2.set_title("Spread Return (%)")

    # bottom, active bars
    colors = np.where(active_m >= 0, green, red)
    ax3.bar(active_m.index, active_m * 100, width=25, color=colors, alpha=0.9)
    ax3.axhline(0, linewidth=1, color=white, alpha=0.8)
    ax3.set_title("Active Return (%)")

    # stats panel
    stats_lines = [
        ("Total Return (%)", f"{total_p*100:8.2f}"),
        ("Benchmark Total (%)", f"{total_b*100:8.2f}"),
        ("Mean Return (%)", f"{mean_p*100:8.2f}"),
        ("Mean Active (%)", f"{mean_active*100:8.2f}"),
        ("Min Return (%)", f"{min_p*100:8.2f}"),
        ("Max Return (%)", f"{max_p*100:8.2f}"),
        ("", ""),
        ("Std Dev (%)", f"{std_p*100:8.2f}"),
        ("Semi variance", f"{semi_var*10000:8.2f}"),
        ("Tracking Error (%)", f"{te_m*100:8.2f}"),
        ("", ""),
        ("Sharpe Ratio", f"{sharpe:8.2f}"),
        ("Up Capture (%)", up_cap_str),
        ("Down Capture (%)", down_cap_str),
        ("Jensen Alpha (%)", f"{alpha_ann*100:8.2f}"),
        ("Information Ratio", f"{info_ratio:8.2f}"),
        ("Beta", f"{beta:8.2f}"),
        ("Correlation", f"{corr:8.2f}"),
    ]

    y0 = 0.98
    dy = 0.038
    dy_blank = 0.018

    y = y0
    for lab, val in stats_lines:
        axs.text(
            0.02,
            y,
            lab,
            va="top",
            ha="left",
            family="monospace",
            fontsize=11,
            color=orange,
        )

        axs.text(
            0.98,
            y,
            val,
            va="top",
            ha="right",
            family="monospace",
            fontsize=11,
            color=white,
        )

        if lab == "":
            y -= dy_blank
        else:
            y -= dy

    plt.show()
