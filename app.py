import streamlit as st
import pandas as pd
from google import genai
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="JLL Restacking Engine v4", layout="wide")

# --- MOCK DATA & CONTEXT ---
# Projected Total Headcount per Product Pod (Base for applying ratios)
projected_base_headcounts = {
    "Swipe My Card": 341,
    "Mobile App": 180,
    "Caff Locator": 254,
    "Cross Section": 133
}

# Ancillary/Specialized Spaces (Decoupled from desk math)
specialized_spaces_list = [
    "Centralized Server Room (15x30)",
    "Brand Strategy Dedicated Open Studio",
    "Tech Digital Lab (12x24)",
    "Tech Locked Storage (12x12)",
    "Comm Locked Room (12x12)",
    "Swipe My Card War Room (12x12)"
]

# Existing Architectural Features (From CSV)
existing_architecture = {
    "3.A": "6 focus desks",
    "3.B": "1 storage room, 1 large partially enclosed collab space",
    "3.C": "1 large open collab space",
    "3.D": "3 enclosed offices",
    "4.A": "1 enclosed office, 1 storage room",
    "4.B": "3 enclosed offices, 1 large collab room",
    "4.C": "6 focus desks",
    "4.D": "1 enclosed office, 6 focus desks"
}

# --- SIDEBAR: MACRO POLICY & SCENARIO ADJUSTMENTS ---
st.sidebar.title("🏢 Scenario Controls")

# Renovation Phase Toggle
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
    # Densified to ~142-143 per quad as per strategic assessment
    quad_capacities = {
        "3.A": 143, "3.B": 143, "3.C": 143, "3.D": 143,
        "4.A": 143, "4.B": 143, "4.C": 143, "4.D": 142
    }

st.sidebar.markdown("---")
st.sidebar.markdown("**2. Adjust Desk Sharing Ratios**")
current_ratios = {}
for pod, hc in projected_base_headcounts.items():
    current_ratios[pod] = st.sidebar.slider(
        f"{pod} Ratio", 
        min_value=0.30, max_value=1.00, value=0.96, step=0.05
    )

# Calculate dynamic demand based on sliders
pod_demand = {pod: math.ceil(hc * current_ratios[pod]) for pod, hc in projected_base_headcounts.items()}

st.sidebar.markdown("---")
st.sidebar.subheader("Total Programmed Demand")
for pod, demand in pod_demand.items():
    st.sidebar.text(f"{pod}: {demand} desks")
st.sidebar.markdown(f"**Total Required: {sum(pod_demand.values())}**")
st.sidebar.markdown(f"**Total Supply: {sum(quad_capacities.values())}**")

# --- MAIN UI: THE RESTACKING BOARD ---
st.title("JLL Restacking Engine: Product-Led Adjacency")
st.markdown(f"**Current State:** `{renovation_phase}` | **Total Assignable Capacity:** `{sum(quad_capacities.values())}`")

# Initialize state for assignments
assignments = {q: [] for q in quad_capacities.keys()}
special_assignments = {q: [] for q in quad_capacities.keys()}

col1, col2, col3, col4 = st.columns(4)
columns = [col1, col2, col3, col4, col1, col2, col3, col4]
quad_keys = list(quad_capacities.keys())

quad_loads = {q: 0 for q in quad_keys}

# First loop: Capture UI assignments
for i, quad in enumerate(quad_keys):
    with columns[i]:
        st.markdown(f"### Quad {quad}")
        st.caption(f"Max Desks: {quad_capacities[quad]}")
        st.caption(f"Architecture: {existing_architecture[quad]}")
        
        # Product Pod Assignment
        assignments[quad] = st.multiselect(
            "Assign Pods", 
            options=list(projected_base_headcounts.keys()), 
            key=f"pod_{quad}",
            label_visibility="collapsed"
        )
        
        # Ancillary Space Assignment
        special_assignments[quad] = st.multiselect(
            "Add Specialized Spaces",
            options=specialized_spaces_list,
            key=f"spec_{quad}"
        )

# Calculate the split load for Pods
pod_quad_count = {pod: sum([1 for q in assignments if pod in assignments[q]]) for pod in projected_base_headcounts}

for quad, assigned_pods in assignments.items():
    for pod in assigned_pods:
        if pod_quad_count[pod] > 0:
            quad_loads[quad] += math.ceil(pod_demand[pod] / pod_quad_count[pod])

# Display the math and warnings
st.markdown("---")
st.subheader("Capacity & Adjacency Analysis")
cols_analysis = st.columns(8)

for i, quad in enumerate(quad_keys):
    capacity = quad_capacities[quad]
    load = quad_loads[quad]
    delta = capacity - load
    
    with cols_analysis[i]:
        st.metric(
            label=f"Quad {quad}", 
            value=f"{load} / {capacity}", 
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
        st.error("API Key not found. Please add GEMINI_API_KEY to your Streamlit secrets.")
    else:
        with st.spinner("Analyzing real estate adjacencies..."):
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                board_state = "\n".join([f"Quad {q} (Cap: {quad_capacities[q]}): Pods -> {assignments[q]}. Existing Architecture -> {existing_architecture[q]}. Assigned Specialized Spaces -> {special_assignments[q]}. Desk Load: {quad_loads[q]}. Remaining Desk Vacancy: {quad_capacities[q] - quad_loads[q]}" for q in quad_keys])
                
                system_prompt = f"""
                You are a Senior Workplace Strategist for JLL. The user is an Occupancy Planner.
                
                Phase: {renovation_phase}
                
                Here is the current Block and Stack scenario:
                {board_state}
                
                Analyze this scenario in 3 professional paragraphs:
                1. Evaluate the physical viability of the assignable desks based on the selected renovation phase.
                2. Evaluate the placement of the Specialized Spaces. Did the planner intelligently align them with the existing architectural features (e.g., placing a locked room where an enclosed office already exists)?
                3. Comment on phased move viability (can two quads be evacuated at once?).
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=system_prompt,
                )
                
                st.info(response.text)
                
            except Exception as e:
                st.error(f"An error occurred with the AI integration: {e}")
