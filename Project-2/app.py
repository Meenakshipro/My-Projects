"""Streamlit dashboard for the Traffic Violations Insight System (streamlit run app.py)."""
import base64
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "traffic_violations.db"
LOGO_PATH = Path(__file__).parent / "assets" / "logo.svg"

# Body text colour used in charts (matches the CSS theme's --ink).
INK = "#EAF0FA"
# Shared colour order for all charts.
CHART_COLORS = [
    "#3EC1D3", "#5BE7C4", "#9D8DF1", "#F4D35E",
    "#4EA8DE", "#7B9EF0", "#57CC99", "#C9ADA7",
]


@st.cache_data
def _logo_data_uri():
    """Return the SVG logo as a data URI for HTML embedding and the tab icon."""
    svg = LOGO_PATH.read_text(encoding="utf-8")
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def style_fig(fig):
    """Give any Plotly figure the dashboard's dark, glassy look."""
    fig.update_layout(
        template="plotly_dark",
        colorway=CHART_COLORS,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Poppins, sans-serif", color=INK),
        title_font=dict(family="Playfair Display, serif"),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(159,176,201,0.12)", zeroline=False),
        yaxis=dict(gridcolor="rgba(159,176,201,0.12)", zeroline=False),
    )
    return fig


def inject_css():
    """Inject the night-highway theme: fonts, glass cards, headers, dividers, sidebar."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Playfair+Display:ital,wght@0,600;0,800;1,500;1,600&family=Poppins:wght@300;400;500;600&family=Rajdhani:wght@500;600;700&family=Sora:wght@400;600;700&display=swap');

        .stApp {
            background:
                radial-gradient(1100px 560px at 8% -8%, #1D3A66 0%, rgba(29,58,102,0) 55%),
                radial-gradient(900px 520px at 98% 4%, #114B4A 0%, rgba(17,75,74,0) 52%),
                radial-gradient(700px 700px at 60% 120%, #2A2154 0%, rgba(42,33,84,0) 55%),
                linear-gradient(165deg, #070E22 0%, #0B1830 55%, #08111F 100%);
            background-attachment: fixed;
        }
        html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
        .block-container { padding-top: 2.4rem; }

        /* ---- hero banner ---- */
        .tv-hero {
            position: relative; overflow: hidden;
            display: flex; align-items: center; gap: 24px;
            padding: 26px 34px; margin: 2px 0 6px 0;
            border-radius: 26px;
            background:
                linear-gradient(120deg, rgba(62,193,211,0.16), rgba(157,141,241,0.14) 50%, rgba(31,182,166,0.14)),
                rgba(11,22,44,0.55);
            border: 1px solid rgba(91,231,196,0.30);
            box-shadow: 0 18px 50px rgba(3,8,20,0.6),
                        inset 0 1px 0 rgba(234,240,250,0.08);
        }
        .tv-hero::after {
            content: ""; position: absolute; inset: -40% -10% auto auto;
            width: 380px; height: 380px; border-radius: 50%;
            background: radial-gradient(circle, rgba(91,231,196,0.22), rgba(91,231,196,0) 62%);
            filter: blur(4px); animation: floatglow 9s ease-in-out infinite;
        }
        @keyframes floatglow {
            0%,100% { transform: translate(0,0) scale(1); opacity:.8; }
            50%     { transform: translate(-18px,14px) scale(1.08); opacity:1; }
        }
        .tv-logo-wrap {
            position: relative; width: 96px; height: 96px; flex: none;
        }
        .tv-logo-wrap::before {
            content: ""; position: absolute; inset: -8px; border-radius: 50%;
            background: conic-gradient(from 0deg, #3EC1D3, #5BE7C4, #9D8DF1, #F4D35E, #3EC1D3);
            filter: blur(9px); opacity: .55; animation: spinglow 7s linear infinite;
        }
        @keyframes spinglow { to { transform: rotate(360deg); } }
        .tv-hero img {
            position: relative; width: 96px; height: 96px;
            filter: drop-shadow(0 8px 18px rgba(0,0,0,0.55));
        }
        .tv-hero-title {
            font-family: 'Cinzel', serif; font-weight: 800;
            font-size: 2.55rem; line-height: 1.04; margin: 0;
            background: linear-gradient(92deg, #5BE7C4 0%, #3EC1D3 38%, #9D8DF1 78%, #F4D35E 120%);
            background-size: 220% auto;
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1.5px; animation: shine 6s linear infinite;
        }
        @keyframes shine { to { background-position: 220% center; } }
        .tv-hero-sub {
            font-family: 'Rajdhani', sans-serif; font-weight: 600;
            letter-spacing: 3px; text-transform: uppercase;
            color: #A9BAD4; font-size: 0.9rem; margin-top: 6px;
        }
        .tv-chips { margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; }
        .tv-chip {
            font-family: 'Sora', sans-serif; font-size: 0.68rem; font-weight: 600;
            letter-spacing: 1.4px; text-transform: uppercase;
            padding: 5px 12px; border-radius: 999px; color: #DCE7F7;
            background: rgba(62,193,211,0.10);
            border: 1px solid rgba(91,231,196,0.32);
        }
        .tv-chip.gold { border-color: rgba(244,211,94,0.45); background: rgba(244,211,94,0.10); color:#F6E4A6; }
        .tv-chip.violet { border-color: rgba(157,141,241,0.45); background: rgba(157,141,241,0.12); color:#D9D2FB; }
        .tv-chip .dot {
            display:inline-block; width:7px; height:7px; border-radius:50%;
            background:#5BE7C4; margin-right:6px; box-shadow:0 0 8px #5BE7C4;
            animation: pulse 1.8s ease-in-out infinite;
        }
        @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:.35;} }

        /* ---- animated road divider ---- */
        .road-div {
            position: relative; height: 16px; border-radius: 8px;
            margin: 22px 0 4px 0;
            background: linear-gradient(180deg,#1B2540,#121B33);
            border: 1px solid rgba(159,176,201,0.10);
            box-shadow: inset 0 2px 6px rgba(0,0,0,0.4);
            overflow: hidden;
        }
        .road-div::before {
            content: ""; position: absolute; top: 50%; left: 0; right: 0; height: 3px;
            transform: translateY(-50%);
            background: repeating-linear-gradient(90deg,#F4D35E 0 26px, transparent 26px 52px);
            opacity: .85; animation: lane 2.6s linear infinite;
        }
        @keyframes lane { to { background-position: 52px 0; } }

        /* ---- decorative section headers ---- */
        .sec { display:flex; align-items:center; gap:14px; margin: 6px 0 2px; }
        .sec-badge {
            width:44px; height:44px; flex:none; display:grid; place-items:center;
            font-size:1.25rem; border-radius:14px;
            background: linear-gradient(160deg, rgba(62,193,211,0.22), rgba(16,26,48,0.9));
            border:1px solid rgba(91,231,196,0.35);
            box-shadow: 0 6px 16px rgba(3,8,20,0.5), inset 0 1px 0 rgba(255,255,255,0.06);
        }
        .sec-title {
            font-family:'Sora', sans-serif; font-weight:700; font-size:1.35rem;
            letter-spacing:.4px; line-height:1.1; width:fit-content;
            background: linear-gradient(92deg,#EAF0FA, #9BD9E4 60%, #B7ACF6);
            -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
        }
        .sec-title::after {
            content:""; display:block; height:3px; margin-top:6px; width:60%;
            border-radius:3px;
            background:linear-gradient(90deg,#5BE7C4,#3EC1D3 45%,#9D8DF1);
            box-shadow:0 0 12px rgba(91,231,196,0.5);
            animation: growbar 2.4s ease-in-out infinite alternate;
        }
        @keyframes growbar { from{ width:36%; opacity:.7;} to{ width:78%; opacity:1;} }
        .sec-sub {
            font-family:'Rajdhani', sans-serif; font-weight:600; font-size:.78rem;
            letter-spacing:1.6px; text-transform:uppercase; color:#8497B4; margin-top:1px;
        }

        /* ---- custom KPI cards ---- */
        .kpi-grid {
            display:grid; grid-template-columns: repeat(5, 1fr); gap:16px; margin:6px 0 2px;
        }
        @media (max-width: 1100px){ .kpi-grid{ grid-template-columns: repeat(2,1fr);} }
        .kpi {
            position:relative; overflow:hidden;
            display:flex; align-items:center; gap:14px;
            padding:18px 18px; border-radius:18px;
            background: linear-gradient(160deg, rgba(22,35,63,0.94), rgba(13,22,42,0.94));
            border:1px solid rgba(159,176,201,0.14);
            box-shadow:0 12px 30px rgba(3,8,20,0.5);
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
        }
        .kpi::before {
            content:""; position:absolute; top:0; left:0; height:100%; width:5px;
            background: var(--accent); box-shadow: 0 0 18px var(--accent);
        }
        .kpi:hover {
            transform: translateY(-4px);
            border-color: color-mix(in srgb, var(--accent) 55%, transparent);
            box-shadow:0 18px 40px rgba(3,8,20,0.6);
        }
        .kpi-ic {
            width:44px; height:44px; flex:none; display:grid; place-items:center;
            font-size:1.35rem; border-radius:13px;
            background: color-mix(in srgb, var(--accent) 18%, rgba(13,22,42,0.9));
            border:1px solid color-mix(in srgb, var(--accent) 45%, transparent);
        }
        .kpi-body { min-width:0; flex:1; }
        .kpi-label {
            font-family:'Rajdhani',sans-serif; font-weight:600; font-size:.72rem;
            letter-spacing:1.2px; text-transform:uppercase; color:#93A6C4;
            white-space:normal; overflow-wrap:anywhere; line-height:1.25;
        }
        .kpi-value {
            font-family:'Playfair Display', serif; font-weight:800;
            font-size:1.2rem; line-height:1.22; color:#EEF4FF; margin-top:3px;
            white-space:normal; overflow-wrap:anywhere; word-break:break-word;
        }

        /* ---- sidebar ---- */
        [data-testid="stSidebar"] {
            background: linear-gradient(190deg, #0C1730 0%, #0A1424 100%);
            border-right: 1px solid rgba(91,231,196,0.18);
        }
        [data-testid="stSidebar"] h2 {
            font-family: 'Cinzel', serif !important; font-weight:700;
            color: #5BE7C4 !important; letter-spacing:.5px;
        }

        /* chart containers as glass panels */
        [data-testid="stPlotlyChart"], .stPlotlyChart {
            background: rgba(14,24,46,0.55);
            border: 1px solid rgba(62,193,211,0.16);
            border-radius: 18px; padding: 8px 10px;
            box-shadow: 0 12px 34px rgba(3,8,20,0.45);
            transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
        }
        [data-testid="stPlotlyChart"]:hover {
            transform: translateY(-3px);
            border-color: rgba(91,231,196,0.42);
            box-shadow: 0 18px 46px rgba(3,8,20,0.6);
        }

        /* ---- custom scrollbars ---- */
        ::-webkit-scrollbar { width:11px; height:11px; }
        ::-webkit-scrollbar-track { background: rgba(8,15,34,0.6); }
        ::-webkit-scrollbar-thumb {
            border-radius: 8px;
            background: linear-gradient(180deg,#3EC1D3,#9D8DF1);
            border: 2px solid rgba(8,15,34,0.6);
        }
        ::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg,#5BE7C4,#B7ACF6); }

        /* ---- footer strip ---- */
        .tv-foot {
            margin: 26px 0 6px; padding: 16px 22px; border-radius: 16px;
            display:flex; align-items:center; justify-content:space-between; gap:14px;
            flex-wrap:wrap;
            background: linear-gradient(120deg, rgba(62,193,211,0.10), rgba(157,141,241,0.10));
            border:1px solid rgba(91,231,196,0.22);
            font-family:'Rajdhani',sans-serif; letter-spacing:1.2px;
            text-transform:uppercase; font-size:.76rem; color:#8FA2C0;
        }
        .tv-foot b { color:#5BE7C4; font-family:'Cinzel',serif; letter-spacing:.5px; }

        footer, #MainMenu { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    """Render the logo hero banner with animated ring and status chips."""
    st.markdown(
        f"""
        <div class="tv-hero">
            <div class="tv-logo-wrap">
                <img src="{_logo_data_uri()}" alt="logo"/>
            </div>
            <div>
                <p class="tv-hero-title">Metropolis Traffic Watch</p>
                <div class="tv-hero-sub">Traffic Violations &nbsp;&#9679;&nbsp; Insight &amp; Enforcement Analytics</div>
                <div class="tv-chips">
                    <span class="tv-chip"><span class="dot"></span>Live Dashboard</span>
                    <span class="tv-chip gold">Montgomery County &bull; MD</span>
                    <span class="tv-chip violet">Open Data Analytics</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def road_divider():
    """Render an animated asphalt divider between sections."""
    st.markdown('<div class="road-div"></div>', unsafe_allow_html=True)


