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
#  DEMO DATA
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
        g_max  = 90  if yr == 2025 else 162
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
        ip_max = 90  if yr == 2025 else 200
        ip_min = 45  if yr == 2025 else 100
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
MIN_PA    = 100
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
            [pd.read_csv(os.path.join(CACHE_DIR, f)) for f in bat_files], ignore_index=True)
        pit_all = pd.concat(
            [pd.read_csv(os.path.join(CACHE_DIR, f)) for f in pit_files], ignore_index=True)
    else:
        try:
            from pybaseball import batting_stats, pitching_stats, cache as pb_cache
            pb_cache.enable()
            bat_frames, pit_frames = [], []
            for yr in YEARS:
                try:
                    b = batting_stats(yr, qual=MIN_PA); b["Season"] = yr; bat_frames.append(b)
                    p = pitching_stats(yr, qual=MIN_IP); p["Season"] = yr; pit_frames.append(p)
                except Exception:
                    pass
            if bat_frames and pit_frames:
                bat_all = pd.concat(bat_frames, ignore_index=True)
                pit_all = pd.concat(pit_frames, ignore_index=True)
                for yr in YEARS:
                    b = bat_all[bat_all["Season"] == yr]
                    p = pit_all[pit_all["Season"] == yr]
                    if not b.empty: b.to_csv(os.path.join(CACHE_DIR, f"batting_{yr}.csv"), index=False)
                    if not p.empty: p.to_csv(os.path.join(CACHE_DIR, f"pitching_{yr}.csv"), index=False)
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
# ─────────────────────────────────────────────────────────────

def _trend_slope(series: list) -> float:
    if len(series) < 2:
        return 0.0
    x = np.arange(len(series))
    slope, *_ = scipy_stats.linregress(x, series)
    return float(slope)


def deep_analysis(df: pd.DataFrame, all_df: pd.DataFrame, ptype: str) -> pd.DataFrame:
    df = df.copy()
    regression_risks, breakout_scores, regression_scores = [], [], []
    profile_tags, summaries = [], []

    for _, row in df.iterrows():
        name = row.get("Name", "")
        hist = all_df[all_df["Name"] == name].sort_values("Season")
        reg_flags, breakout_sigs, summary_lines = [], [], []

        if ptype == "hitter":
            avg    = row.get("AVG",   np.nan); xba    = row.get("xBA",    np.nan)
            babip  = row.get("BABIP", np.nan); hard   = row.get("Hard%",  np.nan)
            barrel = row.get("Barrel%",np.nan); hr    = row.get("HR",     np.nan)
            pa     = row.get("PA",    600);     sb    = row.get("SB",     np.nan)
            spd    = row.get("Spd",   np.nan); kpct   = row.get("K%",    np.nan)
            bbpct  = row.get("BB%",   np.nan); ev    = row.get("EV",     np.nan)
            la     = row.get("LA",    np.nan); wrcplus= row.get("wRC+",  np.nan)
            age    = row.get("Age",   27)

            if pd.notna(avg) and pd.notna(xba):
                diff = avg - xba
                if diff > 0.030:
                    reg_flags.append(f"AVG ({avg:.3f}) outpacing xBA ({xba:.3f}) by +{diff:.3f} — expect decline")
                elif diff < -0.025:
                    breakout_sigs.append(f"AVG ({avg:.3f}) below xBA ({xba:.3f}) by {diff:.3f} — AVG should rise")

            if pd.notna(babip):
                if babip > 0.340 and (pd.isna(hard) or hard < 0.40):
                    reg_flags.append(f"BABIP ({babip:.3f}) well above league avg (.295) without elite contact quality")
                elif babip < 0.265 and pd.notna(hard) and hard > 0.38:
                    breakout_sigs.append(f"BABIP ({babip:.3f}) unusually low despite solid Hard% ({hard:.1%}) — due for positive BABIP luck")

            if pd.notna(hr) and pd.notna(barrel) and pa and pa > 0:
                hr_rate = hr / pa
                if hr_rate > 0.058 and barrel < 0.09:
                    reg_flags.append(f"HR/PA ({hr_rate:.3f}) elevated vs Barrel% ({barrel:.1%}) — HR total likely to drop")
                elif barrel > 0.12 and hr_rate < 0.035:
                    breakout_sigs.append(f"Elite Barrel% ({barrel:.1%}) not yet reflected in HR count — power breakout candidate")

            if pd.notna(ev) and pd.notna(la):
                if ev > 91 and 10 <= la <= 18:
                    breakout_sigs.append(f"Elite EV ({ev} mph) + optimal launch angle ({la}°) — elite contact profile")
                elif ev < 87:
                    reg_flags.append(f"Below-avg EV ({ev} mph) suggests contact quality concern")

            if pd.notna(kpct):
                if kpct > 0.28:
                    reg_flags.append(f"High K% ({kpct:.1%}) limits floor in AVG/OBP categories")
                elif kpct < 0.16 and pd.notna(bbpct) and bbpct > 0.10:
                    breakout_sigs.append(f"Elite plate discipline: K% ({kpct:.1%}) + BB% ({bbpct:.1%}) — sustainable OBP/AVG")

            if pd.notna(sb) and pd.notna(spd):
                if sb > 25 and spd < 4.5:
                    reg_flags.append(f"High SB ({int(sb)}) vs low Spd score ({spd}) — SB pace unsustainable")
                elif spd > 7.0 and sb < 15:
                    breakout_sigs.append(f"Elite speed (Spd {spd}) underutilized — SB breakout possible with green light")

            if pd.notna(age):
                if age <= 25 and pd.notna(wrcplus) and wrcplus > 115:
                    breakout_sigs.append(f"Age {int(age)} with wRC+ {int(wrcplus)} — still on upside of development curve")
                elif age >= 33:
                    reg_flags.append(f"Age {int(age)} — age-related decline risk increases")

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

        else:  # pitcher
            era   = row.get("ERA",   np.nan); xfip  = row.get("xFIP",  np.nan)
            siera = row.get("SIERA", np.nan); lob   = row.get("LOB%",  np.nan)
            babip = row.get("BABIP", np.nan); hrfb  = row.get("HR/FB", np.nan)
            kpct  = row.get("K%",    np.nan); bbpct = row.get("BB%",   np.nan)
            swstr = row.get("SwStr%",np.nan); gb    = row.get("GB%",   np.nan)
            age   = row.get("Age",   28);     csw   = row.get("CSW%",  np.nan)

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

            if pd.notna(lob):
                if lob > 0.80:
                    reg_flags.append(f"LOB% ({lob:.1%}) unsustainably high (league avg ~72%) — ERA/WHIP will worsen")
                elif lob < 0.66:
                    breakout_sigs.append(f"LOB% ({lob:.1%}) unluckily low — ERA/WHIP should improve with normal strand rates")

            if pd.notna(babip):
                if babip < 0.262:
                    reg_flags.append(f"Low BABIP ({babip:.3f}) propping up ERA — opponents will get more hits")
                elif babip > 0.318:
                    breakout_sigs.append(f"High BABIP ({babip:.3f}) inflating ERA — underlying stuff is better than results show")

            if pd.notna(hrfb):
                if hrfb < 0.072:
                    reg_flags.append(f"HR/FB ({hrfb:.1%}) below average — HRs allowed will normalize upward")
                elif hrfb > 0.145:
                    breakout_sigs.append(f"HR/FB ({hrfb:.1%}) elevated — could drop, improving ERA")

            if pd.notna(kpct) and pd.notna(swstr):
                if kpct > 0.28 and swstr > 0.13:
                    breakout_sigs.append(f"Elite strikeout profile: K% {kpct:.1%} + SwStr% {swstr:.1%} — sustainable ace-level stuff")
            if pd.notna(bbpct) and bbpct > 0.11:
                reg_flags.append(f"High BB% ({bbpct:.1%}) — control issues elevate ERA/WHIP ceiling")
            if pd.notna(gb) and gb > 0.52:
                breakout_sigs.append(f"Elite GB% ({gb:.1%}) limits HR exposure — good for ERA stability")
            if pd.notna(csw) and csw > 0.32:
                breakout_sigs.append(f"High CSW% ({csw:.1%}) — above-average pitch quality / command")

            if pd.notna(age):
                if age <= 26 and pd.notna(kpct) and kpct > 0.24:
                    breakout_sigs.append(f"Young arm (age {int(age)}) with strong K% ({kpct:.1%}) — development upside remains")
                elif age >= 35:
                    reg_flags.append(f"Age {int(age)} — injury and decline risk elevated for pitchers")

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

        b_score = min(100, len(breakout_sigs) * 22 + (5 if len(hist) >= 4 else 0))
        r_score = min(100, len(reg_flags) * 22)

        # Profile tag
        if ptype == "hitter":
            barrel_t = row.get("Barrel%", np.nan); spd_t  = row.get("Spd",  np.nan)
            age_t    = row.get("Age",      28);     wrc_t  = row.get("wRC+", np.nan)
            sb_t     = row.get("SB",       np.nan); kpct_t = row.get("K%",   np.nan)
            if   b_score >= 66 and r_score < 22:  tag = "🚀 Elite Breakout"
            elif b_score >= 44 and r_score < 22:  tag = "📈 Breakout Candidate"
            elif r_score >= 66:                   tag = "🚨 High Regression Risk"
            elif r_score >= 44 and b_score < 22:  tag = "📉 Regression Risk"
            elif b_score >= 44 and r_score >= 44: tag = "⚖️ High Ceiling / High Risk"
            elif b_score >= 22 and r_score >= 22: tag = "⚖️ Mixed Signals"
            elif pd.notna(age_t) and age_t <= 24 and pd.notna(wrc_t) and wrc_t > 110: tag = "🌱 Young Talent"
            elif pd.notna(spd_t) and spd_t > 7.0 and pd.notna(sb_t) and sb_t < 15:   tag = "💨 Speed Sleeper"
            elif pd.notna(barrel_t) and barrel_t > 0.12 and b_score > 0:              tag = "💣 Power Upside"
            elif pd.notna(kpct_t) and kpct_t < 0.15 and b_score > 0:                 tag = "🎯 Contact Upside"
            elif b_score > 0:  tag = "👀 Undervalued"
            elif r_score > 0:  tag = "⚠️ Slight Risk"
            else:              tag = "✅ Stable"
        else:
            kpct_t  = row.get("K%",     np.nan); gb_t    = row.get("GB%",    np.nan)
            age_t   = row.get("Age",    28);      swstr_t = row.get("SwStr%", np.nan)
            if   b_score >= 66 and r_score < 22:  tag = "🚀 Ace Breakout"
            elif b_score >= 44 and r_score < 22:  tag = "📈 Breakout Candidate"
            elif r_score >= 66:                   tag = "🚨 High Regression Risk"
            elif r_score >= 44 and b_score < 22:  tag = "📉 Regression Risk"
            elif b_score >= 44 and r_score >= 44: tag = "⚖️ High Ceiling / High Risk"
            elif b_score >= 22 and r_score >= 22: tag = "⚖️ Mixed Signals"
            elif pd.notna(age_t) and age_t <= 25 and pd.notna(kpct_t) and kpct_t > 0.24: tag = "🌱 Young Arm"
            elif pd.notna(gb_t) and gb_t > 0.52 and b_score > 0:                          tag = "🪱 GB Specialist Upside"
            elif pd.notna(swstr_t) and swstr_t > 0.14 and b_score > 0:                    tag = "🎯 Swing-Miss Upside"
            elif b_score > 0:  tag = "👀 Undervalued"
            elif r_score > 0:  tag = "⚠️ Slight Risk"
            else:              tag = "✅ Stable"

        risk = "High" if r_score >= 44 else "Medium" if r_score >= 22 else "Low"

        # Narrative
        narrative_parts = []
        if ptype == "hitter":
            wrc_n = row.get("wRC+", np.nan); barrel_n = row.get("Barrel%", np.nan)
            hr_n  = row.get("HR",   np.nan); sb_n     = row.get("SB",      np.nan)
            spd_n = row.get("Spd",  np.nan); age_n    = row.get("Age",     28)
            if pd.notna(wrc_n):
                if   wrc_n >= 140: narrative_parts.append(f"One of the most productive hitters in baseball with a wRC+ of {int(wrc_n)}, placing him in elite company.")
                elif wrc_n >= 120: narrative_parts.append(f"A legitimate fantasy anchor with a wRC+ of {int(wrc_n)}, consistently producing above-average value.")
                elif wrc_n >= 100: narrative_parts.append(f"A solid contributor with a wRC+ of {int(wrc_n)}, providing league-average or better production.")
                else:              narrative_parts.append(f"A below-average hitter by wRC+ ({int(wrc_n)}), limiting his ceiling in rate categories.")
            if pd.notna(barrel_n) and pd.notna(hr_n):
                if   barrel_n >= 0.14: narrative_parts.append(f"His Barrel% of {barrel_n:.1%} is elite-tier — his HR output ({int(hr_n)}) is well-supported by real contact quality.")
                elif barrel_n >= 0.09: narrative_parts.append(f"With a Barrel% of {barrel_n:.1%}, his power is real but not top-tier — a reliable mid-range HR contributor.")
                else:                  narrative_parts.append(f"A below-average Barrel% ({barrel_n:.1%}) suggests his power numbers may be driven more by luck than contact quality.")
            if pd.notna(sb_n) and pd.notna(spd_n):
                if   sb_n >= 30 and spd_n >= 6.0: narrative_parts.append(f"Elite speed profile — {int(sb_n)} SB backed by Spd score of {spd_n} makes him a top SB asset.")
                elif sb_n >= 20:                   narrative_parts.append(f"A useful SB contributor with {int(sb_n)} steals, though his Spd score of {spd_n} warrants monitoring.")
                elif spd_n >= 7.0 and sb_n < 15:  narrative_parts.append(f"Elite speed score ({spd_n}) is being underutilized — a green light or lineup change could unlock SB upside.")
            if pd.notna(age_n):
                if   age_n <= 23: narrative_parts.append(f"At just {int(age_n)}, he's barely scratched the surface of his development ceiling — buy-high is still appropriate.")
                elif age_n <= 27: narrative_parts.append(f"At {int(age_n)}, he's in the prime performance window — expect stable or improving production.")
                elif age_n >= 34: narrative_parts.append(f"At {int(age_n)}, age-related decline is a real concern. Monitor spring training before investing heavily.")
        else:
            era_n   = row.get("ERA",    np.nan); xfip_n  = row.get("xFIP",   np.nan)
            kpct_n  = row.get("K%",     np.nan); bbpct_n = row.get("BB%",    np.nan)
            swstr_n = row.get("SwStr%", np.nan); gb_n    = row.get("GB%",    np.nan)
            age_n   = row.get("Age",    28)
            if pd.notna(era_n) and pd.notna(xfip_n):
                if   era_n <= 3.00 and xfip_n <= 3.20: narrative_parts.append(f"An elite pitcher — ERA of {era_n:.2f} backed by xFIP of {xfip_n:.2f} means his dominance is real and repeatable.")
                elif era_n <= 3.50 and xfip_n <= 3.50: narrative_parts.append(f"A legitimate No.1/2 starter. ERA ({era_n:.2f}) and xFIP ({xfip_n:.2f}) are aligned, supporting strong future performance.")
                elif era_n > xfip_n + 0.60:            narrative_parts.append(f"ERA ({era_n:.2f}) is being inflated by bad luck — xFIP of {xfip_n:.2f} suggests he's pitching much better than results. Buy low.")
                elif xfip_n > era_n + 0.60:            narrative_parts.append(f"ERA ({era_n:.2f}) looks better than underlying metrics (xFIP {xfip_n:.2f}) — some regression in ERA/WHIP is likely. Sell high.")
            if pd.notna(kpct_n) and pd.notna(swstr_n):
                if   kpct_n >= 0.30 and swstr_n >= 0.14: narrative_parts.append(f"Dominant arsenal: K% {kpct_n:.1%} and SwStr% {swstr_n:.1%} put him among the game's elite strikeout arms.")
                elif kpct_n >= 0.24:                      narrative_parts.append(f"Above-average K rate ({kpct_n:.1%}) makes him a reliable strikeout contributor.")
                elif kpct_n < 0.18:                       narrative_parts.append(f"Below-average K rate ({kpct_n:.1%}) limits his K upside — best as ERA/WHIP streamer.")
            if pd.notna(bbpct_n):
                if   bbpct_n < 0.06: narrative_parts.append(f"Exceptional command (BB% {bbpct_n:.1%}) is a major ERA/WHIP stabilizer.")
                elif bbpct_n > 0.10: narrative_parts.append(f"Control issues (BB% {bbpct_n:.1%}) create week-to-week volatility in ERA and WHIP.")
            if pd.notna(gb_n) and gb_n >= 0.52:
                narrative_parts.append(f"Elite groundball rate ({gb_n:.1%}) naturally suppresses HRs and stabilizes ERA.")
            if pd.notna(age_n):
                if   age_n <= 25: narrative_parts.append(f"Still only {int(age_n)} — more development likely ahead, ceiling not yet reached.")
                elif age_n >= 35: narrative_parts.append(f"At {int(age_n)}, durability is the primary concern. Monitor workload and IL history.")

        narrative = " ".join(narrative_parts)
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

        regression_risks.append(risk); breakout_scores.append(b_score)
        regression_scores.append(r_score); profile_tags.append(tag)
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
#  LOAD DATA & SESSION STATE
# ─────────────────────────────────────────────────────────────

