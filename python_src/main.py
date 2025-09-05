import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
from utils.csv_parser import csv_parser
from schema.resolvers import Query

# Create the GraphQL schema
schema = strawberry.Schema(query=Query)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load CSV data on startup
    await csv_parser.load_data()
    print("✅ CSV data loaded successfully")
    yield

# Create FastAPI app
app = FastAPI(
    title="CSV to GraphQL Service",
    description="A Python service that imports CSV files and serves them through GraphQL",
    version="1.0.0",
    lifespan=lifespan
)

# Create GraphQL router
graphql_app = GraphQLRouter(schema, graphiql=True)

# Include the GraphQL router
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    return {
        "message": "CSV to GraphQL Service",
        "graphql_endpoint": "/graphql",
        "graphiql": "/graphql (interactive playground)"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "data_loaded": bool(csv_parser.users)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CSV to GraphQL Service...")
    print("📊 GraphQL endpoint will be available at: http://localhost:8000/graphql")
    print("🎮 GraphiQL playground will be available at: http://localhost:8000/graphql")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)