def section_header(icon, title, subtitle):
    """Render a section heading with icon badge, gradient title and caption."""
    st.markdown(
        f"""
        <div class="sec">
            <div class="sec-badge">{icon}</div>
            <div>
                <div class="sec-title">{title}</div>
                <div class="sec-sub">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    """A decorative closing strip for the dashboard."""
    st.markdown(
        """
        <div class="tv-foot">
            <span>&#128663; <b>Metropolis Traffic Watch</b> &nbsp;&bull;&nbsp; Drive Safe, Stay Insightful</span>
            <span>Built with Streamlit &nbsp;&bull;&nbsp; Night-Highway Theme</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
FILTER_COLUMNS = [
    ("subagency", "SubAgency"),
    ("location", "Location"),
    ("vehicle_type", "VehicleType"),
    ("gender", "Gender"),
    ("race", "Race"),
    ("violation_type", "Violation Type"),
    ("violation_category", "Violation Category"),
]
# Real JOIN across all 5 tables, aliased back to Title Case column names.
LOAD_QUERY = """
    SELECT
        v.date_of_stop AS "Date Of Stop",
        v.description AS "Description",
        v.location AS "Location",
        v.latitude AS "Latitude",
        v.longitude AS "Longitude",
        v.violation_type AS "Violation Type",
        v.violation_category AS "Violation Category",
        v.accident AS "Accident",
        v.time_of_day AS "Time Of Day",
        a.sub_agency AS "SubAgency",
        veh.make AS "Make",
        veh.model AS "Model",
        veh.vehicle_type AS "VehicleType",
        d.gender AS "Gender",
        d.race AS "Race"
    FROM violations v
    LEFT JOIN agencies a ON v.agency_id = a.agency_id
    LEFT JOIN vehicles veh ON v.vehicle_id = veh.vehicle_id
    LEFT JOIN demographics d ON v.demographic_id = d.demographic_id
"""


@st.cache_data
def load_data(db_path):
    """Load the joined dataset, cached to Parquet (rebuilt when the DB is newer)."""
    cache = Path(db_path).with_suffix(".cache.parquet")
    if cache.exists() and cache.stat().st_mtime >= Path(db_path).stat().st_mtime:
        return pd.read_parquet(cache)
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            LOAD_QUERY, conn, parse_dates=["Date Of Stop"]
        )
    finally:
        conn.close()
    df["Accident"] = df["Accident"].astype(bool)
    df.to_parquet(cache, index=False)
    return df


