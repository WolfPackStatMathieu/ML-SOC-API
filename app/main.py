"""
API for Request Classification using FastAPI.

This module provides endpoints for classifying requests using a pre-trained Random Forest model
and a preprocessing pipeline. It supports prediction from individual requests and from CSV files.

Endpoints:
----------
- GET / : Returns a welcome message with model details.
- POST /predict : Predicts the classification for a single request.
- POST /predict_csv : Predicts the classification for multiple requests from a CSV file.

Usage:
------
Run the API using the command:
    uvicorn main:app --reload
"""

import os  # Module pour interagir avec le système d'exploitation
from contextlib import (
    asynccontextmanager,
)  # Gère le cycle de vie asynchrone de l'application
from typing import Dict, Optional  # Typage pour les dictionnaires et options
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
)  # Framework FastAPI et gestion des exceptions
from pydantic import BaseModel  # Validation et sérialisation des données
import mlflow  # Module pour le suivi des expériences MLflow
import joblib  # Pour charger le modèle pré-entraîné
import pandas as pd  # Manipulation des données


# Gestionnaire de contexte asynchrone pour la durée de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model  # Déclaration globale pour le modèle
    global complete_pipeline  # Déclaration globale pour le pipeline de prétraitement

    # Vérification de la variable d'environnement pour l'URI de suivi MLflow
    if "MLFLOW_TRACKING_URI" in os.environ:
        print(os.environ["MLFLOW_TRACKING_URI"])
    else:
        print(
            "MLflow was not automatically discovered, a tracking URI must be provided manually."
        )

    MODEL_NAME = "random_forest_detection"  # Nom du modèle MLflow
    VERSION = 6  # Version du modèle

    # Chargement du modèle MLflow
    model = mlflow.pyfunc.load_model(model_uri=f"models:/{MODEL_NAME}/{VERSION}")

    # Chargement du pipeline de prétraitement
    os.system(
        "mc cp s3/mthomassin/preprocessor/complete_preprocessor_pipeline.pkl "
        "./complete_preprocessor_pipeline.pkl"
    )
    complete_pipeline = joblib.load("complete_preprocessor_pipeline.pkl")

    model_name = os.getenv("MLFLOW_MODEL_NAME", MODEL_NAME)
    model_version = os.getenv("MLFLOW_MODEL_VERSION", str(VERSION))
    print(f"model_name = {model_name}")
    print(f"model_version = {model_version}")

    yield  # Assure que le gestionnaire de contexte est utilisé correctement


# Définition du modèle de données pour les requêtes de prédiction
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
                "URL": "/index.html HTTP/1.1",
            }
        }


# Initialisation de l'application FastAPI
app = FastAPI(
    lifespan=lifespan,
    title="Request classifier",
    description="<b>Classifier for bad or good request</b>",
    version="1.0.0",
    root_path="/proxy/5000",
)


# Endpoint de bienvenue
@app.get("/", tags=["Welcome"])
def show_welcome_page():
    MODEL_NAME = "random_forest_detection"
    VERSION = 6
    model_name = os.getenv("MLFLOW_MODEL_NAME", MODEL_NAME)
    model_version = os.getenv("MLFLOW_MODEL_VERSION", str(VERSION))
    return {
        "message": "Hello from Request classifier 2",
        "model_name": model_name,
        "model_version": model_version,
    }


