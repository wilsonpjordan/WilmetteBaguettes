"""
================================================================
  FANTASY BASEBALL DRAFT DASHBOARD  |  9-Cat Yahoo League
  Single-file Streamlit app — no other files needed.

  HOW TO RUN:
    1. pip install streamlit pandas numpy plotly pybaseball scipy
    2. streamlit run dashboard.py
================================================================
"""

import os
import warnings
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats as scipy_stats

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fantasy Baseball Dashboard",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background:#1c2333; border-radius:8px; padding:10px;
    }
    .tag-breakout  { background:#1a472a; color:#21C354; padding:3px 8px;
                     border-radius:4px; font-size:12px; font-weight:bold; }
    .tag-regression{ background:#5c1a1a; color:#FF4B4B; padding:3px 8px;
                     border-radius:4px; font-size:12px; font-weight:bold; }
    .tag-neutral   { background:#2a2a2a; color:#aaa;    padding:3px 8px;
                     border-radius:4px; font-size:12px; }
    .target-card   { background:#1c2333; border-radius:8px; padding:12px;
                     margin-bottom:8px; border-left:4px solid #4fc3f7; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  DEMO DATA  (fallback if pybaseball unavailable)
# ─────────────────────────────────────────────────────────────

def _demo_batting() -> pd.DataFrame:
    players = [
        "Mookie Betts","Freddie Freeman","Ronald Acuña Jr.","Juan Soto",
        "Yordan Alvarez","Trea Turner","Corey Seager","Kyle Tucker",
        "Julio Rodriguez","Francisco Lindor","Pete Alonso","Nolan Arenado",
        "Paul Goldschmidt","Bryce Harper","Mike Trout","Shohei Ohtani",
        "Vladimir Guerrero Jr.","Bo Bichette","Austin Riley","Gunnar Henderson",
        "Elly De La Cruz","Bobby Witt Jr.","Corbin Carroll","Matt Olson",
        "Spencer Steer","Adolis Garcia","Randy Arozarena","Cedric Mullins",
        "Ian Happ","Willy Adames","Jackson Merrill","Wyatt Langford",
        "Junior Caminero","Jordan Walker","Evan Carter","James Wood",
    ]
    teams = ["LAD","ATL","ATL","NYY","HOU","PHI","TEX","HOU","SEA","NYM",
             "NYM","STL","STL","PHI","LAA","LAD","TOR","TOR","ATL","BAL",
             "CIN","KC","ARI","ATL","CIN","TEX","TB","BAL","CHC","MIL",
             "SD","TEX","TB","STL","TEX","WSH"]
    positions = ["OF","1B","OF","OF","DH","SS","SS","OF","OF","SS",
                 "1B","3B","1B","1B","OF","DH","1B","SS","3B","SS",
                 "SS","SS","OF","1B","2B","OF","OF","OF","OF","SS",
                 "OF","OF","3B","OF","OF","OF"]
    n = len(players)
    frames = []
    for yr in [2021, 2022, 2023, 2024, 2025]:
        np.random.seed(42 + yr)
        # 2025 has fewer games (partial season sim)
        g_max = 90 if yr == 2025 else 162
        pa_max = 380 if yr == 2025 else 700
        pa_min = 200 if yr == 2025 else 450
        df = pd.DataFrame({
            "Name": players, "Team": teams, "Position": positions, "Season": yr,
            "Age":     np.array([a + (yr - 2021) for a in np.random.randint(22, 33, n)]),
            "G":       np.random.randint(55 if yr==2025 else 110, g_max, n),
            "PA":      np.random.randint(pa_min, pa_max, n),
            "HR":      np.random.randint(4 if yr==2025 else 8, 22 if yr==2025 else 46, n),
            "R":       np.random.randint(25 if yr==2025 else 55, 60 if yr==2025 else 115, n),
            "RBI":     np.random.randint(22 if yr==2025 else 50, 58 if yr==2025 else 115, n),
            "SB":      np.random.randint(0, 28 if yr==2025 else 55, n),
            "AVG":     np.round(np.random.uniform(.228, .322, n), 3),
            "OBP":     np.round(np.random.uniform(.298, .422, n), 3),
            "SLG":     np.round(np.random.uniform(.378, .592, n), 3),
            "wOBA":    np.round(np.random.uniform(.308, .432, n), 3),
            "xwOBA":   np.round(np.random.uniform(.303, .422, n), 3),
            "xBA":     np.round(np.random.uniform(.218, .308, n), 3),
            "wRC+":    np.random.randint(85, 172, n),
            "BB%":     np.round(np.random.uniform(.058, .182, n), 3),
            "K%":      np.round(np.random.uniform(.138, .312, n), 3),
            "BABIP":   np.round(np.random.uniform(.262, .368, n), 3),
            "Hard%":   np.round(np.random.uniform(.285, .562, n), 3),
            "Barrel%": np.round(np.random.uniform(.048, .192, n), 3),
            "SwStr%":  np.round(np.random.uniform(.068, .172, n), 3),
            "maxEV":   np.round(np.random.uniform(100, 118, n), 1),
            "EV":      np.round(np.random.uniform(85, 95, n), 1),
            "LA":      np.round(np.random.uniform(5, 20, n), 1),
            "Spd":     np.round(np.random.uniform(2.4, 9.2, n), 1),
            "Pull%":   np.round(np.random.uniform(.32, .52, n), 3),
            "GB%":     np.round(np.random.uniform(.33, .52, n), 3),
            "FB%":     np.round(np.random.uniform(.25, .44, n), 3),
        })
        df["OPS"] = np.round(df["OBP"] + df["SLG"], 3)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _demo_pitching() -> pd.DataFrame:
    players = [
        "Spencer Strider","Zack Wheeler","Corbin Burnes","Max Fried",
        "Sandy Alcantara","Kevin Gausman","Logan Webb","Shane Bieber",
        "Framber Valdez","Pablo Lopez","Dylan Cease","Yu Darvish",
        "Gerrit Cole","Justin Verlander","Clayton Kershaw",
        "Blake Snell","Tyler Glasnow","Shane McClanahan",
        "Luis Castillo","Nestor Cortes","Joe Musgrove","Freddy Peralta",
        "George Kirby","MacKenzie Gore","Hunter Greene","Reid Detmers",
        "Sonny Gray","Chris Sale","Tarik Skubal","Logan Gilbert",
        "Paul Skenes","Colt Keith","Jacob deGrom","Kodai Senga",
    ]
    teams = ["ATL","PHI","MIL","ATL","MIA","SF","SF","CLE","HOU","MIN",
             "CWS","SD","NYY","NYY","LAD","SD","TB","TB","SEA",
             "NYY","SD","MIL","SEA","WSH","CIN","LAA","STL","ATL","DET","SEA",
             "PIT","DET","TEX","NYM"]
    n = len(players)
    frames = []
    for yr in [2021, 2022, 2023, 2024, 2025]:
        np.random.seed(99 + yr)
        ip_max = 90 if yr == 2025 else 200
        ip_min = 45 if yr == 2025 else 100
        ip   = np.random.randint(ip_min, ip_max, n).astype(float)
        so   = (ip * np.random.uniform(7.5, 12.5, n) / 9).astype(int)
        bb   = (ip * np.random.uniform(1.8,  4.2, n) / 9).astype(int)
        era  = np.round(np.random.uniform(2.4, 5.0, n), 2)
        xfip = np.round(era + np.random.uniform(-0.6, 0.9, n), 2)
        df = pd.DataFrame({
            "Name": players, "Team": teams, "Season": yr,
            "Age":     np.array([a + (yr-2021) for a in np.random.randint(23, 37, n)]),
            "G":       np.random.randint(10 if yr==2025 else 20, 18 if yr==2025 else 33, n),
            "GS":      np.random.randint(9  if yr==2025 else 18, 17 if yr==2025 else 32, n),
            "IP":      np.round(ip, 1),
            "W":       np.random.randint(3 if yr==2025 else 5, 10 if yr==2025 else 19, n),
            "SO":      so,
            "BB":      bb,
            "ERA":     era,
            "WHIP":    np.round(np.random.uniform(0.90, 1.44, n), 2),
            "FIP":     np.round(xfip + np.random.uniform(-0.2, 0.2, n), 2),
            "xFIP":    xfip,
            "SIERA":   np.round(xfip + np.random.uniform(-0.15, 0.25, n), 2),
            "K%":      np.round(so / (so + bb + ip * 2.5), 3),
            "BB%":     np.round(bb / (so + bb + ip * 2.5), 3),
            "BABIP":   np.round(np.random.uniform(.262, .328, n), 3),
            "LOB%":    np.round(np.random.uniform(.61, .84, n), 3),
            "SwStr%":  np.round(np.random.uniform(.088, .192, n), 3),
            "Hard%":   np.round(np.random.uniform(.268, .462, n), 3),
            "Barrel%": np.round(np.random.uniform(.028, .112, n), 3),
            "HR/FB":   np.round(np.random.uniform(.068, .162, n), 3),
            "GB%":     np.round(np.random.uniform(.32, .58, n), 3),
            "FB%":     np.round(np.random.uniform(.22, .42, n), 3),
            "CSW%":    np.round(np.random.uniform(.26, .36, n), 3),
        })
        df["K/9"]   = np.round(df["SO"] / df["IP"] * 9, 2)
        df["BB/9"]  = np.round(df["BB"] / df["IP"] * 9, 2)
        df["K-BB%"] = np.round(df["K%"] - df["BB%"], 3)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# ─────────────────────────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────────────────────────

YEARS     = [2021, 2022, 2023, 2024, 2025]
CACHE_DIR = "data_cache"
MIN_PA    = 100   # lower threshold to capture 2025 partial season
MIN_IP    = 20


@st.cache_data(show_spinner="⚾ Loading baseball data...")
def load_data():
    os.makedirs(CACHE_DIR, exist_ok=True)

    bat_files = sorted([f for f in os.listdir(CACHE_DIR)
                        if f.startswith("batting_") and f.endswith(".csv")])
    pit_files = sorted([f for f in os.listdir(CACHE_DIR)
                        if f.startswith("pitching_") and f.endswith(".csv")])

    if bat_files and pit_files:
        bat_all = pd.concat(
            [pd.read_csv(os.path.join(CACHE_DIR, f)) for f in bat_files],
            ignore_index=True)
        pit_all = pd.concat(
            [pd.read_csv(os.path.join(CACHE_DIR, f)) for f in pit_files],
            ignore_index=True)
    else:
        try:
            from pybaseball import batting_stats, pitching_stats, cache as pb_cache
            pb_cache.enable()
            bat_frames, pit_frames = [], []
            for yr in YEARS:
                try:
                    b = batting_stats(yr, qual=MIN_PA)
                    b["Season"] = yr
                    bat_frames.append(b)
                    p = pitching_stats(yr, qual=MIN_IP)
                    p["Season"] = yr
                    pit_frames.append(p)
                except Exception:
                    pass
            if bat_frames and pit_frames:
                bat_all = pd.concat(bat_frames, ignore_index=True)
                pit_all = pd.concat(pit_frames, ignore_index=True)
                for yr in YEARS:
                    b = bat_all[bat_all["Season"] == yr]
                    p = pit_all[pit_all["Season"] == yr]
                    if not b.empty:
                        b.to_csv(os.path.join(CACHE_DIR, f"batting_{yr}.csv"), index=False)
                    if not p.empty:
                        p.to_csv(os.path.join(CACHE_DIR, f"pitching_{yr}.csv"), index=False)
            else:
                raise RuntimeError("no frames")
        except Exception:
            bat_all = _demo_batting()
            pit_all = _demo_pitching()

    if "Position" not in bat_all.columns:
        bat_all["Position"] = "—"

    latest  = int(bat_all["Season"].max())
    bat_rec = deep_analysis(score_hitters(bat_all[bat_all["Season"] == latest].copy()), bat_all, "hitter")
    pit_rec = deep_analysis(score_pitchers(pit_all[pit_all["Season"] == latest].copy()), pit_all, "pitcher")

    return bat_all, pit_all, bat_rec, pit_rec, latest


# ─────────────────────────────────────────────────────────────
#  SCORING ENGINE
# ─────────────────────────────────────────────────────────────

def _z(s: pd.Series) -> pd.Series:
    mu, sd = s.mean(), s.std()
    return pd.Series(0.0, index=s.index) if sd == 0 else (s - mu) / sd


HITTER_CATS = {
    "HR":  [("HR",1.0,True),("Barrel%",0.7,True),("Hard%",0.4,True)],
    "R":   [("R", 1.0,True),("OBP",   0.5,True),("wRC+", 0.4,True)],
    "RBI": [("RBI",1.0,True),("wOBA", 0.5,True),("Hard%",0.3,True)],
    "SB":  [("SB", 1.0,True),("Spd",  0.7,True)],
    "AVG": [("AVG",1.0,True),("xwOBA",0.6,True),("BABIP",-0.25,True)],
}
PITCHER_CATS = {
    "W":    [("W",   1.0,True)],
    "ERA":  [("ERA", 0.6,False),("xFIP",0.6,False),("SIERA",0.5,False)],
    "WHIP": [("WHIP",0.8,False),("BB%", 0.5,False)],
    "K":    [("SO",  1.0,True), ("K%",  0.8,True), ("SwStr%",0.5,True)],
}


def score_hitters(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    z_cols = []
    for cat, metrics in HITTER_CATS.items():
        w_sum = pd.Series(0.0, index=df.index)
        tot = sum(abs(w) for _, w, _ in metrics)
        for col, w, _ in metrics:
            if col in df.columns:
                w_sum += _z(df[col].fillna(df[col].median())) * w
        df[f"z_{cat}"] = (w_sum / tot).round(2)
        z_cols.append(f"z_{cat}")
    df["composite"] = df[z_cols].mean(axis=1).round(2)
    df["rank"]      = df["composite"].rank(ascending=False).astype(int)
    return df


def score_pitchers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    z_cols = []
    for cat, metrics in PITCHER_CATS.items():
        w_sum = pd.Series(0.0, index=df.index)
        tot = sum(abs(w) for _, w, _ in metrics)
        for col, w, higher in metrics:
            if col in df.columns:
                z = _z(df[col].fillna(df[col].median()))
                w_sum += (z if higher else -z) * w
        df[f"z_{cat}"] = (w_sum / tot).round(2)
        z_cols.append(f"z_{cat}")
    df["composite"] = df[z_cols].mean(axis=1).round(2)
    df["rank"]      = df["composite"].rank(ascending=False).astype(int)
    return df


# ─────────────────────────────────────────────────────────────
#  DEEP ANALYSIS ENGINE
#  Produces: regression_risk, breakout_score, trend_score,
#            profile_tag, and detailed explanation strings
# ─────────────────────────────────────────────────────────────

def _trend_slope(series: list) -> float:
    """Linear regression slope over a short year series."""
    if len(series) < 2:
        return 0.0
    x = np.arange(len(series))
    slope, *_ = scipy_stats.linregress(x, series)
    return float(slope)


def deep_analysis(df: pd.DataFrame, all_df: pd.DataFrame, ptype: str) -> pd.DataFrame:
    """
    For each player in df (most recent season), compute:
      - regression_risk   : High / Medium / Low
      - breakout_score    : 0-100 (higher = more breakout potential)
      - regression_score  : 0-100 (higher = more regression risk)
      - profile_tag       : Breakout / Regression Risk / Trending Up /
                            Trending Down / Stable / Undervalued / Overvalued
      - analysis_summary  : plain-English multi-line explanation
      - trend_<stat>      : slope of key stats over last 3 years
    """
    df = df.copy()
    regression_risks, breakout_scores, regression_scores = [], [], []
    profile_tags, summaries = [], []

    for _, row in df.iterrows():
        name = row.get("Name","")
        hist = all_df[all_df["Name"] == name].sort_values("Season")

        reg_flags    = []
        breakout_sigs = []
        summary_lines = []

        # ── HITTER ANALYSIS ──────────────────────────────────────────
        if ptype == "hitter":

            # 1. AVG vs expected
            avg   = row.get("AVG",  np.nan)
            xba   = row.get("xBA",  np.nan)
            xwoba = row.get("xwOBA",np.nan)
            babip = row.get("BABIP",np.nan)
            hard  = row.get("Hard%",np.nan)
            barrel= row.get("Barrel%",np.nan)
            hr    = row.get("HR",   np.nan)
            pa    = row.get("PA",   600)
            sb    = row.get("SB",   np.nan)
            spd   = row.get("Spd",  np.nan)
            kpct  = row.get("K%",   np.nan)
            bbpct = row.get("BB%",  np.nan)
            ev    = row.get("EV",   np.nan)
            la    = row.get("LA",   np.nan)
            wrcplus = row.get("wRC+", np.nan)
            age   = row.get("Age",  27)

            # AVG vs xBA divergence
            if pd.notna(avg) and pd.notna(xba):
                diff = avg - xba
                if diff > 0.030:
                    reg_flags.append(f"AVG ({avg:.3f}) outpacing xBA ({xba:.3f}) by +{diff:.3f} — expect decline")
                elif diff < -0.025:
                    breakout_sigs.append(f"AVG ({avg:.3f}) below xBA ({xba:.3f}) by {diff:.3f} — AVG should rise")

            # BABIP luck check
            if pd.notna(babip):
                if babip > 0.340 and (pd.isna(hard) or hard < 0.40):
                    reg_flags.append(f"BABIP ({babip:.3f}) well above league avg (.295) without elite contact quality")
                elif babip < 0.265 and (pd.notna(hard) and hard > 0.38):
                    breakout_sigs.append(f"BABIP ({babip:.3f}) unusually low despite solid Hard% ({hard:.1%}) — due for positive BABIP luck")

            # Barrel% vs HR rate
            if pd.notna(hr) and pd.notna(barrel) and pa and pa > 0:
                hr_rate = hr / pa
                if hr_rate > 0.058 and barrel < 0.09:
                    reg_flags.append(f"HR/PA ({hr_rate:.3f}) elevated vs Barrel% ({barrel:.1%}) — HR total likely to drop")
                elif barrel > 0.12 and hr_rate < 0.035:
                    breakout_sigs.append(f"Elite Barrel% ({barrel:.1%}) not yet reflected in HR count — power breakout candidate")

            # EV + LA sweet spot
            if pd.notna(ev) and pd.notna(la):
                if ev > 91 and 10 <= la <= 18:
                    breakout_sigs.append(f"Elite EV ({ev} mph) + optimal launch angle ({la}°) — elite contact profile")
                elif ev < 87:
                    reg_flags.append(f"Below-avg EV ({ev} mph) suggests contact quality concern")

            # K% trend
            if pd.notna(kpct):
                if kpct > 0.28:
                    reg_flags.append(f"High K% ({kpct:.1%}) limits floor in AVG/OBP categories")
                elif kpct < 0.16 and (pd.notna(bbpct) and bbpct > 0.10):
                    breakout_sigs.append(f"Elite plate discipline: K% ({kpct:.1%}) + BB% ({bbpct:.1%}) — sustainable OBP/AVG")

            # SB sustainability
            if pd.notna(sb) and pd.notna(spd):
                if sb > 25 and spd < 4.5:
                    reg_flags.append(f"High SB ({int(sb)}) vs low Spd score ({spd}) — SB pace unsustainable")
                elif spd > 7.0 and sb < 15:
                    breakout_sigs.append(f"Elite speed (Spd {spd}) underutilized — SB breakout possible with green light")

            # Age curve
            if pd.notna(age):
                if age <= 25 and pd.notna(wrcplus) and wrcplus > 115:
                    breakout_sigs.append(f"Age {int(age)} with wRC+ {int(wrcplus)} — still on upside of development curve")
                elif age >= 33:
                    reg_flags.append(f"Age {int(age)} — age-related decline risk increases")

            # Multi-year trend
            if len(hist) >= 3:
                for stat, direction in [("wRC+","up"),("Barrel%","up"),("K%","down")]:
                    if stat in hist.columns:
                        vals = hist[stat].dropna().tolist()[-3:]
                        if len(vals) >= 3:
                            slope = _trend_slope(vals)
                            if direction == "up" and slope > 0:
                                breakout_sigs.append(f"{stat} trending up over last {len(vals)} seasons (slope +{slope:.2f}/yr)")
                            elif direction == "down" and slope < 0:
                                breakout_sigs.append(f"K% trending down (slope {slope:.2f}/yr) — improving contact")
                            elif direction == "up" and slope < -0.5:
                                reg_flags.append(f"{stat} declining trend over last {len(vals)} seasons")

        # ── PITCHER ANALYSIS ─────────────────────────────────────────
        else:
            era   = row.get("ERA",  np.nan)
            xfip  = row.get("xFIP", np.nan)
            siera = row.get("SIERA",np.nan)
            fip   = row.get("FIP",  np.nan)
            lob   = row.get("LOB%", np.nan)
            babip = row.get("BABIP",np.nan)
            hrfb  = row.get("HR/FB",np.nan)
            kpct  = row.get("K%",   np.nan)
            bbpct = row.get("BB%",  np.nan)
            swstr = row.get("SwStr%",np.nan)
            gb    = row.get("GB%",  np.nan)
            whip  = row.get("WHIP", np.nan)
            age   = row.get("Age",  28)
            ip    = row.get("IP",   150)
            csw   = row.get("CSW%", np.nan)

            # ERA vs xFIP/SIERA gap
            if pd.notna(era) and pd.notna(xfip):
                gap = xfip - era
                if gap > 0.70:
                    reg_flags.append(f"ERA ({era:.2f}) significantly below xFIP ({xfip:.2f}) — ERA correction expected (+{gap:.2f})")
                elif gap < -0.60:
                    breakout_sigs.append(f"ERA ({era:.2f}) inflated vs xFIP ({xfip:.2f}) — true skill better than results ({gap:.2f})")

            if pd.notna(era) and pd.notna(siera):
                gap = siera - era
                if gap > 0.65:
                    reg_flags.append(f"ERA ({era:.2f}) also below SIERA ({siera:.2f}) — multiple models agree on regression")

            # LOB% luck
            if pd.notna(lob):
                if lob > 0.80:
                    reg_flags.append(f"LOB% ({lob:.1%}) unsustainably high (league avg ~72%) — ERA/WHIP will worsen")
                elif lob < 0.66:
                    breakout_sigs.append(f"LOB% ({lob:.1%}) unluckily low — ERA/WHIP should improve with normal strand rates")

            # BABIP luck
            if pd.notna(babip):
                if babip < 0.262:
                    reg_flags.append(f"Low BABIP ({babip:.3f}) propping up ERA — opponents will get more hits")
                elif babip > 0.318:
                    breakout_sigs.append(f"High BABIP ({babip:.3f}) inflating ERA — underlying stuff is better than results show")

            # HR/FB
            if pd.notna(hrfb):
                if hrfb < 0.072:
                    reg_flags.append(f"HR/FB ({hrfb:.1%}) below average — HRs allowed will normalize upward")
                elif hrfb > 0.145:
                    breakout_sigs.append(f"HR/FB ({hrfb:.1%}) elevated — could drop, improving ERA")

            # K% + SwStr% combo
            if pd.notna(kpct) and pd.notna(swstr):
                if kpct > 0.28 and swstr > 0.13:
                    breakout_sigs.append(f"Elite strikeout profile: K% {kpct:.1%} + SwStr% {swstr:.1%} — sustainable ace-level stuff")
            if pd.notna(bbpct) and bbpct > 0.11:
                reg_flags.append(f"High BB% ({bbpct:.1%}) — control issues elevate ERA/WHIP ceiling")

            # GB% as ERA stabilizer
            if pd.notna(gb) and gb > 0.52:
                breakout_sigs.append(f"Elite GB% ({gb:.1%}) limits HR exposure — good for ERA stability")

            # CSW% (called strikes + whiffs)
            if pd.notna(csw) and csw > 0.32:
                breakout_sigs.append(f"High CSW% ({csw:.1%}) — above-average pitch quality / command")

            # Age
            if pd.notna(age):
                if age <= 26 and pd.notna(kpct) and kpct > 0.24:
                    breakout_sigs.append(f"Young arm (age {int(age)}) with strong K% ({kpct:.1%}) — development upside remains")
                elif age >= 35:
                    reg_flags.append(f"Age {int(age)} — injury and decline risk elevated for pitchers")

            # Multi-year trend
            if len(hist) >= 3:
                for stat, direction in [("K%","up"),("BB%","down"),("ERA","down")]:
                    if stat in hist.columns:
                        vals = hist[stat].dropna().tolist()[-3:]
                        if len(vals) >= 3:
                            slope = _trend_slope(vals)
                            if direction == "up" and slope > 0.005:
                                breakout_sigs.append(f"{stat} trending up last {len(vals)} seasons (+{slope:.3f}/yr)")
                            elif direction == "down" and slope < 0:
                                breakout_sigs.append(f"{stat} improving last {len(vals)} seasons ({slope:.3f}/yr)")
                            elif direction == "down" and slope > 0.2:
                                reg_flags.append(f"{stat} trending worse last {len(vals)} seasons (+{slope:.3f}/yr)")

        # ── SCORE CALCULATION ─────────────────────────────────────────
        b_score = min(100, len(breakout_sigs) * 22 + (5 if len(hist) >= 4 else 0))
        r_score = min(100, len(reg_flags)    * 22)

        # ── PROFILE TAG (granular) ────────────────────────────────────
        if ptype == "hitter":
            barrel_t = row.get("Barrel%", np.nan)
            spd_t    = row.get("Spd", np.nan)
            age_t    = row.get("Age", 28)
            wrc_t    = row.get("wRC+", np.nan)
            sb_t     = row.get("SB", np.nan)
            kpct_t   = row.get("K%", np.nan)
            if b_score >= 66 and r_score < 22:
                tag = "🚀 Elite Breakout"
            elif b_score >= 44 and r_score < 22:
                tag = "📈 Breakout Candidate"
            elif r_score >= 66:
                tag = "🚨 High Regression Risk"
            elif r_score >= 44 and b_score < 22:
                tag = "📉 Regression Risk"
            elif b_score >= 44 and r_score >= 44:
                tag = "⚖️ High Ceiling / High Risk"
            elif b_score >= 22 and r_score >= 22:
                tag = "⚖️ Mixed Signals"
            elif pd.notna(age_t) and age_t <= 24 and pd.notna(wrc_t) and wrc_t > 110:
                tag = "🌱 Young Talent"
            elif pd.notna(spd_t) and spd_t > 7.0 and pd.notna(sb_t) and sb_t < 15:
                tag = "💨 Speed Sleeper"
            elif pd.notna(barrel_t) and barrel_t > 0.12 and b_score > 0:
                tag = "💣 Power Upside"
            elif pd.notna(kpct_t) and kpct_t < 0.15 and b_score > 0:
                tag = "🎯 Contact Upside"
            elif b_score > 0:
                tag = "👀 Undervalued"
            elif r_score > 0:
                tag = "⚠️ Slight Risk"
            else:
                tag = "✅ Stable"
        else:
            kpct_t  = row.get("K%", np.nan)
            gb_t    = row.get("GB%", np.nan)
            age_t   = row.get("Age", 28)
            swstr_t = row.get("SwStr%", np.nan)
            if b_score >= 66 and r_score < 22:
                tag = "🚀 Ace Breakout"
            elif b_score >= 44 and r_score < 22:
                tag = "📈 Breakout Candidate"
            elif r_score >= 66:
                tag = "🚨 High Regression Risk"
            elif r_score >= 44 and b_score < 22:
                tag = "📉 Regression Risk"
            elif b_score >= 44 and r_score >= 44:
                tag = "⚖️ High Ceiling / High Risk"
            elif b_score >= 22 and r_score >= 22:
                tag = "⚖️ Mixed Signals"
            elif pd.notna(age_t) and age_t <= 25 and pd.notna(kpct_t) and kpct_t > 0.24:
                tag = "🌱 Young Arm"
            elif pd.notna(gb_t) and gb_t > 0.52 and b_score > 0:
                tag = "🪱 GB Specialist Upside"
            elif pd.notna(swstr_t) and swstr_t > 0.14 and b_score > 0:
                tag = "🎯 Swing-Miss Upside"
            elif b_score > 0:
                tag = "👀 Undervalued"
            elif r_score > 0:
                tag = "⚠️ Slight Risk"
            else:
                tag = "✅ Stable"

        # Risk label
        risk = "High" if r_score >= 44 else "Medium" if r_score >= 22 else "Low"

        # ── QUALITATIVE NARRATIVE ─────────────────────────────────────
        narrative_parts = []
        if ptype == "hitter":
            wrc_n    = row.get("wRC+", np.nan)
            barrel_n = row.get("Barrel%", np.nan)
            hr_n     = row.get("HR", np.nan)
            sb_n2    = row.get("SB", np.nan)
            spd_n    = row.get("Spd", np.nan)
            age_n    = row.get("Age", 28)
            xwoba_n  = row.get("xwOBA", np.nan)
            if pd.notna(wrc_n):
                if wrc_n >= 140:
                    narrative_parts.append(f"One of the most productive hitters in baseball with a wRC+ of {int(wrc_n)}, placing him in elite company.")
                elif wrc_n >= 120:
                    narrative_parts.append(f"A legitimate fantasy anchor with a wRC+ of {int(wrc_n)}, consistently producing above-average value.")
                elif wrc_n >= 100:
                    narrative_parts.append(f"A solid contributor with a wRC+ of {int(wrc_n)}, providing league-average or better production.")
                else:
                    narrative_parts.append(f"A below-average hitter by wRC+ ({int(wrc_n)}), limiting his ceiling in rate categories.")
            if pd.notna(barrel_n) and pd.notna(hr_n):
                if barrel_n >= 0.14:
                    narrative_parts.append(f"His Barrel% of {barrel_n:.1%} is elite-tier — his HR output ({int(hr_n)}) is well-supported by real contact quality.")
                elif barrel_n >= 0.09:
                    narrative_parts.append(f"With a Barrel% of {barrel_n:.1%}, his power is real but not top-tier — a reliable mid-range HR contributor.")
                else:
                    narrative_parts.append(f"A below-average Barrel% ({barrel_n:.1%}) suggests his power numbers may be driven more by luck than contact quality.")
            if pd.notna(sb_n2) and pd.notna(spd_n):
                if sb_n2 >= 30 and spd_n >= 6.0:
                    narrative_parts.append(f"Elite speed profile — {int(sb_n2)} SB backed by Spd score of {spd_n} makes him a top SB asset.")
                elif sb_n2 >= 20:
                    narrative_parts.append(f"A useful SB contributor with {int(sb_n2)} steals, though his Spd score of {spd_n} warrants monitoring.")
                elif spd_n >= 7.0 and sb_n2 < 15:
                    narrative_parts.append(f"Elite speed score ({spd_n}) is being underutilized — a green light or lineup change could unlock SB upside.")
            if pd.notna(age_n):
                if age_n <= 23:
                    narrative_parts.append(f"At just {int(age_n)}, he's barely scratched the surface of his development ceiling — buy-high is still appropriate.")
                elif age_n <= 27:
                    narrative_parts.append(f"At {int(age_n)}, he's in the prime performance window — expect stable or improving production.")
                elif age_n >= 34:
                    narrative_parts.append(f"At {int(age_n)}, age-related decline is a real concern. Monitor spring training before investing heavily.")
        else:
            era_n    = row.get("ERA", np.nan)
            xfip_n   = row.get("xFIP", np.nan)
            kpct_n2  = row.get("K%", np.nan)
            bbpct_n  = row.get("BB%", np.nan)
            swstr_n2 = row.get("SwStr%", np.nan)
            gb_n     = row.get("GB%", np.nan)
            age_n    = row.get("Age", 28)
            if pd.notna(era_n) and pd.notna(xfip_n):
                if era_n <= 3.00 and xfip_n <= 3.20:
                    narrative_parts.append(f"An elite pitcher — ERA of {era_n:.2f} backed by xFIP of {xfip_n:.2f} means his dominance is real and repeatable.")
                elif era_n <= 3.50 and xfip_n <= 3.50:
                    narrative_parts.append(f"A legitimate No.1/2 starter. ERA ({era_n:.2f}) and xFIP ({xfip_n:.2f}) are aligned, supporting strong future performance.")
                elif era_n > xfip_n + 0.60:
                    narrative_parts.append(f"ERA ({era_n:.2f}) is being inflated by bad luck — xFIP of {xfip_n:.2f} suggests he's pitching much better than results. Buy low.")
                elif xfip_n > era_n + 0.60:
                    narrative_parts.append(f"ERA ({era_n:.2f}) looks better than underlying metrics (xFIP {xfip_n:.2f}) — some regression in ERA/WHIP is likely. Sell high.")
            if pd.notna(kpct_n2) and pd.notna(swstr_n2):
                if kpct_n2 >= 0.30 and swstr_n2 >= 0.14:
                    narrative_parts.append(f"Dominant arsenal: K% {kpct_n2:.1%} and SwStr% {swstr_n2:.1%} put him among the game's elite strikeout arms.")
                elif kpct_n2 >= 0.24:
                    narrative_parts.append(f"Above-average K rate ({kpct_n2:.1%}) makes him a reliable strikeout contributor.")
                elif kpct_n2 < 0.18:
                    narrative_parts.append(f"Below-average K rate ({kpct_n2:.1%}) limits his K upside — best as ERA/WHIP streamer.")
            if pd.notna(bbpct_n):
                if bbpct_n < 0.06:
                    narrative_parts.append(f"Exceptional command (BB% {bbpct_n:.1%}) is a major ERA/WHIP stabilizer.")
                elif bbpct_n > 0.10:
                    narrative_parts.append(f"Control issues (BB% {bbpct_n:.1%}) create week-to-week volatility in ERA and WHIP.")
            if pd.notna(gb_n) and gb_n >= 0.52:
                narrative_parts.append(f"Elite groundball rate ({gb_n:.1%}) naturally suppresses HRs and stabilizes ERA.")
            if pd.notna(age_n):
                if age_n <= 25:
                    narrative_parts.append(f"Still only {int(age_n)} — more development likely ahead, ceiling not yet reached.")
                elif age_n >= 35:
                    narrative_parts.append(f"At {int(age_n)}, durability is the primary concern. Monitor workload and IL history.")

        narrative = " ".join(narrative_parts)

        # ── SUMMARY TEXT ─────────────────────────────────────────────
        if narrative:
            summary_lines = ["📝 **Scouting Summary:**\n" + narrative, "---"]
        if breakout_sigs:
            summary_lines.append("🟢 **Breakout signals:**")
            summary_lines += [f"  • {s}" for s in breakout_sigs]
        if reg_flags:
            summary_lines.append("🔴 **Regression flags:**")
            summary_lines += [f"  • {s}" for s in reg_flags]
        if not breakout_sigs and not reg_flags:
            summary_lines.append("Profile looks stable — no major flags in either direction.")

        regression_risks.append(risk)
        breakout_scores.append(b_score)
        regression_scores.append(r_score)
        profile_tags.append(tag)
        summaries.append("\n".join(summary_lines))

    df["regression_risk"]  = regression_risks
    df["breakout_score"]   = breakout_scores
    df["regression_score"] = regression_scores
    df["profile_tag"]      = profile_tags
    df["analysis_summary"] = summaries
    return df


# ─────────────────────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────

def style_risk(val):
    c = {"High":"#FF4B4B","Medium":"#FFA500","Low":"#21C354"}.get(val,"")
    return f"color:{c}; font-weight:bold" if c else ""

def style_z(val):
    try:
        v = float(val)
        if v >  1.0: return "background-color:#1a472a"
        if v >  0.5: return "background-color:#2d5a3d"
        if v < -1.0: return "background-color:#5c1a1a"
        if v < -0.5: return "background-color:#7b2d2d"
    except Exception:
        pass
    return ""

def style_breakout(val):
    try:
        v = int(val)
        if v >= 66: return "background-color:#1a472a; color:#21C354; font-weight:bold"
        if v >= 33: return "background-color:#2d5a3d"
        if v <= 10: return "color:#888"
    except Exception:
        pass
    return ""


# ─────────────────────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────────────────────

bat_all, pit_all, bat_rec, pit_rec, LATEST = load_data()
ALL_YEARS = sorted(bat_all["Season"].unique().tolist())


# ─────────────────────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────────────────────

for _k in ["drafted_h","drafted_p","my_h","my_p","targets"]:
    if _k not in st.session_state:
        st.session_state[_k] = [] if _k in ["my_h","my_p","targets"] else set()


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────

st.sidebar.title("⚾ Draft Dashboard")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", [
    "📋 Draft Board",
    "🔍 Player Deep Dive",
    "🧠 Regression & Breakout",
    "📊 Category Scarcity",
    "🎯 Strategy & Target List",
    "⚙️ Weight Dashboard",
    "🏟️ Draft Room",
])
st.sidebar.markdown("---")
using_demo = not any(f.startswith("batting_") for f in os.listdir(CACHE_DIR)) \
             if os.path.exists(CACHE_DIR) else True