# Cap options per multiselect; Streamlit crashes on huge lists (Location ~269K distinct).
MAX_MULTISELECT_OPTIONS = 300


def multiselect_for(df, column, label):
    """One filter checklist widget for a given column."""
    options = df[column].dropna().unique().tolist()
    if len(options) > MAX_MULTISELECT_OPTIONS:
        options = (
            df[column].value_counts()
            .head(MAX_MULTISELECT_OPTIONS).index.tolist()
        )
    options = sorted(options)
    return st.sidebar.multiselect(label, options)


def build_sidebar_filters(df):
    """Draw every filter widget and return the choices made."""
    st.sidebar.header("\U0001F6A7 Filters")
    min_date = df["Date Of Stop"].min()
    max_date = df["Date Of Stop"].max()
    date_range = st.sidebar.date_input("Date range", [min_date, max_date])
    choices = {"date_range": date_range}
    for key, column in FILTER_COLUMNS:
        choices[key] = multiselect_for(df, column, column)
    return choices


def apply_filters(df, choices):
    """Narrow the table down to rows matching every chosen filter."""
    filtered = df.copy()
    if len(choices["date_range"]) == 2:
        start, end = (pd.to_datetime(d) for d in choices["date_range"])
        filtered = filtered[filtered["Date Of Stop"].between(start, end)]
    for key, column in FILTER_COLUMNS:
        if choices[key]:
            filtered = filtered[filtered[column].isin(choices[key])]
    return filtered


