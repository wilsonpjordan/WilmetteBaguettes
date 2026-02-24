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
    bat_rec = score_hitters(bat_all[bat_all["Season"] == latest].copy())
    pit_rec = score_pitchers(pit_all[pit_all["Season"] == latest].copy())
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
#  DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────

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
    """Build (mean, std) for each stat, normalising partial seasons to full-season equivalents."""
    hist = src_df[src_df["Name"] == name].copy()
    if hist.empty:
        return {s: (0.0, 0.0) for s in stat_cols}

    counting = {"HR","R","RBI","SB","W","SO","BB","G","GS","IP","PA"}
    full_g, full_gs, full_pa, full_ip = 162, 32, 650, 180

    scaled_rows = []
    for _, row in hist.iterrows():
        row = row.copy()
        g  = row.get("G",  full_g);  gs = row.get("GS", full_gs)
        pa = row.get("PA", full_pa); ip = row.get("IP", full_ip)
        if "GS" in src_df.columns and not pd.isna(gs) and gs > 0:
            scale = full_gs / max(gs, 1)
        elif "PA" in src_df.columns and not pd.isna(pa) and pa > 0:
            scale = full_pa / max(pa, 1)
        elif not pd.isna(g) and g > 0:
            scale = full_g  / max(g,  1)
        else:
            scale = 1.0
        scale = min(scale, 2.5)
        for s in stat_cols:
            if s in counting and s in row.index and pd.notna(row[s]):
                row[s] = row[s] * scale
        scaled_rows.append(row)

    if not scaled_rows:
        return {s: (0.0, 0.0) for s in stat_cols}

    scaled = pd.DataFrame(scaled_rows)
    out = {}
    for s in stat_cols:
        if s not in scaled.columns:
            out[s] = (0.0, 0.0); continue
        vals = scaled[s].dropna()
        if len(vals) == 0:
            out[s] = (0.0, 0.0)
        elif len(vals) == 1:
            mu = float(vals.iloc[0])
            out[s] = (mu, max(abs(mu) * 0.10, 0.5))
        else:
            mu = float(vals.mean()); sd = float(vals.std())
            sd = min(sd, max(abs(mu) * 0.25, 0.5))
            out[s] = (mu, sd)
    return out


def _mc_apply_sabermetrics(name, dist, src_df, is_hitter, saber_weight, lg_h, lg_p):
    """
    Adjust projected means using sabermetric indicators.
    saber_weight 0.0 = pure counting-stat history, 1.0 = fully sabermetric-adjusted.

    Hitters
    -------
    HR   : Barrel% z-score continuously scales HR mean (+/- up to 20%)
    R    : wRC+ z-score scales R mean (+/- up to 15%)
    RBI  : wOBA z-score scales RBI mean (+/- up to 15%)
    SB   : Spd score z-score scales SB mean (+/- up to 20%)
    AVG  : xwOBA-wOBA gap nudges AVG mean; xBA-AVG gap also applied

    Pitchers
    --------
    ERA  : blended toward xFIP/SIERA (luck correction)
    WHIP : K-BB% z-score scales WHIP mean; GB% bonus for groundballers
    SO   : SwStr% z-score continuously scales SO mean (+/- up to 15%)
    W    : K/9 and GB% adjust slightly (sustainable wins indicator)
    """
    if saber_weight <= 0:
        return dist

    hist = src_df[src_df["Name"] == name]
    if hist.empty:
        return dist

    latest = hist.sort_values("Season").iloc[-1]

    def _safe(col):
        v = latest.get(col, np.nan)
        return float(v) if pd.notna(v) else None

    def _z(val, mu, sd):
        if sd and sd > 0: return (val - mu) / sd
        return 0.0

    def _adjust(dist, stat, factor):
        """Blend current mean with sabermetric-adjusted mean."""
        if stat not in dist: return dist
        mu, sd = dist[stat]
        adj_mu = mu * factor
        blended = mu * (1 - saber_weight) + adj_mu * saber_weight
        dist[stat] = (blended, sd)
        return dist

    if is_hitter:
        # ── HR: Barrel% ──────────────────────────────────────
        barrel  = _safe("Barrel%"); lg_barrel = lg_h.get("Barrel%", 0.08)
        sd_barrel = 0.04
        if barrel is not None:
            bz = _z(barrel, lg_barrel, sd_barrel)
            factor = 1.0 + np.clip(bz * 0.08, -0.20, 0.20)   # ±20% max
            dist = _adjust(dist, "HR", factor)

        # ── R: wRC+ ──────────────────────────────────────────
        wrcplus = _safe("wRC+"); lg_wrc = lg_h.get("wRC+", 100)
        sd_wrc  = 20
        if wrcplus is not None:
            wz = _z(wrcplus, lg_wrc, sd_wrc)
            factor = 1.0 + np.clip(wz * 0.05, -0.15, 0.15)
            dist = _adjust(dist, "R", factor)

        # ── RBI: wOBA ────────────────────────────────────────
        woba = _safe("wOBA"); lg_woba = lg_h.get("wOBA", 0.320)
        sd_woba = 0.040
        if woba is not None:
            wobaz = _z(woba, lg_woba, sd_woba)
            factor = 1.0 + np.clip(wobaz * 0.05, -0.15, 0.15)
            dist = _adjust(dist, "RBI", factor)

        # ── SB: Spd score ────────────────────────────────────
        spd = _safe("Spd"); lg_spd = lg_h.get("Spd", 4.5)
        sd_spd = 1.8
        if spd is not None:
            sz = _z(spd, lg_spd, sd_spd)
            factor = 1.0 + np.clip(sz * 0.08, -0.20, 0.20)
            dist = _adjust(dist, "SB", factor)

        # ── AVG: xwOBA vs wOBA gap + xBA vs AVG gap ──────────
        if "AVG" in dist:
            mu_avg, sd_avg = dist["AVG"]
            adj = 0.0
            xwoba = _safe("xwOBA"); woba2 = _safe("wOBA")
            if xwoba is not None and woba2 is not None:
                adj += (xwoba - woba2) * 0.30   # outperforming xwOBA → slight AVG drag
            xba = _safe("xBA"); avg2 = _safe("AVG")
            if xba is not None and avg2 is not None:
                adj += (xba - avg2) * 0.40       # xBA below AVG → AVG should fall
            blended_adj = mu_avg * (1 - saber_weight) + (mu_avg + adj) * saber_weight
            dist["AVG"] = (float(np.clip(blended_adj, 0.150, 0.400)), sd_avg)

    else:  # pitcher
        # ── ERA: blend toward xFIP / SIERA ───────────────────
        era   = _safe("ERA");   xfip  = _safe("xFIP"); siera = _safe("SIERA")
        if "ERA" in dist and (xfip is not None or siera is not None):
            mu_era, sd_era = dist["ERA"]
            true_era = np.nanmean([v for v in [xfip, siera] if v is not None])
            blended  = mu_era * (1 - saber_weight) + true_era * saber_weight
            dist["ERA"] = (float(np.clip(blended, 1.5, 8.0)), sd_era)

        # ── WHIP: K-BB% z-score + GB% bonus ──────────────────
        kbb = _safe("K-BB%"); gb = _safe("GB%")
        lg_kbb = lg_p.get("K-BB%", 0.12); sd_kbb = 0.07
        if "WHIP" in dist and kbb is not None:
            kbbz = _z(kbb, lg_kbb, sd_kbb)
            factor = 1.0 + np.clip(-kbbz * 0.04, -0.12, 0.12)  # high K-BB% → lower WHIP
            dist = _adjust(dist, "WHIP", factor)
        if "WHIP" in dist and gb is not None:
            gb_bonus = np.clip((gb - 0.44) * 0.15, -0.06, 0.06)
            mu_w, sd_w = dist["WHIP"]
            blended = mu_w * (1 - saber_weight) + (mu_w - gb_bonus) * saber_weight
            dist["WHIP"] = (float(np.clip(blended, 0.80, 2.20)), sd_w)

        # ── SO: SwStr% continuous scale ───────────────────────
        swstr = _safe("SwStr%"); lg_sw = lg_p.get("SwStr%", 0.115); sd_sw = 0.025
        if swstr is not None and "SO" in dist:
            swz = _z(swstr, lg_sw, sd_sw)
            factor = 1.0 + np.clip(swz * 0.05, -0.15, 0.15)
            dist = _adjust(dist, "SO", factor)

        # ── W: slight boost for high K% + GB% (sustainable wins)
        kpct = _safe("K%"); lg_k = lg_p.get("K%", 0.22); sd_k = 0.05
        if kpct is not None and gb is not None and "W" in dist:
            kz = _z(kpct, lg_k, sd_k)
            gb_bonus = np.clip((gb - 0.44) * 0.10, -0.04, 0.04)
            factor = 1.0 + np.clip(kz * 0.02 + gb_bonus, -0.08, 0.08)
            dist = _adjust(dist, "W", factor)

    return dist


