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
import streamlit.components.v1 as st_components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats as scipy_stats
import json, time, urllib.parse, hashlib

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
            "SV":      np.random.randint(0 if yr==2025 else 0, 8 if yr==2025 else 40, n),
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
    "SV":   [("SV",  1.0,True)],
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
MC_P_CATS       = ["W", "SV", "ERA", "WHIP", "SO"]
MC_ALL_CATS     = MC_H_CATS + MC_P_CATS
MC_LOWER_BETTER = {"ERA", "WHIP"}
MC_COUNT_FLOORS = {"HR": 0, "R": 0, "RBI": 0, "SB": 0, "W": 0, "SV": 0, "SO": 0}
MC_H_STATS      = ["HR","R","RBI","SB","AVG","OBP","SLG","wRC+","xwOBA","Barrel%","Hard%"]
MC_P_STATS      = ["W","SV","ERA","WHIP","SO","K%","xFIP","SIERA","BB%","SwStr%","GB%"]


def _mc_player_dist(name, src_df, stat_cols):
    """Build (mean, std) for each stat, normalising partial seasons to full-season equivalents.

    Role detection:
    - Starter:  avg GS >= 10  → scale to 32 GS / 180 IP
    - Reliever: avg GS <  10  → scale to 70 IP (realistic full-season reliever workload)
      This prevents relievers from being projected as 200-IP starters just because
      they appeared in 60+ games.
    """
    hist = src_df[src_df["Name"] == name].copy()
    if hist.empty:
        return {s: (0.0, 0.0) for s in stat_cols}

    counting = {"HR","R","RBI","SB","W","SV","SO","BB","G","GS","IP","PA"}

    # Determine role from historical data
    full_g, full_gs, full_pa = 162, 32, 650
    is_pitcher = "GS" in src_df.columns

    if is_pitcher:
        avg_gs = hist["GS"].fillna(0).mean() if "GS" in hist.columns else 0
        is_starter = avg_gs >= 10
        full_ip = 180 if is_starter else 70   # starters ~180 IP, relievers ~70 IP
    else:
        is_starter = False
        full_ip = 180

    scaled_rows = []
    for _, row in hist.iterrows():
        row = row.copy()
        g  = row.get("G",  full_g)
        gs = row.get("GS", 0) if is_pitcher else row.get("GS", full_gs)
        pa = row.get("PA", full_pa)
        ip = row.get("IP", full_ip)

        if not is_pitcher:
            # Hitter: scale by PA
            if not pd.isna(pa) and pa > 0:
                scale = full_pa / max(pa, 1)
            elif not pd.isna(g) and g > 0:
                scale = full_g / max(g, 1)
            else:
                scale = 1.0
        elif is_starter:
            # SP: scale by GS if available, else IP
            if not pd.isna(gs) and gs > 0:
                scale = full_gs / max(gs, 1)
            elif not pd.isna(ip) and ip > 0:
                scale = full_ip / max(ip, 1)
            else:
                scale = 1.0
        else:
            # Reliever: always scale by IP to reliever full-season ceiling
            if not pd.isna(ip) and ip > 0:
                scale = full_ip / max(ip, 1)
            elif not pd.isna(g) and g > 0:
                # Approx: relievers average ~1 IP/game
                est_ip = g * 1.0
                scale = full_ip / max(est_ip, 1)
            else:
                scale = 1.0

        scale = min(scale, 3.0)

        # SV is opportunity-based, not IP-based — scale by games appeared (G),
        # targeting a full-season closer workload of ~65 appearances.
        # A closer with 35 SV in 60 G should project ~38 SV (35 * 65/60), not get
        # deflated by the IP scaler which would shrink their saves along with SO/W.
        if is_pitcher and not is_starter and "SV" in stat_cols and "G" in row.index:
            sv_g   = row.get("G", None)
            sv_val = row.get("SV", None)
            full_closer_g = 65
            if sv_val is not None and pd.notna(sv_val) and sv_g is not None and pd.notna(sv_g) and sv_g > 0:
                sv_scale = min(full_closer_g / max(sv_g, 1), 2.0)
            else:
                sv_scale = scale  # fallback to IP scale

        for s in stat_cols:
            if s in counting and s in row.index and pd.notna(row[s]):
                # Use appearance-based scale for SV on relievers, IP-based for everything else
                if s == "SV" and is_pitcher and not is_starter:
                    row[s] = row[s] * sv_scale
                else:
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

    # Hard caps for relievers
    if is_pitcher and not is_starter:
        # SO/W/IP caps prevent IP-scaling inflation
        # SV has its own ceiling — elite closers max out ~45 saves
        RP_CAPS = {"SO": 90, "W": 8, "IP": 75, "SV": 48}
        for s, cap in RP_CAPS.items():
            if s in out:
                mu, sd = out[s]
                out[s] = (min(mu, cap), min(sd, cap * 0.25))

        # SV floor: if player has meaningful save history (avg > 2), preserve it
        # Don't let the IP scaler drag saves down to near-zero for real closers
        if "SV" in out:
            hist_sv = hist["SV"].dropna() if "SV" in hist.columns else pd.Series([], dtype=float)
            if len(hist_sv) > 0 and hist_sv.mean() > 2:
                raw_mu = float(hist_sv.mean())  # unscaled historical average
                scaled_mu = out["SV"][0]
                # Use whichever is higher — raw history or scaled projection
                # (prevents deflation from partial-season scaling)
                best_mu = max(scaled_mu, raw_mu * 0.85)
                out["SV"] = (min(best_mu, 48), out["SV"][1])

    return out


