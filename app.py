import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Nephro-Sim", layout="wide")
st.title("🔬 Advanced Nephro-Sim: Transport & Regulation")

# --- SIDEBAR ---
st.sidebar.header("Patient Scenario")

scenario = st.sidebar.radio(
    "Select Condition:",
    ("Normal Physiology",
     "Acetazolamide (Proximal)",
     "Vomiting (Metabolic Alkalosis)",
     "Dehydration",
     "Furosemide (Loop)",
     "Aldactone (Receptor Antagonist)",
     "Furosemide + Aldactone (Combination)",
     "Liddle's Syndrome",
     "Amiloride (Channel Blocker)",
     "PHA Type 1 (ENaC Inactivity)")
)

# --- SCENARIO DEFINITIONS ---
# Each scenario specifies the physiologic state that emerges.
#   aldo         : plasma aldosterone, ng/dL (normal ~5-15)
#   mr_efficacy  : 0 (MR blocked) -> 1 (normal MR signaling)
#   delivery     : relative distal Na+ delivery (1.0 = normal); drives blue-dot count
#   pore_block   : 0 (ENaC open) -> ~1 (ENaC plugged at pore)
#   flux         : effective Na+ reabsorption rate at CD; drives ENaC / ROMK arrows
#   systolic / diastolic : mmHg
#   k_val        : serum K+, mEq/L

SCENARIOS = {
    "Normal Physiology": {
        "aldo": 12, "mr_efficacy": 1.0, "delivery": 1.0, "pore_block": 0.0,
        "flux": 1.0, "systolic": 120, "diastolic": 76, "k_val": 4.0
    },
    "Acetazolamide (Proximal)": {
        # PCT CA inhibition -> ↑ distal Na delivery -> ↑ ENaC activity -> K+ wasting
        # Mild diuresis -> mild volume contraction -> mild aldo bump.
        "aldo": 18, "mr_efficacy": 1.0, "delivery": 1.8, "pore_block": 0.0,
        "flux": 1.8, "systolic": 112, "diastolic": 72, "k_val": 3.3
    },
    "Vomiting (Metabolic Alkalosis)": {
        # Chronic vomiting -> volume depletion -> hypotension + 2° hyperaldosteronism.
        # K+ losses driven by HCO3- as non-reabsorbable anion + aldo.
        "aldo": 65, "mr_efficacy": 1.0, "delivery": 1.1, "pore_block": 0.0,
        "flux": 1.7, "systolic": 100, "diastolic": 65, "k_val": 3.0
    },
    "Dehydration": {
        # Volume contraction -> high aldo BUT ↓ distal Na delivery.
        # Limited substrate at CD -> aldosterone "escape" for K+: serum K+ stays normal.
        "aldo": 75, "mr_efficacy": 1.0, "delivery": 0.5, "pore_block": 0.0,
        "flux": 0.8, "systolic": 95, "diastolic": 65, "k_val": 4.2
    },
    "Furosemide (Loop)": {
        # NKCC2 block -> massive ↑ distal Na delivery + volume loss.
        # Severe K+ wasting; BP falls (was previously, incorrectly, rising).
        "aldo": 50, "mr_efficacy": 1.0, "delivery": 3.5, "pore_block": 0.0,
        "flux": 3.5, "systolic": 105, "diastolic": 70, "k_val": 2.9
    },
    "Aldactone (Receptor Antagonist)": {
        # Competitive MR block -> ENaC/ROMK expression falls -> hyperkalemia, mild BP ↓.
        "aldo": 85, "mr_efficacy": 0.0, "delivery": 1.0, "pore_block": 0.0,
        "flux": 0.2, "systolic": 112, "diastolic": 72, "k_val": 5.5
    },
    "Furosemide + Aldactone (Combination)": {
        # Loop diuresis + MR block: K+ preserved despite massive delivery.
        "aldo": 90, "mr_efficacy": 0.0, "delivery": 3.5, "pore_block": 0.0,
        "flux": 0.6, "systolic": 105, "diastolic": 68, "k_val": 4.3
    },
    "Liddle's Syndrome": {
        # Constitutively active ENaC -> Na retention -> HTN, K+ wasting, SUPPRESSED aldo.
        "aldo": 1.0, "mr_efficacy": 1.0, "delivery": 1.0, "pore_block": 0.0,
        "flux": 4.0, "systolic": 158, "diastolic": 98, "k_val": 2.8
    },
    "Amiloride (Channel Blocker)": {
        # Pore-level ENaC block -> no Na reabsorption / no K+ secretion -> hyperkalemia.
        "aldo": 50, "mr_efficacy": 1.0, "delivery": 1.0, "pore_block": 0.95,
        "flux": 0.2, "systolic": 110, "diastolic": 72, "k_val": 5.8
    },
    "PHA Type 1 (ENaC Inactivity)": {
        # Loss-of-function ENaC: aldo sky-high, MR fully active, but channel broken.
        # Severe salt wasting -> hypotension + severe hyperkalemia (aldo resistance).
        "aldo": 95, "mr_efficacy": 1.0, "delivery": 1.0, "pore_block": 0.0,
        "flux": 0.0, "systolic": 88, "diastolic": 55, "k_val": 6.5
    },
}