if using_demo:
    st.sidebar.warning("⚠️ Demo data active.\nRun `python data_loader.py` for real stats.")
else:
    st.sidebar.success(f"✅ Live data through {LATEST}")
st.sidebar.caption(f"Seasons: {', '.join(map(str, ALL_YEARS))}")

# Target list counter in sidebar
if st.session_state.targets:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**🎯 Target List: {len(st.session_state.targets)} players**")
    for t in st.session_state.targets:
        st.sidebar.caption(f"• {t['name']} ({t['type']})")


# ═════════════════════════════════════════════════════════════
#  PAGE 1 — DRAFT BOARD
# ═════════════════════════════════════════════════════════════

if page == "📋 Draft Board":
    st.title("📋 Draft Board")
    st.caption(f"Composite z-score rankings — {LATEST} season. Green = above avg, red = below avg.")

    ptype = st.radio("", ["Hitters","Pitchers"], horizontal=True)
    df    = bat_rec.copy() if ptype == "Hitters" else pit_rec.copy()

    c1, c2, c3, c4 = st.columns(4)
    teams = ["All"] + sorted(df["Team"].dropna().unique().tolist())
    team_f = c1.selectbox("Team", teams)
    if ptype == "Hitters" and "Position" in df.columns:
        pos_f = c2.selectbox("Position", ["All"] + sorted(df["Position"].dropna().unique().tolist()))
    else:
        pos_f = "All"
    risk_f = c3.selectbox("Regression Risk", ["All","Low","Medium","High"])
    tag_f  = c4.selectbox("Profile", ["All"] + sorted(df["profile_tag"].dropna().unique().tolist()))

    if team_f != "All": df = df[df["Team"] == team_f]
    if pos_f  != "All" and "Position" in df.columns: df = df[df["Position"] == pos_f]
    if risk_f != "All": df = df[df["regression_risk"] == risk_f]
    if tag_f  != "All": df = df[df["profile_tag"] == tag_f]

    z_cols  = [c for c in df.columns if c.startswith("z_")]
    sort_by = st.selectbox("Sort by", ["composite"] + z_cols + ["breakout_score","regression_score"])
    df = df.sort_values(sort_by, ascending=False).reset_index(drop=True)
    df.index += 1

    if ptype == "Hitters":
        show = ["Name","Team","profile_tag","composite","HR","R","RBI","SB","AVG",
                "wRC+","xwOBA","Barrel%","xBA",
                "z_HR","z_R","z_RBI","z_SB","z_AVG",
                "breakout_score","regression_score","regression_risk"]
    else:
        show = ["Name","Team","profile_tag","composite","W","ERA","WHIP","SO",
                "xFIP","SIERA","K%","SwStr%","LOB%",
                "z_W","z_ERA","z_WHIP","z_K",
                "breakout_score","regression_score","regression_risk"]

    show = [c for c in show if c in df.columns]
    z_present = [c for c in show if c.startswith("z_")]

    styled = (
        df[show].style
        .map(style_risk,     subset=["regression_risk"])
        .map(style_z,        subset=z_present)
        .map(style_breakout, subset=["breakout_score"])
        .background_gradient(subset=["composite"], cmap="RdYlGn")
        .format({c: "{:.2f}" for c in ["composite"] + z_present})
    )
    st.dataframe(styled, use_container_width=True, height=560)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Players",      len(df))
    m2.metric("High Risk",    int((df["regression_risk"]=="High").sum()))
    m3.metric("Breakouts",    int((df["breakout_score"] >= 44).sum()))
    m4.metric("Avg composite",f"{df['composite'].mean():.2f}")
    m5.metric("Top player",   df.iloc[0]["Name"] if len(df) else "—")


