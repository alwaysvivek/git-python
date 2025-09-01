from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import time
from src.dag.builder import DagBuilder, topological_sort
from src.dag.refs import resolve_head, get_branches
from src.git_objects.models import CommitObject, TreeObject, BlobObject
from src.git_objects.parser import read_object
import hashlib
import zlib
from src.dag.models import CommitNode
from src.api.schemas import CommitResponse, GraphResponse, GraphNode, GraphEdge, TreeEntryResponse, BlobResponse, CreateCommitRequest
import shutil

import os
import stat

def force_rmtree(path: Path):
    """Recursively delete a directory, handling read-only files."""
    if not path.exists():
        return

    def on_error(func, path, exc_info):
        """
        Error handler for shutil.rmtree.
        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.
        If the error is for another reason it re-raises the error.
        """
        # Is the error an access error?
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        else:
            raise

    shutil.rmtree(path, onerror=on_error)

class GitService:
    def __init__(self, git_dir: Path = Path(".git")):
        self.git_dir = git_dir.resolve()
        self.builder = DagBuilder(self.git_dir)
        self.dag: Dict[str, CommitNode] = {}
        self.sorted_commits: List[CommitNode] = []
        
    # seed_repo method removed

    def refresh(self):
        """Rebuilds the cache."""
        self.dag = self.builder.build_dag()
        self.sorted_commits = topological_sort(self.dag)
        
    def ensure_loaded(self):
        if not self.dag:
            self.refresh()

    def get_commit(self, oid: str) -> Optional[CommitResponse]:
        self.ensure_loaded()
        node = self.dag.get(oid)
        if not node:
            return None
        return self._to_response(node)

    def get_commits(self, limit: int = 50, skip: int = 0) -> List[CommitResponse]:
        self.ensure_loaded()
        # topological_sort returns newest first (children before parents) if using my previous logic
        # Slice the list
        selection = self.sorted_commits[skip : skip + limit]
        return [self._to_response(node) for node in selection]

    def get_graph_data(self) -> GraphResponse:
        self.ensure_loaded()
        nodes = []
        edges = []
        
        for oid, node in self.dag.items():
            # Create Node
            # Use first line of message as label, truncated
            short_msg = node.commit.message.splitlines()[0][:30] if node.commit.message else ""
            label = f"{oid[:7]} - {short_msg}"
            
            nodes.append(GraphNode(
                id=oid, 
                label=label, 
                group="commit",
                message=node.commit.message,
                author=node.commit.author,
                tree_oid=node.commit.tree_oid or "",
                parent_oids=node.commit.parent_oids
            ))
            
            # Create Edges (Child -> Parent to show flow of time? Or Parent -> Child?)
            # Usually Git graphs usually show Parent -> Child arrows (history grows) OR Child -> Parent (pointing to dependency).
            # "from": parent, "to": child is typical for visual direction of "time flow" downwards/rightwards.
            for parent in node.parents:
                # Edge from Child to Parent (Git style: New -> Old)
                edges.append(GraphEdge(source=oid, target=parent))
                
        return GraphResponse(nodes=nodes, edges=edges)

    # get_branches removed for simplification



    def create_commit(self, req: CreateCommitRequest) -> CommitResponse:
        # 1. Resolve Parent
        head_oid = resolve_head(self.git_dir)
        parent_oids = [head_oid] if head_oid else []
        
        # 2. Determine Tree
        tree_oid = None
        
        # Try to create tree from current index (staging area)
        # This allows the user to 'git add' files and then commit via UI
        import subprocess
        try:
            # We must run this in the working directory (parent of .git)
            # and point to the .git dir
            proc = subprocess.run(
                ["git", "--git-dir", str(self.git_dir), "write-tree"], 
                cwd=self.git_dir.parent,
                capture_output=True, 
                check=True
            )
            tree_oid = proc.stdout.decode().strip()
        except Exception as e:
            print(f"Backend: git write-tree failed ({e}), falling back to HEAD's tree")

        # Fallback: if head exists, reuse its tree
        if not tree_oid and head_oid:
            head_commit = read_object(head_oid, self.git_dir)
            if isinstance(head_commit, CommitObject):
                tree_oid = head_commit.tree_oid
        
        # Fallback: empty tree
        if not tree_oid:
             # Create empty tree
             tree = TreeObject(entries=[])
             tree_data = tree.serialize()
             tree_header = f"tree {len(tree_data)}\0".encode()
             tree_store = tree_header + tree_data
             tree_oid = hashlib.sha1(tree_store).hexdigest()
             
             # Write tree
             self._write_loose_object(tree_oid, tree_store)

        # 3. Create Commit Object
        # Timestamp for uniqueness
        ts = int(time.time())
        tz = "+0000"
        author_str = f"{req.author_name} <{req.author_email}> {ts} {tz}"
        committer_str = author_str
        
        commit = CommitObject(
            tree_oid=tree_oid,
            parent_oids=parent_oids,
            author=author_str,
            committer=committer_str,
            message=req.message
        )
        
        # 4. Write Commit
        commit_data = commit.serialize()
        commit_header = f"commit {len(commit_data)}\0".encode()
        commit_store = commit_header + commit_data
        commit_oid = hashlib.sha1(commit_store).hexdigest()
        
        self._write_loose_object(commit_oid, commit_store)
        
        # 5. Update HEAD
        # We assume main branch for now
        # Check if HEAD is detached or ref
        head_path = self.git_dir / "HEAD"
        if head_path.exists():
            content = head_path.read_text().strip()
            if content.startswith("ref: "):
                ref_path = self.git_dir / content[5:]
                ref_path.parent.mkdir(parents=True, exist_ok=True)
                ref_path.write_text(commit_oid)
            else:
                # Detached HEAD, just update HEAD
                head_path.write_text(commit_oid)
        else:
            # Create default main
            (self.git_dir / "refs" / "heads" / "main").parent.mkdir(parents=True, exist_ok=True)
            (self.git_dir / "refs" / "heads" / "main").write_text(commit_oid)
            head_path.write_text("ref: refs/heads/main")

        # 6. Refresh DAG
        self.refresh()
        
        # Return response
        # We need to fetch the node we just added from DAG or construct it
        return self.get_commit(commit_oid)
    
    # Branch and Checkout methods Removed as per user request
    # Only get_branches is kept for DAG readiness, but create_branch/checkout disallowed.
    
    def reset_repo(self):
        """Hard reset: Delete .git and re-initialize."""
        if self.git_dir.exists():
            print(f"Backend: Resetting repo at {self.git_dir}")
            try:
                force_rmtree(self.git_dir)
            except Exception as e:
                print(f"Backend: Error deleting .git root: {e}")
                # Detailed fallback
                for child in self.git_dir.iterdir():
                    try:
                       if child.is_dir():
                           force_rmtree(child)
                       else:
                           child.unlink()
                    except Exception as child_e:
                        print(f"Backend: Failed to delete {child}: {child_e}")
        
        # Give OS a moment
        time.sleep(0.1)

        # Re-init (Basic structure)
        self.git_dir.mkdir(exist_ok=True)
        (self.git_dir / "objects").mkdir(exist_ok=True)
        (self.git_dir / "refs" / "heads").mkdir(parents=True, exist_ok=True)
        
        # Default HEAD
        (self.git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        
        # Clear cache
        self.dag = {}
        self.sorted_commits = []

    def _write_loose_object(self, oid: str, data: bytes):
        path = self.git_dir / "objects" / oid[:2] / oid[2:]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(zlib.compress(data))
            # Make read-only to mimic git behavior
            os.chmod(path, stat.S_IREAD)

    def get_tree(self, oid: str) -> Optional[List[TreeEntryResponse]]:
        obj = read_object(oid, self.git_dir)
        if not isinstance(obj, TreeObject):
            return None
            
        entries = []
        for e in obj.entries:
            # Determine type from mode
            # Mode is bytes, e.g. b'40000' or b'100644'
            mode_str = e.mode.decode()
            obj_type = "blob"
            if mode_str == "40000" or mode_str == "040000":
                obj_type = "tree"
                
            entries.append(TreeEntryResponse(
                mode=mode_str,
                name=e.name,
                type=obj_type,
                oid=e.oid
            ))
        return entries

    def get_blob(self, oid: str) -> Optional[BlobResponse]:
        obj = read_object(oid, self.git_dir)
        if not isinstance(obj, BlobObject):
            return None
            
        # Try to decode content
        content_str = "<Binary Data>"
        try:
            content_str = obj.data.decode("utf-8")
        except UnicodeDecodeError:
            pass
            
        return BlobResponse(
            oid=oid,
            size=len(obj.data),
            content=content_str,
            type="blob"
        )

    def _to_response(self, node: CommitNode) -> CommitResponse:
        return CommitResponse(
            oid=node.oid,
            tree_oid=node.commit.tree_oid,
            parent_oids=node.commit.parent_oids,
            author=node.commit.author,
            committer=node.commit.committer,
            message=node.commit.message
        )