s = SCENARIOS[scenario]
serum_aldo  = s["aldo"]
mr_efficacy = s["mr_efficacy"]
delivery    = s["delivery"]
pore_block  = s["pore_block"]
final_flux  = s["flux"]
systolic    = s["systolic"]
diastolic   = s["diastolic"]
k_val       = s["k_val"]


# --- VISUALIZATION ---
def draw_dashboard(scen, flux, deliv, aldo, mr_eff, systolic, diastolic, k_val):
    fig = plt.figure(figsize=(12, 10))

    ax_nephron = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    ax_cell    = plt.subplot2grid((3, 2), (1, 0), rowspan=2)
    ax_data    = plt.subplot2grid((3, 2), (1, 1), rowspan=2)

    # === MACRO NEPHRON ===
    ax_nephron.set_title("Nephron Overview", fontweight='bold')
    ax_nephron.set_xlim(0, 12)
    ax_nephron.set_ylim(0, 5)
    ax_nephron.axis('off')

    lw = 12
    ax_nephron.plot([1, 3], [4, 4], color='#FF9F40', lw=lw, solid_capstyle='round')           # PCT
    ax_nephron.plot([3, 4, 4, 5], [4, 1, 1, 4], color='#A0A0A0', lw=lw, solid_capstyle='round')  # Loop
    ax_nephron.plot([5, 7], [4, 4], color='#4BC0C0', lw=lw, solid_capstyle='round')           # DCT
    ax_nephron.plot([7, 8, 8, 9], [4, 4, 1, 1], color='#FFD700', lw=lw*1.5, solid_capstyle='round')  # CD

    # Na+ Dots reflect actual distal Na delivery
    dot_count = int(12 * deliv)
    dot_count = min(60, dot_count)
    half = max(1, int(dot_count/2) + 1)
    xf = np.linspace(7, 8, half)
    yf = np.full_like(xf, 4)
    ax_nephron.scatter(xf, yf, color='blue', s=15, zorder=10)
    xv = np.full(half, 8)
    yv = np.linspace(4, 1, half)
    ax_nephron.scatter(xv, yv, color='blue', s=15, zorder=10)

    # Labels
    ax_nephron.text(2, 4.4, "PCT", ha='center', fontsize=8, weight='bold')
    ax_nephron.text(2, 4, "NHE3", ha='center', va='center', fontsize=6, color='white')
    ax_nephron.text(4, 0.5, "Loop", ha='center', fontsize=8)
    ax_nephron.text(4, 1.5, "NKCC2", ha='center', va='center', fontsize=6)
    ax_nephron.text(6, 4.4, "DCT", ha='center', fontsize=8, weight='bold')
    ax_nephron.text(8, 4.4, "CD", ha='center', fontsize=8, weight='bold', color='#B8860B')

    if deliv > 2.0:
        ax_nephron.text(8.5, 3.5, "High Luminal\nNa+", color='blue', fontsize=8, ha='left')
    elif deliv < 0.7:
        ax_nephron.text(8.5, 3.5, "Low Luminal\nNa+", color='blue', fontsize=8, ha='left')

    # === MICRO CELL ===
    ax_cell.set_title("Principal Cell (Zoom)", fontweight='bold')
    ax_cell.set_xlim(0, 10)
    ax_cell.set_ylim(0, 10)
    ax_cell.axis('off')

    ax_cell.add_patch(patches.Rectangle((0, 0), 3, 10, fc='#E0F7FA', alpha=0.5))
    ax_cell.text(1.5, 9.5, "LUMEN", ha='center', color='#006064', weight='bold')
    ax_cell.add_patch(patches.Rectangle((7, 0), 3, 10, fc='#FFEBEE', alpha=0.5))
    ax_cell.text(8.5, 9.5, "BLOOD", ha='center', color='#B71C1C', weight='bold')
    cell_box = patches.FancyBboxPatch((3, 1), 4, 8, boxstyle="round,pad=0.1",
                                       fc='#FFF9C4', ec='black', lw=2)
    ax_cell.add_patch(cell_box)

    # -- MR Status --
    ax_cell.add_patch(patches.Circle((5, 4), 0.7, fc='white', ec='black', ls='--'))

    if mr_eff < 0.1:                    # Aldactone
        mr_col = 'gray'
        mr_txt = "MR Blocked"
        ax_cell.text(5, 4, "❌", ha='center', va='center', fontsize=20)
    elif aldo < 2.0:                    # Liddle's
        mr_col = '#CFD8DC'
        mr_txt = "MR Inactive"
    elif aldo > 20:                     # High aldo
        mr_col = '#00E676'
        mr_txt = "MR Active"
        ax_cell.arrow(5, 4.5, -1, 1, head_width=0.3, color='#00E676', lw=3)
    else:                               # Basal
        mr_col = '#A5D6A7'
        mr_txt = "MR Basal"
        ax_cell.arrow(5, 4.5, -1, 1, head_width=0.2, color='#A5D6A7', lw=1)

    ax_cell.add_patch(patches.Circle((5, 4), 0.3, fc=mr_col))
    ax_cell.text(5, 3.2, mr_txt, ha='center', fontsize=9, weight='bold')

    # -- ENaC --
    ax_cell.plot([3, 4], [6, 6], color='black', lw=2)
    ax_cell.plot([3, 4], [5, 5], color='black', lw=2)

    if "Amiloride" in scen:
        ax_cell.add_patch(patches.Circle((3, 5.5), 0.3, fc='red'))
        ax_cell.text(2.2, 5.5, "Plugged", color='red', fontsize=9, ha='right')
    elif flux < 0.1:
        ax_cell.text(3.5, 5.5, "No Flux", fontsize=8, ha='center', va='center', color='red')
    else:
        w = min(1.2, flux * 0.4)
        ax_cell.arrow(1.5, 5.5, 3.5, 0, head_width=0.3, color='#4CAF50', lw=w*10)
        ax_cell.text(2, 6.2, "Na+ Influx", color='#2E7D32', weight='bold')

    ax_cell.text(3.5, 4.5, "ENaC", ha='center', fontsize=9, weight='bold')

    # -- ROMK --
    ax_cell.plot([3, 3.5], [3, 3], color='purple', lw=2)
    ax_cell.plot([3, 3.5], [2, 2], color='purple', lw=2)

    if flux > 1.5:
        ax_cell.arrow(4.5, 2.5, -3.0, 0, head_width=0.2, color='purple', lw=3)
        ax_cell.text(4, 1.5, "↑↑ K+ Secretion", color='purple', fontsize=8)
    elif flux > 0.5:
        ax_cell.arrow(4.5, 2.5, -2.0, 0, head_width=0.1, color='purple', lw=1)
        ax_cell.text(4, 1.5, "Normal K+", color='purple', fontsize=8)
    else:
        ax_cell.text(2.5, 1.5, "↓ K+ Secretion", color='gray', fontsize=8, ha='center')

    # === DATA PANEL ===
    ax_data.axis('off')

    c_bp = 'green'
    if systolic > 135: c_bp = 'red'
    if systolic < 105: c_bp = 'blue'

    c_k = 'green'
    if k_val < 3.5 or k_val > 5.2: c_k = 'red'

    c_aldo = 'green'
    if aldo > 20: c_aldo = 'red'
    if aldo < 3:  c_aldo = 'blue'

    ax_data.text(0, 0.9, "1. Plasma Aldosterone", fontsize=10, color='gray')
    ax_data.text(0, 0.8, f"{aldo:.0f} ng/dL", fontsize=16, color=c_aldo, weight='bold')

    ax_data.text(0, 0.6, "2. Blood Pressure", fontsize=10, color='gray')
    ax_data.text(0, 0.5, f"{int(systolic)}/{int(diastolic)} mmHg",
                 fontsize=16, color=c_bp, weight='bold')

    ax_data.text(0, 0.3, "3. Serum Potassium", fontsize=10, color='gray')
    ax_data.text(0, 0.2, f"{k_val:.1f} mEq/L", fontsize=16, color=c_k, weight='bold')

    if systolic < 100: ax_data.text(0.5, 0.5, "Hypotension",  color='blue', fontsize=10)
    if systolic > 140: ax_data.text(0.5, 0.5, "Hypertension", color='red',  fontsize=10)
    if k_val > 5.2:    ax_data.text(0.5, 0.2, "Hyperkalemia", color='red',  fontsize=10)
    if k_val < 3.4:    ax_data.text(0.5, 0.2, "Hypokalemia",  color='red',  fontsize=10)

    st.pyplot(fig)


draw_dashboard(scenario, final_flux, delivery, serum_aldo, mr_efficacy,
               systolic, diastolic, k_val)
