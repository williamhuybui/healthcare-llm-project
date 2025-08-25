# Azure Deployment Guide

## Prerequisites
- Azure account with active subscription
- Azure CLI installed (`az --version`)
- Git repository set up

## Deployment Steps

### 1. Create Azure App Service
```bash
# Login to Azure
az login

# Create resource group
az group create --name healthcare-llm-rg --location "East US"

# Create App Service plan
az appservice plan create --name healthcare-llm-plan --resource-group healthcare-llm-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group healthcare-llm-rg --plan healthcare-llm-plan --name healthcare-llm-api --runtime "PYTHON|3.11"
```

### 2. Configure App Settings
```bash
# Set startup file
az webapp config set --resource-group healthcare-llm-rg --name healthcare-llm-api --startup-file "startup.py"

# Set Python version
az webapp config appsettings set --resource-group healthcare-llm-rg --name healthcare-llm-api --settings PYTHON_VERSION=3.11
```

### 3. Deploy Code
```bash
# Configure deployment from local git
az webapp deployment source config-local-git --name healthcare-llm-api --resource-group healthcare-llm-rg

# Add Azure remote
git remote add azure <git-clone-url-from-previous-command>

# Deploy
git add .
git commit -m "Deploy to Azure"
git push azure main
```

### 4. Alternative: Deploy via VS Code
1. Install Azure App Service extension
2. Right-click on project folder
3. Select "Deploy to Web App"
4. Choose your subscription and web app

## Access Your API
Your FastAPI app will be available at:
`https://healthcare-llm-api.azurewebsites.net`

## Troubleshooting
- Check logs: `az webapp log tail --name healthcare-llm-api --resource-group healthcare-llm-rg`
- View in portal: https://portal.azure.com