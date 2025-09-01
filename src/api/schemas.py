from typing import List, Optional
from pydantic import BaseModel

class CommitResponse(BaseModel):
    oid: str
    tree_oid: str
    parent_oids: List[str]
    author: str
    committer: str
    message: str

class GraphNode(BaseModel):
    id: str
    label: str
    group: Optional[str] = None
    # Enriching graph for UI details
    message: str
    author: str
    tree_oid: str
    parent_oids: List[str]

class GraphEdge(BaseModel):
    source: str
    target: str

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class TreeEntryResponse(BaseModel):
    mode: str
    name: str
    type: str # 'blob' or 'tree'
    oid: str

class BlobResponse(BaseModel):
    oid: str
    content: str
    size: int

class CreateCommitRequest(BaseModel):
    message: str
    author_name: str = "User"
    author_email: str = "user@example.com"
