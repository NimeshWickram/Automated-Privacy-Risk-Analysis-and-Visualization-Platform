from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mock_data import DASHBOARD_DATA, APP_DETAILS

app = FastAPI(title="Privacy Risk Analysis API")

# Configure CORS so the React frontend can talk to us if needed 
# (though Vite proxy is better, CORS is a good fallback)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/apps")
def get_apps():
    """
    Returns the list of recently analyzed applications.
    """
    return DASHBOARD_DATA

@app.get("/api/apps/{app_id}")
def get_app_details(app_id: str):
    """
    Returns the detailed privacy risk analysis for a specific app ID.
    """
    if app_id not in APP_DETAILS:
        raise HTTPException(status_code=404, detail="Application not found")
    return APP_DETAILS[app_id]

@app.post("/api/analyze")
def analyze_app():
    """
    Stub for the upload and analyze workflow.
    """
    return {"message": "Analysis started"}
