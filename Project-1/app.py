# app.py - the dashboard. Reads ncaafb.db and shows filterable/searchable tables.
# Run with: streamlit run app.py

import sqlite3
import pandas as pd
import streamlit as st
import config

st.set_page_config(
    page_title="NCAA Football Explorer",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.html(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
    :root {
        --bg-1: #170f3e;         /* deep indigo night */
        --bg-2: #241463;         /* royal violet */
        --bg-3: #0f2f45;         /* deep teal */
        --ink: #eaefff;          /* near-white text on dark */
        --ink-soft: #b9c2ef;     /* muted lavender text */
        --sapphire: #a9b6ff;     /* light royal accent for headings */
        --sapphire-deep: #cdd6ff;
        --cyan: #22d3ee;         /* bright aqua accent */
        --violet: #8b5cff;       /* vivid violet accent */
        --gold: #f4c95d;         /* champagne gold */
        --gold-deep: #e0a92e;
        --card: rgba(255,255,255,0.06);
        --line: rgba(255,255,255,0.10);
        --white: #ffffff;
    }

    html, body, [class*="css"], .stApp,
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
    button, input, textarea, select,
    .stMarkdown, .stText, [data-testid="stWidgetLabel"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* readable text everywhere on the dark canvas */
    .main .block-container, .main .block-container p,
    .main .block-container li, .main .block-container span,
    .main .block-container label, [data-testid="stWidgetLabel"] p,
    .stMarkdown, .stText {
        color: #e7ecff;
    }

    .stApp {
        background:
            repeating-linear-gradient(90deg,
                rgba(255,255,255,0.035) 0 2px, transparent 2px 96px),
            radial-gradient(1200px 620px at 6% -8%, rgba(139,92,255,0.35), transparent 55%),
            radial-gradient(1100px 560px at 100% 0%, rgba(34,211,238,0.22), transparent 52%),
            radial-gradient(900px 500px at 50% 120%, rgba(244,201,93,0.12), transparent 55%),
            linear-gradient(135deg, var(--bg-1) 0%, var(--bg-2) 48%, var(--bg-3) 100%);
        color: var(--ink);
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background:
            radial-gradient(700px 300px at 20% 0%, rgba(124,92,255,0.35), transparent 60%),
            linear-gradient(180deg, #241a6e 0%, #2c2286 55%, #1b1550 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebarNav"] { background: transparent; }
    .stSidebar .block-container { padding-top: 1.1rem; }

    .brand-box {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1.1rem 0.9rem 1.2rem 0.9rem;
        margin: 0.2rem 0 1.2rem 0;
        border-radius: 24px;
        background: linear-gradient(150deg, rgba(255,255,255,0.10), rgba(124,92,255,0.10));
        border: 1px solid rgba(255,255,255,0.14);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.10), 0 18px 40px rgba(15,10,60,0.35);
        overflow: hidden;
    }

    .brand-box::before {
        content: "";
        position: absolute;
        top: -40%; left: -30%;
        width: 160%; height: 90%;
        background: radial-gradient(circle, rgba(23,195,214,0.30), transparent 60%);
        filter: blur(6px);
    }

    .brand-logo {
        position: relative;
        width: 96px;
        height: 96px;
        border-radius: 26px;
        object-fit: cover;
        padding: 6px;
        background: linear-gradient(135deg, rgba(244,201,93,0.30), rgba(23,195,214,0.25));
        box-shadow: 0 14px 30px rgba(23, 195, 214, 0.30);
    }

    .brand-text {
        position: relative;
        font-family: 'Sora', sans-serif;
        font-size: 1.16rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        color: #f6f8ff;
        text-transform: uppercase;
        text-align: center;
        line-height: 1.2;
        margin-top: 0.75rem;
        background: linear-gradient(90deg, #ffffff, #d9f6ff 55%, #f4c95d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .brand-sub {
        position: relative;
        font-size: 0.68rem;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        color: #b9c2ff;
        text-align: center;
        margin-top: 0.3rem;
        font-weight: 600;
    }

    .brand-rule {
        position: relative;
        width: 46px;
        height: 3px;
        margin-top: 0.7rem;
        border-radius: 3px;
        background: linear-gradient(90deg, var(--cyan), var(--gold));
    }

    /* ---------- Sidebar radio nav ---------- */
    .stRadio > div { gap: 0.4rem; }

    .stRadio [role="radiogroup"] > label {
        padding: 0.68rem 0.85rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        color: #eef1ff;
        font-weight: 600;
        transition: all 0.22s ease;
    }

    .stRadio [role="radiogroup"] > label:hover {
        border-color: rgba(23,195,214,0.75);
        background: linear-gradient(90deg, rgba(23,195,214,0.16), rgba(124,92,255,0.14));
        transform: translateX(3px);
    }

    .stRadio [role="radiogroup"] label div { color: #eef1ff !important; }

    /* ---------- Metrics (stadium scoreboard look) ---------- */
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        font-family: 'Sora', 'Consolas', monospace;
        color: #ffe9a8 !important;
        font-weight: 800;
        font-size: 2.2rem !important;
        letter-spacing: 0.04em;
        text-shadow: 0 0 10px rgba(244,201,93,0.65),
                     0 0 22px rgba(244,201,93,0.35);
    }

    [data-testid="stMetricLabel"] {
        color: #8fe9f2;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        text-shadow: 0 0 8px rgba(34,211,238,0.4);
    }

    .stMetric {
        position: relative;
        background:
            radial-gradient(120% 80% at 50% -10%, rgba(34,211,238,0.10), transparent 60%),
            linear-gradient(160deg, #150f3d 0%, #0f0b30 100%);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 18px 38px rgba(8, 4, 40, 0.45),
                    inset 0 0 0 1px rgba(34,211,238,0.10),
                    inset 0 2px 22px rgba(0,0,0,0.5);
        overflow: hidden;
    }

    /* faint scoreboard scan-lines */
    .stMetric::after {
        content: "";
        position: absolute;
        inset: 0;
        background: repeating-linear-gradient(
            180deg, rgba(255,255,255,0.035) 0 1px, transparent 1px 4px);
        pointer-events: none;
    }

    .stMetric::before {
        content: "";
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 5px;
        background: linear-gradient(180deg, var(--cyan), var(--violet), var(--gold));
    }

    /* ---------- Tables ---------- */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--line);
        box-shadow: 0 18px 38px rgba(8, 4, 40, 0.35);
    }

    div[data-testid="stDataFrameContainer"] {
        box-shadow: 0 18px 38px rgba(8, 4, 40, 0.35);
        border-radius: 16px;
    }

    /* ---------- Layout ---------- */
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    .main .block-container {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 28px;
        padding: 1.8rem 1.8rem 2.2rem 1.8rem;
        box-shadow: 0 30px 70px rgba(6, 3, 32, 0.45);
        backdrop-filter: blur(10px);
    }

    /* ---------- Typography ---------- */
    h1, h2, h3 {
        font-family: 'Sora', sans-serif;
        color: var(--sapphire-deep);
        letter-spacing: 0.01em;
        font-weight: 800;
    }

    h1 {
        font-size: 2.35rem;
        margin-bottom: 0.35rem;
        background: linear-gradient(90deg, #ffffff 0%, #a9b6ff 45%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* accent underline under the page title */
    h1::after {
        content: "";
        display: block;
        width: 92px;
        height: 5px;
        margin-top: 0.55rem;
        border-radius: 5px;
        background: linear-gradient(90deg, var(--cyan), var(--violet) 55%, var(--gold));
    }

    h2 { font-size: 1.5rem; }

    .stSubheader, [data-testid="stHeading"] h3 {
        color: var(--sapphire);
        font-weight: 700;
    }

    p, li, .stCaption { color: var(--ink-soft); }

    /* ---------- Inputs ---------- */
    .stButton > button {
        border-radius: 14px;
        background: linear-gradient(135deg, var(--cyan) 0%, var(--violet) 100%);
        color: #ffffff;
        font-weight: 700;
        border: none;
        box-shadow: 0 10px 22px rgba(124,92,255,0.28);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 28px rgba(124,92,255,0.38);
    }

    .stSelectbox div[data-baseweb="select"] > div,
    .stTextInput div[data-baseweb="input"],
    .stNumberInput div[data-baseweb="input"] {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.16);
        background: rgba(255,255,255,0.08);
        color: #eaefff;
    }

    .stSelectbox label, .stTextInput label,
    .stNumberInput label, .stSlider label, .stRadio label {
        color: #d7ddff !important;
        font-weight: 600;
    }

    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background: var(--violet);
    }

    /* hero banner on pages */
    .hero {
        position: relative;
        border-radius: 24px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.4rem;
        background:
            radial-gradient(600px 200px at 90% 0%, rgba(23,195,214,0.30), transparent 60%),
            linear-gradient(120deg, #2c2286 0%, #3a2f9e 45%, #6a4bd6 100%);
        color: #f6f8ff;
        box-shadow: 0 22px 50px rgba(36, 26, 110, 0.28);
        overflow: hidden;
    }

    .hero h1 {
        color: #ffffff;
        -webkit-text-fill-color: #ffffff;
        margin-bottom: 0.25rem;
    }

    .hero h1::after { display: none; }

    .hero-sub {
        color: #cfd6ff;
        font-size: 0.98rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }

    /* football field yard-line strip (decorative) */
    .field-strip {
        height: 12px;
        margin-top: 1rem;
        border-radius: 8px;
        background:
            repeating-linear-gradient(90deg,
                rgba(255,255,255,0.85) 0 2px,
                transparent 2px 30px),
            linear-gradient(90deg, #1f7a4d 0%, #2fa968 50%, #1f7a4d 100%);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.25);
        opacity: 0.9;
    }

    /* themed sidebar footer */
    .side-foot {
        margin-top: 1.4rem;
        padding: 0.9rem 0.9rem 1rem 0.9rem;
        border-radius: 18px;
        text-align: center;
        background: linear-gradient(150deg, rgba(255,255,255,0.06), rgba(139,92,255,0.10));
        border: 1px solid rgba(255,255,255,0.12);
    }

    .side-foot .foot-emoji {
        font-size: 1.35rem;
        letter-spacing: 0.35rem;
    }

    .side-foot .foot-title {
        margin-top: 0.35rem;
        font-family: 'Sora', sans-serif;
        font-weight: 700;
        font-size: 0.82rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #e7ecff;
    }

    .side-foot .foot-note {
        margin-top: 0.2rem;
        font-size: 0.68rem;
        letter-spacing: 0.10em;
        color: #b9c2ef;
    }

    /* chip row of NCAA football accents */
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.2rem 0 1.2rem 0;
    }

    .chip {
        padding: 0.4rem 0.85rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #eef2ff;
        background: linear-gradient(135deg, rgba(34,211,238,0.18), rgba(139,92,255,0.22));
        border: 1px solid rgba(255,255,255,0.16);
    }

    /* ============ Unique decorative polish ============ */

    /* animated shimmer on gradient page titles */
    h1 {
        background-size: 220% auto;
        animation: titleSheen 6s linear infinite;
    }
    @keyframes titleSheen {
        0%   { background-position: 0% center; }
        100% { background-position: 220% center; }
    }

    /* soft fade-up entrance for the main panel */
    .main .block-container {
        animation: fadeUp 0.6s ease both;
    }
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* gentle float + glow on the sidebar logo */
    .brand-logo {
        animation: floatLogo 4.5s ease-in-out infinite;
    }
    @keyframes floatLogo {
        0%, 100% { transform: translateY(0); box-shadow: 0 14px 30px rgba(34,211,238,0.30); }
        50%      { transform: translateY(-5px); box-shadow: 0 22px 40px rgba(139,92,255,0.40); }
    }

    /* moving light-sweep across the hero banner */
    .hero::after {
        content: "";
        position: absolute;
        top: 0; left: -60%;
        width: 45%; height: 100%;
        background: linear-gradient(100deg, transparent, rgba(255,255,255,0.16), transparent);
        transform: skewX(-18deg);
        animation: heroSweep 5.5s ease-in-out infinite;
    }
    @keyframes heroSweep {
        0%   { left: -60%; }
        55%  { left: 120%; }
        100% { left: 120%; }
    }

    /* football-tick accent before every subheader */
    [data-testid="stHeading"] h3::before,
    h3::before {
        content: "";
        display: inline-block;
        width: 10px;
        height: 18px;
        margin-right: 0.6rem;
        vertical-align: -3px;
        border-radius: 3px;
        background: linear-gradient(180deg, var(--cyan), var(--violet) 55%, var(--gold));
        box-shadow: 0 0 10px rgba(34,211,238,0.55);
    }

    /* metric cards lift + glow on hover */
    .stMetric {
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .stMetric:hover {
        transform: translateY(-4px);
        box-shadow: 0 26px 48px rgba(8, 4, 40, 0.5),
                    0 0 0 1px rgba(34,211,238,0.35);
    }

    /* selected nav item gets an aqua->violet highlight */
    .stRadio [role="radiogroup"] > label[data-checked="true"],
    .stRadio [role="radiogroup"] > label:has(input:checked) {
        border-color: rgba(34,211,238,0.85);
        background: linear-gradient(90deg, rgba(34,211,238,0.22), rgba(139,92,255,0.24));
        box-shadow: inset 3px 0 0 0 var(--cyan), 0 8px 18px rgba(8,4,40,0.35);
    }

    /* custom scrollbar in the football palette */
    ::-webkit-scrollbar { width: 11px; height: 11px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.04); }
    ::-webkit-scrollbar-thumb {
        border-radius: 999px;
        background: linear-gradient(180deg, var(--cyan), var(--violet));
        border: 2px solid rgba(23,15,62,0.9);
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--violet), var(--gold));
    }

    /* tidy caption styling */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #b9c2ef !important;
        font-style: italic;
    }

    /* decorative footer at the bottom of every page */
    .app-foot {
        margin-top: 2.2rem;
        padding: 1.1rem 1.2rem;
        border-radius: 20px;
        text-align: center;
        color: #cdd6ff;
        font-size: 0.82rem;
        letter-spacing: 0.06em;
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(139,92,255,0.10));
        border: 1px solid rgba(255,255,255,0.10);
    }
    .app-foot b {
        background: linear-gradient(90deg, #22d3ee, #8b5cff 55%, #f4c95d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* thin team-color accent bar pinned to the very top */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 5px;
        z-index: 1000;
        background: linear-gradient(90deg, var(--cyan), var(--violet) 50%, var(--gold));
    }

    /* chips lift on hover */
    .chip { transition: transform 0.18s ease, box-shadow 0.18s ease; }
    .chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(8, 4, 40, 0.4);
    }

    /* themed info / warning / error boxes */
    [data-testid="stAlert"] {
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.16);
        background: linear-gradient(135deg, rgba(34,211,238,0.12), rgba(139,92,255,0.14));
        color: #eaefff;
    }
    [data-testid="stAlert"] * { color: #eaefff !important; }

    /* dark dropdown popover so options stay readable on the dark theme */
    div[data-baseweb="popover"] ul,
    div[data-baseweb="menu"] {
        background: #1b1350 !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] li { color: #eaefff !important; }
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="menu"] li:hover {
        background: linear-gradient(90deg, rgba(34,211,238,0.22), rgba(139,92,255,0.24)) !important;
    }

    /* rounded corners for the stadium map */
    [data-testid="stDeckGlJsonChart"] { border-radius: 16px; overflow: hidden; }

    /* slider track in the football palette */
    .stSlider [data-baseweb="slider"] div[data-testid="stTickBar"] { display: none; }
    .stSlider [data-baseweb="slider"] > div > div {
        background: linear-gradient(90deg, var(--cyan), var(--violet)) !important;
    }

    /* ===== one-time welcome shower when the dashboard opens ===== */
    .welcome-fx {
        position: fixed;
        inset: 0;
        pointer-events: none;
        overflow: hidden;
        z-index: 9999;
        animation: fxFade 0.8s ease 4.4s forwards;
    }
    @keyframes fxFade { to { opacity: 0; visibility: hidden; } }

    .welcome-fx span {
        position: absolute;
        top: -10%;
        font-size: 1.7rem;
        filter: drop-shadow(0 6px 10px rgba(8,4,40,0.45));
        animation: fxFall 4s cubic-bezier(.4,.05,.5,1) forwards;
        will-change: transform, opacity;
    }
    @keyframes fxFall {
        0%   { transform: translateY(-12vh) rotate(0deg)   scale(0.7); opacity: 0; }
        12%  { opacity: 1; }
        100% { transform: translateY(112vh) rotate(340deg) scale(1);   opacity: 0; }
    }

    .welcome-fx .flash {
        position: absolute;
        left: 50%; top: 34%;
        transform: translate(-50%, -50%);
        font-family: 'Sora', sans-serif;
        font-weight: 800;
        font-size: 2.6rem;
        letter-spacing: 0.04em;
        white-space: nowrap;
        background: linear-gradient(90deg, #22d3ee, #8b5cff 55%, #f4c95d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(139,92,255,0.35);
        animation: flashPop 2.6s ease forwards;
    }
    @keyframes flashPop {
        0%   { opacity: 0; transform: translate(-50%,-50%) scale(0.8); }
        18%  { opacity: 1; transform: translate(-50%,-50%) scale(1.04); }
        70%  { opacity: 1; transform: translate(-50%,-50%) scale(1); }
        100% { opacity: 0; transform: translate(-50%,-58%) scale(1); }
    }

    </style>
    """
)


# One-time football + confetti shower shown when the dashboard first opens
if "welcomed" not in st.session_state:
    st.session_state["welcomed"] = True
    _fx_emojis = ["\U0001F3C8", "\U0001F3C6", "\u2728", "\U0001F31F",
                  "\U0001F3C8", "\u2728", "\U0001F3C8", "\U0001F3C6",
                  "\U0001F31F", "\U0001F3C8", "\u2728", "\U0001F3C8",
                  "\U0001F3C6", "\u2728", "\U0001F3C8", "\U0001F31F"]
    _fx_spans = "".join(
        f'<span style="left:{4 + i * 6}%;'
        f'animation-delay:{(i % 8) * 0.28:.2f}s;'
        f'animation-duration:{3.4 + (i % 5) * 0.35:.2f}s;'
        f'font-size:{1.3 + (i % 4) * 0.35:.2f}rem;">{e}</span>'
        for i, e in enumerate(_fx_emojis)
    )
    st.markdown(
        f'<div class="welcome-fx">{_fx_spans}'
        f'<div class="flash">\U0001F3C8 Welcome to NCAA Football Explorer</div></div>',
        unsafe_allow_html=True,
    )


def run_sql(query, params=()):
    """Run any SQL query and return the result as a table (DataFrame).
    Uses try/except so a bad query shows a friendly message, not a crash."""
    try:
        conn = sqlite3.connect(config.DB_FILE)
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Could not run the query: {e}")
        return pd.DataFrame()


def options(column, table):
    """Get the unique values in a column, to fill a dropdown filter.
    (Used by many pages, so we write it once here instead of repeating it.)"""
    df = run_sql(f"SELECT DISTINCT {column} FROM {table} "
                 f"WHERE {column} IS NOT NULL ORDER BY {column}")
    return df[column].tolist() if not df.empty else []


def page_hero(icon, title, subtitle=""):
    """Decorative banner shown at the top of each page (styling only)."""
    st.markdown(
        f"""
        <div class="hero">
            <h1>{icon} {title}</h1>
            <div class="hero-sub">{subtitle}</div>
            <div class="field-strip"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- The menu on the left side ---
# Drop your own logo into the assets/ folder as "logo.png" (or .jpg/.jpeg/.webp/.svg)
# and it will be used automatically. Otherwise the built-in football "M" logo shows.
import os
import base64


def _find_logo():
    for name in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp",
                 "logo.svg", "football_m_logo.svg"):
        path = os.path.join("assets", name)
        if os.path.exists(path):
            return path
    return None


def _logo_data_uri(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = "svg+xml" if ext == "svg" else ext
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{encoded}"


_logo_path = _find_logo()
_logo_html = (
    f'<img class="brand-logo" src="{_logo_data_uri(_logo_path)}" alt="logo">'
    if _logo_path else ""
)

st.sidebar.markdown(
    f"""
    <div class="brand-box">
        {_logo_html}
        <div class="brand-text">NCAA Football</div>
        <div class="brand-sub">Explorer</div>
        <div class="brand-rule"></div>
    </div>
    """,
    unsafe_allow_html=True,
)
page = st.sidebar.radio("Choose a page", [
    "Home", "Teams Explorer", "Players Explorer", "Player Stats",
    "Season & Schedule", "Rankings", "Venues", "Coaches"
])

st.sidebar.markdown(
    """
    <div class="field-strip"></div>
    <div class="side-foot">
        <div class="foot-emoji">\U0001F3C8 \U0001F3DF\uFE0F \U0001F3C6</div>
        <div class="foot-title">NCAA Football</div>
        <div class="foot-note">Teams &bull; Players &bull; Rankings</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =====================  HOME  =====================
if page == "Home":
    st.markdown(
        """
        <div class="hero">
            <h1>\U0001F3C8 Home Dashboard</h1>
            <div class="hero-sub">A quick, elegant overview of all the data we collected.</div>
            <div class="field-strip"></div>
        </div>
        <div class="chip-row">
            <span class="chip">\U0001F3C8 Gridiron Stats</span>
            <span class="chip">\U0001F3DF\uFE0F Venues</span>
            <span class="chip">\U0001F3C6 Rankings</span>
            <span class="chip">\U0001F465 Rosters</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Teams",   run_sql("SELECT COUNT(*) AS n FROM teams")["n"][0])
    col2.metric("Players", run_sql("SELECT COUNT(*) AS n FROM players")["n"][0])
    col3.metric("Seasons", run_sql("SELECT COUNT(*) AS n FROM seasons")["n"][0])

    st.subheader("All teams and their conferences")
    st.dataframe(run_sql("""
        SELECT teams.name, teams.market, conferences.name AS conference
        FROM teams
        LEFT JOIN conferences ON teams.conference_id = conferences.conference_id
    """))

    st.subheader("All active players")
    st.dataframe(run_sql("""
        SELECT first_name, last_name, position, eligibility
        FROM players WHERE status = 'ACT'
    """))

    st.subheader("Season years and their status")
    st.dataframe(run_sql("SELECT year, status, type_code FROM seasons ORDER BY year"))


# =====================  TEAMS EXPLORER  =====================
elif page == "Teams Explorer":
    page_hero("\U0001F3DF\uFE0F", "Teams Explorer",
              "Browse programs by conference, division and home state.")

    # three filters + one search box (as required)
    conf_list  = options("name", "conferences")
    div_list   = options("name", "divisions")
    state_list = options("state", "venues")

    c1, c2, c3 = st.columns(3)
    conf  = c1.selectbox("Conference", ["All"] + conf_list)
    div   = c2.selectbox("Division", ["All"] + div_list)
    state = c3.selectbox("State", ["All"] + state_list)
    search = st.text_input("Search by team name or alias")

    # build the query safely with parameters (?) instead of gluing strings
    query = """
        SELECT teams.team_id, teams.market, teams.name, teams.alias,
               conferences.name AS conference, divisions.name AS division,
               venues.name AS venue, venues.state
        FROM teams
        LEFT JOIN conferences ON teams.conference_id = conferences.conference_id
        LEFT JOIN divisions   ON teams.division_id   = divisions.division_id
        LEFT JOIN venues      ON teams.venue_id      = venues.venue_id
        WHERE 1=1
    """
    params = []
    if conf != "All":
        query += " AND conferences.name = ?"; params.append(conf)
    if div != "All":
        query += " AND divisions.name = ?"; params.append(div)
    if state != "All":
        query += " AND venues.state = ?"; params.append(state)
    if search:
        query += " AND (teams.name LIKE ? OR teams.alias LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    teams_df = run_sql(query, tuple(params))
    st.dataframe(teams_df)

    # option to view a team's roster by selecting a team
    st.subheader("View a team's roster")
    if not teams_df.empty:
        chosen = st.selectbox("Select a team", teams_df["name"])
        team_id = teams_df.loc[teams_df["name"] == chosen, "team_id"].iloc[0]
        st.dataframe(run_sql("""
            SELECT first_name, last_name, position, eligibility, height, weight, status
            FROM players WHERE team_id = ? ORDER BY position
        """, (team_id,)))


# =====================  PLAYERS EXPLORER  =====================
elif page == "Players Explorer":
    page_hero("\U0001F464", "Players Explorer",
              "Search the roster by position, status and eligibility.")

    pos_list    = options("position", "players")
    status_list = options("status", "players")
    elig_list   = options("eligibility", "players")

    c1, c2, c3 = st.columns(3)
    pos    = c1.selectbox("Position", ["All"] + pos_list)
    status = c2.selectbox("Status", ["All"] + status_list)
    elig   = c3.selectbox("Eligibility", ["All"] + elig_list)
    search = st.text_input("Search by player name or team name")

    query = """
        SELECT players.first_name, players.last_name, players.position,
               players.eligibility, players.height, players.weight,
               players.status, teams.name AS team
        FROM players
        LEFT JOIN teams ON players.team_id = teams.team_id
        WHERE 1=1
    """
    params = []
    if pos != "All":
        query += " AND players.position = ?"; params.append(pos)
    if status != "All":
        query += " AND players.status = ?"; params.append(status)
    if elig != "All":
        query += " AND players.eligibility = ?"; params.append(elig)
    if search:
        query += (" AND (players.first_name LIKE ? OR players.last_name LIKE ? "
                  "OR teams.name LIKE ?)")
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]

    st.dataframe(run_sql(query, tuple(params)))

    # Most common positions overall, and how each is spread across teams
    st.subheader("Most common positions")
    st.dataframe(run_sql("""
        SELECT position, COUNT(*) AS player_count
        FROM players
        GROUP BY position
        ORDER BY player_count DESC
    """))

    st.subheader("Position distribution by team")
    st.dataframe(run_sql("""
        SELECT teams.name AS team, players.position, COUNT(*) AS player_count
        FROM players
        LEFT JOIN teams ON players.team_id = teams.team_id
        GROUP BY teams.team_id, players.position
        ORDER BY teams.name, player_count DESC
    """))


# =====================  PLAYER STATS  =====================
elif page == "Player Stats":
    page_hero("\U0001F4CA", "Player Statistics",
              "Rushing, receiving and return stats for each player, by season.")
    st.caption("Rushing, receiving and return stats for each player, by season.")

    st.dataframe(run_sql("""
        SELECT players.first_name, players.last_name, seasons.year,
               teams.name AS team,
               player_statistics.games_played,
               player_statistics.rushing_yards,
               player_statistics.rushing_touchdowns,
               player_statistics.receiving_yards,
               player_statistics.receiving_touchdowns,
               player_statistics.kick_return_yards,
               player_statistics.fumbles
        FROM player_statistics
        LEFT JOIN players ON player_statistics.player_id = players.player_id
        LEFT JOIN teams   ON player_statistics.team_id   = teams.team_id
        LEFT JOIN seasons ON player_statistics.season_id = seasons.season_id
        ORDER BY player_statistics.rushing_yards DESC
    """))

    st.subheader("Players who appear in multiple seasons")
    st.dataframe(run_sql("""
        SELECT players.first_name, players.last_name,
               COUNT(DISTINCT player_statistics.season_id) AS seasons_played
        FROM player_statistics
        LEFT JOIN players ON player_statistics.player_id = players.player_id
        GROUP BY player_statistics.player_id
        HAVING seasons_played > 1
        ORDER BY seasons_played DESC
    """))


# =====================  SEASON & SCHEDULE  =====================
elif page == "Season & Schedule":
    page_hero("\U0001F5D3\uFE0F", "Season & Schedule",
              "Explore each season and pull up its weekly rankings.")

    year_list = options("year", "seasons")
    status_list = options("status", "seasons")

    c1, c2 = st.columns(2)
    year_pick = c1.selectbox("Year", ["All"] + year_list)
    status_pick = c2.selectbox("Status", ["All"] + status_list)

    query = ("SELECT season_id, year, start_date, end_date, status, type_code "
             "FROM seasons WHERE 1=1")
    params = []
    if year_pick != "All":
        query += " AND year = ?"; params.append(year_pick)
    if status_pick != "All":
        query += " AND status = ?"; params.append(status_pick)
    st.dataframe(run_sql(query, tuple(params)))

    # joinable with rankings for season-specific rankings
    st.subheader("Rankings for a chosen season")
    if year_list:
        year_choice = st.selectbox("Pick a season year", year_list)
        st.dataframe(run_sql("""
            SELECT rankings.week, teams.name AS team, rankings.rank, rankings.points
            FROM rankings
            JOIN seasons ON rankings.season_id = seasons.season_id
            LEFT JOIN teams ON rankings.team_id = teams.team_id
            WHERE seasons.year = ?
            ORDER BY rankings.week, rankings.rank
        """, (year_choice,)))


# =====================  RANKINGS  =====================
elif page == "Rankings":
    page_hero("\U0001F3C6", "Weekly Rankings",
              "Poll standings, first-place votes and top-5 history.")

    poll_list   = options("poll_name", "rankings")
    season_list = options("year", "seasons")
    week_list   = options("week", "rankings")

    c1, c2, c3, c4 = st.columns(4)
    poll_pick   = c1.selectbox("Poll", ["All"] + poll_list)
    season_pick = c2.selectbox("Season", ["All"] + season_list)
    week_pick   = c3.selectbox("Week", ["All"] + week_list)
    rank_max    = c4.slider("Show rank 1 through", 1, 25, 25)   # rank range

    query = """
        SELECT rankings.poll_name, rankings.week, teams.name AS team, rankings.rank,
               rankings.prev_rank, rankings.points, rankings.fp_votes,
               rankings.wins, rankings.losses
        FROM rankings
        LEFT JOIN teams   ON rankings.team_id = teams.team_id
        LEFT JOIN seasons ON rankings.season_id = seasons.season_id
        WHERE rankings.rank <= ?
    """
    params = [rank_max]
    if poll_pick != "All":
        query += " AND rankings.poll_name = ?"; params.append(poll_pick)
    if season_pick != "All":
        query += " AND seasons.year = ?"; params.append(season_pick)
    if week_pick != "All":
        query += " AND rankings.week = ?"; params.append(week_pick)
    query += " ORDER BY rankings.week, rankings.rank"
    st.dataframe(run_sql(query, tuple(params)))

    # search a specific team's ranking history
    st.subheader("Search a team's ranking history")
    team_search = st.text_input("Team name contains")
    if team_search:
        st.dataframe(run_sql("""
            SELECT teams.name AS team, rankings.week, rankings.rank, rankings.points
            FROM rankings JOIN teams ON rankings.team_id = teams.team_id
            WHERE teams.name LIKE ? ORDER BY rankings.week
        """, (f"%{team_search}%",)))

    st.subheader("Teams ranked Top 5 across multiple seasons")
    st.dataframe(run_sql("""
        SELECT teams.name AS team, COUNT(DISTINCT rankings.season_id) AS seasons_in_top5
        FROM rankings
        LEFT JOIN teams ON rankings.team_id = teams.team_id
        WHERE rankings.rank <= 5
        GROUP BY rankings.team_id
        HAVING seasons_in_top5 > 1
        ORDER BY seasons_in_top5 DESC
    """))

    st.subheader("Average ranking points per team by season")
    st.dataframe(run_sql("""
        SELECT teams.name AS team, seasons.year, AVG(rankings.points) AS avg_points
        FROM rankings
        LEFT JOIN teams ON rankings.team_id = teams.team_id
        LEFT JOIN seasons ON rankings.season_id = seasons.season_id
        GROUP BY rankings.team_id, rankings.season_id
        ORDER BY seasons.year, avg_points DESC
    """))

    st.subheader("First-place votes received, by team")
    st.dataframe(run_sql("""
        SELECT teams.name AS team, SUM(rankings.fp_votes) AS total_fp_votes
        FROM rankings
        LEFT JOIN teams ON rankings.team_id = teams.team_id
        GROUP BY rankings.team_id
        ORDER BY total_fp_votes DESC
    """))


# =====================  VENUES  =====================
elif page == "Venues":
    page_hero("\U0001F3DF\uFE0F", "Venue Directory",
              "Stadiums by state, capacity, surface and roof type.")

    state_list = options("state", "venues")
    roof_list  = options("roof_type", "venues")

    c1, c2 = st.columns(2)
    state_pick = c1.selectbox("State", ["All"] + state_list)
    roof_pick  = c2.selectbox("Roof type", ["All"] + roof_list)

    query = "SELECT name, city, state, capacity, surface, roof_type FROM venues WHERE 1=1"
    params = []
    if state_pick != "All":
        query += " AND state = ?"; params.append(state_pick)
    if roof_pick != "All":
        query += " AND roof_type = ?"; params.append(roof_pick)
    query += " ORDER BY capacity DESC"
    st.dataframe(run_sql(query, tuple(params)))

    # a map of the stadiums, using their latitude and longitude
    st.subheader("Stadiums on the map")
    map_data = run_sql("""
        SELECT latitude, longitude FROM venues
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    if not map_data.empty:
        st.map(map_data)
    else:
        st.info("No location data yet. Run get_data.py to load stadium coordinates.")


# =====================  COACHES  =====================
elif page == "Coaches":
    page_hero("\U0001F9E2", "Coaches Table",
              "Find head and position coaches across every program.")

    search = st.text_input("Search by coach name or team")
    query = """
        SELECT coaches.full_name, coaches.position, teams.name AS team
        FROM coaches LEFT JOIN teams ON coaches.team_id = teams.team_id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (coaches.full_name LIKE ? OR teams.name LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    st.dataframe(run_sql(query, tuple(params)))


# --- Decorative footer shown on every page ---
st.markdown(
    """
    <div class="app-foot">
        \U0001F3C8 <b>NCAA Football Explorer</b> &nbsp;&bull;&nbsp;
        Gridiron data, beautifully explored &nbsp;&bull;&nbsp; \U0001F3DF\uFE0F \U0001F3C6
    </div>
    """,
    unsafe_allow_html=True,
)