def _mc_sim_player(dist, n_sim, stat_cols, lower_clip=None):
    """
    Sample from a Truncated Normal distribution bounded by historically
    plausible record ceilings/floors (Option 2 + Option 4 combo).

    Truncated Normal keeps the bell-curve shape intact but cannot produce
    draws outside [lo, hi]. Bounds are grounded in all-time single-season
    records, preventing absurd values like .860 AVG or negative ERA while
    preserving realistic variance within the valid range.
    """
    # (floor, ceiling) — grounded in historical single-season records
    STAT_BOUNDS = {
        # Hitter counting
        "HR":      (0,     65),
        "R":       (0,    150),
        "RBI":     (0,    165),
        "SB":      (0,     85),
        "BB":      (0,    170),
        # Hitter rate
        "AVG":     (0.150, 0.400),
        "OBP":     (0.250, 0.550),
        "SLG":     (0.250, 0.900),
        "OPS":     (0.500, 1.400),
        "wOBA":    (0.250, 0.550),
        "xwOBA":   (0.250, 0.550),
        "xBA":     (0.150, 0.380),
        "wRC+":    (30,    230),
        "BB%":     (0.03,  0.30),
        "K%":      (0.03,  0.50),
        "BABIP":   (0.200, 0.450),
        "Hard%":   (0.10,  0.80),
        "Barrel%": (0.01,  0.35),
        "SwStr%":  (0.02,  0.25),
        "EV":      (75,    100),
        "maxEV":   (90,    125),
        "LA":      (-10,    35),
        "Spd":     (1,      10),
        "Pull%":   (0.20,  0.65),
        "GB%":     (0.20,  0.70),
        "FB%":     (0.10,  0.60),
        # Pitcher counting
        "W":       (0,     25),
        "SO":      (0,    320),
        "IP":      (0,    250),
        # Pitcher rate
        "ERA":     (0.50,  9.00),
        "WHIP":    (0.60,  2.20),
        "FIP":     (0.50,  9.00),
        "xFIP":    (0.50,  9.00),
        "SIERA":   (0.50,  9.00),
        "LOB%":    (0.40,  0.95),
        "HR/FB":   (0.01,  0.30),
        "CSW%":    (0.15,  0.45),
        "K-BB%":   (-0.10, 0.40),
        "K/9":     (1.0,   16.0),
        "BB/9":    (0.5,    8.0),
    }

    lc = lower_clip or {}
    data = {}
    for s in stat_cols:
        mu, sd = dist.get(s, (0.0, 0.0))
        sd = max(sd, 1e-6)

        if s in STAT_BOUNDS:
            lo, hi = STAT_BOUNDS[s]
            if s in lc:
                lo = max(lo, lc[s])
            a = (lo - mu) / sd
            b = (hi - mu) / sd
            # If mean is outside bounds, clamp before sampling
            if a >= b:
                mu = float(np.clip(mu, lo + 1e-6, hi - 1e-6))
                a = (lo - mu) / sd
                b = (hi - mu) / sd
            draws = scipy_stats.truncnorm.rvs(a, b, loc=mu, scale=sd, size=n_sim)
        else:
            draws = np.random.normal(mu, sd, n_sim)
            if s in lc:
                draws = np.clip(draws, lc[s], None)

        data[s] = draws
    return pd.DataFrame(data)


@st.cache_data(show_spinner=False, ttl=3600)
def mc_run_simulation(hitters, pitchers, n_sim, injury_pct,
                      regression_pull, platoon_boost, saber_weight, run_count):
    """
    injury_pct   : 0.0–0.40  — probability each player suffers an IL stint
    regression_pull: 0.0–1.0 — pull means toward league average
    saber_weight : 0.0–1.0  — how much sabermetric adjustments shift the projected means
    run_count    : int       — unique per button-press to bust the cache
    """
    np.random.seed(run_count)
    lg_h = {s: bat_all[s].mean() for s in MC_H_STATS if s in bat_all.columns}
    lg_p = {s: pit_all[s].mean() for s in MC_P_STATS if s in pit_all.columns}
    # Also need K-BB% for pitchers
    if "K-BB%" not in lg_p and "K%" in pit_all.columns and "BB%" in pit_all.columns:
        pit_all_copy = pit_all.copy()
        pit_all_copy["K-BB%"] = pit_all_copy["K%"] - pit_all_copy["BB%"]
        lg_p["K-BB%"] = float(pit_all_copy["K-BB%"].mean())

    def pull(mu, la, strength):
        return mu * (1 - strength) + la * strength

    def apply_injury(sims, counting_stats, inj_prob):
        if inj_prob <= 0:
            return sims
        hurt    = np.random.random(n_sim) < inj_prob
        pct_out = np.random.uniform(0.15, 0.50, n_sim)
        scale   = np.where(hurt, 1.0 - pct_out, 1.0)
        for s in counting_stats:
            if s in sims.columns:
                sims[s] = np.clip(sims[s] * scale, 0, None)
        return sims

    sim_h = {c: np.zeros(n_sim) for c in MC_H_CATS}
    player_sims = {}

    for name in hitters:
        dist = _mc_player_dist(name, bat_all, MC_H_STATS)
        # 1. Mean reversion toward league average
        for s in MC_H_STATS:
            if s in dist and s in lg_h:
                mu, sd = dist[s]; dist[s] = (pull(mu, lg_h[s], regression_pull), sd)
        # 2. Sabermetric adjustments
        dist = _mc_apply_sabermetrics(name, dist, bat_all, True, saber_weight, lg_h, lg_p)
        # 3. Legacy platoon boost (only if saber_weight == 0, otherwise saber handles it)
        if platoon_boost and saber_weight == 0 and "Barrel%" in dist and "HR" in dist:
            bmu, _ = dist["Barrel%"]; hmu, hsd = dist["HR"]
            dist["HR"] = (hmu * 1.10 if bmu > 0.12 else hmu * 0.92 if bmu < 0.07 else hmu, hsd)
        sims = _mc_sim_player(dist, n_sim, MC_H_STATS, MC_COUNT_FLOORS)
        sims = apply_injury(sims, ["HR", "R", "RBI", "SB"], injury_pct)
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
        dist = _mc_apply_sabermetrics(name, dist, pit_all, False, saber_weight, lg_h, lg_p)
        if platoon_boost and saber_weight == 0 and "SwStr%" in dist and "SO" in dist:
            swmu, _ = dist["SwStr%"]; somu, sosd = dist["SO"]
            dist["SO"] = (somu * 1.08 if swmu > 0.14 else somu * 0.93 if swmu < 0.09 else somu, sosd)
        sims = _mc_sim_player(dist, n_sim, MC_P_STATS, MC_COUNT_FLOORS)
        sims = apply_injury(sims, ["W", "SO"], injury_pct)
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
        odf, _ = mc_run_simulation(hs, ps, n_sim, 0.15, 0.3, True, 0.5, run_count=run_count + i)
        for c in MC_ALL_CATS:
            if c in odf.columns: opp_cat[c].append(odf[c].values)
    return {c: np.array(v) for c, v in opp_cat.items() if v}


@st.cache_data(ttl=3600)
def mc_single_player_opp_pool(n_players, n_sim, is_hitter, run_count):
    """
    Build a league median for a SINGLE player position by simulating
    individual players rather than full rosters. This gives an apples-to-apples
    comparison: one player's projected stats vs. one average player at that position.
    """
    np.random.seed(run_count + 777)
    pool_src  = bat_all if is_hitter else pit_all
    stat_cols = MC_H_STATS if is_hitter else MC_P_STATS
    cats      = MC_H_CATS  if is_hitter else MC_P_CATS
    all_names = pool_src["Name"].dropna().unique().tolist()

    lg   = {s: pool_src[s].mean() for s in stat_cols if s in pool_src.columns}
    cat_arrays = {c: [] for c in cats}

    chosen = list(np.random.choice(all_names, size=min(n_players, len(all_names)), replace=False))
    for pname in chosen:
        dist = _mc_player_dist(pname, pool_src, stat_cols)
        # Apply light mean reversion only
        for s in stat_cols:
            if s in dist and s in lg:
                mu, sd = dist[s]
                dist[s] = (mu * 0.7 + lg[s] * 0.3, sd)
        sims = _mc_sim_player(dist, n_sim, stat_cols, MC_COUNT_FLOORS)
        # Apply realistic injury rate
        hurt    = np.random.random(n_sim) < 0.15
        pct_out = np.random.uniform(0.15, 0.50, n_sim)
        scale   = np.where(hurt, 1.0 - pct_out, 1.0)
        for c in cats:
            if c in sims.columns and c not in MC_LOWER_BETTER:
                cat_arrays[c].append(np.clip(sims[c].values * scale, 0, None))
            elif c in sims.columns:
                cat_arrays[c].append(sims[c].values)

    return {c: np.array(v) for c, v in cat_arrays.items() if v}


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────

