#!/bin/bash
set -e

PROJECT_ID=${1:-ucla-sentiment-analysis}
REGION=${2:-us-central1}

echo "Deploying to Google Cloud Project: $PROJECT_ID"

# Set project
gcloud config set project $PROJECT_ID

# Build and deploy
gcloud builds submit --config cloudbuild.yaml .

echo "Deployment completed!"
