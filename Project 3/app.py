from __future__ import annotations

import json

import altair as alt
import joblib
import pandas as pd
import streamlit as st

from src.config import MODELS_DIR, PROCESSED_FILE, REPORTS_DIR

st.set_page_config(
    page_title="Rapido Mobility Insights",
    page_icon="assets/favicon.svg",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600;1,700&family=Playfair+Display:ital,wght@0,700;0,800;1,600&family=Poppins:wght@400;500;600&display=swap');

        :root {
            --rapido: #ffd000;        /* Rapido brand yellow */
            --rapido-deep: #ffb700;
            --asphalt: #1b2540;       /* charcoal night streets */
            --brand-2: #7f92ff;       /* signal: info blue (bright on dark) */
            --brand-3: #5b3fd6;
            --go: #06d6a0;            /* signal: go / green */
            --caution: #ffb703;       /* signal: caution / amber */
            --stop: #ff5d73;          /* signal: stop / coral-red */
            --ink: #eef2ff;           /* light text on dark */
            --muted: #9aa7c7;
            --surface: rgba(255,255,255,0.06);
            --surface-brd: rgba(255,255,255,0.12);
        }

        .stApp {
            background:
                radial-gradient(42% 42% at 15% 18%, rgba(255,199,0,0.20), transparent 62%),
                radial-gradient(46% 46% at 86% 12%, rgba(0,209,178,0.22), transparent 62%),
                radial-gradient(52% 52% at 82% 88%, rgba(138,58,255,0.26), transparent 62%),
                radial-gradient(46% 46% at 16% 90%, rgba(20,140,255,0.20), transparent 62%),
                linear-gradient(125deg, #060a15 0%, #0b1028 48%, #140c26 100%);
            background-size: 220% 220%, 220% 220%, 220% 220%, 220% 220%, 100% 100%;
            background-attachment: fixed;
            animation: meshMove 28s ease-in-out infinite alternate;
        }
        @keyframes meshMove {
            0%   { background-position: 0% 0%, 100% 0%, 100% 100%, 0% 100%, 0 0; }
            100% { background-position: 35% 25%, 65% 20%, 60% 75%, 25% 80%, 0 0; }
        }
        html, body, [class*="css"], p, span, label, div, li { font-family: 'Cormorant Garamond', 'Poppins', system-ui, serif; }
        .stApp, .stMarkdown, [data-testid="stMarkdownContainer"] p, label, li { color: #c7d1ee; }
        h1, h2, h3 { font-family: 'Cormorant Garamond', 'Playfair Display', Georgia, serif !important; color: var(--ink); letter-spacing: 0.3px; }
        .block-container { padding-top: 1.4rem; max-width: 1250px; position: relative; z-index: 1; }
        #MainMenu, footer { visibility: hidden; }

        /* Hero banner */
        .hero {
            position: relative; overflow: hidden;
            border-radius: 26px; padding: 34px 40px; margin: 4px 0 26px 0;
            background: linear-gradient(120deg, #0f2027 0%, #203a43 46%, #2c5364 100%);
            box-shadow: 0 22px 55px rgba(15,32,39,0.35);
        }
        .hero::after {
            content: ""; position: absolute; bottom: -90px; left: 32%;
            width: 300px; height: 300px; border-radius: 50%;
            background: radial-gradient(circle, rgba(255,208,0,0.22), transparent 60%);
        }
        /* decorative floral blossoms */
        .blossom {
            position: absolute; z-index: 1; opacity: 0.85;
            animation: floaty 7s ease-in-out infinite;
        }
        .blossom.b1 { top: 16px; right: 34px; width: 46px; animation-delay: 0s; }
        .blossom.b2 { bottom: 20px; right: 120px; width: 30px; opacity: 0.6; animation-delay: 1.5s; }
        .blossom.b3 { top: 60px; right: 180px; width: 22px; opacity: 0.5; animation-delay: 3s; }
        @keyframes floaty { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-9px) rotate(8deg); } }
        .hero-row { position: relative; z-index: 2; display: flex; align-items: center; gap: 26px; }
        .logo-badge {
            position: relative; width: 96px; height: 96px; border-radius: 50%;
            background: radial-gradient(circle at 34% 28%, #2b2b3c 0%, #14141d 62%, #0c0c12 100%);
            display: grid; place-items: center; overflow: visible;
            box-shadow: 0 18px 40px rgba(0,0,0,0.6), inset 0 0 0 2px rgba(255,208,0,0.55), 0 0 22px rgba(255,208,0,0.18);
        }
        .logo-m {
            position: relative; z-index: 2;
            font-family: 'Cormorant Garamond', 'Playfair Display', serif;
            font-weight: 700; font-style: italic; font-size: 4rem; line-height: 1;
            background: linear-gradient(160deg, #fff3c4 0%, #ffd700 45%, #c8961b 100%);
            -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 2px 5px rgba(0,0,0,0.55));
            animation: mGlow 3.4s ease-in-out infinite;
        }
        .logo-wing { position: absolute; top: 50%; width: 42px; height: 48px; z-index: 1;
            transform: translateY(-64%); filter: drop-shadow(0 3px 6px rgba(0,0,0,0.45)); }
        .logo-wing.left { right: 55%; }
        .logo-wing.right { left: 55%; transform: translateY(-64%) scaleX(-1); }
        @keyframes mGlow {
            0%,100% { filter: drop-shadow(0 0 3px rgba(255,208,0,0.30)) drop-shadow(0 2px 5px rgba(0,0,0,0.55)); }
            50%     { filter: drop-shadow(0 0 11px rgba(255,208,0,0.75)) drop-shadow(0 2px 5px rgba(0,0,0,0.55)); }
        }
        .logo-scooter {
            position: absolute; top: -8px; right: -8px; line-height: 0;
            background: linear-gradient(135deg, #2a2a3a, #12121c); border-radius: 12px;
            padding: 4px 5px; border: 2px solid rgba(255,208,0,0.7);
            box-shadow: 0 6px 16px rgba(0,0,0,0.5);
        }
        .logo-scooter svg { display: block; }
        .hero-title { font-weight: 700; font-size: 3rem; margin: 0; color: #fff; line-height: 1.05; letter-spacing: 0.5px; }
        .hero-title .accent {
            background: linear-gradient(90deg, #ffe259, #ffb700);
            -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
        }
        .hero-sub { font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 600; font-size: 1.42rem; margin: 6px 0 10px 0; color: #e6d9b8; letter-spacing: 0.4px; }
        .hero-chips { display: flex; flex-wrap: wrap; gap: 8px; }
        .chip {
            font-family: 'Cormorant Garamond', serif; font-size: 0.92rem; font-weight: 600; color: #232526; padding: 4px 14px;
            border-radius: 999px; background: linear-gradient(120deg, #ffe259, #ffd000); border: 1px solid rgba(255,255,255,0.25);
        }
        /* animated rider crossing the hero */
        .rider {
            position: absolute; bottom: 12px; left: -60px; z-index: 2; font-size: 2rem;
            animation: ride 9s linear infinite; filter: brightness(0) invert(1) drop-shadow(0 4px 6px rgba(0,0,0,0.35));
        }
        @keyframes ride {
            0% { left: -60px; transform: translateY(0); }
            50% { transform: translateY(-4px); }
            100% { left: 105%; transform: translateY(0); }
        }
        .road-dash {
            position: absolute; bottom: 8px; left: 0; width: 100%; height: 3px; z-index: 1;
            background: repeating-linear-gradient(90deg, rgba(255,208,0,0.6) 0 22px, transparent 22px 44px);
        }

        /* Section heading underline */
        h2::after, h3::after {
            content: ""; display: block; width: 54px; height: 4px; margin-top: 8px; border-radius: 999px;
            background: linear-gradient(90deg, var(--rapido), var(--go));
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background: var(--surface); backdrop-filter: blur(8px); border-radius: 18px; padding: 18px 20px 16px 20px;
            box-shadow: 0 14px 32px rgba(0,0,0,0.42); transition: transform 0.18s ease, box-shadow 0.18s ease;
            border: 1px solid var(--surface-brd);
            border-left: 5px solid transparent; border-image: linear-gradient(180deg, var(--rapido), var(--go)) 1;
        }
        [data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 20px 44px rgba(0,0,0,0.55); }
        [data-testid="stMetricLabel"] p { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 1rem !important; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
        [data-testid="stMetricValue"] { font-family: 'Cormorant Garamond', 'Playfair Display', serif; font-weight: 700; color: #ffffff; }

        /* Tabs */
        [data-baseweb="tab-list"] { gap: 6px; background: rgba(255,255,255,0.06); padding: 6px; border-radius: 14px; border: 1px solid var(--surface-brd); }
        [data-baseweb="tab"] { border-radius: 10px; padding: 8px 18px; font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 1.08rem; color: #aeb9d6; }
        [aria-selected="true"][data-baseweb="tab"] { background: linear-gradient(120deg, #3a56e4, #7b2ff7); color: #fff !important; }
        [data-baseweb="tab-highlight"] { background: transparent; }

        /* Buttons */
        .stButton > button, [data-testid="stDownloadButton"] > button {
            border-radius: 12px; border: none; font-weight: 600; padding: 10px 22px; color: #1b2540;
            background: linear-gradient(120deg, var(--rapido), var(--rapido-deep)); box-shadow: 0 10px 24px rgba(255,183,0,0.35);
        }
        .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover { transform: translateY(-2px); color: #1b2540; }

        /* Section headers */
        .sec-head { display: flex; align-items: center; gap: 14px; margin: 26px 0 14px 0; }
        .sec-icon {
            flex: 0 0 auto; width: 46px; height: 46px; border-radius: 14px; display: grid; place-items: center;
            font-size: 1.35rem; color: #fff; box-shadow: 0 8px 20px rgba(27,37,64,0.18);
        }
        .sec-icon.g1 { background: linear-gradient(135deg, #3a56e4, #5b3fd6); }   /* info */
        .sec-icon.g2 { background: linear-gradient(135deg, #06d6a0, #0bbfd6); }   /* go */
        .sec-icon.g3 { background: linear-gradient(135deg, #ffd000, #ffb703); color: #1b2540; }  /* caution */
        .sec-icon.g4 { background: linear-gradient(135deg, #ff5d73, #ff8c42); }   /* stop */
        .sec-eyebrow { font-size: 0.95rem; font-weight: 600; font-style: italic; letter-spacing: 1.5px; text-transform: uppercase; color: #2fd4c4; margin: 0; font-family: 'Cormorant Garamond', serif; }
        .sec-title {
            font-family: 'Cormorant Garamond', 'Playfair Display', serif; font-weight: 700; font-size: 1.75rem; margin: 0; line-height: 1.12; letter-spacing: 0.3px;
            background: linear-gradient(92deg, #ffe9a8 0%, #ffd000 42%, #ff9e5e 100%);
            -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
        }
        .sec-title::after { display: none; }
        .sec-live { margin-left: auto; display: flex; align-items: center; gap: 7px; font-size: 0.68rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--go); }
        .sec-live .pulse { width: 9px; height: 9px; border-radius: 50%; background: var(--go); box-shadow: 0 0 0 0 rgba(6,214,160,0.6); animation: pulse 1.8s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(6,214,160,0.55); } 70% { box-shadow: 0 0 0 10px rgba(6,214,160,0); } 100% { box-shadow: 0 0 0 0 rgba(6,214,160,0); } }

        /* Glass card panels (bordered containers) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255,255,255,0.05); backdrop-filter: blur(8px);
            border: 1px solid var(--surface-brd) !important; border-radius: 20px;
            padding: 8px 10px; box-shadow: 0 16px 36px rgba(0,0,0,0.42);
        }

        /* Inputs */
        [data-testid="stFileUploaderDropzone"] { border-radius: 16px; border: 1.6px dashed rgba(127,146,255,0.5); background: rgba(127,146,255,0.06); }
        [data-baseweb="select"] > div { border-radius: 12px; background: rgba(255,255,255,0.06) !important; border-color: var(--surface-brd) !important; color: #e6ecff; }
        [data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] input { color: #e6ecff !important; }
        [data-baseweb="select"] svg { fill: #9aa7c7; }
        [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] { background: #161c33 !important; border: 1px solid var(--surface-brd); }
        [data-baseweb="popover"] li, [data-baseweb="menu"] li { color: #e6ecff !important; }
        [data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover { background: rgba(255,208,0,0.14) !important; }
        [data-testid="stExpander"] {
            border: 1px solid var(--surface-brd) !important; border-radius: 14px;
            background: rgba(255,255,255,0.05); overflow: hidden;
        }
        [data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: #c7d1ee !important; }
        [data-testid="stExpander"] summary:hover { color: #ffd000 !important; }
        [data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }

        /* Per-tab mini hero banners */
        .mini-hero {
            position: relative; overflow: hidden; border-radius: 20px;
            padding: 22px 28px; margin: 6px 0 20px 0; color: #fff;
        }
        .mini-hero.m1 { background: linear-gradient(120deg, #2b2d6e 0%, #4361ee 55%, #7b2ff7 100%); }
        .mini-hero.m2 { background: linear-gradient(120deg, #0b6e5f 0%, #06d6a0 55%, #12c2e9 100%); }
        .mini-hero.m3 { background: linear-gradient(120deg, #8a4b00 0%, #ffb700 60%, #ff8c42 100%); }
        .mini-hero::after {
            content: ""; position: absolute; top: -50px; right: -30px;
            width: 190px; height: 190px; border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.22), transparent 62%);
        }
        .mini-hero .mh-icon { font-size: 1.7rem; }
        .mini-hero h3 { font-family: 'Cormorant Garamond', 'Playfair Display', serif; font-weight: 700; font-size: 1.9rem; margin: 4px 0 2px 0; color: #fff !important; letter-spacing: 0.4px; }
        .mini-hero h3::after { display: none; }
        .mini-hero p { margin: 0; font-family: 'Cormorant Garamond', serif; font-size: 1.1rem; font-weight: 500; color: rgba(255,255,255,0.92); }

        /* Live scrolling stats ticker */
        .ticker {
            position: relative; overflow: hidden; white-space: nowrap;
            border-radius: 14px; margin: -14px 0 22px 0; padding: 10px 0;
            background: linear-gradient(90deg, #232526, #414345);
            border: 1px solid rgba(255,208,0,0.35);
        }
        .ticker-track { display: inline-block; padding-left: 100%; animation: scroll 26s linear infinite; }
        .ticker:hover .ticker-track { animation-play-state: paused; }
        .ticker-item { color: #fff; font-family: 'Cormorant Garamond', serif; font-size: 1.05rem; font-weight: 600; margin: 0 34px; }
        .ticker-item b { color: #ffd000; }
        .ticker-item .dot { color: #06d6a0; margin-right: 8px; }
        @keyframes scroll { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }

        /* Floating mobility icons overlay */
        .petal-field { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
        .map-grid { position: fixed; inset: 0; z-index: 0; pointer-events: none;
            background-image:
                linear-gradient(rgba(120,180,255,0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(120,180,255,0.05) 1px, transparent 1px);
            background-size: 46px 46px;
            -webkit-mask-image: radial-gradient(circle at 50% 32%, #000 0%, transparent 82%);
            mask-image: radial-gradient(circle at 50% 32%, #000 0%, transparent 82%);
        }
        .petal { position: absolute; top: -70px; opacity: 0.16; animation: fall linear infinite; will-change: transform; filter: brightness(0) invert(1); }
        @keyframes fall {
            0% { transform: translateY(-70px) translateX(0) rotate(0deg); }
            50% { transform: translateY(45vh) translateX(30px) rotate(10deg); }
            100% { transform: translateY(105vh) translateX(-20px) rotate(-8deg); }
        }

        /* Prediction result cards */
        .pred-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 8px 0 18px 0; }
        @media (max-width: 900px) { .pred-grid { grid-template-columns: repeat(2, 1fr); } }
        .pred-card {
            background: rgba(255,255,255,0.06); backdrop-filter: blur(8px);
            border: 1px solid var(--surface-brd); border-radius: 18px; padding: 18px;
            box-shadow: 0 14px 32px rgba(0,0,0,0.42); transition: transform 0.18s ease;
        }
        .pred-card:hover { transform: translateY(-4px); }
        .pred-ic { width: 44px; height: 44px; border-radius: 13px; display: grid; place-items: center; font-size: 1.3rem; margin-bottom: 12px; box-shadow: 0 8px 18px rgba(0,0,0,0.35); }
        .pred-lbl { font-family: 'Cormorant Garamond', serif; font-size: 0.92rem; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; color: var(--muted); margin: 0 0 6px 0; }
        .pred-val { font-family: 'Cormorant Garamond', serif; font-weight: 700; font-size: 1.9rem; color: #fff; margin: 0; line-height: 1; }
        .pred-bar { height: 9px; border-radius: 999px; background: rgba(255,255,255,0.10); overflow: hidden; margin: 8px 0 8px 0; }
        .pred-bar-fill { height: 100%; border-radius: 999px; transition: width 0.6s ease; }
        .pred-risk { font-weight: 600; font-size: 0.92rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    blossom = (
        '<svg class="blossom {cls}" viewBox="0 0 24 32" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M12 0 C5 0 0 5 0 12 C0 21 12 32 12 32 C12 32 24 21 24 12 C24 5 19 0 12 0Z" fill="{fill}"/>'
        '<circle cx="12" cy="12" r="4.5" fill="#12121c"/></svg>'
    )
    scooter_svg = (
        '<svg width="26" height="20" viewBox="0 0 40 28" fill="none" '
        'xmlns="http://www.w3.org/2000/svg" stroke="#ffffff" stroke-width="2.4" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="9" cy="22" r="4"/><circle cx="31" cy="22" r="4"/>'
        '<path d="M9 22 L26 22"/><path d="M26 22 C24 12 27 8 33 8"/>'
        '<path d="M29 8 L37 6"/><path d="M9 22 L13 13 L21 13"/></svg>'
    )
    wing = (
        '<svg class="logo-wing {side}" viewBox="0 0 40 48" xmlns="http://www.w3.org/2000/svg">'
        '<defs><linearGradient id="wg{side}" x1="0" y1="1" x2="1" y2="0">'
        '<stop offset="0%" stop-color="#c8961b"/><stop offset="55%" stop-color="#ffd700"/>'
        '<stop offset="100%" stop-color="#fff3c4"/></linearGradient></defs>'
        '<path fill="url(#wg{side})" d="M38 42 C24 42 12 36 4 24 C14 28 22 28 30 30 '
        'C22 26 14 22 9 14 C18 20 26 22 33 24 C27 20 22 15 20 8 C27 16 33 22 38 28 Z"/></svg>'
    )
    logo = (
        '<div class="logo-badge">'
        + wing.format(side="left")
        + wing.format(side="right")
        + '<span class="logo-m">M</span>'
        + '<span class="logo-scooter">' + scooter_svg + '</span>'
        + '</div>'
    )
    html = (
        '<div class="hero">'
        + blossom.format(cls="b1", fill="#ffe259")
        + blossom.format(cls="b2", fill="#06d6a0")
        + blossom.format(cls="b3", fill="#12c2e9")
        + '<div class="hero-row">'
        + f'<div class="hero-logo">{logo}</div>'
        + '<div>'
        + '<h1 class="hero-title">Rapido <span class="accent">Mobility Insights</span></h1>'
        + '<p class="hero-sub">Intelligent analytics for every ride, driver &amp; fare</p>'
        + '<div class="hero-chips">'
        + '<span class="chip">🚦 Ride Outcomes</span>'
        + '<span class="chip">🔮 Cancellation Risk</span>'
        + '<span class="chip">⏱ Driver Reliability</span>'
        + '<span class="chip">💸 Fare Forecasting</span>'
        + '</div></div></div>'
        + '<div class="road-dash"></div><div class="rider">🛵💨</div>'
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_petals() -> None:
    # project-themed drifting icons instead of flowers
    item = (
        '<span class="petal" style="left:{left}%; font-size:{size}px; '
        'animation-duration:{dur}s; animation-delay:-{delay}s;">{icon}</span>'
    )
    specs = [
        (6, 30, 20, 0, "🛵"), (18, 22, 26, 6, "📍"),
        (32, 26, 22, 3, "🚦"), (46, 24, 28, 9, "🛵"),
        (60, 28, 21, 2, "📍"), (72, 20, 27, 7, "🗺️"),
        (84, 30, 23, 4, "🛵"), (93, 24, 29, 11, "🚦"),
    ]
    icons = "".join(
        item.format(left=l, size=s, dur=d, delay=dl, icon=ic) for l, s, d, dl, ic in specs
    )
    st.markdown(f'<div class="map-grid"></div><div class="petal-field">{icons}</div>', unsafe_allow_html=True)


@st.cache_data
def load_processed_data() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_FILE)


@st.cache_resource
def load_models() -> dict:
    return {
        "ride_outcome": joblib.load(MODELS_DIR / "ride_outcome_model.joblib"),
        "fare": joblib.load(MODELS_DIR / "fare_model.joblib"),
        "customer_cancel": joblib.load(MODELS_DIR / "customer_cancel_model.joblib"),
        "driver_delay": joblib.load(MODELS_DIR / "driver_delay_model.joblib"),
    }


def model_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    # Must match src/train_models.py::_split_features_target, which only drops target columns
    # (it trains on raw booking_date/booking_time/etc., so those cannot be dropped here).
    target_cols = {
        "ride_outcome_target",
        "fare_target",
        "customer_cancel_target",
        "driver_delay_target",
    }

    cols_to_drop = [c for c in target_cols if c in df.columns]
    return df.drop(columns=cols_to_drop)


RUSH_HOURS = {8, 9, 10, 17, 18, 19, 20}


def _feature_template(df: pd.DataFrame) -> pd.DataFrame:
    # Neutral baseline that never borrows existing-data statistics: 0 for numeric
    # columns and a novel "NEW" for text (ignored by the encoder). Every column is
    # then set by user input, derivation, or explicit neutralization in build_manual_row.
    feats = model_feature_frame(df)
    row: dict = {}
    for col in feats.columns:
        row[col] = 0.0 if pd.api.types.is_numeric_dtype(feats[col]) else "NEW"
    return pd.DataFrame([row])


def build_manual_row(df: pd.DataFrame, overrides: dict) -> pd.DataFrame:
    # Start from a neutral template, apply the user's inputs, then recompute the
    # deterministic engineered fields so they stay consistent with the new values.
    row = _feature_template(df)
    for key, value in overrides.items():
        if key in row.columns:
            row.at[0, key] = value

    # Blank out identity/timestamp columns so an unseen ride is not anchored to any
    # real booking/customer/driver; OneHotEncoder(handle_unknown="ignore") maps these
    # novel values to all-zeros, so they add no signal to the prediction.
    novel_ids = {
        "booking_id": "NEW_RIDE",
        "customer_id": "NEW_CUSTOMER",
        "driver_id": "NEW_DRIVER",
        "booking_date": "NEW",
        "booking_time": "NEW",
        "booking_datetime": "NEW",
        "booking_hourly_ts": "NEW",
        "datetime": "NEW",
    }
    for col, placeholder in novel_ids.items():
        if col in row.columns:
            row.at[0, col] = placeholder

    # These flags are near-copies of the cancel/delay targets; zero them out so an
    # unseen ride is predicted from its attributes, not a leaked historical answer.
    for leak_col in ("customer_cancel_flag", "driver_delay_flag"):
        if leak_col in row.columns:
            row.at[0, leak_col] = 0

    # The driver's vehicle equals the ride's vehicle for a matched booking.
    if "vehicle_type_driver" in row.columns and "vehicle_type" in overrides:
        row.at[0, "vehicle_type_driver"] = overrides["vehicle_type"]
    if "preferred_vehicle_type" in row.columns and "vehicle_type" in overrides:
        row.at[0, "preferred_vehicle_type"] = overrides["vehicle_type"]

    if "actual_ride_time_min" in row.columns and "estimated_ride_time_min" in overrides:
        row.at[0, "actual_ride_time_min"] = overrides["estimated_ride_time_min"]

    base_fare = float(row.at[0, "base_fare"]) if "base_fare" in row.columns else 0.0
    surge = float(row.at[0, "surge_multiplier"]) if "surge_multiplier" in row.columns else 1.0
    if "booking_value" in row.columns:
        row.at[0, "booking_value"] = round(base_fare * surge, 2)
    booking_value = float(row.at[0, "booking_value"]) if "booking_value" in row.columns else 0.0

    dist = float(row.at[0, "ride_distance_km"]) if "ride_distance_km" in row.columns else 0.0
    ride_time = float(row.at[0, "actual_ride_time_min"]) if "actual_ride_time_min" in row.columns else 0.0
    if "fare_per_km" in row.columns:
        row.at[0, "fare_per_km"] = booking_value / dist if dist else 0.0
    if "fare_per_min" in row.columns:
        row.at[0, "fare_per_min"] = booking_value / ride_time if ride_time else 0.0

    hour = int(row.at[0, "hour_of_day"]) if "hour_of_day" in row.columns else 0
    if "hour_of_day_time" in row.columns:
        row.at[0, "hour_of_day_time"] = hour
    if "rush_hour_flag" in row.columns:
        row.at[0, "rush_hour_flag"] = 1 if hour in RUSH_HOURS else 0
    if "peak_time_flag" in row.columns:
        row.at[0, "peak_time_flag"] = 1 if hour in RUSH_HOURS else 0

    threshold = float(df["ride_distance_km"].quantile(0.75))
    if "long_distance_flag" in row.columns:
        row.at[0, "long_distance_flag"] = 1 if dist >= threshold else 0

    # Keep the weekday mirrors and weekend flags consistent with the chosen day.
    if "day_of_week" in overrides:
        day = str(overrides["day_of_week"])
        weekend = 1 if day in {"Saturday", "Sunday"} else 0
        for day_col in ("day_of_week", "day_of_week_time"):
            if day_col in row.columns:
                row.at[0, day_col] = day
        for wk_col in ("is_weekend", "is_weekend_time"):
            if wk_col in row.columns:
                row.at[0, wk_col] = weekend

    if "city_pair" in row.columns:
        row.at[0, "city_pair"] = f'{row.at[0, "pickup_location"]}__{row.at[0, "drop_location"]}'

    # Recompute composite scores from the entered components (same formula as the
    # pipeline) so they reflect the user's ride, not the template baseline.
    if "driver_reliability_score" in row.columns:
        acc = float(row.at[0, "acceptance_rate"]) if "acceptance_rate" in row.columns else 0.0
        dly = float(row.at[0, "delay_rate"]) if "delay_rate" in row.columns else 0.0
        drt = float(row.at[0, "avg_driver_rating"]) if "avg_driver_rating" in row.columns else 0.0
        row.at[0, "driver_reliability_score"] = 0.4 * acc + 0.4 * (1 - dly) + 0.2 * (drt / 5)
    if "customer_loyalty_score" in row.columns:
        tb = float(row.at[0, "total_bookings"]) if "total_bookings" in row.columns else 0.0
        max_tb = float(df["total_bookings"].max()) or 1.0
        crt = float(row.at[0, "cancellation_rate"]) if "cancellation_rate" in row.columns else 0.0
        crg = float(row.at[0, "avg_customer_rating"]) if "avg_customer_rating" in row.columns else 0.0
        row.at[0, "customer_loyalty_score"] = 0.4 * (tb / max_tb) + 0.4 * (1 - crt) + 0.2 * (crg / 5)

    # Derive customer ride counts from the entered totals/rates so nothing is borrowed.
    tot_bk = float(row.at[0, "total_bookings"]) if "total_bookings" in row.columns else 0.0
    crate = float(row.at[0, "cancellation_rate"]) if "cancellation_rate" in row.columns else 0.0
    cancelled = round(tot_bk * crate)
    if "cancelled_rides" in row.columns:
        row.at[0, "cancelled_rides"] = cancelled
    if "incomplete_rides" in row.columns:
        row.at[0, "incomplete_rides"] = 0
    if "completed_rides" in row.columns:
        row.at[0, "completed_rides"] = max(int(tot_bk) - cancelled, 0)

    # Mirror the home city and demand surge onto the user's choices.
    for city_col in ("customer_city", "driver_city"):
        if city_col in row.columns and "city" in overrides:
            row.at[0, city_col] = overrides["city"]
    if "avg_surge_multiplier" in row.columns and "surge_multiplier" in overrides:
        row.at[0, "avg_surge_multiplier"] = overrides["surge_multiplier"]

    # Neutralize only the leaked/identity columns (median imputation would reintroduce
    # the ride-outcome answer or a real entity, so these must stay novel/zero).
    neutral = {
        "booking_status": "NEW",
        "incomplete_ride_reason": "None",
    }
    for col, val in neutral.items():
        if col in row.columns:
            row.at[0, col] = val

    # Unprovided-but-legit aggregates the user cannot know: set to 0 so the prediction
    # rests on user inputs only, never on existing-data statistics.
    zero_fill = (
        "total_assigned_rides",
        "accepted_rides",
        "incomplete_rides_driver",
        "delay_count",
        "avg_pickup_delay_min",
        "total_requests",
        "completed_rides_demand",
        "cancelled_rides_demand",
    )
    for col in zero_fill:
        if col in row.columns:
            row.at[0, col] = 0

    return row


def render_manual_inputs(df: pd.DataFrame) -> dict:
    # Collect the human-known fields for an unseen ride; the rest come from the template.
    def opts(col: str) -> list:
        return sorted(df[col].dropna().astype(str).unique().tolist()) if col in df.columns else []

    overrides: dict = {}
    st.markdown("**Trip details**")
    t1, t2, t3 = st.columns(3)
    overrides["city"] = t1.text_input("City", value="")
    overrides["pickup_location"] = t2.text_input("Pickup location", value="")
    overrides["drop_location"] = t3.text_input("Drop location", value="")

    t4, t5, t6 = st.columns(3)
    overrides["vehicle_type"] = t4.selectbox("Vehicle type", opts("vehicle_type"))
    overrides["ride_distance_km"] = t5.number_input(
        "Ride distance (km)", min_value=0.1, value=5.0, step=0.5
    )
    overrides["estimated_ride_time_min"] = t6.number_input(
        "Ride time (min)", min_value=1.0, value=20.0, step=1.0
    )

    t7, t8, t9 = st.columns(3)
    overrides["hour_of_day"] = t7.slider("Hour of day", 0, 23, 12)
    overrides["traffic_level"] = t8.selectbox("Traffic level", opts("traffic_level"))
    overrides["weather_condition"] = t9.selectbox("Weather", opts("weather_condition"))

    st.markdown("**Pricing**")
    p1, p2 = st.columns(2)
    overrides["base_fare"] = p1.number_input(
        "Base fare (₹)", min_value=0.0, value=100.0, step=5.0
    )
    overrides["surge_multiplier"] = p2.number_input(
        "Surge multiplier", min_value=1.0, max_value=5.0, value=1.0, step=0.1
    )

    st.markdown("**Customer & driver history** (drives cancel / delay risk)")
    d1, d2, d3 = st.columns(3)
    overrides["customer_age"] = d1.number_input("Customer age", min_value=16, max_value=90, value=30)
    overrides["cancellation_rate"] = d2.slider("Customer cancel rate", 0.0, 1.0, 0.1)
    overrides["avg_customer_rating"] = d3.slider("Customer rating", 1.0, 5.0, 4.0)

    d4, d5, d6 = st.columns(3)
    overrides["acceptance_rate"] = d4.slider("Driver acceptance rate", 0.0, 1.0, 0.9)
    overrides["delay_rate"] = d5.slider("Driver delay rate", 0.0, 1.0, 0.1)
    overrides["avg_driver_rating"] = d6.slider("Driver rating", 1.0, 5.0, 4.0)

    with st.expander("Advanced inputs (optional)"):
        a1, a2, a3 = st.columns(3)
        overrides["driver_experience_years"] = a1.number_input(
            "Driver experience (years)", min_value=0, max_value=50, value=5
        )
        overrides["avg_wait_time_min"] = a2.number_input(
            "Avg wait time (min)", min_value=0.0, value=10.0, step=1.0
        )
        overrides["total_bookings"] = a3.number_input(
            "Customer total bookings", min_value=0, value=10
        )

        a4, a5, a6 = st.columns(3)
        overrides["customer_signup_days_ago"] = a4.number_input(
            "Customer signup (days ago)", min_value=0, value=180
        )
        overrides["demand_level"] = a5.selectbox("Demand level", opts("demand_level"))
        overrides["driver_age"] = a6.number_input(
            "Driver age", min_value=18, max_value=75, value=35
        )

        a7, a8, a9 = st.columns(3)
        overrides["day_of_week"] = a7.selectbox("Day of week", opts("day_of_week"))
        overrides["season"] = a8.selectbox("Season", opts("season"))
        overrides["is_holiday"] = 1 if a9.checkbox("Holiday") else 0

        a10, _, _ = st.columns(3)
        overrides["customer_gender"] = a10.selectbox("Customer gender", opts("customer_gender"))

    return overrides


def validate_manual_inputs(df: pd.DataFrame, ov: dict) -> list[str]:
    # Compare each entry against the existing-data categories/ranges and flag entries
    # that are empty, mistyped, out-of-range, unseen, or mutually inconsistent.
    issues: list[str] = []

    def known(col: str) -> set:
        return set(df[col].dropna().astype(str)) if col in df.columns else set()

    for col, label in (("city", "City"), ("pickup_location", "Pickup location"), ("drop_location", "Drop location")):
        val = str(ov.get(col, "")).strip()
        if not val:
            continue  # empty required fields blank the output instead of warning
        if not any(ch.isalpha() for ch in val):
            issues.append(f"⚠️ {label} '{val}' isn't a valid place name (needs letters).")
        elif val not in known(col):
            issues.append(f"ℹ️ {label} '{val}' is new — treated as an unknown location.")

    pickup = str(ov.get("pickup_location", "")).strip()
    drop = str(ov.get("drop_location", "")).strip()
    if pickup and drop and pickup == drop:
        issues.append("⚠️ Pickup and drop are the same location.")

    for col, label in (
        ("ride_distance_km", "Ride distance"),
        ("estimated_ride_time_min", "Ride time"),
        ("base_fare", "Base fare"),
    ):
        if col in ov and col in df.columns:
            lo, hi = float(df[col].min()), float(df[col].max())
            v = float(ov[col])
            if v < lo or v > hi:
                issues.append(f"⚠️ {label} {v:g} is outside the data range [{lo:g}–{hi:g}] — may be unreliable.")

    if ov.get("avg_customer_rating", 0) >= 4.5 and ov.get("cancellation_rate", 0) >= 0.5:
        issues.append("⚠️ High customer rating with a high cancel rate is inconsistent.")
    if ov.get("avg_driver_rating", 0) >= 4.5 and ov.get("delay_rate", 0) >= 0.5:
        issues.append("⚠️ High driver rating with a high delay rate is inconsistent.")

    return issues


REQUIRED_FIELDS = {"city": "City", "pickup_location": "Pickup location", "drop_location": "Drop location"}


def missing_required_fields(ov: dict) -> list[str]:
    return [label for col, label in REQUIRED_FIELDS.items() if not str(ov.get(col, "")).strip()]


def blank_prediction_cards() -> None:
    labels = ["Ride Outcome", "Predicted Fare", "Customer Cancel Risk", "Driver Delay Risk"]
    cards = "".join(
        f'<div class="pred-card"><p class="pred-lbl">{lbl}</p><p class="pred-val">—</p></div>' for lbl in labels
    )
    st.markdown(f'<div class="pred-grid">{cards}</div>', unsafe_allow_html=True)


def section_header(icon: str, title: str, eyebrow: str, gradient: str = "g1", live: bool = False) -> None:
    live_html = '<div class="sec-live"><span class="pulse"></span>Live</div>' if live else ""
    st.markdown(
        f'<div class="sec-head"><div class="sec-icon {gradient}">{icon}</div>'
        f'<div><p class="sec-eyebrow">{eyebrow}</p><p class="sec-title">{title}</p></div>'
        f'{live_html}</div>',
        unsafe_allow_html=True,
    )


def tab_banner(icon: str, title: str, subtitle: str, variant: str) -> None:
    st.markdown(
        f'<div class="mini-hero {variant}"><span class="mh-icon">{icon}</span>'
        f'<h3>{title}</h3><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def render_ticker(df: pd.DataFrame) -> None:
    total = len(df)
    cancel_rate = df["booking_status"].eq("Cancelled").mean()
    avg_value = df["booking_value"].mean()
    avg_dist = df["ride_distance_km"].mean()
    peak_hour = (
        df.assign(c=df["booking_status"].eq("Cancelled").astype(int))
        .groupby("hour_of_day")["c"].mean().idxmax()
    )
    scooter = (
        '<svg width="20" height="14" viewBox="0 0 40 28" fill="none" stroke="#ffffff" '
        'stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
        'style="vertical-align:middle;margin-right:4px;">'
        '<circle cx="9" cy="22" r="4"/><circle cx="31" cy="22" r="4"/>'
        '<path d="M9 22 L26 22"/><path d="M26 22 C24 12 27 8 33 8"/>'
        '<path d="M29 8 L37 6"/><path d="M9 22 L13 13 L21 13"/></svg>'
    )
    items = [
        f"{scooter}<b>{total:,}</b> total rides analysed",
        f"❌ Cancellation rate <b>{cancel_rate:.1%}</b>",
        f"💰 Avg booking value <b>₹{avg_value:.0f}</b>",
        f"📍 Avg ride distance <b>{avg_dist:.1f} km</b>",
        f"⏰ Peak cancellation hour <b>{int(peak_hour)}:00</b>",
        "⚡ Powered by 4 Random-Forest models",
    ]
    spans = "".join(
        f'<span class="ticker-item"><span class="dot">●</span>{it}</span>' for it in items
    )
    # duplicate the run so the loop is seamless
    st.markdown(
        f'<div class="ticker"><div class="ticker-track">{spans}{spans}</div></div>',
        unsafe_allow_html=True,
    )


def render_metrics_summary() -> None:
    metrics_path = REPORTS_DIR / "metrics.json"
    if not metrics_path.exists():
        st.warning("Training metrics not found. Run: python -m src.run_pipeline")
        return

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ride Outcome Accuracy", f"{metrics['ride_outcome']['accuracy']:.2%}")
    c2.metric("Fare RMSE", f"{metrics['fare']['rmse']:.2f}")
    c3.metric("Customer Cancel AUC", f"{metrics['customer_cancel'].get('roc_auc', 0):.3f}")
    c4.metric("Driver Delay AUC", f"{metrics['driver_delay'].get('roc_auc', 0):.3f}")


_CHART_BG = "#12172b"


def _chart_theme(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeWidth=0, fill=_CHART_BG)
        .configure(background=_CHART_BG)
        .configure_axis(
            labelColor="#9aa7c7", titleColor="#c7d1ee", gridColor="rgba(255,255,255,0.06)",
            domainColor="rgba(255,255,255,0.12)", tickColor="rgba(255,255,255,0.12)",
            labelFont="Poppins", titleFont="Poppins", titleFontWeight=600,
        )
    )


def cancellations_chart(hourly: pd.DataFrame) -> alt.Chart:
    grad = alt.Gradient(
        gradient="linear",
        stops=[
            alt.GradientStop(color="rgba(255,93,115,0.02)", offset=0),
            alt.GradientStop(color="rgba(255,93,115,0.55)", offset=1),
        ],
        x1=1, x2=1, y1=1, y2=0,
    )
    base = alt.Chart(hourly).encode(
        x=alt.X("hour_of_day:Q", title="Hour of Day", scale=alt.Scale(nice=False)),
        y=alt.Y("cancelled:Q", title="Cancellation Rate", axis=alt.Axis(format="%")),
        tooltip=[
            alt.Tooltip("hour_of_day:Q", title="Hour"),
            alt.Tooltip("cancelled:Q", title="Cancel rate", format=".1%"),
        ],
    )
    area = base.mark_area(line={"color": "#ff5d73", "strokeWidth": 3}, color=grad, interpolate="monotone")
    points = base.mark_circle(size=70, color="#ffd000", stroke="#12172b", strokeWidth=1.5)
    return _chart_theme((area + points).properties(height=300))


def distance_fare_chart(df: pd.DataFrame) -> alt.Chart:
    sample = df[["ride_distance_km", "booking_value"]].dropna()
    if len(sample) > 4000:
        sample = sample.sample(4000, random_state=1)
    chart = (
        alt.Chart(sample)
        .mark_circle(size=42, opacity=0.55)
        .encode(
            x=alt.X("ride_distance_km:Q", title="Ride Distance (km)"),
            y=alt.Y("booking_value:Q", title="Fare (₹)"),
            color=alt.Color(
                "booking_value:Q",
                scale=alt.Scale(scheme="viridis"),
                legend=alt.Legend(title="Fare", labelColor="#9aa7c7", titleColor="#c7d1ee"),
            ),
            tooltip=[
                alt.Tooltip("ride_distance_km:Q", title="Distance", format=".1f"),
                alt.Tooltip("booking_value:Q", title="Fare", format=".0f"),
            ],
        )
        .properties(height=300)
    )
    return _chart_theme(chart)


def _risk_tone(prob: float) -> tuple[str, str]:
    if prob >= 0.6:
        return "#ff5d73", "High"
    if prob >= 0.3:
        return "#ffb703", "Medium"
    return "#06d6a0", "Low"


def prediction_cards(ride_outcome: str, fare: float, cust_prob: float, driver_prob: float) -> None:
    cust_col, cust_lbl = _risk_tone(cust_prob)
    drv_col, drv_lbl = _risk_tone(driver_prob)

    sw = 'fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    ic_flag = f'<svg viewBox="0 0 24 24" width="22" height="22" {sw}><path d="M7 3v18"/><path d="M7 4h11l-3 4 3 4H7"/></svg>'
    ic_fare = f'<svg viewBox="0 0 24 24" width="22" height="22" {sw}><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M9 10h4M9 13h4M12 10c2 0 2 6-2 6l3 0"/></svg>'
    ic_person = f'<svg viewBox="0 0 24 24" width="22" height="22" {sw}><circle cx="12" cy="8" r="3.2"/><path d="M6 20c0-4 12-4 12 0"/></svg>'
    ic_scooter = (
        f'<svg viewBox="0 0 40 28" width="24" height="18" {sw}>'
        '<circle cx="9" cy="22" r="4"/><circle cx="31" cy="22" r="4"/>'
        '<path d="M9 22 L26 22"/><path d="M26 22 C24 12 27 8 33 8"/>'
        '<path d="M29 8 L37 6"/><path d="M9 22 L13 13 L21 13"/></svg>'
    )

    def gauge(color: str, prob: float, label: str) -> str:
        pct = max(3, round(prob * 100))
        return (
            f'<div class="pred-bar"><div class="pred-bar-fill" style="width:{pct}%;'
            f'background:linear-gradient(90deg,{color},{color}cc);"></div></div>'
            f'<div class="pred-risk" style="color:{color};">{label} · {prob:.1%}</div>'
        )

    html = (
        '<div class="pred-grid">'
        f'<div class="pred-card"><div class="pred-ic" style="background:linear-gradient(135deg,#3a56e4,#7b2ff7);">{ic_flag}</div>'
        f'<p class="pred-lbl">Ride Outcome</p><p class="pred-val">{ride_outcome}</p></div>'
        f'<div class="pred-card"><div class="pred-ic" style="background:linear-gradient(135deg,#06d6a0,#0bbfd6);">{ic_fare}</div>'
        f'<p class="pred-lbl">Predicted Fare</p><p class="pred-val">₹{fare:.0f}</p></div>'
        f'<div class="pred-card"><div class="pred-ic" style="background:linear-gradient(135deg,{cust_col},#ff8c42);">{ic_person}</div>'
        f'<p class="pred-lbl">Customer Cancel Risk</p>{gauge(cust_col, cust_prob, cust_lbl)}</div>'
        f'<div class="pred-card"><div class="pred-ic" style="background:linear-gradient(135deg,{drv_col},#ff8c42);">{ic_scooter}</div>'
        f'<p class="pred-lbl">Driver Delay Risk</p>{gauge(drv_col, driver_prob, drv_lbl)}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def main() -> None:
    inject_styles()
    render_petals()
    render_hero()

    if not PROCESSED_FILE.exists() or not (MODELS_DIR / "fare_model.joblib").exists():
        st.error("Model artifacts are missing. Run: python -m src.run_pipeline")
        st.stop()

    df = load_processed_data()
    models = load_models()

    render_ticker(df)

    tab1, tab2, tab3 = st.tabs(["📊 Business KPIs", "🎯 Single Ride Prediction", "📦 Batch Prediction"])

    with tab1:
        tab_banner("📊", "Business KPIs", "Model accuracy, live operations and demand trends at a glance", "m1")
        section_header("📈", "Model Performance", "Predictive Accuracy", "g1")
        render_metrics_summary()

        section_header("🧭", "Operational Snapshot", "Live Business Pulse", "g2", live=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Bookings", f"{len(df):,}")
        k2.metric("Cancellation Rate", f"{(df['booking_status'].eq('Cancelled').mean()):.2%}")
        k3.metric("Avg Booking Value", f"{df['booking_value'].mean():.2f}")
        k4.metric("Avg Ride Distance (km)", f"{df['ride_distance_km'].mean():.2f}")

        col_a, col_b = st.columns(2)
        with col_a:
            section_header("🕒", "Cancellations by Hour", "Demand Timing", "g4")
            hourly = (
                df.assign(cancelled=df["booking_status"].eq("Cancelled").astype(int))
                .groupby("hour_of_day", as_index=False)["cancelled"]
                .mean()
            )
            with st.container(border=True):
                st.altair_chart(cancellations_chart(hourly), width='stretch')
        with col_b:
            section_header("💠", "Distance vs Fare", "Pricing Spread", "g3")
            with st.container(border=True):
                st.altair_chart(distance_fare_chart(df), width='stretch')

    with tab2:
        tab_banner("🎯", "Single Ride Prediction", "Score any historical booking across all four models instantly", "m2")
        section_header("🎯", "Single Ride Prediction", "Booking-Level Intelligence", "g1")

        mode = st.radio(
            "Input source",
            ["📁 Existing booking", "✍️ Manual entry (new ride)"],
            horizontal=True,
        )

        if mode == "📁 Existing booking":
            booking_id = st.selectbox("Select Booking ID", options=df["booking_id"].astype(str).tolist()[:5000])
            row = df.loc[df["booking_id"].astype(str) == booking_id].head(1)
            row_features = model_feature_frame(row)
            missing = []
        else:
            overrides = render_manual_inputs(df)
            missing = missing_required_fields(overrides)
            for msg in validate_manual_inputs(df, overrides):
                (st.info if msg.startswith("ℹ️") else st.warning)(msg)
            row = build_manual_row(df, overrides)
            row_features = row

        if st.button("Run Predictions", type="primary"):
            if missing:
                st.info("Fill required field(s) to see predictions: " + ", ".join(missing) + ".")
                blank_prediction_cards()
            else:
                ride_outcome = models["ride_outcome"].predict(row_features)[0]
                fare_pred = float(models["fare"].predict(row_features)[0])
                cust_prob = float(models["customer_cancel"].predict_proba(row_features)[:, 1][0])
                driver_prob = float(models["driver_delay"].predict_proba(row_features)[:, 1][0])

                prediction_cards(str(ride_outcome), fare_pred, cust_prob, driver_prob)

                with st.expander("View full booking record"):
                    st.dataframe(row.T.astype(str), width='stretch')

    with tab3:
        tab_banner("📦", "Batch Prediction", "Upload a CSV and score thousands of rides in one pass", "m3")
        section_header("📦", "Batch Prediction", "Bulk Scoring via CSV", "g2")
        st.write("Upload a CSV with the same columns as the processed dataset (or at least required features).")
        uploaded = st.file_uploader("Upload File", type=["csv"])

        if uploaded is not None:
            batch_df = pd.read_csv(uploaded)
            batch_features = model_feature_frame(batch_df)

            out = batch_df.copy()
            out["pred_ride_outcome"] = models["ride_outcome"].predict(batch_features)
            out["pred_fare"] = models["fare"].predict(batch_features)
            out["pred_customer_cancel_prob"] = models["customer_cancel"].predict_proba(batch_features)[:, 1]
            out["pred_driver_delay_prob"] = models["driver_delay"].predict_proba(batch_features)[:, 1]

            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Rows Scored", f"{len(out):,}")
            b2.metric("Avg Predicted Fare", f"₹{out['pred_fare'].mean():.0f}")
            b3.metric("High Cancel Risk", f"{(out['pred_customer_cancel_prob'] >= 0.6).mean():.1%}")
            b4.metric("High Delay Risk", f"{(out['pred_driver_delay_prob'] >= 0.6).mean():.1%}")

            with st.container(border=True):
                st.dataframe(out.head(50), width='stretch')
            st.download_button(
                "Download Predictions",
                data=out.to_csv(index=False),
                file_name="rapido_predictions.csv",
                mime="text/csv",
            )


if __name__ == "__main__":
    main()
