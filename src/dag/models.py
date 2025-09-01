from dataclasses import dataclass, field
from typing import List, Set
from src.git_objects.models import CommitObject

@dataclass
class CommitNode:
    oid: str
    commit: CommitObject
    parents: List[str] = field(default_factory=list)
    children: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        # Ensure we use the parents from the commit object if not provided explicitly
        if not self.parents and self.commit.parent_oids:
            self.parents = self.commit.parent_oids
