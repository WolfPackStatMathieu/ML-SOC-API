# ML-SOC-API

## Description
This project provides an API for classifying requests using a pre-trained Random Forest model and a preprocessing pipeline.

## Interactions de l'API

Le schéma suivant illustre les interactions entre l'API, le stockage S3 et le serveur MLflow lors du processus de prédiction :

![Diagramme des interactions de l'API](documentation/Interaction-between-API-S3-Storage-and-MLflow.png)

1. **API FastAPI** :
   - Gère les requêtes des utilisateurs pour les prédictions.
   - Charge le pipeline de prétraitement depuis S3 (MinIO).
   - Charge le modèle de classification depuis MLflow.

2. **Stockage S3 (MinIO)** :
   - Stocke le pipeline de prétraitement utilisé par l'API.

3. **Serveur MLflow** :
   - Fournit le modèle de classification pré-entraîné utilisé par l'API.

### Interactions

- **Charger le pipeline de prétraitement** : L'API FastAPI télécharge le pipeline de prétraitement depuis le stockage S3.
- **Charger le modèle** : L'API FastAPI charge le modèle de classification depuis le serveur MLflow.
