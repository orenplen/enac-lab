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
     "PHA1 (Loss of Function)")
)

# --- LOGIC ENGINE ---
def calculate_state(scen):
    # Variables: 
    # 1. Genotype Factor (Mutations)
    # 2. Serum Aldosterone (The systemic level)
    # 3. Receptor Function (0.0 = Blocked/Defect, 1.0 = Normal)
    # 4. Distal Delivery (1.0 = Normal, >1 = High Load)
    # 5. ENaC Pore Block (0.0 = Open, 1.0 = Plugged)
    
    if scen == "Normal Physiology":
        return 1.0, 10.0, 1.0, 1.0, 0.0
        
    if scen == "Acetazolamide (Proximal)":
        # Blocks NHE3 -> High Na/HCO3 downstream
        return 1.0, 30.0, 1.0, 1.8, 0.0
        
    if scen == "Vomiting (Metabolic Alkalosis)":
        # Loss of H+/Cl- -> Volume Depletion -> High Aldo
        # High Bicarb in tubule -> High Na Delivery (obligatory anion)
        return 1.0, 85.0, 1.0, 1.5, 0.0

    if scen == "Furosemide (Loop)":
        return 1.0, 80.0, 1.0, 3.0, 0.0
        
    if scen == "Dehydration":
        return 1.0, 95.0, 1.0, 0.5, 0.0
        
    if scen == "Liddle's Syndrome":
        # Gain of function (High Surface Expression). Aldo is suppressed.
        return 4.0, 2.0, 1.0, 1.0, 0.0
        
    if scen == "Amiloride (Channel Blocker)":
        return 1.0, 15.0, 1.0, 1.0, 0.95
        
    if scen == "Aldactone (Receptor Antagonist)":
        # Blocks MR. Systemic Aldo is HIGH (compensatory), but Effect is LOW.
        return 1.0, 90.0, 0.05, 1.0, 0.0
        
    if scen == "PHA1 (Loss of Function)":
        # ENaC broken. Aldo very high.
        return 0.1, 100.0, 1.0, 1.0, 0.0
        
    return 1.0, 10.0, 1.0, 1.0, 0.0

g_factor, serum_aldo, mr_efficacy, delivery, pore_block = calculate_state(scenario)

# --- PHYSIOLOGY MATH ---
# Effective Aldo at the DNA level = Serum * Receptor Efficacy
aldo_effective = serum_aldo * mr_efficacy

# Activity Calculation
# Note: Liddle's bypasses the receptor requirement (constitutive)
if scenario == "Liddle's Syndrome":
    aldo_factor = 1.0 # Aldo not needed
else:
    aldo_factor = 1 + (aldo_effective / 20.0)

activity = (g_factor * aldo_factor * delivery) * (1 - pore_block)

# BP Model
vol_mod = 0.9 if scenario in ["Acetazolamide (Proximal)", "Furosemide (Loop)", "Vomiting (Metabolic Alkalosis)"] else 1.0
bp = 120 * (0.8 + (0.2 * activity)) * vol_mod
bp = max(80, min(220, bp))

# K+ Model (Na reabsorption drives K secretion)
k_val = 4.0 - (0.4 * (activity - 1.5))
k_val = max(1.5, min(8.5, k_val))

