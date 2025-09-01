from pathlib import Path
from typing import Dict, List, Set, Deque
from collections import deque

from src.git_objects.parser import read_object
from src.git_objects.models import CommitObject
from src.dag.models import CommitNode
from src.dag.refs import get_branches, resolve_head

class DagBuilder:
    def __init__(self, git_dir: Path = Path(".git")):
        self.git_dir = git_dir
        self.nodes: Dict[str, CommitNode] = {}
        
    def build_dag(self) -> Dict[str, CommitNode]:
        """Builds the commit graph starting from all refs."""
        # Identifying starting points (roots for traversal, tips of branches)
        start_oids = set(get_branches(self.git_dir).values())
        head_oid = resolve_head(self.git_dir)
        if head_oid:
            start_oids.add(head_oid)
            
        queue: Deque[str] = deque(start_oids)
        visited: Set[str] = set()
        
        while queue:
            oid = queue.popleft()
            if oid in visited:
                continue
            visited.add(oid)
            
            try:
                commit_obj = read_object(oid, self.git_dir)
                if not isinstance(commit_obj, CommitObject):
                    continue
                    
                node = CommitNode(oid=oid, commit=commit_obj)
                self.nodes[oid] = node
                
                # Add parents to queue
                for parent_oid in node.parents:
                    queue.append(parent_oid)
                    
            except (ValueError, FileNotFoundError):
                # Handle cases where object is missing or invalid
                continue
                
        # Second pass: Link children
        for oid, node in self.nodes.items():
            for parent_oid in node.parents:
                if parent_oid in self.nodes:
                    self.nodes[parent_oid].children.add(oid)
                    
        return self.nodes

def topological_sort(dag: Dict[str, CommitNode]) -> List[CommitNode]:
    """Sorts commits topologically (children before parents)."""
    # Kahn's algorithm or DFS based.
    # Since it's a history graph, "children before parents" means newer commits first.
    # This is equivalent to reverse topological sort if strictly going parent->child.
    
    # Let's use a simple approach: logic similar to `git log` default.
    # We want to visit nodes that have no unprocessed children.
    
    # Since we want children before parents (new -> old):
    # In-degree here would be "number of processed children" if we go backwards?
    # Actually simpler: standard topological sort on the parent->child graph gives parents first.
    # We want the reverse of that.
    
    # Let's do DFS post-order traversal and reverse result?
    # Or Kahn's algorithm on component.
    
    # Standard terminology:
    # A -> B (A is parent of B). 
    # Visual: B
    #         |
    #         A
    # We want [B, A].
    # This means we output a node only after all its descendants are output?
    # No, we output B first.
    # So we want to pick nodes with in-degree 0 in the CHILD->PARENT graph? No.
    # In the PARENT->CHILD graph (A->B), we want B then A.
    # So we want Reverse Topological Sort.
    
    # 1. Compute in-degree (number of parents)? No, number of children.
    # Wait, DAG edges are CHILD -> PARENT (pointer wise).
    # B has pointer to A.
    # If we topologically sort the "refers to" graph:
    # B refers to A. So A must come after B?
    # Topo sort: "For every directed edge U -> V, vertex U comes before V in the ordering."
    # Edge: B -> A (B is child, A is parent).
    # Topo sort: [B, A].
    # This is exactly what we want!
    
    # So just standard topological sort on the graph where edges are defined by `node.parents`.
    
    result = []
    visited = set()
    temp_mark = set()  # detecting cycles (though git history shouldn't have them)
    
    # We need to ensure we visit all nodes.
    # Start with nodes that are tips (no children in the DAG subset, or rather not pointed to by anyone yet?)
    # Actually just iterate all nodes.
    
    def visit(oid):
        if oid in visited:
            return
        if oid in temp_mark:
            raise ValueError("Cycle detected in commit graph")
            
        temp_mark.add(oid)
        
        node = dag.get(oid)
        if node:
            for parent in node.parents:
                visit(parent)
        
        temp_mark.remove(oid)
        visited.add(oid)
        result.append(node)

    # We want B to come before A.
    # The normal recursion above `visit(parent)` puts parent in result BEFORE the child is added to result (post-order).
    # So `result` will be [A, B].
    # usage `visit(B)` -> calls `visit(A)` -> adds A -> adds B.
    # So we need to reverse the final list.
    
    sorted_oids = sorted(dag.keys()) # Deterministic starting order
    for oid in sorted_oids:
        visit(oid)
        
    return list(reversed(result))
