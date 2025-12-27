import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Nephro-Sim: ENaC Module", layout="wide")

# --- CSS FOR REALISM ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #555;
    }
</style>
""", unsafe_allow_html=True)

st.title("🫘 Nephro-Sim: The ENaC & Principal Cell Laboratory")
st.markdown("Investigate how the Epithelial Sodium Channel (ENaC) regulates blood pressure and potassium balance.")

# --- SIDEBAR: SCENARIO SELECTOR ---
st.sidebar.header("1. Choose Patient Profile")
scenario = st.sidebar.radio(
    "Clinical Scenario:",
    ("Normal Physiology", "Furosemide Use", "Dehydration", "Liddle's Syndrome", "Amiloride Use", "PHA1 (Loss of Function)")
)

st.sidebar.markdown("---")
st.sidebar.header("2. Manual Adjustments")
override = st.sidebar.checkbox("Override Scenario Settings")

# --- SIMULATION LOGIC ---
# Returns: (Genotype_Activity, Aldosterone, Na_Delivery, Block_Percent)
def get_scenario_params(scenario):
    if scenario == "Normal Physiology":
        return 1.0, 10.0, 1.0, 0.0
    elif scenario == "Furosemide Use":
        return 1.0, 80.0, 3.0, 0.0 
    elif scenario == "Dehydration":
        return 1.0, 95.0, 0.8, 0.0
    elif scenario == "Liddle's Syndrome":
        return 4.0, 2.0, 1.0, 0.0
    elif scenario == "Amiloride Use":
        return 1.0, 10.0, 1.0, 0.95 
    elif scenario == "PHA1 (Loss of Function)":
        return 0.1, 100.0, 1.0, 0.0 

genotype_factor, aldo_level, na_delivery, amiloride_block = get_scenario_params(scenario)

if override:
    aldo_level = st.sidebar.slider("Aldosterone Level (nM)", 0.0, 100.0, aldo_level)
    amiloride_block = st.sidebar.slider("Amiloride Block (%)", 0.0, 1.0, amiloride_block)

# --- CALCULATIONS ---
# 1. ENaC Activity Calculation
aldo_effect = 1 + (aldo_level / 20.0) 
enac_activity = (genotype_factor * aldo_effect * na_delivery) * (1 - amiloride_block)

# 2. Systemic Effects
base_systolic = 120
base_k = 4.0

if scenario == "Furosemide Use":
    volume_modifier = 0.85 
else:
    volume_modifier = 1.0

# BP Calculation
systolic_bp = base_systolic * (0.8 + (0.2 * enac_activity)) * volume_modifier
systolic_bp = max(80, min(220, systolic_bp))

# Potassium Calculation
potassium = base_k - (0.4 * (enac_activity - 1.5)) 
potassium = max(1.5, min(8.5, potassium))

# --- VISUALIZATION (THE NEPHRON) ---
def draw_nephron_status(bp, k, activity, scenario):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Draw Tubules
    path_x = [1, 2, 2, 4, 4, 6, 6, 8, 8]
    path_y = [5, 5, 2, 2, 5, 5, 3, 3, 1]
    
    ax.plot(path_x[:5], path_y[:5], color='#d3d3d3', linewidth=20, alpha=0.5, solid_capstyle='round') 
    ax.plot(path_x[4:], path_y[4:], color='#FFD700', linewidth=25, solid_capstyle='round') 

    # Labels
    ax.text(1.5, 5.5, "Proximal / Loop", color='gray', fontsize=10)
    ax.text(6.0, 5.5, "Collecting Duct (ENaC Site)", color='#B8860B', fontsize=12, weight='bold', ha='center')

    # Scenario Annotations
    if scenario == "Furosemide Use":
        ax.text(3, 1.5, "❌ NKCC2 Block", color='red', weight='bold')
    if scenario == "Amiloride Use":
        ax.text(6, 4.0, "❌ ENaC Blocked", color='red', weight='bold', ha='center')

    # Principal Cell
    circle = patches.Circle((6, 4), radius=0.8, edgecolor='black', facecolor='white', zorder=10)
    ax.add_patch(circle)
    
    # Arrows
    if activity > 2.5:
        arrow_width = 0.2
        arrow_color = 'red' 
    elif activity < 0.5:
        arrow_width = 0.02
        arrow_color = 'gray' 
    else:
        arrow_width = 0.08
        arrow_color = 'green'
        
    ax.arrow(6, 5.2, 0, -0.6, width=arrow_width, color=arrow_color, zorder=11)
    ax.text(6.2, 4.9, "Na+ In", color=arrow_color, weight='bold', fontsize=8)

    ax.arrow(6, 3.4, 0, 0.6, width=arrow_width, color='purple', zorder=11) 
    ax.text(5.6, 3.6, "K+ Out", color='purple', weight='bold', fontsize=8)

    # --- DASHBOARD BOXES ---
    # Blood Pressure Box
    bp_color = "red" if bp > 140 else "blue" if bp < 100 else "green"
    rect_bp = patches.FancyBboxPatch((8.2, 4.5), 1.8, 1.2, boxstyle="round,pad=0.1", fc='white', ec=bp_color, lw=2)
    ax.add_patch(rect_bp)
    ax.text(9.1, 5.3, "Blood Pressure", ha='center', size=10)
    ax.text(9.1, 4.8, f"{int(bp)}/{int(bp*0.66)}", ha