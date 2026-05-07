import pandas as pd
import matplotlib.pyplot as plt


def hist_g(r_list, interval, bmk):

    # r_list[k] = total return for portfolio size k+1
    top_max = len(r_list)

    # build table
    top_n_list = []
    total_list = []

    for k in range(top_max):
        top_n_list.append(k + 1)
        total_list.append(r_list[k])

    res_fixed = pd.DataFrame({
        "top_n": top_n_list,
        "total_return": total_list
    })

    # best portfolio size
    best_idx = res_fixed["total_return"].idxmax()
    best_top_n = int(res_fixed.loc[best_idx, "top_n"])
    best_total_return = res_fixed.loc[best_idx, "total_return"]

    print("best portfolio size:", best_top_n)
    print("best total return:", round(best_total_return * 100, 2))

    # benchmark total return passed as argument
    bmk_total = (1 + bmk).prod() - 1

    plt.figure(figsize=(11, 5))
    plt.plot(
        res_fixed["top_n"],
        res_fixed["total_return"] * 100,
        label="Portfolio total return"
    )

    plt.axhline(
        bmk_total * 100,
        linestyle="--",
        color="red",
        alpha=0.9,
        label="Benchmark total return"
    )

    plt.axvline(
        best_top_n,
        linestyle="--",
        alpha=0.6,
        label=f"Best Portfolio Size = {best_top_n}"
    )

    plt.xlim(1, top_max)
    plt.xlabel("Portfolio Size")
    plt.ylabel("Total Return (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

    interval_winners = []

    start_val = 1
    while start_val <= top_max:
        end_val = start_val + interval - 1
        if end_val > top_max:
            end_val = top_max

        mask = (res_fixed["top_n"] >= start_val) & (res_fixed["top_n"] <= end_val)
        sub = res_fixed[mask]

        sub_best_idx = sub["total_return"].idxmax()
        sub_best_n = int(res_fixed.loc[sub_best_idx, "top_n"])
        sub_best_tr = res_fixed.loc[sub_best_idx, "total_return"] * 100
        interval_winners.append((start_val, end_val, sub_best_n, sub_best_tr))

        start_val = end_val + 1

    interval_table = pd.DataFrame(
        interval_winners,
        columns=["start", "end", "best_top_n", "best_total_return_%"]
    )

    interval_col = []
    for i in range(interval_table.shape[0]):
        a = str(interval_table.loc[i, "start"])
        b = str(interval_table.loc[i, "end"])
        interval_col.append(a + "-" + b)

    interval_table["interval"] = interval_col

    plt.figure(figsize=(11, 5))
    plt.bar(interval_table["interval"], interval_table["best_total_return_%"])

    plt.xlabel("Portfolio size")
    plt.ylabel("Best Total Return per Interval (%)")

    for i in range(interval_table.shape[0]):
        row = interval_table.iloc[i]
        plt.text(
            i,
            row["best_total_return_%"],
            str(int(row["best_top_n"])),
            ha="center",
            va="bottom",
            fontsize=9
        )

    plt.xticks(rotation=45, ha="right")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()
