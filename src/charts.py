from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

from config import INCLUDED_STATUSES, START, END, CATEGORY_COL
from load_data import load_merged

FIG = Path("figures")
FIG.mkdir(exist_ok=True)

BLUE, LIGHT_BLUE, GREY = "#1f77b4", "#9ecae1", "#888888"
EXPECTED_TOTAL = 13_181_027.13   # verified in verify_claims.py

plt.rcParams.update({
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "font.size": 10,
})

thousands = FuncFormatter(lambda x, _: f"{x / 1e3:,.0f}k")


def footnote(fig, text):
    fig.text(0.01, 0.01, text, fontsize=8, color="#555555", ha="left", va="bottom")


def chart_monthly(w):
    m = w.assign(month=w["order_purchase_timestamp"].dt.to_period("M"))
    monthly = m.groupby("month")["price"].sum()

    expected = pd.period_range("2017-01", "2018-08", freq="M")
    assert list(monthly.index) == list(expected), "Unexpected or missing months"

    labels = monthly.index.strftime("%b %Y")
    colors = [BLUE] * (len(monthly) - 1) + [LIGHT_BLUE]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(labels, monthly.values, color=colors)
    bars[-1].set_hatch("//")
    bars[-1].set_edgecolor(BLUE)

    ax.set_title("Monthly item value, delivered orders (Jan 2017 - Aug 2018)",
                 loc="left", fontweight="bold")
    ax.set_ylabel("Item value (BRL, thousands)")
    ax.yaxis.set_major_formatter(thousands)
    ax.tick_params(axis="x", rotation=60)
    ax.grid(axis="x", visible=False)

    peak = monthly.idxmax()
    peak_i = list(monthly.index).index(peak)
    ax.annotate(f"Peak: {peak.strftime('%b %Y')}\n{monthly.max() / 1e3:,.0f}k",
                xy=(peak_i, monthly.max()),
                xytext=(peak_i - 3.2, monthly.max() * 1.0),
                arrowprops=dict(arrowstyle="->", color=GREY), fontsize=9)
    ax.annotate("Aug 2018:\npartial period*",
                xy=(len(monthly) - 1, monthly.iloc[-1]),
                xytext=(len(monthly) - 4.2, monthly.max() * 0.45),
                arrowprops=dict(arrowstyle="->", color=GREY), fontsize=9)

    fig.subplots_adjust(bottom=0.25)
    footnote(fig,
             "*Purchase records thin out after about 20 Aug 2018, so August is likely a lower bound. "
             "Item value = sum of price (freight excluded), not profit.\n"
             "Source: Olist Brazilian E-Commerce dataset. Month = purchase month.")
    fig.savefig(FIG / "01_monthly_item_value.png", dpi=200)
    plt.close(fig)
    return monthly


def chart_categories(w, total):
    cat = w.groupby(CATEGORY_COL)["price"].sum().sort_values(ascending=False)
    top = cat.head(10)
    share = top / total * 100
    top10_share = share.sum()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top.index[::-1], share.values[::-1], color=BLUE)
    for y, v in enumerate(share.values[::-1]):
        ax.text(v + 0.1, y, f"{v:.1f}%", va="center", fontsize=9)

    ax.set_title("Top 10 product categories by share of item value",
                 loc="left", fontweight="bold")
    ax.set_xlabel("Share of total item value (%)")
    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.set_xlim(0, share.max() * 1.15)
    ax.grid(axis="y", visible=False)

    fig.subplots_adjust(bottom=0.2)
    footnote(fig,
             f"Top 10 categories = {top10_share:.1f}% of {total:,.0f} total item value "
             f"(Jan 2017 - Aug 2018, delivered orders, {cat.size} categories incl. 'unknown').\n"
             "Ranked by value; ranking by order count gives a different order "
             "(e.g. bed_bath_table leads on orders).")
    fig.savefig(FIG / "02_category_share.png", dpi=200)
    plt.close(fig)
    return cat


def chart_concentration(w, total):
    prod = (w.groupby("product_id")["price"].sum().rename("v").reset_index()
              .sort_values(["v", "product_id"], ascending=[False, True])
              .reset_index(drop=True))
    n = len(prod)
    cum = np.concatenate([[0], prod["v"].cumsum().to_numpy() / total * 100])
    x = np.arange(n + 1) / n * 100

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(x, cum, color=BLUE, lw=2, label="Cumulative item value")
    ax.plot([0, 100], [0, 100], color=GREY, ls="--", lw=1,
            label="Equal contribution (reference)")

    for pct in (1, 10, 20):
        k = int(round(n * pct / 100))
        y = cum[k]
        ax.plot(pct, y, "o", color="#d62728")
        ax.annotate(f"Top {pct}% ({k:,} products)\n= {y:.1f}% of value",
                    xy=(pct, y), xytext=(pct + 6, y - 14),
                    arrowprops=dict(arrowstyle="->", color=GREY), fontsize=9)

    ax.set_title("Product concentration: item value by product rank",
                 loc="left", fontweight="bold")
    ax.set_xlabel("Products ranked by item value (% of all products)")
    ax.set_ylabel("Cumulative share of item value (%)")
    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", frameon=False)

    fig.subplots_adjust(bottom=0.2)
    footnote(fig,
             f"Denominator: all {n:,} products sold in the window. Ranked by item value only (ties broken by product_id),\n"
             "so high-priced low-order products rank alongside high-order products. Not a measure of profit.")
    fig.savefig(FIG / "03_product_concentration.png", dpi=200)
    plt.close(fig)
    return prod


def main():
    df = load_merged()
    w = df[
        df["order_status"].isin(INCLUDED_STATUSES)
        & (df["order_purchase_timestamp"] >= START)
        & (df["order_purchase_timestamp"] < END)
    ]
    total = w["price"].sum()
    assert abs(total - EXPECTED_TOTAL) < 0.005, f"Window total changed: {total:,.2f}"

    monthly = chart_monthly(w)
    assert abs(monthly.sum() - total) < 1e-6
    cat = chart_categories(w, total)
    assert abs(cat.sum() - total) < 1e-6
    prod = chart_concentration(w, total)
    assert abs(prod["v"].sum() - total) < 1e-6

    print(f"Total item value: {total:,.2f} (all three charts reconcile)")
    print(f"Saved charts to {FIG.resolve()}")


if __name__ == "__main__":
    main()