st.sidebar.title("⚾ Draft Dashboard")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", [
    "📋 Draft Board",
    "🔍 Player Deep Dive",
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
    c1, c2 = st.columns(2)
    teams  = ["All"] + sorted(df["Team"].dropna().unique().tolist())
    team_f = c1.selectbox("Team", teams)
    if ptype == "Hitters" and "Position" in df.columns:
        pos_f = c2.selectbox("Position", ["All"] + sorted(df["Position"].dropna().unique().tolist()))
    else:
        pos_f = "All"
    if team_f != "All": df = df[df["Team"] == team_f]
    if pos_f  != "All" and "Position" in df.columns: df = df[df["Position"] == pos_f]
    z_cols  = [c for c in df.columns if c.startswith("z_")]
    sort_by = st.selectbox("Sort by", ["composite"] + z_cols)
    df = df.sort_values(sort_by, ascending=False).reset_index(drop=True)
    df.index += 1
    if ptype == "Hitters":
        show = ["Name","Team","composite","HR","R","RBI","SB","AVG",
                "wRC+","xwOBA","Barrel%","xBA","z_HR","z_R","z_RBI","z_SB","z_AVG"]
    else:
        show = ["Name","Team","composite","W","ERA","WHIP","SO",
                "xFIP","SIERA","K%","SwStr%","LOB%","z_W","z_ERA","z_WHIP","z_K"]
    show = [c for c in show if c in df.columns]
    z_present = [c for c in show if c.startswith("z_")]
    styled = (
        df[show].style
        .map(style_z,        subset=z_present)
        .background_gradient(subset=["composite"], cmap="RdYlGn")
        .format({c: "{:.2f}" for c in ["composite"] + z_present})
    )
    st.dataframe(styled, use_container_width=True, height=560)
    m1, m2, m3 = st.columns(3)
    m1.metric("Players",       len(df))
    m2.metric("Avg composite", f"{df['composite'].mean():.2f}")
    m3.metric("Top player",    df.iloc[0]["Name"] if len(df) else "—")


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
        if not rec.empty and "composite" in rec.columns:
            st.metric("Draft Value Score", f"{float(rec.iloc[0].get('composite', 0)):.2f}")
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

    # ══════════════════════════════════════════════════════════
    #  MONTE CARLO SECTION — Player Deep Dive
    # ══════════════════════════════════════════════════════════
    st.markdown("### 🎲 Monte Carlo Projections")

    # Determine if a prior team sim has been run
    mc_p_cached = st.session_state.get("mc_params")
    is_hitter_dive = (ptype == "Hitter")

    # Check if this player is in the cached roster
    in_cached_roster = False
    if mc_p_cached:
        roster_set = set(mc_p_cached.get("hitters", ())) | set(mc_p_cached.get("pitchers", ()))
        in_cached_roster = name in roster_set

    # ── Setup controls ──────────────────────────────────────
    with st.expander("⚙️ Simulation Settings", expanded=not in_cached_roster):
        dc1, dc2, dc3, dc4 = st.columns(4)
        d_n_sim     = dc1.select_slider("Simulations", options=[500,1_000,2_500,5_000,10_000],
                        value=2_500, key="dive_n_sim")
        d_inj       = dc2.slider("Injury risk (%)", 0, 40, 15, key="dive_inj",
                        help="% chance each player misses 15–50% of season")
        d_regr      = dc3.slider("Mean reversion", 0.0, 1.0, 0.3, 0.05, key="dive_regr",
                        help="0 = raw history, 1 = fully regress to league avg")
        d_saber     = dc4.slider("Sabermetric weight", 0.0, 1.0, 0.5, 0.05, key="dive_saber",
                        help="How much xwOBA/Barrel%/xFIP etc. shift the projection")

        run_dive = st.button("▶️ Run Monte Carlo for this player", type="primary", key="dive_run")

        if in_cached_roster and mc_p_cached and not run_dive:
            st.info(f"✅ **{name}** is in your cached team sim — showing those results below. "
                    f"Click the button above to run a fresh player-specific simulation.")

    # ── Run or use cache ────────────────────────────────────
    # We run a single-player sim: wrap player in a 1-person roster
    dive_key = f"dive_sim_{name}"

    if run_dive:
        st.session_state["mc_run_count"] = st.session_state.get("mc_run_count", 0) + 1
        rc = st.session_state["mc_run_count"]
        with st.spinner(f"🎲 Running {d_n_sim:,} simulations for {name}..."):
            if is_hitter_dive:
                p_sims, all_sims = mc_run_simulation(
                    hitters=(name,), pitchers=(),
                    n_sim=d_n_sim, injury_pct=d_inj/100,
                    regression_pull=d_regr, platoon_boost=False,
                    saber_weight=d_saber, run_count=rc)
            else:
                p_sims, all_sims = mc_run_simulation(
                    hitters=(), pitchers=(name,),
                    n_sim=d_n_sim, injury_pct=d_inj/100,
                    regression_pull=d_regr, platoon_boost=False,
                    saber_weight=d_saber, run_count=rc)
        st.session_state[dive_key] = {
            "team_sims": p_sims, "player_sims": all_sims,
            "n_sim": d_n_sim, "inj": d_inj, "regr": d_regr, "saber": d_saber,
        }

    elif in_cached_roster and mc_p_cached and dive_key not in st.session_state:
        # Use the cached team sim — run the whole team sim again (cached) and extract this player
        with st.spinner("Loading cached simulation..."):
            _, cached_player_sims = mc_run_simulation(
                hitters=mc_p_cached["hitters"], pitchers=mc_p_cached["pitchers"],
                n_sim=mc_p_cached["n_sim"], injury_pct=mc_p_cached["injury_pct"],
                regression_pull=mc_p_cached["regression_pull"],
                platoon_boost=mc_p_cached["platoon_boost"],
                saber_weight=mc_p_cached.get("saber_weight", 0.5),
                run_count=mc_p_cached.get("run_count", 0))
        if name in cached_player_sims:
            # Build a single-player team_sims equivalent
            psdf = cached_player_sims[name]
            cats = MC_H_CATS if is_hitter_dive else MC_P_CATS
            team_equiv = pd.DataFrame({c: psdf[c].values for c in cats if c in psdf.columns})
            st.session_state[dive_key] = {
                "team_sims": team_equiv, "player_sims": cached_player_sims,
                "n_sim": mc_p_cached["n_sim"], "inj": int(mc_p_cached["injury_pct"]*100),
                "regr": mc_p_cached["regression_pull"],
                "saber": mc_p_cached.get("saber_weight", 0.5),
            }

    # ── Display results ─────────────────────────────────────
    dive_data = st.session_state.get(dive_key)

    if dive_data is None:
        st.info("👆 Click **▶️ Run Monte Carlo for this player** above to generate projections.")
    else:
        tsims      = dive_data["team_sims"]
        psims_all  = dive_data["player_sims"]
        d_n        = dive_data["n_sim"]
        cats_dive  = MC_H_CATS if is_hitter_dive else MC_P_CATS
        cats_avail = [c for c in cats_dive if c in tsims.columns]

        st.caption(
            f"**{d_n:,} simulations** · Injury risk {dive_data['inj']}% · "
            f"Mean reversion {dive_data['regr']:.2f} · Sabermetric weight {dive_data['saber']:.2f}"
        )

        # ── P10 / Median / P90 table ──────────────────────
        st.markdown("#### 📊 Season Projection Ranges")
        proj_rows = []
        for cat in cats_avail:
            vals = tsims[cat].dropna()
            if len(vals) == 0: continue
            p10, p25, p50, p75, p90 = np.percentile(vals, [10, 25, 50, 75, 90])
            cv = round(float(vals.std() / abs(vals.mean()) * 100), 1) if vals.mean() != 0 else 0
            proj_rows.append({
                "Category": cat,
                "Floor (P10)": round(p10, 3 if cat in ["AVG","ERA","WHIP"] else 0),
                "P25":         round(p25, 3 if cat in ["AVG","ERA","WHIP"] else 0),
                "Median":      round(p50, 3 if cat in ["AVG","ERA","WHIP"] else 0),
                "P75":         round(p75, 3 if cat in ["AVG","ERA","WHIP"] else 0),
                "Ceiling (P90)":round(p90,3 if cat in ["AVG","ERA","WHIP"] else 0),
                "Volatility (CV%)": cv,
                "Direction":   "⬇️ Lower=Better" if cat in MC_LOWER_BETTER else "⬆️ Higher=Better",
            })
        if proj_rows:
            proj_df = pd.DataFrame(proj_rows)
            def _dir_color(val):
                return "color:#FFA500" if "Lower" in str(val) else "color:#4fc3f7"
            def _cv_color(val):
                try:
                    v = float(val)
                    if v > 40: return "color:#FF4B4B; font-weight:bold"
                    if v > 25: return "color:#FFA500"
                    return "color:#21C354"
                except: return ""
            st.dataframe(
                proj_df.style
                    .map(_dir_color, subset=["Direction"])
                    .map(_cv_color,  subset=["Volatility (CV%)"])
                    .format({"Volatility (CV%)": "{:.1f}%"}),
                use_container_width=True, hide_index=True)
            st.caption("**CV%** = volatility. Green < 25% = consistent. Orange 25–40% = variable. Red > 40% = highly unpredictable.")

        st.markdown("---")

        # ── Distribution histograms ───────────────────────
        st.markdown("#### 📈 Projected Distribution by Category")
        n_cats = len(cats_avail)
        hist_cols = st.columns(min(n_cats, 3))
        for i, cat in enumerate(cats_avail):
            vals = tsims[cat].dropna().values
            if len(vals) == 0: continue
            p10v, p50v, p90v = np.percentile(vals, [10, 50, 90])
            with hist_cols[i % 3]:
                fig_h = go.Figure()
                fig_h.add_trace(go.Histogram(
                    x=vals, nbinsx=45,
                    marker_color="#4fc3f7", showlegend=False,
                    hovertemplate=f"{cat}: %{{x}}<br>Count: %{{y}}<extra></extra>"))
                # Median line
                fig_h.add_vline(x=float(p50v), line_dash="dash", line_color="yellow",
                    annotation_text=f"Med: {p50v:.3f}" if cat in ["AVG","ERA","WHIP"] else f"Med: {int(p50v)}",
                    annotation_position="top right", annotation_font_size=10)
                # P10–P90 shaded band
                fig_h.add_vrect(x0=float(p10v), x1=float(p90v),
                    fillcolor="rgba(79,195,247,0.10)", line_width=0)
                # P10 and P90 labels
                fig_h.add_vline(x=float(p10v), line_dash="dot", line_color="rgba(255,255,255,0.3)",
                    annotation_text="P10", annotation_position="top left", annotation_font_size=9)
                fig_h.add_vline(x=float(p90v), line_dash="dot", line_color="rgba(255,255,255,0.3)",
                    annotation_text="P90", annotation_position="top right", annotation_font_size=9)
                fig_h.update_layout(
                    title=dict(text=cat, font_size=14),
                    template="plotly_dark", height=240,
                    margin=dict(l=8, r=8, t=36, b=8),
                    xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_h, use_container_width=True)

        st.markdown("---")

        # ── vs. League median comparison ──────────────────
        st.markdown("#### 🆚 vs. Average Player at Position")
        st.caption(
            "Compares this player's projected stats against a pool of average players "
            "at the same position — so HR is one player vs. one player, not a whole team."
        )
        with st.spinner("Building position comparison pool..."):
            rc_opp = dive_data.get("run_count", st.session_state.get("mc_run_count", 0))
            opp_pool_dive = mc_single_player_opp_pool(
                n_players=30, n_sim=min(d_n, 1000),
                is_hitter=is_hitter_dive, run_count=rc_opp)

        RATE_CATS = {"AVG", "ERA", "WHIP"}

        def _fmt(val, cat):
            """Format a stat value appropriately — no trailing zeros."""
            if cat in RATE_CATS:
                return round(float(val), 3)
            return round(float(val), 1)

        vs_rows = []
        for cat in cats_avail:
            if cat not in opp_pool_dive or len(opp_pool_dive[cat]) == 0: continue
            my_vals  = tsims[cat].values
            # opp_pool_dive[cat] is shape (n_players, n_sim) — take median across players
            opp_med_per_player = np.median(opp_pool_dive[cat], axis=1)  # one median per player
            opp_med  = float(np.median(opp_med_per_player))
            my_med   = float(np.median(my_vals))
            # Win% vs a randomly selected average player
            opp_flat = opp_pool_dive[cat].flatten()
            n        = min(len(my_vals), len(opp_flat))
            win_pct  = float(
                np.mean(my_vals[:n] < opp_flat[:n]) if cat in MC_LOWER_BETTER
                else np.mean(my_vals[:n] > opp_flat[:n])
            ) * 100
            edge     = my_med - opp_med
            strength = ("💪 Dominant" if win_pct >= 65 else
                        "✅ Solid"    if win_pct >= 52 else
                        "⚖️ Toss-up"  if win_pct >= 46 else
                        "⚠️ Weak"     if win_pct >= 35 else "🚨 Punt")
            vs_rows.append({
                "Category":       cat,
                "Your Median":    _fmt(my_med,  cat),
                "Avg Player Med": _fmt(opp_med, cat),
                "Edge":           _fmt(edge,    cat),
                "Win %":          round(win_pct, 1),
                "Assessment":     strength,
            })

        if vs_rows:
            vs_df = pd.DataFrame(vs_rows)
            def _win_color(val):
                try:
                    v = float(val)
                    if v >= 65: return "color:#21C354; font-weight:bold"
                    if v >= 52: return "color:#21C354"
                    if v >= 46: return "color:#FFA500"
                    if v >= 35: return "color:#FF4B4B"
                    return "color:#FF4B4B; font-weight:bold"
                except: return ""
            def _edge_color(val):
                try:
                    v = float(val)
                    if v > 0: return "color:#21C354"
                    if v < 0: return "color:#FF4B4B"
                except: return ""
            st.dataframe(
                vs_df.style
                    .map(_win_color,  subset=["Win %"])
                    .map(_edge_color, subset=["Edge"])
                    .format({"Win %": "{:.1f}%", "Your Median": "{}", "Avg Player Med": "{}", "Edge": "{}"}),
                use_container_width=True, hide_index=True)

            # Mini radar of win% per category
            cats_r   = vs_df["Category"].tolist()
            probs_r  = vs_df["Win %"].tolist()
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=probs_r + [probs_r[0]], theta=cats_r + [cats_r[0]],
                fill="toself", line_color="#4fc3f7",
                fillcolor="rgba(79,195,247,0.15)", name="Win%"))
            fig_radar.add_trace(go.Scatterpolar(
                r=[50] * (len(cats_r) + 1), theta=cats_r + [cats_r[0]],
                mode="lines", line=dict(dash="dash", color="gray", width=1),
                name="50% baseline"))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="%", tickfont_size=9)),
                template="plotly_dark", height=380,
                legend=dict(orientation="h", y=-0.15),
                margin=dict(l=40, r=40, t=20, b=60))
            st.plotly_chart(fig_radar, use_container_width=True)

            exp_cat_wins = sum(r["Win %"] / 100 for _, r in vs_df.iterrows())
            cats_total   = len(cats_avail)
            st.metric(
                f"Expected category wins vs. average opponent (out of {cats_total})",
                f"{exp_cat_wins:.2f} / {cats_total}",
                f"{'above' if exp_cat_wins > cats_total/2 else 'below'} .500")


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
                 "tag":  "—",
                 "composite": float(rec.iloc[0].get("composite",0)) if not rec.empty else 0,
                 "note": note_input}
        if not any(t["name"] == name for t in st.session_state.targets):
            st.session_state.targets.append(entry); st.success(f"✅ {name} added to your target list!")
        else:
            st.info(f"{name} is already in your target list.")
    st.markdown("---")
    st.markdown("### 📄 Full Historical Stats")
    drop = [c for c in ["playerid","rank","composite"] if c in hist.columns]
    st.dataframe(hist.drop(columns=drop).set_index("Season"), use_container_width=True)


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
    show_c = [c for c in ["Name","Team",col,"composite"] if c in top10.columns]
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
                        h_c = [c for c in ["Name","Team","composite","HR","AVG","xwOBA"] if c in sug_h.columns]
                        st.dataframe(sug_h[h_c], use_container_width=True, hide_index=True)
                    if not sug_p.empty:
                        st.markdown("**Pitcher targets:**")
                        p_c = [c for c in ["Name","Team","composite","ERA","xFIP","K%"] if c in sug_p.columns]
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
                    "tag":"—",
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
                    mini = ([c for c in ["HR","AVG","xwOBA","Barrel%","SB","wRC+"] if c in r.index]
                            if t["type"]=="Hitter" else
                            [c for c in ["ERA","xFIP","K%","SwStr%","WHIP"] if c in r.index])
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
                cc = [c for c in ["Name","Team","composite","HR","R","RBI","SB","AVG","wRC+","xwOBA","xBA","Barrel%","SwStr%"] if c in h_df.columns]
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
                cc = [c for c in ["Name","Team","composite","W","ERA","WHIP","SO","xFIP","SIERA","K%","SwStr%","LOB%"] if c in p_df.columns]
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
            show_h = [c for c in ["Name","Team","composite","HR","R","RBI","SB","AVG","wRC+","xwOBA","Barrel%","z_HR","z_R","z_RBI","z_SB","z_AVG"] if c in avail_h.columns]
            is_target = avail_h["Name"].isin([t["name"] for t in st.session_state.targets])
            st.markdown(f"**{len(avail_h)} hitters available** &nbsp;|&nbsp; 🎯 {is_target.sum()} on your target list")
            st.dataframe(avail_h[show_h].style.map(style_z,subset=[c for c in show_h if c.startswith("z_")]).background_gradient(subset=["composite"],cmap="RdYlGn"), use_container_width=True, height=420)
            pick_h = st.selectbox("Select hitter", [""]+avail_h["Name"].tolist(), key="sel_h")
            ca, cb, cc = st.columns(3)
            if ca.button("✅ Add to MY team", key="btn_add_h") and pick_h:
                st.session_state.drafted_h.add(pick_h); st.session_state.my_h.append(pick_h); st.rerun()
            if cb.button("❌ Drafted (not me)", key="btn_skip_h") and pick_h:
                st.session_state.drafted_h.add(pick_h); st.rerun()
            if cc.button("🎯 Add to Targets", key="btn_target_h") and pick_h:
                rr = bat_rec[bat_rec["Name"]==pick_h]
                entry = {"name":pick_h,"type":"Hitter","tag":"—",
                    "composite":float(rr.iloc[0].get("composite",0)) if not rr.empty else 0,"note":"Added from draft room"}
                if not any(t["name"]==pick_h for t in st.session_state.targets):
                    st.session_state.targets.append(entry); st.success(f"🎯 {pick_h} added to targets!")
        with tab_p:
            avail_p = pit_rec[~pit_rec["Name"].isin(st.session_state.drafted_p)].sort_values("composite",ascending=False).reset_index(drop=True)
            avail_p.index += 1
            show_p = [c for c in ["Name","Team","composite","W","ERA","WHIP","SO","xFIP","SIERA","K%","z_W","z_ERA","z_WHIP","z_K"] if c in avail_p.columns]
            st.markdown(f"**{len(avail_p)} pitchers available**")
            st.dataframe(avail_p[show_p].style.map(style_z,subset=[c for c in show_p if c.startswith("z_")]).background_gradient(subset=["composite"],cmap="RdYlGn"), use_container_width=True, height=420)
            pick_p = st.selectbox("Select pitcher", [""]+avail_p["Name"].tolist(), key="sel_p")
            cd, ce, cf = st.columns(3)
            if cd.button("✅ Add to MY team", key="btn_add_p") and pick_p:
                st.session_state.drafted_p.add(pick_p); st.session_state.my_p.append(pick_p); st.rerun()
            if ce.button("❌ Drafted (not me)", key="btn_skip_p") and pick_p:
                st.session_state.drafted_p.add(pick_p); st.rerun()
            if cf.button("🎯 Add to Targets", key="btn_target_p") and pick_p:
                rr = pit_rec[pit_rec["Name"]==pick_p]
                entry = {"name":pick_p,"type":"Pitcher","tag":"—",
                    "composite":float(rr.iloc[0].get("composite",0)) if not rr.empty else 0,"note":"Added from draft room"}
                if not any(t["name"]==pick_p for t in st.session_state.targets):
                    st.session_state.targets.append(entry); st.success(f"🎯 {pick_p} added to targets!")

    with right:
        st.markdown("### 🏆 My Team")
        if st.session_state.my_h:
            st.markdown("**Hitters**")
            for name in st.session_state.my_h:
                row = bat_rec[bat_rec["Name"]==name]
                composite = row.iloc[0]["composite"] if not row.empty else 0
                st.caption(f"Composite: {float(composite):.2f}")
                dot  = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(risk,"⚪")
                st.markdown(f"{dot} **{name}** {tag}")
        if st.session_state.my_p:
            st.markdown("**Pitchers**")
            for name in st.session_state.my_p:
                row = pit_rec[pit_rec["Name"]==name]
                composite = row.iloc[0]["composite"] if not row.empty else 0
                st.caption(f"Composite: {float(composite):.2f}")
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

    all_h_names_mc = sorted(bat_all["Name"].dropna().unique())
    all_p_names_mc = sorted(pit_all["Name"].dropna().unique())

    # ═══════════════════════════════════════════════════════════
    #  DEPTH CHART — visual roster builder
    # ═══════════════════════════════════════════════════════════

    # Yahoo standard positions
    LINEUP_POSITIONS = {
        "C":  {"label":"C",  "x":0.50,"y":0.10,"max":1},
        "1B": {"label":"1B", "x":0.72,"y":0.28,"max":1},
        "2B": {"label":"2B", "x":0.60,"y":0.35,"max":1},
        "3B": {"label":"3B", "x":0.28,"y":0.28,"max":1},
        "SS": {"label":"SS", "x":0.40,"y":0.35,"max":1},
        "LF": {"label":"LF", "x":0.18,"y":0.55,"max":1},
        "CF": {"label":"CF", "x":0.50,"y":0.65,"max":1},
        "RF": {"label":"RF", "x":0.82,"y":0.55,"max":1},
        "CI": {"label":"CI", "x":0.72,"y":0.14,"max":1},
        "MI": {"label":"MI", "x":0.28,"y":0.14,"max":1},
        "Util":{"label":"Util","x":0.50,"y":0.20,"max":1},
        "BN1":{"label":"BN", "x":0.15,"y":0.88,"max":1},
        "BN2":{"label":"BN", "x":0.35,"y":0.88,"max":1},
        "BN3":{"label":"BN", "x":0.55,"y":0.88,"max":1},
        "BN4":{"label":"BN", "x":0.75,"y":0.88,"max":1},
        "SP1":{"label":"SP", "x":0.10,"y":0.78,"max":1},
        "SP2":{"label":"SP", "x":0.28,"y":0.78,"max":1},
        "SP3":{"label":"SP", "x":0.46,"y":0.78,"max":1},
        "SP4":{"label":"SP", "x":0.64,"y":0.78,"max":1},
        "SP5":{"label":"SP", "x":0.82,"y":0.78,"max":1},
        "RP1":{"label":"RP", "x":0.20,"y":0.68,"max":1},
        "RP2":{"label":"RP", "x":0.38,"y":0.68,"max":1},
        "RP3":{"label":"RP", "x":0.56,"y":0.68,"max":1},
        "RP4":{"label":"RP", "x":0.74,"y":0.68,"max":1},
        "RP5":{"label":"RP", "x":0.90,"y":0.68,"max":1},
    }

    # Init depth chart state
    if "dc_roster" not in st.session_state:
        st.session_state["dc_roster"] = {pos: "" for pos in LINEUP_POSITIONS}

    st.markdown("### 🏟️ Depth Chart Roster")
    st.caption("Assign players to positions below, then run the sim. SP/RP/BN slots are pitcher spots.")

    st.markdown("""
    <style>
    .dc-field { background: radial-gradient(ellipse 80% 60% at 50% 50%, #2d5a1b 60%, #1a3a0d 100%);
                border-radius:12px; padding:4px; position:relative; border:2px solid #3d7a2b; }
    .dc-slot  { background:rgba(0,0,0,0.55); border:1.5px solid #4fc3f7; border-radius:8px;
                padding:5px 8px; text-align:center; font-size:11px; cursor:pointer;
                transition:all 0.2s; min-height:42px; }
    .dc-slot:hover { border-color:#FFD700; background:rgba(79,195,247,0.18); }
    .dc-slot-filled { border-color:#21C354 !important; background:rgba(33,195,84,0.12) !important; }
    .dc-pos-label { color:#4fc3f7; font-weight:700; font-size:10px; letter-spacing:1px; }
    .dc-player-name { color:#fff; font-size:11px; font-weight:600; margin-top:2px; white-space:nowrap;
                      overflow:hidden; text-overflow:ellipsis; max-width:80px; }
    .dc-infield-dirt { position:absolute; width:30%; height:30%; background:radial-gradient(#8B5E3C,#6B4226);
                       border-radius:50%; top:35%; left:35%; opacity:0.35; }
    </style>
    """, unsafe_allow_html=True)

    # Draw depth chart using a plotly figure as background + columns for slots
    # Use columns grid layout for the actual selectors
    dc = st.session_state["dc_roster"]

    # ── Draw the baseball field SVG background + position slots using plotly ──
    def build_field_figure(dc, pos_defs):
        fig = go.Figure()
        # Field background — green oval
        theta = np.linspace(0, 2*np.pi, 200)
        fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1,
            fillcolor="#1e4d0f", line_color="#2d6e1a", line_width=2)
        # Infield dirt diamond
        dia_x = [0.50, 0.72, 0.50, 0.28, 0.50]
        dia_y = [0.12, 0.35, 0.58, 0.35, 0.12]
        fig.add_trace(go.Scatter(x=dia_x, y=dia_y, fill="toself",
            fillcolor="#7a5230", line=dict(color="#5c3d20", width=2),
            mode="lines", showlegend=False, hoverinfo="skip"))
        # Outfield arc
        arc_theta = np.linspace(np.pi*0.05, np.pi*0.95, 100)
        arc_x = 0.50 + 0.46 * np.cos(arc_theta)
        arc_y = 0.35 + 0.50 * np.sin(arc_theta)
        fig.add_trace(go.Scatter(x=arc_x, y=arc_y, mode="lines",
            line=dict(color="#4a9e2f", width=3), showlegend=False, hoverinfo="skip"))
        # Pitcher's mound
        fig.add_shape(type="circle", x0=0.44, y0=0.295, x1=0.56, y1=0.365,
            fillcolor="#9e7a50", line_color="#7a5c3a", line_width=1.5)
        # Home plate
        fig.add_shape(type="rect", x0=0.47, y0=0.09, x1=0.53, y1=0.13,
            fillcolor="white", line_color="#ccc", line_width=1)
        # Position slots
        for pos_key, pd_ in pos_defs.items():
            player = dc.get(pos_key, "")
            is_filled = bool(player)
            color     = "#21C354" if is_filled else "#4fc3f7"
            bg        = "rgba(33,195,84,0.20)" if is_filled else "rgba(0,0,0,0.55)"
            label_txt = pd_["label"]
            player_short = player[:10] + "…" if len(player) > 10 else player
            display   = f"<b>{label_txt}</b><br><span style='font-size:9px'>{player_short if player_short else '—'}</span>"
            fig.add_annotation(
                x=pd_["x"], y=pd_["y"],
                text=display,
                showarrow=False,
                font=dict(size=10, color=color),
                bgcolor=bg,
                bordercolor=color,
                borderwidth=1.5,
                borderpad=4,
                align="center",
            )
        fig.update_layout(
            xaxis=dict(range=[0,1], visible=False, fixedrange=True),
            yaxis=dict(range=[0,1], visible=False, fixedrange=True, scaleanchor="x"),
            margin=dict(l=0,r=0,t=0,b=0),
            height=500,
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1e4d0f",
            showlegend=False,
            hovermode=False,
        )
        return fig

    col_field, col_sliders = st.columns([3, 2])

    with col_field:
        fig_field = build_field_figure(dc, LINEUP_POSITIONS)
        st.plotly_chart(fig_field, use_container_width=True, config={"displayModeBar": False})

    with col_sliders:
        st.markdown("**🔴 Batting Order / Position Players**")
        hit_positions = ["C","1B","2B","3B","SS","LF","CF","RF","CI","MI","Util","BN1","BN2","BN3","BN4"]
        pit_positions = ["SP1","SP2","SP3","SP4","SP5","RP1","RP2","RP3","RP4","RP5"]

        with st.expander("⚾ Hitter Slots", expanded=True):
            for pos in hit_positions:
                cur = dc.get(pos, "")
                options = [""] + [n for n in all_h_names_mc if n not in dc.values() or n == cur]
                sel = st.selectbox(
                    f"{LINEUP_POSITIONS[pos]['label']} slot",
                    options=options,
                    index=options.index(cur) if cur in options else 0,
                    key=f"dc_{pos}",
                    label_visibility="collapsed",
                    placeholder=f"{LINEUP_POSITIONS[pos]['label']} — select player",
                )
                st.session_state["dc_roster"][pos] = sel

        with st.expander("⚾ Pitcher Slots", expanded=True):
            for pos in pit_positions:
                cur = dc.get(pos, "")
                options = [""] + [n for n in all_p_names_mc if n not in [dc.get(p,"") for p in pit_positions] or n == cur]
                sel = st.selectbox(
                    f"{LINEUP_POSITIONS[pos]['label']} slot",
                    options=options,
                    index=options.index(cur) if cur in options else 0,
                    key=f"dc_{pos}",
                    label_visibility="collapsed",
                    placeholder=f"{LINEUP_POSITIONS[pos]['label']} — select player",
                )
                st.session_state["dc_roster"][pos] = sel

    # Derive hitter/pitcher lists from depth chart
    dc_hitters = list({v for k,v in dc.items() if k in hit_positions and v})
    dc_pitchers = list({v for k,v in dc.items() if k in pit_positions and v})

    # Sync to my_h / my_p session state so other pages see them
    if dc_hitters: st.session_state["my_h"] = dc_hitters
    if dc_pitchers: st.session_state["my_p"] = dc_pitchers

    # ── Settings row ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚙️ Simulation Settings")
    col_a, col_b = st.columns(2)
    n_sim_val      = col_a.select_slider("Number of simulations",
        options=[500,1_000,2_500,5_000,10_000], value=2_500)
    league_size_mc = col_b.slider("League size", 8, 16, 12, key="mc_league")

    adv1, adv2, adv3, adv4 = st.columns(4)
    injury_pct_val   = adv1.slider("Injury risk (%)", 0, 40, 15, key="mc_inj",
        help="% chance each player suffers an IL stint; when injured misses 15–50% of season.")
    regr_pull_val    = adv2.slider("Mean reversion", 0.0, 1.0, 0.3, 0.05, key="mc_regr",
        help="0 = raw historical mean. 1 = fully regress to league average.")
    saber_weight_val = adv3.slider("Sabermetric weight", 0.0, 1.0, 0.5, 0.05, key="mc_saber",
        help="How much xwOBA/Barrel%/xFIP etc. adjust projected means.")
    platoon_val      = adv4.checkbox("Legacy quality boost", value=False, key="mc_platoon")

    run_clicked = st.button(
        "▶️ Run Monte Carlo Simulation", type="primary",
        disabled=(len(dc_hitters) == 0 and len(dc_pitchers) == 0),
        key="mc_run_btn",
    )

    if run_clicked:
        st.session_state["mc_run_count"] = st.session_state.get("mc_run_count", 0) + 1
        st.session_state["mc_params"] = {
            "n_sim":          n_sim_val,
            "league_size":    league_size_mc,
            "hitters":        tuple(dc_hitters),
            "pitchers":       tuple(dc_pitchers),
            "injury_pct":     injury_pct_val / 100,
            "regression_pull":regr_pull_val,
            "saber_weight":   saber_weight_val,
            "platoon_boost":  platoon_val,
            "run_count":      st.session_state["mc_run_count"],
        }

    st.markdown("---")

    # ── Results tabs ────────────────────────────────────────────
    tab_results, tab_cat, tab_alt, tab_opp, tab_season = st.tabs([
        "📈 Season Projections",
        "🏆 Category Win Odds",
        "🔀 Roster Alternatives",
        "👥 vs. Opponent",
        "📅 Season Sim",
    ])

    mc_p = st.session_state.get("mc_params")

    if mc_p is None:
        for t in [tab_results, tab_cat, tab_alt, tab_opp, tab_season]:
            with t:
                st.info("👆 Build your roster on the depth chart above and click **▶️ Run Monte Carlo Simulation** to begin.")
    else:
        with st.spinner("🎲 Running simulations..."):
            team_sims, player_sims = mc_run_simulation(
                hitters        = mc_p["hitters"],
                pitchers       = mc_p["pitchers"],
                n_sim          = mc_p["n_sim"],
                injury_pct     = mc_p["injury_pct"],
                regression_pull= mc_p["regression_pull"],
                platoon_boost  = mc_p["platoon_boost"],
                saber_weight   = mc_p.get("saber_weight", 0.5),
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
            st.caption("**CV%** = volatility. High CV% = unpredictable category for your roster.")

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
                spc = ["Name","Type"] + [c for c in MC_H_CATS + MC_P_CATS + ["wRC+","xwOBA","Barrel%","K%","xFIP"] if c in pproj.columns]
                st.dataframe(pproj[spc].sort_values(["Type","Name"]), use_container_width=True, hide_index=True)

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
                            "⚖️ Toss-up" if awp >= 0.46 else "⚠️ Weak" if awp >= 0.35 else "🚨 Punt")
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
                r=[50]*(len(cats_r)+1), theta=cats_r + [cats_r[0]],
                mode="lines", line=dict(dash="dash", color="gray", width=1), name="50% line"))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(range=[0,100], ticksuffix="%", tickfont_size=9)),
                template="plotly_dark", height=420,
                legend=dict(orientation="h", y=-0.1), margin=dict(l=40,r=40,t=40,b=60))
            st.plotly_chart(fig_radar, use_container_width=True)
            exp_wins = sum(r["Win%"]/100 for _,r in win_df.iterrows())
            st.metric("📊 Expected Category Wins per matchup", f"{exp_wins:.2f} / 9",
                f"{'above' if exp_wins > 4.5 else 'below'} .500")

        # ── Tab 3: Roster Alternatives ─────────────────────────
        with tab_alt:
            st.markdown("### 🔀 Roster Alternative Comparison")
            st.caption("Swap one player and see how category distributions shift.")
            all_current = list(mc_p["hitters"]) + list(mc_p["pitchers"])
            if not all_current:
                st.info("Add players in the depth chart above first.")
            else:
                swap_out  = st.selectbox("Player to replace", all_current, key="swap_out")
                is_h_swap = swap_out in mc_p["hitters"]
                taken     = set(mc_p["hitters"] if is_h_swap else mc_p["pitchers"])
                pool_opts = [n for n in (all_h_names_mc if is_h_swap else all_p_names_mc) if n not in taken]
                swap_in   = st.selectbox("Replace with", pool_opts, key="swap_in")

                if st.button("🔄 Compare Rosters", key="btn_compare"):
                    if is_h_swap:
                        alt_h = tuple(h if h != swap_out else swap_in for h in mc_p["hitters"])
                        alt_p = mc_p["pitchers"]
                    else:
                        alt_h = mc_p["hitters"]
                        alt_p = tuple(pp if pp != swap_out else swap_in for pp in mc_p["pitchers"])
                    with st.spinner("Running alternative simulation..."):
                        alt_sims, _ = mc_run_simulation(
                            alt_h, alt_p, mc_p["n_sim"],
                            mc_p["injury_pct"], mc_p["regression_pull"],
                            mc_p["platoon_boost"], mc_p.get("saber_weight", 0.5),
                            run_count=mc_p.get("run_count", 0) + 77)
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
                            direction = "✅ Better" if delta > 0.01 else "❌ Worse" if delta < -0.01 else "➡️ Similar"
                        comp_rows.append({
                            "Category": cat,
                            f"Base ({swap_out})": round(bm, 2),
                            f"Alt ({swap_in})": round(am, 2),
                            "Delta": round(delta, 2), "Impact": direction,
                        })
                    comp_df = pd.DataFrame(comp_rows)
                    def _ci(val):
                        if "Better" in str(val): return "color:#21C354; font-weight:bold"
                        if "Worse"  in str(val): return "color:#FF4B4B; font-weight:bold"
                        return "color:#aaa"
                    st.dataframe(comp_df.style.map(_ci, subset=["Impact"]), use_container_width=True, hide_index=True)
                    imp_cat = comp_df.reindex(comp_df["Delta"].abs().sort_values(ascending=False).index).iloc[0]["Category"]
                    st.markdown(f"#### Distribution shift — most impacted: **{imp_cat}**")
                    fig_ov = go.Figure()
                    fig_ov.add_trace(go.Histogram(x=team_sims[imp_cat], nbinsx=40,
                        name=f"Base ({swap_out})", opacity=0.65, marker_color="#4fc3f7"))
                    fig_ov.add_trace(go.Histogram(x=alt_sims[imp_cat], nbinsx=40,
                        name=f"Alt ({swap_in})", opacity=0.65, marker_color="#FF7043"))
                    fig_ov.update_layout(barmode="overlay", template="plotly_dark", height=320,
                        legend=dict(orientation="h", y=1.1), xaxis_title=imp_cat)
                    st.plotly_chart(fig_ov, use_container_width=True)

        # ── Tab 4: vs. Opponent ────────────────────────────────
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
                        opp_sims, _ = mc_run_simulation(
                            tuple(opp_hitters), tuple(opp_pitchers), mc_p["n_sim"],
                            mc_p["injury_pct"], mc_p["regression_pull"],
                            mc_p["platoon_boost"], mc_p.get("saber_weight", 0.5),
                            run_count=mc_p.get("run_count", 0) + 55)
                    h2h_rows = []; my_score = 0; opp_score = 0
                    for cat in MC_ALL_CATS:
                        if cat not in team_sims.columns or cat not in opp_sims.columns: continue
                        n = min(len(team_sims), len(opp_sims))
                        my_v  = team_sims[cat].values[:n]
                        opp_v = opp_sims[cat].values[:n]
                        wp = float(np.mean(my_v < opp_v) if cat in MC_LOWER_BETTER else np.mean(my_v > opp_v)) * 100
                        exp = "Win" if wp >= 55 else "Loss" if wp <= 45 else "Toss-up"
                        if exp == "Win": my_score += 1
                        elif exp == "Loss": opp_score += 1
                        h2h_rows.append({
                            "Category": cat,
                            "My Median":  round(float(np.median(my_v)), 2),
                            "Opp Median": round(float(np.median(opp_v)), 2),
                            "Win Prob": round(wp, 1), "Expected": exp,
                        })
                    h2h_df = pd.DataFrame(h2h_rows)
                    def _ch2h(val):
                        if val == "Win":  return "color:#21C354; font-weight:bold"
                        if val == "Loss": return "color:#FF4B4B; font-weight:bold"
                        return "color:#FFA500"
                    def _cwp(val):
                        try:
                            v = float(val)
                            if v >= 60: return "color:#21C354; font-weight:bold"
                            if v <= 40: return "color:#FF4B4B; font-weight:bold"
                        except: pass
                        return ""
                    st.dataframe(
                        h2h_df.style.map(_ch2h, subset=["Expected"]).map(_cwp, subset=["Win Prob"])
                            .format({"Win Prob": "{:.1f}%"}),
                        use_container_width=True, hide_index=True)
                    ties = 9 - my_score - opp_score
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("My Expected Cats", my_score)
                    mc2.metric("Toss-ups", ties)
                    mc3.metric("Opp Expected Cats", opp_score)
                    result_label = ("🏆 Projected WIN" if my_score > opp_score else
                                    "⚔️ Projected SPLIT" if my_score == opp_score else "💀 Projected LOSS")
                    result_color = ("#21C354" if my_score > opp_score else
                                    "#FFA500" if my_score == opp_score else "#FF4B4B")
                    st.markdown(f"<h2 style='color:{result_color};text-align:center'>{result_label}</h2>",
                        unsafe_allow_html=True)
                    fig_h2h = go.Figure()
                    fig_h2h.add_trace(go.Bar(
                        x=h2h_df["Category"], y=h2h_df["Win Prob"],
                        marker_color=["#21C354" if v >= 55 else "#FF4B4B" if v <= 45 else "#FFA500"
                                      for v in h2h_df["Win Prob"]],
                        text=[f"{v:.0f}%" for v in h2h_df["Win Prob"]], textposition="outside"))
                    fig_h2h.add_hline(y=50, line_dash="dash", line_color="white", opacity=0.5)
                    fig_h2h.update_layout(template="plotly_dark", height=380,
                        yaxis=dict(range=[0,110], title="Win Probability (%)"),
                        xaxis_title="Category", showlegend=False, margin=dict(t=20))
                    st.plotly_chart(fig_h2h, use_container_width=True)

        # ── Tab 5: Season Sim ──────────────────────────────────
        with tab_season:
            st.markdown("### 📅 20-Week Yahoo Fantasy Season Simulator")
            st.caption(
                "Simulates a full 20-week head-to-head 9-category Yahoo fantasy season. "
                "Each week your team's 9-cat stats are drawn from the Monte Carlo distributions "
                "and compared against a randomly generated opponent. Tracks standings, streaks, "
                "and category-level performance week by week."
            )

            ss_col1, ss_col2, ss_col3 = st.columns(3)
            ss_n_seasons  = ss_col1.slider("Seasons to simulate", 100, 2000, 500, 100,
                key="ss_n_seasons", help="More seasons = more stable standings estimates")
            ss_league_sz  = ss_col2.slider("League size", 8, 16, 12, key="ss_league_sz")
            ss_playoff_wk = ss_col3.slider("Playoffs start week", 14, 18, 16, key="ss_playoff_wk",
                help="Regular season ends; top N teams make playoffs")
            ss_playoff_spots = st.slider("Playoff spots", 2, 8, 4, key="ss_playoff_spots")

            run_season_sim = st.button("🏆 Run Season Simulation", type="primary", key="btn_season_sim")

            if run_season_sim:
                np.random.seed(mc_p.get("run_count", 0) + 42)
                N_WEEKS   = 20
                REG_WEEKS = ss_playoff_wk - 1
                N_SIM     = ss_n_seasons
                CATS      = MC_ALL_CATS
                cats_avail_ss = [c for c in CATS if c in team_sims.columns]

                # ── Build weekly distributions from season sims ──
                # Divide season totals by ~26 (weeks a player accumulates over 162 game sched)
                # Rate stats stay as-is (they're per-PA averages, not cumulative)
                RATE_SS = {"AVG", "ERA", "WHIP"}
                COUNT_SCALE = 26  # approx. scoring weeks in a season

                def _weekly_draws(sims_df, n_weeks, n_sim_ss):
                    """Convert season-total sims to week-level distributions."""
                    weekly = {}
                    for cat in cats_avail_ss:
                        season_vals = sims_df[cat].values
                        mu = float(np.median(season_vals))
                        sd = float(np.std(season_vals))
                        if cat in RATE_SS:
                            # Rate stats: weekly noise around season mean
                            wk_mu = mu; wk_sd = sd * 1.4  # more week-to-week variance
                        else:
                            # Counting: divide by weeks, add variance
                            wk_mu = mu / COUNT_SCALE
                            wk_sd = (sd / COUNT_SCALE) * 1.5
                        # Truncate to valid ranges
                        lo = 0.0 if cat not in RATE_SS else (0.5 if cat == "ERA" else 0.6 if cat == "WHIP" else 0.150)
                        hi = wk_mu * 4 + wk_sd * 3  # generous ceiling
                        a_tn = (lo - wk_mu) / max(wk_sd, 1e-6)
                        b_tn = (hi - wk_mu) / max(wk_sd, 1e-6)
                        weekly[cat] = scipy_stats.truncnorm.rvs(
                            a_tn, b_tn, loc=wk_mu, scale=max(wk_sd, 1e-6),
                            size=(n_sim_ss, n_weeks))
                    return weekly  # {cat: array(n_sim, n_weeks)}

                # Opponent pool: generate n_league-1 opponents weekly
                def _opp_weekly(n_opp, n_weeks, n_sim_ss):
                    """Random opponent weekly stats — league-average profile with noise."""
                    opp_weekly = {}
                    for cat in cats_avail_ss:
                        if cat in team_sims.columns:
                            lg_mu = float(np.median(team_sims[cat])) * 0.92  # opps slightly worse on average
                            lg_sd = float(np.std(team_sims[cat]))
                        else:
                            lg_mu, lg_sd = 0.0, 1.0
                        if cat not in RATE_SS:
                            lg_mu /= COUNT_SCALE; lg_sd = lg_sd / COUNT_SCALE * 1.5
                        else:
                            lg_sd *= 1.4
                        lo = 0.0 if cat not in RATE_SS else 0.5
                        hi = lg_mu * 4 + lg_sd * 3
                        a_t = (lo - lg_mu) / max(lg_sd, 1e-6)
                        b_t = (hi - lg_mu) / max(lg_sd, 1e-6)
                        opp_weekly[cat] = scipy_stats.truncnorm.rvs(
                            a_t, b_t, loc=lg_mu, scale=max(lg_sd, 1e-6),
                            size=(n_sim_ss, n_opp, n_weeks))
                    return opp_weekly

                with st.spinner(f"📅 Simulating {N_SIM:,} full seasons × {N_WEEKS} weeks..."):
                    my_weekly  = _weekly_draws(team_sims, N_WEEKS, N_SIM)
                    opp_weekly = _opp_weekly(ss_league_sz - 1, N_WEEKS, N_SIM)

                    # ── Simulate each week of each season ──
                    # Results: (n_sim, n_weeks) arrays of W/L/T and cat wins
                    all_wins   = np.zeros((N_SIM, N_WEEKS), dtype=int)  # matchup wins
                    all_losses = np.zeros((N_SIM, N_WEEKS), dtype=int)
                    all_ties   = np.zeros((N_SIM, N_WEEKS), dtype=int)
                    cat_wins_matrix = np.zeros((N_SIM, N_WEEKS, len(cats_avail_ss)))

                    for wi in range(N_WEEKS):
                        # Pick a random opponent for this week (one of n_opp)
                        opp_idx = np.random.randint(0, ss_league_sz - 1, size=N_SIM)
                        wk_cat_wins = np.zeros(N_SIM)
                        for ci, cat in enumerate(cats_avail_ss):
                            my_val  = my_weekly[cat][:, wi]           # (N_SIM,)
                            opp_val = opp_weekly[cat][np.arange(N_SIM), opp_idx, wi]
                            if cat in MC_LOWER_BETTER:
                                cat_win = (my_val < opp_val).astype(float)
                            else:
                                cat_win = (my_val > opp_val).astype(float)
                            cat_wins_matrix[:, wi, ci] = cat_win
                            wk_cat_wins += cat_win

                        n_cats = len(cats_avail_ss)
                        matchup_win  = (wk_cat_wins > n_cats / 2).astype(int)
                        matchup_loss = (wk_cat_wins < n_cats / 2).astype(int)
                        matchup_tie  = ((wk_cat_wins == n_cats / 2)).astype(int)
                        all_wins[:,wi]   = matchup_win
                        all_losses[:,wi] = matchup_loss
                        all_ties[:,wi]   = matchup_tie

                    # ── Season-level aggregates ──
                    reg_wins   = all_wins[:, :REG_WEEKS].sum(axis=1)    # (N_SIM,)
                    reg_losses = all_losses[:, :REG_WEEKS].sum(axis=1)
                    reg_ties   = all_ties[:, :REG_WEEKS].sum(axis=1)
                    playoff_rate = (reg_wins >= np.percentile(reg_wins, (1 - ss_playoff_spots/ss_league_sz)*100)).mean()

                    # Per-cat win rates
                    cat_win_rates = cat_wins_matrix[:, :REG_WEEKS, :].mean(axis=(0,1))  # per cat

                # ── Display results ──
                st.markdown("---")
                st.markdown("#### 📊 Regular Season Record Distribution")
                rw_p10, rw_med, rw_p90 = int(np.percentile(reg_wins,10)), int(np.median(reg_wins)), int(np.percentile(reg_wins,90))
                rl_p10, rl_med, rl_p90 = int(np.percentile(reg_losses,10)), int(np.median(reg_losses)), int(np.percentile(reg_losses,90))

                sm1, sm2, sm3, sm4, sm5 = st.columns(5)
                sm1.metric("Median Wins",    rw_med)
                sm2.metric("Median Losses",  rl_med)
                sm3.metric("Win Range (P10–P90)", f"{rw_p10}–{rw_p90}")
                sm4.metric("Win %",          f"{(reg_wins/(REG_WEEKS)).mean()*100:.1f}%")
                sm5.metric("Playoff Rate",   f"{playoff_rate*100:.1f}%",
                    help=f"% of simulated seasons where you finish in top {ss_playoff_spots} of {ss_league_sz}")

                # Win distribution histogram
                fig_wins = go.Figure()
                fig_wins.add_trace(go.Histogram(
                    x=reg_wins, nbinsx=REG_WEEKS,
                    marker_color="#4fc3f7", showlegend=False,
                    hovertemplate="Wins: %{x}<br>Count: %{y}<extra></extra>"))
                fig_wins.add_vline(x=rw_med, line_dash="dash", line_color="yellow",
                    annotation_text=f"Median: {rw_med}W", annotation_position="top right")
                fig_wins.add_vrect(x0=rw_p10, x1=rw_p90,
                    fillcolor="rgba(79,195,247,0.08)", line_width=0,
                    annotation_text="P10–P90", annotation_position="top left")
                # Playoff threshold line
                thresh_w = np.percentile(reg_wins, (1 - ss_playoff_spots/ss_league_sz)*100)
                fig_wins.add_vline(x=thresh_w, line_dash="dot", line_color="#21C354",
                    annotation_text=f"~Playoff cutoff ({int(thresh_w)}W)", annotation_position="top left",
                    annotation_font_color="#21C354")
                fig_wins.update_layout(
                    title=f"Wins distribution over {REG_WEEKS}-week regular season",
                    template="plotly_dark", height=300,
                    xaxis_title="Regular Season Wins", yaxis_title="# Simulated Seasons",
                    margin=dict(l=40,r=20,t=50,b=40))
                st.plotly_chart(fig_wins, use_container_width=True)

                st.markdown("---")
                st.markdown("#### 🏅 Category Win Rates (Regular Season)")
                cat_wr_df = pd.DataFrame({
                    "Category": cats_avail_ss,
                    "Win Rate": [round(r*100, 1) for r in cat_win_rates],
                    "Assessment": [
                        "💪 Dominant" if r >= 0.65 else "✅ Solid" if r >= 0.52 else
                        "⚖️ Toss-up" if r >= 0.46 else "⚠️ Weak" if r >= 0.35 else "🚨 Punt"
                        for r in cat_win_rates
                    ]
                }).sort_values("Win Rate", ascending=False)
                def _cwr(val):
                    try:
                        v = float(val)
                        if v >= 65: return "color:#21C354; font-weight:bold"
                        if v >= 52: return "color:#21C354"
                        if v >= 46: return "color:#FFA500"
                        if v >= 35: return "color:#FF4B4B"
                        return "color:#FF4B4B; font-weight:bold"
                    except: return ""
                st.dataframe(
                    cat_wr_df.style.map(_cwr, subset=["Win Rate"]).format({"Win Rate": "{:.1f}%"}),
                    use_container_width=True, hide_index=True)

                # Category win rate bar chart
                fig_catbar = go.Figure(go.Bar(
                    x=cat_wr_df["Category"],
                    y=cat_wr_df["Win Rate"],
                    marker_color=["#21C354" if v >= 52 else "#FF4B4B" if v < 46 else "#FFA500"
                                  for v in cat_wr_df["Win Rate"]],
                    text=[f"{v:.1f}%" for v in cat_wr_df["Win Rate"]],
                    textposition="outside"))
                fig_catbar.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.6,
                    annotation_text="50% baseline")
                fig_catbar.update_layout(
                    template="plotly_dark", height=320,
                    yaxis=dict(range=[0,100], title="Win Rate %"),
                    xaxis_title="Category", showlegend=False, margin=dict(t=20,b=40))
                st.plotly_chart(fig_catbar, use_container_width=True)

                st.markdown("---")
                st.markdown("#### 📆 Week-by-Week Win Probability")
                weekly_win_rates = all_wins.mean(axis=0)  # (N_WEEKS,)
                fig_wk = go.Figure()
                fig_wk.add_trace(go.Scatter(
                    x=list(range(1, N_WEEKS+1)), y=weekly_win_rates*100,
                    mode="lines+markers",
                    line=dict(color="#4fc3f7", width=2),
                    marker=dict(size=7, color=[
                        "#21C354" if v >= 0.55 else "#FF4B4B" if v <= 0.45 else "#FFA500"
                        for v in weekly_win_rates
                    ]),
                    name="Win probability",
                    hovertemplate="Week %{x}<br>Win prob: %{y:.1f}%<extra></extra>"
                ))
                fig_wk.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5,
                    annotation_text="50%")
                if ss_playoff_wk <= N_WEEKS:
                    fig_wk.add_vline(x=ss_playoff_wk, line_dash="dot", line_color="#FFD700",
                        annotation_text="Playoffs", annotation_font_color="#FFD700")
                fig_wk.update_layout(
                    title="Matchup win probability by week (% of simulated seasons you win that week)",
                    template="plotly_dark", height=340,
                    xaxis=dict(title="Week", dtick=1),
                    yaxis=dict(range=[0,100], title="Win Probability %"),
                    margin=dict(l=40,r=20,t=50,b=40))
                st.plotly_chart(fig_wk, use_container_width=True)

                st.markdown("---")
                st.markdown("#### 🧮 Standings Projection")
                st.caption(f"Simulated final regular season records across {N_SIM:,} seasons")
                record_counts = {}
                for w, l in zip(reg_wins, reg_losses):
                    key = f"{int(w)}-{int(l)}"
                    record_counts[key] = record_counts.get(key, 0) + 1
                top_records = sorted(record_counts.items(), key=lambda x: -x[1])[:12]
                rec_df = pd.DataFrame(top_records, columns=["Record", "Frequency"])
                rec_df["Probability"] = (rec_df["Frequency"] / N_SIM * 100).round(1)
                rec_df["Approx Rank"] = rec_df["Record"].apply(
                    lambda r: "🏆 Contender" if int(r.split("-")[0]) >= rw_p90 * 0.9
                              else "✅ Playoff"   if int(r.split("-")[0]) >= thresh_w
                              else "⚠️ Bubble"   if int(r.split("-")[0]) >= thresh_w - 2
                              else "❌ Rebuild")
                st.dataframe(
                    rec_df[["Record","Probability","Approx Rank"]].style
                        .format({"Probability": "{:.1f}%"})
                        .map(lambda v: "color:#21C354; font-weight:bold" if "Contender" in str(v)
                              else "color:#4fc3f7" if "Playoff" in str(v)
                              else "color:#FFA500" if "Bubble" in str(v)
                              else "color:#FF4B4B", subset=["Approx Rank"]),
                    use_container_width=True, hide_index=True)
            else:
                st.info("👆 Configure league settings above and click **🏆 Run Season Simulation**.")
                st.markdown("""
                **How this works:**
                - Your Monte Carlo season projections are broken into weekly scoring segments
                - Each week, your team's 9 categories are sampled from those distributions and compared against a randomly drawn opponent
                - A matchup is won if you win more than 4.5 of the 9 categories that week
                - This repeats across 20 weeks and hundreds of simulated seasons to estimate your true win% and playoff odds
                - The opponent pool uses a slightly weaker-than-average team profile to simulate realistic league competition
                """)

