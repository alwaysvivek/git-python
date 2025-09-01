import os
import zlib
import hashlib
import time
from pathlib import Path
from src.git_objects.models import BlobObject, TreeObject, CommitObject, TreeEntry

def write_object(obj, git_dir):
    data = obj.serialize()
    # Compute header and content
    header = f"{obj.type.decode()} {len(data)}".encode() + b"\x00"
    store = header + data
    
    # Compute OID
    oid = hashlib.sha1(store).hexdigest()
    
    # Write to disk
    obj_dir = git_dir / "objects" / oid[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    obj_file = obj_dir / oid[2:]
    
    if not obj_file.exists():
        compressed = zlib.compress(store)
        with open(obj_file, "wb") as f:
            f.write(compressed)
            
    return oid

def main():
    repo_dir = Path("demo_repo")
    if repo_dir.exists():
        import shutil
        shutil.rmtree(repo_dir)
    
    repo_dir.mkdir()
    git_dir = repo_dir / ".git"
    git_dir.mkdir()
    (git_dir / "objects").mkdir()
    (git_dir / "refs" / "heads").mkdir(parents=True)
    (git_dir / "HEAD").write_text("ref: refs/heads/main")
    
    print(f"Creating demo repo in {repo_dir}...")
    
    # Commit 1: Initial
    blob = BlobObject(b"Hello World")
    blob_oid = write_object(blob, git_dir)
    
    tree_entry = TreeEntry(mode=b"100644", name="hello.txt", oid=blob_oid)
    tree = TreeObject(entries=[tree_entry])
    tree_oid = write_object(tree, git_dir)
    
    commit1 = CommitObject(
        tree_oid=tree_oid,
        parent_oids=[],
        author="User <user@example.com>",
        committer="User <user@example.com>",
        message="Initial commit"
    )
    c1_oid = write_object(commit1, git_dir)
    print(f"Created Commit 1: {c1_oid}")
    
    # Commit 2: Update
    blob2 = BlobObject(b"Hello Git Graph")
    blob2_oid = write_object(blob2, git_dir)
    
    tree_entry2 = TreeEntry(mode=b"100644", name="hello.txt", oid=blob2_oid)
    tree2 = TreeObject(entries=[tree_entry2])
    tree2_oid = write_object(tree2, git_dir)
    
    commit2 = CommitObject(
        tree_oid=tree2_oid,
        parent_oids=[c1_oid],
        author="User <user@example.com>",
        committer="User <user@example.com>",
        message="Update text"
    )
    c2_oid = write_object(commit2, git_dir)
    print(f"Created Commit 2: {c2_oid}")
    
    # Update HEAD
    (git_dir / "refs" / "heads" / "main").write_text(c2_oid)
    
    print("\nRepo created. Running demo_dag.py inside it...")
    
    # Run demo_dag.py logic here or subprocess
    import sys
    sys.path.append(str(Path.cwd()))
    from src.dag.builder import DagBuilder, topological_sort
    
    builder = DagBuilder(git_dir)
    dag = builder.build_dag()
    commits = topological_sort(dag)
    
    print("\n--- Log ---")
    for node in commits:
        print(f"* {node.oid[:7]} - {node.commit.message}")

if __name__ == "__main__":
    main()
