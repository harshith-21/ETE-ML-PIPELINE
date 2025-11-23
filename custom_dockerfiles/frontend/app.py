"""
FastAPI Frontend for Criteo CTR Prediction
Provides a web UI for users to make predictions using the BentoML service
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Criteo CTR Prediction Service")

# Configuration
BENTO_URL = os.getenv("BENTO_URL", "http://bento-svc.harshith.svc.cluster.local:3000")
PREDICT_ENDPOINT = f"{BENTO_URL}/predict"
HEALTH_ENDPOINT = f"{BENTO_URL}/health"
MODEL_INFO_ENDPOINT = f"{BENTO_URL}/model_info"

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(HEALTH_ENDPOINT, json={})
            bento_status = response.json()
        
        return {
            "status": "healthy",
            "frontend": "running",
            "bento_service": bento_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "frontend": "running",
                "bento_service": "unavailable",
                "error": str(e)
            }
        )

@app.get("/api/model-info")
async def get_model_info():
    """Get model information from BentoML"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(MODEL_INFO_ENDPOINT, json={})
            return response.json()
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/predict")
async def predict(request: Request):
    """Make prediction using BentoML service"""
    try:
        # Get request data
        data = await request.json()
        
        # Validate input
        if "features" not in data:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing 'features' field"}
            )
        
        features = data["features"]
        
        # Validate feature count (should be 39 for Criteo)
        if isinstance(features[0], list) and len(features[0]) != 39:
            return JSONResponse(
                status_code=400,
                content={"error": f"Expected 39 features, got {len(features[0])}"}
            )
        
        # Call BentoML service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                PREDICT_ENDPOINT,
                json={"features": features}
            )
            
            if response.status_code != 200:
                return JSONResponse(
                    status_code=response.status_code,
                    content={"error": f"BentoML service error: {response.text}"}
                )
            
            result = response.json()
            
            # Add metadata
            result["num_predictions"] = len(result.get("predictions", []))
            
            return result
    
    except httpx.TimeoutException:
        logger.error("Prediction request timed out")
        return JSONResponse(
            status_code=504,
            content={"error": "Prediction request timed out"}
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/predict-sample")
async def predict_sample():
    """Make prediction with a sample data"""
    # Sample Criteo features (39 features: 13 integer + 26 categorical converted to integers)
    sample_features = [
        [1, 2, 5, 0, 1382, 4, 15, 2, 181, 1, 2, 0, 3, 
         1, 0, 2, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0]
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                PREDICT_ENDPOINT,
                json={"features": sample_features}
            )
            
            result = response.json()
            result["sample_data"] = sample_features[0]
            
            return result
    
    except Exception as e:
        logger.error(f"Sample prediction failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

