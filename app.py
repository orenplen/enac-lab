import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Nephro-Sim", layout="wide")
st.title("🔬 Advanced Nephro-Sim: Transport & Regulation")

# --- SIDEBAR ---
st.sidebar.header("Patient Scenario")

# Reordered list as requested: Singles first, then combination.
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

# --- PHYSIOLOGY ENGINE ---
def get_parameters(scen):
    # RETURNS:
    # 1. Genotype Factor (0.0 = Dead, 1.0 = Normal)
    # 2. Serum Aldo (ng/dL, Normal ~10-15)
    # 3. MR Efficacy (0.0 = Blocked, 1.0 = Normal)
    # 4. Distal Na Delivery (1.0 = Normal)
    # 5. Pore Block % (0.95 = Blocked)
    # 6. Volume BP Modifier (1.0 = Normal)
    
    if scen == "Normal Physiology":
        return 1.0, 12.0, 1.0, 1.0, 0.0, 1.0
        
    if scen == "Acetazolamide (Proximal)":
        return 1.0, 15.0, 1.0, 1.6, 0.0, 0.95
        
    if scen == "Vomiting (Metabolic Alkalosis)":
        return 1.0, 60.0, 1.0, 1.2, 0.0, 0.88

    if scen == "Dehydration":
        return 1.0, 80.0, 1.0, 0.6, 0.0, 0.85

    if scen == "Furosemide (Loop)":
        return 1.0, 45.0, 1.0, 3.0, 0.0, 0.92

    if scen == "Aldactone (Receptor Antagonist)":
        return 1.0, 80.0, 0.0, 1.0, 0.0, 0.94
        
    if scen == "Furosemide + Aldactone (Combination)":
        # High Delivery + Blocked Receptor + High Aldo
        return 1.0, 85.0, 0.0, 3.0, 0.0, 0.89
        
    if scen == "Liddle's Syndrome":
        return 4.0, 1.0, 1.0, 1.0, 0.0, 1.15
        
    if scen == "Amiloride (Channel Blocker)":
        return 1.0, 70.0, 1.0, 1.0, 0.95, 0.95
        
    if scen == "PHA Type 1 (ENaC Inactivity)":
        return 0.0, 90.0, 1.0, 1.0, 0.0, 0.88
        
    return 1.0, 12.0, 1.0, 1.0, 0.0, 1.0

g_factor, serum_aldo, mr_efficacy, delivery, pore_block, vol_mod = get_parameters(scenario)

# --- CALCULATIONS ---

# 1. MR Receptor & Gene Expression
effective_aldo_signal = serum_aldo * mr_efficacy

if mr_efficacy < 0.1:
    expression_level = 0.1 # Basal expression only (Aldactone)
else:
    expression_level = 0.2 + (effective_aldo_signal / 12.0)

# 2. Total Flux Calculation
if scenario == "Liddle's Syndrome":
    raw_flux = 4.0 * delivery 
elif scenario == "PHA Type 1 (ENaC Inactivity)":
    raw_flux = 0.0 
else:
    raw_flux = g_factor * expression_level * delivery

final_flux = raw_flux * (1 - pore_block)

# 3. Blood Pressure
base_bp = 120 * vol_mod
bp_shift = (final_flux - 1.0) * 5 
systolic = base_bp + bp_shift
systolic = max(90, min(190, systolic))

# 4. Potassium
k_val = 4.0 - (0.6 * (final_flux - 1.0))

# --- Specific Overrides for Clinical Accuracy ---
if scenario == "Amiloride (Channel Blocker)":
    k_val = 6.0 
elif scenario == "Acetazolamide (Proximal)":
    k_val = 3.3 
elif scenario == "Furosemide + Aldactone (Combination)":
    k_val = 4.4 
elif final_flux < 0.2: # PHA / Pure Aldactone
    k_val = 5.8 

k_val = max(2.8, min(7.5, k_val))


