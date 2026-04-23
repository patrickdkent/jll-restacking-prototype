# 🏢 JLL Restacking Engine: Proof of Concept

This repository contains a lightweight, interactive occupancy planning tool developed as a proof-of-concept for dynamic restacking and space utilization analysis.

## Overview
Moving a business from function-based silos to a product-led adjacency model requires balancing strict floor capacities against shifting headcount projections. This tool allows Occupancy Planners to model those scenarios in real-time. 

## Key Features
* **Dynamic Demand Calculation:** Adjust macro desk-sharing ratios (e.g., shifting tech teams from 0.96 to 0.80) to instantly visualize the impact on total programmed demand.
* **Interactive Block & Stack:** Assign product pods to specific floor quads to visualize capacity deficits, surpluses, and co-location risks.
* **Agentic Strategy Advisor:** Integrates with the Google GenAI SDK (Gemini 2.5 Flash) to analyze the current staging scenario and provide a professional executive summary on adjacencies and phased-move strategies.

## Tech Stack
* **Frontend/Hosting:** Python, Streamlit Community Cloud
* **Data Processing:** Pandas, Math
* **AI Orchestration:** Google GenAI SDK (`gemini-2.5-flash`)

*Note: All organizational data utilized in this prototype (AcmeCaff) is purely fictional and generated for assessment purposes.*