# ═════════════════════════════════════════════════════════════
#  PAGE 2 — PLAYER DEEP DIVE
# ═════════════════════════════════════════════════════════════

elif page == "🔍 Player Deep Dive":
    st.title("🔍 Player Deep Dive")
    st.caption("Full historical snapshot, trend charts, radar chart, and analysis for any player.")

    ptype  = st.radio("", ["Hitter","Pitcher"], horizontal=True)
    all_df = bat_all if ptype == "Hitter" else pit_all
    rec_df = bat_rec if ptype == "Hitter" else pit_rec

    name = st.selectbox("Select player", sorted(all_df["Name"].dropna().unique().tolist()))
    hist = all_df[all_df["Name"] == name].sort_values("Season")
    rec  = rec_df[rec_df["Name"] == name]

    if hist.empty:
        st.warning("No data found.")
        st.stop()

    team = hist.iloc[-1].get("Team","—")
    age  = hist.iloc[-1].get("Age","—")
    st.markdown(f"## {name}  `{team}`  Age {age}")

    # profile tag + analysis
    if not rec.empty:
        tag   = rec.iloc[0].get("profile_tag","✅ Stable")
        bscore = rec.iloc[0].get("breakout_score", 0)
        rscore = rec.iloc[0].get("regression_score", 0)
        summary = rec.iloc[0].get("analysis_summary","")

        tc1, tc2, tc3 = st.columns(3)
        tc1.markdown(f"**Profile:** {tag}")
        tc2.metric("Breakout Score",   f"{bscore}/100")
        tc3.metric("Regression Score", f"{rscore}/100")

        if summary:
            with st.expander("📋 Full Analysis", expanded=True):
                lines = summary.split("\n")
                for line in lines:
                    if line.startswith("📝 **Scouting Summary:**"):
                        # Narrative header — medium size
                        st.markdown("<p style='font-size:13px;font-weight:bold;margin-bottom:4px'>📝 Scouting Summary</p>", unsafe_allow_html=True)
                    elif line == "---":
                        st.markdown("<hr style='margin:8px 0;border-color:#333'>", unsafe_allow_html=True)
                    elif line and not line.startswith("  •") and not line.startswith("🟢") and not line.startswith("🔴"):
                        # Narrative body — smaller font
                        st.markdown(f"<p style='font-size:13px;color:#ccc;line-height:1.6;margin:0'>{line}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(line)

    st.markdown("---")

    # key stat metrics
    if ptype == "Hitter":
        key = ["HR","R","RBI","SB","AVG","wRC+","xwOBA","xBA","Barrel%","BB%","K%","EV"]
    else:
        key = ["W","ERA","WHIP","SO","K%","xFIP","SIERA","SwStr%","BB%","LOB%","GB%","CSW%"]
    key = [k for k in key if k in hist.columns]

    latest_row = hist.iloc[-1]
    prev_row   = hist.iloc[-2] if len(hist) > 1 else None
    cols = st.columns(min(len(key), 6))
    for i, stat in enumerate(key[:6]):
        val = latest_row.get(stat, np.nan)
        if pd.isna(val): continue
        if stat in ["AVG","OBP","SLG","OPS","wOBA","xwOBA","xBA","ERA","WHIP","FIP","xFIP","SIERA","BABIP"]:
            disp = f"{float(val):.3f}"
        elif stat in ["BB%","K%","Hard%","Barrel%","SwStr%","LOB%","K-BB%","HR/FB","GB%","CSW%"]:
            disp = f"{float(val):.1%}"
        else:
            disp = str(int(round(float(val))))
        delta = None
        if prev_row is not None:
            pv = prev_row.get(stat, np.nan)
            if pd.notna(pv) and pd.notna(val):
                delta = round(float(val) - float(pv), 3)
        cols[i].metric(stat, disp, delta)

    if len(key) > 6:
        cols2 = st.columns(len(key) - 6)
        for i, stat in enumerate(key[6:]):
            val = latest_row.get(stat, np.nan)
            if pd.isna(val): continue
            if stat in ["AVG","OBP","SLG","OPS","wOBA","xwOBA","xBA","ERA","WHIP","FIP","xFIP","SIERA","BABIP"]:
                disp = f"{float(val):.3f}"
            elif stat in ["BB%","K%","Hard%","Barrel%","SwStr%","LOB%","K-BB%","HR/FB","GB%","CSW%"]:
                disp = f"{float(val):.1%}"
            else:
                disp = str(int(round(float(val))))
            cols2[i].metric(stat, disp)

    st.markdown("---")

    # trend charts
    st.markdown("### 📈 Historical Trends")

    def make_chart(hist, cols_list, dual_axis_col=None, expanded=False, label=""):
        """
        Render a trend chart. If dual_axis_col is set, that column goes on
        a secondary y-axis so mismatched scales (e.g. wRC+ vs wOBA) display properly.
        """
        avail = [c for c in cols_list if c in hist.columns]
        if not avail:
            return
        with st.expander(label, expanded=expanded):
            if dual_axis_col and dual_axis_col in avail:
                # Split: primary (rate stats) vs secondary (counting/index)
                primary   = [c for c in avail if c != dual_axis_col]
                secondary = [dual_axis_col]
                fig = go.Figure()
                colors = px.colors.qualitative.Plotly
                ci = 0
                for col in primary:
                    fig.add_trace(go.Scatter(
                        x=hist["Season"], y=hist[col],
                        mode="lines+markers", name=col,
                        line=dict(color=colors[ci % len(colors)]),
                        yaxis="y1"
                    ))
                    ci += 1
                for col in secondary:
                    fig.add_trace(go.Scatter(
                        x=hist["Season"], y=hist[col],
                        mode="lines+markers", name=col,
                        line=dict(color=colors[ci % len(colors)], dash="dot", width=2),
                        yaxis="y2"
                    ))
                fig.update_layout(
                    template="plotly_dark", height=300,
                    margin=dict(l=10,r=10,t=10,b=10),
                    legend=dict(orientation="h", y=1.15),
                    xaxis=dict(tickvals=ALL_YEARS, tickmode="array"),
                    yaxis =dict(title=", ".join(primary),  side="left"),
                    yaxis2=dict(title=dual_axis_col, side="right",
                                overlaying="y", showgrid=False),
                )
            else:
                melt = hist[["Season"] + avail].melt("Season", var_name="Metric", value_name="Value")
                fig  = px.line(melt, x="Season", y="Value", color="Metric",
                               markers=True, template="plotly_dark",
                               color_discrete_sequence=px.colors.qualitative.Plotly)
                fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10),
                                  legend=dict(orientation="h", y=1.15))
                fig.update_xaxes(tickvals=ALL_YEARS, tickmode="array")
            st.plotly_chart(fig, use_container_width=True)

    if ptype == "Hitter":
        make_chart(hist, ["HR","R","RBI","SB"],              expanded=True,  label="Counting Stats")
        make_chart(hist, ["Barrel%","Hard%","EV","maxEV"],   expanded=False, label="Quality of Contact")
        # True Talent: wOBA/xwOBA/xBA on left axis (~0.300-0.420), wRC+ on right (~80-160)
        make_chart(hist, ["wOBA","xwOBA","xBA","wRC+"],      expanded=True,
                   dual_axis_col="wRC+",                     label="True Talent (wOBA / xwOBA / xBA  |  wRC+ →)")
        make_chart(hist, ["BB%","K%","SwStr%"],              expanded=False, label="Plate Discipline")
        make_chart(hist, ["GB%","FB%","Pull%","LA"],         expanded=False, dual_axis_col="LA", label="Batted Ball Profile (GB% / FB% / Pull%  |  Launch Angle →)")
    else:
        # Results: ERA/WHIP on left (~1.0-5.0), K/9 on right (~6-14)
        make_chart(hist, ["ERA","WHIP","K/9"],               expanded=True,
                   dual_axis_col="K/9",                      label="Results (ERA / WHIP  |  K/9 →)")
        # True Talent: xFIP/SIERA/FIP all same scale — no dual axis needed
        make_chart(hist, ["xFIP","SIERA","FIP"],             expanded=True,  label="True Talent (xFIP / SIERA / FIP)")
        make_chart(hist, ["K%","SwStr%","BB%","CSW%"],       expanded=False, label="Stuff & Command")
        make_chart(hist, ["BABIP","LOB%","HR/FB"],           expanded=False, label="Luck Indicators")
        make_chart(hist, ["GB%","FB%","Hard%","Barrel%"],    expanded=False, label="Batted Ball")

    # radar
    if not rec.empty:
        st.markdown("---")
        st.markdown(f"### 🕸️ Category Value Radar ({LATEST})")
        if ptype == "Hitter":
            zcats, labels = ["z_HR","z_R","z_RBI","z_SB","z_AVG"], ["HR","R","RBI","SB","AVG"]
        else:
            zcats, labels = ["z_W","z_ERA","z_WHIP","z_K"], ["W","ERA","WHIP","K"]
        vals = [max(-3, min(3, float(rec.iloc[0].get(c,0)))) for c in zcats]
        fig_r = go.Figure(go.Scatterpolar(
            r=vals+[vals[0]], theta=labels+[labels[0]],
            fill="toself", line_color="#4fc3f7",
            fillcolor="rgba(79,195,247,0.18)"
        ))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(range=[-3,3], tickfont_size=9)),
            template="plotly_dark", height=360,
            margin=dict(l=40,r=40,t=40,b=40)
        )
        st.plotly_chart(fig_r, use_container_width=True)

    # add to target list button
    st.markdown("---")
    note_input = st.text_input("Add a note (optional)", key="dive_note")
    if st.button(f"🎯 Add {name} to Target List"):
        entry = {
            "name": name,
            "type": ptype,
            "tag":  rec.iloc[0].get("profile_tag","—") if not rec.empty else "—",
            "composite": float(rec.iloc[0].get("composite",0)) if not rec.empty else 0,
            "note": note_input,
        }
        if not any(t["name"] == name for t in st.session_state.targets):
            st.session_state.targets.append(entry)
            st.success(f"✅ {name} added to your target list!")
        else:
            st.info(f"{name} is already in your target list.")

    # full table
    st.markdown("---")
    st.markdown("### 📄 Full Historical Stats")
    drop = [c for c in ["playerid","regression_risk","regression_score","breakout_score",
                         "profile_tag","analysis_summary","rank","composite"] if c in hist.columns]
    st.dataframe(hist.drop(columns=drop).set_index("Season"), use_container_width=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 3 — REGRESSION & BREAKOUT ANALYSIS
# ═════════════════════════════════════════════════════════════

elif page == "🧠 Regression & Breakout":
    st.title("🧠 Regression & Breakout Analysis")
    st.caption("Deep dives into who is due for a correction and who is poised to take off.")

    ptype = st.radio("", ["Hitters","Pitchers"], horizontal=True)
    df = bat_rec.copy() if ptype == "Hitters" else pit_rec.copy()

    tab_break, tab_reg, tab_mixed = st.tabs([
        "🚀 Breakout Candidates",
        "📉 Regression Risks",
        "⚖️ Mixed / Undervalued"
    ])

    with tab_break:
        st.markdown("### 🚀 Breakout Candidates")
        st.caption("Players whose underlying metrics suggest performance should improve — either first-timers or bounce-backs.")
        breakouts = df[df["breakout_score"] >= 33].sort_values("breakout_score", ascending=False)
        if breakouts.empty:
            st.info("No breakout candidates found with current filters.")
        else:
            for _, row in breakouts.head(15).iterrows():
                with st.expander(f"**{row['Name']}** ({row.get('Team','—')})  —  Breakout Score: {int(row['breakout_score'])}/100  |  {row['profile_tag']}"):
                    summary = row.get("analysis_summary","")
                    # Show only breakout signals
                    lines = [l for l in summary.split("\n") if "🟢" in l or "•" in l and "🔴" not in l]
                    for line in lines:
                        st.markdown(line)
                    # Key stats
                    if ptype == "Hitters":
                        key_s = ["composite","HR","AVG","xwOBA","xBA","Barrel%","wRC+","BABIP","Spd"]
                    else:
                        key_s = ["composite","ERA","xFIP","SIERA","K%","SwStr%","LOB%","GB%","BABIP"]
                    key_s = [s for s in key_s if s in row.index]
                    sc = st.columns(len(key_s))
                    for i, s in enumerate(key_s):
                        v = row.get(s, np.nan)
                        if pd.notna(v):
                            sc[i].metric(s, f"{v:.3f}" if isinstance(v, float) and v < 10 else str(round(v,1) if isinstance(v, float) else int(v)))
                    if st.button(f"🎯 Add to Target List", key=f"add_break_{row['Name']}"):
                        entry = {"name": row["Name"], "type": ptype.rstrip("s"),
                                 "tag": row["profile_tag"], "composite": float(row["composite"]), "note": "Breakout candidate"}
                        if not any(t["name"] == row["Name"] for t in st.session_state.targets):
                            st.session_state.targets.append(entry)
                            st.success(f"Added {row['Name']}!")

    with tab_reg:
        st.markdown("### 📉 Regression Risks")
        st.caption("Players whose surface stats are ahead of their underlying metrics — expect correction.")
        risks = df[df["regression_score"] >= 33].sort_values("regression_score", ascending=False)
        if risks.empty:
            st.info("No major regression risks found.")
        else:
            for _, row in risks.head(15).iterrows():
                with st.expander(f"**{row['Name']}** ({row.get('Team','—')})  —  Regression Score: {int(row['regression_score'])}/100  |  {row['profile_tag']}"):
                    summary = row.get("analysis_summary","")
                    lines = [l for l in summary.split("\n") if "🔴" in l or ("•" in l and "🟢" not in l)]
                    for line in lines:
                        st.markdown(line)
                    if ptype == "Hitters":
                        key_s = ["composite","HR","AVG","xwOBA","xBA","Barrel%","BABIP"]
                    else:
                        key_s = ["composite","ERA","xFIP","SIERA","LOB%","BABIP","HR/FB"]
                    key_s = [s for s in key_s if s in row.index]
                    sc = st.columns(len(key_s))
                    for i, s in enumerate(key_s):
                        v = row.get(s, np.nan)
                        if pd.notna(v):
                            sc[i].metric(s, f"{v:.3f}" if isinstance(v, float) and v < 10 else str(round(v,1) if isinstance(v, float) else int(v)))

    with tab_mixed:
        st.markdown("### ⚖️ Mixed Signals & Undervalued")
        st.caption("Players with both upside signals and risk flags — or players ranked lower than their underlying metrics suggest.")

        # Undervalued = high breakout score but low composite rank
        df["value_gap"] = df["breakout_score"] - df["composite"] * 10
        mixed = df[
            (df["profile_tag"].str.contains("Mixed|Undervalued|Trending Up", na=False)) |
            (df["value_gap"] > 20)
        ].sort_values("value_gap", ascending=False)

        if mixed.empty:
            st.info("No mixed/undervalued players found.")
        else:
            for _, row in mixed.head(12).iterrows():
                with st.expander(f"**{row['Name']}** — {row['profile_tag']}  |  Breakout: {int(row['breakout_score'])}  Regression: {int(row['regression_score'])}"):
                    st.markdown(row.get("analysis_summary",""))
                    if st.button(f"🎯 Add to Target List", key=f"add_mixed_{row['Name']}"):
                        entry = {"name": row["Name"], "type": ptype.rstrip("s"),
                                 "tag": row["profile_tag"], "composite": float(row["composite"]), "note": "Undervalued / mixed signals"}
                        if not any(t["name"] == row["Name"] for t in st.session_state.targets):
                            st.session_state.targets.append(entry)
                            st.success(f"Added {row['Name']}!")

    # ── Scatter: Breakout Score vs Composite ─────────────────────────────────
    st.markdown("---")
    st.markdown("### 📉📈 Breakout vs Composite Score Scatter")
    fig_sc = px.scatter(
        df, x="composite", y="breakout_score",
        hover_name="Name", color="regression_risk",
        color_discrete_map={"High":"#FF4B4B","Medium":"#FFA500","Low":"#21C354"},
        size="breakout_score", size_max=20,
        template="plotly_dark",
        labels={"composite":"Composite Draft Value","breakout_score":"Breakout Score"},
        title="Top-right = high value + high upside  |  Bottom-left = low value + no upside",
    )
    fig_sc.add_hline(y=33, line_dash="dash", line_color="gray", opacity=0.5)
    fig_sc.add_vline(x=0,  line_dash="dash", line_color="gray", opacity=0.5)
    fig_sc.update_layout(height=450)
    st.plotly_chart(fig_sc, use_container_width=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 4 — CATEGORY SCARCITY
# ═════════════════════════════════════════════════════════════

elif page == "📊 Category Scarcity":
    st.title("📊 Category Scarcity")
    st.caption("Where elite production is thin — so you know when to reach for each category.")

    cat_sources = {
        "HR": (bat_rec,"HR"), "R": (bat_rec,"R"), "RBI": (bat_rec,"RBI"),
        "SB": (bat_rec,"SB"), "AVG": (bat_rec,"AVG"),
        "W":  (pit_rec,"W"),  "ERA": (pit_rec,"ERA"),
        "WHIP": (pit_rec,"WHIP"),
        "K":  (pit_rec,"SO"),
    }

    rows = []
    for cat, (src, col) in cat_sources.items():
        if col not in src.columns: continue
        s = src[col].dropna()
        lower = cat in ["ERA","WHIP"]
        p50  = s.quantile(0.50)
        p75  = s.quantile(0.75)
        p90  = s.quantile(0.10) if lower else s.quantile(0.90)
        rows.append({
            "Category": cat,
            "Type": "Pitching" if cat in ["W","ERA","WHIP","K"] else "Hitting",
            "Median": round(p50, 3),
            "Good (P75)": round(p75, 3),
            "Elite": round(p90, 3),
            "Std Dev": round(s.std(), 3),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.markdown("---")
    cat_choice = st.selectbox("Explore category distribution", list(cat_sources.keys()))
    src, col   = cat_sources[cat_choice]
    series     = src[col].dropna()
    lower      = cat_choice in ["ERA","WHIP"]
    p50 = series.quantile(0.50)
    p90 = series.quantile(0.10) if lower else series.quantile(0.90)

    fig = px.histogram(x=series, nbins=35, template="plotly_dark",
                       labels={"x": cat_choice, "y": "Players"},
                       title=f"{cat_choice} Distribution — {LATEST}",
                       color_discrete_sequence=["#4fc3f7"])
    fig.add_vline(x=p50, line_dash="dash", line_color="yellow", annotation_text="Median")
    fig.add_vline(x=p90, line_dash="dash", line_color="#FF4B4B", annotation_text="Elite")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)

    top10 = src.nsmallest(10,col) if lower else src.nlargest(10,col)
    show_c = [c for c in ["Name","Team",col,"composite","breakout_score","regression_risk"] if c in top10.columns]
    st.markdown(f"**Top 10 — {cat_choice}**")
    st.dataframe(top10[show_c].reset_index(drop=True), use_container_width=True)

    st.markdown("---")
    st.markdown("### 💡 Strategy Tips")
    tips = {
        "SB":  "Scarcest category. Target in rounds 3–6. Look for Spd > 6 AND OBP > .330.",
        "HR":  "Deep but differentiated. Barrel% > 10% is the truest predictor. Wait on power.",
        "AVG": "Trust xBA and xwOBA over surface AVG. High BABIP + low Hard% = avoid.",
        "ERA": "Find ERA > xFIP = undervalued. ERA < xFIP by 0.75+ = regression incoming.",
        "WHIP":"LOB% > 80% is unsustainable. K-BB% > 15% is the best WHIP floor indicator.",
        "K":   "SwStr% > 12% is elite. CSW% > 30% shows pitch quality beyond raw whiffs.",
        "W":   "Luckiest category. Target high IP + run support + K/BB > 3.5.",
        "R":   "Correlates with lineup spot + OBP. Find leadoff/2-hole hitters.",
        "RBI": "wOBA + HR pace > raw RBI. Lineup protection matters.",
    }
    for cat, tip in tips.items():
        with st.expander(f"**{cat}**"):
            st.write(tip)


# ═════════════════════════════════════════════════════════════
#  PAGE 5 — STRATEGY & TARGET LIST
# ═════════════════════════════════════════════════════════════

elif page == "🎯 Strategy & Target List":
    st.title("🎯 Strategy & Target List")
    st.caption("Plan your draft strategy by round and manage your personal target list.")

    tab_strat, tab_targets, tab_compare = st.tabs([
        "🗺️ Draft Strategy Planner",
        "⭐ My Target List",
        "📊 Compare Targets"
    ])

    # ── Tab 1: Strategy Planner ───────────────────────────────────────────────
    with tab_strat:
        st.markdown("### 🗺️ Draft Strategy Planner")

        league_size = st.slider("League size (teams)", 8, 16, 12)
        your_pick   = st.slider("Your draft position", 1, league_size, 6)
        roster_slots = st.columns(2)
        with roster_slots[0]:
            h_slots = st.number_input("Hitter roster spots", 1, 15, 9)
        with roster_slots[1]:
            p_slots = st.number_input("Pitcher roster spots", 1, 15, 7)

        st.markdown("---")
        st.markdown("#### 🎯 Category Priority — drag to reorder")
        st.caption("Rank which categories you want to target most aggressively.")
        cat_priority = st.multiselect(
            "Your category priorities (select in order of importance)",
            ["HR","R","RBI","SB","AVG","W","ERA","WHIP","K"],
            default=["SB","HR","K","ERA","WHIP","R","RBI","AVG","W"]
        )

        st.markdown("---")

        # Auto-generate round-by-round advice
        st.markdown("#### 📋 Round-by-Round Guidance")

        # Snake draft: calculate approximate pick numbers
        total_rounds = h_slots + p_slots
        pick_numbers = []
        for rd in range(1, total_rounds + 1):
            if rd % 2 == 1:  # odd round: left to right
                pick_numbers.append((rd - 1) * league_size + your_pick)
            else:             # even round: right to left
                pick_numbers.append(rd * league_size - your_pick + 1)

        round_advice = {
            1:  ("Superstar anchor", "Elite 1st-rounders: 60+ HR pace, .300+ AVG, or ace SP. Don't reach."),
            2:  ("Top-10 talent",    "Best player available. If you didn't get SB in R1, address it now."),
            3:  ("SB or SP ace",     "SB dries up fast. If no speed yet, round 3 is your last cheap window."),
            4:  ("SP or power bat",  "Start your SP core. Target xFIP < 3.20 starters over name-brand ERA."),
            5:  ("Upside SP",        "Second SP or breakout hitter. Breakout Score > 44 is your filter."),
            6:  ("Category fill",    "Identify your weakest projected category and target specifically."),
            7:  ("Closer or depth",  "Saves/Holds if your league counts them. Otherwise best available."),
            8:  ("Depth + upside",   "Players with Breakout Score > 33 and low composite — buy low."),
            9:  ("Bench depth",      "Multi-position eligibility is gold in Yahoo. Prioritize SP/SS/2B."),
            10: ("Lottery tickets",  "Young players with elite underlying metrics but low ADP — Barrel% > 12%."),
        }

        for rd in range(1, min(total_rounds + 1, 11)):
            pick_no = pick_numbers[rd - 1] if rd - 1 < len(pick_numbers) else "—"
            label, advice = round_advice.get(rd, (f"Round {rd}", "Best player available."))
            pct_done = (pick_no / (league_size * total_rounds)) * 100 if isinstance(pick_no, int) else 0

            with st.expander(f"**Round {rd}** — Pick ~{pick_no}  |  {label}"):
                st.write(advice)

                # Suggest actual players from the board for this round
                approx_rank_lo = (rd - 1) * league_size
                approx_rank_hi = rd * league_size
                if rd <= 5:
                    sug_h = bat_rec[(bat_rec["rank"] >= approx_rank_lo) &
                                    (bat_rec["rank"] <= approx_rank_hi)].head(4)
                    sug_p = pit_rec[(pit_rec["rank"] >= approx_rank_lo) &
                                    (pit_rec["rank"] <= approx_rank_hi)].head(3)
                    if not sug_h.empty:
                        st.markdown("**Hitter targets in this range:**")
                        h_cols = [c for c in ["Name","Team","composite","HR","AVG","xwOBA","breakout_score","profile_tag"] if c in sug_h.columns]
                        st.dataframe(sug_h[h_cols], use_container_width=True, hide_index=True)
                    if not sug_p.empty:
                        st.markdown("**Pitcher targets in this range:**")
                        p_cols = [c for c in ["Name","Team","composite","ERA","xFIP","K%","breakout_score","profile_tag"] if c in sug_p.columns]
                        st.dataframe(sug_p[p_cols], use_container_width=True, hide_index=True)

        # Category weakness identifier
        st.markdown("---")
        st.markdown("#### 🔍 Category Gap Finder")
        st.caption("Based on your current target list, which categories are you thin on?")

        if st.session_state.targets:
            my_h_names = [t["name"] for t in st.session_state.targets if t["type"] == "Hitter"]
            my_p_names = [t["name"] for t in st.session_state.targets if t["type"] == "Pitcher"]
            my_h_df = bat_rec[bat_rec["Name"].isin(my_h_names)]
            my_p_df = pit_rec[pit_rec["Name"].isin(my_p_names)]

            gap_rows = []
            for cat, (src, col) in {
                "HR":(bat_rec,"z_HR"),"R":(bat_rec,"z_R"),"RBI":(bat_rec,"z_RBI"),
                "SB":(bat_rec,"z_SB"),"AVG":(bat_rec,"z_AVG"),
                "W":(pit_rec,"z_W"),"ERA":(pit_rec,"z_ERA"),
                "WHIP":(pit_rec,"z_WHIP"),"K":(pit_rec,"z_K"),
            }.items():
                df_chunk = my_h_df if cat in ["HR","R","RBI","SB","AVG"] else my_p_df
                if col in df_chunk.columns and len(df_chunk) > 0:
                    avg_z = df_chunk[col].mean()
                    status = "✅ Strong" if avg_z > 0.5 else "⚠️ Weak" if avg_z < -0.2 else "➡️ Average"
                    gap_rows.append({"Category": cat, "Your Avg Z": round(avg_z, 2), "Status": status})
            if gap_rows:
                st.dataframe(pd.DataFrame(gap_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Add players to your target list to see category gaps.")

    # ── Tab 2: Target List ────────────────────────────────────────────────────
    with tab_targets:
        st.markdown("### ⭐ My Target List")

        # Add player manually
        with st.expander("➕ Add a player manually"):
            col_a, col_b, col_c = st.columns(3)
            add_type = col_a.radio("Type", ["Hitter","Pitcher"], horizontal=True, key="manual_type")
            all_names_manual = sorted(
                (bat_rec if add_type == "Hitter" else pit_rec)["Name"].dropna().unique().tolist()
            )
            add_name = col_b.selectbox("Player", all_names_manual, key="manual_name")
            add_note = col_c.text_input("Note", placeholder="e.g. 'Value in round 8'", key="manual_note")
            if st.button("Add to Target List", key="manual_add"):
                rec_src = bat_rec if add_type == "Hitter" else pit_rec
                rec_row = rec_src[rec_src["Name"] == add_name]
                entry = {
                    "name": add_name, "type": add_type,
                    "tag":  rec_row.iloc[0].get("profile_tag","—") if not rec_row.empty else "—",
                    "composite": float(rec_row.iloc[0].get("composite",0)) if not rec_row.empty else 0,
                    "note": add_note,
                }
                if not any(t["name"] == add_name for t in st.session_state.targets):
                    st.session_state.targets.append(entry)
                    st.success(f"✅ Added {add_name}!")
                    st.rerun()
                else:
                    st.info(f"{add_name} already in list.")

        st.markdown("---")

        if not st.session_state.targets:
            st.info("Your target list is empty. Add players from the Draft Board, Deep Dive, or Regression pages.")
        else:
            # Sort options
            sort_opt = st.selectbox("Sort targets by", ["composite","name","type"], key="target_sort")
            sorted_targets = sorted(
                st.session_state.targets,
                key=lambda x: (-x["composite"] if sort_opt == "composite"
                               else x["name"] if sort_opt == "name"
                               else x["type"]),
            )

            to_remove = []
            for i, t in enumerate(sorted_targets):
                rec_src = bat_rec if t["type"] == "Hitter" else pit_rec
                rec_row = rec_src[rec_src["Name"] == t["name"]]

                with st.container():
                    st.markdown(f"""<div class='target-card'>
                        <b>{t['name']}</b> &nbsp; <span style='color:#aaa'>{t['type']}</span>
                        &nbsp;|&nbsp; {t['tag']}
                        &nbsp;|&nbsp; Composite: <b>{t['composite']:.2f}</b>
                        {"&nbsp;|&nbsp; 📝 " + t['note'] if t['note'] else ""}
                    </div>""", unsafe_allow_html=True)

                    if not rec_row.empty:
                        r = rec_row.iloc[0]
                        if t["type"] == "Hitter":
                            mini_stats = [c for c in ["HR","AVG","xwOBA","Barrel%","SB","wRC+","breakout_score"] if c in r.index]
                        else:
                            mini_stats = [c for c in ["ERA","xFIP","K%","SwStr%","WHIP","breakout_score"] if c in r.index]
                        mcols = st.columns(len(mini_stats))
                        for ci, s in enumerate(mini_stats):
                            v = r.get(s, np.nan)
                            if pd.notna(v):
                                disp = f"{float(v):.3f}" if isinstance(v,float) and v < 10 else str(int(round(float(v))))
                                mcols[ci].metric(s, disp)

                    if st.button(f"🗑️ Remove", key=f"rem_{i}_{t['name']}"):
                        to_remove.append(t["name"])

            for name in to_remove:
                st.session_state.targets = [t for t in st.session_state.targets if t["name"] != name]
            if to_remove:
                st.rerun()

            st.markdown("---")
            if st.button("🗑️ Clear Entire Target List"):
                st.session_state.targets = []
                st.rerun()

    # ── Tab 3: Compare Targets ────────────────────────────────────────────────
    with tab_compare:
        st.markdown("### 📊 Compare Your Targets")
        if len(st.session_state.targets) < 2:
            st.info("Add at least 2 players to your target list to compare them.")
        else:
            target_names = [t["name"] for t in st.session_state.targets]

            # Hitter comparison
            h_targets = [t for t in st.session_state.targets if t["type"] == "Hitter"]
            p_targets = [t for t in st.session_state.targets if t["type"] == "Pitcher"]

            if h_targets:
                st.markdown("#### Hitter Comparison")
                h_df = bat_rec[bat_rec["Name"].isin([t["name"] for t in h_targets])]
                compare_cols = [c for c in ["Name","Team","composite","HR","R","RBI","SB","AVG",
                                             "wRC+","xwOBA","xBA","Barrel%","SwStr%",
                                             "breakout_score","regression_score","profile_tag"] if c in h_df.columns]
                st.dataframe(
                    h_df[compare_cols].sort_values("composite", ascending=False)
                    .style.background_gradient(subset=["composite"], cmap="RdYlGn"),
                    use_container_width=True, hide_index=True
                )

                # Radar comparison
                z_h = ["z_HR","z_R","z_RBI","z_SB","z_AVG"]
                z_h = [c for c in z_h if c in h_df.columns]
                if z_h:
                    fig_comp = go.Figure()
                    labels = [c.replace("z_","") for c in z_h]
                    colors = px.colors.qualitative.Plotly
                    for ci, (_, row) in enumerate(h_df.iterrows()):
                        vals = [max(-3,min(3,float(row.get(c,0)))) for c in z_h]
                        fig_comp.add_trace(go.Scatterpolar(
                            r=vals+[vals[0]], theta=labels+[labels[0]],
                            fill="toself", name=row["Name"],
                            line_color=colors[ci % len(colors)],
                        ))
                    fig_comp.update_layout(
                        polar=dict(radialaxis=dict(range=[-3,3])),
                        template="plotly_dark", height=400,
                        legend=dict(orientation="h", y=-0.1)
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)

            if p_targets:
                st.markdown("#### Pitcher Comparison")
                p_df = pit_rec[pit_rec["Name"].isin([t["name"] for t in p_targets])]
                compare_cols = [c for c in ["Name","Team","composite","W","ERA","WHIP","SO",
                                             "xFIP","SIERA","K%","SwStr%","LOB%",
                                             "breakout_score","regression_score","profile_tag"] if c in p_df.columns]
                st.dataframe(
                    p_df[compare_cols].sort_values("composite", ascending=False)
                    .style.background_gradient(subset=["composite"], cmap="RdYlGn"),
                    use_container_width=True, hide_index=True
                )


# ═════════════════════════════════════════════════════════════
#  PAGE 6 — DRAFT ROOM
# ═════════════════════════════════════════════════════════════

elif page == "⚙️ Weight Dashboard":
    st.title("⚙️ Composite Score Weight Dashboard")
    st.caption("Manually tune how each stat contributes to the composite draft value score. Scores recalculate instantly.")

    st.info("💡 **How it works:** Each category (HR, R, RBI, SB, AVG for hitters; W, ERA, WHIP, K for pitchers) is scored using a weighted blend of underlying stats. Adjust the sliders to reflect your league's priorities. Set a weight to 0 to exclude a stat entirely.")

    tab_hw, tab_pw, tab_preview = st.tabs(["⚾ Hitter Weights", "🎯 Pitcher Weights", "👁️ Live Preview"])

    # ── Default weight definitions ────────────────────────────────────────────
    default_hitter_weights = {
        "HR":  {"HR": 1.0, "Barrel%": 0.7, "Hard%": 0.4},
        "R":   {"R":  1.0, "OBP":     0.5, "wRC+":  0.4},
        "RBI": {"RBI":1.0, "wOBA":    0.5, "Hard%": 0.3},
        "SB":  {"SB": 1.0, "Spd":     0.7},
        "AVG": {"AVG":1.0, "xwOBA":   0.6, "BABIP": -0.25},
    }
    default_pitcher_weights = {
        "W":    {"W":    1.0},
        "ERA":  {"ERA":  0.6, "xFIP":  0.6, "SIERA": 0.5},
        "WHIP": {"WHIP": 0.8, "BB%":   0.5},
        "K":    {"SO":   1.0, "K%":    0.8, "SwStr%":0.5},
    }

    # Category-level weights (how much each category contributes to composite)
    default_cat_weights_h = {"HR":1.0,"R":1.0,"RBI":1.0,"SB":1.0,"AVG":1.0}
    default_cat_weights_p = {"W":1.0,"ERA":1.0,"WHIP":1.0,"K":1.0}

    # ── Session state for weights ─────────────────────────────────────────────
    if "hw" not in st.session_state:
        st.session_state.hw = {cat: dict(stats) for cat, stats in default_hitter_weights.items()}
    if "pw" not in st.session_state:
        st.session_state.pw = {cat: dict(stats) for cat, stats in default_pitcher_weights.items()}
    if "cwh" not in st.session_state:
        st.session_state.cwh = dict(default_cat_weights_h)
    if "cwp" not in st.session_state:
        st.session_state.cwp = dict(default_cat_weights_p)

    # ── Helper to build custom-weighted scores ────────────────────────────────
    def custom_score_hitters(df, stat_weights, cat_weights):
        df = df.copy()
        z_cols = []
        for cat, metrics in stat_weights.items():
            tot = sum(abs(w) for w in metrics.values())
            if tot == 0:
                df[f"z_{cat}"] = 0.0
                z_cols.append(f"z_{cat}")
                continue
            w_sum = pd.Series(0.0, index=df.index)
            for col, w in metrics.items():
                if col in df.columns:
                    w_sum += _z(df[col].fillna(df[col].median())) * w
            df[f"z_{cat}"] = (w_sum / tot).round(2)
            z_cols.append(f"z_{cat}")
        # weighted composite using cat weights
        composite = pd.Series(0.0, index=df.index)
        tot_cat = sum(abs(v) for v in cat_weights.values())
        for cat, cw in cat_weights.items():
            zc = f"z_{cat}"
            if zc in df.columns and tot_cat > 0:
                composite += df[zc] * cw / tot_cat
        df["composite"] = composite.round(2)
        df["rank"] = df["composite"].rank(ascending=False).astype(int)
        return df

    def custom_score_pitchers(df, stat_weights, cat_weights):
        df = df.copy()
        lower_better = {"ERA","WHIP"}
        z_cols = []
        for cat, metrics in stat_weights.items():
            tot = sum(abs(w) for w in metrics.values())
            if tot == 0:
                df[f"z_{cat}"] = 0.0
                z_cols.append(f"z_{cat}")
                continue
            w_sum = pd.Series(0.0, index=df.index)
            for col, w in metrics.items():
                if col in df.columns:
                    z = _z(df[col].fillna(df[col].median()))
                    w_sum += (-z if cat in lower_better else z) * w
            df[f"z_{cat}"] = (w_sum / tot).round(2)
            z_cols.append(f"z_{cat}")
        composite = pd.Series(0.0, index=df.index)
        tot_cat = sum(abs(v) for v in cat_weights.values())
        for cat, cw in cat_weights.items():
            zc = f"z_{cat}"
            if zc in df.columns and tot_cat > 0:
                composite += df[zc] * cw / tot_cat
        df["composite"] = composite.round(2)
        df["rank"] = df["composite"].rank(ascending=False).astype(int)
        return df

    # ── TAB 1: Hitter Weights ─────────────────────────────────────────────────
    with tab_hw:
        st.markdown("### ⚾ Hitter Stat Weights")
        st.markdown("#### Category Importance")
        st.caption("How much each Yahoo category contributes to the overall composite score.")
        cw_cols = st.columns(5)
        for i, cat in enumerate(["HR","R","RBI","SB","AVG"]):
            st.session_state.cwh[cat] = cw_cols[i].slider(
                f"{cat} importance", 0.0, 3.0,
                float(st.session_state.cwh[cat]), 0.25, key=f"cwh_{cat}"
            )

        st.markdown("---")
        st.markdown("#### Stat-Level Weights (within each category)")
        st.caption("Controls which underlying stats drive each category's z-score.")

        stat_info = {
            "HR":  {"HR":"Raw HR count","Barrel%":"Barrel rate (best HR predictor)","Hard%":"Hard contact rate"},
            "R":   {"R":"Raw R count","OBP":"On-base percentage","wRC+":"Weighted runs created+"},
            "RBI": {"RBI":"Raw RBI count","wOBA":"Weighted on-base average","Hard%":"Hard contact rate"},
            "SB":  {"SB":"Raw SB count","Spd":"Speed score (sprint speed proxy)"},
            "AVG": {"AVG":"Batting average","xwOBA":"Expected wOBA (true talent)","BABIP":"BABIP (negative = luck correction)"},
        }

        for cat, stats in default_hitter_weights.items():
            with st.expander(f"**{cat}** category weights", expanded=True):
                new_w = {}
                wcols = st.columns(len(stats))
                for i, (stat, default_val) in enumerate(stats.items()):
                    info = stat_info.get(cat, {}).get(stat, stat)
                    new_w[stat] = wcols[i].slider(
                        f"{stat}", -1.0, 2.0,
                        float(st.session_state.hw[cat].get(stat, default_val)),
                        0.05, key=f"hw_{cat}_{stat}",
                        help=info
                    )
                st.session_state.hw[cat] = new_w

        col_reset = st.columns(2)
        if col_reset[0].button("🔄 Reset Hitter Weights to Default"):
            st.session_state.hw  = {cat: dict(stats) for cat, stats in default_hitter_weights.items()}
            st.session_state.cwh = dict(default_cat_weights_h)
            st.rerun()

    # ── TAB 2: Pitcher Weights ────────────────────────────────────────────────
    with tab_pw:
        st.markdown("### 🎯 Pitcher Stat Weights")
        st.markdown("#### Category Importance")
        cw_cols_p = st.columns(4)
        for i, cat in enumerate(["W","ERA","WHIP","K"]):
            st.session_state.cwp[cat] = cw_cols_p[i].slider(
                f"{cat} importance", 0.0, 3.0,
                float(st.session_state.cwp[cat]), 0.25, key=f"cwp_{cat}"
            )

        st.markdown("---")
        st.markdown("#### Stat-Level Weights")

        stat_info_p = {
            "W":    {"W":"Raw win count"},
            "ERA":  {"ERA":"Earned run average (lower=better)","xFIP":"xFIP (lower=better)","SIERA":"SIERA (lower=better)"},
            "WHIP": {"WHIP":"WHIP (lower=better)","BB%":"Walk rate (lower=better)"},
            "K":    {"SO":"Raw strikeout count","K%":"Strikeout rate","SwStr%":"Swinging strike rate"},
        }

        for cat, stats in default_pitcher_weights.items():
            with st.expander(f"**{cat}** category weights", expanded=True):
                new_w = {}
                wcols = st.columns(len(stats))
                for i, (stat, default_val) in enumerate(stats.items()):
                    info = stat_info_p.get(cat, {}).get(stat, stat)
                    new_w[stat] = wcols[i].slider(
                        f"{stat}", 0.0, 2.0,
                        float(st.session_state.pw[cat].get(stat, default_val)),
                        0.05, key=f"pw_{cat}_{stat}",
                        help=info
                    )
                st.session_state.pw[cat] = new_w

        if st.button("🔄 Reset Pitcher Weights to Default"):
            st.session_state.pw  = {cat: dict(stats) for cat, stats in default_pitcher_weights.items()}
            st.session_state.cwp = dict(default_cat_weights_p)
            st.rerun()

    # ── TAB 3: Live Preview ───────────────────────────────────────────────────
    with tab_preview:
        st.markdown("### 👁️ Live Rankings Preview")
        st.caption("Rankings recalculated in real time using your custom weights. Compare against the default composite.")

        preview_type = st.radio("", ["Hitters","Pitchers"], horizontal=True, key="preview_type")

        if preview_type == "Hitters":
            custom_h = custom_score_hitters(
                bat_rec.drop(columns=["composite","rank"], errors="ignore"),
                st.session_state.hw,
                st.session_state.cwh
            )
            # Merge default rank for comparison
            default_ranks = bat_rec[["Name","composite","rank"]].rename(
                columns={"composite":"default_composite","rank":"default_rank"}
            )
            custom_h = custom_h.merge(default_ranks, on="Name", how="left")
            custom_h["rank_change"] = custom_h["default_rank"] - custom_h["rank"]
            custom_h = custom_h.sort_values("rank")

            show_cols = [c for c in ["Name","Team","rank","composite","default_rank","default_composite",
                                      "rank_change","HR","R","RBI","SB","AVG","xwOBA","Barrel%",
                                      "z_HR","z_R","z_RBI","z_SB","z_AVG"] if c in custom_h.columns]

            def style_rank_change(val):
                try:
                    v = int(val)
                    if v > 5:  return "color:#21C354; font-weight:bold"
                    if v > 0:  return "color:#21C354"
                    if v < -5: return "color:#FF4B4B; font-weight:bold"
                    if v < 0:  return "color:#FF4B4B"
                except: pass
                return ""

            styled = (
                custom_h[show_cols].head(50).style
                .map(style_rank_change, subset=["rank_change"])
                .map(style_z, subset=[c for c in show_cols if c.startswith("z_")])
                .background_gradient(subset=["composite"], cmap="RdYlGn")
                .format({"composite":"{:.2f}","default_composite":"{:.2f}",
                         "rank_change":"{:+d}"})
            )
            st.dataframe(styled, use_container_width=True, height=520)

            # Category weight bar chart
            st.markdown("#### Your Category Weights vs Default")
            weight_df = pd.DataFrame({
                "Category": list(st.session_state.cwh.keys()),
                "Your Weight": list(st.session_state.cwh.values()),
                "Default": [1.0] * len(st.session_state.cwh),
            })
            fig_w = px.bar(weight_df.melt("Category", var_name="Type", value_name="Weight"),
                           x="Category", y="Weight", color="Type", barmode="group",
                           template="plotly_dark", color_discrete_sequence=["#4fc3f7","#666"],
                           title="Category Importance Weights")
            fig_w.update_layout(height=280)
            st.plotly_chart(fig_w, use_container_width=True)

        else:
            custom_p = custom_score_pitchers(
                pit_rec.drop(columns=["composite","rank"], errors="ignore"),
                st.session_state.pw,
                st.session_state.cwp
            )
            default_ranks_p = pit_rec[["Name","composite","rank"]].rename(
                columns={"composite":"default_composite","rank":"default_rank"}
            )
            custom_p = custom_p.merge(default_ranks_p, on="Name", how="left")
            custom_p["rank_change"] = custom_p["default_rank"] - custom_p["rank"]
            custom_p = custom_p.sort_values("rank")

            show_cols_p = [c for c in ["Name","Team","rank","composite","default_rank","default_composite",
                                        "rank_change","W","ERA","WHIP","SO","xFIP","SIERA","K%",
                                        "z_W","z_ERA","z_WHIP","z_K"] if c in custom_p.columns]

            def style_rank_change_p(val):
                try:
                    v = int(val)
                    if v > 5:  return "color:#21C354; font-weight:bold"
                    if v > 0:  return "color:#21C354"
                    if v < -5: return "color:#FF4B4B; font-weight:bold"
                    if v < 0:  return "color:#FF4B4B"
                except: pass
                return ""

            styled_p = (
                custom_p[show_cols_p].head(50).style
                .map(style_rank_change_p, subset=["rank_change"])
                .map(style_z, subset=[c for c in show_cols_p if c.startswith("z_")])
                .background_gradient(subset=["composite"], cmap="RdYlGn")
                .format({"composite":"{:.2f}","default_composite":"{:.2f}",
                         "rank_change":"{:+d}"})
            )
            st.dataframe(styled_p, use_container_width=True, height=520)

            weight_df_p = pd.DataFrame({
                "Category": list(st.session_state.cwp.keys()),
                "Your Weight": list(st.session_state.cwp.values()),
                "Default": [1.0] * len(st.session_state.cwp),
            })
            fig_wp = px.bar(weight_df_p.melt("Category", var_name="Type", value_name="Weight"),
                            x="Category", y="Weight", color="Type", barmode="group",
                            template="plotly_dark", color_discrete_sequence=["#4fc3f7","#666"],
                            title="Category Importance Weights")
            fig_wp.update_layout(height=280)
            st.plotly_chart(fig_wp, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 💡 Weight Tuning Tips")
        tips_w = {
            "SB-heavy league": "Raise SB category importance to 2.0–3.0 and increase Spd weight to 1.5 within SB.",
            "HR-heavy league": "Raise HR importance to 2.0 and boost Barrel% weight to 1.5 — it's the best HR predictor.",
            "Strikeout-focused": "Raise K importance to 2.0–3.0, boost SwStr% weight to 1.5 within K.",
            "AVG matters a lot": "Raise AVG importance, increase xwOBA weight, and reduce the BABIP negative weight to 0.",
            "ERA/WHIP ratio league": "Raise ERA and WHIP importance, increase SIERA weight as it's the most predictive ERA estimator.",
            "Wins don't matter": "Set W importance to 0 to completely ignore wins in composite scoring.",
        }
        for tip, desc in tips_w.items():
            with st.expander(f"**{tip}**"):
                st.write(desc)


elif page == "🏟️ Draft Room":
    st.title("🏟️ Live Draft Room")
    st.caption("Mark players as drafted. Your board updates in real time.")

    left, right = st.columns([3, 1])

    with left:
        tab_h, tab_p = st.tabs(["⚾ Hitters", "🎯 Pitchers"])

        with tab_h:
            avail_h = (
                bat_rec[~bat_rec["Name"].isin(st.session_state.drafted_h)]
                .sort_values("composite", ascending=False).reset_index(drop=True)
            )
            avail_h.index += 1
            show_h = [c for c in ["Name","Team","profile_tag","composite",
                                   "HR","R","RBI","SB","AVG","wRC+","xwOBA",
                                   "Barrel%","breakout_score","z_HR","z_SB","regression_risk"]
                      if c in avail_h.columns]
            # Highlight target list players
            is_target = avail_h["Name"].isin([t["name"] for t in st.session_state.targets])
            st.markdown(f"**{len(avail_h)} hitters available** &nbsp;|&nbsp; "
                        f"🎯 {is_target.sum()} on your target list")
            st.dataframe(
                avail_h[show_h].style
                    .map(style_risk, subset=["regression_risk"])
                    .map(style_z, subset=[c for c in show_h if c.startswith("z_")])
                    .map(style_breakout, subset=["breakout_score"]),
                use_container_width=True, height=420
            )
            pick_h = st.selectbox("Select hitter", [""] + avail_h["Name"].tolist(), key="sel_h")
            ca, cb, cc = st.columns(3)
            if ca.button("✅ Add to MY team", key="btn_add_h") and pick_h:
                st.session_state.drafted_h.add(pick_h)
                st.session_state.my_h.append(pick_h)
                st.rerun()
            if cb.button("❌ Drafted (not me)", key="btn_skip_h") and pick_h:
                st.session_state.drafted_h.add(pick_h)
                st.rerun()
            if cc.button("🎯 Add to Targets", key="btn_target_h") and pick_h:
                rec_row = bat_rec[bat_rec["Name"] == pick_h]
                entry = {"name": pick_h, "type": "Hitter",
                         "tag": rec_row.iloc[0].get("profile_tag","—") if not rec_row.empty else "—",
                         "composite": float(rec_row.iloc[0].get("composite",0)) if not rec_row.empty else 0,
                         "note": "Added from draft room"}
                if not any(t["name"] == pick_h for t in st.session_state.targets):
                    st.session_state.targets.append(entry)
                    st.success(f"🎯 {pick_h} added to targets!")

        with tab_p:
            avail_p = (
                pit_rec[~pit_rec["Name"].isin(st.session_state.drafted_p)]
                .sort_values("composite", ascending=False).reset_index(drop=True)
            )
            avail_p.index += 1
            show_p = [c for c in ["Name","Team","profile_tag","composite",
                                   "W","ERA","WHIP","SO","xFIP","SIERA","K%",
                                   "breakout_score","z_ERA","z_K","regression_risk"]
                      if c in avail_p.columns]
            st.markdown(f"**{len(avail_p)} pitchers available**")
            st.dataframe(
                avail_p[show_p].style
                    .map(style_risk, subset=["regression_risk"])
                    .map(style_z, subset=[c for c in show_p if c.startswith("z_")])
                    .map(style_breakout, subset=["breakout_score"]),
                use_container_width=True, height=420
            )
            pick_p = st.selectbox("Select pitcher", [""] + avail_p["Name"].tolist(), key="sel_p")
            cd, ce, cf = st.columns(3)
            if cd.button("✅ Add to MY team", key="btn_add_p") and pick_p:
                st.session_state.drafted_p.add(pick_p)
                st.session_state.my_p.append(pick_p)
                st.rerun()
            if ce.button("❌ Drafted (not me)", key="btn_skip_p") and pick_p:
                st.session_state.drafted_p.add(pick_p)
                st.rerun()
            if cf.button("🎯 Add to Targets", key="btn_target_p") and pick_p:
                rec_row = pit_rec[pit_rec["Name"] == pick_p]
                entry = {"name": pick_p, "type": "Pitcher",
                         "tag": rec_row.iloc[0].get("profile_tag","—") if not rec_row.empty else "—",
                         "composite": float(rec_row.iloc[0].get("composite",0)) if not rec_row.empty else 0,
                         "note": "Added from draft room"}
                if not any(t["name"] == pick_p for t in st.session_state.targets):
                    st.session_state.targets.append(entry)
                    st.success(f"🎯 {pick_p} added to targets!")

    # ── Right panel: My Team ─────────────────────────────────────────────────
    with right:
        st.markdown("### 🏆 My Team")

        if st.session_state.my_h:
            st.markdown("**Hitters**")
            for name in st.session_state.my_h:
                row = bat_rec[bat_rec["Name"] == name]
                risk = row.iloc[0]["regression_risk"] if not row.empty else "Low"
                tag  = row.iloc[0]["profile_tag"] if not row.empty else ""
                dot  = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(risk,"⚪")
                st.markdown(f"{dot} **{name}** {tag}")

        if st.session_state.my_p:
            st.markdown("**Pitchers**")
            for name in st.session_state.my_p:
                row = pit_rec[pit_rec["Name"] == name]
                risk = row.iloc[0]["regression_risk"] if not row.empty else "Low"
                tag  = row.iloc[0]["profile_tag"] if not row.empty else ""
                dot  = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(risk,"⚪")
                st.markdown(f"{dot} **{name}** {tag}")

        # category strength
        my_h_df = bat_rec[bat_rec["Name"].isin(st.session_state.my_h)]
        my_p_df = pit_rec[pit_rec["Name"].isin(st.session_state.my_p)]
        if not my_h_df.empty or not my_p_df.empty:
            st.markdown("---")
            st.markdown("**Category Strength**")
            for df_chunk in [my_h_df, my_p_df]:
                for zc in [c for c in df_chunk.columns if c.startswith("z_")]:
                    val   = df_chunk[zc].mean()
                    cat   = zc.replace("z_","")
                    color = "#21C354" if val > 0.5 else "#FFA500" if val > -0.5 else "#FF4B4B"
                    filled = int(min(10, max(0, (val + 3) / 6 * 10)))
                    bar = "█" * filled + "░" * (10 - filled)
                    st.markdown(
                        f"**{cat}** {val:+.2f} <span style='color:{color}'>{bar}</span>",
                        unsafe_allow_html=True
                    )

        # targets still available
        avail_targets = [
            t for t in st.session_state.targets
            if t["name"] not in st.session_state.drafted_h
            and t["name"] not in st.session_state.drafted_p
        ]
        if avail_targets:
            st.markdown("---")
            st.markdown(f"**🎯 Targets still available ({len(avail_targets)})**")
            for t in avail_targets:
                st.caption(f"• {t['name']} ({t['type']})")

        st.markdown("---")
        total_drafted = len(st.session_state.drafted_h) + len(st.session_state.drafted_p)
        st.caption(f"{total_drafted} players drafted total")
        if st.button("🔄 Reset Draft"):
            for k in ["drafted_h","drafted_p","my_h","my_p"]:
                del st.session_state[k]
            st.rerun()