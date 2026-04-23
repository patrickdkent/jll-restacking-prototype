import streamlit as st
import pandas as pd
from google import genai
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="JLL Restacking Engine v5", layout="wide")

# --- MOCK DATA & CONTEXT ---
projected_base_headcounts = {
    "Swipe My Card": 341,
    "Mobile App": 180,
    "Caff Locator": 254,
    "Cross Section": 133
}

specialized_spaces_list = [
    "Centralized Server Room (15x30)",
    "Brand Strategy Dedicated Open Studio",
    "Tech Digital Lab (12x24)",
    "Tech Locked Storage (12x12)",
    "Comm Locked Room (12x12)",
    "Swipe My Card War Room (12x12)"
]

existing_architecture = {
    "3.A": "6 focus desks",
    "3.B": "1 storage room, 1 large collab space",
    "3.C": "1 large open collab space",
    "3.D": "3 enclosed offices",
    "4.A": "1 enclosed office, 1 storage room",
    "4.B": "3 enclosed offices, 1 collab room",
    "4.C": "6 focus desks",
    "4.D": "1 enclosed office, 6 focus desks"
}

# --- SIDEBAR: MACRO POLICY ---
st.sidebar.title("🏢 Scenario Controls")

renovation_phase = st.sidebar.radio(
    "1. Select Renovation Phase",
    options=["Pre-Renovation (Current)", "Post-Renovation (Hexagonal Densification)"],
    help="Hexagonal desking densifies assignable desks by ~25%."
)

if renovation_phase == "Pre-Renovation (Current)":
    quad_capacities = {"3.A": 124, "3.B": 96, "3.C": 108, "3.D": 108, "4.A": 126, "4.B": 96, "4.C": 108, "4.D": 121}
else:
    quad_capacities = {"3.A": 143, "3.B": 143, "3.C": 143, "3.D": 143, "4.A": 143, "4.B": 143, "4.C": 143, "4.D": 142}

st.sidebar.markdown("---")
st.sidebar.markdown("**2. Adjust Desk Sharing Ratios**")
current_ratios = {}
for pod, hc in projected_base_headcounts.items():
    current_ratios[pod] = st.sidebar.slider(f"{pod} Ratio", 0.30, 1.00, 0.96, 0.05)

# Total Programmed Demand (Target)
pod_demand = {pod: math.ceil(hc * current_ratios[pod]) for pod, hc in projected_base_headcounts.items()}

# --- MAIN UI ---
st.title("JLL Restacking Engine: Product-Led Adjacency")

# --- NEW: INVENTORY TRACKER ---
st.subheader("📊 Workstation Inventory")
inv_cols = st.columns(len(projected_base_headcounts))

# Need to track assignments first to calculate "Unplaced"
# We'll use a temporary state hack to ensure we catch UI changes
if 'assignments' not in st.session_state:
    st.session_state.assignments = {q: [] for q in quad_capacities.keys()}

# Logic to calculate placement
pod_quad_count = {pod: sum([1 for q in quad_capacities.keys() if pod in st.session_state.get(f"pod_{q}", [])]) for pod in projected_base_headcounts}

for i, (pod, target) in enumerate(pod_demand.items()):
    placed = target if pod_quad_count[pod] > 0 else 0
    remaining = target - placed
    with inv_cols[i]:
        if pod_quad_count[pod] > 0:
            st.success(f"**{pod}**\n\nFully Seated ({target} desks)")
        else:
            st.error(f"**{pod}**\n\n{target} Desks Unplaced")

st.markdown("---")

# --- THE BOARD ---
col1, col2, col3, col4 = st.columns(4)
columns = [col1, col2, col3, col4, col1, col2, col3, col4]
quad_keys = list(quad_capacities.keys())
quad_loads = {q: 0 for q in quad_keys}

for i, quad in enumerate(quad_keys):
    with columns[i]:
        st.markdown(f"### Quad {quad}")
        st.caption(f"Max: {quad_capacities[quad]} | {existing_architecture[quad]}")
        
        # User input
        selected_pods = st.multiselect("Assign Pods", options=list(projected_base_headcounts.keys()), key=f"pod_{quad}", label_visibility="collapsed")
        st.session_state[f"pod_{quad}"] = selected_pods # Sync back to inventory
        
        st.multiselect("Specialized Spaces", options=specialized_spaces_list, key=f"spec_{quad}")

# Math for the Metrics
for quad in quad_keys:
    assigned_pods = st.session_state.get(f"pod_{quad}", [])
    for pod in assigned_pods:
        if pod_quad_count[pod] > 0:
            quad_loads[quad] += math.ceil(pod_demand[pod] / pod_quad_count[pod])

# --- RESULTS & AI ---
st.markdown("---")
st.subheader("Capacity Analysis")
cols_analysis = st.columns(8)
for i, quad in enumerate(quad_keys):
    cap = quad_capacities[quad]
    load = quad_loads[quad]
    delta = cap - load
    with cols_analysis[i]:
        st.metric(label=f"Quad {quad}", value=f"{load}/{cap}", delta=delta, delta_color="normal" if delta >= 0 else "inverse")

st.markdown("---")
if st.button("Generate Strategy Summary", type="primary"):
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("API Key missing.")
    else:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        board_data = "\n".join([f"Quad {q}: {st.session_state.get(f'pod_{q}', [])}. Load: {quad_loads[q]}/{quad_capacities[q]}" for q in quad_keys])
        response = client.models.generate_content(model='gemini-2.5-flash', contents=f"As a JLL Strategist, evaluate this restack scenario:\n{board_data}")
        st.info(response.text)
