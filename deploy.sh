#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================================="
echo "  CopaSync 2026: Google Cloud Run Deployment Pipeline"
echo "========================================================="

# 1. Ask for GCP Project ID
if [ -z "$GCP_PROJECT_ID" ]; then
    read -p "Enter your Google Cloud Project ID: " GCP_PROJECT_ID
fi

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "ERROR: GCP Project ID is required."
    exit 1
fi

GCP_REGION="us-central1"
REPO_NAME="copasync-repo"
SERVICE_NAME="copasync-service"
IMAGE_NAME="copasync-app"

echo "Setting active project to: $GCP_PROJECT_ID..."
gcloud config set project "$GCP_PROJECT_ID"

echo "Enabling required Google Cloud APIs (Cloud Build, Cloud Run, Artifact Registry)..."
gcloud services enable run.googleapis.com \
                       cloudbuild.googleapis.com \
                       artifactregistry.googleapis.com

echo "Creating Google Artifact Registry Docker Repository ($REPO_NAME) in $GCP_REGION if it doesn't exist..."
gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$GCP_REGION" \
    --description="Docker repository for CopaSync 2026 App" \
    2>/dev/null || echo "Repository already exists, proceeding."

IMAGE_TAG="$GCP_REGION-docker.pkg.dev/$GCP_PROJECT_ID/$REPO_NAME/$IMAGE_NAME:latest"

echo "Submitting Docker build to Google Cloud Build. Tag: $IMAGE_TAG..."
gcloud builds submit --tag "$IMAGE_TAG" .

echo "Deploying container image to Google Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_TAG" \
    --region "$GCP_REGION" \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 3

echo "========================================================="
echo "  Deployment Complete!"
echo "  Your CopaSync 2026 service is live at the Cloud Run URL above."
echo "========================================================="
