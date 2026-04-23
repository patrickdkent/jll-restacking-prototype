import streamlit as st
import pandas as pd
from google import genai
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="JLL Restacking Engine v7", layout="wide")

# --- DATA INITIALIZATION (Relational Demand Model) ---
# Accurate headcount distribution based on AcmeCaff Programming CSVs
# Totals: Swipe My Card (341), Mobile App (180), Caff Locator (254), Cross Section (133)
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
        "Communications": 62,
        "Brand Strategy": 28
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
    options=["Pre-Renovation (Current)", "Post-Renovation (Hexagonal Densification)"],
    help="Hexagonal desking densifies assignable desks by ~25%."
)

# Set dynamic capacities based on toggle
if renovation_phase == "Pre-Renovation (Current)":
    quad_capacities = {
        "3.A": 124, "3.B": 96, "3.C": 108, "3.D": 108,
        "4.A": 126, "4.B": 96, "4.C": 108, "4.D": 121
    }
else:
    # Densified targets based on strategic assessment
    quad_capacities = {
        "3.A": 143, "3.B": 143, "3.C": 143, "3.D": 143,
        "4.A": 143, "4.B": 143, "4.C": 143, "4.D": 142
    }

st.sidebar.markdown("---")
st.sidebar.subheader("2. Business Unit Sharing Ratios")
st.sidebar.caption("Define the desk-sharing policy for the official BUs.")

# Official Business Unit List
unique_bus = ["Tech", "Communications", "Finance", "Data Analysts", "Brand Strategy", "Horizontal Admin Support"]
bu_ratios = {}
for bu in unique_bus:
    # Defaulting Tech/Data to ~0.965 and others to 0.50 based on assessment context
    default_ratio = 0.965 if bu in ["Tech", "Data Analysts"] else 0.50
    bu_ratios[bu] = st.sidebar.slider(f"{bu} Ratio", 0.10, 1.00, default_ratio, 0.005)

# --- MATH ENGINE: HIERARCHICAL DEMAND ---
# This calculates the aggregate desk requirement for each pod based on its member BU ratios
pod_demand = {}
for pod, bu_counts in pod_bu_mapping.items():
    total_desks = 0
    for bu, hc in bu_counts.items():
        total_desks += (hc * bu_ratios.get(bu, 1.0)) 
    pod_demand[pod] = math.ceil(total_desks)

# --- MAIN UI ---
st.title("JLL Restacking Engine: Relational Demand Model")
st.caption(f"Strategy: {renovation_phase} | Total Assignable Desks: {sum(quad_capacities.values())}")

# --- DYNAMIC INVENTORY TRACKER ---
# Logic: A pod's demand is divided among the quads it is assigned to.
pod_assignments = {pod: [] for pod in pod_bu_mapping}
for q in quad_capacities.keys():
    selected = st.session_state.get(f"pod_{q}", [])
    for p in selected:
        pod_assignments[p].append(q)

st.subheader("📊 Workstation Inventory")
st.caption("Calculated by: Σ (BU Members in Pod * BU Sharing Ratio)")
inv_cols = st.columns(len(pod_bu_mapping))

quad_loads = {q: 0 for q in quad_capacities.keys()}
placed_totals = {pod: 0 for pod in pod_bu_mapping}

for q in quad_capacities.keys():
    assigned_here = st.session_state.get(f"pod_{q}", [])
    for p in assigned_here:
        if len(pod_assignments[p]) > 0:
            share = math.ceil(pod_demand[p] / len(pod_assignments[p]))
            quad_loads[q] += share
            placed_totals[p] += share

# Display the inventory status bars
for i, (pod, target) in enumerate(pod_demand.items()):
    placed = placed_totals[pod]
    remaining = target - placed
    with inv_cols[i]:
        if remaining <= 0 and placed > 0:
            st.success(f"**{pod}**\n\nGoal: {target} Desks\n\nSTATUS: FULLY PLACED")
        elif placed > 0:
            st.warning(f"**{pod}**\n\nGoal: {target} Desks\n\nREMAINING: {remaining}")
        else:
            st.error(f"**{pod}**\n\nGoal: {target} Desks\n\nSTATUS: UNPLACED")

st.markdown("---")

# --- THE BLOCK & STACK BOARD ---
col1, col2, col3, col4 = st.columns(4)
columns = [col1, col2, col3, col4, col1, col2, col3, col4]
quad_keys = list(quad_capacities.keys())

for i, quad in enumerate(quad_keys):
    with columns[i]:
        st.markdown(f"### Quad {quad}")
        st.caption(f"Cap: {quad_capacities[quad]} | Architecture: {existing_architecture[quad]}")
        
        # User Selection UI
        st.multiselect(
            "Assign Pods", 
            options=list(pod_bu_mapping.keys()), 
            key=f"pod_{quad}", 
            label_visibility="collapsed"
        )
        st.multiselect(
            "Add Specialized Spaces", 
            options=specialized_spaces_list, 
            key=f"spec_{quad}"
        )

# --- CAPACITY ANALYSIS METRICS ---
st.markdown("---")
st.subheader("Capacity & Adjacency Analysis")
cols_analysis = st.columns(8)
for i, quad in enumerate(quad_keys):
    cap = quad_capacities[quad]
    load = quad_loads[quad]
    delta = cap - load
    with cols_analysis[i]:
        st.metric(
            label=f"Quad {quad}", 
            value=f"{load}/{cap}", 
            delta=delta, 
            delta_color="normal" if delta >= 0 else "inverse"
        )
        if delta < 0:
            st.error("DEFICIT")
        elif load > 0:
            st.success("STABLE")

# --- AGENTIC INTEGRATION: GEMINI STRATEGY ADVISOR ---
st.markdown("---")
st.subheader("🧠 Agentic Strategy Advisor")

if st.button("Generate Strategy Summary", type="primary"):
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    else:
        with st.spinner("Analyzing cross-functional adjacencies..."):
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                # Construct board state for the AI
                board_summary = "\n".join([
                    f"Quad {q}: Pods {st.session_state.get(f'pod_{q}', [])}, "
                    f"Specialized Spaces {st.session_state.get(f'spec_{q}', [])}. "
                    f"Load: {quad_loads[q]}/{quad_capacities[q]}" 
                    for q in quad_keys
                ])
                
                system_prompt = f"""
                You are a Senior Workplace Strategist for JLL. Evaluate this restack scenario.
                
                Context: Transitioning from functional silos to product-led adjacencies.
                Phase: {renovation_phase}
                
                Current Stacking Scenario:
                {board_summary}
                
                Provide a professional 3-paragraph executive summary covering:
                1. Stacking Efficiency: How well does the current allocation fit within capacity limits?
                2. Adjacency Strategy: Evaluate the pod co-location and specialized space placement.
                3. Phased Implementation: Which quads are optimal for the next furniture replacement phase based on vacancy?
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=system_prompt
                )
                
                st.info(response.text)
                
            except Exception as e:
                st.error(f"An error occurred with the AI integration: {e}")