# --- VISUALIZATION ---
def draw_dashboard(scen, flux, deliv, aldo, mr_eff):
    fig = plt.figure(figsize=(12, 10))
    
    ax_nephron = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    ax_cell = plt.subplot2grid((3, 2), (1, 0), rowspan=2)
    ax_data = plt.subplot2grid((3, 2), (1, 1), rowspan=2)
    
    # === MACRO NEPHRON ===
    ax_nephron.set_title("Nephron Overview", fontweight='bold')
    ax_nephron.set_xlim(0, 12)
    ax_nephron.set_ylim(0, 5)
    ax_nephron.axis('off')
    
    lw = 12
    # Draw Segments
    ax_nephron.plot([1, 3], [4, 4], color='#FF9F40', lw=lw, solid_capstyle='round') # PCT
    ax_nephron.plot([3, 4, 4, 5], [4, 1, 1, 4], color='#A0A0A0', lw=lw, solid_capstyle='round') # Loop
    ax_nephron.plot([5, 7], [4, 4], color='#4BC0C0', lw=lw, solid_capstyle='round') # DCT
    ax_nephron.plot([7, 8, 8, 9], [4, 4, 1, 1], color='#FFD700', lw=lw*1.5, solid_capstyle='round') # CD

    # Na+ Dots (Visualizing Delivery)
    dot_count = int(12 * deliv)
    dot_count = min(60, dot_count) 
    
    xf = np.linspace(7, 8, int(dot_count/2) + 1)
    yf = np.full_like(xf, 4)
    ax_nephron.scatter(xf, yf, color='blue', s=15, zorder=10)
    xv = np.full(int(dot_count/2) + 1, 8)
    yv = np.linspace(4, 1, int(dot_count/2) + 1)
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

    # === MICRO CELL ===
    ax_cell.set_title("Principal Cell (Zoom)", fontweight='bold')
    ax_cell.set_xlim(0, 10)
    ax_cell.set_ylim(0, 10)
    ax_cell.axis('off')
    
    # Compartments
    ax_cell.add_patch(patches.Rectangle((0, 0), 3, 10, fc='#E0F7FA', alpha=0.5))
    ax_cell.text(1.5, 9.5, "LUMEN", ha='center', color='#006064', weight='bold')
    ax_cell.add_patch(patches.Rectangle((7, 0), 3, 10, fc='#FFEBEE', alpha=0.5))
    ax_cell.text(8.5, 9.5, "BLOOD", ha='center', color='#B71C1C', weight='bold')
    cell_box = patches.FancyBboxPatch((3, 1), 4, 8, boxstyle="round,pad=0.1", fc='#FFF9C4', ec='black', lw=2)
    ax_cell.add_patch(cell_box)
    
    # -- MR STATUS --
    ax_cell.add_patch(patches.Circle((5, 4), 0.7, fc='white', ec='black', ls='--')) 
    
    # Logic for MR colors and text
    if mr_eff < 0.1: # Aldactone
        mr_col = 'gray'
        mr_txt = "MR Blocked"
        ax_cell.text(5, 4, "❌", ha='center', va='center', fontsize=20)
    elif aldo < 2.0: # Liddle
        mr_col = '#CFD8DC' 
        mr_txt = "MR Inactive"
    elif aldo > 20: # High Aldo
        mr_col = '#00E676'
        mr_txt = "MR Active"
        ax_cell.arrow(5, 4.5, -1, 1, head_width=0.3, color='#00E676', lw=3)
    else: 
        mr_col = '#A5D6A7'
        mr_txt = "MR Basal"
        ax_cell.arrow(5, 4.5, -1, 1, head_width=0.2, color='#A5D6A7', lw=1)

    ax_cell.add_patch(patches.Circle((5, 4), 0.3, fc=mr_col))
    # MOVED DOWN to 2.2 to avoid overlap with ROMK
    ax_cell.text(5, 2.2, mr_txt, ha='center', fontsize=9, weight='bold')

    # -- ENaC CHANNEL --
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

    # ROMK
    ax_cell.plot([3, 3.5], [3, 3], color='purple', lw=2)
    ax_cell.plot([3, 3.5], [2, 2], color='purple', lw=2)
    
    # ROMK Secretion Visuals
    # MOVED UP to 3.2 to avoid overlap with MR
    if flux > 0.8:
        ax_cell.arrow(4.5, 2.5, -3.0, 0, head_width=0.2, color='purple', lw=3)
        ax_cell.text(4, 3.2, "K+ Secretion", color='purple', fontsize=8)
    elif flux > 0.2: 
        ax_cell.arrow(4.5, 2.5, -2.0, 0, head_width=0.1, color='purple', lw=1)
        ax_cell.text(4, 3.2, "Normal K+", color='purple', fontsize=8)
    else:
        ax_cell.text(2.5, 2.5, "Reduced", color='gray', fontsize=8, ha='center')

    # === DATA PANEL ===
    ax_data.axis('off')
    
    c_bp = 'green'
    if systolic > 135: c_bp = 'red'
    if systolic < 105: c_bp = 'blue'
    
    c_k = 'green'
    if k_val < 3.5 or k_val > 5.2: c_k = 'red'
    
    c_aldo = 'green'
    if aldo > 20: c_aldo = 'red'
    if aldo < 3: c_aldo = 'blue'
    
    ax_data.text(0, 0.9, "1. Plasma Aldosterone", fontsize=10, color='gray')
    ax_data.text(0, 0.8, f"{aldo:.0f} ng/dL", fontsize=16, color=c_aldo, weight='bold')
    
    ax_data.text(0, 0.6, "2. Blood Pressure", fontsize=10, color='gray')
    ax_data.text(0, 0.5, f"{int(systolic)}/{int(systolic*0.66)} mmHg", fontsize=16, color=c_bp, weight='bold')
    
    ax_data.text(0, 0.3, "3. Serum Potassium", fontsize=10, color='gray')
    ax_data.text(0, 0.2, f"{k_val:.1f} mEq/L", fontsize=16, color=c_k, weight='bold')
    
    if systolic < 100: ax_data.text(0.5, 0.5, "Hypotension", color='blue', fontsize=10)
    if systolic > 140: ax_data.text(0.5, 0.5, "Hypertension", color='red', fontsize=10)
    if k_val > 5.2: ax_data.text(0.5, 0.2, "Hyperkalemia", color='red', fontsize=10)
    if k_val < 3.4: ax_data.text(0.5, 0.2, "Hypokalemia", color='red', fontsize=10)

    st.pyplot(fig)

draw_dashboard(scenario, final_flux, delivery, serum_aldo, mr_efficacy)
