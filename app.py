import streamlit as st
import pandas as pd
from google import genai
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="JLL Restacking Engine", layout="wide")

# --- DATA INITIALIZATION ---
# Base headcounts from your CSV data
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
    "3.B": "1 storage, 1 large collab space",
    "3.C": "1 large open collab space",
    "3.D": "3 enclosed offices",
    "4.A": "1 office, 1 storage room",
    "4.B": "3 offices, 1 collab room",
    "4.C": "6 focus desks",
    "4.D": "1 office, 6 focus desks"
}

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🏢 Scenario Controls")

renovation_phase = st.sidebar.radio(
    "1. Select Renovation Phase",
    options=["Pre-Renovation (Current)", "Post-Renovation (Hexagonal Densification)"]
)

if renovation_phase == "Pre-Renovation (Current)":
    quad_capacities = {"3.A": 124, "3.B": 96, "3.C": 108, "3.D": 108, "4.A": 126, "4.B": 96, "4.C": 108, "4.D": 121}
else:
    # Densified targets based on your strategic assessment
    quad_capacities = {"3.A": 143, "3.B": 143, "3.C": 143, "3.D": 143, "4.A": 143, "4.B": 143, "4.C": 143, "4.D": 142}

st.sidebar.markdown("---")
st.sidebar.markdown("**2. Adjust Desk Sharing Ratios**")
current_ratios = {}
for pod, hc in projected_base_headcounts.items():
    current_ratios[pod] = st.sidebar.slider(f"{pod} Ratio", 0.30, 1.00, 0.96, 0.05)

# Calculate dynamic demand target
pod_demand = {pod: math.ceil(hc * current_ratios[pod]) for pod, hc in projected_base_headcounts.items()}

# --- MAIN UI ---
st.title("JLL Restacking Engine: Product-Led Adjacency")
st.caption(f"Current Environment: {renovation_phase} | Total Capacity: {sum(quad_capacities.values())} desks")

# --- DYNAMIC INVENTORY CALCULATION ---
# We check the current selections in the UI to see what has been assigned
pod_assignments = {pod: [] for pod in projected_base_headcounts}
for q in quad_capacities.keys():
    selected = st.session_state.get(f"pod_{q}", [])
    for p in selected:
        pod_assignments[p].append(q)

st.subheader("📊 Workstation Inventory")
inv_cols = st.columns(len(projected_base_headcounts))

# Calculate how many desks are "placed" per pod
# Logic: A pod's demand is divided among the quads it is assigned to.
# Each quad can only take up to its max capacity.
quad_loads = {q: 0 for q in quad_capacities.keys()}
placed_totals = {pod: 0 for pod in projected_base_headcounts}

# Pass 1: Determine load per quad
for q in quad_capacities.keys():
    assigned_here = st.session_state.get(f"pod_{q}", [])
    for p in assigned_here:
        # Split the pod's demand by number of quads it occupies
        share = math.ceil(pod_demand[p] / len(pod_assignments[p]))
        quad_loads[q] += share
        placed_totals[p] += share

# Display Inventory Tracker
for i, (pod, target) in enumerate(pod_demand.items()):
    placed = placed_totals[pod]
    remaining = target - placed
    with inv_cols[i]:
        if remaining <= 0 and placed > 0:
            st.success(f"**{pod}**\n\nFully Seated")
        elif placed > 0:
            st.warning(f"**{pod}**\n\n{remaining} desks left")
        else:
            st.error(f"**{pod}**\n\n{target} desks unplaced")

st.markdown("---")

# --- THE BLOCK & STACK BOARD ---
col1, col2, col3, col4 = st.columns(4)
columns = [col1, col2, col3, col4, col1, col2, col3, col4]
quad_keys = list(quad_capacities.keys())

for i, quad in enumerate(quad_keys):
    with columns[i]:
        st.markdown(f"### Quad {quad}")
        st.caption(f"Max: {quad_capacities[quad]} | {existing_architecture[quad]}")
        
        # UI Inputs
        st.multiselect("Assign Pods", options=list(projected_base_headcounts.keys()), key=f"pod_{quad}", label_visibility="collapsed")
        st.multiselect("Ancillary Spaces", options=specialized_spaces_list, key=f"spec_{quad}")

# --- CAPACITY METRICS ---
st.markdown("---")
st.subheader("Capacity Analysis")
cols_analysis = st.columns(8)
for i, quad in enumerate(quad_keys):
    cap = quad_capacities[quad]
    load = quad_loads[quad]
    delta = cap - load
    with cols_analysis[i]:
        st.metric(label=f"Quad {quad}", value=f"{load}/{cap}", delta=delta, delta_color="normal" if delta >= 0 else "inverse")

# --- AI STRATEGY ADVISOR ---
st.markdown("---")
st.subheader("🧠 Agentic Strategy Advisor")

if st.button("Generate Strategy Summary", type="primary"):
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    else:
        with st.spinner("Consulting JLL Strategy guidelines..."):
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                board_summary = "\n".join([f"Quad {q}: {st.session_state.get(f'pod_{q}', [])}. Load: {quad_loads[q]}/{quad_capacities[q]}" for q in quad_keys])
                
                prompt = f"""
                You are a Senior Workplace Strategist for JLL. Evaluate this restack scenario:
                
                Phase: {renovation_phase}
                Board State:
                {board_summary}
                
                Provide a 3-paragraph analysis of the adjacency and capacity viability.
                """
                
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.info(response.text)
            except Exception as e:
                st.error(f"AI Error: {e}")
