import os
from contextlib import asynccontextmanager
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow
import joblib
import pandas as pd

from utils import get_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    global complete_pipeline

    if "MLFLOW_TRACKING_URI" in os.environ:
        print(os.environ["MLFLOW_TRACKING_URI"])
    else:
        print("MLflow was not automatically discovered, a tracking URI must be provided manually.")

    MODEL_NAME = "random_forest_detection"
    VERSION = 5

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

    yield

class PredictionRequest(BaseModel):
    Method: str
    User_Agent: str
    Pragma: str
    Cache_Control: str
    Accept: str
    Accept_encoding: str
    Accept_charset: str
    language: str
    host: str
    cookie: str
    content_type: Optional[str]
    connection: str
    lenght: Optional[str]
    content: Optional[str]
    URL: str

    class Config:
        json_schema_extra = {
            "example": {
                "Method": "GET",
                "User_Agent": "Mozilla/5.0",
                "Pragma": "no-cache",
                "Cache_Control": "no-cache",
                "Accept": "text/html",
                "Accept_encoding": "gzip, deflate",
                "Accept_charset": "UTF-8",
                "language": "en-US",
                "host": "example.com",
                "cookie": "example_cookie",
                "content_type": "application/json",
                "connection": "keep-alive",
                "lenght": "0",
                "content": "",
                "URL": "/index.html HTTP/1.1"
            }
        }

app = FastAPI(
    lifespan=lifespan,
    title="Request classifier",
    description="Classifier for bad or good request",
    version="0.0.1",
    root_path="/proxy/5000"
)

@app.get("/", tags=["Welcome"])
def show_welcome_page():
    MODEL_NAME = "random_forest_detection"
    VERSION = 5
    model_name = os.getenv("MLFLOW_MODEL_NAME", MODEL_NAME)
    model_version = os.getenv("MLFLOW_MODEL_VERSION", str(VERSION))
    return {
        "message": "Request classifier",
        "model_name": model_name,
        "model_version": model_version,
    }

@app.post("/predict", tags=["Predict"])
async def predict(request: PredictionRequest) -> Dict:
    try:
        data = pd.DataFrame([request.dict()])

        print("Données reçues pour la prédiction:")
        print(data)

        # Renommer les colonnes pour correspondre au dataset original
        data.columns = [
            'Method', 'User-Agent', 'Pragma', 'Cache-Control',
            'Accept', 'Accept-encoding', 'Accept-charset', 'language', 'host',
            'cookie', 'content-type', 'connection', 'lenght', 'content', 'URL'
        ]

        # Ajouter la colonne 'classification' avec une valeur par défaut
        data['classification'] = 0  # ou une autre valeur par défaut

        # Afficher les colonnes avant transformation
        print("Colonnes avant transformation:")
        print(data.columns)

        # Appliquer les transformations de prétraitement
        feature_builder = complete_pipeline.named_steps['feature_builder']
        X_transformed, _ = feature_builder.transform(data)

        if isinstance(X_transformed, pd.DataFrame):
            print(f"Colonnes après feature_builder.transform: {X_transformed.columns}")
        else:
            print(f"Forme de X_transformed: {X_transformed.shape}")

        preprocessor = complete_pipeline.named_steps['preprocessor']
        X = preprocessor.transform(X_transformed)

        print("Forme de X après preprocessor.transform:", X.shape)

        # Prédiction
        predictions = model.predict(X)

        url = data['URL'].tolist()[0].split(" ")[0]
        prediction = int(predictions[0])

        return {"url": url, "prediction": prediction}

    except ValueError as e:
        print(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=f"ValueError during transformation or prediction: {e}")
    except KeyError as e:
        print(f"KeyError: {e}")
        raise HTTPException(status_code=400, detail=f"KeyError during transformation or prediction: {e}")
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during transformation or prediction: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
