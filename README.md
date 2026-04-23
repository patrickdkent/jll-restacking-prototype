# 🏢 JLL Restacking Engine: Strategic Adjacency Prototype

This repository contains an interactive occupancy planning tool developed to model complex restacking scenarios, balancing strict floor capacities with existing architectural constraints.

## Overview
Moving a business from function-based silos to an agile, product-led adjacency model requires more than just math—it requires spatial awareness. This tool allows Occupancy Planners to model dynamic headcount density while strategically placing specialized amenity spaces (Labs, War Rooms) into existing hard-walled architecture to minimize construction costs.

## Key Features
* **Architectural Context Integration:** Overlays existing floor plan assets (e.g., enclosed offices, storage rooms) to guide the intelligent placement of specialized ancillary spaces without sacrificing assignable desk capacity.
* **Dynamic Demand Calculation:** Adjust macro desk-sharing ratios (e.g., shifting tech teams from 0.96 to 0.80) to instantly visualize the impact on total programmed demand.
* **Interactive Block & Stack:** Assign product pods to specific floor quads to visualize capacity deficits, surpluses, and co-location risks based on pre- or post-renovation density targets.
* **Agentic Strategy Advisor:** Integrates with the Google GenAI SDK (`gemini-2.5-flash`) to analyze the current staging scenario, evaluate architectural alignment, and provide a professional executive summary on phased-move viability.

## Tech Stack
* **Frontend/Hosting:** Python, Streamlit Community Cloud
* **Data Processing:** Pandas, Math
* **AI Orchestration:** Google GenAI SDK (`gemini-2.5-flash`)

*Note: All organizational data utilized in this prototype (AcmeCaff) is purely fictional and generated for assessment purposes.*
