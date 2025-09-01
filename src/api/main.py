from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pathlib import Path
import os

from src.api.service import GitService
from src.api.schemas import CommitResponse, GraphResponse, TreeEntryResponse, BlobResponse, CreateCommitRequest

import logging

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Git Graph Explorer API")

# Allow CORS
# In production, set ALLOWED_ORIGINS to a comma-separated list of domains
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Service
# By default look in CWD. Can be overridden by env var GIT_DIR.
git_dir_path = os.getenv("GIT_DIR", ".git")
service = GitService(Path(git_dir_path))

@app.on_event("startup")
def startup_event():
    # Reset repo on application startup
    try:
        service.reset_repo()
        logger.info(f"Reset git repo at {service.git_dir}")
    except Exception as e:
        logger.error(f"Failed to reset repo on startup: {e}")

@app.get("/api/commits", response_model=List[CommitResponse])
def get_commits(limit: int = 50, skip: int = 0):
    """Get list of commits (topological order)."""
    return service.get_commits(limit, skip)

@app.get("/api/commits/{oid}", response_model=CommitResponse)
def get_commit(oid: str):
    """Get details of a specific commit."""
    commit = service.get_commit(oid)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    return commit

@app.post("/api/commits", response_model=CommitResponse)
def create_commit(req: CreateCommitRequest):
    """Create a new commit (on current HEAD)."""
    return service.create_commit(req)

# seed_repo endpoint removed

# reset endpoint removed

@app.get("/api/graph", response_model=GraphResponse)
def get_graph():
    """Get the full commit graph (nodes and edges)."""
    return service.get_graph_data()



@app.get("/api/tree/{oid}", response_model=List[TreeEntryResponse])
def get_tree(oid: str):
    tree = service.get_tree(oid)
    if not tree:
         raise HTTPException(status_code=404, detail="Tree not found")
    return tree

@app.get("/api/blob/{oid}", response_model=BlobResponse)
def get_blob(oid: str):
    blob = service.get_blob(oid)
    if not blob:
        raise HTTPException(status_code=404, detail="Blob not found")
    return blob

@app.get("/health")
def health_check():
    return {"status": "ok", "repo": str(service.git_dir)}

