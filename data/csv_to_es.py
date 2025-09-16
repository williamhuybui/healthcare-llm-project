import pandas as pd
from elasticsearch import Elasticsearch, helpers
import os 

# Initialize Elasticsearch client
es = Elasticsearch("http://localhost:9200")  # security off as in the Docker run
MOCK_MODE = False

print("Files in directory:", os.listdir('.'))

# Test Elasticsearch connection
try:
    if es.ping():
        print("Connected to Elasticsearch successfully!")
    else:
        print("Failed to connect to Elasticsearch")
        print("WARNING: Elasticsearch not available. Script will create mock data instead.")
        MOCK_MODE = True
except Exception as e:
    print(f"Error connecting to Elasticsearch: {e}")
    print("WARNING: Elasticsearch not available. Script will create mock data instead.")
    print("To use real Elasticsearch, make sure it's running on localhost:9200")
    print("You can start it with: docker run -d --name elasticsearch -p 9200:9200 -e \"discovery.type=single-node\" -e \"xpack.security.enabled=false\" elasticsearch:8.15.0")
    MOCK_MODE = True

def csv_to_es(csv_path, index):
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found, skipping...")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Processing {csv_path} with {len(df)} records for index '{index}'")
    
    if 'MOCK_MODE' in globals() and MOCK_MODE:
        # Mock mode - just show what would be indexed
        print(f"MOCK: Would index {len(df)} documents to '{index}' index")
        print(f"Sample data from {csv_path}:")
        print(df.head(2).to_string())
        print("-" * 50)
        return
    
    try:
        # Optional: define a mapping first so numbers/dates are typed correctly
        if not es.indices.exists(index=index):
            es.indices.create(index=index, mappings={
                "properties": {
                    "premium_monthly": {"type": "float"},
                    "deductible_individual": {"type": "integer"},
                    "deductible_family": {"type": "integer"},
                    "oop_max_individual": {"type": "integer"},
                    "oop_max_family": {"type": "integer"},
                    "effective_start": {"type": "date"},
                    "effective_end": {"type": "date"}
                }
            })
        actions = []
        for doc in df.to_dict(orient="records"):
            actions.append({"_index": index, "_source": doc})
        helpers.bulk(es, actions)
        print(f"Successfully indexed {len(df)} documents to '{index}' index")
    except Exception as e:
        print(f"Error indexing {csv_path}: {e}")

csv_to_es("plans.csv", "plans")
csv_to_es("user_information.csv", "user_information")
csv_to_es("facility.csv", "facility")
csv_to_es("doctor.csv", "doctor")
csv_to_es("coverage.csv", "coverage")
print("Done.")
