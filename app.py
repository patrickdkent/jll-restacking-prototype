import streamlit as st
import pandas as pd
from google import genai
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="JLL Restacking Engine v6", layout="wide")

# --- DATA INITIALIZATION (Relational Demand Model) ---
# Hardcoded based on AcmeCaff Programming Document
# Key: Product Pod -> {Business Unit: Total Projected HC}
pod_bu_mapping = {
    "Swipe My Card": {
        "Tech": 257,
        "Data Analysts": 34,
        "Product Management": 50
    },
    "Mobile App": {
        "Tech": 103,
        "Data Analysts": 44,
        "Product Management": 33
    },
    "Caff Locator": {
        "Tech": 65,
        "Data Analysts": 99,
        "Product Management": 90
    },
    "Cross Section": {
        "Finance": 22,
        "Data Analysts": 39,
        "Operations": 40,
        "Marketing": 32
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
    "1. Renovation Phase",
    options=["Pre-Renovation (Current)", "Post-Renovation (Hexagonal Densification)"]
)

if renovation_phase == "Pre-Renovation (Current)":
    quad_capacities = {"3.A": 124, "3.B": 96, "3.C": 108, "3.D": 108, "4.A": 126, "4.B": 96, "4.C": 108, "4.D": 121}
else:
    # Densified targets based on Patrick's V1 strategic assessment
    quad_capacities = {"3.A": 143, "3.B": 143, "3.C": 143, "3.D": 143, "4.A": 143, "4.B": 143, "4.C": 143, "4.D": 142}

st.sidebar.markdown("---")
st.sidebar.subheader("2. Business Unit Sharing Ratios")
st.sidebar.caption("Define the desk-sharing policy for each department.")

unique_bus = ["Tech", "Data Analysts", "Product Management", "Finance", "Operations", "Marketing"]
bu_ratios = {}
for bu in unique_bus:
    # Set default values mirroring the assessment programming
    default_ratio = 0.965 if bu in ["Tech", "Data Analysts", "Product Management"] else 0.50
    bu_ratios[bu] = st.sidebar.slider(f"{bu} Ratio", 0.10, 1.00, default_ratio, 0.005)

# --- THE MATH ENGINE: CALCULATING HIERARCHICAL DEMAND ---
# This calculates the aggregate desk requirement for each pod based on its member BU ratios
pod_demand = {}
for pod, bu_counts in pod_bu_mapping.items():
    total_desks = 0
    for bu, hc in bu_counts.items():
        total_desks += (hc * bu_ratios[bu])
    pod_demand[pod] = math.ceil(total_desks)

# --- MAIN UI ---
st.title("JLL Restacking Engine: Relational Demand Model")
st.caption(f"Strategy: {renovation_phase} | Total Assignable Desks: {sum(quad_capacities.values())}")

# --- INVENTORY TRACKER ---
# Track pod assignments to determine placement status
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

# Logic: Demand for a pod is distributed across all quads it is assigned to
for q in quad_capacities.keys():
    assigned_here = st.session_state.get(f"pod_{q}", [])
    for p in assigned_here:
        share = math.ceil(pod_demand[p] / len(pod_assignments[p]))
        quad_loads[q] += share
        placed_totals[p] += share

for i, (pod, target) in enumerate(pod_demand.items()):
    placed = placed_totals[pod]
    remaining = target - placed
    with inv_cols[i]:
        if remaining <= 0 and placed > 0:
            st.success(f"**{pod}**\n\nGoal: {target} Desks\n\nFULLY PLACED")
        elif placed > 0:
            st.warning(f"**{pod}**\n\nGoal: {target} Desks\n\nREMAINING: {remaining}")
        else:
            st.error(f"**{pod}**\n\nGoal: {target} Desks\n\nUNPLACED")

st.markdown("---")

# --- THE BLOCK & STACK BOARD ---
col1, col2, col3, col4 = st.columns(4)
columns = [col1, col2, col3, col4, col1, col2, col3, col4]
quad_keys = list(quad_capacities.keys())

for i, quad in enumerate(quad_keys):
    with columns[i]:
        st.markdown(f"### Quad {quad}")
        st.caption(f"Cap: {quad_capacities[quad]} | {existing_architecture[quad]}")
        
        # User selection
        st.multiselect("Assign Pods", options=list(pod_bu_mapping.keys()), key=f"pod_{quad}", label_visibility="collapsed")
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
        with st.spinner("Analyzing cross-functional adjacencies..."):
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                board_summary = "\n".join([f"Quad {q}: {st.session_state.get(f'pod_{q}', [])}. Load: {quad_loads[q]}/{quad_capacities[q]}" for q in quad_keys])
                
                prompt = f"""
                You are a Senior Workplace Strategist for JLL. Evaluate this restack scenario.
                Context: Moving to a product-led model from function silos.
                Phase: {renovation_phase}
                
                Current Board State:
                {board_summary}
                
                Provide a professional 3-paragraph summary on:
                1. Stacking efficiency (capacity usage).
                2. Pod co-location strategy.
                3. Recommendation for the next move phase based on vacancies.
                """
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.info(response.text)
            except Exception as e:
                st.error(f"AI Error: {e}")
