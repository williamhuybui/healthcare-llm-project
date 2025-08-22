# PowerShell script for Windows
# Create virtual environment if it doesn't exist
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& venv\Scripts\Activate.ps1

# Install dependencies from requirements.txt
Write-Host "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

Write-Host "Environment setup complete!"
Write-Host "To run the FastAPI server, use: python main.py"