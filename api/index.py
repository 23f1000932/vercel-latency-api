import json
import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Initialize the FastAPI app
app = FastAPI()

# --- Enable CORS for POST requests ---
# This is a specific requirement from the prompt.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin
    allow_credentials=True,
    allow_methods=["POST"], # Only allow POST
    allow_headers=["*"],
)

# --- Load Data ---
# Load the telemetry data once when the app starts.
with open("q-vercel-latency.json", "r") as f:
    telemetry_data = json.load(f)

# --- Define Request Body Model ---
# This ensures the incoming JSON has the correct structure.
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

# --- Create the POST Endpoint ---
@app.post("/")
async def get_latency_metrics(request: LatencyRequest):
    # Filter the main dataset to only include records from the requested regions
    relevant_data = [
        record for record in telemetry_data if record.get("region") in request.regions
    ]
    
    results = {}

    # Calculate metrics for each requested region
    for region in request.regions:
        # Get data for the current region
        region_data = [
            record for record in relevant_data if record.get("region") == region
        ]
        
        if not region_data:
            continue

        # Extract specific metrics into lists for calculation
        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_percent"] for r in region_data]

        # Calculate all required values
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        breaches = sum(1 for lat in latencies if lat > request.threshold_ms)

        # Store the results
        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return results