def _mc_apply_sabermetrics(name, dist, src_df, is_hitter, saber_weight, lg_h, lg_p):
    """
    Adjust projected means using sabermetric indicators.
    saber_weight 0.0 = pure counting-stat history, 1.0 = fully sabermetric-adjusted.

    Uses a weighted average of recent seasons (more recent = higher weight) rather
    than just latest season, making adjustments more stable.

    Adjustment magnitudes are calibrated to produce noticeable but realistic shifts:
    - A 2-sigma elite Barrel% player gets +30-35% HR boost at full saber_weight
    - A pitcher with xFIP 1.0 better than ERA gets that ERA corrected ~100% at sw=1.0
    """
    if saber_weight <= 0:
        return dist

    hist = src_df[src_df["Name"] == name].copy()
    if hist.empty:
        return dist

    # Weighted average across seasons — most recent gets highest weight
    hist = hist.sort_values("Season")
    n = len(hist)
    weights = np.array([1.5**i for i in range(n)], dtype=float)
    weights /= weights.sum()

    def _wavg(col):
        """Weighted average of a column across seasons."""
        if col not in hist.columns: return None
        vals = hist[col].values.astype(float)
        mask = ~np.isnan(vals)
        if mask.sum() == 0: return None
        w = weights.copy(); w[~mask] = 0
        if w.sum() == 0: return None
        return float(np.dot(vals * mask, w / w.sum()))

    def _zs(val, mu, sd):
        """Z-score helper."""
        if val is None or mu is None: return 0.0
        if sd and sd > 0: return (val - mu) / sd
        return 0.0

    def _blend(dist, stat, adj_mu, clip_lo=None, clip_hi=None):
        """
        Blend raw projection mean with sabermetric-adjusted mean.
        adj_mu is the fully-adjusted target; saber_weight controls the mix.
        """
        if stat not in dist: return dist
        mu, sd = dist[stat]
        blended = mu * (1 - saber_weight) + adj_mu * saber_weight
        if clip_lo is not None or clip_hi is not None:
            blended = float(np.clip(blended, clip_lo or -np.inf, clip_hi or np.inf))
        dist[stat] = (blended, sd)
        return dist

    if is_hitter:
        # ── HR: Barrel% is the strongest HR predictor ────────
        # A 2-sigma elite Barrel% player (e.g. 16% vs 8% avg) gets +35% HR
        barrel   = _wavg("Barrel%")
        lg_barrel = lg_h.get("Barrel%", 0.08)
        sd_barrel = src_df["Barrel%"].std() if "Barrel%" in src_df else 0.04
        if barrel is not None and "HR" in dist:
            bz     = _zs(barrel, lg_barrel, sd_barrel)
            factor = 1.0 + np.clip(bz * 0.17, -0.35, 0.40)
            mu, sd = dist["HR"]
            dist   = _blend(dist, "HR", mu * factor, clip_lo=0)

        # ── R: wRC+ is the best run-scoring proxy ────────────
        # A 2-sigma elite wRC+ (140 vs 100 avg, sd~20) gets +20% R
        wrcplus  = _wavg("wRC+")
        lg_wrc   = lg_h.get("wRC+", 100)
        sd_wrc   = src_df["wRC+"].std() if "wRC+" in src_df else 20.0
        if wrcplus is not None and "R" in dist:
            wz     = _zs(wrcplus, lg_wrc, sd_wrc)
            factor = 1.0 + np.clip(wz * 0.10, -0.25, 0.30)
            mu, sd = dist["R"]
            dist   = _blend(dist, "R", mu * factor, clip_lo=0)

        # ── RBI: wOBA captures true run production ────────────
        # Also use Hard% as secondary indicator
        woba    = _wavg("wOBA")
        hard    = _wavg("Hard%")
        lg_woba = lg_h.get("wOBA", 0.320)
        sd_woba = src_df["wOBA"].std() if "wOBA" in src_df else 0.040
        if woba is not None and "RBI" in dist:
            wobaz  = _zs(woba, lg_woba, sd_woba)
            hard_z = _zs(hard, lg_h.get("Hard%", 0.37), 0.07) if hard is not None else 0.0
            factor = 1.0 + np.clip(wobaz * 0.10 + hard_z * 0.04, -0.25, 0.30)
            mu, sd = dist["RBI"]
            dist   = _blend(dist, "RBI", mu * factor, clip_lo=0)

        # ── SB: Spd score is the best SB predictor ───────────
        # A 2-sigma speed demon (Spd 8 vs 4.5 avg) gets +40% SB
        spd    = _wavg("Spd")
        lg_spd = lg_h.get("Spd", 4.5)
        sd_spd = src_df["Spd"].std() if "Spd" in src_df else 1.8
        if spd is not None and "SB" in dist:
            sz     = _zs(spd, lg_spd, sd_spd)
            factor = 1.0 + np.clip(sz * 0.18, -0.35, 0.45)
            mu, sd = dist["SB"]
            dist   = _blend(dist, "SB", mu * factor, clip_lo=0)

        # ── AVG: xBA is the primary regressor, xwOBA as secondary
        # If xBA is well below AVG, project regression; if above, upside
        xba  = _wavg("xBA");   avg  = _wavg("AVG")
        xwoba = _wavg("xwOBA"); woba2 = _wavg("wOBA")
        if "AVG" in dist:
            mu_avg, sd_avg = dist["AVG"]
            adj = mu_avg  # start from raw projection
            if xba is not None and avg is not None:
                # Strong regression signal: weight xBA heavily
                xba_gap = xba - avg  # negative = avg is inflated by luck
                adj += xba_gap * 0.55
            if xwoba is not None and woba2 is not None:
                xwoba_gap = xwoba - woba2
                adj += xwoba_gap * 0.20
            dist = _blend(dist, "AVG", float(np.clip(adj, 0.150, 0.400)),
                          clip_lo=0.150, clip_hi=0.400)

    else:  # pitcher
        # ── ERA: blend toward xFIP/SIERA (luck correction) ───
        # xFIP and SIERA strip out HR/BABIP luck — strongly predictive
        # At saber_weight=1.0, ERA fully replaced by xFIP/SIERA blend
        xfip  = _wavg("xFIP"); siera = _wavg("SIERA"); fip = _wavg("FIP")
        if "ERA" in dist:
            mu_era, sd_era = dist["ERA"]
            # Weight: xFIP 40%, SIERA 40%, FIP 20% (if available)
            true_vals = [(xfip, 0.40), (siera, 0.40), (fip, 0.20)]
            avail     = [(v, w) for v, w in true_vals if v is not None]
            if avail:
                tot_w     = sum(w for _, w in avail)
                true_era  = sum(v * w for v, w in avail) / tot_w
                dist      = _blend(dist, "ERA", float(np.clip(true_era, 1.5, 8.0)),
                                   clip_lo=1.5, clip_hi=8.0)

        # ── WHIP: K-BB% and GB% are strong indicators ────────
        kbb   = _wavg("K-BB%"); gb = _wavg("GB%"); bb_pct = _wavg("BB%")
        lg_kbb = lg_p.get("K-BB%", 0.12)
        sd_kbb = src_df["K-BB%"].std() if "K-BB%" in src_df else 0.07
        if "WHIP" in dist:
            mu_whip, sd_whip = dist["WHIP"]
            adj_whip = mu_whip
            if kbb is not None:
                kbbz      = _zs(kbb, lg_kbb, sd_kbb)
                adj_whip += np.clip(-kbbz * 0.07, -0.18, 0.18)  # high K-BB% → lower WHIP
            if gb is not None:
                # GB pitchers suppress hard contact → lower WHIP
                adj_whip += np.clip(-(gb - 0.44) * 0.25, -0.08, 0.08)
            if bb_pct is not None:
                lg_bb = lg_p.get("BB%", 0.085)
                sd_bb = src_df["BB%"].std() if "BB%" in src_df else 0.025
                bbz   = _zs(bb_pct, lg_bb, sd_bb)
                adj_whip += np.clip(bbz * 0.05, -0.10, 0.10)  # high BB% → higher WHIP
            dist = _blend(dist, "WHIP", float(np.clip(adj_whip, 0.80, 2.20)),
                          clip_lo=0.80, clip_hi=2.20)

        # ── SO: SwStr% and K% are the best strikeout predictors
        swstr = _wavg("SwStr%"); kpct = _wavg("K%")
        lg_sw = lg_p.get("SwStr%", 0.115); sd_sw = src_df["SwStr%"].std() if "SwStr%" in src_df else 0.025
        lg_k  = lg_p.get("K%",    0.220);  sd_k  = src_df["K%"].std()    if "K%"    in src_df else 0.050
        if "SO" in dist:
            mu_so, sd_so = dist["SO"]
            factor = 1.0
            if swstr is not None:
                swz     = _zs(swstr, lg_sw, sd_sw)
                factor += np.clip(swz * 0.12, -0.25, 0.30)   # SwStr% very predictive
            if kpct is not None:
                kz      = _zs(kpct, lg_k, sd_k)
                factor += np.clip(kz * 0.08, -0.20, 0.25)    # K% also predictive
            factor = np.clip(factor, 0.50, 1.80)
            dist   = _blend(dist, "SO", mu_so * factor, clip_lo=0)

        # ── W: K/9, GB%, and ERA-xFIP gap all inform sustainability
        k9  = _wavg("K/9"); csw = _wavg("CSW%")
        lg_k9 = lg_p.get("K/9", 8.5); sd_k9 = src_df["K/9"].std() if "K/9" in src_df else 2.0
        if "W" in dist:
            mu_w, sd_w = dist["W"]
            factor = 1.0
            if k9 is not None:
                k9z     = _zs(k9, lg_k9, sd_k9)
                factor += np.clip(k9z * 0.06, -0.12, 0.15)
            if gb is not None:
                factor += np.clip((gb - 0.44) * 0.15, -0.06, 0.08)
            if csw is not None:
                csw_z   = _zs(csw, lg_p.get("CSW%", 0.30), 0.03)
                factor += np.clip(csw_z * 0.04, -0.08, 0.10)
            factor = np.clip(factor, 0.70, 1.40)
            dist   = _blend(dist, "W", mu_w * factor, clip_lo=0)

        # ── SV: CSW% and K% indicate closer dominance / leverage
        # High CSW% / K% closers earn and keep save opportunities
        if "SV" in dist:
            mu_sv, sd_sv = dist["SV"]
            if mu_sv > 3:   # only apply to actual closers
                factor = 1.0
                if csw is not None:
                    csw_z   = _zs(csw, lg_p.get("CSW%", 0.30), 0.03)
                    factor += np.clip(csw_z * 0.10, -0.18, 0.20)
                if kpct is not None:
                    kz      = _zs(kpct, lg_k, sd_k)
                    factor += np.clip(kz * 0.06, -0.12, 0.15)
                factor = np.clip(factor, 0.70, 1.40)
                dist   = _blend(dist, "SV", mu_sv * factor, clip_lo=0)

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
        "SV":      (0,     60),
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
        sims = apply_injury(sims, ["W", "SV", "SO"], injury_pct)
        player_sims[name] = sims
        for s in ["W", "SV", "SO"]:
            if s in sims.columns: sim_p[s] += sims[s].values
        for s in ["ERA", "WHIP"]:
            if s in sims.columns: sim_p[s] += sims[s].values

    n_p = max(len(pitchers), 1); sim_p["ERA"] /= n_p; sim_p["WHIP"] /= n_p
    team_df = pd.DataFrame({
        "HR": sim_h["HR"], "R": sim_h["R"], "RBI": sim_h["RBI"],
        "SB": sim_h["SB"], "AVG": sim_h["AVG"],
        "W": sim_p["W"], "SV": sim_p["SV"], "ERA": sim_p["ERA"], "WHIP": sim_p["WHIP"], "SO": sim_p["SO"],
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
    "🎲 Monte Carlo Sim",
    "🏆 My Yahoo League",
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
    ptype = st.radio("Player type", ["Hitters","Pitchers"], horizontal=True, label_visibility="collapsed")
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
        show = ["Name","Team","composite","W","SV","ERA","WHIP","SO",
                "xFIP","SIERA","K%","SwStr%","LOB%","z_W","z_SV","z_ERA","z_WHIP","z_K"]
    show = [c for c in show if c in df.columns]
    z_present = [c for c in show if c.startswith("z_")]
    styled = (
        df[show].style
        .map(style_z,        subset=z_present)
        .background_gradient(subset=["composite"], cmap="RdYlGn")
        .format({c: "{:.2f}" for c in ["composite"] + z_present})
    )
    st.dataframe(styled, width="stretch", height=560)
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
    ptype  = st.radio("Player type", ["Hitter","Pitcher"], horizontal=True, label_visibility="collapsed")
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
        key = ["W","SV","ERA","WHIP","SO","K%","xFIP","SIERA","SwStr%","BB%","LOB%","GB%","CSW%"]
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
                "Floor (P10)": round(p10, 3 if cat == "AVG" else 2),
                "P25":         round(p25, 3 if cat == "AVG" else 2),
                "Median":      round(p50, 3 if cat == "AVG" else 2),
                "P75":         round(p75, 3 if cat == "AVG" else 2),
                "Ceiling (P90)":round(p90, 3 if cat == "AVG" else 2),
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
            def _clean_num(val):
                try:
                    v = float(val)
                    if v != v: return val  # NaN
                    if v == int(v): return str(int(v))
                    s = f"{v:.3f}".rstrip("0").rstrip(".")
                    return s
                except: return val
            num_cols = [c for c in ["Floor (P10)","P25","Median","P75","Ceiling (P90)"] if c in proj_df.columns]
            fmt_map = {c: _clean_num for c in num_cols}
            fmt_map["Volatility (CV%)"] = "{:.1f}%"
            st.dataframe(
                proj_df.style
                    .map(_dir_color, subset=["Direction"])
                    .map(_cv_color,  subset=["Volatility (CV%)"])
                    .format(fmt_map),
                use_container_width=True, hide_index=True)
            st.caption("**CV%** = volatility. Green < 25% = consistent. Orange 25–40% = variable. Red > 40% = highly unpredictable.")

        st.markdown("---")

        # ── Narrative summary ─────────────────────────────
        st.markdown("#### 🗒️ Projection Summary")
        if proj_rows:
            summary_parts = []
            for row in proj_rows:
                cat   = row["Category"]
                med   = row["Median"]
                p10   = row["Floor (P10)"]
                p90   = row["Ceiling (P90)"]
                cv    = row["Volatility (CV%)"]
                lower = cat in MC_LOWER_BETTER
                vol   = "highly volatile" if cv > 40 else "variable" if cv > 25 else "consistent"
                tier  = ""
                if not lower:
                    if cat == "AVG":
                        tier = "elite" if med >= 0.290 else "above avg" if med >= 0.270 else "avg" if med >= 0.250 else "below avg"
                    elif cat == "HR":
                        tier = "elite" if med >= 35 else "above avg" if med >= 25 else "avg" if med >= 15 else "below avg"
                    elif cat == "SB":
                        tier = "elite" if med >= 30 else "above avg" if med >= 18 else "avg" if med >= 8 else "below avg"
                    elif cat in ("R","RBI"):
                        tier = "elite" if med >= 100 else "above avg" if med >= 80 else "avg" if med >= 60 else "below avg"
                    elif cat == "W":
                        tier = "elite" if med >= 16 else "above avg" if med >= 12 else "avg" if med >= 8 else "below avg"
                    elif cat == "SO":
                        tier = "elite" if med >= 220 else "above avg" if med >= 170 else "avg" if med >= 120 else "below avg"
                else:
                    if cat == "ERA":
                        tier = "elite" if med <= 2.80 else "above avg" if med <= 3.50 else "avg" if med <= 4.20 else "below avg"
                    elif cat == "WHIP":
                        tier = "elite" if med <= 1.00 else "above avg" if med <= 1.18 else "avg" if med <= 1.30 else "below avg"
                fmt    = f"{med:.3f}" if cat=="AVG" else f"{med:.2f}" if cat in ("ERA","WHIP") else str(int(round(med)))
                pfmt10 = f"{p10:.3f}" if cat=="AVG" else f"{p10:.2f}" if cat in ("ERA","WHIP") else str(int(round(p10)))
                pfmt90 = f"{p90:.3f}" if cat=="AVG" else f"{p90:.2f}" if cat in ("ERA","WHIP") else str(int(round(p90)))
                tier_color = {"elite":"🟢","above avg":"🔵","avg":"🟡","below avg":"🔴"}.get(tier,"⚪")
                summary_parts.append(
                    f"{tier_color} **{cat}**: {tier} ({fmt})  ·  range {pfmt10}–{pfmt90}  ·  {vol}"
                )
            for line in summary_parts:
                st.markdown(line)

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
            if cat == "AVG":
                return round(float(val), 3)
            return round(float(val), 2)

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

        # ── Player Compare ────────────────────────────────
        st.markdown("#### ⚖️ Compare vs. Another Player")
        st.caption("Run MC projections for a second player and compare side by side.")

        compare_pool = sorted(bat_all["Name"].dropna().unique()) if is_hitter_dive else sorted(pit_all["Name"].dropna().unique())
        compare_pool = [n for n in compare_pool if n != name]
        cmp_name = st.selectbox("Select player to compare", ["— select —"] + compare_pool, key="dive_cmp_name")

        if cmp_name and cmp_name != "— select —":
            run_cmp = st.button(f"⚖️ Compare {name} vs {cmp_name}", key="dive_cmp_run")
            cmp_key = f"dive_cmp_{name}_vs_{cmp_name}"

            if run_cmp:
                rc_cmp = st.session_state.get("mc_run_count", 0) + 999
                with st.spinner(f"Simulating {cmp_name}..."):
                    if is_hitter_dive:
                        cmp_sims, _ = mc_run_simulation(
                            hitters=(cmp_name,), pitchers=(),
                            n_sim=dive_data["n_sim"], injury_pct=dive_data["inj"]/100,
                            regression_pull=dive_data["regr"], platoon_boost=False,
                            saber_weight=dive_data["saber"], run_count=rc_cmp)
                    else:
                        cmp_sims, _ = mc_run_simulation(
                            hitters=(), pitchers=(cmp_name,),
                            n_sim=dive_data["n_sim"], injury_pct=dive_data["inj"]/100,
                            regression_pull=dive_data["regr"], platoon_boost=False,
                            saber_weight=dive_data["saber"], run_count=rc_cmp)
                st.session_state[cmp_key] = cmp_sims

            cmp_data = st.session_state.get(cmp_key)
            if cmp_data is not None:
                cmp_rows = []
                for cat in cats_avail:
                    if cat not in tsims.columns or cat not in cmp_data.columns: continue
                    my_v   = tsims[cat].dropna().values
                    cmp_v  = cmp_data[cat].dropna().values
                    my_med  = float(np.median(my_v))
                    cmp_med = float(np.median(cmp_v))
                    my_p10  = float(np.percentile(my_v, 10))
                    my_p90  = float(np.percentile(my_v, 90))
                    cmp_p10 = float(np.percentile(cmp_v, 10))
                    cmp_p90 = float(np.percentile(cmp_v, 90))
                    n       = min(len(my_v), len(cmp_v))
                    if cat in MC_LOWER_BETTER:
                        h2h_win = float(np.mean(my_v[:n] < cmp_v[:n])) * 100
                        edge    = cmp_med - my_med   # positive = I'm better (lower)
                    else:
                        h2h_win = float(np.mean(my_v[:n] > cmp_v[:n])) * 100
                        edge    = my_med - cmp_med   # positive = I'm better (higher)
                    fmt = lambda v: f"{v:.3f}" if cat=="AVG" else f"{v:.2f}" if cat in ("ERA","WHIP") else str(int(round(v)))
                    advantage = f"✅ {name}" if edge > 0 else f"🔴 {cmp_name}" if edge < 0 else "⚖️ Even"
                    cmp_rows.append({
                        "Category":          cat,
                        f"{name} Median":    fmt(my_med),
                        f"{name} Range":     f"{fmt(my_p10)}–{fmt(my_p90)}",
                        f"{cmp_name} Median":fmt(cmp_med),
                        f"{cmp_name} Range": f"{fmt(cmp_p10)}–{fmt(cmp_p90)}",
                        "H2H Win %":         round(h2h_win, 1),
                        "Advantage":         advantage,
                    })

                cmp_df = pd.DataFrame(cmp_rows)

                def _adv_color(val):
                    if name in str(val) and "✅" in str(val): return "color:#21C354; font-weight:bold"
                    if "🔴" in str(val): return "color:#FF4B4B; font-weight:bold"
                    return "color:#FFA500"

                def _h2h_color(val):
                    try:
                        v = float(val)
                        if v >= 60: return "color:#21C354; font-weight:bold"
                        if v >= 50: return "color:#21C354"
                        if v >= 40: return "color:#FFA500"
                        return "color:#FF4B4B"
                    except: return ""

                st.dataframe(
                    cmp_df.style
                        .map(_adv_color, subset=["Advantage"])
                        .map(_h2h_color, subset=["H2H Win %"])
                        .format({"H2H Win %": "{:.1f}%"}),
                    use_container_width=True, hide_index=True)

                # Overlay distribution chart for most impacted category
                best_cat = cmp_df.reindex(
                    (cmp_df["H2H Win %"] - 50).abs().sort_values(ascending=False).index
                ).iloc[0]["Category"]
                st.markdown(f"**Distribution overlay — {best_cat}** (most differentiated category)")
                fig_ov = go.Figure()
                fig_ov.add_trace(go.Histogram(
                    x=tsims[best_cat].values, nbinsx=40, name=name,
                    opacity=0.65, marker_color="#4fc3f7"))
                fig_ov.add_trace(go.Histogram(
                    x=cmp_data[best_cat].values, nbinsx=40, name=cmp_name,
                    opacity=0.65, marker_color="#FF7043"))
                fig_ov.update_layout(
                    barmode="overlay", template="plotly_dark", height=280,
                    legend=dict(orientation="h", y=1.1),
                    xaxis_title=best_cat, margin=dict(l=20,r=20,t=10,b=40))
                st.plotly_chart(fig_ov, use_container_width=True)

                # Summary verdict
                my_wins   = sum(1 for r in cmp_rows if name in r["Advantage"] and "✅" in r["Advantage"])
                cmp_wins  = sum(1 for r in cmp_rows if cmp_name in r["Advantage"] and "🔴" in r["Advantage"])
                verdict_color = "#21C354" if my_wins > cmp_wins else "#FF4B4B" if cmp_wins > my_wins else "#FFA500"
                verdict_text  = (f"✅ {name} wins {my_wins}/{len(cmp_rows)} categories"
                                 if my_wins > cmp_wins else
                                 f"🔴 {cmp_name} wins {cmp_wins}/{len(cmp_rows)} categories"
                                 if cmp_wins > my_wins else
                                 f"⚖️ Even split ({my_wins}/{len(cmp_rows)} each)")
                st.markdown(f"<h4 style='color:{verdict_color};text-align:center'>{verdict_text}</h4>",
                    unsafe_allow_html=True)

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
            zcats, labels = ["z_W","z_SV","z_ERA","z_WHIP","z_K"], ["W","SV","ERA","WHIP","K"]
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
        rows.append({"Category":cat, "Type":"Pitching" if cat in ["W","SV","ERA","WHIP","K"] else "Hitting",
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

    # ── ADP loader (Yahoo API if connected, else None) ────────
    yahoo_connected = st.session_state.get("yahoo_token") is not None
    league_key_adp  = st.session_state.get("yahoo_league_key")

    @st.cache_data(ttl=1800, show_spinner=False)
    def _fetch_adp_batch(league_key: str, access_token: str,
                         player_keys: tuple) -> dict:
        """
        Fetch draft_analysis (ADP) for up to 25 players at a time.
        Returns {player_key: {average_pick, average_round, percent_drafted}}
        """
        import requests
        results = {}
        batch_size = 25
        keys_list  = list(player_keys)
        for i in range(0, len(keys_list), batch_size):
            batch = keys_list[i:i+batch_size]
            keys_str = ",".join(batch)
            url = (f"https://fantasysports.yahooapis.com/fantasy/v2"
                   f"/league/{league_key}/players;player_keys={keys_str}"
                   f"/draft_analysis?format=json")
            try:
                r = requests.get(url,
                    headers={"Authorization": f"Bearer {access_token}",
                             "Accept": "application/json"},
                    timeout=15)
                if r.status_code != 200:
                    continue
                data = r.json()
                players = data["fantasy_content"]["league"][1]["players"]
                for k, v in players.items():
                    if k == "count": continue
                    p      = v["player"]
                    p_info = p[0]
                    da     = p[1].get("draft_analysis", {}) if len(p) > 1 else {}
                    name   = next((x["name"]["full"] for x in p_info
                                   if isinstance(x,dict) and "name" in x), None)
                    if name and da:
                        results[name] = {
                            "adp":     float(da.get("average_pick",  999) or 999),
                            "adp_rnd": float(da.get("average_round", 99)  or 99),
                            "pct_own": float(da.get("percent_drafted", 0) or 0),
                        }
            except Exception:
                continue
        return results

    # Cache ADP data in session state to avoid re-fetching on every widget change
    if "adp_cache_h" not in st.session_state:
        st.session_state["adp_cache_h"] = {}   # hitters only
    if "adp_cache_p" not in st.session_state:
        st.session_state["adp_cache_p"] = {}   # pitchers only

    def _get_adp(name: str, is_hitter: bool = True) -> dict:
        """Return ADP dict for a player name from the correct typed cache."""
        cache = st.session_state["adp_cache_h"] if is_hitter else st.session_state["adp_cache_p"]
        return cache.get(name, {})

    def _adp_cache_combined():
        """Combined cache for backward compat (target list, etc.)."""
        combined = {}
        combined.update(st.session_state["adp_cache_h"])
        combined.update(st.session_state["adp_cache_p"])
        return combined

    def _adp_label(adp_val: float) -> str:
        if adp_val >= 999: return "—"
        return f"{adp_val:.1f}"

    def _value_label(z: float, adp: float, league_sz: int = 12) -> str:
        """Compare z-score rank to ADP. Returns value/reach label."""
        if adp >= 999: return "—"
        # Convert z to rough rank among all players
        z_rank_h = int(bat_rec["composite"].rank(ascending=False).get(
            bat_rec[bat_rec["composite"] == z].index[0] if len(bat_rec[bat_rec["composite"]==z])>0 else -1, 999))
        gap = adp - z_rank_h if z_rank_h < 999 else 0
        if   gap >= 20: return "🔥 Big Value"
        elif gap >= 10: return "✅ Value"
        elif gap >= -5: return "➡️ Fair"
        elif gap >= -15: return "⚠️ Slight Reach"
        else: return "🚨 Reach"

    tab_adp, tab_strat, tab_targets, tab_compare, tab_grade = st.tabs([
        "🏟️ Draft Room",
        "🗺️ Draft Strategy Planner",
        "⭐ My Target List",
        "📊 Compare Targets",
        "🎓 Draft Grade",
    ])

    # ══════════════════════════════════════════════════════════
    #  TAB 1 — DRAFT ROOM (ADP + Live Draft Board)
    # ══════════════════════════════════════════════════════════
    with tab_adp:
        st.markdown("### 🏟️ Draft Room")
        st.caption(
            "Live draft board with Yahoo ADP. Mark players as drafted by you or others. "
            "All players shown with ADP gap — positive = value pick, negative = reach."
        )

        # Init draft state
        if "drafted_h"  not in st.session_state: st.session_state["drafted_h"]  = set()
        if "drafted_p"  not in st.session_state: st.session_state["drafted_p"]  = set()
        if "my_h"       not in st.session_state: st.session_state["my_h"]       = []
        if "my_p"       not in st.session_state: st.session_state["my_p"]       = []

        # ── Controls ──────────────────────────────────────────
        dr_c1, dr_c2, dr_c3, dr_c4 = st.columns(4)
        dr_ptype   = dr_c1.radio("Players", ["Hitters","Pitchers"], horizontal=True,
                                  key="dr_ptype", label_visibility="collapsed")
        dr_filter  = dr_c2.selectbox("Show", ["All players","Available only",
                                               "My picks","Has ADP"],
                                     key="dr_filter")
        dr_sort    = dr_c3.selectbox("Sort by", ["ADP","Z-Score","Name"],
                                     key="dr_sort")
        dr_search  = dr_c4.text_input("🔍 Search player", key="dr_search",
                                      placeholder="Filter by name...")

        src_df_dr = bat_rec.copy() if dr_ptype == "Hitters" else pit_rec.copy()
        drafted_set = st.session_state["drafted_h"] if dr_ptype == "Hitters" else st.session_state["drafted_p"]
        my_set      = set(st.session_state["my_h"] if dr_ptype == "Hitters" else st.session_state["my_p"])

        # ── Yahoo ADP status ──────────────────────────────────
        adp_loaded_dr = len(st.session_state.get("adp_cache_h",{})) + len(st.session_state.get("adp_cache_p",{}))
        if not yahoo_connected:
            st.warning("⚠️ Connect Yahoo (🏆 My Yahoo League) to load live ADP.")
            load_adp_dr = False
        elif not league_key_adp:
            st.warning("⚠️ Select your league on the 🏆 My Yahoo League page first.")
            load_adp_dr = False
        else:
            adc1, adc2 = st.columns([2,4])
            load_adp_dr = adc1.button(
                f"🔄 {'Reload' if adp_loaded_dr else 'Load'} Yahoo ADP",
                key="btn_load_adp_dr",
                type="primary" if not adp_loaded_dr else "secondary"
            )
            if adp_loaded_dr:
                adc2.success(f"✅ ADP loaded for {adp_loaded_dr} players")
            else:
                adc2.info("👆 Load ADP to see value gaps")

        if yahoo_connected and league_key_adp and load_adp_dr:
            access_token_dr = st.session_state["yahoo_token"]["access_token"]
            import requests as _rdr

            def _safe_float_dr(val, default):
                try: return float(val) if val not in (None,"","—") else default
                except: return default

            def _extract_da_dr(obj):
                if isinstance(obj, dict):
                    if "average_pick" in obj: return obj
                    if "draft_analysis" in obj: return _extract_da_dr(obj["draft_analysis"])
                    for v in obj.values():
                        found = _extract_da_dr(v)
                        if found: return found
                elif isinstance(obj, list):
                    for item in obj:
                        found = _extract_da_dr(item)
                        if found: return found
                return {}

            headers_dr = {"Authorization": f"Bearer {access_token_dr}",
                          "Accept": "application/json"}
            prog = st.progress(0, text="Fetching ADP...")
            total_loaded_dr = 0

            for pos_type, label in [("B","hitters"),("P","pitchers")]:
                for start_idx in range(0, 500, 25):  # up to 500 each
                    url_dr = (
                        f"https://fantasysports.yahooapis.com/fantasy/v2"
                        f"/league/{league_key_adp}/players"
                        f";position={pos_type};sort=AR"
                        f";start={start_idx};count=25"
                        f";out=draft_analysis?format=json"
                    )
                    try:
                        r_dr = _rdr.get(url_dr, headers=headers_dr, timeout=20)
                        if r_dr.status_code != 200: break
                        items_dr = r_dr.json()["fantasy_content"]["league"][1]["players"]
                        batch_count = 0
                        for k_dr, v_dr in items_dr.items():
                            if k_dr == "count": continue
                            p_dr = v_dr["player"]
                            p0_dr = p_dr[0]
                            name_dr = next((x["name"]["full"] for x in p0_dr
                                            if isinstance(x,dict) and "name" in x), None)
                            if not name_dr: continue
                            da_dr = _extract_da_dr(p_dr[1:])
                            entry_dr = {
                                "adp":     _safe_float_dr(da_dr.get("average_pick"),  999),
                                "adp_rnd": _safe_float_dr(da_dr.get("average_round"), 99),
                                "pct_own": _safe_float_dr(da_dr.get("percent_drafted"),0),
                            }
                            if pos_type == "B":
                                st.session_state["adp_cache_h"][name_dr] = entry_dr
                            else:
                                st.session_state["adp_cache_p"][name_dr] = entry_dr
                            batch_count += 1
                            total_loaded_dr += 1
                        if batch_count < 25: break
                    except Exception: break
                    pct = min(0.99, (start_idx+25)/500*0.5 + (0.5 if pos_type=="P" else 0))
                    prog.progress(pct, text=f"Loading {label}... ({total_loaded_dr})")
            prog.empty()
            if total_loaded_dr:
                st.success(f"✅ Loaded ADP for {total_loaded_dr} players")
                st.rerun()
            else:
                st.warning("No ADP data returned from Yahoo. Draft may not have occurred yet.")
                with st.expander("🔍 Debug: raw API response"):
                    try:
                        dbg = _rdr.get(
                            f"https://fantasysports.yahooapis.com/fantasy/v2"
                            f"/league/{league_key_adp}/players"
                            f";position=B;sort=AR;start=0;count=3"
                            f";out=draft_analysis?format=json",
                            headers=headers_dr, timeout=10)
                        st.json(dbg.json() if dbg.status_code==200
                                else {"error": dbg.status_code, "body": dbg.text[:500]})
                    except Exception as de:
                        st.caption(f"Debug failed: {de}")

        # ── Build board from Yahoo ADP (primary source) ──────
        # Yahoo ADP is the single source of truth for player rankings.
        # FanGraphs stats are shown as supplementary context only.
        adp_cache = (st.session_state.get("adp_cache_h", {})
                     if dr_ptype == "Hitters"
                     else st.session_state.get("adp_cache_p", {}))
        rows_dr = []

        if adp_cache:
            for yahoo_name, adp_d in adp_cache.items():
                adp = adp_d.get("adp", 999)
                pct = adp_d.get("pct_own", 0)
                is_mine    = yahoo_name in my_set
                is_drafted = yahoo_name in drafted_set and not is_mine
                status = ("✅ My Pick" if is_mine else
                          "❌ Drafted" if is_drafted else "🟢 Available")
                # Supplement with FanGraphs stats (best effort, no penalty if missing)
                is_hit   = dr_ptype == "Hitters"
                stat_df  = bat_rec if is_hit else pit_rec
                stat_row = stat_df[stat_df["Name"] == yahoo_name]
                z = float(stat_row.iloc[0].get("composite",0)) if not stat_row.empty else 0.0
                r = {
                    "Status":  status,
                    "Name":    yahoo_name,
                    "ADP":     round(adp, 1) if adp < 999 else None,
                    "Z-Score": round(z, 2),
                    "%Owned":  f"{pct*100:.0f}%" if pct > 0.001 else "—",
                }
                if is_hit:
                    for col, fmt in [("HR",int),("R",int),("RBI",int),("SB",int)]:
                        r[col] = fmt(stat_row.iloc[0][col]) if not stat_row.empty and pd.notna(stat_row.iloc[0].get(col)) else ""
                    r["AVG"] = round(float(stat_row.iloc[0]["AVG"]),3) if not stat_row.empty and pd.notna(stat_row.iloc[0].get("AVG")) else ""
                else:
                    for col, fmt in [("W",int),("SV",int),("SO",int)]:
                        r[col] = fmt(stat_row.iloc[0][col]) if not stat_row.empty and pd.notna(stat_row.iloc[0].get(col)) else ""
                    r["ERA"]  = round(float(stat_row.iloc[0]["ERA"]),2)  if not stat_row.empty and pd.notna(stat_row.iloc[0].get("ERA"))  else ""
                    r["WHIP"] = round(float(stat_row.iloc[0]["WHIP"]),3) if not stat_row.empty and pd.notna(stat_row.iloc[0].get("WHIP")) else ""
                rows_dr.append(r)
        else:
            # No ADP loaded — show FanGraphs data without ADP column
            for _, row in src_df_dr.iterrows():
                name = row.get("Name","")
                is_mine    = name in my_set
                is_drafted = name in drafted_set and not is_mine
                status = ("✅ My Pick" if is_mine else
                          "❌ Drafted" if is_drafted else "🟢 Available")
                r = {"Status": status, "Name": name, "ADP": None,
                     "Z-Score": round(float(row.get("composite",0)),2), "%Owned": "—"}
                if dr_ptype == "Hitters":
                    for col, fmt in [("HR",int),("R",int),("RBI",int),("SB",int)]:
                        r[col] = fmt(row[col]) if pd.notna(row.get(col)) else ""
                    r["AVG"] = round(float(row["AVG"]),3) if pd.notna(row.get("AVG")) else ""
                else:
                    for col, fmt in [("W",int),("SV",int),("SO",int)]:
                        r[col] = fmt(row[col]) if pd.notna(row.get(col)) else ""
                    r["ERA"]  = round(float(row["ERA"]),2)  if pd.notna(row.get("ERA"))  else ""
                    r["WHIP"] = round(float(row["WHIP"]),3) if pd.notna(row.get("WHIP")) else ""
                rows_dr.append(r)

        bdf = pd.DataFrame(rows_dr)

        # Apply search
        if dr_search:
            bdf = bdf[bdf["Name"].str.contains(dr_search, case=False, na=False)]

        # Apply filter
        if dr_filter == "Available only":
            bdf = bdf[bdf["Status"] == "🟢 Available"]
        elif dr_filter == "My picks":
            bdf = bdf[bdf["Status"] == "✅ My Pick"]
        elif dr_filter == "Has ADP":
            bdf = bdf[bdf["ADP"].notna()]

        # Sort
        if dr_sort == "ADP":
            bdf["_adp_sort"] = bdf["ADP"].apply(
                lambda x: float(x) if x is not None and x == x else 9999)
            bdf = bdf.sort_values("_adp_sort").drop(columns=["_adp_sort"])
        elif dr_sort == "Z-Score":
            bdf = bdf.sort_values("Z-Score", ascending=False)
        elif dr_sort == "Name":
            bdf = bdf.sort_values("Name")

        # Counters
        n_avail   = (bdf["Status"] == "🟢 Available").sum()
        n_drafted = (bdf["Status"] == "❌ Drafted").sum()
        n_mine    = (bdf["Status"] == "✅ My Pick").sum()
        ct1, ct2, ct3 = st.columns(3)
        ct1.metric("Available",  n_avail)
        ct2.metric("Drafted (others)", n_drafted)
        ct3.metric("My Picks",   n_mine)

        # Color functions
        def _status_color(val):
            if "My Pick" in str(val):  return "color:#4fc3f7;font-weight:bold"
            if "Drafted" in str(val):  return "color:#888;text-decoration:line-through"
            return "color:#21C354"

        def _val_color_dr(val):
            v = str(val)
            if "Big Value" in v:  return "color:#21C354;font-weight:bold"
            if "Value"     in v:  return "color:#21C354"
            if "Fair"      in v:  return "color:#888"
            if "Big Reach" in v:  return "color:#FF4B4B;font-weight:bold"
            if "Reach"     in v:  return "color:#FFA500"
            return "color:#aaa"

        def _gap_color_dr(val):
            try:
                v = float(str(val).replace("+",""))
                if v >= 25:  return "color:#21C354;font-weight:bold"
                if v >= 12:  return "color:#21C354"
                if v >= -8:  return "color:#888"
                if v >= -20: return "color:#FFA500"
                return "color:#FF4B4B"
            except: return ""

        # Convert mixed-type columns to proper types before styling
        # ADP is float or None — fill None with NaN so pandas handles it cleanly
        if "ADP" in bdf.columns:
            bdf["ADP"] = pd.to_numeric(bdf["ADP"], errors="coerce")
        for col in ["AVG", "ERA", "WHIP", "Z-Score"]:
            if col in bdf.columns:
                bdf[col] = pd.to_numeric(bdf[col], errors="coerce")
        for col in ["HR","R","RBI","SB","W","SV","SO"]:
            if col in bdf.columns:
                bdf[col] = pd.to_numeric(bdf[col], errors="coerce")

        fmt_cols = {"Z-Score": "{:.2f}"}
        if "ADP"  in bdf.columns: fmt_cols["ADP"]  = "{:.1f}"
        if "AVG"  in bdf.columns: fmt_cols["AVG"]  = "{:.3f}"
        if "ERA"  in bdf.columns: fmt_cols["ERA"]  = "{:.2f}"
        if "WHIP" in bdf.columns: fmt_cols["WHIP"] = "{:.3f}"

        styled = bdf.style.map(_status_color, subset=["Status"])
        styled = styled.format(fmt_cols, na_rep="—")
        st.dataframe(styled, use_container_width=True, hide_index=True, height=480)

        # ── Mark drafted ──────────────────────────────────────
        st.markdown("---")
        st.markdown("#### ✏️ Mark a Player")
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        # Use Yahoo names from the correct typed cache
        if adp_cache:
            all_names_dr = sorted(adp_cache.keys())
        else:
            all_names_dr = src_df_dr["Name"].tolist()
        pick_dr = mc1.selectbox("Select player",
                                [""] + [n for n in all_names_dr if n not in drafted_set],
                                key="sel_dr")
        if mc2.button("✅ My pick", key="btn_my_dr") and pick_dr:
            if dr_ptype == "Hitters":
                st.session_state["drafted_h"].add(pick_dr)
                if pick_dr not in st.session_state["my_h"]:
                    st.session_state["my_h"].append(pick_dr)
            else:
                st.session_state["drafted_p"].add(pick_dr)
                if pick_dr not in st.session_state["my_p"]:
                    st.session_state["my_p"].append(pick_dr)
            st.rerun()
        if mc3.button("❌ Drafted (not me)", key="btn_skip_dr") and pick_dr:
            if dr_ptype == "Hitters":
                st.session_state["drafted_h"].add(pick_dr)
            else:
                st.session_state["drafted_p"].add(pick_dr)
            st.rerun()
        if mc4.button("↩️ Undo last", key="btn_undo_dr"):
            if dr_ptype == "Hitters" and st.session_state["drafted_h"]:
                last = list(st.session_state["drafted_h"])[-1]
                st.session_state["drafted_h"].discard(last)
                if last in st.session_state["my_h"]:
                    st.session_state["my_h"].remove(last)
            elif dr_ptype == "Pitchers" and st.session_state["drafted_p"]:
                last = list(st.session_state["drafted_p"])[-1]
                st.session_state["drafted_p"].discard(last)
                if last in st.session_state["my_p"]:
                    st.session_state["my_p"].remove(last)
            st.rerun()
        if mc5.button("🔄 Reset all", key="btn_reset_dr"):
            for k in ["drafted_h","drafted_p","my_h","my_p"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

        # ── My team summary sidebar ───────────────────────────
        if st.session_state.get("my_h") or st.session_state.get("my_p"):
            st.markdown("---")
            st.markdown("#### 🏆 My Team So Far")
            tm1, tm2 = st.columns(2)
            with tm1:
                if st.session_state.get("my_h"):
                    st.markdown("**⚾ Hitters**")
                    for name in st.session_state["my_h"]:
                        row = bat_rec[bat_rec["Name"]==name]
                        z_val = round(float(row.iloc[0]["composite"]),2) if not row.empty else 0
                        adp_d2 = _get_adp(name)
                        adp2   = adp_d2.get("adp",999)
                        adp_str= f" · ADP {adp2:.0f}" if adp2 < 999 else ""
                        st.markdown(f"• **{name}** (Z:{z_val}{adp_str})")
            with tm2:
                if st.session_state.get("my_p"):
                    st.markdown("**🎯 Pitchers**")
                    for name in st.session_state["my_p"]:
                        row = pit_rec[pit_rec["Name"]==name]
                        z_val = round(float(row.iloc[0]["composite"]),2) if not row.empty else 0
                        adp_d2 = _get_adp(name)
                        adp2   = adp_d2.get("adp",999)
                        adp_str= f" · ADP {adp2:.0f}" if adp2 < 999 else ""
                        st.markdown(f"• **{name}** (Z:{z_val}{adp_str})")

            # Category strength bars
            my_h_df_dr = bat_rec[bat_rec["Name"].isin(st.session_state.get("my_h",[]))]
            my_p_df_dr = pit_rec[pit_rec["Name"].isin(st.session_state.get("my_p",[]))]
            if not my_h_df_dr.empty or not my_p_df_dr.empty:
                st.markdown("**Category Strength**")
                cat_map = {"HR":"z_HR","R":"z_R","RBI":"z_RBI","SB":"z_SB","AVG":"z_AVG",
                           "W":"z_W","SV":"z_SV","SO":"z_K","ERA":"z_ERA","WHIP":"z_WHIP"}
                bar_rows = []
                for cat, zcol in cat_map.items():
                    df_c = my_h_df_dr if cat in ["HR","R","RBI","SB","AVG"] else my_p_df_dr
                    if zcol in df_c.columns and len(df_c) > 0:
                        val = df_c[zcol].mean()
                        bar_rows.append({
                            "Cat": cat, "Z": round(val,2),
                            "Rating": ("💪 Elite" if val>1.0 else "✅ Strong" if val>0.3
                                       else "➡️ Avg" if val>-0.3 else "⚠️ Weak")
                        })
                if bar_rows:
                    bdf2 = pd.DataFrame(bar_rows)
                    fig_bars = go.Figure(go.Bar(
                        x=bdf2["Cat"], y=bdf2["Z"],
                        marker_color=["#21C354" if v>0.3 else "#FFA500" if v>-0.3 else "#FF4B4B"
                                      for v in bdf2["Z"]],
                        text=[f"{v:+.2f}" for v in bdf2["Z"]], textposition="outside"
                    ))
                    fig_bars.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.4)
                    fig_bars.update_layout(template="plotly_dark", height=220,
                                           margin=dict(t=10,b=30))
                    st.plotly_chart(fig_bars, use_container_width=True)

            # Available targets
            avail_tgts = [t for t in st.session_state.targets
                          if t["name"] not in st.session_state.get("drafted_h",set())
                          and t["name"] not in st.session_state.get("drafted_p",set())]
            if avail_tgts:
                st.markdown(f"**🎯 Targets still on board ({len(avail_tgts)})**")
                for t in avail_tgts:
                    adp_t = _get_adp(t["name"]).get("adp", 999)
                    adp_str = f" · ADP {adp_t:.0f}" if adp_t < 999 else ""
                    st.caption(f"• {t['name']} ({t['type']}){adp_str}")

    # ══════════════════════════════════════════════════════════
    #  TAB 2 — DRAFT STRATEGY PLANNER
    # ══════════════════════════════════════════════════════════
    with tab_strat:
        st.markdown("### 🗺️ Draft Strategy Planner")
        league_size = st.slider("League size (teams)", 8, 16, 12)
        your_pick   = st.slider("Your draft position", 1, league_size, 6)
        rs = st.columns(3)
        h_slots  = rs[0].number_input("Hitter spots (starters)", 1, 15, 9)
        p_slots  = rs[1].number_input("Pitcher spots (starters)", 1, 15, 7)
        bn_slots = rs[2].number_input("Bench spots", 0, 10, 7,
                                      help="Yahoo standard: 5 bench + IL spots = 7 extra rounds")
        st.markdown("---")
        cat_priorities = st.multiselect(
            "Your category priorities (select in order of importance)",
            ["HR","R","RBI","SB","AVG","W","SV","ERA","WHIP","K"],
            default=["SB","HR","K","ERA","WHIP","R","RBI","AVG","W"]
        )
        st.markdown("---")
        st.markdown("#### 📋 Round-by-Round Guide")
        total_rounds = h_slots + p_slots + bn_slots  # starters + bench = 23 in Yahoo standard
        pick_numbers = [
            (rd-1)*league_size + your_pick if rd % 2 == 1
            else rd*league_size - your_pick + 1
            for rd in range(1, total_rounds+1)
        ]
        round_advice = {
            1:  ("Superstar anchor",
                 "Elite 1st-rounders: Judge, Ohtani, Witt, Acuna territory. 50+ HR pace, .300+ AVG, or generational SP. "
                 "Don't reach — if your guy is gone, take the next best player, not a consolation prize."),
            2:  ("Top-10 talent",
                 "Best player available. If you missed SB in R1, this is your last easy window for a true speed elite. "
                 "Power hitters with multi-cat upside (HR+R+RBI) are also fine here."),
            3:  ("Speed or SP ace",
                 "SB supply dries up FAST — by round 4 the elite speedsters are gone. "
                 "If you have 0 SB so far, prioritize here. Otherwise lock in your SP1 with an ace-level arm (xFIP < 3.10)."),
            4:  ("SP core / power bat",
                 "Build your pitching core. Target proven starters with xFIP under 3.30 over ERA flukes. "
                 "If pitching is covered, take a power hitter with 35+ HR upside."),
            5:  ("SP2 or breakout hitter",
                 "Secure your rotation's second pillar. Alternatively, target a hitter with elite Barrel% (>12%) "
                 "or SwStr% suppression — players whose underlying metrics outpace their current ADP."),
            6:  ("Category gap fill",
                 "Audit your roster: which of the 10 cats are you losing? If weak in AVG, target a contact hitter. "
                 "If weak in SV, grab a proven closer. This is your last round for targeted category construction before depth takes over."),
            7:  ("Closer + ratio stabilizer",
                 "Lock in saves. Elite closers (35+ SV pace) rarely make it past round 8. "
                 "Also consider high-K, low-WHIP middle relievers who help ERA/WHIP without costing you a starter slot."),
            8:  ("High-upside flier",
                 "Buy low on players with elite underlying metrics but depressed ADP — injuries, role uncertainty, or "
                 "slow starts last year. Barrel% > 12% hitters or SwStr% > 13% pitchers going in rounds 9-12 are your targets."),
            9:  ("Multi-position flex",
                 "Yahoo multi-position eligibility is a massive advantage — 2B/SS, 1B/3B, OF/1B players give you lineup flexibility. "
                 "Prioritize players who qualify at 2+ positions even if their composite rank is slightly lower."),
            10: ("Lottery tickets / SP depth",
                 "Young breakout candidates with elite batted-ball profiles (Barrel% > 10%, hard contact > 40%). "
                 "SP streamers who can be used in 2-start weeks. Target players on good offenses for run/RBI counting stat support."),
            11: ("Saves depth / WHIP anchor",
                 "Second closer or high-leverage RP with saves opportunities. In H2H, SV can swing weekly matchups. "
                 "Also good round for a WHIP anchor — groundball pitchers with K-BB% > 15%."),
            12: ("Bench hitter with eligibility",
                 "A versatile hitter who can fill holes across your lineup. Look for players with 2+ position eligibility "
                 "and platoon upside — someone who starts vs RHP and gives you lineup flexibility on any given week."),
            13: ("SP handcuff / streamer",
                 "A reliable streaming SP — someone with 2 starts in favorable matchup weeks. Target pitchers on good offenses "
                 "for win support and K rates above 25%. This spot is essentially a weekly waiver wire preview."),
            14: ("Speed or AVG specialist",
                 "SB specialists or high-AVG contact hitters who help you win weekly ratio battles. "
                 "A .290+ AVG hitter with 20+ SB potential can be a weekly category winner on his own."),
            15: ("Catcher depth",
                 "If you haven't locked in a second catcher yet, do it now before the pool is gone. "
                 "Look for catchers with framing metrics that suggest playing time security even if offense is marginal."),
            16: ("RP ratio stabilizer",
                 "A high-K, low-BB reliever who anchors your ERA and WHIP without eating into SP slots. "
                 "K-BB% > 18% and GB% > 48% are your filters. These arms help you win pitching ratio cats on weeks your SP struggles."),
            17: ("Upside SP flier",
                 "A high-ceiling SP with stuff metrics that outpace results — high SwStr%, decent xFIP, but ERA is fluky. "
                 "These are your 'start when the matchup is right' arms. FanGraphs Stuff+ > 105 is a good filter."),
            18: ("Handcuff hitter",
                 "The backup for your most injury-prone star. If you drafted a player with IL history, grab his handcuff. "
                 "Also consider platoon hitters who rake vs LHP — useful in daily-swap leagues."),
            19: ("Counting stat accumulator",
                 "High-PA hitters on good offenses who rack up R and RBI even without elite tools. "
                 "Look for 3-4-5 hole hitters on playoff-contending MLB teams. Playing time security matters here."),
            20: ("Closer handcuff",
                 "Back up your closer spot. Identify the 8th-inning setup man behind your closer — if the closer gets hurt "
                 "or loses the job, this player steps in. Also good for teams with committee save situations."),
            21: ("Deep sleeper / prospect",
                 "A prospect with a clear path to the majors mid-season, or a veteran on a new team who hasn't "
                 "gotten buzz yet. xwOBA > .340 with a new hitting coach situation is a classic buy-low signal."),
            22: ("IL gamble",
                 "A high-upside player currently on the IL with a return date within 4-6 weeks. "
                 "These are essentially free picks — worst case they stay hurt, best case you get a starter-quality player for a bench price."),
            23: ("Last pick — pure upside",
                 "Swing for the fences. 23rd round pick is nearly worthless at face value — take the highest-ceiling "
                 "player available regardless of risk. Young pitcher with electric stuff, or a hitter with elite exit velocity "
                 "who just needs a starting job. Nothing to lose."),
        }
        for rd in range(1, total_rounds+1):
            pick_no   = pick_numbers[rd-1] if rd-1 < len(pick_numbers) else "—"
            label, advice = round_advice.get(rd, (f"Round {rd}", "Best player available."))
            with st.expander(f"**Round {rd}** — Pick ~{pick_no}  |  {label}"):
                st.write(advice)
                # Show player suggestions for rounds 1-15
                # Filter out already-drafted players (from draft room session state)
                all_drafted = (st.session_state.get("drafted_h", set()) |
                               st.session_state.get("drafted_p", set()))
                # Player suggestions for all 23 rounds — filter out drafted players
                lo = (rd-1)*league_size
                hi = rd*league_size
                my_picks   = set(st.session_state.get("my_h", []) + st.session_state.get("my_p", []))
                adp_combo  = _adp_cache_combined()

                # For late rounds (16+), expand the rank window since fewer players rank here
                if rd > 15:
                    lo = max(0, (rd-2)*league_size)   # widen window for depth rounds
                    hi = (rd+1)*league_size

                sug_h = bat_rec[
                    (bat_rec["rank"]>=lo) &
                    (bat_rec["rank"]<=hi) &
                    (~bat_rec["Name"].isin(all_drafted))
                ].head(5)
                sug_p = pit_rec[
                    (pit_rec["rank"]>=lo) &
                    (pit_rec["rank"]<=hi) &
                    (~pit_rec["Name"].isin(all_drafted))
                ].head(3)

                if not sug_h.empty:
                    st.markdown("**Hitter targets** *(available only)*:")
                    h_c = [c for c in ["Name","Team","composite","HR","R","RBI",
                                       "SB","AVG","xwOBA","Barrel%"] if c in sug_h.columns]
                    sug_h = sug_h[h_c].copy()
                    sug_h["ADP"]    = sug_h["Name"].apply(lambda n: _adp_label(adp_combo.get(n,{}).get("adp",999)))
                    sug_h["Status"] = sug_h["Name"].apply(lambda n: "✅ Mine" if n in my_picks else "")
                    st.dataframe(sug_h, use_container_width=True, hide_index=True)

                if not sug_p.empty:
                    st.markdown("**Pitcher targets** *(available only)*:")
                    p_c = [c for c in ["Name","Team","composite","W","SV","ERA",
                                       "xFIP","K%","SwStr%"] if c in sug_p.columns]
                    sug_p = sug_p[p_c].copy()
                    sug_p["ADP"]    = sug_p["Name"].apply(lambda n: _adp_label(adp_combo.get(n,{}).get("adp",999)))
                    sug_p["Status"] = sug_p["Name"].apply(lambda n: "✅ Mine" if n in my_picks else "")
                    st.dataframe(sug_p, use_container_width=True, hide_index=True)

                if all_drafted:
                    st.caption(f"🚫 {len(all_drafted)} drafted players hidden")

        st.markdown("---")
        st.markdown("#### 🔍 Category Gap Finder")
        if st.session_state.targets:
            my_h_df = bat_rec[bat_rec["Name"].isin(
                [t["name"] for t in st.session_state.targets if t["type"]=="Hitter"])]
            my_p_df = pit_rec[pit_rec["Name"].isin(
                [t["name"] for t in st.session_state.targets if t["type"]=="Pitcher"])]
            gap_rows = []
            for cat, (src_df2, col) in {
                "HR":(bat_rec,"z_HR"),"R":(bat_rec,"z_R"),"RBI":(bat_rec,"z_RBI"),
                "SB":(bat_rec,"z_SB"),"AVG":(bat_rec,"z_AVG"),"W":(pit_rec,"z_W"),
                "SV":(pit_rec,"z_SV"),"ERA":(pit_rec,"z_ERA"),
                "WHIP":(pit_rec,"z_WHIP"),"K":(pit_rec,"z_K")
            }.items():
                chunk = my_h_df if cat in ["HR","R","RBI","SB","AVG"] else my_p_df
                if col in chunk.columns and len(chunk) > 0:
                    avg_z = chunk[col].mean()
                    gap_rows.append({
                        "Category": cat,
                        "Your Avg Z": round(avg_z, 2),
                        "Status": ("✅ Strong" if avg_z > 0.5 else
                                   "⚠️ Weak"   if avg_z < -0.2 else "➡️ Average")
                    })
            if gap_rows:
                st.dataframe(pd.DataFrame(gap_rows),
                             use_container_width=True, hide_index=True)
        else:
            st.info("Add players to your target list to see category gaps.")

    # ══════════════════════════════════════════════════════════
    #  TAB 3 — MY TARGET LIST
    # ══════════════════════════════════════════════════════════
    with tab_targets:
        st.markdown("### ⭐ My Target List")
        with st.expander("➕ Add a player manually"):
            col_a, col_b, col_c = st.columns(3)
            add_type = col_a.radio("Type", ["Hitter","Pitcher"], horizontal=True,
                                   key="manual_type", label_visibility="collapsed")
            all_names_manual = sorted(
                (bat_rec if add_type=="Hitter" else pit_rec)["Name"].dropna().unique().tolist())
            add_name = col_b.selectbox("Player", all_names_manual, key="manual_name")
            add_note = col_c.text_input("Note", placeholder="e.g. 'Value in round 8'",
                                        key="manual_note")
            if st.button("Add to Target List", key="manual_add"):
                rec_src = bat_rec if add_type=="Hitter" else pit_rec
                rec_row = rec_src[rec_src["Name"]==add_name]
                entry   = {"name": add_name, "type": add_type, "tag": "—",
                           "composite": float(rec_row.iloc[0].get("composite",0)) if not rec_row.empty else 0,
                           "note": add_note}
                if not any(t["name"]==add_name for t in st.session_state.targets):
                    st.session_state.targets.append(entry)
                    st.success(f"✅ Added {add_name}!")
                    st.rerun()
                else:
                    st.info(f"{add_name} already in list.")

        st.markdown("---")
        if not st.session_state.targets:
            st.info("Your target list is empty. Add players from the Draft Board, Deep Dive, or this page.")
        else:
            sc1, sc2 = st.columns(2)
            sort_opt = sc1.selectbox("Sort by",
                ["Composite Z","ADP (earliest first)","ADP Value Gap","Name","Type"],
                key="target_sort")

            # Enrich with ADP
            def _sort_key(t):
                adp_d = _get_adp(t["name"])
                adp   = adp_d.get("adp", 999)
                z_rank = int(bat_rec["composite"].rank(ascending=False).get(
                    bat_rec[bat_rec["Name"]==t["name"]].index[0]
                    if t["type"]=="Hitter" else -1, 999))
                gap = adp - z_rank if adp < 999 else -999
                if sort_opt == "Composite Z":         return -t["composite"]
                elif sort_opt == "ADP (earliest first)": return adp
                elif sort_opt == "ADP Value Gap":     return -gap
                elif sort_opt == "Name":              return t["name"]
                else:                                 return t["type"]

            sorted_targets = sorted(st.session_state.targets, key=_sort_key)
            to_remove = []

            for i, t in enumerate(sorted_targets):
                rec_src = bat_rec if t["type"]=="Hitter" else pit_rec
                rec_row = rec_src[rec_src["Name"]==t["name"]]
                adp_d   = _get_adp(t["name"])
                adp     = adp_d.get("adp", 999)
                pct_own = adp_d.get("pct_own", 0)

                # Value gap
                z_rank = int(rec_src["composite"].rank(ascending=False).get(
                    rec_row.index[0] if not rec_row.empty else -1, 999))
                gap = adp - z_rank if adp < 999 else None
                if gap is None:    vtag = "❓ No ADP"
                elif gap >= 25:    vtag = "🔥 Big Value"
                elif gap >= 12:    vtag = "✅ Value"
                elif gap >= -8:    vtag = "➡️ Fair"
                elif gap >= -20:   vtag = "⚠️ Reach"
                else:              vtag = "🚨 Big Reach"

                gap_str = (f"+{gap:.0f}" if gap and gap > 0 else f"{gap:.0f}") if gap else "—"
                adp_display = f"ADP {adp:.1f}" if adp < 999 else "No ADP"
                owned_str   = f"{pct_own*100:.0f}% owned" if pct_own and pct_own > 0.001 else ""

                with st.container(border=True):
                    h1, h2 = st.columns([4,1])
                    h1.markdown(
                        f"**{t['name']}** &nbsp; `{t['type']}` &nbsp; "
                        f"Z: **{t['composite']:.2f}** (Rank #{z_rank})"
                        + (f"  |  📝 {t['note']}" if t['note'] else "")
                    )
                    h1.caption(
                        f"{adp_display}  ·  Gap: {gap_str}  ·  {vtag}"
                        + (f"  ·  {owned_str}" if owned_str else "")
                    )
                    if not rec_row.empty:
                        r = rec_row.iloc[0]
                        mini = ([c for c in ["HR","R","RBI","SB","AVG","wRC+","xwOBA","Barrel%"] if c in r.index]
                                if t["type"]=="Hitter" else
                                [c for c in ["W","SV","SO","ERA","WHIP","xFIP","K%","SwStr%"] if c in r.index])
                        mcols = st.columns(len(mini))
                        for ci, s in enumerate(mini):
                            v = r.get(s, np.nan)
                            if pd.notna(v):
                                mcols[ci].metric(s,
                                    f"{float(v):.3f}" if isinstance(v,float) and v < 10
                                    else str(int(round(float(v)))))
                    btn_c1, btn_c2, btn_c3 = h2.columns(3) if False else (h2, h2, h2)
                    b1, b2 = h2.columns(2)
                    if b1.button("➕ MC", key=f"mc_{i}_{t['name']}", help="Add to MC Sim"):
                        mc_key = "mc_hitters" if t["type"]=="Hitter" else "mc_pitchers"
                        if mc_key not in st.session_state:
                            st.session_state[mc_key] = []
                        if t["name"] not in st.session_state[mc_key]:
                            st.session_state[mc_key].append(t["name"])
                            st.toast(f"Added {t['name']} to MC Sim")
                    if b2.button("🗑️", key=f"rem_{i}_{t['name']}", help="Remove"):
                        to_remove.append(t["name"])

            for nm in to_remove:
                st.session_state.targets = [t for t in st.session_state.targets if t["name"]!=nm]
            if to_remove:
                st.rerun()

            st.markdown("---")
            # Summary stats
            if len(st.session_state.targets) >= 3:
                st.markdown("#### 📊 Target List Summary")
                vals   = [t for t in st.session_state.targets if _get_adp(t["name"]).get("adp",999) < 999]
                n_val  = sum(1 for t in vals if ((_get_adp(t["name"])["adp"]) -
                             int(rec_src["composite"].rank(ascending=False).get(
                                 rec_src[rec_src["Name"]==t["name"]].index[0]
                                 if not rec_src[rec_src["Name"]==t["name"]].empty else -1, 999))) >= 12)
                sc_a, sc_b, sc_c = st.columns(3)
                sc_a.metric("Total targets",   len(st.session_state.targets))
                sc_b.metric("Value picks",     n_val)
                sc_c.metric("Avg Z-Score",
                    round(np.mean([t["composite"] for t in st.session_state.targets]),2))

            if st.button("🗑️ Clear Entire Target List"):
                st.session_state.targets = []
                st.rerun()

    # ══════════════════════════════════════════════════════════
    #  TAB 4 — COMPARE TARGETS
    # ══════════════════════════════════════════════════════════
    with tab_compare:
        st.markdown("### 📊 Compare Your Targets")
        if len(st.session_state.targets) < 2:
            st.info("Add at least 2 players to your target list to compare them.")
        else:
            h_targets = [t for t in st.session_state.targets if t["type"]=="Hitter"]
            p_targets = [t for t in st.session_state.targets if t["type"]=="Pitcher"]

            def _mc_proj_for(names, is_hitter):
                """Run quick MC sim for each player and return median projections."""
                proj = {}
                for name in names:
                    try:
                        df, _ = mc_run_simulation(
                            (name,), (), 500,
                            0.10, 0.20, 0.05, 0.5,
                            run_count=abs(hash(name)) % 100000
                        ) if is_hitter else mc_run_simulation(
                            (), (name,), 500,
                            0.10, 0.20, 0.05, 0.5,
                            run_count=abs(hash(name)) % 100000
                        )
                        proj[name] = {c: round(float(df[c].median()), 2)
                                      for c in df.columns if c != "Name"}
                    except Exception:
                        proj[name] = {}
                return proj

            if h_targets:
                st.markdown("#### ⚾ Hitter Comparison")
                h_names = [t["name"] for t in h_targets]
                h_df = bat_rec[bat_rec["Name"].isin(h_names)].copy()
                h_df["ADP"] = h_df["Name"].apply(
                    lambda n: _adp_label((_adp_cache_combined()).get(n, {}).get("adp",999)))

                # Stats table
                cc = [c for c in ["Name","Team","ADP","composite","HR","R","RBI",
                                   "SB","AVG","wRC+","xwOBA","xBA","Barrel%","SwStr%"]
                      if c in h_df.columns]
                st.dataframe(
                    h_df[cc].sort_values("composite", ascending=False)
                        .style.background_gradient(subset=["composite"], cmap="RdYlGn")
                        .format({"composite":"{:.2f}","AVG":"{:.3f}",
                                 "xwOBA":"{:.3f}","xBA":"{:.3f}","Barrel%":"{:.3f}",
                                 "SwStr%":"{:.3f}"}),
                    use_container_width=True, hide_index=True)

                # Radar chart
                z_h = [c for c in ["z_HR","z_R","z_RBI","z_SB","z_AVG"] if c in h_df.columns]
                if z_h:
                    fig_comp = go.Figure()
                    labels = [c.replace("z_","") for c in z_h]
                    colors = px.colors.qualitative.Plotly
                    for ci, (_, row) in enumerate(h_df.iterrows()):
                        vals = [max(-3,min(3,float(row.get(c,0)))) for c in z_h]
                        fig_comp.add_trace(go.Scatterpolar(
                            r=vals+[vals[0]], theta=labels+[labels[0]],
                            fill="toself", name=row["Name"],
                            line_color=colors[ci%len(colors)]))
                    fig_comp.update_layout(
                        polar=dict(radialaxis=dict(range=[-3,3])),
                        template="plotly_dark", height=380,
                        legend=dict(orientation="h", y=-0.15))
                    st.plotly_chart(fig_comp, use_container_width=True)

                # MC projections
                st.markdown("**🎲 Monte Carlo Season Projections (Median)**")
                st.caption("Individual player MC sims — 500 seasons each.")
                if st.button("Run MC Projections for Hitters", key="btn_mc_compare_h"):
                    with st.spinner("Running MC sims..."):
                        mc_projs = _mc_proj_for(h_names, True)
                    mc_rows = []
                    for name in h_names:
                        p = mc_projs.get(name, {})
                        mc_rows.append({
                            "Name":  name,
                            "HR":    p.get("HR","—"),
                            "R":     p.get("R","—"),
                            "RBI":   p.get("RBI","—"),
                            "SB":    p.get("SB","—"),
                            "AVG":   round(p["AVG"],3) if "AVG" in p else "—",
                        })
                    st.dataframe(pd.DataFrame(mc_rows), use_container_width=True, hide_index=True)

            if p_targets:
                st.markdown("#### 🎯 Pitcher Comparison")
                p_names = [t["name"] for t in p_targets]
                p_df = pit_rec[pit_rec["Name"].isin(p_names)].copy()
                p_df["ADP"] = p_df["Name"].apply(
                    lambda n: _adp_label((_adp_cache_combined()).get(n, {}).get("adp",999)))

                cc = [c for c in ["Name","Team","ADP","composite","W","SV","ERA",
                                   "WHIP","SO","xFIP","SIERA","K%","SwStr%","GB%"]
                      if c in p_df.columns]
                st.dataframe(
                    p_df[cc].sort_values("composite", ascending=False)
                        .style.background_gradient(subset=["composite"], cmap="RdYlGn")
                        .format({"composite":"{:.2f}","ERA":"{:.2f}","WHIP":"{:.3f}",
                                 "xFIP":"{:.2f}","K%":"{:.3f}","SwStr%":"{:.3f}",
                                 "GB%":"{:.3f}"}),
                    use_container_width=True, hide_index=True)

                # Radar chart
                z_p = [c for c in ["z_W","z_SV","z_ERA","z_WHIP","z_K"] if c in p_df.columns]
                if z_p:
                    fig_p = go.Figure()
                    labels_p = [c.replace("z_","") for c in z_p]
                    colors = px.colors.qualitative.Plotly
                    for ci, (_, row) in enumerate(p_df.iterrows()):
                        vals = [max(-3,min(3,float(row.get(c,0)))) for c in z_p]
                        fig_p.add_trace(go.Scatterpolar(
                            r=vals+[vals[0]], theta=labels_p+[labels_p[0]],
                            fill="toself", name=row["Name"],
                            line_color=colors[ci%len(colors)]))
                    fig_p.update_layout(
                        polar=dict(radialaxis=dict(range=[-3,3])),
                        template="plotly_dark", height=380,
                        legend=dict(orientation="h", y=-0.15))
                    st.plotly_chart(fig_p, use_container_width=True)

                # MC projections
                st.markdown("**🎲 Monte Carlo Season Projections (Median)**")
                if st.button("Run MC Projections for Pitchers", key="btn_mc_compare_p"):
                    with st.spinner("Running MC sims..."):
                        mc_projs_p = _mc_proj_for(p_names, False)
                    mc_rows_p = []
                    for name in p_names:
                        p2 = mc_projs_p.get(name, {})
                        mc_rows_p.append({
                            "Name":  name,
                            "W":     p2.get("W","—"),
                            "SV":    p2.get("SV","—"),
                            "SO":    p2.get("SO","—"),
                            "ERA":   round(p2["ERA"],2)  if "ERA"  in p2 else "—",
                            "WHIP":  round(p2["WHIP"],3) if "WHIP" in p2 else "—",
                        })
                    st.dataframe(pd.DataFrame(mc_rows_p), use_container_width=True, hide_index=True)


    # ══════════════════════════════════════════════════════════
    #  TAB 5 — DRAFT GRADE
    # ══════════════════════════════════════════════════════════
    with tab_grade:
        st.markdown("### 🎓 Post-Draft Grade")
        st.caption(
            "After your draft completes, connect Yahoo and load your roster to grade "
            "every pick against ADP and our projections. See where you found value, "
            "where you reached, and get an overall draft score."
        )

        if not yahoo_connected or not league_key_adp:
            st.info("👆 Connect your Yahoo account on the **🏆 My Yahoo League** page first, "
                    "then come back here to grade your draft.")
            st.stop()

        # Load roster for grading
        my_team_key_grade = st.session_state.get("yahoo_my_team_key")
        my_team_name_grade = st.session_state.get("yahoo_my_team_name","My Team")

        if not my_team_key_grade:
            st.warning("Could not find your team key. Visit **🏆 My Yahoo League → My Roster** first.")
            st.stop()

        if st.button("🔄 Load Draft Results & Grade", type="primary", key="btn_draft_grade"):
            st.session_state.pop("draft_grade_data", None)

        if "draft_grade_data" not in st.session_state:
            with st.spinner("Fetching your drafted roster..."):
                import requests as _rg
                access_token_g = st.session_state["yahoo_token"]["access_token"]

                # Fetch roster
                roster_url = (f"https://fantasysports.yahooapis.com/fantasy/v2"
                              f"/team/{my_team_key_grade}/roster/players?format=json")
                r_resp = _rg.get(roster_url,
                    headers={"Authorization": f"Bearer {access_token_g}",
                             "Accept": "application/json"}, timeout=15)

                # Fetch draft results for the league
                draft_url = (f"https://fantasysports.yahooapis.com/fantasy/v2"
                             f"/league/{league_key_adp}/draftresults?format=json")
                d_resp = _rg.get(draft_url,
                    headers={"Authorization": f"Bearer {access_token_g}",
                             "Accept": "application/json"}, timeout=15)

                st.session_state["draft_grade_data"] = {
                    "roster": r_resp.json() if r_resp.status_code == 200 else {"error": f"HTTP {r_resp.status_code}"},
                    "draft":  d_resp.json() if d_resp.status_code == 200 else {"error": f"HTTP {d_resp.status_code}"},
                }

        if "draft_grade_data" not in st.session_state:
            st.info("Click **Load Draft Results & Grade** above to begin.")
            st.stop()

        grade_data   = st.session_state["draft_grade_data"]
        roster_data  = grade_data["roster"]
        draft_resp   = grade_data["draft"]

        # ── Parse roster ──────────────────────────────────────
        my_players = []
        if "error" not in roster_data:
            try:
                entries = roster_data["fantasy_content"]["team"][1]["roster"]["0"]["players"]
                for k, v in entries.items():
                    if k == "count": continue
                    p0   = v["player"][0]
                    name = next((x["name"]["full"] for x in p0 if isinstance(x,dict) and "name" in x), None)
                    pos  = next((x["display_position"] for x in p0 if isinstance(x,dict) and "display_position" in x), "")
                    pkey = next((x["player_key"] for x in p0 if isinstance(x,dict) and "player_key" in x), "")
                    if name:
                        my_players.append({"name": name, "pos": pos, "player_key": pkey})
            except Exception as e:
                st.error(f"Could not parse roster: {e}")

        # ── Parse draft results ────────────────────────────────
        # Map player_key → pick number for my players
        my_picks = {}
        if "error" not in draft_resp:
            try:
                picks_raw = draft_resp["fantasy_content"]["league"][1]["draft_results"]["0"]["draft_results"]
                for k, v in picks_raw.items():
                    if k == "count": continue
                    dr = v["draft_result"]
                    team_key  = dr.get("team_key","")
                    pick_num  = int(dr.get("pick", 0))
                    round_num = int(dr.get("round", 0))
                    pkey      = dr.get("player_key","")
                    # Is this pick mine?
                    if my_team_key_grade in team_key or team_key == my_team_key_grade:
                        my_picks[pkey] = {"pick": pick_num, "round": round_num}
            except Exception as e:
                st.warning(f"Could not parse draft results: {e}. "
                           "Draft may not have happened yet, or results aren't available via API.")

        if not my_players:
            st.warning("No roster found. Make sure your draft is complete.")
            st.stop()

        # ── Build grade table ──────────────────────────────────
        LETTER_GRADES = {
            (30, 999):  ("A+", "#21C354", "Steal of the draft"),
            (15,  30):  ("A",  "#21C354", "Big value"),
            (8,   15):  ("B+", "#7BC67E", "Good value"),
            (0,    8):  ("B",  "#FFA500", "Solid pick, fair price"),
            (-10,  0):  ("C",  "#FFA500", "Slight reach"),
            (-25, -10): ("D",  "#FF4B4B", "Reach"),
            (-999,-25): ("F",  "#FF4B4B", "Significant reach"),
        }

        def _letter(gap):
            for (lo, hi), (grade, color, label) in LETTER_GRADES.items():
                if lo <= gap < hi:
                    return grade, color, label
            return "C", "#FFA500", "Fair pick"

        grade_rows = []
        grade_scores = []

        for p in my_players:
            name   = p["name"]
            pos    = p["pos"]
            pkey   = p["player_key"]
            is_hit = any(x in pos for x in ["1B","2B","3B","SS","OF","C","DH","Util"])
            src_df_g = bat_rec if is_hit else pit_rec
            rec    = src_df_g[src_df_g["Name"].str.lower() == name.lower()]

            # Our rank
            our_rank = int(src_df_g["composite"].rank(ascending=False)[rec.index[0]]
                           ) if not rec.empty else 999
            z_score  = float(rec.iloc[0].get("composite",0)) if not rec.empty else 0

            # ADP from cache or pick from draft results
            adp_d  = _get_adp(name)
            adp    = adp_d.get("adp", 999)

            # Actual pick number
            pick_info = my_picks.get(pkey, {})
            actual_pick = pick_info.get("pick", None)
            actual_round = pick_info.get("round", None)

            # Use actual pick if available, else ADP
            compare_pick = actual_pick if actual_pick else adp
            gap = round(compare_pick - our_rank, 1) if compare_pick and compare_pick < 999 else None

            if gap is not None:
                grade, color, label = _letter(gap)
                grade_scores.append(gap)
            else:
                grade, color, label = "?", "#888", "No ADP data"

            # Key stat
            if not rec.empty:
                r = rec.iloc[0]
                key_stat = (f"HR:{int(r['HR'])} AVG:{r['AVG']:.3f}" if is_hit
                            else f"ERA:{r['ERA']:.2f} K:{int(r['SO'])}")
            else:
                key_stat = ""

            grade_rows.append({
                "Round":       actual_round or ("~" + str(round(adp/12)) if adp < 999 else "?"),
                "Pick":        actual_pick or ("~" + f"{adp:.0f}" if adp < 999 else "?"),
                "Name":        name,
                "Pos":         pos,
                "Our Rank":    our_rank if our_rank < 999 else "?",
                "ADP":         f"{adp:.1f}" if adp < 999 else "—",
                "Gap":         (f"+{gap:.0f}" if gap and gap > 0 else f"{gap:.0f}") if gap else "—",
                "Grade":       grade,
                "Assessment":  label,
                "Key Stats":   key_stat,
                "Z-Score":     round(z_score, 2),
            })

        # Sort by round/pick
        grade_rows.sort(key=lambda x: float(str(x["Pick"]).replace("~","").replace("?","999") or 999))

        gdf = pd.DataFrame(grade_rows)

        # ── Overall draft score ────────────────────────────────
        if grade_scores:
            avg_gap    = np.mean(grade_scores)
            pct_value  = sum(1 for g in grade_scores if g >= 8) / len(grade_scores) * 100
            pct_reach  = sum(1 for g in grade_scores if g < -10) / len(grade_scores) * 100

            # Overall letter grade
            if   avg_gap >= 15: overall, oc = "A",  "#21C354"
            elif avg_gap >= 8:  overall, oc = "B+", "#7BC67E"
            elif avg_gap >= 2:  overall, oc = "B",  "#FFA500"
            elif avg_gap >= -5: overall, oc = "C+", "#FFA500"
            elif avg_gap >= -12:overall, oc = "C",  "#FF8C00"
            else:               overall, oc = "D",  "#FF4B4B"

            st.markdown(
                f"<h1 style='text-align:center;color:{oc};font-size:72px'>{overall}</h1>"
                f"<p style='text-align:center;color:#aaa'>Overall Draft Grade for {my_team_name_grade}</p>",
                unsafe_allow_html=True
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Avg Value Gap",    f"{avg_gap:+.1f} picks")
            m2.metric("Value Picks",      f"{pct_value:.0f}%",
                      help="% of picks where you got value vs ADP")
            m3.metric("Reaches",          f"{pct_reach:.0f}%",
                      help="% of picks where you reached 10+ spots")
            m4.metric("Picks Graded",     len(grade_scores))

            # Grade distribution bar chart
            grade_counts = {}
            for row in grade_rows:
                g = row["Grade"]
                grade_counts[g] = grade_counts.get(g, 0) + 1
            grade_order = ["A+","A","B+","B","C","D","F","?"]
            grade_colors_map = {
                "A+":"#21C354","A":"#21C354","B+":"#7BC67E","B":"#FFA500",
                "C":"#FFA500","D":"#FF4B4B","F":"#FF4B4B","?":"#888"
            }
            fig_grades = go.Figure(go.Bar(
                x=[g for g in grade_order if g in grade_counts],
                y=[grade_counts.get(g,0) for g in grade_order if g in grade_counts],
                marker_color=[grade_colors_map.get(g,"#888") for g in grade_order if g in grade_counts],
                text=[grade_counts.get(g,0) for g in grade_order if g in grade_counts],
                textposition="outside"
            ))
            fig_grades.update_layout(
                template="plotly_dark", height=220,
                xaxis_title="Grade", yaxis_title="# of Picks",
                margin=dict(t=10,b=40)
            )
            st.plotly_chart(fig_grades, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📋 Pick-by-Pick Breakdown")

        def _grade_color(val):
            return grade_colors_map.get(str(val), "")

        def _gap_color_g(val):
            try:
                v = float(str(val).replace("+",""))
                if v >= 15:  return "color:#21C354;font-weight:bold"
                if v >= 8:   return "color:#21C354"
                if v >= -10: return "color:#FFA500"
                return "color:#FF4B4B"
            except: return ""

        st.dataframe(
            gdf.style
                .map(lambda v: f"color:{grade_colors_map.get(str(v),'#888')};font-weight:bold",
                     subset=["Grade"])
                .map(_gap_color_g, subset=["Gap"]),
            use_container_width=True, hide_index=True, height=520
        )

        # ── Best and worst picks ──────────────────────────────
        st.markdown("---")
        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown("#### 🏆 Best Picks")
            best = gdf[gdf["Grade"].isin(["A+","A","B+"])].head(5)
            if not best.empty:
                for _, row in best.iterrows():
                    st.markdown(
                        f"**Rd {row['Round']} Pick {row['Pick']} — {row['Name']}** "
                        f"({row['Pos']}) · Grade **{row['Grade']}** · {row['Assessment']} "
                        f"· Gap: {row['Gap']}"
                    )
            else:
                st.info("No A/B+ picks found.")

        with bc2:
            st.markdown("#### ⚠️ Reaches to Watch")
            worst = gdf[gdf["Grade"].isin(["D","F"])].head(5)
            if not worst.empty:
                for _, row in worst.iterrows():
                    st.markdown(
                        f"**Rd {row['Round']} Pick {row['Pick']} — {row['Name']}** "
                        f"({row['Pos']}) · Grade **{row['Grade']}** · {row['Assessment']} "
                        f"· Gap: {row['Gap']}"
                    )
            else:
                st.success("No significant reaches — solid draft!")

        # ── Category coverage from draft ──────────────────────
        st.markdown("---")
        st.markdown("#### 📊 Category Coverage from Your Draft")
        st.caption("How well your drafted roster covers all 10 categories based on z-scores.")
        drafted_h = [p["name"] for p in my_players
                     if any(x in p["pos"] for x in ["1B","2B","3B","SS","OF","C","DH","Util"])]
        drafted_p = [p["name"] for p in my_players
                     if any(x in p["pos"] for x in ["SP","RP","P"])]
        dh_df = bat_rec[bat_rec["Name"].isin(drafted_h)]
        dp_df = pit_rec[pit_rec["Name"].isin(drafted_p)]
        cat_cov = []
        for cat, (df_c, zcol) in {
            "HR":(dh_df,"z_HR"),"R":(dh_df,"z_R"),"RBI":(dh_df,"z_RBI"),
            "SB":(dh_df,"z_SB"),"AVG":(dh_df,"z_AVG"),
            "W":(dp_df,"z_W"),"SV":(dp_df,"z_SV"),"SO":(dp_df,"z_K"),
            "ERA":(dp_df,"z_ERA"),"WHIP":(dp_df,"z_WHIP"),
        }.items():
            if zcol in df_c.columns and len(df_c) > 0:
                avg_z = df_c[zcol].mean()
                cat_cov.append({
                    "Category": cat,
                    "Avg Z": round(avg_z, 2),
                    "Rating": ("💪 Elite"   if avg_z > 1.0 else
                               "✅ Strong"  if avg_z > 0.3 else
                               "➡️ Average" if avg_z > -0.3 else
                               "⚠️ Weak"    if avg_z > -0.8 else
                               "🚨 Punt"),
                })

        if cat_cov:
            cov_df = pd.DataFrame(cat_cov)
            fig_cov = go.Figure(go.Bar(
                x=cov_df["Category"], y=cov_df["Avg Z"],
                marker_color=["#21C354" if v>0.3 else "#FFA500" if v>-0.3 else "#FF4B4B"
                              for v in cov_df["Avg Z"]],
                text=[f"{v:+.2f}" for v in cov_df["Avg Z"]],
                textposition="outside"
            ))
            fig_cov.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            fig_cov.update_layout(
                template="plotly_dark", height=270,
                yaxis_title="Avg Z-Score", margin=dict(t=10,b=40)
            )
            st.plotly_chart(fig_cov, use_container_width=True)
            st.dataframe(cov_df.style.map(
                lambda v: ("color:#21C354" if "Elite" in str(v) or "Strong" in str(v)
                           else "color:#FFA500" if "Average" in str(v)
                           else "color:#FF4B4B"), subset=["Rating"]),
                use_container_width=True, hide_index=True)


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
        "SV":   {"SV":1.0},
        "ERA":  {"ERA":0.6,"xFIP":0.6,"SIERA":0.5},
        "WHIP": {"WHIP":0.8,"BB%":0.5},
        "K":    {"SO":1.0,"K%":0.8,"SwStr%":0.5},
    }
    default_cat_weights_h = {"HR":1.0,"R":1.0,"RBI":1.0,"SB":1.0,"AVG":1.0}
    default_cat_weights_p = {"W":1.0,"SV":1.0,"ERA":1.0,"WHIP":1.0,"K":1.0}

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
        cw_cols_p = st.columns(5)
        for i, cat in enumerate(["W","SV","ERA","WHIP","K"]):
            st.session_state.cwp[cat] = cw_cols_p[i].slider(f"{cat} importance",0.0,3.0,float(st.session_state.cwp.get(cat,1.0)),0.25,key=f"cwp_{cat}")
        st.markdown("---"); st.markdown("#### Stat-Level Weights")
        stat_info_p = {
            "W":  {"W":"Raw win count"},
            "SV": {"SV":"Raw save count"},
            "ERA":{"ERA":"ERA (lower=better)","xFIP":"xFIP (lower=better)","SIERA":"SIERA (lower=better)"},
            "WHIP":{"WHIP":"WHIP (lower=better)","BB%":"Walk rate (lower=better)"},
            "K":  {"SO":"Raw strikeout count","K%":"Strikeout rate","SwStr%":"Swinging strike rate"},
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
        preview_type = st.radio("Preview type", ["Hitters","Pitchers"], horizontal=True, key="preview_type", label_visibility="collapsed")

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
            sc = [c for c in ["Name","Team","rank","composite","default_rank","default_composite","rank_change","W","SV","ERA","WHIP","SO","xFIP","SIERA","K%","z_W","z_SV","z_ERA","z_WHIP","z_K"] if c in cp.columns]
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

    # ── Yahoo 12-team standard roster composition ──────────────
    # C, 1B, 2B, 3B, SS, OF, OF, OF, Util, Util, SP, SP, RP, RP, P, P, P, P, BN x5, IL x4
    ALL_POSITIONS = [
        "C","1B","2B","3B","SS",
        "OF1","OF2","OF3",
        "Util1","Util2",
        "SP1","SP2","RP1","RP2",
        "P1","P2","P3","P4",
        "BN1","BN2","BN3","BN4","BN5",
    ]

    HIT_POSITIONS = ["C","1B","2B","3B","SS","OF1","OF2","OF3","Util1","Util2","BN1","BN2","BN3","BN4","BN5"]
    PIT_POSITIONS = ["SP1","SP2","RP1","RP2","P1","P2","P3","P4","BN1","BN2","BN3","BN4","BN5"]
    PURE_PIT = ["SP1","SP2","RP1","RP2","P1","P2","P3","P4"]
    PURE_HIT = ["C","1B","2B","3B","SS","OF1","OF2","OF3","Util1","Util2"]
    SHARED   = ["BN1","BN2","BN3","BN4","BN5"]

    POS_LABEL = {
        "C":"C","1B":"1B","2B":"2B","3B":"3B","SS":"SS",
        "OF1":"OF","OF2":"OF","OF3":"OF",
        "Util1":"Util","Util2":"Util",
        "SP1":"SP","SP2":"SP","RP1":"RP","RP2":"RP",
        "P1":"P","P2":"P","P3":"P","P4":"P",
        "BN1":"BN","BN2":"BN","BN3":"BN","BN4":"BN","BN5":"BN",
    }

    # Init depth chart state
    if "dc_roster" not in st.session_state:
        st.session_state["dc_roster"] = {pos: "" for pos in ALL_POSITIONS}

    dc = st.session_state["dc_roster"]

    st.markdown("### 🏟️ Depth Chart Roster")
    st.caption("Build your Yahoo fantasy roster below. Field positions on the left, pitchers & bench on the right.")

    # ── CSS ──────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .dc-wrapper { display:flex; gap:16px; align-items:flex-start; }
    .dc-field-col { flex:0 0 auto; }
    .dc-right-col { flex:1; }
    .dc-section-title {
        font-size:13px; font-weight:700; color:#4fc3f7;
        letter-spacing:1px; text-transform:uppercase;
        margin:10px 0 4px 0; border-bottom:1px solid #2d3748; padding-bottom:3px;
    }
    .dc-slot-row {
        display:flex; align-items:center; gap:6px;
        padding:3px 0;
    }
    .dc-pos-badge {
        background:#1a2332; border:1px solid #4fc3f7; border-radius:4px;
        color:#4fc3f7; font-weight:700; font-size:10px;
        padding:2px 6px; min-width:32px; text-align:center;
        white-space:nowrap;
    }
    .dc-pos-badge.filled { border-color:#21C354; color:#21C354; background:#0d1f10; }
    .dc-pos-badge.bench  { border-color:#FFA500; color:#FFA500; background:#1f1700; }
    .dc-pos-badge.il     { border-color:#FF4B4B; color:#FF4B4B; background:#1f0000; }
    .dc-player-val {
        background:#0e1117; border:1px solid #2d3748; border-radius:4px;
        color:#eee; font-size:11px; padding:3px 8px; flex:1;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    }
    .dc-player-val.empty { color:#555; font-style:italic; }
    </style>
    """, unsafe_allow_html=True)

    # ── Build the HTML baseball field with position labels overlaid ──
    def _field_html(dc):
        def _slot(key, x_pct, y_pct, label, anchor="center"):
            player = dc.get(key, "")
            short  = (player[:12] + "…") if len(player) > 12 else player
            disp   = short if short else "—"
            filled = "filled" if player else ""
            # anchor: center | left | right
            transform = {
                "center": "translate(-50%,-50%)",
                "left":   "translate(0%,-50%)",
                "right":  "translate(-100%,-50%)",
            }[anchor]
            return f'''
            <div style="position:absolute; left:{x_pct}%; top:{y_pct}%;
                        transform:{transform}; text-align:center; z-index:10;">
                <div style="font-size:11px; font-weight:800; color:{'#21C354' if player else '#FFD700'};
                            text-shadow:1px 1px 3px #000; letter-spacing:0.5px;">{label}</div>
                <div style="background:{'rgba(33,195,84,0.25)' if player else 'rgba(0,0,0,0.65)'};
                            border:1.5px solid {'#21C354' if player else 'rgba(255,255,255,0.3)'};
                            border-radius:4px; padding:2px 6px; min-width:80px;
                            font-size:10px; color:{'#21C354' if player else '#aaa'};
                            white-space:nowrap; font-weight:600;">{disp}</div>
            </div>'''

        # Field: 600×520px SVG + position divs
        # Coordinate system: 0,0 = top-left of the 600×520 container
        # Diamond corners (in %): Home=50%,88% | 1B=78%,62% | 2B=50%,36% | 3B=22%,62%
        return f'''
        <div style="position:relative; width:600px; height:520px; margin:0 auto;
                    background:#0e1117; border-radius:12px; overflow:hidden;">

          <!-- SVG field -->
          <svg width="600" height="520" style="position:absolute;top:0;left:0;">
            <!-- Sky/warning track fill -->
            <rect width="600" height="520" fill="#1a3d0a"/>
            <!-- Outfield grass wedge (clipped arc) -->
            <path d="M 300 460 L 30 460 Q 20 160 300 60 Q 580 160 570 460 Z"
                  fill="#2d6b14" stroke="#3d8a1e" stroke-width="2"/>
            <!-- Infield grass -->
            <path d="M 300 440 L 468 290 L 300 140 L 132 290 Z"
                  fill="#3a7d1e" stroke="#4a9d28" stroke-width="1.5"/>
            <!-- Infield dirt diamond -->
            <path d="M 300 430 L 460 285 L 300 140 L 140 285 Z"
                  fill="#9e7040" stroke="#7a5230" stroke-width="2"/>
            <!-- Foul lines -->
            <line x1="300" y1="450" x2="40"  y2="50"  stroke="white" stroke-width="1.5" opacity="0.6"/>
            <line x1="300" y1="450" x2="560" y2="50"  stroke="white" stroke-width="1.5" opacity="0.6"/>
            <!-- Outfield arc/wall -->
            <path d="M 40 450 Q 20 140 300 50 Q 580 140 560 450"
                  fill="none" stroke="#5aaa28" stroke-width="4"/>
            <!-- Warning track -->
            <path d="M 55 445 Q 30 150 300 65 Q 570 150 545 445"
                  fill="none" stroke="#c4a96a" stroke-width="8" opacity="0.5"/>
            <!-- Pitcher mound -->
            <ellipse cx="300" cy="285" rx="22" ry="16" fill="#b8945a" stroke="#8a6c3a" stroke-width="1.5"/>
            <!-- Pitcher's rubber -->
            <rect x="293" y="281" width="14" height="5" rx="1" fill="white" opacity="0.8"/>
            <!-- Bases -->
            <rect x="288" y="128" width="24" height="24" rx="2" fill="white" stroke="#ddd" stroke-width="1" transform="rotate(45,300,140)"/>
            <rect x="448" y="273" width="24" height="24" rx="2" fill="white" stroke="#ddd" stroke-width="1" transform="rotate(45,460,285)"/>
            <rect x="128" y="273" width="24" height="24" rx="2" fill="white" stroke="#ddd" stroke-width="1" transform="rotate(45,140,285)"/>
            <!-- Home plate (pentagon) -->
            <polygon points="288,444 312,444 318,452 300,462 282,452" fill="white" stroke="#ddd" stroke-width="1"/>
            <!-- Grass mowing stripes -->
            <line x1="300" y1="60"  x2="300" y2="450" stroke="rgba(255,255,255,0.04)" stroke-width="18"/>
            <line x1="220" y1="80"  x2="220" y2="450" stroke="rgba(255,255,255,0.03)" stroke-width="14"/>
            <line x1="380" y1="80"  x2="380" y2="450" stroke="rgba(255,255,255,0.03)" stroke-width="14"/>
            <line x1="140" y1="130" x2="140" y2="450" stroke="rgba(255,255,255,0.02)" stroke-width="10"/>
            <line x1="460" y1="130" x2="460" y2="450" stroke="rgba(255,255,255,0.02)" stroke-width="10"/>
          </svg>

          <!-- Position labels overlaid on field -->
          {_slot("CF",  50,  14, "CF")}
          {_slot("OF1", 26,  28, "LF", "left")}
          {_slot("OF2", 74,  28, "RF", "right")}
          {_slot("SS",  38,  52, "SS")}
          {_slot("2B",  62,  52, "2B")}
          {_slot("3B",  22,  56, "3B", "left")}
          {_slot("1B",  78,  56, "1B", "right")}
          {_slot("P1",  50,  58, "P")}
          {_slot("C",   50,  84, "C")}
        </div>
        '''

    # ── Render field + side panels ────────────────────────────
    left_col, field_col, right_col = st.columns([1, 3, 1])

    with field_col:
        st_components.html(_field_html(dc), height=540, scrolling=False)

    # ── Selector panels below the field ───────────────────────
    st.markdown("---")
    sel_cols = st.columns([1,1,1,1])

    # Panel 1: Infield/Battery
    with sel_cols[0]:
        st.markdown('<div class="dc-section-title">⚾ Infield / Battery</div>', unsafe_allow_html=True)
        for pos in ["C","1B","2B","3B","SS"]:
            cur  = dc.get(pos, "")
            taken = {v for k,v in dc.items() if v and k != pos}
            opts = [""] + [n for n in all_h_names_mc if n not in taken]
            idx  = opts.index(cur) if cur in opts else 0
            sel  = st.selectbox(f"{POS_LABEL[pos]}", opts, index=idx, key=f"dc_{pos}",
                                label_visibility="visible")
            st.session_state["dc_roster"][pos] = sel

    # Panel 2: Outfield + Util
    with sel_cols[1]:
        st.markdown('<div class="dc-section-title">🌿 Outfield / Util</div>', unsafe_allow_html=True)
        for pos in ["OF1","OF2","OF3","Util1","Util2"]:
            cur  = dc.get(pos, "")
            taken = {v for k,v in dc.items() if v and k != pos}
            opts = [""] + [n for n in all_h_names_mc if n not in taken]
            idx  = opts.index(cur) if cur in opts else 0
            sel  = st.selectbox(f"{POS_LABEL[pos]} {'('+str(['OF1','OF2','OF3'].index(pos)+1)+')' if 'OF' in pos else '('+ str(['Util1','Util2'].index(pos)+1)+')'}",
                                opts, index=idx, key=f"dc_{pos}", label_visibility="visible")
            st.session_state["dc_roster"][pos] = sel

    # Panel 3: Pitchers
    with sel_cols[2]:
        st.markdown('<div class="dc-section-title">⚡ Pitchers</div>', unsafe_allow_html=True)
        for pos in ["SP1","SP2","RP1","RP2","P1","P2","P3","P4"]:
            cur  = dc.get(pos, "")
            taken = {v for k,v in dc.items() if v and k != pos}
            opts = [""] + [n for n in all_p_names_mc if n not in taken]
            idx  = opts.index(cur) if cur in opts else 0
            n    = int(pos[-1])
            sel  = st.selectbox(f"{POS_LABEL[pos]} ({n})", opts, index=idx, key=f"dc_{pos}",
                                label_visibility="visible")
            st.session_state["dc_roster"][pos] = sel

    # Panel 4: Bench
    with sel_cols[3]:
        st.markdown('<div class="dc-section-title">🪑 Bench</div>', unsafe_allow_html=True)
        all_players = sorted(all_h_names_mc + all_p_names_mc)
        for pos in ["BN1","BN2","BN3","BN4","BN5"]:
            cur  = dc.get(pos, "")
            taken = {v for k,v in dc.items() if v and k != pos}
            opts = [""] + [n for n in all_players if n not in taken]
            idx  = opts.index(cur) if cur in opts else 0
            n    = int(pos[-1])
            sel  = st.selectbox(f"{POS_LABEL[pos]} ({n})", opts, index=idx, key=f"dc_{pos}",
                                label_visibility="visible")
            st.session_state["dc_roster"][pos] = sel

    # ── Derive rosters from depth chart ───────────────────────
    # Hitters: pure hit slots + BN/IL that contain a hitter name
    h_name_set  = set(all_h_names_mc)
    p_name_set  = set(all_p_names_mc)
    dc_hitters  = list({v for k,v in dc.items() if v and (k in PURE_HIT or (k in SHARED and v in h_name_set))})
    dc_pitchers = list({v for k,v in dc.items() if v and (k in PURE_PIT or (k in SHARED and v in p_name_set))})

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
                    "10th %ile": round(p10, 3 if cat == "AVG" else 2),
                    "25th %ile": round(p25, 3 if cat == "AVG" else 2),
                    "Median": round(p50, 3 if cat == "AVG" else 2),
                    "75th %ile": round(p75, 3 if cat == "AVG" else 2),
                    "90th %ile": round(p90, 3 if cat == "AVG" else 2),
                    "Std Dev": round(float(vals.std()), 3 if cat == "AVG" else 2), "CV%": cv,
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
        # ── Tab 5: Season Sim ──────────────────────────────────
        with tab_season:
            st.markdown("### 📅 Yahoo Fantasy Season Simulator")
            st.caption(
                "Simulates 20 weeks of H2H 10-cat matchups. "
                "**Correct methodology:** samples *weekly* stat totals from per-game rates × games that week, "
                "then compares your weekly totals vs opponent weekly totals category-by-category. "
                "A great season = ~120 W (6/10 cats/week). Average = 100 W (5/10). "
                "Total slots = 20 weeks × 10 cats = 200."
            )

            ss_col1, ss_col2, ss_col3 = st.columns(3)
            ss_n_seasons     = ss_col1.slider("Seasons to simulate", 500, 5000, 1000, 500, key="ss_n_seasons")
            ss_league_sz     = ss_col2.slider("League size", 8, 16, 12, key="ss_league_sz")
            ss_playoff_spots = ss_col3.slider("Playoff spots", 2, 8, 4, key="ss_playoff_spots")

            run_season_sim = st.button("🏆 Run Season Simulation", type="primary", key="btn_season_sim")

            if run_season_sim:
                REG_WEEKS   = 20
                N_SIM       = ss_n_seasons
                N_OPP       = ss_league_sz - 1
                cats_ss     = [c for c in MC_ALL_CATS if c in team_sims.columns]
                N_CATS      = len(cats_ss)
                TOTAL_SLOTS = REG_WEEKS * N_CATS   # 200

                # ── WEEKLY STAT DISTRIBUTIONS ─────────────────────────────
                # The correct approach for H2H categories:
                # Compare WEEKLY stat totals (not season totals) head-to-head each week.
                #
                # Weekly counting stat = Poisson(season_rate / 26 weeks * games_this_week)
                # Weekly rate stat (AVG, ERA, WHIP) = re-sampled with higher SD (small sample)
                #
                # Season totals from MC sim → per-week rates → weekly Poisson draws
                # Each simulated week is independent with realistic variance.
                #
                # Key insight from research:
                #   - An avg fantasy team hits ~8 HR/week (range 2-18 in a given week)
                #   - A good team gets ~6/10 cats most weeks, but swings 3-9 range
                #   - Season winner needs ~120W = 6/10 avg; playoff bubble ~110W
                #   - .500 team = exactly 100W (5/10 every week)

                GAMES_PER_WEEK = 6.5   # MLB teams play ~6-7 games/week average
                SEASON_GAMES   = 162
                HITTER_AB_WEEK = 25    # ~25 AB per hitter per week (6.5 games * ~4 AB/game)
                WEEKS_IN_YEAR  = 26    # full MLB season is ~26 scoring weeks

                # Derive per-week rates from season MC distributions
                # team_sims already contains season totals; convert to weekly rates
                def weekly_rates_from_season(team_df, cats):
                    """
                    Convert MC season distributions to weekly sampling parameters.

                    Two-layer model for counting stats:
                      Layer 1 (outer): N(mu_season, sd_mc) — draws each team's TRUE
                                       season talent (captures draft/roster quality spread)
                      Layer 2 (inner): Poisson(true_season / 26) per week — captures
                                       baseball's inherent week-to-week randomness

                    Rate stats (AVG, ERA, WHIP): Normal with empirically calibrated
                    weekly SD reflecting small-sample variance (~200 AB, ~18 IP/week).
                    """
                    rates = {}
                    for cat in cats:
                        if cat not in team_df.columns:
                            continue
                        season_vals = team_df[cat].values
                        mu_season = float(np.mean(season_vals))
                        sd_season = float(np.std(season_vals))

                        if cat in ["HR", "R", "RBI", "SB", "W", "SV", "SO"]:
                            # Outer SD = full MC season SD (NOT divided by 26!)
                            # This is the key fix: sd_season already represents
                            # season-level uncertainty, which drives team quality spread.
                            # Divide mu (not sd) by 26 to get the weekly rate per sim.
                            rates[cat] = {
                                "mu":  mu_season,          # true season total
                                "sd":  sd_season,          # season-level SD (outer layer)
                                "type": "count"
                            }
                        elif cat == "AVG":
                            # Weekly AVG: 9 hitters × ~22 AB/week ≈ 200 AB total
                            # SD = sqrt(p*(1-p)/AB) ≈ 0.031 for .262 AVG, 200 AB
                            # Use actual MC SD as floor in case it's wider
                            wk_sd_binomial = float(np.sqrt(mu_season * (1 - mu_season) / 200))
                            rates[cat] = {
                                "mu":  mu_season,
                                "sd":  max(sd_season, wk_sd_binomial, 0.025),
                                "type": "rate", "lo": 0.100, "hi": 0.600
                            }
                        elif cat == "ERA":
                            # Weekly ERA: ~18 IP sample → huge variance
                            # Empirically: team ERA swings ±1.5 ERA points week-to-week
                            rates[cat] = {
                                "mu":  mu_season,
                                "sd":  max(sd_season, 1.40),
                                "type": "rate", "lo": 0.0, "hi": 18.0
                            }
                        elif cat == "WHIP":
                            # Weekly WHIP: ~18 IP → ±0.18 realistic weekly SD
                            rates[cat] = {
                                "mu":  mu_season,
                                "sd":  max(sd_season, 0.18),
                                "type": "rate", "lo": 0.50, "hi": 3.50
                            }
                    return rates

                def sample_team_week(rates, n_weeks, n_sims):
                    """
                    Sample weekly stat arrays: shape (n_sims, n_weeks) per category.

                    Counting stats — two-layer compound model:
                      1. Draw true season total per sim: N(mu_season, sd_season)
                         This gives each of n_sims teams a slightly different talent level.
                      2. Weekly draws: Poisson(true_season / WEEKS_IN_YEAR)
                         Each week is an independent Poisson draw given that team's rate.

                    Rate stats — Normal with calibrated weekly SD (small-sample variance).
                    """
                    weekly = {}
                    for cat, r in rates.items():
                        if r["type"] == "count":
                            # Step 1: each sim's true season total (team quality)
                            true_szn = np.clip(
                                np.random.normal(r["mu"], r["sd"], size=n_sims),
                                0.0, None)
                            # Step 2: weekly lambda = true_season / 26 weeks
                            wk_lam = (true_szn / WEEKS_IN_YEAR)[:, None] * np.ones((1, n_weeks))
                            # Step 3: Poisson draw per week
                            weekly[cat] = np.random.poisson(wk_lam).astype(float)
                        else:
                            lo, hi = r.get("lo", -np.inf), r.get("hi", np.inf)
                            weekly[cat] = np.clip(
                                np.random.normal(r["mu"], r["sd"],
                                                 size=(n_sims, n_weeks)),
                                lo, hi)
                    return weekly

                # ── Build opponent pool ────────────────────────────────────
                # Each opponent is a real MC sim of a drafted team, with tiered quality.
                # Tier controls stud/depth roster mix — every team draws from the same
                # player pool but with different proportions of elite vs. depth players.
                with st.spinner("Building calibrated opponent field..."):
                    all_h_sorted = bat_rec.sort_values("composite", ascending=False)["Name"].tolist()
                    all_p_sorted = pit_rec.sort_values("composite", ascending=False)["Name"].tolist()

                    # Quality multipliers per tier (applied to season projections)
                    # Centers the opponent field so that the league average team
                    # has roughly equal numbers above and below the median.
                    TIER_QUALITY = [
                        (0.08, 0.55, 0.55, 1.15),   # Contender: +15% vs avg
                        (0.12, 0.44, 0.44, 1.08),   # Strong:    +8%
                        (0.18, 0.33, 0.33, 1.03),   # Solid:     +3%
                        (0.20, 0.22, 0.22, 1.00),   # Average:   ±0%
                        (0.17, 0.15, 0.15, 0.97),   # Below avg: -3%
                        (0.13, 0.10, 0.10, 0.92),   # Weak:      -8%
                        (0.12, 0.05, 0.05, 0.85),   # Rebuilding:-15%
                    ]

                    opp_weekly = []
                    opp_n_sims = min(N_SIM, 500)   # opponent MC precision

                    for oi in range(N_OPP):
                        # Draw tier from distribution
                        tier_roll = np.random.random()
                        cum = 0.0
                        stud_h = stud_p = 0.22
                        quality_mult = 1.0
                        for frac, sh, sp, qm in TIER_QUALITY:
                            cum += frac
                            if tier_roll <= cum:
                                stud_h, stud_p, quality_mult = sh, sp, qm
                                break

                        n_h = min(9, len(all_h_sorted))
                        n_p = min(7, len(all_p_sorted))
                        stud_pool_h = all_h_sorted[:max(int(len(all_h_sorted)*0.30), 10)]
                        stud_pool_p = all_p_sorted[:max(int(len(all_p_sorted)*0.30), 8)]
                        depth_pool_h = all_h_sorted[len(stud_pool_h):]
                        depth_pool_p = all_p_sorted[len(stud_pool_p):]

                        n_studs_h = max(1, round(n_h * stud_h))
                        n_studs_p = max(1, round(n_p * stud_p))

                        studs_h = list(np.random.choice(stud_pool_h, min(n_studs_h, len(stud_pool_h)), replace=False))
                        depth_h = list(np.random.choice(depth_pool_h, min(n_h - n_studs_h, len(depth_pool_h)), replace=False))
                        studs_p = list(np.random.choice(stud_pool_p, min(n_studs_p, len(stud_pool_p)), replace=False))
                        depth_p = list(np.random.choice(depth_pool_p, min(n_p - n_studs_p, len(depth_pool_p)), replace=False))

                        hs = tuple(studs_h + depth_h)
                        ps = tuple(studs_p + depth_p)

                        odf, _ = mc_run_simulation(
                            hs, ps, opp_n_sims,
                            mc_p["injury_pct"], mc_p["regression_pull"],
                            mc_p["platoon_boost"], mc_p.get("saber_weight", 0.5),
                            run_count=mc_p.get("run_count", 0) + 800 + oi)

                        # Apply quality multiplier to counting stats only
                        # (rate stats like ERA/WHIP scale inversely — skip them here,
                        #  their natural spread handles the quality difference)
                        odf_scaled = odf.copy()
                        for cat in ["HR","R","RBI","SB","W","SV","SO"]:
                            if cat in odf_scaled.columns:
                                odf_scaled[cat] = odf_scaled[cat] * quality_mult
                        # ERA/WHIP: better teams have lower ERA, so invert mult for them
                        for cat in ["ERA","WHIP"]:
                            if cat in odf_scaled.columns:
                                # quality_mult > 1 = better team → lower ERA/WHIP
                                inv_mult = 2.0 - quality_mult   # 1.15 → 0.85, etc.
                                odf_scaled[cat] = np.clip(odf_scaled[cat] * inv_mult, 0.5, 18.0)

                        opp_rates = weekly_rates_from_season(odf_scaled, cats_ss)
                        opp_weekly_stats = sample_team_week(opp_rates, REG_WEEKS, opp_n_sims)
                        opp_weekly.append(opp_weekly_stats)

                # ── Sample MY weekly stats ─────────────────────────────────
                with st.spinner("Sampling your weekly distributions..."):
                    my_rates = weekly_rates_from_season(team_sims, cats_ss)
                    my_weekly = sample_team_week(my_rates, REG_WEEKS, N_SIM)

                # ── Simulate N_SIM seasons ────────────────────────────────
                with st.spinner(f"Simulating {N_SIM:,} seasons × {REG_WEEKS} weeks × {N_CATS} cats..."):
                    # cat_wlt[sim, week, cat_idx] = +1 W / 0 T / -1 L
                    cat_wlt = np.zeros((N_SIM, REG_WEEKS, N_CATS), dtype=np.int8)

                    for ci, cat in enumerate(cats_ss):
                        if cat not in my_weekly:
                            continue
                        my_vals = my_weekly[cat]   # (N_SIM, REG_WEEKS)

                        # Each week, pick a random opponent from the pool
                        # (you face different opponents each week)
                        for wk in range(REG_WEEKS):
                            opp_idx = wk % N_OPP   # cycle through opponents
                            opp_wk_dict = opp_weekly[opp_idx]
                            if cat not in opp_wk_dict:
                                continue

                            n_opp_sims = opp_wk_dict[cat].shape[0]
                            opp_wk_col = opp_wk_dict[cat][:, wk % opp_wk_dict[cat].shape[1]]

                            # Match sim counts — sample with replacement if needed
                            if n_opp_sims < N_SIM:
                                idx = np.random.randint(0, n_opp_sims, size=N_SIM)
                                opp_vals = opp_wk_col[idx]
                            else:
                                opp_vals = opp_wk_col[:N_SIM]

                            my_wk = my_vals[:, wk]

                            if cat in MC_LOWER_BETTER:
                                wins = (my_wk < opp_vals).astype(np.int8)
                                ties = (my_wk == opp_vals).astype(np.int8)
                            else:
                                wins = (my_wk > opp_vals).astype(np.int8)
                                ties = (np.abs(my_wk.astype(float) - opp_vals.astype(float)) < 1e-9).astype(np.int8)

                            cat_wlt[:, wk, ci] = wins - (1 - wins - ties)

                # ── Aggregate ──────────────────────────────────────────────
                season_W = (cat_wlt ==  1).sum(axis=(1,2)).astype(int)
                season_L = (cat_wlt == -1).sum(axis=(1,2)).astype(int)
                season_T = (cat_wlt ==  0).sum(axis=(1,2)).astype(int)

                cat_win_rates  = (cat_wlt ==  1).mean(axis=(0,1))
                cat_loss_rates = (cat_wlt == -1).mean(axis=(0,1))
                cat_tie_rates  = (cat_wlt ==  0).mean(axis=(0,1))

                best_szn_idx  = int(np.argmax(season_W))
                worst_szn_idx = int(np.argmin(season_W))
                med_szn_idx   = int(np.argmin(np.abs(season_W - np.median(season_W))))

                playoff_cutoff = float(np.percentile(season_W, (1 - ss_playoff_spots/ss_league_sz)*100))
                playoff_rate   = float((season_W >= playoff_cutoff).mean())

                # ── Display ────────────────────────────────────────────────
                st.markdown("---")
                med_W  = float(np.median(season_W))
                med_L  = float(np.median(season_L))
                med_T  = float(np.median(season_T))
                p10_W  = float(np.percentile(season_W, 10))
                p90_W  = float(np.percentile(season_W, 90))
                win_pct = med_W / TOTAL_SLOTS * 100

                # Weekly rate sanity check
                with st.expander("📊 Weekly rate parameters used in simulation"):
                    rate_rows = []
                    for cat in cats_ss:
                        if cat not in my_rates: continue
                        r = my_rates[cat]
                        if r["type"] == "count":
                            rate_rows.append({
                                "Category": cat, "Type": "Counting",
                                "Avg/Week": f"{r['mu']:.2f}",
                                "Team SD": f"{r['sd']:.2f}",
                                "Projected Season": f"{r['mu']*WEEKS_IN_YEAR:.1f}"
                            })
                        else:
                            rate_rows.append({
                                "Category": cat, "Type": "Rate",
                                "Avg/Week": f"{r['mu']:.3f}",
                                "Weekly SD": f"{r['sd']:.3f}",
                                "Projected Season": "—"
                            })
                    st.dataframe(pd.DataFrame(rate_rows), hide_index=True, use_container_width=True)
                    st.caption("Counting stats use two-layer Poisson model (team quality uncertainty + weekly baseball randomness). Rate stats use Normal with inflated weekly SD to capture small-sample variance.")

                sm1, sm2, sm3, sm4, sm5 = st.columns(5)
                sm1.metric("Median Season Record",  f"{int(med_W)}-{int(med_L)}-{int(med_T)}")
                sm2.metric("Win Range (P10–P90)",   f"{int(p10_W)}–{int(p90_W)} W")
                sm3.metric("Win % (cat basis)",     f"{win_pct:.1f}%")
                sm4.metric("Avg Cat Wins / Week",   f"{med_W/REG_WEEKS:.1f} / {N_CATS}")
                sm5.metric("Est. Playoff %",        f"{playoff_rate*100:.1f}%")

                # Distribution histogram
                st.markdown("#### 📊 Season Category-Win Distribution")
                fig_wins = go.Figure()
                fig_wins.add_trace(go.Histogram(
                    x=season_W, nbinsx=50, marker_color="#4fc3f7", showlegend=False,
                    hovertemplate="Cat Wins: %{x}<br>Seasons: %{y}<extra></extra>"))
                fig_wins.add_vline(x=med_W, line_dash="dash", line_color="yellow",
                    annotation_text=f"Median {int(med_W)}W", annotation_position="top right")
                fig_wins.add_vrect(x0=p10_W, x1=p90_W,
                    fillcolor="rgba(79,195,247,0.07)", line_width=0)
                fig_wins.add_vline(x=playoff_cutoff, line_dash="dot", line_color="#21C354",
                    annotation_text=f"~Playoff ({int(playoff_cutoff)}W)",
                    annotation_font_color="#21C354")
                fig_wins.add_vline(x=100, line_dash="dash", line_color="gray",
                    opacity=0.5, annotation_text=".500 (100W)")
                fig_wins.add_vline(x=120, line_dash="dash", line_color="#FFA500",
                    opacity=0.4, annotation_text="Great (120W)")
                fig_wins.update_layout(template="plotly_dark", height=270,
                    xaxis_title=f"Total Category Wins (out of {TOTAL_SLOTS})",
                    yaxis_title="Simulated Seasons", margin=dict(l=40,r=20,t=20,b=40))
                st.plotly_chart(fig_wins, use_container_width=True)

                # Per-cat record
                st.markdown("---")
                st.markdown("#### 🏅 Per-Category Season Record")
                st.caption(f"Expected W-L-T per category across all {REG_WEEKS} weeks. 10 cats/week = 20 W per cat for a perfect team.")
                cat_rec_df = pd.DataFrame({
                    "Category":  cats_ss,
                    "Avg W":     [round(r * REG_WEEKS, 1) for r in cat_win_rates],
                    "Avg L":     [round(r * REG_WEEKS, 1) for r in cat_loss_rates],
                    "Avg T":     [round(r * REG_WEEKS, 1) for r in cat_tie_rates],
                    "Win %":     [round(r * 100, 1) for r in cat_win_rates],
                    "Assessment":[
                        "💪 Dominant" if r >= 0.65 else "✅ Solid" if r >= 0.52 else
                        "⚖️ Toss-up" if r >= 0.46 else "⚠️ Weak" if r >= 0.35 else "🚨 Punt"
                        for r in cat_win_rates]
                }).sort_values("Win %", ascending=False)

                def _cwr(val):
                    try:
                        v = float(val)
                        if v >= 65: return "color:#21C354; font-weight:bold"
                        if v >= 52: return "color:#21C354"
                        if v >= 46: return "color:#FFA500"
                        if v >= 35: return "color:#FF4B4B"
                        return "color:#FF4B4B; font-weight:bold"
                    except: return ""

                st.dataframe(cat_rec_df.style.map(_cwr, subset=["Win %"])
                    .format({"Win %":"{:.1f}%","Avg W":"{:.1f}","Avg L":"{:.1f}","Avg T":"{:.1f}"}),
                    use_container_width=True, hide_index=True)

                fig_catbar = go.Figure(go.Bar(
                    x=cat_rec_df["Category"], y=cat_rec_df["Win %"],
                    marker_color=["#21C354" if v>=52 else "#FFA500" if v>=46 else "#FF4B4B"
                                  for v in cat_rec_df["Win %"]],
                    text=[f"{v:.1f}%" for v in cat_rec_df["Win %"]], textposition="outside"))
                fig_catbar.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5,
                    annotation_text="50%")
                fig_catbar.update_layout(template="plotly_dark", height=280,
                    yaxis=dict(range=[0,105], title="Category Win %"), margin=dict(t=10,b=40))
                st.plotly_chart(fig_catbar, use_container_width=True)

                # ── Season performer breakdowns ────────────────────────────
                st.markdown("---")
                st.markdown("#### 🎭 Season Outcome Breakdowns")
                st.caption("Best, median, and worst simulated seasons — showing week-by-week scores.")

                def _build_scoreboard(sim_idx, label, color):
                    cum_W = cum_L = cum_T = 0
                    rows = []
                    for wi in range(REG_WEEKS):
                        wW = int((cat_wlt[sim_idx, wi, :] ==  1).sum())
                        wL = int((cat_wlt[sim_idx, wi, :] == -1).sum())
                        wT = int((cat_wlt[sim_idx, wi, :] ==  0).sum())
                        cum_W += wW; cum_L += wL; cum_T += wT
                        rows.append({"Week": f"Wk {wi+1}",
                                     "Score": f"{wW}-{wL}-{wT}",
                                     "Cumulative": f"{cum_W}-{cum_L}-{cum_T}"})
                    final = f"{season_W[sim_idx]}-{season_L[sim_idx]}-{season_T[sim_idx]}"
                    st.markdown(f"<span style='color:{color};font-weight:bold'>{label}: {final}</span>",
                        unsafe_allow_html=True)
                    def _sw(val):
                        try:
                            w = int(str(val).split("-")[0])
                            if w >= 7: return "color:#21C354; font-weight:bold"
                            if w >= 6: return "color:#21C354"
                            if w == 5: return "color:#FFA500"
                            return "color:#FF4B4B"
                        except: return ""
                    df = pd.DataFrame(rows)
                    st.dataframe(df.style.map(_sw, subset=["Score"]),
                        use_container_width=True, hide_index=True, height=400)

                tab_best, tab_med, tab_worst = st.tabs(["🏆 Best Season", "📊 Median Season", "💀 Worst Season"])
                with tab_best:
                    _build_scoreboard(best_szn_idx, "Best simulated season", "#21C354")
                with tab_med:
                    _build_scoreboard(med_szn_idx, "Median simulated season", "#FFA500")
                with tab_worst:
                    _build_scoreboard(worst_szn_idx, "Worst simulated season", "#FF4B4B")

                # ── Percentile table ───────────────────────────────────────
                st.markdown("---")
                st.markdown("#### 🌟 Season Outcome Percentiles")
                pcts = [10, 25, 50, 75, 90, 95]
                pct_df = pd.DataFrame({
                    "Percentile": [f"P{p}" for p in pcts],
                    "Season W":   [int(np.percentile(season_W, p)) for p in pcts],
                    "Season L":   [int(np.percentile(season_L, 100-p)) for p in pcts],
                    "Context":    ["Rough season", "Below avg", "Median", "Above avg", "Great season", "Elite season"]
                })
                perf_cols = st.columns(3)
                p90_thresh = int(np.percentile(season_W, 90))
                p10_thresh = int(np.percentile(season_W, 10))
                perf_cols[0].metric("🏆 Great Season (P90+)", f"{p90_thresh}+ W")
                perf_cols[1].metric("📊 Median Season",       f"{int(np.median(season_W))} W")
                perf_cols[2].metric("💀 Rough Season (P10-)", f"{p10_thresh}- W")

                def _pct_color(val):
                    ctx = str(val)
                    if "Elite" in ctx or "Great" in ctx: return "color:#21C354; font-weight:bold"
                    if "Above" in ctx: return "color:#21C354"
                    if "Median" in ctx: return "color:#FFA500"
                    return "color:#FF4B4B"
                st.dataframe(pct_df.style.map(_pct_color, subset=["Context"]),
                    use_container_width=True, hide_index=True)

            else:
                st.info("👆 Run your Monte Carlo sim first, then click **🏆 Run Season Simulation**.")
                st.markdown("""
                **Correct methodology — weekly stat sampling:**
                - Your season MC projections are converted to per-week rates (e.g. 30 HR/season → ~1.15 HR/week avg)
                - Each simulated week draws fresh stat totals using a **two-layer model**:
                  - Outer layer: Normal draw of your true weekly rate (captures team quality variance)
                  - Inner layer: Poisson draw given that rate (captures baseball's week-to-week randomness)
                - Rate stats (AVG, ERA, WHIP) use inflated weekly SD to reflect small-sample variance (~25 AB, ~15 IP)
                - Your weekly totals are compared directly to opponent weekly totals, category by category
                - **Reference points:** .500 = 100W | Good season = 110W | Great season = 120W+ | Elite = 130W+
                """)


# ═════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════
#  PAGE 8 — MY YAHOO LEAGUE  (OAuth2 PKCE flow for Streamlit Cloud)
# ═════════════════════════════════════════════════════════════
#
#  Flow:
#  1. App builds Yahoo OAuth URL using consumer_key from st.secrets
#  2. User clicks "Connect" → Yahoo login page opens
#  3. Yahoo redirects back with ?code=... in the URL
#  4. App catches the code via st.query_params, exchanges it for tokens
#  5. Tokens stored in st.session_state for the session
#  6. All API calls use the session access_token
#  7. Auto-refresh when token is near expiry using refresh_token
#

if page == "🏆 My Yahoo League":
    import requests as _req
    import base64 as _b64
    import hashlib as _hs
    import secrets as _sec
    import urllib.parse as _up
    import time as _time

    YAHOO_AUTH_URL    = "https://api.login.yahoo.com/oauth2/request_auth"
    YAHOO_TOKEN_URL   = "https://api.login.yahoo.com/oauth2/get_token"
    YAHOO_API_BASE    = "https://fantasysports.yahooapis.com/fantasy/v2"
    REDIRECT_URI      = "https://wilmettebaguettes-gmaswasa6yvu3ssqlb9tub.streamlit.app/"

    # Read credentials from Streamlit secrets (never from repo)
    try:
        CONSUMER_KEY    = st.secrets["yahoo"]["consumer_key"]
        CONSUMER_SECRET = st.secrets["yahoo"]["consumer_secret"]
    except Exception:
        st.error("⚠️ Yahoo credentials not found in Streamlit secrets. "
                 "Go to your app **Settings → Secrets** and add:\n\n"
                 "```toml\n[yahoo]\nconsumer_key = \"...\"\nconsumer_secret = \"...\"\n```")
        st.stop()

    # ── PKCE helpers ──────────────────────────────────────────
    def _pkce_pair():
        verifier  = _sec.token_urlsafe(64)
        challenge = _b64.urlsafe_b64encode(
            _hs.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()
        return verifier, challenge

    def _make_state(verifier: str) -> str:
        """
        Encode the PKCE verifier INTO the OAuth state parameter.
        This survives the full page reload that happens after Yahoo redirects back,
        since Streamlit Cloud resets session_state on every fresh page load.

        Format: base64url(verifier + "||" + hmac)
        HMAC prevents a malicious state parameter from injecting an arbitrary verifier.
        """
        import hmac as _hmac
        sig = _hmac.new(
            CONSUMER_SECRET.encode(),
            verifier.encode(),
            _hs.sha256
        ).hexdigest()[:16]
        raw = f"{verifier}||{sig}"
        return _b64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")

    def _decode_state(state: str) -> str | None:
        """Recover verifier from state. Returns None if signature invalid."""
        import hmac as _hmac
        try:
            # Re-pad base64
            padded = state + "=" * (-len(state) % 4)
            raw    = _b64.urlsafe_b64decode(padded).decode()
            verifier, sig = raw.split("||", 1)
            expected = _hmac.new(
                CONSUMER_SECRET.encode(),
                verifier.encode(),
                _hs.sha256
            ).hexdigest()[:16]
            if _hmac.compare_digest(sig, expected):
                return verifier
        except Exception:
            pass
        return None

    def _auth_url(state: str, challenge: str) -> str:
        params = {
            "client_id":             CONSUMER_KEY,
            "redirect_uri":          REDIRECT_URI,
            "response_type":         "code",
            "scope":                 "fspt-r",
            "state":                 state,
            "code_challenge":        challenge,
            "code_challenge_method": "S256",
        }
        return YAHOO_AUTH_URL + "?" + _up.urlencode(params)

    def _exchange_code(code: str, verifier: str) -> dict:
        """Exchange auth code for access + refresh tokens."""
        creds = _b64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()).decode()
        r = _req.post(YAHOO_TOKEN_URL, headers={
            "Authorization": f"Basic {creds}",
            "Content-Type":  "application/x-www-form-urlencoded",
        }, data={
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  REDIRECT_URI,
            "code_verifier": verifier,
        }, timeout=15)
        if r.status_code != 200:
            return {"error": f"Token exchange failed ({r.status_code}): {r.text[:400]}"}
        d = r.json()
        d["issued_at"] = _time.time()
        return d

    def _refresh_token(refresh_tok: str) -> dict:
        """Use refresh token to get a new access token."""
        creds = _b64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()).decode()
        r = _req.post(YAHOO_TOKEN_URL, headers={
            "Authorization": f"Basic {creds}",
            "Content-Type":  "application/x-www-form-urlencoded",
        }, data={
            "grant_type":    "refresh_token",
            "refresh_token": refresh_tok,
            "redirect_uri":  REDIRECT_URI,
        }, timeout=15)
        if r.status_code != 200:
            return {"error": f"Refresh failed ({r.status_code}): {r.text[:400]}"}
        d = r.json()
        d["issued_at"] = _time.time()
        return d

    def _api(path: str) -> dict:
        """Authenticated Yahoo Fantasy API call. Auto-refreshes if needed."""
        tok = st.session_state.get("yahoo_token", {})
        if not tok:
            return {"error": "not_authenticated"}

        # Refresh if within 5 min of expiry
        age = _time.time() - tok.get("issued_at", 0)
        expires_in = tok.get("expires_in", 3600)
        if age > expires_in - 300:
            new_tok = _refresh_token(tok.get("refresh_token",""))
            if "error" not in new_tok:
                st.session_state["yahoo_token"] = new_tok
                tok = new_tok
            else:
                return {"error": "Token expired and refresh failed. Please reconnect."}

        headers = {
            "Authorization": f"Bearer {tok['access_token']}",
            "Accept":        "application/json",
        }
        url = f"{YAHOO_API_BASE}{path}?format=json"
        try:
            r = _req.get(url, headers=headers, timeout=15)
            if r.status_code == 401:
                # Try one refresh on 401
                new_tok = _refresh_token(tok.get("refresh_token",""))
                if "error" not in new_tok:
                    st.session_state["yahoo_token"] = new_tok
                    headers["Authorization"] = f"Bearer {new_tok['access_token']}"
                    r = _req.get(url, headers=headers, timeout=15)
                else:
                    return {"error": "401 — please reconnect Yahoo."}
            if r.status_code != 200:
                return {"error": f"HTTP {r.status_code}: {r.text[:300]}"}
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    # ── OAuth state init ──────────────────────────────────────
    if "yahoo_oauth_state"    not in st.session_state:
        st.session_state["yahoo_oauth_state"]    = None
    if "yahoo_pkce_verifier"  not in st.session_state:
        st.session_state["yahoo_pkce_verifier"]  = None
    if "yahoo_auth_url"       not in st.session_state:
        st.session_state["yahoo_auth_url"]       = None
    if "yahoo_token"          not in st.session_state:
        st.session_state["yahoo_token"]          = None
    if "yahoo_league_key"     not in st.session_state:
        st.session_state["yahoo_league_key"]     = None
    if "yahoo_my_team_key"    not in st.session_state:
        st.session_state["yahoo_my_team_key"]    = None
    if "yahoo_my_team_name"   not in st.session_state:
        st.session_state["yahoo_my_team_name"]   = None

    # ── Catch OAuth callback code from URL ────────────────────
    qp = st.query_params
    if "code" in qp and st.session_state["yahoo_token"] is None:
        code      = qp["code"]
        ret_state = qp.get("state","")

        # Recover verifier from the state parameter itself —
        # session_state is reset on page reload so we can't rely on it here
        verifier = _decode_state(ret_state)

        if verifier:
            with st.spinner("Exchanging authorization code for tokens..."):
                tok = _exchange_code(code, verifier)
            if "error" in tok:
                st.error(f"OAuth error: {tok['error']}")
                st.query_params.clear()
            else:
                st.session_state["yahoo_token"]    = tok
                st.session_state["yahoo_auth_url"] = None  # reset so a fresh URL is made next time
                st.query_params.clear()
                st.rerun()
        else:
            st.warning("Could not verify OAuth state. Please try connecting again.")
            st.query_params.clear()

    # ── Main page UI ──────────────────────────────────────────
    st.title("🏆 My Yahoo League")

    if st.session_state["yahoo_token"] is None:
        # ── Not authenticated ─────────────────────────────────
        st.markdown("### Connect your Yahoo Fantasy account")
        st.markdown(
            "Click below to securely authorize this app with Yahoo. "
            "You'll be redirected to Yahoo's login page, then brought back here automatically."
        )
        # Generate auth URL and store PKCE state
        if "yahoo_auth_url" not in st.session_state or st.session_state.get("yahoo_auth_url") is None:
            verifier, challenge = _pkce_pair()
            # Embed verifier IN the state so it survives the page reload on redirect
            state = _make_state(verifier)
            st.session_state["yahoo_auth_url"] = _auth_url(state, challenge)

        auth_url = st.session_state["yahoo_auth_url"]

        # st.link_button opens the URL in the same tab (target="_self" equivalent)
        # This is the correct Streamlit-native way — avoids iframe/CSP issues
        st.link_button(
            "🔗 Connect Yahoo Fantasy",
            auth_url,
            type="primary",
            use_container_width=False,
        )
        st.caption(
            "Clicking above takes you to Yahoo's login page. "
            "After authorizing, Yahoo will redirect you back here automatically."
        )
        st.info(
            "💡 **Note:** After clicking, you may see Yahoo's login page open. "
            "Once you approve access, you'll be brought back to this page with "
            "your league data loaded."
        )
    else:
        # ── Authenticated ─────────────────────────────────────
        tok     = st.session_state["yahoo_token"]
        age_min = (_time.time() - tok.get("issued_at", 0)) / 60
        exp_min = tok.get("expires_in", 3600) / 60

        col_title, col_disc = st.columns([5,1])
        col_title.markdown("### ✅ Connected to Yahoo Fantasy")
        col_title.caption(f"Token age: {age_min:.0f} min / {exp_min:.0f} min — "
                          f"{'🟢 valid' if age_min < exp_min - 5 else '🟡 refreshing soon'}")
        if col_disc.button("Disconnect", key="btn_yahoo_disc"):
            for k in ["yahoo_token","yahoo_league_key","yahoo_my_team_key","yahoo_my_team_name","yahoo_auth_url"]:
                st.session_state[k] = None
            st.rerun()

        # ── League selector ───────────────────────────────────
        if st.session_state["yahoo_league_key"] is None:
            with st.spinner("Loading your leagues..."):
                lg_resp = _api("/users;use_login=1/games;game_keys=mlb/leagues")

            if "error" in lg_resp:
                st.error(lg_resp["error"])
                st.stop()

            leagues = []
            try:
                users = lg_resp["fantasy_content"]["users"]["0"]["user"]
                games = users[1]["games"]
                for gk, gv in games.items():
                    if gk == "count": continue
                    game_lgs = gv["game"][1].get("leagues", {})
                    for lk, lv in game_lgs.items():
                        if lk == "count": continue
                        lg = lv["league"][0]
                        leagues.append({
                            "key":    lg.get("league_key",""),
                            "name":   lg.get("name",""),
                            "teams":  lg.get("num_teams","?"),
                            "type":   lg.get("scoring_type",""),
                            "season": lg.get("season",""),
                            "draft":  lg.get("draft_status",""),
                        })
            except Exception as e:
                st.error(f"Could not parse leagues: {e}")
                st.stop()

            if not leagues:
                st.info("No active MLB leagues found on this Yahoo account.")
                st.stop()

            st.markdown("#### Select your league")
            for lg in leagues:
                label = f"**{lg['name']}** — {lg['season']} · {lg['teams']} teams · {lg['type']} · Draft: {lg['draft']}"
                if st.button(label, key=f"lg_{lg['key']}"):
                    st.session_state["yahoo_league_key"] = lg["key"]
                    st.session_state["yahoo_my_team_key"]  = None
                    st.session_state["yahoo_my_team_name"] = None

                    # Strategy 1: /users;use_login=1/teams — most reliable for finding MY team
                    try:
                        import requests as _rteam
                        headers_t = {"Authorization": f"Bearer {st.session_state['yahoo_token']['access_token']}",
                                     "Accept": "application/json"}
                        r_mine = _rteam.get(
                            f"https://fantasysports.yahooapis.com/fantasy/v2"
                            f"/users;use_login=1/games;game_keys=mlb/teams?format=json",
                            headers=headers_t, timeout=15)
                        if r_mine.status_code == 200:
                            ud = r_mine.json()["fantasy_content"]["users"]["0"]["user"]
                            games = ud[1]["games"]
                            for gk, gv in games.items():
                                if gk == "count": continue
                                game_teams = gv["game"][1].get("teams", {})
                                for tk, tv in game_teams.items():
                                    if tk == "count": continue
                                    t_info = tv["team"][0]
                                    t_key  = next((x["team_key"] for x in t_info if isinstance(x,dict) and "team_key" in x), None)
                                    t_name = next((x["name"] for x in t_info if isinstance(x,dict) and "name" in x), None)
                                    t_lkey = next((x["league_key"] for x in t_info if isinstance(x,dict) and "league_key" in x), None)
                                    if t_key and t_lkey == lg["key"]:
                                        st.session_state["yahoo_my_team_key"]  = t_key
                                        st.session_state["yahoo_my_team_name"] = t_name or "My Team"
                                        break
                    except Exception:
                        pass

                    # Strategy 2: loop league teams, check is_owned_by_current_login
                    if not st.session_state["yahoo_my_team_key"]:
                        try:
                            teams_resp = _api(f"/league/{lg['key']}/teams")
                            if "error" not in teams_resp:
                                all_teams = []
                                teams_raw = teams_resp["fantasy_content"]["league"][1]["teams"]
                                for k, v in teams_raw.items():
                                    if k == "count": continue
                                    t = v["team"][0]
                                    is_mine = int(next((x.get("is_owned_by_current_login", 0)
                                                    for x in t if isinstance(x,dict)), 0))
                                    t_key  = next((x["team_key"] for x in t if isinstance(x,dict) and "team_key" in x), None)
                                    t_name = next((x["name"] for x in t if isinstance(x,dict) and "name" in x), "?")
                                    all_teams.append({"key": t_key, "name": t_name, "is_mine": is_mine})
                                    if is_mine and t_key:
                                        st.session_state["yahoo_my_team_key"]  = t_key
                                        st.session_state["yahoo_my_team_name"] = t_name
                                # Store all teams for manual fallback
                                st.session_state["yahoo_all_teams"] = all_teams
                        except Exception:
                            pass

                    st.rerun()
        else:
            # ── League loaded — show tabs ─────────────────────
            league_key    = st.session_state["yahoo_league_key"]
            my_team_key   = st.session_state["yahoo_my_team_key"]
            my_team_name  = st.session_state["yahoo_my_team_name"] or "My Team"

            st.markdown(f"**League key:** `{league_key}` | **My team:** {my_team_name}")

            # If team key detection failed, show manual picker
            if not my_team_key:
                st.warning("⚠️ Could not auto-detect your team. Select it manually:")
                all_teams = st.session_state.get("yahoo_all_teams", [])
                if not all_teams:
                    # Fetch teams list now
                    try:
                        tr = _api(f"/league/{league_key}/teams")
                        if "error" not in tr:
                            all_teams = []
                            for k, v in tr["fantasy_content"]["league"][1]["teams"].items():
                                if k == "count": continue
                                t = v["team"][0]
                                all_teams.append({
                                    "key":  next((x["team_key"] for x in t if isinstance(x,dict) and "team_key" in x), ""),
                                    "name": next((x["name"] for x in t if isinstance(x,dict) and "name" in x), "?"),
                                })
                            st.session_state["yahoo_all_teams"] = all_teams
                    except Exception as e:
                        st.error(f"Could not load teams: {e}")

                if all_teams:
                    team_options = {f"{t['name']} ({t['key']})": t for t in all_teams}
                    chosen = st.selectbox("Pick your team", list(team_options.keys()), key="manual_team_sel")
                    if st.button("✅ Set as my team", key="btn_set_team"):
                        st.session_state["yahoo_my_team_key"]  = team_options[chosen]["key"]
                        st.session_state["yahoo_my_team_name"] = team_options[chosen]["name"]
                        st.rerun()
                st.stop()

            sc1, sc2 = st.columns([4,1])
            sc2.button("← Switch league", key="btn_switch_lg",
                       on_click=lambda: [
                           st.session_state.update({
                               "yahoo_league_key": None,
                               "yahoo_my_team_key": None,
                               "yahoo_my_team_name": None,
                           })
                       ])

            ytab_roster, ytab_stand, ytab_matchup, ytab_stream, ytab_leaguesim, ytab_matchupsim = st.tabs([
                "👥 My Roster", "📊 Standings", "⚔️ This Week", "🌊 Streamers",
                "🏆 League Season Sim", "⚔️ Matchup Sim"
            ])

            # ── helpers ───────────────────────────────────────
            def _enrich_hitter(name):
                m = bat_rec[bat_rec["Name"].str.lower() == name.lower()]
                if m.empty: return {}
                r = m.iloc[0]
                return {"Z": round(float(r.get("composite",0)),2),
                        "HR": int(r["HR"]) if pd.notna(r.get("HR")) else "",
                        "R":  int(r["R"])  if pd.notna(r.get("R"))  else "",
                        "RBI":int(r["RBI"])if pd.notna(r.get("RBI"))else "",
                        "SB": int(r["SB"]) if pd.notna(r.get("SB")) else "",
                        "AVG":round(float(r["AVG"]),3) if pd.notna(r.get("AVG")) else ""}

            def _enrich_pitcher(name):
                m = pit_rec[pit_rec["Name"].str.lower() == name.lower()]
                if m.empty: return {}
                r = m.iloc[0]
                return {"Z": round(float(r.get("composite",0)),2),
                        "W":  int(r["W"])   if pd.notna(r.get("W"))   else "",
                        "SV": int(r["SV"])  if pd.notna(r.get("SV"))  else "",
                        "SO": int(r["SO"])  if pd.notna(r.get("SO"))  else "",
                        "ERA":round(float(r["ERA"]),2)  if pd.notna(r.get("ERA"))  else "",
                        "WHIP":round(float(r["WHIP"]),3)if pd.notna(r.get("WHIP"))else ""}

            def _parse_players_list(raw: dict) -> list[dict]:
                players = []
                try:
                    items = raw["fantasy_content"]["league"][1]["players"]
                    for k, v in items.items():
                        if k == "count": continue
                        p0 = v["player"][0]
                        name = next((x["name"]["full"] for x in p0 if isinstance(x,dict) and "name" in x), None)
                        pos  = next((x["display_position"] for x in p0 if isinstance(x,dict) and "display_position" in x), "")
                        team = next((x["editorial_team_abbr"] for x in p0 if isinstance(x,dict) and "editorial_team_abbr" in x), "")
                        stat = next((x.get("status","") for x in p0 if isinstance(x,dict) and "status" in x), "")
                        if name:
                            players.append({"name":name,"pos":pos,"team":team,"status":stat})
                except Exception:
                    pass
                return players

            # ── MY ROSTER ─────────────────────────────────────
            with ytab_roster:
                st.markdown("#### 👥 Current Roster")
                if st.button("🔄 Refresh Roster", key="btn_roster"):
                    st.session_state.pop("yahoo_roster_data", None)

                if "yahoo_roster_data" not in st.session_state:
                    with st.spinner("Fetching roster..."):
                        r_data = _api(f"/team/{my_team_key}/roster/players")
                        st.session_state["yahoo_roster_data"] = r_data

                r_data = st.session_state["yahoo_roster_data"]
                if "error" in r_data:
                    st.error(r_data["error"])
                else:
                    try:
                        roster_players = []
                        entries = r_data["fantasy_content"]["team"][1]["roster"]["0"]["players"]
                        for k, v in entries.items():
                            if k == "count": continue
                            p0 = v["player"][0]
                            name  = next((x["name"]["full"] for x in p0 if isinstance(x,dict) and "name" in x), "?")
                            pos   = next((x["display_position"] for x in p0 if isinstance(x,dict) and "display_position" in x), "")
                            team  = next((x["editorial_team_abbr"] for x in p0 if isinstance(x,dict) and "editorial_team_abbr" in x), "")
                            stat  = next((x.get("status","") for x in p0 if isinstance(x,dict) and "status" in x), "Active")
                            sel_pos = next((x.get("selected_position",[{}])[1].get("position","") for x in v["player"] if isinstance(x,dict) and "selected_position" in x), "")
                            is_hit = any(x in pos for x in ["1B","2B","3B","SS","OF","C","Util","DH"])
                            enrich = _enrich_hitter(name) if is_hit else _enrich_pitcher(name)
                            roster_players.append({"Name":name,"Slot":sel_pos,"Pos":pos,"Team":team,
                                                    "Status":stat or "Active", **enrich})

                        rdf = pd.DataFrame(roster_players)
                        hitters  = rdf[rdf["Pos"].str.contains("1B|2B|3B|SS|OF|C|DH|Util", na=False)]
                        pitchers = rdf[~rdf["Pos"].str.contains("1B|2B|3B|SS|OF|C|DH|Util", na=False)]

                        rhc, rpc = st.columns(2)
                        with rhc:
                            st.markdown("**⚾ Hitters**")
                            h_cols = [c for c in ["Name","Slot","Pos","Team","Status","Z","HR","R","RBI","SB","AVG"] if c in hitters.columns]
                            st.dataframe(hitters[h_cols], width="stretch", hide_index=True)
                        with rpc:
                            st.markdown("**🎯 Pitchers**")
                            p_cols = [c for c in ["Name","Slot","Pos","Team","Status","Z","W","SV","SO","ERA","WHIP"] if c in pitchers.columns]
                            st.dataframe(pitchers[p_cols], width="stretch", hide_index=True)

                        # Pre-fill MC sim
                        st.markdown("---")
                        valid_h = [p["Name"] for p in roster_players
                                   if any(x in p["Pos"] for x in ["1B","2B","3B","SS","OF","C","DH","Util"])
                                   and p["Name"] in bat_all["Name"].values]
                        valid_p = [p["Name"] for p in roster_players
                                   if any(x in p["Pos"] for x in ["SP","RP","P"])
                                   and p["Name"] in pit_all["Name"].values]
                        if st.button("⚡ Load this roster into Monte Carlo Sim", key="btn_mc_prefill"):
                            st.session_state["mc_hitters"]  = valid_h
                            st.session_state["mc_pitchers"] = valid_p
                            st.success(f"✅ Loaded {len(valid_h)} hitters + {len(valid_p)} pitchers. "
                                       "Go to 🎲 Monte Carlo Sim to run projections.")
                    except Exception as e:
                        st.warning(f"Could not parse roster: {e}")
                        st.json(r_data)

            # ── STANDINGS ─────────────────────────────────────
            with ytab_stand:
                st.markdown("#### 📊 League Standings")
                if st.button("🔄 Refresh Standings", key="btn_stand"):
                    st.session_state.pop("yahoo_standings_data", None)

                if "yahoo_standings_data" not in st.session_state:
                    with st.spinner("Fetching standings..."):
                        st.session_state["yahoo_standings_data"] = _api(f"/league/{league_key}/standings")

                sd = st.session_state["yahoo_standings_data"]
                if "error" in sd:
                    st.error(sd["error"])
                else:
                    try:
                        rows = []
                        teams = sd["fantasy_content"]["league"][1]["standings"][0]["teams"]
                        for k, v in teams.items():
                            if k == "count": continue
                            t      = v["team"]
                            info   = t[0]
                            tstats = t[2]["team_standings"] if len(t) > 2 else {}
                            name   = next((x["name"] for x in info if isinstance(x,dict) and "name" in x), "?")
                            rec    = tstats.get("outcome_totals", {})
                            is_me  = name == my_team_name
                            rows.append({
                                "Rank":  tstats.get("rank","?"),
                                "Team":  ("🟢 " if is_me else "") + name,
                                "W":     rec.get("wins","?"),
                                "L":     rec.get("losses","?"),
                                "T":     rec.get("ties","?"),
                                "Win%":  rec.get("percentage","?"),
                                "Pts For":   tstats.get("points_for",""),
                                "Pts Agnst": tstats.get("points_against",""),
                            })
                        sdf = pd.DataFrame(rows)
                        try:
                            sdf["Rank"] = sdf["Rank"].astype(int)
                            sdf = sdf.sort_values("Rank")
                        except Exception: pass

                        def _rc(val):
                            try:
                                v = int(val)
                                if v == 1:  return "color:#FFD700;font-weight:bold"
                                if v <= 4:  return "color:#21C354"
                                if v <= 8:  return "color:#FFA500"
                                return "color:#FF4B4B"
                            except: return ""

                        st.dataframe(sdf.style.map(_rc, subset=["Rank"]),
                                     use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.warning(f"Could not parse standings: {e}")
                        st.json(sd)

            # ── THIS WEEK'S MATCHUP ───────────────────────────
            with ytab_matchup:
                st.markdown("#### ⚔️ Current Week Matchup")
                if st.button("🔄 Refresh Matchup", key="btn_mu"):
                    st.session_state.pop("yahoo_matchup_data", None)

                if "yahoo_matchup_data" not in st.session_state:
                    with st.spinner("Fetching matchup..."):
                        st.session_state["yahoo_matchup_data"] = _api(
                            f"/team/{my_team_key}/matchups")

                mu_d = st.session_state["yahoo_matchup_data"]
                if "error" in mu_d:
                    st.error(mu_d["error"])
                else:
                    try:
                        matchups_raw = mu_d["fantasy_content"]["team"][1]["matchups"]
                        # Find current week
                        cur_mu = None
                        for mk, mv in matchups_raw.items():
                            if mk == "count": continue
                            mu = mv.get("matchup", mv)
                            if str(mu.get("is_current_week","0")) == "1":
                                cur_mu = mu; break
                        if cur_mu is None:
                            # Fall back to first matchup
                            for mk, mv in matchups_raw.items():
                                if mk == "count": continue
                                cur_mu = mv.get("matchup", mv); break

                        if not cur_mu:
                            st.info("No matchup found for this week.")
                        else:
                            week = cur_mu.get("week","?")
                            st.markdown(f"**Week {week}**")
                            mu_teams = cur_mu["0"]["teams"]
                            summaries = []
                            for tk in ["0","1"]:
                                tm     = mu_teams[tk]["team"]
                                t_info = tm[0]
                                name   = next((x["name"] for x in t_info if isinstance(x,dict) and "name" in x),"?")
                                is_me  = name == my_team_name
                                # Stat map: stat_id → value
                                cat_vals = {}
                                if len(tm) > 1:
                                    raw_st = tm[1].get("team_stats",{}).get("stats",{})
                                    for sk, sv in raw_st.items():
                                        if sk == "count": continue
                                        s = sv.get("stat",{})
                                        cat_vals[s.get("stat_id","")] = s.get("value","—")
                                # Cat win/loss if available
                                cat_wl = {}
                                if len(tm) > 1:
                                    raw_cwl = tm[1].get("team_stats",{}).get("stat_winners",{})
                                    for sk, sv in raw_cwl.items():
                                        if sk == "count": continue
                                        w = sv.get("stat_winner",{})
                                        cat_wl[w.get("stat_id","")] = w.get("winner_team_key","")
                                summaries.append({"name":name,"is_me":is_me,
                                                  "stats":cat_vals,"winners":cat_wl})

                            # Yahoo stat_id → category name map (standard 10-cat)
                            STAT_MAP = {
                                "7":"R","12":"HR","13":"RBI","16":"SB","3":"AVG",
                                "28":"W","32":"SV","42":"SO","26":"ERA","27":"WHIP",
                            }

                            if len(summaries) == 2:
                                me  = next((s for s in summaries if s["is_me"]), summaries[0])
                                opp = next((s for s in summaries if not s["is_me"]), summaries[1])
                                my_score  = 0
                                opp_score = 0
                                mu_rows = []
                                for sid, cat in STAT_MAP.items():
                                    my_val  = me["stats"].get(sid,"—")
                                    opp_val = opp["stats"].get(sid,"—")
                                    winner_key = me["winners"].get(sid,"")
                                    if winner_key == my_team_key:
                                        result = "✅ W"; my_score += 1
                                    elif winner_key and winner_key != my_team_key:
                                        result = "❌ L"; opp_score += 1
                                    else:
                                        result = "—"
                                    mu_rows.append({"Category":cat,
                                                    f"Me ({me['name']})":my_val,
                                                    f"Opp ({opp['name']})":opp_val,
                                                    "Result":result})

                                mc1,mc2,mc3 = st.columns(3)
                                mc1.metric("My Score",  my_score)
                                mc2.metric("Opp Score", opp_score)
                                outcome = ("🏆 Winning" if my_score > opp_score else
                                           "💀 Losing"  if my_score < opp_score else "⚖️ Tied")
                                mc3.metric("Status", outcome)

                                mu_df = pd.DataFrame(mu_rows)
                                def _mu_color(val):
                                    if val == "✅ W": return "color:#21C354;font-weight:bold"
                                    if val == "❌ L": return "color:#FF4B4B;font-weight:bold"
                                    return "color:#888"
                                st.dataframe(mu_df.style.map(_mu_color, subset=["Result"]),
                                             use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.warning(f"Could not parse matchup: {e}")
                        st.json(mu_d)

            # ── STREAMERS ─────────────────────────────────────
            with ytab_stream:
                st.markdown("#### 🌊 Streaming Recommendations")
                st.caption(
                    "Free agents scored by streamer value: ERA/WHIP quality × "
                    "projected starts this week × K rate. Best adds for your H2H matchup."
                )

                stream_col1, stream_col2 = st.columns(2)
                stream_pos = stream_col1.selectbox(
                    "Position", ["SP (Starters)", "RP (Relievers)", "All Pitchers",
                                 "Hitters (Any)", "OF", "1B/3B", "2B/SS"],
                    key="stream_pos")
                stream_sort = stream_col2.selectbox(
                    "Sort by", ["Streamer Score", "ERA", "WHIP", "K", "Z-Score"],
                    key="stream_sort")

                if st.button("🔄 Find Streamers", key="btn_streamers"):
                    st.session_state.pop("yahoo_fa_data", None)

                if "yahoo_fa_data" not in st.session_state:
                    # Map position filter to Yahoo status param
                    pos_filter_map = {
                        "SP (Starters)":   "SP",
                        "RP (Relievers)":  "RP",
                        "All Pitchers":    "P",
                        "Hitters (Any)":   "B",
                        "OF":              "OF",
                        "1B/3B":           "CI",
                        "2B/SS":           "MI",
                    }
                    ypos = pos_filter_map.get(stream_pos, "P")
                    with st.spinner(f"Fetching available {stream_pos}..."):
                        # Fetch top 50 free agents sorted by % owned (most relevant)
                        fa_resp = _api(
                            f"/league/{league_key}/players"
                            f";status=FA"
                            f";position={ypos}"
                            f";sort=AR"
                            f";count=50"
                        )
                        st.session_state["yahoo_fa_data"] = fa_resp

                if "yahoo_fa_data" in st.session_state:
                    fa_d = st.session_state["yahoo_fa_data"]
                    if "error" in fa_d:
                        st.error(fa_d["error"])
                    else:
                        fa_players = _parse_players_list(fa_d)

                        if not fa_players:
                            st.info("No free agents found — season may not have started yet, "
                                    "or all players are rostered.")
                        else:
                            enriched = []
                            is_pitcher_tab = stream_pos in [
                                "SP (Starters)","RP (Relievers)","All Pitchers"]

                            for p in fa_players:
                                name = p["name"]
                                pos  = p["pos"]
                                team = p["team"]

                                if is_pitcher_tab:
                                    stats = _enrich_pitcher(name)
                                    if not stats:
                                        continue
                                    era  = float(stats.get("ERA", 4.50) or 4.50)
                                    whip = float(stats.get("WHIP", 1.30) or 1.30)
                                    k    = float(stats.get("SO", 150) or 150)
                                    z    = float(stats.get("Z", 0) or 0)
                                    # Streamer score: rewards low ERA/WHIP + high K
                                    # Normalize: ERA 2=best(1.0) ERA 6=worst(0.0)
                                    era_score  = max(0, min(1, (6.0 - era)  / 4.0))
                                    whip_score = max(0, min(1, (1.80 - whip)/ 0.80))
                                    k_score    = min(1, k / 250.0)
                                    # SP bonus (more weekly impact)
                                    sp_bonus   = 0.15 if "SP" in pos else 0.0
                                    streamer_score = round(
                                        (era_score * 0.35 + whip_score * 0.35 +
                                         k_score * 0.20 + sp_bonus + z * 0.02),
                                        3)
                                    enriched.append({
                                        "Name": name, "Pos": pos, "Team": team,
                                        "Z": stats.get("Z",""),
                                        "ERA": stats.get("ERA",""),
                                        "WHIP": stats.get("WHIP",""),
                                        "K": stats.get("SO",""),
                                        "W": stats.get("W",""),
                                        "SV": stats.get("SV",""),
                                        "Streamer Score": streamer_score,
                                        "Rec": (
                                            "🔥 Must Add"  if streamer_score >= 0.70 else
                                            "✅ Strong Add" if streamer_score >= 0.55 else
                                            "📋 Spot Start" if streamer_score >= 0.40 else
                                            "⚠️ Risky"
                                        )
                                    })
                                else:
                                    stats = _enrich_hitter(name)
                                    if not stats:
                                        continue
                                    z = float(stats.get("Z",0) or 0)
                                    enriched.append({
                                        "Name": name, "Pos": pos, "Team": team,
                                        "Z": stats.get("Z",""),
                                        "HR": stats.get("HR",""),
                                        "R":  stats.get("R",""),
                                        "RBI":stats.get("RBI",""),
                                        "SB": stats.get("SB",""),
                                        "AVG":stats.get("AVG",""),
                                        "Streamer Score": round(z, 3),
                                        "Rec": (
                                            "🔥 Must Add"   if z >= 2.0  else
                                            "✅ Strong Add"  if z >= 1.0  else
                                            "📋 Good Pickup" if z >= 0.0  else
                                            "⚠️ Risky"
                                        )
                                    })

                            if not enriched:
                                st.info("None of the available players matched our FanGraphs data.")
                            else:
                                edf = pd.DataFrame(enriched)
                                sort_col_map = {
                                    "Streamer Score": ("Streamer Score", False),
                                    "ERA":   ("ERA",   True),
                                    "WHIP":  ("WHIP",  True),
                                    "K":     ("K",     False),
                                    "Z-Score":("Z",    False),
                                }
                                sc, asc = sort_col_map.get(stream_sort, ("Streamer Score", False))
                                if sc in edf.columns:
                                    edf = edf.sort_values(sc, ascending=asc)

                                def _rec_color(val):
                                    if "Must"   in str(val): return "color:#21C354;font-weight:bold"
                                    if "Strong" in str(val): return "color:#21C354"
                                    if "Spot"   in str(val) or "Good" in str(val): return "color:#FFA500"
                                    return "color:#FF4B4B"

                                st.dataframe(
                                    edf.style.map(_rec_color, subset=["Rec"]),
                                    use_container_width=True, hide_index=True)

                                st.markdown("---")
                                st.caption(
                                    "**Streamer Score formula (pitchers):** "
                                    "ERA quality (35%) + WHIP quality (35%) + K rate (20%) + "
                                    "SP bonus (15%) + composite z (10%). "
                                    "🔥 Must Add = 0.70+ | ✅ Strong = 0.55+ | 📋 Spot = 0.40+"
                                )

            # ── LEAGUE SEASON SIM ─────────────────────────────
            with ytab_leaguesim:
                st.markdown("#### 🏆 League Season Simulator")
                st.caption(
                    "Imports all 12 teams' rosters from Yahoo, runs MC projections for each, "
                    "then simulates a full 20-week H2H season to project final standings."
                )

                lsim_col1, lsim_col2 = st.columns(2)
                lsim_n = lsim_col1.slider("Seasons to simulate", 200, 2000, 500, 100, key="lsim_n")

                if st.button("🚀 Import Rosters & Simulate Season", type="primary", key="btn_league_sim"):
                    st.session_state.pop("league_sim_results", None)

                if "league_sim_results" not in st.session_state:
                    if st.button("(results will appear here after simulation)", disabled=True, key="lsim_placeholder"):
                        pass
                else:
                    pass  # show results below

                if st.button("🚀 Import Rosters & Simulate Season", type="primary", key="btn_league_sim2") or \
                   "league_sim_results" not in st.session_state and False:
                    pass

                # Main sim button logic
                run_lsim = st.session_state.get("_run_lsim", False)
                if st.button("🚀 Run League Season Sim", type="primary", key="btn_lsim_go"):
                    import requests as _rlsim

                    headers_ls = {
                        "Authorization": f"Bearer {st.session_state['yahoo_token']['access_token']}",
                        "Accept": "application/json"
                    }

                    # Step 1: fetch all teams in league
                    with st.spinner("Fetching all team rosters..."):
                        teams_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/teams?format=json"
                        tr = _rlsim.get(teams_url, headers=headers_ls, timeout=15)
                        if tr.status_code != 200:
                            st.error(f"Could not fetch teams: HTTP {tr.status_code}")
                            st.stop()

                        all_teams_ls = []
                        try:
                            teams_raw = tr.json()["fantasy_content"]["league"][1]["teams"]
                            for k, v in teams_raw.items():
                                if k == "count": continue
                                t_info = v["team"][0]
                                t_key  = next((x["team_key"] for x in t_info if isinstance(x,dict) and "team_key" in x), None)
                                t_name = next((x["name"] for x in t_info if isinstance(x,dict) and "name" in x), f"Team {k}")
                                is_me  = t_key == my_team_key
                                all_teams_ls.append({"key": t_key, "name": t_name, "is_me": is_me})
                        except Exception as e:
                            st.error(f"Could not parse teams: {e}")
                            st.stop()

                    prog_ls = st.progress(0, text="Building team MC projections...")
                    team_mc_results = {}

                    # Step 2: fetch each team's roster and run MC sim
                    for ti, team in enumerate(all_teams_ls):
                        prog_ls.progress((ti) / len(all_teams_ls),
                                         text=f"Running MC for {team['name']} ({ti+1}/{len(all_teams_ls)})...")
                        try:
                            r_url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{team['key']}/roster/players?format=json"
                            rr = _rlsim.get(r_url, headers=headers_ls, timeout=15)
                            if rr.status_code != 200:
                                continue

                            roster_data = rr.json()
                            hitters_ls, pitchers_ls = [], []
                            entries = roster_data["fantasy_content"]["team"][1]["roster"]["0"]["players"]
                            for k, v in entries.items():
                                if k == "count": continue
                                p0   = v["player"][0]
                                name = next((x["name"]["full"] for x in p0 if isinstance(x,dict) and "name" in x), None)
                                pos  = next((x["display_position"] for x in p0 if isinstance(x,dict) and "display_position" in x), "")
                                if not name: continue
                                if any(x in pos for x in ["SP","RP","P"]):
                                    if name in pit_all["Name"].values: pitchers_ls.append(name)
                                else:
                                    if name in bat_all["Name"].values: hitters_ls.append(name)

                            if not hitters_ls and not pitchers_ls:
                                continue

                            team_sims_ls, _ = mc_run_simulation(
                                tuple(hitters_ls), tuple(pitchers_ls), 300,
                                0.12, 0.20, 0.05, 0.5,
                                run_count=abs(hash(team["key"])) % 100000
                            )
                            team_mc_results[team["name"]] = {
                                "sims": team_sims_ls,
                                "is_me": team["is_me"],
                                "hitters": hitters_ls,
                                "pitchers": pitchers_ls,
                            }
                        except Exception as e:
                            team_mc_results[team["name"]] = {"error": str(e), "is_me": team["is_me"]}

                    prog_ls.progress(1.0, text="Running season simulation...")

                    # Step 3: simulate seasons
                    REG_WEEKS_LS = 20
                    N_SIM_LS     = lsim_n
                    WEEKS_LS     = 26
                    cats_ls = ["HR","R","RBI","SB","AVG","W","SV","SO","ERA","WHIP"]
                    MC_LOWER = {"ERA","WHIP"}

                    def _wk_rates(team_df, cats):
                        rates = {}
                        for cat in cats:
                            if cat not in team_df.columns: continue
                            mu = float(team_df[cat].mean())
                            sd = float(team_df[cat].std())
                            if cat in ["HR","R","RBI","SB","W","SV","SO"]:
                                rates[cat] = {"mu": mu, "sd": sd, "type": "count"}
                            elif cat == "AVG":
                                rates[cat] = {"mu": mu, "sd": max(sd, 0.025), "type": "rate", "lo": 0.1, "hi": 0.6}
                            elif cat == "ERA":
                                rates[cat] = {"mu": mu, "sd": max(sd, 1.4), "type": "rate", "lo": 0.0, "hi": 18.0}
                            elif cat == "WHIP":
                                rates[cat] = {"mu": mu, "sd": max(sd, 0.18), "type": "rate", "lo": 0.5, "hi": 3.5}
                        return rates

                    def _sample_wk(rates, n_weeks, n_sims):
                        weekly = {}
                        for cat, r in rates.items():
                            if r["type"] == "count":
                                true_szn = np.clip(np.random.normal(r["mu"], r["sd"], n_sims), 0, None)
                                lam = (true_szn / WEEKS_LS)[:, None] * np.ones((1, n_weeks))
                                weekly[cat] = np.random.poisson(lam).astype(float)
                            else:
                                lo, hi = r.get("lo", -np.inf), r.get("hi", np.inf)
                                weekly[cat] = np.clip(
                                    np.random.normal(r["mu"], r["sd"], (n_sims, n_weeks)), lo, hi)
                        return weekly

                    # Build weekly distributions per team
                    team_weekly = {}
                    valid_teams = [t for t in all_teams_ls
                                   if t["name"] in team_mc_results
                                   and "sims" in team_mc_results[t["name"]]]

                    for team in valid_teams:
                        rates = _wk_rates(team_mc_results[team["name"]]["sims"], cats_ls)
                        team_weekly[team["name"]] = _sample_wk(rates, REG_WEEKS_LS, N_SIM_LS)

                    # Simulate season: each team vs a random opponent each week
                    team_names = list(team_weekly.keys())
                    n_teams    = len(team_names)
                    # W/L/T records: [team_idx, sim] → total cat wins
                    team_cat_wins = {t: np.zeros(N_SIM_LS, dtype=int) for t in team_names}
                    team_cat_loss = {t: np.zeros(N_SIM_LS, dtype=int) for t in team_names}

                    for sim in range(N_SIM_LS):
                        # Random schedule: each week pair teams
                        for wk in range(REG_WEEKS_LS):
                            shuffled = np.random.permutation(team_names)
                            for i in range(0, n_teams - 1, 2):
                                t1, t2 = shuffled[i], shuffled[i+1]
                                if t1 not in team_weekly or t2 not in team_weekly:
                                    continue
                                for cat in cats_ls:
                                    if cat not in team_weekly[t1] or cat not in team_weekly[t2]:
                                        continue
                                    v1 = team_weekly[t1][cat][sim, wk]
                                    v2 = team_weekly[t2][cat][sim, wk]
                                    lower = cat in MC_LOWER
                                    if lower:
                                        w1 = v1 < v2; w2 = v2 < v1
                                    else:
                                        w1 = v1 > v2; w2 = v2 > v1
                                    if w1:
                                        team_cat_wins[t1][sim] += 1
                                        team_cat_loss[t2][sim] += 1
                                    elif w2:
                                        team_cat_wins[t2][sim] += 1
                                        team_cat_loss[t1][sim] += 1

                    prog_ls.empty()

                    # Build results
                    standings_rows = []
                    for tname in team_names:
                        med_w  = int(np.median(team_cat_wins[tname]))
                        med_l  = int(np.median(team_cat_loss[tname]))
                        p10_w  = int(np.percentile(team_cat_wins[tname], 10))
                        p90_w  = int(np.percentile(team_cat_wins[tname], 90))
                        is_me  = next((t["is_me"] for t in all_teams_ls if t["name"]==tname), False)
                        standings_rows.append({
                            "Team":       ("🟢 " if is_me else "") + tname,
                            "Median W":   med_w,
                            "Median L":   med_l,
                            "Win %":      round(med_w / (med_w + med_l) * 100, 1) if (med_w+med_l) > 0 else 0,
                            "Range":      f"{p10_w}–{p90_w}",
                            "Playoff %":  0,  # computed below
                        })

                    # Compute playoff probabilities (top 4 in each sim)
                    PLAYOFF_SPOTS = 4
                    playoff_counts = {t: 0 for t in team_names}
                    for sim in range(N_SIM_LS):
                        sim_wins = [(t, team_cat_wins[t][sim]) for t in team_names]
                        sim_wins.sort(key=lambda x: -x[1])
                        for t, _ in sim_wins[:PLAYOFF_SPOTS]:
                            playoff_counts[t] += 1

                    for row in standings_rows:
                        tname_clean = row["Team"].replace("🟢 ", "")
                        row["Playoff %"] = round(playoff_counts.get(tname_clean, 0) / N_SIM_LS * 100, 1)

                    standings_rows.sort(key=lambda x: -x["Median W"])

                    # Category strength table
                    cat_strength = {}
                    for tname in team_names:
                        if "sims" not in team_mc_results[tname]: continue
                        sims_df = team_mc_results[tname]["sims"]
                        cat_strength[tname] = {
                            cat: round(float(sims_df[cat].mean()), 2)
                            for cat in cats_ls if cat in sims_df.columns
                        }

                    st.session_state["league_sim_results"] = {
                        "standings": standings_rows,
                        "cat_strength": cat_strength,
                        "my_team": my_team_name,
                        "n_sim": N_SIM_LS,
                    }
                    st.rerun()

                # Display results
                if "league_sim_results" in st.session_state:
                    res = st.session_state["league_sim_results"]
                    st.markdown(f"*{res['n_sim']:,} simulated seasons — based on current Yahoo rosters*")
                    st.markdown("---")

                    # Standings table
                    st.markdown("#### 📊 Projected Final Standings")
                    sdf = pd.DataFrame(res["standings"])

                    def _playoff_color(val):
                        try:
                            v = float(val)
                            if v >= 70: return "color:#21C354;font-weight:bold"
                            if v >= 50: return "color:#21C354"
                            if v >= 30: return "color:#FFA500"
                            return "color:#FF4B4B"
                        except: return ""

                    def _team_color(val):
                        if "🟢" in str(val): return "color:#4fc3f7;font-weight:bold"
                        return ""

                    st.dataframe(
                        sdf.style
                           .map(_team_color, subset=["Team"])
                           .map(_playoff_color, subset=["Playoff %"])
                           .format({"Win %": "{:.1f}%", "Playoff %": "{:.1f}%"}),
                        use_container_width=True, hide_index=True
                    )

                    # Category strength heatmap
                    st.markdown("---")
                    st.markdown("#### 🔥 Category Strength by Team")
                    cs = res["cat_strength"]
                    if cs:
                        cats_order = ["HR","R","RBI","SB","AVG","W","SV","SO","ERA","WHIP"]
                        cs_rows = []
                        for tname, cat_vals in cs.items():
                            is_me = tname == res["my_team"]
                            row = {"Team": ("🟢 " if is_me else "") + tname}
                            row.update({c: cat_vals.get(c, "") for c in cats_order if c in cat_vals})
                            cs_rows.append(row)
                        cs_rows.sort(key=lambda x: x.get("HR", 0), reverse=True)
                        cs_df = pd.DataFrame(cs_rows)
                        num_cols = [c for c in cats_order if c in cs_df.columns]
                        st.dataframe(
                            cs_df.style.background_gradient(subset=num_cols, cmap="RdYlGn"),
                            use_container_width=True, hide_index=True
                        )

                    # Per-opponent projected record
                    st.markdown("---")
                    st.markdown("#### ⚔️ My Projected Record vs Each Opponent")
                    st.caption("Expected W-L-T across all simulated seasons when facing each opponent.")
                    my_name_ls = res["my_team"]
                    if my_name_ls in team_weekly:
                        opp_records = []
                        for opp_name_ls in team_names:
                            if opp_name_ls == my_name_ls: continue
                            # Re-simulate just my team vs this one opponent
                            N_OPP_SIM = min(lsim_n, 1000)
                            # Simulate all 20 weeks vs this opponent
                            # my_cats_won[sim] = total category wins across all 20 weeks
                            my_cats_won  = np.zeros(N_OPP_SIM, dtype=int)
                            opp_cats_won = np.zeros(N_OPP_SIM, dtype=int)
                            for cat in cats_ls:
                                if cat not in team_weekly.get(my_name_ls, {}) or                                    cat not in team_weekly.get(opp_name_ls, {}): continue
                                # Shape: (N_OPP_SIM, REG_WEEKS_LS)
                                my_all  = team_weekly[my_name_ls][cat][:N_OPP_SIM, :]   # all 20 weeks
                                opp_all = team_weekly[opp_name_ls][cat][:N_OPP_SIM, :]
                                lower   = cat in MC_LOWER
                                if lower:
                                    my_cats_won  += (my_all < opp_all).sum(axis=1)
                                    opp_cats_won += (my_all > opp_all).sum(axis=1)
                                else:
                                    my_cats_won  += (my_all > opp_all).sum(axis=1)
                                    opp_cats_won += (my_all < opp_all).sum(axis=1)

                            # Median season record across all sims
                            med_w = int(np.median(my_cats_won))
                            med_l = int(np.median(opp_cats_won))
                            med_t = REG_WEEKS_LS * len(cats_ls) - med_w - med_l
                            win_pct_vs = med_w / (med_w + med_l) * 100 if (med_w+med_l) > 0 else 50
                            opp_records.append({
                                "Opponent":   opp_name_ls,
                                "Cat W-L-T":  f"{med_w}–{med_l}–{max(0,med_t)}",
                                "Total Slots":f"{REG_WEEKS_LS * len(cats_ls)}",
                                "My Win %":   round(win_pct_vs, 1),
                                "Result":    ("🔥 Easy W" if win_pct_vs >= 65 else
                                              "✅ Likely W" if win_pct_vs >= 55 else
                                              "⚖️ Toss-up" if win_pct_vs >= 45 else
                                              "⚠️ Tough L" if win_pct_vs >= 35 else
                                              "🚨 Hard L"),
                            })

                        opp_records.sort(key=lambda x: -x["My Win %"])
                        odf = pd.DataFrame(opp_records)

                        def _opp_result_color(val):
                            v = str(val)
                            if "Easy"   in v: return "color:#21C354;font-weight:bold"
                            if "Likely" in v: return "color:#21C354"
                            if "Toss"   in v: return "color:#FFA500"
                            if "Tough"  in v: return "color:#FFA500"
                            return "color:#FF4B4B;font-weight:bold"

                        def _owin_color(val):
                            try:
                                v = float(val)
                                if v >= 65: return "color:#21C354;font-weight:bold"
                                if v >= 55: return "color:#21C354"
                                if v >= 45: return "color:#FFA500"
                                return "color:#FF4B4B"
                            except: return ""

                        st.dataframe(
                            odf.style
                               .map(_owin_color,      subset=["My Win %"])
                               .map(_opp_result_color, subset=["Result"])
                               .format({"My Win %": "{:.1f}%"}),
                            use_container_width=True, hide_index=True
                        )

                    if st.button("🔄 Re-run Simulation", key="btn_lsim_rerun"):
                        st.session_state.pop("league_sim_results", None)
                        st.rerun()

            # ── MATCHUP SIM ───────────────────────────────────
            with ytab_matchupsim:
                st.markdown("#### ⚔️ Current Matchup Simulator")
                st.caption(
                    "Fetches your current week's opponent roster and simulates "
                    "the 10-category matchup 1,000 times to show win probabilities per category "
                    "and score distribution."
                )

                msim_n = st.slider("Matchup simulations", 500, 5000, 1000, 500, key="msim_n")

                if st.button("🎲 Simulate This Week's Matchup", type="primary", key="btn_msim"):
                    import requests as _rmsim

                    headers_ms = {
                        "Authorization": f"Bearer {st.session_state['yahoo_token']['access_token']}",
                        "Accept": "application/json"
                    }

                    with st.spinner("Fetching current matchup..."):
                        # Get current week matchup to find opponent
                        mu_url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{my_team_key}/matchups?format=json"
                        mu_r   = _rmsim.get(mu_url, headers=headers_ms, timeout=15)

                        opp_team_key  = None
                        opp_team_name = "Opponent"
                        week_num      = "?"

                        if mu_r.status_code == 200:
                            try:
                                matchups = mu_r.json()["fantasy_content"]["team"][1]["matchups"]
                                for mk, mv in matchups.items():
                                    if mk == "count": continue
                                    mu = mv.get("matchup", mv)
                                    if str(mu.get("is_current_week","0")) == "1" or mk == "0":
                                        week_num = mu.get("week","?")
                                        mu_teams = mu["0"]["teams"]
                                        for tk in ["0","1"]:
                                            t_info = mu_teams[tk]["team"][0]
                                            t_key  = next((x["team_key"] for x in t_info if isinstance(x,dict) and "team_key" in x), None)
                                            t_name = next((x["name"] for x in t_info if isinstance(x,dict) and "name" in x), "?")
                                            if t_key and t_key != my_team_key:
                                                opp_team_key  = t_key
                                                opp_team_name = t_name
                                        break
                            except Exception as e:
                                st.warning(f"Could not parse matchup: {e}")

                        if not opp_team_key:
                            st.error("Could not find current opponent. Season may not have started yet.")
                            st.stop()

                    st.markdown(f"**Week {week_num}:** {my_team_name} vs **{opp_team_name}**")

                    def _fetch_roster_names(team_key):
                        hitters, pitchers = [], []
                        try:
                            r = _rmsim.get(
                                f"https://fantasysports.yahooapis.com/fantasy/v2/team/{team_key}/roster/players?format=json",
                                headers=headers_ms, timeout=15)
                            if r.status_code != 200: return hitters, pitchers
                            entries = r.json()["fantasy_content"]["team"][1]["roster"]["0"]["players"]
                            for k, v in entries.items():
                                if k == "count": continue
                                p0   = v["player"][0]
                                name = next((x["name"]["full"] for x in p0 if isinstance(x,dict) and "name" in x), None)
                                pos  = next((x["display_position"] for x in p0 if isinstance(x,dict) and "display_position" in x), "")
                                if not name: continue
                                if any(x in pos for x in ["SP","RP","P"]):
                                    if name in pit_all["Name"].values: pitchers.append(name)
                                else:
                                    if name in bat_all["Name"].values: hitters.append(name)
                        except Exception:
                            pass
                        return hitters, pitchers

                    with st.spinner(f"Loading rosters for both teams..."):
                        my_h_ms,  my_p_ms  = _fetch_roster_names(my_team_key)
                        opp_h_ms, opp_p_ms = _fetch_roster_names(opp_team_key)

                    if not my_h_ms and not my_p_ms:
                        st.warning("Could not load your roster from FanGraphs data. Names may not match.")
                    if not opp_h_ms and not opp_p_ms:
                        st.warning(f"Could not load {opp_team_name}'s roster from FanGraphs data.")

                    with st.spinner("Running MC projections for both rosters..."):
                        my_sims,  _ = mc_run_simulation(
                            tuple(my_h_ms),  tuple(my_p_ms),  500,
                            0.12, 0.20, 0.05, 0.5, run_count=1111)
                        opp_sims, _ = mc_run_simulation(
                            tuple(opp_h_ms), tuple(opp_p_ms), 500,
                            0.12, 0.20, 0.05, 0.5, run_count=2222)

                    with st.spinner(f"Simulating {msim_n:,} matchup weeks..."):
                        cats_ms  = ["HR","R","RBI","SB","AVG","W","SV","SO","ERA","WHIP"]
                        LOWER_MS = {"ERA","WHIP"}
                        WEEKS_MS = 26

                        def _weekly_single(team_df, cats, n):
                            result = {}
                            for cat in cats:
                                if cat not in team_df.columns: continue
                                mu = float(team_df[cat].mean())
                                sd = float(team_df[cat].std())
                                if cat in ["HR","R","RBI","SB","W","SV","SO"]:
                                    true_szn = np.clip(np.random.normal(mu, sd, n), 0, None)
                                    result[cat] = np.random.poisson(true_szn / WEEKS_MS).astype(float)
                                elif cat == "AVG":
                                    result[cat] = np.clip(np.random.normal(mu, max(sd,0.025), n), 0.1, 0.6)
                                elif cat == "ERA":
                                    result[cat] = np.clip(np.random.normal(mu, max(sd,1.4), n), 0.0, 18.0)
                                elif cat == "WHIP":
                                    result[cat] = np.clip(np.random.normal(mu, max(sd,0.18), n), 0.5, 3.5)
                            return result

                        N = msim_n
                        my_wk  = _weekly_single(my_sims,  cats_ms, N)
                        opp_wk = _weekly_single(opp_sims, cats_ms, N)

                        cat_results = {}
                        score_dist  = np.zeros(11, dtype=int)  # 0-10 my cats won

                        for sim in range(N):
                            my_score = 0
                            for cat in cats_ms:
                                if cat not in my_wk or cat not in opp_wk: continue
                                mv = my_wk[cat][sim]; ov = opp_wk[cat][sim]
                                if cat in LOWER_MS:
                                    win = mv < ov; tie = abs(mv-ov) < 0.001
                                else:
                                    win = mv > ov; tie = abs(mv-ov) < 0.001
                                if cat not in cat_results:
                                    cat_results[cat] = {"w":0,"l":0,"t":0}
                                if win:
                                    cat_results[cat]["w"] += 1; my_score += 1
                                elif tie:
                                    cat_results[cat]["t"] += 1
                                else:
                                    cat_results[cat]["l"] += 1
                            score_dist[my_score] += 1

                    # ── Display results ──────────────────────────────
                    st.markdown("---")

                    # Overall win probability (win = score 6+ out of 10)
                    overall_win  = sum(score_dist[6:]) / N * 100
                    overall_loss = sum(score_dist[:5]) / N * 100
                    overall_tie  = score_dist[5] / N * 100

                    color_win = "#21C354" if overall_win > 55 else "#FFA500" if overall_win > 45 else "#FF4B4B"
                    outcome   = ("🏆 Projected WIN" if overall_win > 55 else
                                 "⚖️ Toss-up"      if overall_win > 45 else
                                 "💀 Projected LOSS")
                    st.markdown(
                        f"<h2 style='text-align:center;color:{color_win}'>{outcome}</h2>",
                        unsafe_allow_html=True)

                    oc1, oc2, oc3 = st.columns(3)
                    oc1.metric("My Win Probability",  f"{overall_win:.1f}%",
                               delta=f"{overall_win-50:+.1f}% vs coin flip")
                    oc2.metric("Toss-up",             f"{overall_tie:.1f}%")
                    oc3.metric("Opp Win Probability", f"{overall_loss:.1f}%")

                    # Per-category win % — the core output
                    st.markdown("---")
                    st.markdown(f"#### 🏅 Category Win Probabilities vs {opp_team_name}")
                    cat_rows = []
                    for cat in cats_ms:
                        if cat not in cat_results: continue
                        cr    = cat_results[cat]
                        w_pct = cr["w"] / N * 100
                        l_pct = cr["l"] / N * 100
                        t_pct = cr["t"] / N * 100

                        # Weekly projected stat (median of weekly draws)
                        my_proj  = float(np.median(my_wk[cat]))  if cat in my_wk  else 0
                        opp_proj = float(np.median(opp_wk[cat])) if cat in opp_wk else 0
                        if cat == "AVG":
                            proj_str = f"{my_proj:.3f} vs {opp_proj:.3f}"
                        elif cat in ["ERA","WHIP"]:
                            proj_str = f"{my_proj:.2f} vs {opp_proj:.2f}"
                        else:
                            proj_str = f"{my_proj:.1f} vs {opp_proj:.1f}"

                        edge = ("🔥 Strong win"  if w_pct >= 65 else
                                "✅ Likely win"   if w_pct >= 55 else
                                "⚖️ Toss-up"      if w_pct >= 45 else
                                "⚠️ Likely loss"  if w_pct >= 35 else
                                "🚨 Losing badly")

                        cat_rows.append({
                            "Category":          cat,
                            "My Win %":          round(w_pct, 1),
                            "Opp Win %":         round(l_pct, 1),
                            "Tie %":             round(t_pct, 1),
                            "Avg/Wk (Me / Opp)": proj_str,
                            "Edge":              edge,
                        })

                    cdf = pd.DataFrame(cat_rows)

                    def _edge_col(val):
                        v = str(val)
                        if "Strong"  in v: return "color:#21C354;font-weight:bold"
                        if "Likely win" in v: return "color:#21C354"
                        if "Toss"    in v: return "color:#FFA500"
                        if "Likely loss" in v: return "color:#FFA500"
                        return "color:#FF4B4B;font-weight:bold"

                    def _wpct_col(val):
                        try:
                            v = float(val)
                            if v >= 65: return "color:#21C354;font-weight:bold"
                            if v >= 55: return "color:#21C354"
                            if v >= 45: return "color:#FFA500"
                            return "color:#FF4B4B"
                        except: return ""

                    st.dataframe(
                        cdf.style
                           .map(_wpct_col, subset=["My Win %"])
                           .map(_edge_col,  subset=["Edge"])
                           .format({"My Win %": "{:.1f}%",
                                    "Opp Win %": "{:.1f}%",
                                    "Tie %": "{:.1f}%"}),
                        use_container_width=True, hide_index=True
                    )

                    # Expected score summary
                    exp_wins = sum(cr["w"]/N for cr in cat_results.values())
                    exp_loss = sum(cr["l"]/N for cr in cat_results.values())
                    st.caption(
                        f"Expected score: **{exp_wins:.1f} – {exp_loss:.1f}** "
                        f"| Simulated {N:,} matchups"
                    )

                    # Roster summary
                    st.markdown("---")
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        st.markdown(f"**My Roster ({my_team_name})**")
                        if my_h_ms:  st.caption("Hitters: "  + ", ".join(my_h_ms))
                        if my_p_ms:  st.caption("Pitchers: " + ", ".join(my_p_ms))
                        if not my_h_ms and not my_p_ms:
                            st.warning("No players matched FanGraphs data")
                    with rc2:
                        st.markdown(f"**{opp_team_name}**")
                        if opp_h_ms: st.caption("Hitters: "  + ", ".join(opp_h_ms))
                        if opp_p_ms: st.caption("Pitchers: " + ", ".join(opp_p_ms))
                        if not opp_h_ms and not opp_p_ms:
                            st.warning("No players matched FanGraphs data")

                else:
                    st.info("Click **🎲 Simulate This Week's Matchup** to run the simulation. "
                            "Requires the season to have started and a current week matchup.")
