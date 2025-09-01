from pathlib import Path
import pytest
import os
from src.api.main import app, service
from httpx import ASGITransport, AsyncClient

import pytest_asyncio

# Fixture for async client
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# We need to point the service to a temporary repo for testing
@pytest.fixture
def mock_repo(tmp_path):
    # Setup a simple repo structure
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "objects").mkdir()
    (git_dir / "refs" / "heads").mkdir(parents=True)
    
    # Point the global service to this tmp path
    service.git_dir = git_dir
    service.builder.git_dir = git_dir  # Fix: update builder path too
    service.dag = {}
    service.sorted_commits = []
    
    # Create some dummy data (using manual injection into service cache or files)
    from src.git_objects.models import CommitObject
    from src.git_objects.parser import read_object
    import hashlib, zlib
    
    def write_commit(msg):
        c = CommitObject(tree_oid="tree", parent_oids=[], author="A", committer="C", message=msg)
        data = c.serialize()
        header = f"commit {len(data)}\0".encode()
        store = header + data
        oid = hashlib.sha1(store).hexdigest()
        
        path = git_dir / "objects" / oid[:2] / oid[2:]
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(zlib.compress(store))
        return oid

    oid1 = write_commit("Initial")
    
    # Write commit 2 with parent
    c2 = CommitObject(tree_oid="tree", parent_oids=[oid1], author="A", committer="C", message="Second")
    data2 = c2.serialize()
    header2 = f"commit {len(data2)}\0".encode()
    store2 = header2 + data2
    oid2 = hashlib.sha1(store2).hexdigest()
    path2 = git_dir / "objects" / oid2[:2] / oid2[2:]
    path2.parent.mkdir(exist_ok=True)
    path2.write_bytes(zlib.compress(store2))
    
    # Set HEAD/Branches
    (git_dir / "HEAD").write_text("ref: refs/heads/main")
    (git_dir / "refs" / "heads" / "main").write_text(oid2)
    
    return git_dir, oid1, oid2

@pytest.mark.asyncio
async def test_health(client, mock_repo):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_get_commits(client, mock_repo):
    response = await client.get("/api/commits")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1  # Should find at least one reachable from main

@pytest.mark.asyncio
async def test_get_commit_detail(client, mock_repo):
    _, oid1, _ = mock_repo
    response = await client.get(f"/api/commits/{oid1}")
    assert response.status_code == 200
    assert response.json()["oid"] == oid1
    assert response.json()["message"] == "Initial"

@pytest.mark.asyncio
async def test_get_graph(client, mock_repo):
    response = await client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data

@pytest.mark.asyncio
async def test_get_branches(client, mock_repo):
    response = await client.get("/api/branches")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "main"
