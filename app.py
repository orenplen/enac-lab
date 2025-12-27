import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Nephro-Sim", layout="wide")

# --- CSS ---
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

st.title("🫘 Nephro-Sim: ENaC Laboratory")

# --- SIDEBAR ---
st.sidebar.header("1. Patient Profile")
scenario = st.sidebar.radio(
    "Select Scenario:",
    ("Normal Physiology", "Furosemide Use", "Dehydration", 
     "Liddle's Syndrome", "Amiloride Use", "PHA1 (Loss of Function)")
)

st.sidebar.markdown("---")
st.sidebar.header("2. Adjustments")
override = st.sidebar.checkbox("Override Settings")

# --- LOGIC ---
def get_params(scen):
    # Returns: (Genotype, Aldo, Delivery, Block)
    if scen == "Normal Physiology": return 1.0, 10.0, 1.0, 0.0
    if scen == "Furosemide Use": return 1.0, 80.0, 3.0, 0.0
    if scen == "Dehydration": return 1.0, 95.0, 0.8, 0.0
    if scen == "Liddle's Syndrome": return 4.0, 2.0, 1.0, 0.0
    if scen == "Amiloride Use": return 1.0, 10.0, 1.0, 0.95
    if scen == "PHA1 (Loss of Function)": return 0.1, 100.0, 1.0, 0.0
    return 1.0, 10.0, 1.0, 0.0

g_factor, aldo, delivery, block = get_params(scenario)

if override:
    aldo = st.sidebar.slider("Aldosterone (nM)", 0.0, 100.0, float(aldo))
    block = st.sidebar.slider("Amiloride Block (%)", 0.0, 1.0, float(block))

# --- CALCULATION ---
# Activity
aldo_eff = 1 + (aldo / 20.0)
activity = (g_factor * aldo_eff * delivery) * (1 - block)

# Systemic
vol_mod = 0.85 if scenario == "Furosemide Use" else 1.0

# BP
bp = 120 * (0.8 + (0.2 * activity)) * vol_mod
bp = max(80, min(220, bp))

# Potassium
k_val = 4.0 - (0.4 * (activity - 1.5))
k_val = max(1.5, min(8.5, k_val))

# --- DRAWING ---
def draw_nephron(bp_in, k_in, act, scen):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Draw Tubules
    x = [1, 2, 2, 4, 4, 6, 6, 8, 8]
    y = [5, 5, 2, 2, 5, 5, 3, 3, 1]
    
    # Proximal
    ax.plot(x[:5], y[:5], color='#d3d3d3', linewidth=20, alpha=0.5, solid_capstyle='round')
    # Distal
    ax.plot(x[4:], y[4:], color='#FFD700', linewidth=25, solid_capstyle='round')

    # Labels
    ax.text(1.5, 5.5, "Proximal", color='gray', fontsize=10)
    ax.text(6.0, 5.5, "Collecting Duct", color='#B8860B', fontsize=12, weight='bold', ha='center')

    # Annotations
    if scen == "Furosemide Use":
        ax.text(3, 1.5, "NKCC2 Block", color='red', weight='bold')
    if scen == "Amiloride Use":
        ax.text(6, 4.0, "Blocked", color='red', weight='bold', ha='center')

    # Cell
    circle = patches.Circle((6, 4), radius=0.8, ec='black', fc='white', zorder=10)
    ax.add_patch(circle)
    
    # Arrows
    if act > 2.5: col, wid = 'red', 0.2
    elif act < 0.5: col, wid = 'gray', 0.02
    else: col, wid = 'green', 0.08
        
    ax.arrow(6, 5.2, 0, -0.6, width=wid, color=col, zorder=11)
    ax.text(6.2, 4.9, "Na+ In", color=col, fontsize=8)

    ax.arrow(6, 3.4, 0, 0.6, width=wid, color='purple', zorder=11)
    ax.text(5.6, 3.6, "K+ Out", color='purple', fontsize=8)

    # --- BOXES ---
    
    # BP Box
    c_bp = "red" if bp_in > 140 else "blue" if bp_in < 100 else "green"
    rect_bp = patches.FancyBboxPatch((8.2, 4.5), 1.8, 1.2, boxstyle="round,pad=0.1", fc='white', ec=c_bp, lw=2)
    ax.add_patch(rect_bp)
    
    bp_txt = f"{int(bp_in)}/{int(bp_in*0.66)}"
    ax.text(9.1, 5.3, "BP (mmHg)", ha='center', size=10)
    ax.text(9.1, 4.8, bp_txt, ha='center', size=14, weight='bold', color=c_bp)

    # K Box
    c_k = "red" if (k_in > 5.2 or k_in < 3.2) else "green"
    rect_k = patches.FancyBboxPatch((8.2, 2.8), 1.8, 1.2, boxstyle="round,pad=0.1", fc='white', ec=c_k, lw=2)
    ax.add_patch(rect_k)
    
    ax.text(9.1, 3.6, "Serum K+", ha='center', size=10)
    ax.text(9.1, 3.1, f"{k_in:.1f}", ha='center', size=14, weight='bold', color=c_k)

    st.pyplot(fig)

# --- LAYOUT ---
c1, c2 = st.columns([3, 1])

with c1:
    draw_nephron(bp, k_val, activity, scenario)

with c2:
    st.subheader("Status")
    if bp > 140: st.error("Hypertension")
    elif bp < 100: st.info("Hypotension")
    else: st.success("Normotension")
        
    if k_val < 3.5: st.error("Hypokalemia")
    elif k_val > 5.0: st.error("Hyperkalemia")
    else: st.success("Normokalemia")

    st.markdown(f"**Aldo:** {aldo} nM | **Block:** {int(block*100)}%")
