# System Architecture

## Overview
Git Graph Explorer is a full-stack application that visualizes the internal structure of a Git repository. It bypasses the standard `git` CLI and interacts directly with the `.git` directory to parse objects and construct the commit graph.

## Components

### 1. Backend (Python/FastAPI)
The backend is responsible for:
- **Direct Object Parsing**: Reads binary files from `.git/objects/` (zlib compressed).
- **DAG Construction**: Builds the Directed Acyclic Graph of commits in memory.
- **Topological Sorting**: Orders commits for the linear log view.
- **API Layer**: Exposes REST endpoints for the frontend.

**Key Modules (`src/`):**
- `git_objects/`: Parsers for Commit, Tree, and Blob objects.
- `dag/`: Logic for linking commits (Parents -> Children) and traversing history.
- `api/`: FastAPI routes and Pydantic models.

### 2. Frontend (React)
The frontend visualizes the data:
- **Graph Visualization**: Uses `react-force-graph-2d` to render the commit history.
- **Object Inspector**: Allows navigating through Trees (directories) and viewing Blobs (files).

## Data Flow
1. User opens the App.
2. Backend scans `.git` directory defined by `GIT_DIR`.
3. Backend parses all loose objects and builds the DAG.
4. Frontend fetches the graph structure via `/api/graph`.
5. User clicks a commit -> Frontend fetches commit details (`/api/commits/:oid`).
6. User browses files -> Frontend fetches Tree/Blob content (`/api/tree/:oid`).

## Security & Deployment
- **Read-Only**: The current version is primarily read-only to avoid corrupting the repo.
- **Environment**: Configurable via `GIT_DIR` and `ALLOWED_ORIGINS`.