bat_all, pit_all, bat_rec, pit_rec, LATEST = load_data()
ALL_YEARS = sorted(bat_all["Season"].unique().tolist())

for _k in ["drafted_h","drafted_p","my_h","my_p","targets"]:
    if _k not in st.session_state:
        st.session_state[_k] = [] if _k in ["my_h","my_p","targets"] else set()

# ─────────────────────────────────────────────────────────────
#  MONTE CARLO — top-level constants & cached functions
#  Must live here at module level (NOT inside elif) so that
#  @st.cache_data registers the function once and invalidation
#  works correctly across button presses.
# ─────────────────────────────────────────────────────────────

MC_H_CATS       = ["HR", "R", "RBI", "SB", "AVG"]
MC_P_CATS       = ["W", "ERA", "WHIP", "SO"]
MC_ALL_CATS     = MC_H_CATS + MC_P_CATS
MC_LOWER_BETTER = {"ERA", "WHIP"}
MC_COUNT_FLOORS = {"HR": 0, "R": 0, "RBI": 0, "SB": 0, "W": 0, "SO": 0}
MC_H_STATS      = ["HR","R","RBI","SB","AVG","OBP","SLG","wRC+","xwOBA","Barrel%","Hard%"]
MC_P_STATS      = ["W","ERA","WHIP","SO","K%","xFIP","SIERA","BB%","SwStr%","GB%"]


def _mc_player_dist(name, src_df, stat_cols):
    hist = src_df[src_df["Name"] == name][stat_cols].dropna(how="all")
    out = {}
    for s in stat_cols:
        vals = hist[s].dropna()
        if len(vals) >= 2:
            out[s] = (float(vals.mean()), float(vals.std()))
        elif len(vals) == 1:
            v = float(vals.iloc[0]); out[s] = (v, abs(v) * 0.15)
        else:
            out[s] = (0.0, 0.0)
    return out


def _mc_sim_player(dist, n_sim, stat_cols, lower_clip=None):
    lc = lower_clip or {}
    data = {}
    for s in stat_cols:
        mu, sd = dist.get(s, (0.0, 0.0))
        draws = np.random.normal(mu, max(sd, 1e-6), n_sim)
        if s in lc:
            draws = np.clip(draws, lc[s], None)
        data[s] = draws
    return pd.DataFrame(data)


# run_count is in the signature so every button press = unique cache key = fresh sim
@st.cache_data(show_spinner=False, ttl=3600)
def mc_run_simulation(hitters, pitchers, n_sim, injury_pct,
                      regression_pull, platoon_boost, run_count):
    np.random.seed(run_count)
    lg_h = {s: bat_all[s].mean() for s in MC_H_STATS if s in bat_all.columns}
    lg_p = {s: pit_all[s].mean() for s in MC_P_STATS if s in pit_all.columns}

    def pull(mu, la, strength):
        return mu * (1 - strength) + la * strength

    sim_h = {c: np.zeros(n_sim) for c in MC_H_CATS}
    player_sims = {}

    for name in hitters:
        dist = _mc_player_dist(name, bat_all, MC_H_STATS)
        for s in MC_H_STATS:
            if s in dist and s in lg_h:
                mu, sd = dist[s]; dist[s] = (pull(mu, lg_h[s], regression_pull), sd)
        if platoon_boost and "Barrel%" in dist and "HR" in dist:
            bmu, _ = dist["Barrel%"]; hmu, hsd = dist["HR"]
            dist["HR"] = (hmu * 1.10 if bmu > 0.12 else hmu * 0.92 if bmu < 0.07 else hmu, hsd)
        sims = _mc_sim_player(dist, n_sim, MC_H_STATS, MC_COUNT_FLOORS)
        imask = np.random.random(n_sim) < 0.30
        red   = np.random.uniform(injury_pct * 0.5, injury_pct * 1.5, n_sim)
        for s in ["HR", "R", "RBI", "SB"]:
            if s in sims.columns:
                sims[s] = np.clip(np.where(imask, sims[s] * (1 - red), sims[s]), 0, None)
        player_sims[name] = sims
        for s in ["HR", "R", "RBI", "SB"]:
            if s in sims.columns: sim_h[s] += sims[s].values
        if "AVG" in sims.columns: sim_h["AVG"] += sims["AVG"].values

    n_h = max(len(hitters), 1); sim_h["AVG"] /= n_h
    sim_p = {c: np.zeros(n_sim) for c in MC_P_CATS}

    for name in pitchers:
        dist = _mc_player_dist(name, pit_all, MC_P_STATS)
        for s in MC_P_STATS:
            if s in dist and s in lg_p:
                mu, sd = dist[s]; dist[s] = (pull(mu, lg_p[s], regression_pull), sd)
        if platoon_boost and "SwStr%" in dist and "SO" in dist:
            swmu, _ = dist["SwStr%"]; somu, sosd = dist["SO"]
            dist["SO"] = (somu * 1.08 if swmu > 0.14 else somu * 0.93 if swmu < 0.09 else somu, sosd)
        sims = _mc_sim_player(dist, n_sim, MC_P_STATS, MC_COUNT_FLOORS)
        imask = np.random.random(n_sim) < 0.25
        red   = np.random.uniform(injury_pct * 0.5, injury_pct * 1.5, n_sim)
        for s in ["W", "SO"]:
            if s in sims.columns:
                sims[s] = np.clip(np.where(imask, sims[s] * (1 - red), sims[s]), 0, None)
        player_sims[name] = sims
        for s in ["W", "SO"]:
            if s in sims.columns: sim_p[s] += sims[s].values
        for s in ["ERA", "WHIP"]:
            if s in sims.columns: sim_p[s] += sims[s].values

    n_p = max(len(pitchers), 1); sim_p["ERA"] /= n_p; sim_p["WHIP"] /= n_p
    team_df = pd.DataFrame({
        "HR": sim_h["HR"], "R": sim_h["R"], "RBI": sim_h["RBI"],
        "SB": sim_h["SB"], "AVG": sim_h["AVG"],
        "W": sim_p["W"], "ERA": sim_p["ERA"], "WHIP": sim_p["WHIP"], "SO": sim_p["SO"],
    })
    return team_df, player_sims


