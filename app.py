import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- PAGE SETUP ---
st.set_page_config(page_title="Nephro-Sim", layout="wide")
st.title("🔬 Advanced Nephro-Sim: Transport & Regulation")

# --- SIDEBAR ---
st.sidebar.header("Patient Scenario")
scenario = st.sidebar.radio(
    "Select Condition:",
    ("Normal Physiology", 
     "Acetazolamide (Proximal)", 
     "Vomiting (Metabolic Alkalosis)",
     "Furosemide (Loop)", 
     "Dehydration", 
     "Liddle's Syndrome", 
     "Amiloride (Channel Blocker)", 
     "Aldactone (Receptor Antagonist)",
     "PHA Type 1 (ENaC Inactivity)")
)

# --- LOGIC ENGINE ---
def get_parameters(scen):
    # RETURNS: 
    # 1. Genotype (1.0 = Normal)
    # 2. Serum Aldo (ng/dL, Norm=10-15)
    # 3. MR Efficacy (0 to 1)
    # 4. Distal Na Load (1.0 = Normal)
    # 5. Pore Block % (0 to 1)
    # 6. Volume Status Modifier (Affects BP directly, 1.0=Euvol)
    
    if scen == "Normal Physiology":
        # Baseline: Aldo allows moderate Na reabsorption
        return 1.0, 12.0, 1.0, 1.0, 0.0, 1.0
        
    if scen == "Acetazolamide (Proximal)":
        # Diuretic -> Low BP.
        # User Logic: Hypokalemia/Acidosis context suppressing Aldo/MR despite vol depletion.
        return 1.0, 8.0, 0.8, 1.5, 0.0, 0.90
        
    if scen == "Vomiting (Metabolic Alkalosis)":
        # Vol Depletion -> Low BP. 
        # High Aldo (RAAS). High Bicarb delivery obligates Na/K loss.
        return 1.0, 60.0, 1.0, 1.4, 0.0, 0.85

    if scen == "Furosemide (Loop)":
        # Massive Na delivery. Significant Volume loss (Low BP).
        # High Aldo.
        return 1.0, 50.0, 1.0, 3.5, 0.0, 0.88
        
    if scen == "Dehydration":
        # Max Aldo. Low flow/delivery (prerenal), but avid retention.
        # BP Low due to hypovolemia.
        return 1.0, 80.0, 1.0, 0.6, 0.0, 0.85
        
    if scen == "Liddle's Syndrome":
        # Const. Active. Vol Expansion -> Hypertension.
        # Aldo Suppressed.
        return 4.0, 2.0, 1.0, 1.0, 0.0, 1.15
        
    if scen == "Amiloride (Channel Blocker)":
        # ENaC Blocked. Na wasting -> Vol Drop -> High Aldo (Compensatory).
        # MR is ACTIVE, but channel is plugged.
        # BP slightly low/normal.
        return 1.0, 70.0, 1.0, 1.0, 0.95, 0.94
        
    if scen == "Aldactone (Receptor Antagonist)":
        # MR Blocked. Aldo is HIGH (trying to fix it).
        # Natriuresis -> Mild BP drop.
        return 1.0, 80.0, 0.0, 1.0, 0.0, 0.94
        
    if scen == "PHA Type 1 (ENaC Inactivity)":
        # Mimics Amiloride but genetic. ENaC dead.
        # Salt Wasting -> Low BP -> High Aldo.
        return 0.1, 90.0, 1.0, 1.0, 0.0, 0.88
        
    return 1.0, 10.0, 1.0, 1.0, 0.0, 1.0

g_factor, serum_aldo, mr_efficacy, delivery, pore_block, vol_mod = get_parameters(scenario)

# --- PHYSIOLOGY CALCULATION ---

# 1. Effective Aldosterone Signal
# (Serum Level * Receptor Health). 
# Note: In Liddle's, the channel ignores the low Aldo signal and stays open.
aldo_signal = serum_aldo * mr_efficacy
aldo_stim = 1 + (aldo_signal / 15.0) 

if scenario == "Liddle's Syndrome":
    # Mutation overrides low aldo
    channel_open_prob = g_factor 
else:
    channel_open_prob = g_factor * aldo_stim

# 2. Total ENaC Activity (Flux)
# Flux = (Open Probability * Substrate Delivery) * (1 - Physical Block)
enac_flux = channel_open_prob * delivery * (1 - pore_block)

