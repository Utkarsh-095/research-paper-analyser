"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routes import papers, qa

app = FastAPI(
    title="Research Paper RAG System",
    description="Upload research papers, get summaries, and ask questions using RAG.",
    version="1.0.0",
)

# CORS – allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(papers.router, prefix="/api")
app.include_router(qa.router, prefix="/api")


@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Database initialized")
    print("✅ Research Paper RAG System is ready!")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Research Paper RAG System"}