# Endpoint pour prédire la classification d'une requête unique
@app.post("/predict", tags=["Predict"])
async def predict(request: PredictionRequest) -> Dict:
    try:
        data = pd.DataFrame([request.dict()])  # Convertit la requête en DataFrame

        print("Données reçues pour la prédiction:")
        print(data)

        # Renommer les colonnes pour correspondre au dataset original
        data.columns = [
            "Method",
            "User-Agent",
            "Pragma",
            "Cache-Control",
            "Accept",
            "Accept-encoding",
            "Accept-charset",
            "language",
            "host",
            "cookie",
            "content-type",
            "connection",
            "lenght",
            "content",
            "URL",
        ]

        # Ajouter la colonne 'classification' avec une valeur par défaut
        data["classification"] = 0  # ou une autre valeur par défaut

        # Afficher les colonnes avant transformation
        print("Colonnes avant transformation:")
        print(data.columns)

        # Appliquer les transformations de prétraitement
        feature_builder = complete_pipeline.named_steps["feature_builder"]
        X_transformed, _ = feature_builder.transform(data)

        if isinstance(X_transformed, pd.DataFrame):
            print(f"Colonnes après feature_builder.transform: {X_transformed.columns}")
        else:
            print(f"Forme de X_transformed: {X_transformed.shape}")

        preprocessor = complete_pipeline.named_steps["preprocessor"]
        X = preprocessor.transform(X_transformed)

        print("Forme de X après preprocessor.transform:", X.shape)

        # Prédiction
        predictions = model.predict(X)

        url = data["URL"].tolist()[0].split(" ")[0]
        prediction = int(predictions[0])

        return {"url": url, "prediction": prediction}

    except ValueError as e:
        print(f"ValueError: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"ValueError during transformation or prediction: {e}",
        )
    except KeyError as e:
        print(f"KeyError: {e}")
        raise HTTPException(
            status_code=400, detail=f"KeyError during transformation or prediction: {e}"
        )
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during transformation or prediction: {e}",
        )


# Endpoint pour prédire la classification à partir d'un fichier CSV
@app.post("/predict_csv", tags=["Predict CSV"])
async def predict_csv(file: UploadFile = File(...)) -> Dict:
    try:
        # Lire le fichier CSV téléchargé
        df = pd.read_csv(file.file)

        print("Données reçues pour la prédiction à partir du fichier CSV:")
        print(df)

        # Vérifier que le fichier contient les bonnes colonnes
        expected_columns = [
            "Method",
            "User-Agent",
            "Pragma",
            "Cache-Control",
            "Accept",
            "Accept-encoding",
            "Accept-charset",
            "language",
            "host",
            "cookie",
            "content-type",
            "connection",
            "lenght",
            "content",
            "URL",
        ]
        if not all(col in df.columns for col in expected_columns):
            raise HTTPException(
                status_code=400,
                detail="Le fichier CSV ne contient pas les colonnes nécessaires",
            )

        # Ajouter la colonne 'classification' avec une valeur par défaut
        df["classification"] = 0  # ou une autre valeur par défaut

        # Afficher les colonnes avant transformation
        print("Colonnes avant transformation:")
        print(df.columns)

        # Appliquer les transformations de prétraitement
        feature_builder = complete_pipeline.named_steps["feature_builder"]
        X_transformed, _ = feature_builder.transform(df)

        if isinstance(X_transformed, pd.DataFrame):
            print(f"Colonnes après feature_builder.transform: {X_transformed.columns}")
        else:
            print(f"Forme de X_transformed: {X_transformed.shape}")

        preprocessor = complete_pipeline.named_steps["preprocessor"]
        X = preprocessor.transform(X_transformed)

        print("Forme de X après preprocessor.transform:", X.shape)

        # Prédiction
        predictions = model.predict(X)

        # Préparer la réponse
        response = []
        urls = df["URL"].tolist()
        for i, prediction in enumerate(predictions):
            url = urls[i].split(" ")[0]  # Extraire l'URL avant " HTTP/1.1"
            response.append({"url": url, "prediction": int(prediction)})

        return {"predictions": response}

    except ValueError as e:
        print(f"ValueError: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"ValueError during transformation or prediction: {e}",
        )
    except KeyError as e:
        print(f"KeyError: {e}")
        raise HTTPException(
            status_code=400, detail=f"KeyError during transformation ou prediction: {e}"
        )
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during transformation or prediction: {e}",
        )


# Point d'entrée de l'application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
