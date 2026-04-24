import streamlit as st
import pandas as pd
from google import genai
import math
import sys

# --- PAGE CONFIG ---
st.set_page_config(page_title="JLL Restacking Engine v7.8", layout="wide")

# --- DATA INITIALIZATION ---
# Relational Demand Model: Mapping Business Units to Product Pods
# Per User Instruction: Brand Strategy is excluded from all pod desk counts.
pod_bu_mapping = {
    "Swipe My Card": {
        "Tech": 257,
        "Data Analysts": 34,
        "Horizontal Admin Support": 50
    },
    "Mobile App": {
        "Tech": 103,
        "Data Analysts": 44,
        "Communications": 33
    },
    "Caff Locator": {
        "Tech": 65,
        "Data Analysts": 99,
        "Communications": 90 
    },
    "Cross Section": {
        "Data Analysts": 131,
        "Finance": 2
    }
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
    "3.A": "6 focus desks", "3.B": "1 storage, 1 large collab space", 
    "3.C": "1 open collab space", "3.D": "3 enclosed offices",
    "4.A": "1 office, 1 storage room", "4.B": "3 offices, 1 collab room",
    "4.C": "6 focus desks", "4.D": "1 office, 6 focus desks"
}

# --- SIDEBAR: POLICY CONTROLS ---
st.sidebar.title("🏢 Policy & Scenario")

renovation_phase = st.sidebar.radio(
    "1. Select Renovation Phase",
    options=["Pre-Renovation (Current)", "Post-Renovation (Hexagonal Densification)"]
)

if renovation_phase == "Pre-Renovation (Current)":
    quad_capacities = {"3.A": 124, "3.B": 96, "3.C": 108, "3.D": 108, "4.A": 126, "4.B": 96, "4.C": 108, "4.D": 121}
else:
    quad_capacities = {"3.A": 143, "3.B": 143, "3.C": 143, "3.D": 143, "4.A": 143, "4.B": 143, "4.C": 143, "4.D": 142}

st.sidebar.markdown("---")
st.sidebar.subheader("2. Business Unit Sharing Ratios")

unique_bus = ["Tech", "Communications", "Finance", "Data Analysts", "Brand Strategy", "Horizontal Admin Support"]
bu_ratios = {}
for bu in unique_bus:
    # UPDATED LOGIC: Tech 0.96, Communications 0.50, all others 1.00
    if bu == "Tech":
        default_val = 0.96
    elif bu == "Communications":
        default_val = 0.50
    else:
        default_val = 1.00
        
    bu_ratios[bu] = st.sidebar.slider(f"{bu} Ratio", 0.10, 1.00, default_val, 0.005)

# --- MATH ENGINE ---
pod_demand = {}
for pod, bu_counts in pod_bu_mapping.items():
    total = sum([(hc * bu_ratios.get(bu, 1.0)) for bu, hc in bu_counts.items()])
    pod_demand[pod] = math.ceil(total)

pod_assignments = {pod: [] for pod in pod_bu_mapping}
for q in quad_capacities.keys():
    selected = st.session_state.get(f"pod_{q}", [])
    for p in selected:
        pod_assignments[p].append(q)

placed_per_pod = {pod: 0 for pod in pod_bu_mapping}
quad_loads = {q: 0 for q in quad_capacities.keys()}

for q, cap in quad_capacities.items():
    assigned_pods = st.session_state.get(f"pod_{q}", [])
    if not assigned_pods:
        continue
    
    # Logic: Divide pod's total demand by number of quads it is assigned to
    quad_pod_shares = {p: (pod_demand[p] / len(pod_assignments[p])) for p in assigned_pods}
    total_quad_demand = sum(quad_pod_shares.values())
    quad_loads[q] = math.ceil(total_quad_demand)
    
    # Cap placement at physical quad capacity
    actual_fulfillment = min(total_quad_demand, cap)
    
    for p in assigned_pods:
        ratio = quad_pod_shares[p] / total_quad_demand
        placed_per_pod[p] += (ratio * actual_fulfillment)

# --- MAIN UI ---
st.title("JLL Restacking Engine: Capacity Validation")
st.caption(f"Strategy: {renovation_phase} | Total Supply: {sum(quad_capacities.values())} desks")