# --- VISUALIZATION FUNCTION ---
def draw_dashboard(scen, act, deliv, aldo_level, mr_status):
    fig = plt.figure(figsize=(12, 9))
    
    # Grid Layout
    ax_nephron = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    ax_cell = plt.subplot2grid((3, 2), (1, 0), rowspan=2)
    ax_data = plt.subplot2grid((3, 2), (1, 1), rowspan=2)
    
    # === 1. MACRO: THE NEPHRON ===
    ax_nephron.set_title("Nephron Transport Sites", fontweight='bold')
    ax_nephron.set_xlim(0, 12)
    ax_nephron.set_ylim(0, 5)
    ax_nephron.axis('off')
    
    # Draw Segments
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

    # Visualizing Na+ Flow (Blue Dots in Lumen)
    # Density depends on 'delivery'
    dot_count = int(10 * deliv)
    # Generate random positions in the CD segment (x=7-8, y=4 down to 1)
    # Horizontal part
    xf = np.linspace(7, 8, int(dot_count/2))
    yf = np.full_like(xf, 4)
    ax_nephron.scatter(xf, yf, color='blue', s=10, zorder=10)
    # Vertical part
    xv = np.full(int(dot_count/2), 8)
    yv = np.linspace(4, 1, int(dot_count/2))
    ax_nephron.scatter(xv, yv, color='blue', s=10, zorder=10)
    
    if deliv > 1.2:
        ax_nephron.text(8.5, 3, "High Distal\nNa+ Load", color='blue', fontsize=8)

    # Transporter Highlights
    ax_nephron.text(2, 4, "NHE3", ha='center', va='center', fontsize=7, color='white', weight='bold')
    ax_nephron.text(4, 1.5, "NKCC2", ha='center', va='center', fontsize=7, weight='bold')
    ax_nephron.text(6, 4, "NCC", ha='center', va='center', fontsize=7, color='white', weight='bold')
    ax_nephron.text(8, 2.5, "ENaC", ha='center', va='center', fontsize=8, weight='bold')

    # === 2. MICRO: PRINCIPAL CELL ===
    ax_cell.set_title("Principal Cell Zoom", fontweight='bold')
    ax_cell.set_xlim(0, 10)
    ax_cell.set_ylim(0, 10)
    ax_cell.axis('off')
    
    # Backgrounds
    ax_cell.add_patch(patches.Rectangle((0, 0), 3, 10, fc='#E0F7FA', alpha=0.5)) # Lumen
    ax_cell.text(1.5, 9.5, "LUMEN", ha='center', color='#006064', weight='bold')
    ax_cell.add_patch(patches.Rectangle((7, 0), 3, 10, fc='#FFEBEE', alpha=0.5)) # Blood
    ax_cell.text(8.5, 9.5, "BLOOD", ha='center', color='#B71C1C', weight='bold')
    
    # Cell Body
    cell_box = patches.FancyBboxPatch((3, 1), 4, 8, boxstyle="round,pad=0.1", fc='#FFF9C4', ec='black', lw=2)
    ax_cell.add_patch(cell_box)
    
    # -- ALDOSTERONE PATHWAY --
    # Draw MR Receptor in Nucleus area
    ax_cell.add_patch(patches.Circle((5, 4), 0.6, fc='white', ec='black', ls='--')) # Nucleus
    
    # MR Status
    if mr_status < 0.5: # Blocked by Aldactone
        mr_color = 'gray'
        mr_text = "MR (Blocked)"
        ax_cell.text(5, 4, "❌", ha='center', va='center', fontsize=15)
    elif aldo_level > 15: # High Aldo
        mr_color = '#4CAF50' # Green
        mr_text = "MR (Active)"
        # Arrow from MR to ENaC
        ax_cell.arrow(5, 4.5, -1, 1, head_width=0.2, color='green', lw=2)
    else: # Low Aldo
        mr_color = '#A5D6A7' # Pale Green
        mr_text = "MR (Idle)"

    ax_cell.add_patch(patches.Circle((5, 4), 0.3, fc=mr_color, alpha=0.5))
    ax_cell.text(5, 3.2, mr_text, ha='center', fontsize=8)

    # -- ENaC Channel (Apical) --
    ax_cell.plot([3, 4], [6, 6], color='black', lw=2) 
    ax_cell.plot([3, 4], [5, 5], color='black', lw=2) 
    
    # Na+ Influx Visuals
    if "Amiloride" in scen:
        ax_cell.add_patch(patches.Circle((3, 5.5), 0.3, fc='red'))
        ax_cell.text(2.2, 5.5, "Blocked", color='red', fontsize=8, ha='right')
    elif act > 0.5:
        # Draw Na+ ions passing through
        ax_cell.arrow(1.5, 5.5, 3.5, 0, head_width=0.3, color='#4CAF50', lw=act*2)
        ax_cell.text(2, 6.2, "Na+ Influx", color='#2E7D32', weight='bold')
        # Na ions inside
        ax_cell.scatter([3.2, 3.5, 3.8], [5.5, 5.5, 5.5], color='blue', s=30, zorder=10)

    ax_cell.text(3.5, 4.5, "ENaC", ha='center', fontsize=9, weight='bold')
    
    # -- ROMK Channel --
    ax_cell.plot([3, 3.5], [3, 3], color='purple', lw=2)
    ax_cell.plot([3, 3.5], [2, 2], color='purple', lw=2)
    if act > 1.5:
        ax_cell.arrow(4.5, 2.5, -3.0, 0, head_width=0.2, color='purple', lw=3)
        ax_cell.text(4, 2.8, "K+ Secretion", color='purple', fontsize=8)

    # === 3. DATA PANEL ===
    ax_data.axis('off')
    
    # Formatting
    def get_color(val, low, high, reverse=False):
        if reverse:
            if val > high: return 'green' 
            return 'red'
        if val > high: return 'red'
        if val < low: return 'blue'
        return 'green'

    # Aldo Text
    c_aldo = 'red' if aldo_level > 20 else 'green'
    ax_data.text(0, 0.9, "1. Plasma Aldosterone", fontsize=10, color='gray')
    ax_data.text(0, 0.8, f"{aldo_level} ng/dL", fontsize=14, color=c_aldo, weight='bold')
    
    # BP Text
    c_bp = get_color(bp, 100, 140)
    ax_data.text(0, 0.6, "2. Blood Pressure", fontsize=10, color='gray')
    ax_data.text(0, 0.5, f"{int(bp)}/{int(bp*0.66)} mmHg", fontsize=14, color=c_bp, weight='bold')
    
    # K Text
    c_k = 'red' if (k_val < 3.5 or k_val > 5.0) else 'green'
    ax_data.text(0, 0.3, "3. Serum Potassium", fontsize=10, color='gray')
    ax_data.text(0, 0.2, f"{k_val:.1f} mEq/L", fontsize=14, color=c_k, weight='bold')
    
    if k_val < 3.5: ax_data.text(0.5, 0.2, "Hypokalemia", fontsize=9, color='red')
    if k_val > 5.0: ax_data.text(0.5, 0.2, "Hyperkalemia", fontsize=9, color='red')

    st.pyplot(fig)

# --- RENDER ---
draw_dashboard(scenario, activity, delivery, serum_aldo, mr_efficacy)