@st.cache_data(ttl=3600)
def mc_opponent_pool(n_teams, n_sim, run_count):
    np.random.seed(run_count + 999)
    all_h = bat_all["Name"].dropna().unique().tolist()
    all_p = pit_all["Name"].dropna().unique().tolist()
    opp_cat = {c: [] for c in MC_ALL_CATS}
    for i in range(n_teams):
        hs = tuple(np.random.choice(all_h, size=min(9, len(all_h)), replace=False))
        ps = tuple(np.random.choice(all_p, size=min(7, len(all_p)), replace=False))
        odf, _ = mc_run_simulation(hs, ps, n_sim, 0.15, 0.3, True, run_count=run_count + i)
        for c in MC_ALL_CATS:
            if c in odf.columns: opp_cat[c].append(odf[c].values)
    return {c: np.array(v) for c, v in opp_cat.items() if v}


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
    "🎲 Monte Carlo Sim",
])
st.sidebar.markdown("---")
using_demo = not any(f.startswith("batting_") for f in os.listdir(CACHE_DIR)) \
             if os.path.exists(CACHE_DIR) else True
if using_demo:
    st.sidebar.warning("⚠️ Demo data active.\nRun `python data_loader.py` for real stats.")
else:
    st.sidebar.success(f"✅ Live data through {LATEST}")
