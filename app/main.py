import os
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, HTTPException
import mlflow
import joblib
import pandas as pd

from utils import get_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for managing the lifespan of the API.
    This context manager is used to load the ML model and other resources
    when the API starts and clean them up when the API stops.
    Args:
        app (FastAPI): The FastAPI application.
    """
    global model
    global complete_pipeline
    
    if "MLFLOW_TRACKING_URI" in os.environ:
        print(os.environ["MLFLOW_TRACKING_URI"])
    else:
        print("MLflow was not automatically discovered, a tracking URI must be provided manually.")

    MODEL_NAME = "random_forest_detection"
    VERSION = 2

    model = mlflow.pyfunc.load_model(
        model_uri=f"models:/{MODEL_NAME}/{VERSION}"
    )

    # Load the preprocessor pipeline
    os.system(f"mc cp s3/mthomassin/preprocessor/complete_preprocessor_pipeline.pkl ./complete_preprocessor_pipeline.pkl")
    complete_pipeline = joblib.load('complete_preprocessor_pipeline.pkl')

    model_name = os.getenv("MLFLOW_MODEL_NAME", MODEL_NAME)
    model_version = os.getenv("MLFLOW_MODEL_VERSION", str(VERSION))
    print(f"model_name = {model_name}")
    print(f"model_version = {model_version}")
    
    # Load the ML model using the utility function
    model = get_model(model_name, model_version)
    
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Request classifier",
    description="Classifier for bad or good request",
    version="0.0.1",
)


@app.get("/", tags=["Welcome"])
def show_welcome_page():
    """
    Show welcome page with current model name and version.
    """
    MODEL_NAME = "random_forest_detection"
    VERSION = 2
    model_name = os.getenv("MLFLOW_MODEL_NAME", MODEL_NAME)
    model_version = os.getenv("MLFLOW_MODEL_VERSION", str(VERSION))
    return {
        "message": "Request classifier",
        "model_name": model_name,
        "model_version": model_version,
    }


@app.post("/predict", tags=["Predict"])
async def predict(description: str) -> Dict:
    """
    Predict good or bad request.
    This endpoint accepts input data as query parameters and uses the loaded
    ML model to predict if the request is good or bad based on the input data.

    Args:
        description (str): The request.

    Returns:
        Dict: 0 or 1
    """
    try:
        # Prepare data for prediction
        data = pd.DataFrame({"URL": [description]})
        
        # Transform data using the complete pipeline
        feature_builder = complete_pipeline.named_steps['feature_builder']
        X_transformed, _ = feature_builder.transform(data)
        preprocessor = complete_pipeline.named_steps['preprocessor']
        X = preprocessor.transform(X_transformed)

        # Make prediction
        predictions = model.predict(X)

        # Prepare response
        url = data['URL'].tolist()[0].split(" ")[0]  # Extract URL before " HTTP/1.1"
        prediction = int(predictions[0])

        return {"url": url, "prediction": prediction}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"ValueError during transformation or prediction: {e}")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"KeyError during transformation or prediction: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during transformation or prediction: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