def most_frequent(df, column):
    """Most common value in a column, or 'N/A' if the table is empty."""
    return df[column].mode().iloc[0] if not df.empty else "N/A"


def show_summary_metrics(df):
    """Render the five KPI glass cards with icons and accent colours."""
    section_header(
        "\U0001F4CA", "Enforcement Snapshot",
        "Key figures for the current filter selection",
    )
    accidents = int(df["Accident"].sum()) if "Accident" in df else 0
    cards = [
        ("#3EC1D3", "\U0001F6A6", "Total Violations", f"{len(df):,}"),
        ("#E63946", "\U0001F4A5", "Involving Accidents", f"{accidents:,}"),
        ("#F4D35E", "\U0001F4CD", "Top Hotspot",
         str(most_frequent(df, "Location"))[:22]),
        ("#5BE7C4", "\U0001F697", "Most Cited Make",
         str(most_frequent(df, "Make"))),
        ("#9D8DF1", "\U0001F3F7\uFE0F", "Most Cited Model",
         str(most_frequent(df, "Model"))),
    ]
    tiles = "".join(
        f"""<div class="kpi" style="--accent:{color}">
                <div class="kpi-ic">{icon}</div>
                <div class="kpi-body">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value" title="{value}">{value}</div>
                </div>
            </div>"""
        for color, icon, label, value in cards
    )
    st.markdown(f'<div class="kpi-grid">{tiles}</div>',
                unsafe_allow_html=True)