# --- INVENTORY TRACKER ---
st.subheader("📊 Workstation Inventory")
inv_cols = st.columns(len(pod_bu_mapping))

for i, pod in enumerate(pod_demand.keys()):
    goal = pod_demand[pod]
    placed = math.floor(placed_per_pod[pod])
    remaining = max(0, goal - placed)
    
    with inv_cols[i]:
        st.markdown(f"**{pod}**")
        st.markdown(f"Goal: {goal}")
        st.markdown(f"**{placed} placed / {remaining} remaining**")
        if remaining == 0 and placed > 0:
            st.success("STATUS: FULLY PLACED")
        elif placed > 0:
            st.warning("STATUS: PARTIAL")
        else:
            st.error("STATUS: UNPLACED")

st.markdown("---")

# --- THE BOARD ---
col1, col2, col3, col4 = st.columns(4)
columns = [col1, col2, col3, col4, col1, col2, col3, col4]
quad_keys = list(quad_capacities.keys())

for i, quad in enumerate(quad_keys):
    with columns[i]:
        st.markdown(f"### Quad {quad}")
        st.caption(f"Cap: {quad_capacities[quad]} | Architecture: {existing_architecture[quad]}")
        st.multiselect("Assign Pods", options=list(pod_bu_mapping.keys()), key=f"pod_{quad}", label_visibility="collapsed")
        st.multiselect("Add Specialized Spaces", options=specialized_spaces_list, key=f"spec_{quad}")

# --- CAPACITY ANALYSIS ---
st.markdown("---")
st.subheader("Capacity & Adjacency Analysis")
cols_analysis = st.columns(8)
for i, quad in enumerate(quad_keys):
    cap = quad_capacities[quad]
    load = quad_loads[quad]
    delta = cap - load
    with cols_analysis[i]:
        st.metric(label=f"Quad {quad}", value=f"{load}/{cap}", delta=delta, delta_color="normal" if delta >= 0 else "inverse")
        if delta < 0:
            st.error("OVER CAPACITY")

# --- AI STRATEGY ADVISOR (v7.8 - Accurate Constraint Logic) ---
st.markdown("---")
st.subheader("🧠 Agentic Strategy Advisor")

if st.button("Generate Strategy Summary", type="primary"):
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("DEBUG: 'GEMINI_API_KEY' not found in Streamlit Secrets.")
    else:
        with st.spinner("Analyzing occupancy patterns..."):
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                # Context 1: Total Program Demand
                inventory_data = "\n".join([
                    f"- {pod}: Target {pod_demand[pod]} total desks needed. Currently successfully placed: {math.floor(placed_per_pod[pod])}."
                    for pod in pod_demand.keys()
                ])
                
                # Context 2: Physical Board State
                board_data = "\n".join([
                    f"- Quad {q}: Capacity {quad_capacities[q]} seats. Assigned Pods: {st.session_state.get(f'pod_{q}', [])}. Current Load: {quad_loads[q]}."
                    for q in quad_keys
                ])
                
                system_prompt = f"""
                You are a Senior Occupancy Planner. Evaluate this restack.
                
                CRITICAL MATH CONSTRAINTS:
                - A 'Quad' has a physical limit (Max Capacity).
                - NEVER suggest consolidating a team into a single Quad if their 'Target' demand is higher than the Quad's capacity.
                - For example: If Mobile App needs 160 desks and a Quad only holds 143, you MUST acknowledge they need at least two quads.
                
                DEMAND PROGRAM (THE GOAL):
                {inventory_data}
                
                CURRENT PLACEMENT (THE MAP):
                {board_data}
                
                PHASE: {renovation_phase}
                
                Analyze the scenario in 3 paragraphs:
                1. Placement Integrity: Are all pods actually seated? Identify any pods with 'Remaining' desk needs.
                2. Capacity Efficiency: Identify any Quads that are 'Over Capacity' or 'Underutilized'.
                3. Strategic Recommendation: Suggest which team to move next, or which Quad to renovate, based on actual vacancies.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=system_prompt
                )
                st.info(response.text)
                
            except Exception as e:
                st.error(f"AI Error: {e}")