# 3. Blood Pressure Model
# Base 120. Affected by Volume Status (primary) and ENaC retention (secondary fine tune)
# We weight Volume Status heavily for cases like Dehydration/Vomiting
base_bp = 120
bp = base_bp * vol_mod
# Small fine-tuning by ENaC activity (retention vs wasting)
bp += (enac_flux - 1.5) * 4 
# Safety clamps
bp = max(85, min(190, bp))

# 4. Potassium Model
# Base 4.0. Driven inversely by ENaC Flux (Na in -> K out).
# Higher Flux = Lower K.
# Algorithm: Start at 4.0. Subtract proportional to flux.
k_val = 4.0 - (0.5 * (enac_flux - 2.0))

# Special Adjustment for Aldactone/Amiloride/PHA (Hyperkalemia drivers)
# If ENaC is blocked/dead, K secretion stops, K rises significantly.
if pore_block > 0.8 or g_factor < 0.2 or mr_efficacy < 0.1:
    k_val += 1.5 # Boost to hyperkalemic range

# Safety Clamps (User Request: prevent 1.5)
k_val = max(2.8, min(6.5, k_val))

# --- VISUALIZATION ---
def draw_dashboard(scen, flux, deliv, aldo, mr_eff):
    fig = plt.figure(figsize=(12, 9))
    
    ax_nephron = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    ax_cell = plt.subplot2grid((3, 2), (1, 0), rowspan=2)
    ax_data = plt.subplot2grid((3, 2), (1, 1), rowspan=2)
    
    # === MACRO NEPHRON ===
    ax_nephron.set_title("Nephron Transport Sites", fontweight='bold')
    ax_nephron.set_xlim(0, 12)
    ax_nephron.set_ylim(0, 5)
    ax_nephron.axis('off')
    
    lw = 12 
    # PCT
    ax_nephron.plot([1, 3], [4, 4], color='#FF9F40', lw=lw, solid_capstyle='round')
    ax_nephron.text(2, 4.4, "PCT", ha='center', fontsize=9, weight='bold')
    # Loop
    ax_nephron.plot([3, 4, 4, 5], [4, 1, 1, 4], color='#A0A0A0', lw=lw, solid_capstyle='round')
    ax_nephron.text(4, 0.5, "Loop", ha='center', fontsize=9)
    # DCT
    ax_nephron.plot([5, 7], [4, 4], color='#4BC0C0', lw=lw, solid_capstyle='round')
    ax_nephron.text(6, 4.4, "DCT", ha='center', fontsize=9, weight='bold')
    # CD
    ax_nephron.plot([7, 8, 8, 9], [4, 4, 1, 1], color='#FFD700', lw=lw*1.5, solid_capstyle='round')
    ax_nephron.text(8, 4.4, "Collecting Duct", ha='center', fontsize=9, color='#B8860B', weight='bold')

    # Na+ Dots
    dot_count = int(12 * deliv)
    xf = np.linspace(7, 8, int(dot_count/2))
    yf = np.full_like(xf, 4)
    ax_nephron.scatter(xf, yf, color='blue', s=15, zorder=10)
    xv = np.full(int(dot_count/2), 8)
    yv = np.linspace(4, 1, int(dot_count/2))
    ax_nephron.scatter(xv, yv, color='blue', s=15, zorder=10)
    
    # Labels
    ax_nephron.text(2, 4, "NHE3", ha='center', va='center', fontsize=7, color='white', weight='bold')
    ax_nephron.text(4, 1.5, "NKCC2", ha='center', va='center', fontsize=7, weight='bold')
    ax_nephron.text(6, 4, "NCC", ha='center', va='center', fontsize=7, color='white', weight='bold')
    ax_nephron.text(8, 2.5, "ENaC", ha='center', va='center', fontsize=8, weight='bold')

    # === MICRO CELL ===
    ax_cell.set_title("Principal Cell Zoom", fontweight='bold')
    ax_cell.set_xlim(0, 10)
    ax_cell.set_ylim(0, 10)
    ax_cell.axis('off')
    
    # Lumen/Blood/Cell
    ax_cell.add_patch(patches.Rectangle((0, 0), 3, 10, fc='#E0F7FA', alpha=0.5))
    ax_cell.text(1.5, 9.5, "LUMEN", ha='center', color='#006064', weight='bold')
    ax_cell.add_patch(patches.Rectangle((7, 0), 3, 10, fc='#FFEBEE', alpha=0.5))
    ax_cell.text(8.5, 9.5, "BLOOD", ha='center', color='#B71C1C', weight='bold')
    cell_box = patches.FancyBboxPatch((3, 1), 4, 8, boxstyle="round,pad=0.1", fc='#FFF9C4', ec='black', lw=2)
    ax_cell.add_patch(cell_box)
    
    # MR RECEPTOR VISUAL
    # Nucleus
    ax_cell.add_patch(patches.Circle((5, 4), 0.7, fc='white', ec='black', ls='--')) 
    
    if mr_eff < 0.1: # Aldactone
        mr_col = 'gray'
        mr_txt = "MR Blocked"
        ax_cell.text(5, 4, "❌", ha='center', va='center', fontsize=20)
    elif aldo > 15: # High Aldo (Amiloride/Vomit/Dehyd)
        mr_col = '#00C853' # Bright Green
        mr_txt = "MR High Activity"
        # Strong signal arrow
        ax_cell.arrow(5, 4.5, -1, 1, head_width=0.3, color='#00C853', lw=3)
    else: # Baseline/Low
        mr_col = '#A5D6A7'
        mr_txt = "MR Basal"
        ax_cell.arrow(5, 4.5, -1, 1, head_width=0.2, color='#A5D6A7', lw=1)

    ax_cell.add_patch(patches.Circle((5, 4), 0.3, fc=mr_col))
    ax_cell.text(5, 3.0, mr_txt, ha='center', fontsize=9, weight='bold')

    # ENaC CHANNEL
    ax_cell.plot([3, 4], [6, 6], color='black', lw=2) 
    ax_cell.plot([3, 4], [5, 5], color='black', lw=2) 
    
    if "Amiloride" in scen:
        ax_cell.add_patch(patches.Circle((3, 5.5), 0.3, fc='red'))
        ax_cell.text(2.2, 5.5, "Plugged", color='red', fontsize=9, ha='right')
    elif flux > 0.3:
        # Flow Arrow thickness depends on flux
        w = min(1.0, flux * 0.3)
        ax_cell.arrow(1.5, 5.5, 3.5, 0, head_width=0.3, color='#4CAF50', lw=w*10)
        ax_cell.text(2, 6.2, "Na+ Influx", color='#2E7D32', weight='bold')
    else:
        ax_cell.text(3.5, 5.5, "Inactive", fontsize=8, ha='center', va='center', rotation=90)
        
    ax_cell.text(3.5, 4.5, "ENaC", ha='center', fontsize=9, weight='bold')

    # ROMK
    ax_cell.plot([3, 3.5], [3, 3], color='purple', lw=2)
    ax_cell.plot([3, 3.5], [2, 2], color='purple', lw=2)
    # Secretion depends on ENaC flux (driving force)
    if flux > 1.0:
        ax_cell.arrow(4.5, 2.5, -3.0, 0, head_width=0.2, color='purple', lw=3)
        ax_cell.text(4, 2.8, "K+ Secretion", color='purple', fontsize=8)
    else:
        ax_cell.text(2.5, 2.5, "Low K+ Flow", color='gray', fontsize=8, ha='center')

    # === DATA ===
    ax_data.axis('off')
    
    # Logic for colors
    c_bp = 'green'
    if bp > 135: c_bp = 'red'
    if bp < 105: c_bp = 'blue'
    
    c_k = 'green'
    if k_val < 3.5 or k_val > 5.2: c_k = 'red'
    
    c_aldo = 'green'
    if aldo > 20: c_aldo = 'red'
    
    ax_data.text(0, 0.9, "1. Plasma Aldosterone", fontsize=10, color='gray')
    ax_data.text(0, 0.8, f"{aldo:.0f} ng/dL", fontsize=16, color=c_aldo, weight='bold')
    
    ax_data.text(0, 0.6, "2. Blood Pressure", fontsize=10, color='gray')
    ax_data.text(0, 0.5, f"{int(bp)}/{int(bp*0.66)} mmHg", fontsize=16, color=c_bp, weight='bold')
    
    ax_data.text(0, 0.3, "3. Serum Potassium", fontsize=10, color='gray')
    ax_data.text(0, 0.2, f"{k_val:.1f} mEq/L", fontsize=16, color=c_k, weight='bold')
    
    # Interpretation Text
    if bp < 100: ax_data.text(0.5, 0.5, "Hypotension", color='blue', fontsize=10)
    if bp > 140: ax_data.text(0.5, 0.5, "Hypertension", color='red', fontsize=10)
    if k_val > 5.2: ax_data.text(0.5, 0.2, "Hyperkalemia", color='red', fontsize=10)
    if k_val < 3.2: ax_data.text(0.5, 0.2, "Hypokalemia", color='red', fontsize=10)

    st.pyplot(fig)

draw_dashboard(scenario, enac_flux, delivery, serum_aldo, mr_efficacy)
