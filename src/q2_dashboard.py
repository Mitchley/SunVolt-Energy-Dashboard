"""
SunVolt Energy - Question 2: Executive dashboard
Run: streamlit run src/q2_dashboard.py
Reads: data/SunVolt Solar Customer Data.xlsx
"""

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "SunVolt Solar Customer Data.xlsx"

NAVY, TEAL, ORANGE = "#264653", "#2A9D8F", "#E76F51"
GREY, DARKGREY = "#C5CCD3", "#4A5560"

AGE_ORDER = ["Under 30", "30-39", "40-49", "50-59", "60+"]
INC_ORDER = ["<30k", "30k-49k", "50k-69k", "70k-99k", "100k+"]

st.set_page_config(page_title="SunVolt Energy - Growth Dashboard", page_icon="☀️", layout="wide")

st.markdown(
    """
<style>
.block-container { padding-top: 1.4rem; padding-bottom: 1rem; max-width: 1500px; }
.big-idea { background:#264653; color:white; padding:20px 26px; border-radius:10px; margin-bottom:16px; }
.big-idea h1 { color:white !important; font-size:1.55rem; margin:0 0 8px 0; line-height:1.3; }
.big-idea p { color:#C9D6E3 !important; margin:0; font-size:1rem; }
.sec { color:#5B6B7B !important; font-size:0.9rem; font-weight:700; letter-spacing:.08em; margin:12px 0 0 0; }
.ctitle { color:#1B2A38 !important; font-size:1.02rem; font-weight:700; line-height:1.3; margin:3px 0 0 0; }
.csub { color:#5B6B7B !important; font-size:0.86rem; margin:0 0 3px 0; }
.card { border:1px solid #E1E6EB; border-top:4px solid #E76F51; border-radius:8px; padding:14px 16px; height:100%; background:#FBFCFD; }
.card h4 { color:#1B2A38 !important; margin:0 0 8px 0; font-size:1.05rem; }
.card p { color:#33414F !important; font-size:0.9rem; margin:0 0 8px 0; line-height:1.45; }
.card .tgt { color:#E76F51 !important; font-weight:700; font-size:0.88rem; }
</style>
""",
    unsafe_allow_html=True,
)

_HAS_WIDTH = "width" in inspect.signature(st.plotly_chart).parameters


def show(fig):
    if _HAS_WIDTH:
        st.plotly_chart(fig, width="stretch")
    else:
        st.plotly_chart(fig, use_container_width=True)


def pct(x, d=0):
    return f"{x * 100:.{d}f}%"


def section(label):
    st.markdown(f"<p class='sec'>{label}</p>", unsafe_allow_html=True)


def chart_title(title, sub=""):
    st.markdown(f"<p class='ctitle'>{title}</p><p class='csub'>{sub}</p>", unsafe_allow_html=True)


@st.cache_data
def load_data(path):
    df = pd.read_excel(path).drop_duplicates().reset_index(drop=True)
    df["Purchase Flag"] = (df["Purchased Solar System"].str.strip() == "Yes").astype(int)
    if set(df["Age Group"].unique()) <= set(AGE_ORDER):
        df["Age Group"] = pd.Categorical(df["Age Group"], AGE_ORDER, ordered=True)
    order = (df.drop_duplicates("Distance from Nearest Installer")
             .sort_values("Installer Distance Order")["Distance from Nearest Installer"].tolist())
    df["Distance Band"] = pd.Categorical(df["Distance from Nearest Installer"], order, ordered=True)
    df["Far"] = df["Distance Band"].cat.codes >= 3
    return df


def rate_table(df, col):
    t = (df.groupby(col, observed=True)["Purchase Flag"]
         .agg(customers="count", purchasers="sum", rate="mean").reset_index())
    t["non_purchasers"] = t["customers"] - t["purchasers"]
    t[col] = t[col].astype(str)
    return t


def bar(labels, rates, colors, texts, height=320, xlabel="", hover=None, y_max=None,
        tick_size=12, title_size=13, label_size=12, margin=None):
    if y_max is None:
        y_max = max(rates) * 1.25
    fig = go.Figure(go.Bar(
        x=labels, y=rates, marker_color=colors,
        text=texts, textposition="outside", cliponaxis=False,
        textfont=dict(size=label_size, color=NAVY),
        hovertext=hover,
        hovertemplate="%{x}<br>Purchase rate: %{y:.0%}<br>%{hovertext}<extra></extra>"
        if hover else "%{x}<br>Purchase rate: %{y:.0%}<extra></extra>",
    ))
    fig.update_layout(
        height=height, plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        margin=margin or dict(l=60, r=20, t=20, b=90),
        font=dict(color=NAVY, size=tick_size), bargap=0.35,
    )
    fig.update_xaxes(
        title=dict(text=xlabel, font=dict(color=NAVY, size=title_size)),
        showline=True, linecolor=GREY, linewidth=1,
        ticks="outside", tickcolor=GREY, ticklen=4,
        tickfont=dict(color=NAVY, size=tick_size), showgrid=False, zeroline=False,
    )
    fig.update_yaxes(
        title=dict(text="Purchase Rate", font=dict(color=NAVY, size=title_size)),
        showline=False, showgrid=True, gridcolor="#E5E5E5", gridwidth=1,
        zeroline=False, tickformat=".0%", tickfont=dict(color=NAVY, size=tick_size),
        range=[0, y_max],
    )
    return fig