st.sidebar.caption(f"Seasons: {', '.join(map(str, ALL_YEARS))}")
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
    teams  = ["All"] + sorted(df["Team"].dropna().unique().tolist())
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
                "wRC+","xwOBA","Barrel%","xBA","z_HR","z_R","z_RBI","z_SB","z_AVG",
                "breakout_score","regression_score","regression_risk"]
    else:
        show = ["Name","Team","profile_tag","composite","W","ERA","WHIP","SO",
                "xFIP","SIERA","K%","SwStr%","LOB%","z_W","z_ERA","z_WHIP","z_K",
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
    m1.metric("Players",       len(df))
    m2.metric("High Risk",     int((df["regression_risk"]=="High").sum()))
    m3.metric("Breakouts",     int((df["breakout_score"] >= 44).sum()))
    m4.metric("Avg composite", f"{df['composite'].mean():.2f}")
    m5.metric("Top player",    df.iloc[0]["Name"] if len(df) else "—")


# ═════════════════════════════════════════════════════════════
#  PAGE 2 — PLAYER DEEP DIVE
# ═════════════════════════════════════════════════════════════

elif page == "🔍 Player Deep Dive":
    st.title("🔍 Player Deep Dive")
    st.caption("Full historical snapshot, trend charts, radar chart, and analysis for any player.")
    ptype  = st.radio("", ["Hitter","Pitcher"], horizontal=True)
    all_df = bat_all if ptype == "Hitter" else pit_all
    rec_df = bat_rec if ptype == "Hitter" else pit_rec
    name   = st.selectbox("Select player", sorted(all_df["Name"].dropna().unique().tolist()))
    hist   = all_df[all_df["Name"] == name].sort_values("Season")
    rec    = rec_df[rec_df["Name"] == name]
    if hist.empty:
        st.warning("No data found."); st.stop()
    team = hist.iloc[-1].get("Team","—"); age = hist.iloc[-1].get("Age","—")
    st.markdown(f"## {name}  `{team}`  Age {age}")
    if not rec.empty:
        tag    = rec.iloc[0].get("profile_tag","✅ Stable")
        bscore = rec.iloc[0].get("breakout_score", 0)
        rscore = rec.iloc[0].get("regression_score", 0)
        summary= rec.iloc[0].get("analysis_summary","")
        tc1, tc2, tc3 = st.columns(3)
        tc1.markdown(f"**Profile:** {tag}")
        tc2.metric("Breakout Score",   f"{bscore}/100")
        tc3.metric("Regression Score", f"{rscore}/100")
        if summary:
            with st.expander("📋 Full Analysis", expanded=True):
                for line in summary.split("\n"):
                    if line.startswith("📝 **Scouting Summary:**"):
                        st.markdown("<p style='font-size:13px;font-weight:bold;margin-bottom:4px'>📝 Scouting Summary</p>", unsafe_allow_html=True)
                    elif line == "---":
                        st.markdown("<hr style='margin:8px 0;border-color:#333'>", unsafe_allow_html=True)
                    elif line and not line.startswith("  •") and not line.startswith("🟢") and not line.startswith("🔴"):
                        st.markdown(f"<p style='font-size:13px;color:#ccc;line-height:1.6;margin:0'>{line}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(line)
    st.markdown("---")
    if ptype == "Hitter":
        key = ["HR","R","RBI","SB","AVG","wRC+","xwOBA","xBA","Barrel%","BB%","K%","EV"]
    else:
        key = ["W","ERA","WHIP","SO","K%","xFIP","SIERA","SwStr%","BB%","LOB%","GB%","CSW%"]
    key = [k for k in key if k in hist.columns]
    latest_row = hist.iloc[-1]; prev_row = hist.iloc[-2] if len(hist) > 1 else None
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
            if pd.notna(pv) and pd.notna(val): delta = round(float(val) - float(pv), 3)
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
    st.markdown("### 📈 Historical Trends")

    def make_chart(hist, cols_list, dual_axis_col=None, expanded=False, label=""):
        avail = [c for c in cols_list if c in hist.columns]
        if not avail: return
        with st.expander(label, expanded=expanded):
            if dual_axis_col and dual_axis_col in avail:
                primary = [c for c in avail if c != dual_axis_col]
                fig = go.Figure()
                colors = px.colors.qualitative.Plotly
                for ci, col in enumerate(primary):
                    fig.add_trace(go.Scatter(x=hist["Season"], y=hist[col], mode="lines+markers",
                        name=col, line=dict(color=colors[ci % len(colors)]), yaxis="y1"))
                fig.add_trace(go.Scatter(x=hist["Season"], y=hist[dual_axis_col], mode="lines+markers",
                    name=dual_axis_col, line=dict(color=colors[len(primary) % len(colors)], dash="dot", width=2), yaxis="y2"))
                fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10,r=10,t=10,b=10),
                    legend=dict(orientation="h", y=1.15), xaxis=dict(tickvals=ALL_YEARS, tickmode="array"),
                    yaxis=dict(title=", ".join(primary), side="left"),
                    yaxis2=dict(title=dual_axis_col, side="right", overlaying="y", showgrid=False))
            else:
                melt = hist[["Season"] + avail].melt("Season", var_name="Metric", value_name="Value")
                fig  = px.line(melt, x="Season", y="Value", color="Metric", markers=True,
                               template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Plotly)
                fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), legend=dict(orientation="h", y=1.15))
                fig.update_xaxes(tickvals=ALL_YEARS, tickmode="array")
            st.plotly_chart(fig, use_container_width=True)

    if ptype == "Hitter":
        make_chart(hist, ["HR","R","RBI","SB"],            expanded=True,  label="Counting Stats")
        make_chart(hist, ["Barrel%","Hard%","EV","maxEV"], expanded=False, label="Quality of Contact")
        make_chart(hist, ["wOBA","xwOBA","xBA","wRC+"],    expanded=True,  dual_axis_col="wRC+",
                   label="True Talent (wOBA / xwOBA / xBA  |  wRC+ →)")
        make_chart(hist, ["BB%","K%","SwStr%"],            expanded=False, label="Plate Discipline")
        make_chart(hist, ["GB%","FB%","Pull%","LA"],       expanded=False, dual_axis_col="LA",
                   label="Batted Ball Profile (GB% / FB% / Pull%  |  Launch Angle →)")
    else:
        make_chart(hist, ["ERA","WHIP","K/9"],             expanded=True,  dual_axis_col="K/9",
                   label="Results (ERA / WHIP  |  K/9 →)")
        make_chart(hist, ["xFIP","SIERA","FIP"],           expanded=True,  label="True Talent (xFIP / SIERA / FIP)")
        make_chart(hist, ["K%","SwStr%","BB%","CSW%"],     expanded=False, label="Stuff & Command")
        make_chart(hist, ["BABIP","LOB%","HR/FB"],         expanded=False, label="Luck Indicators")
        make_chart(hist, ["GB%","FB%","Hard%","Barrel%"],  expanded=False, label="Batted Ball")

    if not rec.empty:
        st.markdown("---")
        st.markdown(f"### 🕸️ Category Value Radar ({LATEST})")
        if ptype == "Hitter":
            zcats, labels = ["z_HR","z_R","z_RBI","z_SB","z_AVG"], ["HR","R","RBI","SB","AVG"]
        else:
            zcats, labels = ["z_W","z_ERA","z_WHIP","z_K"], ["W","ERA","WHIP","K"]
        vals = [max(-3, min(3, float(rec.iloc[0].get(c,0)))) for c in zcats]
        fig_r = go.Figure(go.Scatterpolar(r=vals+[vals[0]], theta=labels+[labels[0]],
            fill="toself", line_color="#4fc3f7", fillcolor="rgba(79,195,247,0.18)"))
        fig_r.update_layout(polar=dict(radialaxis=dict(range=[-3,3], tickfont_size=9)),
            template="plotly_dark", height=360, margin=dict(l=40,r=40,t=40,b=40))
        st.plotly_chart(fig_r, use_container_width=True)

    st.markdown("---")
    note_input = st.text_input("Add a note (optional)", key="dive_note")
    if st.button(f"🎯 Add {name} to Target List"):
        entry = {"name": name, "type": ptype,
                 "tag":  rec.iloc[0].get("profile_tag","—") if not rec.empty else "—",
                 "composite": float(rec.iloc[0].get("composite",0)) if not rec.empty else 0,
                 "note": note_input}
        if not any(t["name"] == name for t in st.session_state.targets):
            st.session_state.targets.append(entry); st.success(f"✅ {name} added to your target list!")
        else:
            st.info(f"{name} is already in your target list.")
    st.markdown("---")
    st.markdown("### 📄 Full Historical Stats")
    drop = [c for c in ["playerid","regression_risk","regression_score","breakout_score",
                         "profile_tag","analysis_summary","rank","composite"] if c in hist.columns]
    st.dataframe(hist.drop(columns=drop).set_index("Season"), use_container_width=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 3 — REGRESSION & BREAKOUT
# ═════════════════════════════════════════════════════════════

elif page == "🧠 Regression & Breakout":
    st.title("🧠 Regression & Breakout Analysis")
    st.caption("Deep dives into who is due for a correction and who is poised to take off.")
    ptype = st.radio("", ["Hitters","Pitchers"], horizontal=True)
    df = bat_rec.copy() if ptype == "Hitters" else pit_rec.copy()
    tab_break, tab_reg, tab_mixed = st.tabs(["🚀 Breakout Candidates","📉 Regression Risks","⚖️ Mixed / Undervalued"])

    with tab_break:
        st.markdown("### 🚀 Breakout Candidates")
        breakouts = df[df["breakout_score"] >= 33].sort_values("breakout_score", ascending=False)
        if breakouts.empty:
            st.info("No breakout candidates found.")
        else:
            for _, row in breakouts.head(15).iterrows():
                with st.expander(f"**{row['Name']}** ({row.get('Team','—')})  —  Breakout Score: {int(row['breakout_score'])}/100  |  {row['profile_tag']}"):
                    lines = [l for l in row.get("analysis_summary","").split("\n") if "🟢" in l or ("•" in l and "🔴" not in l)]
                    for line in lines: st.markdown(line)
                    key_s = (["composite","HR","AVG","xwOBA","xBA","Barrel%","wRC+","BABIP","Spd"]
                             if ptype == "Hitters" else
                             ["composite","ERA","xFIP","SIERA","K%","SwStr%","LOB%","GB%","BABIP"])
                    key_s = [s for s in key_s if s in row.index]
                    sc = st.columns(len(key_s))
                    for i, s in enumerate(key_s):
                        v = row.get(s, np.nan)
                        if pd.notna(v):
                            sc[i].metric(s, f"{v:.3f}" if isinstance(v,float) and v < 10 else str(round(v,1) if isinstance(v,float) else int(v)))
                    if st.button("🎯 Add to Target List", key=f"add_break_{row['Name']}"):
                        entry = {"name": row["Name"], "type": ptype.rstrip("s"),
                                 "tag": row["profile_tag"], "composite": float(row["composite"]), "note": "Breakout candidate"}
                        if not any(t["name"] == row["Name"] for t in st.session_state.targets):
                            st.session_state.targets.append(entry); st.success(f"Added {row['Name']}!")

    with tab_reg:
        st.markdown("### 📉 Regression Risks")
        risks = df[df["regression_score"] >= 33].sort_values("regression_score", ascending=False)
        if risks.empty:
            st.info("No major regression risks found.")
        else:
            for _, row in risks.head(15).iterrows():
                with st.expander(f"**{row['Name']}** ({row.get('Team','—')})  —  Regression Score: {int(row['regression_score'])}/100  |  {row['profile_tag']}"):
                    lines = [l for l in row.get("analysis_summary","").split("\n") if "🔴" in l or ("•" in l and "🟢" not in l)]
                    for line in lines: st.markdown(line)
                    key_s = (["composite","HR","AVG","xwOBA","xBA","Barrel%","BABIP"]
                             if ptype == "Hitters" else
                             ["composite","ERA","xFIP","SIERA","LOB%","BABIP","HR/FB"])
                    key_s = [s for s in key_s if s in row.index]
                    sc = st.columns(len(key_s))
                    for i, s in enumerate(key_s):
                        v = row.get(s, np.nan)
                        if pd.notna(v):
                            sc[i].metric(s, f"{v:.3f}" if isinstance(v,float) and v < 10 else str(round(v,1) if isinstance(v,float) else int(v)))

    with tab_mixed:
        st.markdown("### ⚖️ Mixed Signals & Undervalued")
        df["value_gap"] = df["breakout_score"] - df["composite"] * 10
        mixed = df[(df["profile_tag"].str.contains("Mixed|Undervalued|Trending Up", na=False)) | (df["value_gap"] > 20)].sort_values("value_gap", ascending=False)
        if mixed.empty:
            st.info("No mixed/undervalued players found.")
        else:
            for _, row in mixed.head(12).iterrows():
                with st.expander(f"**{row['Name']}** — {row['profile_tag']}  |  Breakout: {int(row['breakout_score'])}  Regression: {int(row['regression_score'])}"):
                    st.markdown(row.get("analysis_summary",""))
                    if st.button("🎯 Add to Target List", key=f"add_mixed_{row['Name']}"):
                        entry = {"name": row["Name"], "type": ptype.rstrip("s"),
                                 "tag": row["profile_tag"], "composite": float(row["composite"]), "note": "Undervalued / mixed signals"}
                        if not any(t["name"] == row["Name"] for t in st.session_state.targets):
                            st.session_state.targets.append(entry); st.success(f"Added {row['Name']}!")

    st.markdown("---")
    st.markdown("### 📉📈 Breakout vs Composite Score Scatter")
    fig_sc = px.scatter(df, x="composite", y="breakout_score", hover_name="Name", color="regression_risk",
        color_discrete_map={"High":"#FF4B4B","Medium":"#FFA500","Low":"#21C354"},
        size="breakout_score", size_max=20, template="plotly_dark",
        labels={"composite":"Composite Draft Value","breakout_score":"Breakout Score"},
        title="Top-right = high value + high upside  |  Bottom-left = low value + no upside")
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
        "HR":(bat_rec,"HR"),"R":(bat_rec,"R"),"RBI":(bat_rec,"RBI"),"SB":(bat_rec,"SB"),"AVG":(bat_rec,"AVG"),
        "W":(pit_rec,"W"),"ERA":(pit_rec,"ERA"),"WHIP":(pit_rec,"WHIP"),"K":(pit_rec,"SO"),
    }
    rows = []
    for cat, (src, col) in cat_sources.items():
        if col not in src.columns: continue
        s = src[col].dropna(); lower = cat in ["ERA","WHIP"]
        rows.append({"Category":cat, "Type":"Pitching" if cat in ["W","ERA","WHIP","K"] else "Hitting",
            "Median":round(s.quantile(0.50),3), "Good (P75)":round(s.quantile(0.75),3),
            "Elite":round(s.quantile(0.10) if lower else s.quantile(0.90),3), "Std Dev":round(s.std(),3)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.markdown("---")
    cat_choice = st.selectbox("Explore category distribution", list(cat_sources.keys()))
    src, col   = cat_sources[cat_choice]; series = src[col].dropna(); lower = cat_choice in ["ERA","WHIP"]
    p50 = series.quantile(0.50); p90 = series.quantile(0.10) if lower else series.quantile(0.90)
    fig = px.histogram(x=series, nbins=35, template="plotly_dark", labels={"x":cat_choice,"y":"Players"},
        title=f"{cat_choice} Distribution — {LATEST}", color_discrete_sequence=["#4fc3f7"])
    fig.add_vline(x=p50, line_dash="dash", line_color="yellow", annotation_text="Median")
    fig.add_vline(x=p90, line_dash="dash", line_color="#FF4B4B", annotation_text="Elite")
    fig.update_layout(height=360); st.plotly_chart(fig, use_container_width=True)
    top10 = src.nsmallest(10,col) if lower else src.nlargest(10,col)
    show_c = [c for c in ["Name","Team",col,"composite","breakout_score","regression_risk"] if c in top10.columns]
    st.markdown(f"**Top 10 — {cat_choice}**")
    st.dataframe(top10[show_c].reset_index(drop=True), use_container_width=True)
    st.markdown("---"); st.markdown("### 💡 Strategy Tips")
    for cat, tip in {"SB":"Scarcest category. Target in rounds 3–6. Look for Spd > 6 AND OBP > .330.",
        "HR":"Deep but differentiated. Barrel% > 10% is the truest predictor. Wait on power.",
        "AVG":"Trust xBA and xwOBA over surface AVG. High BABIP + low Hard% = avoid.",
        "ERA":"Find ERA > xFIP = undervalued. ERA < xFIP by 0.75+ = regression incoming.",
        "WHIP":"LOB% > 80% is unsustainable. K-BB% > 15% is the best WHIP floor indicator.",
        "K":"SwStr% > 12% is elite. CSW% > 30% shows pitch quality beyond raw whiffs.",
        "W":"Luckiest category. Target high IP + run support + K/BB > 3.5.",
        "R":"Correlates with lineup spot + OBP. Find leadoff/2-hole hitters.",
        "RBI":"wOBA + HR pace > raw RBI. Lineup protection matters."}.items():
        with st.expander(f"**{cat}**"): st.write(tip)


# ═════════════════════════════════════════════════════════════
#  PAGE 5 — STRATEGY & TARGET LIST
# ═════════════════════════════════════════════════════════════

elif page == "🎯 Strategy & Target List":
    st.title("🎯 Strategy & Target List")
    tab_strat, tab_targets, tab_compare = st.tabs(["🗺️ Draft Strategy Planner","⭐ My Target List","📊 Compare Targets"])

    with tab_strat:
        st.markdown("### 🗺️ Draft Strategy Planner")
        league_size = st.slider("League size (teams)", 8, 16, 12)
        your_pick   = st.slider("Your draft position", 1, league_size, 6)
        rs = st.columns(2)
        h_slots = rs[0].number_input("Hitter roster spots", 1, 15, 9)
        p_slots = rs[1].number_input("Pitcher roster spots", 1, 15, 7)
        st.markdown("---")
        st.multiselect("Your category priorities (select in order of importance)",
            ["HR","R","RBI","SB","AVG","W","ERA","WHIP","K"],
            default=["SB","HR","K","ERA","WHIP","R","RBI","AVG","W"])
        st.markdown("---"); st.markdown("#### 📋 Round-by-Round Guidance")
        total_rounds = h_slots + p_slots
        pick_numbers = [(rd-1)*league_size+your_pick if rd%2==1 else rd*league_size-your_pick+1
                        for rd in range(1, total_rounds+1)]
        round_advice = {
            1:("Superstar anchor","Elite 1st-rounders: 60+ HR pace, .300+ AVG, or ace SP. Don't reach."),
            2:("Top-10 talent","Best player available. If you didn't get SB in R1, address it now."),
            3:("SB or SP ace","SB dries up fast. If no speed yet, round 3 is your last cheap window."),
            4:("SP or power bat","Start your SP core. Target xFIP < 3.20 starters over name-brand ERA."),
            5:("Upside SP","Second SP or breakout hitter. Breakout Score > 44 is your filter."),
            6:("Category fill","Identify your weakest projected category and target specifically."),
            7:("Closer or depth","Saves/Holds if your league counts them. Otherwise best available."),
            8:("Depth + upside","Players with Breakout Score > 33 and low composite — buy low."),
            9:("Bench depth","Multi-position eligibility is gold in Yahoo. Prioritize SP/SS/2B."),
            10:("Lottery tickets","Young players with elite underlying metrics but low ADP — Barrel% > 12%."),
        }
        for rd in range(1, min(total_rounds+1, 11)):
            pick_no = pick_numbers[rd-1] if rd-1 < len(pick_numbers) else "—"
            label, advice = round_advice.get(rd, (f"Round {rd}", "Best player available."))
            with st.expander(f"**Round {rd}** — Pick ~{pick_no}  |  {label}"):
                st.write(advice)
                if rd <= 5:
                    lo, hi = (rd-1)*league_size, rd*league_size
                    sug_h = bat_rec[(bat_rec["rank"]>=lo)&(bat_rec["rank"]<=hi)].head(4)
                    sug_p = pit_rec[(pit_rec["rank"]>=lo)&(pit_rec["rank"]<=hi)].head(3)
                    if not sug_h.empty:
                        st.markdown("**Hitter targets:**")
                        h_c = [c for c in ["Name","Team","composite","HR","AVG","xwOBA","breakout_score","profile_tag"] if c in sug_h.columns]
                        st.dataframe(sug_h[h_c], use_container_width=True, hide_index=True)
                    if not sug_p.empty:
                        st.markdown("**Pitcher targets:**")
                        p_c = [c for c in ["Name","Team","composite","ERA","xFIP","K%","breakout_score","profile_tag"] if c in sug_p.columns]
                        st.dataframe(sug_p[p_c], use_container_width=True, hide_index=True)
        st.markdown("---"); st.markdown("#### 🔍 Category Gap Finder")
        if st.session_state.targets:
            my_h_df = bat_rec[bat_rec["Name"].isin([t["name"] for t in st.session_state.targets if t["type"]=="Hitter"])]
            my_p_df = pit_rec[pit_rec["Name"].isin([t["name"] for t in st.session_state.targets if t["type"]=="Pitcher"])]
            gap_rows = []
            for cat, (src, col) in {"HR":(bat_rec,"z_HR"),"R":(bat_rec,"z_R"),"RBI":(bat_rec,"z_RBI"),
                "SB":(bat_rec,"z_SB"),"AVG":(bat_rec,"z_AVG"),"W":(pit_rec,"z_W"),
                "ERA":(pit_rec,"z_ERA"),"WHIP":(pit_rec,"z_WHIP"),"K":(pit_rec,"z_K")}.items():
                chunk = my_h_df if cat in ["HR","R","RBI","SB","AVG"] else my_p_df
                if col in chunk.columns and len(chunk)>0:
                    avg_z = chunk[col].mean()
                    gap_rows.append({"Category":cat,"Your Avg Z":round(avg_z,2),
                        "Status":"✅ Strong" if avg_z>0.5 else "⚠️ Weak" if avg_z<-0.2 else "➡️ Average"})
            if gap_rows: st.dataframe(pd.DataFrame(gap_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Add players to your target list to see category gaps.")

    with tab_targets:
        st.markdown("### ⭐ My Target List")
        with st.expander("➕ Add a player manually"):
            col_a, col_b, col_c = st.columns(3)
            add_type = col_a.radio("Type", ["Hitter","Pitcher"], horizontal=True, key="manual_type")
            all_names_manual = sorted((bat_rec if add_type=="Hitter" else pit_rec)["Name"].dropna().unique().tolist())
            add_name = col_b.selectbox("Player", all_names_manual, key="manual_name")
            add_note = col_c.text_input("Note", placeholder="e.g. 'Value in round 8'", key="manual_note")
            if st.button("Add to Target List", key="manual_add"):
                rec_src = bat_rec if add_type=="Hitter" else pit_rec
                rec_row = rec_src[rec_src["Name"]==add_name]
                entry = {"name":add_name,"type":add_type,
                    "tag":rec_row.iloc[0].get("profile_tag","—") if not rec_row.empty else "—",
                    "composite":float(rec_row.iloc[0].get("composite",0)) if not rec_row.empty else 0,
                    "note":add_note}
                if not any(t["name"]==add_name for t in st.session_state.targets):
                    st.session_state.targets.append(entry); st.success(f"✅ Added {add_name}!"); st.rerun()
                else:
                    st.info(f"{add_name} already in list.")
        st.markdown("---")
        if not st.session_state.targets:
            st.info("Your target list is empty. Add players from the Draft Board, Deep Dive, or Regression pages.")
        else:
            sort_opt = st.selectbox("Sort targets by", ["composite","name","type"], key="target_sort")
            sorted_targets = sorted(st.session_state.targets, key=lambda x:(
                -x["composite"] if sort_opt=="composite" else x["name"] if sort_opt=="name" else x["type"]))
            to_remove = []
            for i, t in enumerate(sorted_targets):
                rec_src = bat_rec if t["type"]=="Hitter" else pit_rec
                rec_row = rec_src[rec_src["Name"]==t["name"]]
                st.markdown(f"""<div class='target-card'><b>{t['name']}</b> &nbsp;
                    <span style='color:#aaa'>{t['type']}</span> &nbsp;|&nbsp; {t['tag']}
                    &nbsp;|&nbsp; Composite: <b>{t['composite']:.2f}</b>
                    {"&nbsp;|&nbsp; 📝 " + t['note'] if t['note'] else ""}
                    </div>""", unsafe_allow_html=True)
                if not rec_row.empty:
                    r = rec_row.iloc[0]
                    mini = ([c for c in ["HR","AVG","xwOBA","Barrel%","SB","wRC+","breakout_score"] if c in r.index]
                            if t["type"]=="Hitter" else
                            [c for c in ["ERA","xFIP","K%","SwStr%","WHIP","breakout_score"] if c in r.index])
                    mcols = st.columns(len(mini))
                    for ci, s in enumerate(mini):
                        v = r.get(s, np.nan)
                        if pd.notna(v):
                            mcols[ci].metric(s, f"{float(v):.3f}" if isinstance(v,float) and v<10 else str(int(round(float(v)))))
                if st.button("🗑️ Remove", key=f"rem_{i}_{t['name']}"): to_remove.append(t["name"])
            for nm in to_remove: st.session_state.targets = [t for t in st.session_state.targets if t["name"]!=nm]
            if to_remove: st.rerun()
            st.markdown("---")
            if st.button("🗑️ Clear Entire Target List"): st.session_state.targets = []; st.rerun()

    with tab_compare:
        st.markdown("### 📊 Compare Your Targets")
        if len(st.session_state.targets) < 2:
            st.info("Add at least 2 players to your target list to compare them.")
        else:
            h_targets = [t for t in st.session_state.targets if t["type"]=="Hitter"]
            p_targets = [t for t in st.session_state.targets if t["type"]=="Pitcher"]
            if h_targets:
                st.markdown("#### Hitter Comparison")
                h_df = bat_rec[bat_rec["Name"].isin([t["name"] for t in h_targets])]
                cc = [c for c in ["Name","Team","composite","HR","R","RBI","SB","AVG","wRC+","xwOBA","xBA","Barrel%","SwStr%","breakout_score","regression_score","profile_tag"] if c in h_df.columns]
                st.dataframe(h_df[cc].sort_values("composite",ascending=False).style.background_gradient(subset=["composite"],cmap="RdYlGn"), use_container_width=True, hide_index=True)
                z_h = [c for c in ["z_HR","z_R","z_RBI","z_SB","z_AVG"] if c in h_df.columns]
                if z_h:
                    fig_comp = go.Figure(); labels = [c.replace("z_","") for c in z_h]; colors = px.colors.qualitative.Plotly
                    for ci, (_, row) in enumerate(h_df.iterrows()):
                        vals = [max(-3,min(3,float(row.get(c,0)))) for c in z_h]
                        fig_comp.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=labels+[labels[0]], fill="toself", name=row["Name"], line_color=colors[ci%len(colors)]))
                    fig_comp.update_layout(polar=dict(radialaxis=dict(range=[-3,3])), template="plotly_dark", height=400, legend=dict(orientation="h",y=-0.1))
                    st.plotly_chart(fig_comp, use_container_width=True)
            if p_targets:
                st.markdown("#### Pitcher Comparison")
                p_df = pit_rec[pit_rec["Name"].isin([t["name"] for t in p_targets])]
                cc = [c for c in ["Name","Team","composite","W","ERA","WHIP","SO","xFIP","SIERA","K%","SwStr%","LOB%","breakout_score","regression_score","profile_tag"] if c in p_df.columns]
                st.dataframe(p_df[cc].sort_values("composite",ascending=False).style.background_gradient(subset=["composite"],cmap="RdYlGn"), use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════
#  PAGE 6 — WEIGHT DASHBOARD
# ═════════════════════════════════════════════════════════════

elif page == "⚙️ Weight Dashboard":
    st.title("⚙️ Composite Score Weight Dashboard")
    st.caption("Manually tune how each stat contributes to the composite draft value score. Scores recalculate instantly.")
    st.info("💡 **How it works:** Each category is scored using a weighted blend of underlying stats. Adjust sliders to reflect your league's priorities.")
    tab_hw, tab_pw, tab_preview = st.tabs(["⚾ Hitter Weights","🎯 Pitcher Weights","👁️ Live Preview"])

    default_hitter_weights = {
        "HR":  {"HR":1.0,"Barrel%":0.7,"Hard%":0.4},
        "R":   {"R":1.0,"OBP":0.5,"wRC+":0.4},
        "RBI": {"RBI":1.0,"wOBA":0.5,"Hard%":0.3},
        "SB":  {"SB":1.0,"Spd":0.7},
        "AVG": {"AVG":1.0,"xwOBA":0.6,"BABIP":-0.25},
    }
    default_pitcher_weights = {
        "W":    {"W":1.0},
        "ERA":  {"ERA":0.6,"xFIP":0.6,"SIERA":0.5},
        "WHIP": {"WHIP":0.8,"BB%":0.5},
        "K":    {"SO":1.0,"K%":0.8,"SwStr%":0.5},
    }
    default_cat_weights_h = {"HR":1.0,"R":1.0,"RBI":1.0,"SB":1.0,"AVG":1.0}
    default_cat_weights_p = {"W":1.0,"ERA":1.0,"WHIP":1.0,"K":1.0}

    if "hw"  not in st.session_state: st.session_state.hw  = {cat:dict(s) for cat,s in default_hitter_weights.items()}
    if "pw"  not in st.session_state: st.session_state.pw  = {cat:dict(s) for cat,s in default_pitcher_weights.items()}
    if "cwh" not in st.session_state: st.session_state.cwh = dict(default_cat_weights_h)
    if "cwp" not in st.session_state: st.session_state.cwp = dict(default_cat_weights_p)

    def custom_score_hitters(df, sw, cw):
        df = df.copy()
        for cat, metrics in sw.items():
            tot = sum(abs(w) for w in metrics.values())
            ws  = pd.Series(0.0, index=df.index)
            for col, w in metrics.items():
                if col in df.columns: ws += _z(df[col].fillna(df[col].median())) * w
            df[f"z_{cat}"] = (ws/tot if tot else ws).round(2)
        composite = pd.Series(0.0, index=df.index)
        tot_cat = sum(abs(v) for v in cw.values())
        for cat, cval in cw.items():
            zc = f"z_{cat}"
            if zc in df.columns and tot_cat: composite += df[zc] * cval / tot_cat
        df["composite"] = composite.round(2); df["rank"] = df["composite"].rank(ascending=False).astype(int)
        return df

    def custom_score_pitchers(df, sw, cw):
        df = df.copy(); lb = {"ERA","WHIP"}
        for cat, metrics in sw.items():
            tot = sum(abs(w) for w in metrics.values())
            ws  = pd.Series(0.0, index=df.index)
            for col, w in metrics.items():
                if col in df.columns:
                    z = _z(df[col].fillna(df[col].median()))
                    ws += (-z if cat in lb else z) * w
            df[f"z_{cat}"] = (ws/tot if tot else ws).round(2)
        composite = pd.Series(0.0, index=df.index)
        tot_cat = sum(abs(v) for v in cw.values())
        for cat, cval in cw.items():
            zc = f"z_{cat}"
            if zc in df.columns and tot_cat: composite += df[zc] * cval / tot_cat
        df["composite"] = composite.round(2); df["rank"] = df["composite"].rank(ascending=False).astype(int)
        return df

    with tab_hw:
        st.markdown("### ⚾ Hitter Stat Weights")
        st.markdown("#### Category Importance")
        cw_cols = st.columns(5)
        for i, cat in enumerate(["HR","R","RBI","SB","AVG"]):
            st.session_state.cwh[cat] = cw_cols[i].slider(f"{cat} importance",0.0,3.0,float(st.session_state.cwh[cat]),0.25,key=f"cwh_{cat}")
        st.markdown("---"); st.markdown("#### Stat-Level Weights")
        stat_info = {
            "HR":{"HR":"Raw HR count","Barrel%":"Barrel rate (best HR predictor)","Hard%":"Hard contact rate"},
            "R":{"R":"Raw R count","OBP":"On-base percentage","wRC+":"Weighted runs created+"},
            "RBI":{"RBI":"Raw RBI count","wOBA":"Weighted on-base average","Hard%":"Hard contact rate"},
            "SB":{"SB":"Raw SB count","Spd":"Speed score"},
            "AVG":{"AVG":"Batting average","xwOBA":"Expected wOBA","BABIP":"BABIP (negative = luck correction)"},
        }
        for cat, stats in default_hitter_weights.items():
            with st.expander(f"**{cat}** category weights", expanded=True):
                nw = {}; wcols = st.columns(len(stats))
                for i,(stat,dv) in enumerate(stats.items()):
                    nw[stat] = wcols[i].slider(stat,-1.0,2.0,float(st.session_state.hw[cat].get(stat,dv)),0.05,
                        key=f"hw_{cat}_{stat}", help=stat_info.get(cat,{}).get(stat,stat))
                st.session_state.hw[cat] = nw
        if st.columns(2)[0].button("🔄 Reset Hitter Weights to Default"):
            st.session_state.hw = {cat:dict(s) for cat,s in default_hitter_weights.items()}
            st.session_state.cwh = dict(default_cat_weights_h); st.rerun()

    with tab_pw:
        st.markdown("### 🎯 Pitcher Stat Weights")
        st.markdown("#### Category Importance")
        cw_cols_p = st.columns(4)
        for i, cat in enumerate(["W","ERA","WHIP","K"]):
            st.session_state.cwp[cat] = cw_cols_p[i].slider(f"{cat} importance",0.0,3.0,float(st.session_state.cwp[cat]),0.25,key=f"cwp_{cat}")
        st.markdown("---"); st.markdown("#### Stat-Level Weights")
        stat_info_p = {
            "W":{"W":"Raw win count"},
            "ERA":{"ERA":"ERA (lower=better)","xFIP":"xFIP (lower=better)","SIERA":"SIERA (lower=better)"},
            "WHIP":{"WHIP":"WHIP (lower=better)","BB%":"Walk rate (lower=better)"},
            "K":{"SO":"Raw strikeout count","K%":"Strikeout rate","SwStr%":"Swinging strike rate"},
        }
        for cat, stats in default_pitcher_weights.items():
            with st.expander(f"**{cat}** category weights", expanded=True):
                nw = {}; wcols = st.columns(len(stats))
                for i,(stat,dv) in enumerate(stats.items()):
                    nw[stat] = wcols[i].slider(stat,0.0,2.0,float(st.session_state.pw[cat].get(stat,dv)),0.05,
                        key=f"pw_{cat}_{stat}", help=stat_info_p.get(cat,{}).get(stat,stat))
                st.session_state.pw[cat] = nw
        if st.button("🔄 Reset Pitcher Weights to Default"):
            st.session_state.pw = {cat:dict(s) for cat,s in default_pitcher_weights.items()}
            st.session_state.cwp = dict(default_cat_weights_p); st.rerun()

    with tab_preview:
        st.markdown("### 👁️ Live Rankings Preview")
        preview_type = st.radio("", ["Hitters","Pitchers"], horizontal=True, key="preview_type")

        def style_rc(val):
            try:
                v = int(val)
                if v > 5:  return "color:#21C354; font-weight:bold"
                if v > 0:  return "color:#21C354"
                if v < -5: return "color:#FF4B4B; font-weight:bold"
                if v < 0:  return "color:#FF4B4B"
            except: pass
            return ""

        if preview_type == "Hitters":
            ch = custom_score_hitters(bat_rec.drop(columns=["composite","rank"],errors="ignore"), st.session_state.hw, st.session_state.cwh)
            dr = bat_rec[["Name","composite","rank"]].rename(columns={"composite":"default_composite","rank":"default_rank"})
            ch = ch.merge(dr, on="Name", how="left"); ch["rank_change"] = ch["default_rank"] - ch["rank"]; ch = ch.sort_values("rank")
            sc = [c for c in ["Name","Team","rank","composite","default_rank","default_composite","rank_change","HR","R","RBI","SB","AVG","xwOBA","Barrel%","z_HR","z_R","z_RBI","z_SB","z_AVG"] if c in ch.columns]
            st.dataframe(ch[sc].head(50).style.map(style_rc,subset=["rank_change"]).map(style_z,subset=[c for c in sc if c.startswith("z_")]).background_gradient(subset=["composite"],cmap="RdYlGn").format({"composite":"{:.2f}","default_composite":"{:.2f}","rank_change":"{:+d}"}), use_container_width=True, height=520)
            wdf = pd.DataFrame({"Category":list(st.session_state.cwh.keys()),"Your Weight":list(st.session_state.cwh.values()),"Default":[1.0]*len(st.session_state.cwh)})
            fig_w = px.bar(wdf.melt("Category",var_name="Type",value_name="Weight"),x="Category",y="Weight",color="Type",barmode="group",template="plotly_dark",color_discrete_sequence=["#4fc3f7","#666"],title="Category Importance Weights")
            fig_w.update_layout(height=280); st.plotly_chart(fig_w, use_container_width=True)
        else:
            cp = custom_score_pitchers(pit_rec.drop(columns=["composite","rank"],errors="ignore"), st.session_state.pw, st.session_state.cwp)
            dr = pit_rec[["Name","composite","rank"]].rename(columns={"composite":"default_composite","rank":"default_rank"})
            cp = cp.merge(dr, on="Name", how="left"); cp["rank_change"] = cp["default_rank"] - cp["rank"]; cp = cp.sort_values("rank")
            sc = [c for c in ["Name","Team","rank","composite","default_rank","default_composite","rank_change","W","ERA","WHIP","SO","xFIP","SIERA","K%","z_W","z_ERA","z_WHIP","z_K"] if c in cp.columns]
            st.dataframe(cp[sc].head(50).style.map(style_rc,subset=["rank_change"]).map(style_z,subset=[c for c in sc if c.startswith("z_")]).background_gradient(subset=["composite"],cmap="RdYlGn").format({"composite":"{:.2f}","default_composite":"{:.2f}","rank_change":"{:+d}"}), use_container_width=True, height=520)
            wdf_p = pd.DataFrame({"Category":list(st.session_state.cwp.keys()),"Your Weight":list(st.session_state.cwp.values()),"Default":[1.0]*len(st.session_state.cwp)})
            fig_wp = px.bar(wdf_p.melt("Category",var_name="Type",value_name="Weight"),x="Category",y="Weight",color="Type",barmode="group",template="plotly_dark",color_discrete_sequence=["#4fc3f7","#666"],title="Category Importance Weights")
            fig_wp.update_layout(height=280); st.plotly_chart(fig_wp, use_container_width=True)

        st.markdown("---"); st.markdown("#### 💡 Weight Tuning Tips")
        for tip, desc in {"SB-heavy league":"Raise SB importance to 2.0–3.0 and Spd weight to 1.5.",
            "HR-heavy league":"Raise HR importance to 2.0 and Barrel% weight to 1.5.",
            "Strikeout-focused":"Raise K importance to 2.0–3.0, SwStr% weight to 1.5.",
            "AVG matters a lot":"Raise AVG importance, increase xwOBA weight, reduce BABIP negative weight.",
            "ERA/WHIP ratio league":"Raise ERA and WHIP importance, increase SIERA weight.",
            "Wins don't matter":"Set W importance to 0 to ignore wins entirely."}.items():
            with st.expander(f"**{tip}**"): st.write(desc)


# ═════════════════════════════════════════════════════════════
#  PAGE 7 — DRAFT ROOM
# ═════════════════════════════════════════════════════════════

elif page == "🏟️ Draft Room":
    st.title("🏟️ Live Draft Room")
    st.caption("Mark players as drafted. Your board updates in real time.")
    left, right = st.columns([3, 1])

    with left:
        tab_h, tab_p = st.tabs(["⚾ Hitters","🎯 Pitchers"])
        with tab_h:
            avail_h = bat_rec[~bat_rec["Name"].isin(st.session_state.drafted_h)].sort_values("composite",ascending=False).reset_index(drop=True)
            avail_h.index += 1
            show_h = [c for c in ["Name","Team","profile_tag","composite","HR","R","RBI","SB","AVG","wRC+","xwOBA","Barrel%","breakout_score","z_HR","z_SB","regression_risk"] if c in avail_h.columns]
            is_target = avail_h["Name"].isin([t["name"] for t in st.session_state.targets])
            st.markdown(f"**{len(avail_h)} hitters available** &nbsp;|&nbsp; 🎯 {is_target.sum()} on your target list")
            st.dataframe(avail_h[show_h].style.map(style_risk,subset=["regression_risk"]).map(style_z,subset=[c for c in show_h if c.startswith("z_")]).map(style_breakout,subset=["breakout_score"]), use_container_width=True, height=420)
            pick_h = st.selectbox("Select hitter", [""]+avail_h["Name"].tolist(), key="sel_h")
            ca, cb, cc = st.columns(3)
            if ca.button("✅ Add to MY team", key="btn_add_h") and pick_h:
                st.session_state.drafted_h.add(pick_h); st.session_state.my_h.append(pick_h); st.rerun()
            if cb.button("❌ Drafted (not me)", key="btn_skip_h") and pick_h:
                st.session_state.drafted_h.add(pick_h); st.rerun()
            if cc.button("🎯 Add to Targets", key="btn_target_h") and pick_h:
                rr = bat_rec[bat_rec["Name"]==pick_h]
                entry = {"name":pick_h,"type":"Hitter","tag":rr.iloc[0].get("profile_tag","—") if not rr.empty else "—",
                    "composite":float(rr.iloc[0].get("composite",0)) if not rr.empty else 0,"note":"Added from draft room"}
                if not any(t["name"]==pick_h for t in st.session_state.targets):
                    st.session_state.targets.append(entry); st.success(f"🎯 {pick_h} added to targets!")
        with tab_p:
            avail_p = pit_rec[~pit_rec["Name"].isin(st.session_state.drafted_p)].sort_values("composite",ascending=False).reset_index(drop=True)
            avail_p.index += 1
            show_p = [c for c in ["Name","Team","profile_tag","composite","W","ERA","WHIP","SO","xFIP","SIERA","K%","breakout_score","z_ERA","z_K","regression_risk"] if c in avail_p.columns]
            st.markdown(f"**{len(avail_p)} pitchers available**")
            st.dataframe(avail_p[show_p].style.map(style_risk,subset=["regression_risk"]).map(style_z,subset=[c for c in show_p if c.startswith("z_")]).map(style_breakout,subset=["breakout_score"]), use_container_width=True, height=420)
            pick_p = st.selectbox("Select pitcher", [""]+avail_p["Name"].tolist(), key="sel_p")
            cd, ce, cf = st.columns(3)
            if cd.button("✅ Add to MY team", key="btn_add_p") and pick_p:
                st.session_state.drafted_p.add(pick_p); st.session_state.my_p.append(pick_p); st.rerun()
            if ce.button("❌ Drafted (not me)", key="btn_skip_p") and pick_p:
                st.session_state.drafted_p.add(pick_p); st.rerun()
            if cf.button("🎯 Add to Targets", key="btn_target_p") and pick_p:
                rr = pit_rec[pit_rec["Name"]==pick_p]
                entry = {"name":pick_p,"type":"Pitcher","tag":rr.iloc[0].get("profile_tag","—") if not rr.empty else "—",
                    "composite":float(rr.iloc[0].get("composite",0)) if not rr.empty else 0,"note":"Added from draft room"}
                if not any(t["name"]==pick_p for t in st.session_state.targets):
                    st.session_state.targets.append(entry); st.success(f"🎯 {pick_p} added to targets!")

    with right:
        st.markdown("### 🏆 My Team")
        if st.session_state.my_h:
            st.markdown("**Hitters**")
            for name in st.session_state.my_h:
                row = bat_rec[bat_rec["Name"]==name]
                risk = row.iloc[0]["regression_risk"] if not row.empty else "Low"
                tag  = row.iloc[0]["profile_tag"] if not row.empty else ""
                dot  = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(risk,"⚪")
                st.markdown(f"{dot} **{name}** {tag}")
        if st.session_state.my_p:
            st.markdown("**Pitchers**")
            for name in st.session_state.my_p:
                row = pit_rec[pit_rec["Name"]==name]
                risk = row.iloc[0]["regression_risk"] if not row.empty else "Low"
                tag  = row.iloc[0]["profile_tag"] if not row.empty else ""
                dot  = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(risk,"⚪")
                st.markdown(f"{dot} **{name}** {tag}")
        my_h_df = bat_rec[bat_rec["Name"].isin(st.session_state.my_h)]
        my_p_df = pit_rec[pit_rec["Name"].isin(st.session_state.my_p)]
        if not my_h_df.empty or not my_p_df.empty:
            st.markdown("---"); st.markdown("**Category Strength**")
            for dfc in [my_h_df, my_p_df]:
                for zc in [c for c in dfc.columns if c.startswith("z_")]:
                    val   = dfc[zc].mean(); cat = zc.replace("z_","")
                    color = "#21C354" if val>0.5 else "#FFA500" if val>-0.5 else "#FF4B4B"
                    filled = int(min(10, max(0, (val+3)/6*10))); bar = "█"*filled + "░"*(10-filled)
                    st.markdown(f"**{cat}** {val:+.2f} <span style='color:{color}'>{bar}</span>", unsafe_allow_html=True)
        avail_targets = [t for t in st.session_state.targets
                         if t["name"] not in st.session_state.drafted_h and t["name"] not in st.session_state.drafted_p]
        if avail_targets:
            st.markdown("---"); st.markdown(f"**🎯 Targets still available ({len(avail_targets)})**")
            for t in avail_targets: st.caption(f"• {t['name']} ({t['type']})")
        st.markdown("---")
        total_drafted = len(st.session_state.drafted_h) + len(st.session_state.drafted_p)
        st.caption(f"{total_drafted} players drafted total")
        if st.button("🔄 Reset Draft"):
            for k in ["drafted_h","drafted_p","my_h","my_p"]: del st.session_state[k]
            st.rerun()


# ═════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════
#  PAGE 8 — MONTE CARLO SIMULATION
# ═════════════════════════════════════════════════════════════

elif page == "🎲 Monte Carlo Sim":
    st.title("🎲 Monte Carlo Season Simulator")
    st.caption(
        "Simulate thousands of full seasons for your roster. "
        "See probability distributions across all 9 Yahoo categories, "
        "estimate expected category wins vs. a league of opponents, "
        "and stress-test alternative roster builds."
    )

    # All MC constants/functions are defined at module level above (mc_run_simulation, etc.)
    all_h_names_mc = sorted(bat_all["Name"].dropna().unique())
    all_p_names_mc = sorted(pit_all["Name"].dropna().unique())

    # ── Setup controls (always visible above tabs) ─────────────
    st.markdown("### ⚙️ Setup")
    col_a, col_b = st.columns(2)
    n_sim_val       = col_a.select_slider("Number of simulations",
        options=[500, 1_000, 2_500, 5_000, 10_000], value=2_500)
    league_size_mc  = col_b.slider("League size", 8, 16, 12, key="mc_league")

    pre_h = list(st.session_state.get("my_h", []))
    pre_p = list(st.session_state.get("my_p", []))
    mc_hitters  = st.multiselect("My Hitters (up to 14)", options=all_h_names_mc,
        default=[h for h in pre_h if h in all_h_names_mc], max_selections=14, key="mc_hitters")
    mc_pitchers = st.multiselect("My Pitchers (up to 10)", options=all_p_names_mc,
        default=[p for p in pre_p if p in all_p_names_mc], max_selections=10, key="mc_pitchers")

    adv1, adv2, adv3 = st.columns(3)
    injury_pct_val   = adv1.slider("Injury / games-lost risk (%)", 0, 40, 15,
        help="Each sim randomly reduces counting stats for ~30% of sims.")
    regr_pull_val    = adv2.slider("Mean-reversion strength", 0.0, 1.0, 0.3, 0.05,
        help="0 = raw historical mean. 1 = fully regress to league average.")
    platoon_val      = adv3.checkbox("Apply Barrel%/SwStr% quality multiplier", value=True)

    run_clicked = st.button(
        "▶️ Run Monte Carlo Simulation", type="primary",
        disabled=(len(mc_hitters) == 0 and len(mc_pitchers) == 0),
    )

    # Increment run_count on each click so cache key is always unique
    if run_clicked:
        st.session_state["mc_run_count"] = st.session_state.get("mc_run_count", 0) + 1
        st.session_state["mc_params"] = {
            "n_sim": n_sim_val,
            "league_size": league_size_mc,
            "hitters": tuple(mc_hitters),
            "pitchers": tuple(mc_pitchers),
            "injury_pct": injury_pct_val / 100,
            "regression_pull": regr_pull_val,
            "platoon_boost": platoon_val,
            "run_count": st.session_state["mc_run_count"],
        }

    st.markdown("---")

    # ── Results tabs (always rendered; content conditional on params) ──
    tab_results, tab_cat, tab_alt, tab_opp = st.tabs([
        "📈 Season Projections",
        "🏆 Category Win Odds",
        "🔀 Roster Alternatives",
        "👥 vs. Opponent Sims",
    ])

    mc_p = st.session_state.get("mc_params")

    if mc_p is None:
        for t in [tab_results, tab_cat, tab_alt, tab_opp]:
            with t:
                st.info("👆 Select your roster above and click **▶️ Run Monte Carlo Simulation** to begin.")
    else:
        # Run (cached) simulation
        with st.spinner("🎲 Running simulations — this may take a few seconds..."):
            team_sims, player_sims = mc_run_simulation(
                hitters        = mc_p["hitters"],
                pitchers       = mc_p["pitchers"],
                n_sim          = mc_p["n_sim"],
                injury_pct     = mc_p["injury_pct"],
                regression_pull= mc_p["regression_pull"],
                platoon_boost  = mc_p["platoon_boost"],
                run_count      = mc_p.get("run_count", 0),
            )

        # ── Tab 1: Season Projections ──────────────────────────
        with tab_results:
            st.markdown(f"### 📈 Team Season Projections  ({mc_p['n_sim']:,} simulations)")
            st.caption(f"Roster: {', '.join(mc_p['hitters'])} | {', '.join(mc_p['pitchers'])}")
            summary_rows = []
            for cat in MC_ALL_CATS:
                if cat not in team_sims.columns: continue
                vals = team_sims[cat].dropna()
                p10, p25, p50, p75, p90 = np.percentile(vals, [10, 25, 50, 75, 90])
                cv = round(float(vals.std() / abs(vals.mean()) * 100), 1) if vals.mean() != 0 else 0
                summary_rows.append({
                    "Category": cat,
                    "Type": "Lower=Better" if cat in MC_LOWER_BETTER else "Higher=Better",
                    "10th %ile": round(p10, 2), "25th %ile": round(p25, 2),
                    "Median": round(p50, 2),
                    "75th %ile": round(p75, 2), "90th %ile": round(p90, 2),
                    "Std Dev": round(float(vals.std()), 2), "CV%": cv,
                })
            sdf = pd.DataFrame(summary_rows)
            def _color_type(val):
                return "color:#4fc3f7" if val == "Higher=Better" else "color:#FFA500"
            st.dataframe(
                sdf.style
                    .map(_color_type, subset=["Type"])
                    .background_gradient(subset=["Std Dev"], cmap="YlOrRd")
                    .format({"CV%": "{:.1f}%"}),
                use_container_width=True, hide_index=True)
            st.caption("**CV%** = volatility. High CV% = this category is especially unpredictable for your roster.")

            st.markdown("---")
            st.markdown("#### 📊 Category Distribution Plots")
            cat_grid = st.columns(3)
            for i, cat in enumerate(MC_ALL_CATS):
                if cat not in team_sims.columns: continue
                vals = team_sims[cat].values
                p10v, p90v = np.percentile(vals, [10, 90])
                with cat_grid[i % 3]:
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(x=vals, nbinsx=40, marker_color="#4fc3f7", showlegend=False))
                    fig.add_vline(x=float(np.median(vals)), line_dash="dash", line_color="yellow",
                        annotation_text="Median", annotation_position="top right")
                    fig.add_vrect(x0=float(p10v), x1=float(p90v),
                        fillcolor="rgba(79,195,247,0.08)", line_width=0,
                        annotation_text="P10–P90", annotation_position="top left")
                    fig.update_layout(title=cat, template="plotly_dark", height=220,
                        margin=dict(l=8, r=8, t=36, b=8))
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 👤 Per-Player Median Projections")
            player_rows = []
            for name, sdf2 in player_sims.items():
                row = {"Name": name, "Type": "Hitter" if name in mc_p["hitters"] else "Pitcher"}
                for col in sdf2.columns:
                    row[col] = round(float(sdf2[col].median()), 3)
                player_rows.append(row)
            if player_rows:
                pproj = pd.DataFrame(player_rows)
                spc = ["Name", "Type"] + [c for c in MC_H_CATS + MC_P_CATS + ["wRC+","xwOBA","Barrel%","K%","xFIP"] if c in pproj.columns]
                st.dataframe(pproj[spc].sort_values(["Type", "Name"]), use_container_width=True, hide_index=True)

        # ── Tab 2: Category Win Odds ───────────────────────────
        with tab_cat:
            st.markdown("### 🏆 Category Win Probability")
            st.caption("Win% against randomly assembled opponents drawn from the full player pool.")
            with st.spinner("Simulating opponent pool..."):
                opp_pool = mc_opponent_pool(mc_p["league_size"] - 1, min(mc_p["n_sim"], 1000), mc_p.get("run_count", 0))
            win_pct_rows = []
            for cat in MC_ALL_CATS:
                if cat not in team_sims.columns or cat not in opp_pool: continue
                my_v = team_sims[cat].values[:len(opp_pool[cat][0])]
                wins_per_opp = []
                for opp in opp_pool[cat]:
                    n = min(len(my_v), len(opp))
                    wins_per_opp.append(
                        np.mean(my_v[:n] < opp[:n]) if cat in MC_LOWER_BETTER
                        else np.mean(my_v[:n] > opp[:n])
                    )
                awp = float(np.mean(wins_per_opp))
                med_me  = float(np.median(my_v))
                med_opp = float(np.median(np.concatenate(opp_pool[cat])))
                strength = ("💪 Dominant" if awp >= 0.65 else "✅ Solid" if awp >= 0.52 else
                            "⚖️ Toss-up" if awp >= 0.46 else "⚠️ Weak"  if awp >= 0.35 else "🚨 Punt")
                win_pct_rows.append({
                    "Category": cat, "Win%": round(awp * 100, 1),
                    "My Median": round(med_me, 2), "Opp Median": round(med_opp, 2),
                    "Edge": round(med_me - med_opp, 2), "Assessment": strength,
                })
            win_df = pd.DataFrame(win_pct_rows).sort_values("Win%", ascending=False)
            def _color_win(val):
                try:
                    v = float(val)
                    if v >= 65: return "color:#21C354; font-weight:bold"
                    if v >= 52: return "color:#21C354"
                    if v >= 46: return "color:#FFA500"
                    if v >= 35: return "color:#FF4B4B"
                    return "color:#FF4B4B; font-weight:bold"
                except: return ""
            st.dataframe(
                win_df.style.map(_color_win, subset=["Win%"]).format({"Win%": "{:.1f}%"}),
                use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### 🕸️ Category Win% Radar")
            cats_r = win_df["Category"].tolist(); probs_r = win_df["Win%"].tolist()
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=probs_r + [probs_r[0]], theta=cats_r + [cats_r[0]],
                fill="toself", line_color="#4fc3f7",
                fillcolor="rgba(79,195,247,0.15)", name="Win%"))
            fig_radar.add_trace(go.Scatterpolar(
                r=[50] * (len(cats_r) + 1), theta=cats_r + [cats_r[0]],
                mode="lines", line=dict(dash="dash", color="gray", width=1), name="50% line"))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="%", tickfont_size=9)),
                template="plotly_dark", height=420,
                legend=dict(orientation="h", y=-0.1), margin=dict(l=40,r=40,t=40,b=60))
            st.plotly_chart(fig_radar, use_container_width=True)

            exp_wins = sum(r["Win%"] / 100 for _, r in win_df.iterrows())
            st.metric("📊 Expected Category Wins per matchup", f"{exp_wins:.2f} / 9",
                f"{'above' if exp_wins > 4.5 else 'below'} .500")

        # ── Tab 3: Roster Alternatives ─────────────────────────
        with tab_alt:
            st.markdown("### 🔀 Roster Alternative Comparison")
            st.caption("Swap one player and see how category distributions shift.")
            all_current = list(mc_p["hitters"]) + list(mc_p["pitchers"])
            if not all_current:
                st.info("Add players in the Setup section above first.")
            else:
                swap_out   = st.selectbox("Player to replace", all_current, key="swap_out")
                is_h_swap  = swap_out in mc_p["hitters"]
                taken      = set(mc_p["hitters"] if is_h_swap else mc_p["pitchers"])
                pool       = [n for n in (all_h_names_mc if is_h_swap else all_p_names_mc) if n not in taken]
                swap_in    = st.selectbox("Replace with", pool, key="swap_in")

                if st.button("🔄 Compare Rosters", key="btn_compare"):
                    if is_h_swap:
                        alt_h = tuple(h if h != swap_out else swap_in for h in mc_p["hitters"])
                        alt_p = mc_p["pitchers"]
                    else:
                        alt_h = mc_p["hitters"]
                        alt_p = tuple(pp if pp != swap_out else swap_in for pp in mc_p["pitchers"])

                    with st.spinner("Running alternative simulation..."):
                        alt_sims, _ = run_monte_carlo(
                            alt_h, alt_p, mc_p["n_sim"],
                            mc_p["injury_pct"], mc_p["regression_pull"],
                            mc_p["platoon_boost"], seed=77)

                    st.markdown(f"#### Comparing: **{swap_out}** → **{swap_in}**")
                    comp_rows = []
                    for cat in MC_ALL_CATS:
                        if cat not in team_sims.columns or cat not in alt_sims.columns: continue
                        bm = float(np.median(team_sims[cat]))
                        am = float(np.median(alt_sims[cat]))
                        delta = am - bm
                        if cat in MC_LOWER_BETTER:
                            direction = "✅ Better" if delta < -0.01 else "❌ Worse" if delta > 0.01 else "➡️ Similar"
                        else:
                            direction = "✅ Better" if delta >  0.01 else "❌ Worse" if delta < -0.01 else "➡️ Similar"
                        comp_rows.append({
                            "Category": cat,
                            f"Base ({swap_out})": round(bm, 2),
                            f"Alt ({swap_in})":   round(am, 2),
                            "Delta": round(delta, 2),
                            "Impact": direction,
                        })
                    comp_df = pd.DataFrame(comp_rows)
                    def _ci(val):
                        if "Better" in str(val): return "color:#21C354; font-weight:bold"
                        if "Worse"  in str(val): return "color:#FF4B4B; font-weight:bold"
                        return "color:#aaa"
                    st.dataframe(comp_df.style.map(_ci, subset=["Impact"]),
                        use_container_width=True, hide_index=True)

                    imp_cat = comp_df.reindex(
                        comp_df["Delta"].abs().sort_values(ascending=False).index
                    ).iloc[0]["Category"]
                    st.markdown(f"#### Distribution shift — most impacted: **{imp_cat}**")
                    fig_ov = go.Figure()
                    fig_ov.add_trace(go.Histogram(x=team_sims[imp_cat], nbinsx=40,
                        name=f"Base ({swap_out})", opacity=0.65, marker_color="#4fc3f7"))
                    fig_ov.add_trace(go.Histogram(x=alt_sims[imp_cat],  nbinsx=40,
                        name=f"Alt ({swap_in})",  opacity=0.65, marker_color="#FF7043"))
                    fig_ov.update_layout(barmode="overlay", template="plotly_dark", height=320,
                        legend=dict(orientation="h", y=1.1), xaxis_title=imp_cat)
                    st.plotly_chart(fig_ov, use_container_width=True)

        # ── Tab 4: vs. Opponent Sims ───────────────────────────
        with tab_opp:
            st.markdown("### 👥 Head-to-Head Matchup Simulator")
            st.caption("Build a specific opponent's roster and simulate the matchup.")
            opp_h_opts = [n for n in all_h_names_mc if n not in mc_p["hitters"]]
            opp_p_opts = [n for n in all_p_names_mc if n not in mc_p["pitchers"]]
            opp_hitters  = st.multiselect("Opponent's Hitters",  options=opp_h_opts, max_selections=14, key="opp_hitters")
            opp_pitchers = st.multiselect("Opponent's Pitchers", options=opp_p_opts, max_selections=10, key="opp_pitchers")

            if st.button("⚔️ Simulate Matchup", key="btn_matchup"):
                if not opp_hitters and not opp_pitchers:
                    st.warning("Add at least one opponent player.")
                else:
                    with st.spinner("Simulating matchup..."):
                        opp_sims, _ = run_monte_carlo(
                            tuple(opp_hitters), tuple(opp_pitchers), mc_p["n_sim"],
                            mc_p["injury_pct"], mc_p["regression_pull"],
                            mc_p["platoon_boost"], seed=55)

                    h2h_rows = []; my_score = 0; opp_score = 0
                    for cat in MC_ALL_CATS:
                        if cat not in team_sims.columns or cat not in opp_sims.columns: continue
                        n = min(len(team_sims), len(opp_sims))
                        my_v  = team_sims[cat].values[:n]
                        opp_v = opp_sims[cat].values[:n]
                        wp = float(np.mean(my_v < opp_v) if cat in MC_LOWER_BETTER else np.mean(my_v > opp_v)) * 100
                        exp = "Win" if wp >= 55 else "Loss" if wp <= 45 else "Toss-up"
                        if exp == "Win":  my_score  += 1
                        elif exp == "Loss": opp_score += 1
                        h2h_rows.append({
                            "Category": cat,
                            "My Median":  round(float(np.median(my_v)),  2),
                            "Opp Median": round(float(np.median(opp_v)), 2),
                            "Win Prob": round(wp, 1),
                            "Expected": exp,
                        })

                    h2h_df = pd.DataFrame(h2h_rows)
                    def _ch2h(val):
                        if val == "Win":     return "color:#21C354; font-weight:bold"
                        if val == "Loss":    return "color:#FF4B4B; font-weight:bold"
                        return "color:#FFA500"
                    def _cwp(val):
                        try:
                            v = float(val)
                            if v >= 60: return "color:#21C354; font-weight:bold"
                            if v <= 40: return "color:#FF4B4B; font-weight:bold"
                        except: pass
                        return ""
                    st.dataframe(
                        h2h_df.style
                            .map(_ch2h, subset=["Expected"])
                            .map(_cwp,  subset=["Win Prob"])
                            .format({"Win Prob": "{:.1f}%"}),
                        use_container_width=True, hide_index=True)

                    ties = 9 - my_score - opp_score
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("My Expected Cats",  my_score)
                    mc2.metric("Toss-ups",           ties)
                    mc3.metric("Opp Expected Cats",  opp_score)

                    result_label = ("🏆 Projected WIN"   if my_score > opp_score else
                                    "⚔️ Projected SPLIT" if my_score == opp_score else
                                    "💀 Projected LOSS")
                    result_color = ("#21C354" if my_score > opp_score else
                                    "#FFA500" if my_score == opp_score else "#FF4B4B")
                    st.markdown(f"<h2 style='color:{result_color};text-align:center'>{result_label}</h2>",
                        unsafe_allow_html=True)

                    fig_h2h = go.Figure()
                    fig_h2h.add_trace(go.Bar(
                        x=h2h_df["Category"], y=h2h_df["Win Prob"],
                        marker_color=["#21C354" if v >= 55 else "#FF4B4B" if v <= 45 else "#FFA500"
                                      for v in h2h_df["Win Prob"]],
                        text=[f"{v:.0f}%" for v in h2h_df["Win Prob"]],
                        textposition="outside"))
                    fig_h2h.add_hline(y=50, line_dash="dash", line_color="white",
                        opacity=0.5, annotation_text="50% line")
                    fig_h2h.update_layout(template="plotly_dark", height=380,
                        yaxis=dict(range=[0, 110], title="Win Probability (%)"),
                        xaxis_title="Category", showlegend=False, margin=dict(t=20))
                    st.plotly_chart(fig_h2h, use_container_width=True)
