# CopaSync 2026 Cloud Run Deployment Script for PowerShell
$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  CopaSync 2026: Google Cloud Run Deployment Pipeline" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Prompt for Project ID
$GcpProjectId = Read-Host "Enter your Google Cloud Project ID"
if ([string]::IsNullOrWhiteSpace($GcpProjectId)) {
    Write-Error "GCP Project ID is required."
    exit
}

$GcpRegion = "us-central1"
$RepoName = "copasync-repo"
$ServiceName = "copasync-service"
$ImageName = "copasync-app"

Write-Host "Setting active project to: $GcpProjectId..." -ForegroundColor Yellow
gcloud config set project $GcpProjectId

Write-Host "Enabling Google Cloud APIs (Cloud Build, Cloud Run, Artifact Registry)..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

Write-Host "Creating Google Artifact Registry Repository ($RepoName) in $GcpRegion if needed..." -ForegroundColor Yellow
try {
    gcloud artifacts repositories create $RepoName `
        --repository-format=docker `
        --location=$GcpRegion `
        --description="Docker repository for CopaSync 2026 App"
} catch {
    Write-Host "Repository may already exist, proceeding." -ForegroundColor Gray
}

$ImageTag = "$GcpRegion-docker.pkg.dev/$GcpProjectId/$RepoName/$ImageName:latest"

Write-Host "Submitting Docker build to Google Cloud Build. Tag: $ImageTag..." -ForegroundColor Yellow
gcloud builds submit --tag $ImageTag .

Write-Host "Deploying container image to Google Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --image $ImageTag `
    --region $GcpRegion `
    --platform managed `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 3

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "  Your CopaSync 2026 service is live at the Cloud Run URL." -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
