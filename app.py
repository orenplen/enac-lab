import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- PAGE SETUP ---
st.set_page_config(page_title="Nephro-Sim", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔬 Advanced Nephro-Sim: Transport & Regulation")

# --- SIDEBAR ---
st.sidebar.header("Patient Scenario")
scenario = st.sidebar.radio(
    "Select Condition:",
    ("Normal Physiology", 
     "Acetazolamide (Proximal)", 
     "Furosemide (Loop)", 
     "Dehydration", 
     "Liddle's Syndrome", 
     "Amiloride (Distal)", 
     "PHA1 (Loss of Function)")
)

# --- LOGIC ENGINE ---
def calculate_state(scen):
    # Returns: (Genotype_Factor, Aldo_Level, Distal_Delivery, ENaC_Block, Specific_Label)
    
    if scen == "Normal Physiology":
        return 1.0, 10.0, 1.0, 0.0, ""
        
    if scen == "Acetazolamide (Proximal)":
        # Blocks CA/NHE3 in PCT -> High Na+ & HCO3- delivery downstream
        # Mild volume depletion -> Mild Aldo rise
        return 1.0, 30.0, 1.8, 0.0, "NHE3 Blocked"
        
    if scen == "Furosemide (Loop)":
        # Blocks NKCC2 -> Massive Na+ delivery
        # Volume depletion -> High Aldo
        return 1.0, 80.0, 3.0, 0.0, "NKCC2 Blocked"
        
    if scen == "Dehydration":
        # Max conservation
        return 1.0, 95.0, 0.5, 0.0, "Max Conservation"
        
    if scen == "Liddle's Syndrome":
        # Gain of function mutation
        return 4.0, 5.0, 1.0, 0.0, "Constitutive Activation"
        
    if scen == "Amiloride (Distal)":
        # Direct ENaC block
        return 1.0, 10.0, 1.0, 0.95, "ENaC Blocked"
        
    if scen == "PHA1 (Loss of Function)":
        # Loss of function
        return 0.1, 100.0, 1.0, 0.0, "ENaC Failure"
        
    return 1.0, 10.0, 1.0, 0.0, ""

g_factor, aldo, delivery, block, label_txt = calculate_state(scenario)

# --- PHYSIOLOGY MATH ---
aldo_eff = 1 + (aldo / 20.0)
# Activity = (Genotype * Hormone * Load) * (Open Probability)
activity = (g_factor * aldo_eff * delivery) * (1 - block)

# BP Model
vol_mod = 0.9 if scenario in ["Acetazolamide (Proximal)", "Furosemide (Loop)"] else 1.0
bp = 120 * (0.8 + (0.2 * activity)) * vol_mod
bp = max(80, min(220, bp))

# K+ Model
k_val = 4.0 - (0.4 * (activity - 1.5))
k_val = max(1.5, min(8.5, k_val))

# --- VISUALIZATION FUNCTION ---
def draw_dashboard(scen, act, deliv_rate):
    fig = plt.figure(figsize=(12, 8))
    
    # Define Layout: Top (Nephron), Bottom (Principal Cell)
    ax_nephron = plt.subplot2grid((2, 2), (0, 0), colspan=2)
    ax_cell = plt.subplot2grid((2, 2), (1, 0))
    ax_data = plt.subplot2grid((2, 2), (1, 1))
    
    # === 1. MACRO: THE NEPHRON ===
    ax_nephron.set_title("The Nephron: Sites of Action", fontweight='bold')
    ax_nephron.set_xlim(0, 12)
    ax_nephron.set_ylim(0, 5)
    ax_nephron.axis('off')
    
    # -- Drawing Segments --
    lw = 12 # Line width
    
    # PCT (Proximal) - Orange
    ax_nephron.plot([1, 3], [4, 4], color='#FF9F40', lw=lw, solid_capstyle='round')
    ax_nephron.text(2, 4.3, "Proximal (PCT)", ha='center', fontsize=9, color='#FF9F40', weight='bold')
    
    # Loop of Henle - Gray
    ax_nephron.plot([3, 4, 4, 5], [4, 1, 1, 4], color='#A0A0A0', lw=lw, solid_capstyle='round')
    ax_nephron.text(4, 0.5, "Loop of Henle", ha='center', fontsize=9, color='gray')
    
    # DCT (Distal) - Blue
    ax_nephron.plot([5, 7], [4, 4], color='#4BC0C0', lw=lw, solid_capstyle='round')
    ax_nephron.text(6, 4.3, "Distal (DCT)", ha='center', fontsize=9, color='#4BC0C0', weight='bold')
    
    # CD (Collecting Duct) - Gold
    ax_nephron.plot([7, 8, 8], [4, 4, 1], color='#FFD700', lw=lw*1.5, solid_capstyle='round')
    ax_nephron.text(8, 4.3, "Collecting Duct", ha='center', fontsize=9, color='#B8860B', weight='bold')

    # -- Highlighting Transporters --
    
    # 1. NHE3 (PCT)
    nhe_color = 'red' if "Acetazolamide" in scen else 'black'
    ax_nephron.add_patch(patches.Circle((2, 4), 0.3, fc='white', ec=nhe_color, lw=2))
    ax_nephron.text(2, 4, "NHE3", ha='center', va='center', fontsize=7, weight='bold')
    
    # 2. NKCC2 (Loop)
    nkcc_color = 'red' if "Furosemide" in scen else 'black'
    ax_nephron.add_patch(patches.Rectangle((3.7, 1.5), 0.6, 0.6, fc='white', ec=nkcc_color, lw=2))
    ax_nephron.text(4, 1.8, "NKCC2", ha='center', va='center', fontsize=7, weight='bold')

    # 3. NCC (DCT)
    # Thiazides block here (not in list, but we show the channel)
    ax_nephron.add_patch(patches.RegularPolygon((6, 4), numVertices=3, radius=0.35, fc='white', ec='black', lw=2))
    ax_nephron.text(6, 3.9, "NCC", ha='center', va='center', fontsize=7, weight='bold')

    # 4. ENaC (CD) - The Star
    enac_ec = 'red' if "Amiloride" in scen else 'black'
    ax_nephron.add_patch(patches.Circle((8, 2.5), 0.5, fc='#FFFACD', ec=enac_ec, lw=2))
    ax_nephron.text(8, 2.5, "ENaC", ha='center', va='center', fontsize=8, weight='bold')
    
    # Flow Arrow
    if deliv_rate > 1.2:
        ax_nephron.arrow(8.5, 3.5, 0, -1.5, head_width=0.2, color='blue', lw=3)
        ax_nephron.text(8.7, 2.8, "High Na+\nDelivery", color='blue', fontsize=8)


    # === 2. MICRO: PRINCIPAL CELL ===
    ax_cell.set_title("Zoom: Principal Cell", fontweight='bold')
    ax_cell.set_xlim(0, 10)
    ax_cell.set_ylim(0, 10)
    ax_cell.axis('off')
    
    # Backgrounds
    # Lumen (Left)
    ax_cell.add_patch(patches.Rectangle((0, 0), 3, 10, fc='#E0F7FA', alpha=0.5))
    ax_cell.text(1.5, 9, "LUMEN\n(Urine)", ha='center', color='#006064', weight='bold')
    
    # Blood (Right)
    ax_cell.add_patch(patches.Rectangle((7, 0), 3, 10, fc='#FFEBEE', alpha=0.5))
    ax_cell.text(8.5, 9, "BLOOD\n(Interstitium)", ha='center', color='#B71C1C', weight='bold')
    
    # The Cell (Center)
    cell_box = patches.FancyBboxPatch((3, 1), 4, 8, boxstyle="round,pad=0.1", fc='#FFF9C4', ec='black', lw=2)
    ax_cell.add_patch(cell_box)
    
    # -- ENaC Channel (Apical/Left) --
    # Draw channel walls
    ax_cell.plot([3, 4], [6, 6], color='black', lw=2) # Top wall
    ax_cell.plot([3, 4], [5, 5], color='black', lw=2) # Bottom wall
    
    # Channel Status
    if "Amiloride" in scen:
        # Plug the hole
        ax_cell.add_patch(patches.Circle((3, 5.5), 0.3, fc='red'))
        ax_cell.text(2.5, 5.5, "X", color='white', weight='bold', ha='center', va='center')
    elif act < 0.2:
        # Closed/Degraded
        ax_cell.text(3.5, 5.5, "Degraded", fontsize=8, ha='center', va='center', rotation=90)
    else:
        # Open - Draw Na+ passing through
        width = min(0.8, act * 0.2) # Thickness based on activity
        ax_cell.arrow(1.5, 5.5, 4.0, 0, head_width=0.3, color='#4CAF50', lw=width*10, zorder=10)
        ax_cell.text(2, 6.2, "Na+ Influx", color='#2E7D32', weight='bold', fontsize=9)
    
    ax_cell.text(3.5, 4.5, "ENaC", ha='center', fontsize=9, weight='bold')
    
    # -- ROMK Channel (Apical/Left) --
    # K+ goes OUT
    ax_cell.plot([3, 3.5], [3, 3], color='purple', lw=2)
    ax_cell.plot([3, 3.5], [2, 2], color='purple', lw=2)
    
    if act > 1.5: # Driven by electrical gradient from ENaC
        ax_cell.arrow(4.5, 2.5, -3.0, 0, head_width=0.2, color='purple', lw=3)
        ax_cell.text(4, 2.8, "K+ Secretion", color='purple', fontsize=8)
    else:
        ax_cell.text(2.5, 2.5, "Low K+\nEfflux", color='gray', fontsize=8, ha='center')

    # -- Na/K ATPase (Basolateral/Right) --
    ax_cell.add_patch(patches.Circle((7, 4), 0.4, fc='white', ec='black'))
    ax_cell.text(7.8, 4, "Na/K\nATPase", fontsize=7, ha='center')

    # === 3. DATA & OUTCOMES ===
    ax_data.axis('off')
    
    # Color logic
    c_bp = 'red' if bp > 140 else 'blue' if bp < 100 else 'green'
    c_k = 'red' if (k_val < 3.5 or k_val > 5.0) else 'green'
    
    ax_data.text(0.1, 0.9, "Physiological Outcomes", fontsize=12, weight='bold')
    
    # BP Text
    ax_data.text(0.1, 0.7, f"Blood Pressure: {int(bp)}/{int(bp*0.66)}", fontsize=14, color=c_bp, weight='bold')
    if bp > 140: ax_data.text(0.1, 0.6, "⚠️ HYPERTENSION (Vol Expansion)", fontsize=9, color='red')
    elif bp < 100: ax_data.text(0.1, 0.6, "⚠️ HYPOTENSION (Vol Depletion)", fontsize=9, color='blue')
    
    # K Text
    ax_data.text(0.1, 0.4, f"Serum Potassium: {k_val:.1f} mEq/L", fontsize=14, color=c_k, weight='bold')
    if k_val < 3.5: ax_data.text(0.1, 0.3, "⚠️ HYPOKALEMIA (K+ Wasting)", fontsize=9, color='red')
    elif k_val > 5.0: ax_data.text(0.1, 0.3, "⚠️ HYPERKALEMIA (K+ Retention)", fontsize=9, color='red')

    # Scenario Notes
    ax_data.text(0.1, 0.1, f"Mechanism: {scen}", fontsize=10, style='italic')

    st.pyplot(fig)

# --- RENDER ---
draw_dashboard(scenario, activity, delivery)
