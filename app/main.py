"""
Main file for the API.
"""
import os
from contextlib import asynccontextmanager
from typing import List, Dict
from fastapi import FastAPI
from pydantic import BaseModel

from app.utils import (
    get_model,
)


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

    model_name: str = os.getenv("MLFLOW_MODEL_NAME")
    model_version: str = os.getenv("MLFLOW_MODEL_VERSION")
    # Load the ML model
    model = get_model(model_name, model_version)
    yield


class ActivityDescriptions(BaseModel):
    """
    Pydantic BaseModel for representing the input data for the API.
    This BaseModel defines the structure of the input data required
    for the API's "/predict-batch" endpoint.

    Attributes:
        text_descriptions (List[str]): The text descriptions.
    """

    text_descriptions: List[str]

    class Config:
        schema_extra = {
            "example": {
                "text_description": [
                    (
                        "LOUEUR MEUBLE NON PROFESSIONNEL EN RESIDENCE DE "
                        "SERVICES (CODE APE 6820A Location de logements)"
                    )
                ]
            }
        }


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
    model_name: str = os.getenv("MLFLOW_MODEL_NAME")
    model_version: str = os.getenv("MLFLOW_MODEL_VERSION")
    return {
        "message": "Request classifier",
        "model_name": f"{model_name}",
        "model_version": f"{model_version}",
    }


@app.get("/predict", tags=["Predict"])
async def predict(
    description: str
) -> Dict:
    """
    Predict good or bad request.
    This endpoint accepts input data as query parameters and uses the loaded
    ML model to predict if the request is good or bad based on the input data.

    Args:

        description (str): The request.

    Returns:

        Dict: 0 or 1
    """
    query = {
        "query": [description],
    }

    predictions = model.predict(query)

    return predictions[0]
