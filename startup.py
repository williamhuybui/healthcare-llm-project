import os
import sys

# Add the site packages path
site_packages = os.path.join(os.path.dirname(__file__), 'env', 'Lib', 'site-packages')
sys.path.insert(0, site_packages)

# Import and run the FastAPI app
from main import app
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)