def plot_bar(icon, title, subtitle, series, x_label):
    """Decorative section header + bar chart, reused for count charts."""
    section_header(icon, title, subtitle)
    labels = {"index": x_label, "value": "Count"}
    fig = px.bar(
        series, labels=labels,
        color=series.values, color_continuous_scale=["#3EC1D3", "#9D8DF1"],
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(marker_line_width=0)
    fig.update_xaxes(tickangle=-30, automargin=True,
                     title_standoff=22, tickfont=dict(size=11))
    st.plotly_chart(style_fig(fig), width="stretch")


def show_charts(df):
    """Every chart on the page, in order."""
    road_divider()
    top_violations = df["Description"].value_counts().head(10)
    plot_bar("\U0001F6A6", "Most Common Violations",
             "Top 10 cited offences", top_violations, "Violation")

    road_divider()
    section_header("\U0001F4C8", "Violations Trend Over Time",
                   "Monthly citation volume")
    trend = df.groupby(df["Date Of Stop"].dt.to_period("M")).size()
    trend.index = trend.index.astype(str)
    labels = {"index": "Month", "value": "Violations"}
    fig = px.line(trend, labels=labels, markers=True)
    fig.update_traces(line_color="#5BE7C4", line_width=3,
                      marker=dict(color="#F4D35E", size=6),
                      fill="tozeroy", fillcolor="rgba(91,231,196,0.10)")
    st.plotly_chart(style_fig(fig), width="stretch")

    if "Time Of Day" in df.columns:
        road_divider()
        time_counts = df["Time Of Day"].value_counts()
        plot_bar("\U0001F551", "Violations by Time of Day",
                 "When stops happen", time_counts, "Time of Day")

    road_divider()
    section_header("\U0001F5FA\uFE0F", "Violation Hotspot Map",
                   "Geographic distribution of stops")
    map_data = df.dropna(subset=["Latitude", "Longitude"])
    if not map_data.empty:
        map_data = map_data.rename(
            columns={"Latitude": "lat", "Longitude": "lon"}
        )
        st.map(map_data, color="#3EC1D3")
    else:
        st.info("No valid coordinates in the current filter selection.")


def main():
    st.set_page_config(
        page_title="Metropolis Traffic Watch",
        page_icon=str(LOGO_PATH),
        layout="wide",
    )
    inject_css()
    render_hero()
    road_divider()
    try:
        df = load_data(DB_PATH)
    except pd.errors.DatabaseError:
        st.error(
            f"Could not read '{DB_PATH}'. "
            f"Run data_cleaning.py then build_database.py first."
        )
        return
    filtered_df = apply_filters(df, build_sidebar_filters(df))
    if filtered_df.empty:
        st.warning(
            "No records match the current filter combination. "
            "Filters are combined with AND \u2014 try removing one "
            "(e.g. a Location, Violation Type or a narrow date range) "
            "so it doesn't conflict with your Violation Category choice."
        )
        render_footer()
        return
    show_summary_metrics(filtered_df)
    show_charts(filtered_df)
    render_footer()


if __name__ == "__main__":
    main()