def highlight_colors(rates, avg):
    rates = list(rates)
    hi, lo = int(np.argmax(rates)), int(np.argmin(rates))
    return [TEAL if i == hi else ORANGE if i == lo else GREY for i in range(len(rates))]


def main():
    if not DATA_FILE.exists():
        st.error(f"Data file not found: {DATA_FILE}")
        st.stop()

    df = load_data(str(DATA_FILE))
    n, avg = len(df), df["Purchase Flag"].mean()
    not_bought = int((1 - df["Purchase Flag"]).sum())

    reg = rate_table(df, "Region")
    worst_reg, best_reg = reg.loc[reg["rate"].idxmin()], reg.loc[reg["rate"].idxmax()]
    weak_share = worst_reg["non_purchasers"] / reg["non_purchasers"].sum()

    age = rate_table(df, "Age Group")
    best_age, worst_age = age.loc[age["rate"].idxmax()], age.loc[age["rate"].idxmin()]

    inc = rate_table(df, "Income Band").set_index("Income Band").reindex(INC_ORDER).reset_index()
    worst_inc = inc.loc[inc["rate"].idxmin()]

    mar = rate_table(df, "Marital Status").sort_values("rate", ascending=False)
    married_rate = float(mar.loc[mar["Marital Status"] == "Married", "rate"].iloc[0])
    single_rate = float(mar.loc[mar["Marital Status"] == "Single", "rate"].iloc[0])

    near = df.loc[~df["Far"], "Purchase Flag"].mean()
    far = df.loc[df["Far"], "Purchase Flag"].mean()
    n_far = int(df["Far"].sum())

    # ---- Banner ----
    st.markdown(
        f"""
<div class="big-idea">
<h1>{pct(avg)} of our customers have bought a solar backup system. The next wave of growth is in
{worst_reg['Region']}, in married households, and beyond 5 km from an installer.</h1>
<p>{not_bought:,} customers have not yet bought. Targeted action on four areas we can control
could convert a meaningful share of them.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # ---- KPIs ----
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Customers analysed", f"{n:,}")
    k2.metric("Purchase rate", pct(avg, 1))
    k3.metric("Not yet purchased", f"{not_bought:,}")
    k4.metric("Top age group", best_age["Age Group"], f"{pct(best_age['rate'])} purchase rate")

    # =============================================================
    # ROW 1 — Where we stand
    # =============================================================
    section("1 · Where we stand")

    r = reg.sort_values("rate", ascending=False)
    reg_hover = [f"{int(c)} customers · {int(nb)} not bought"
                 for c, nb in zip(r["customers"], r["non_purchasers"])]
    age_hover = [f"{int(c)} customers · {int(nb)} not bought"
                 for c, nb in zip(age["customers"], age["non_purchasers"])]
    mar_hover = [f"{int(c)} customers · {int(nb)} not bought"
                 for c, nb in zip(mar["customers"], mar["non_purchasers"])]

    d1, d2, d3 = st.columns(3)
    with d1:
        chart_title("Regional performance",
                    f"{worst_reg['Region']} trails at {pct(worst_reg['rate'])}")
        show(bar(list(r["Region"]), list(r["rate"]), highlight_colors(r["rate"], avg),
                 [pct(x) for x in r["rate"]], height=300, xlabel="",
                 hover=reg_hover, tick_size=11, title_size=11, label_size=11,
                 margin=dict(l=10, r=10, t=10, b=60)))
    with d2:
        chart_title("Age profile",
                    f"{best_age['Age Group']} leads at {pct(best_age['rate'])}")
        show(bar(list(age["Age Group"]), list(age["rate"]), highlight_colors(age["rate"], avg),
                 [pct(x) for x in age["rate"]], height=300, xlabel="",
                 hover=age_hover, tick_size=11, title_size=11, label_size=11,
                 margin=dict(l=10, r=10, t=10, b=60)))
    with d3:
        chart_title("Household type",
                    f"Single customers lead at {pct(single_rate)}")
        show(bar(list(mar["Marital Status"]), list(mar["rate"]), highlight_colors(mar["rate"], avg),
                 [pct(x) for x in mar["rate"]], height=300, xlabel="",
                 hover=mar_hover, tick_size=11, title_size=11, label_size=11,
                 margin=dict(l=10, r=10, t=10, b=60)))

    # =============================================================
    # ROW 2 — What drives purchase
    # =============================================================
    section("2 · What drives purchase")

    dist = rate_table(df, "Distance Band")
    dist_colors = [ORANGE if i >= 3 else GREY for i in range(len(dist))]
    dist_hover = [f"{int(c)} customers" for c in dist["customers"]]
    inc_hover = [f"{int(c)} customers · {int(nb)} not bought"
                 for c, nb in zip(inc["customers"], inc["non_purchasers"])]

    e1, e2 = st.columns(2)
    with e1:
        chart_title(
            "Distance from installer",
            f"Beyond 5 km, purchases fall from {pct(near)} to {pct(far)}",
        )
        show(bar(list(dist["Distance Band"]), list(dist["rate"]), dist_colors,
                 [pct(x) for x in dist["rate"]], height=320,
                 xlabel="Distance from Nearest Installer", hover=dist_hover))
    with e2:
        chart_title(
            "Income band",
            "Income only acts as a barrier below 30k",
        )
        show(bar(list(inc["Income Band"]), list(inc["rate"]), highlight_colors(inc["rate"], avg),
                 [pct(x) for x in inc["rate"]], height=320,
                 xlabel="Income Band", hover=inc_hover))

    # =============================================================
    # ROW 3 — What we should fix
    # =============================================================
    section("3 · What we should fix")

    f1, f2 = st.columns([2, 3])
    with f1:
        chart_title("The Key Gaps",
                    "The five segments with the lowest purchase rates")
        segments = [
            ("Age 60+", float(age.loc[age["Age Group"] == "60+", "rate"].iloc[0]),
                       int(age.loc[age["Age Group"] == "60+", "customers"].iloc[0])),
            ("Live 5+ km from installer", far, n_far),
            ("Income <30k", float(inc.loc[inc["Income Band"] == "<30k", "rate"].iloc[0]),
                            int(inc.loc[inc["Income Band"] == "<30k", "customers"].iloc[0])),
            ("North America", float(reg.loc[reg["Region"] == "North America", "rate"].iloc[0]),
                              int(reg.loc[reg["Region"] == "North America", "customers"].iloc[0])),
            ("Married households", married_rate,
                                   int(mar.loc[mar["Marital Status"] == "Married", "customers"].iloc[0])),
        ]
        seg_sorted = sorted(segments, key=lambda x: x[1])
        labels = [s[0] for s in seg_sorted]
        rates = [s[1] for s in seg_sorted]
        counts = [s[2] for s in seg_sorted]
        gaps = [avg - rr for rr in rates]
        max_gap = max(gaps) if max(gaps) > 0 else 1
        colors = [f"rgba(231, 111, 81, {0.35 + 0.65 * (g / max_gap):.2f})" if g > 0 else GREY
                  for g in gaps]

        fig = go.Figure(go.Bar(
            y=labels, x=rates, orientation="h", marker_color=colors,
            text=[f"{pct(rr)} · {c}" for rr, c in zip(rates, counts)],
            textposition="outside", cliponaxis=False,
            textfont=dict(size=11, color=NAVY),
            hovertemplate="%{y}<br>Purchase rate: %{x:.0%}<br>%{text}<extra></extra>",
        ))
        fig.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                          showlegend=False, margin=dict(l=10, r=120, t=10, b=60),
                          font=dict(color=NAVY, size=12))
        fig.update_xaxes(title=dict(text="Purchase Rate", font=dict(color=NAVY, size=12)),
                         showline=True, linecolor=GREY, linewidth=1,
                         ticks="outside", tickcolor=GREY, ticklen=4,
                         tickformat=".0%", range=[0, max(rates) * 1.45],
                         tickfont=dict(color=NAVY, size=11))
        fig.update_yaxes(title="",
                         showline=False, showgrid=True, gridcolor="#E5E5E5", gridwidth=1,
                         automargin=True, tickfont=dict(size=11, color=NAVY))
        show(fig)

    with f2:
        chart_title("Proposed Solutions",
                    "Four targeted areas to increase sales")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(
                f"""<div class="card"><h4>1. Boost {worst_reg['Region']} Sales</h4>
<p>Localised campaigns, installer partnerships and financing for the region with lowest sales.</p>
<span class="tgt">Target: toward {best_reg['Region']}'s {pct(best_reg['rate'])}</span></div>""",
                unsafe_allow_html=True)
        with r2:
            st.markdown(
                f"""<div class="card"><h4>2. Family offer for married households</h4>
<p>Married customers purchase at {pct(married_rate)}. Bundle packages and financing to close the gap.</p>
<span class="tgt">Target: toward the {pct(avg)} average</span></div>""",
                unsafe_allow_html=True)
        st.write("")
        r3, r4 = st.columns(2)
        with r3:
            st.markdown(
                f"""<div class="card"><h4>3. Close the installer gap</h4>
<p>Establish regional installation teams and remote consultations for distant areas (5+ km away).</p>
<span class="tgt">Target: from {pct(far)} toward {pct(near)}</span></div>""",
                unsafe_allow_html=True)
        with r4:
            st.markdown(
                f"""<div class="card"><h4>4. Financing for under-30k band</h4>
<p>A rent-to-own option unlocks the only income band that lags the average.</p>
<span class="tgt">Target: from {pct(worst_inc['rate'])} to {pct(avg)}</span></div>""",
                unsafe_allow_html=True)

    st.caption(
        f"Source: SunVolt customer data, {n:,} unique customers after removing duplicate rows. "
        "Findings show association, not proven cause."
    )


main()
