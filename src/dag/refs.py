from pathlib import Path
from typing import Optional, Dict

def resolve_ref(git_dir: Path, ref_path: str) -> Optional[str]:
    """Resolves a reference (e.g., 'refs/heads/main') to an OID."""
    full_path = git_dir / ref_path
    if not full_path.exists():
        return None
        
    content = full_path.read_text().strip()
    if content.startswith("ref: "):
        # Recursive resolution (e.g. HEAD -> refs/heads/main)
        return resolve_ref(git_dir, content[5:])
    return content

def resolve_head(git_dir: Path = Path(".git")) -> Optional[str]:
    """Resolves HEAD to the current commit OID."""
    return resolve_ref(git_dir, "HEAD")

def get_branches(git_dir: Path = Path(".git")) -> Dict[str, str]:
    """Returns a dictionary of branch names and their tip OIDs."""
    heads_dir = git_dir / "refs" / "heads"
    branches = {}
    
    if not heads_dir.exists():
        return branches
        
    for path in heads_dir.glob("**/*"):
        if path.is_file():
            # branch name is relative to refs/heads
            branch_name = str(path.relative_to(heads_dir))
            oid = path.read_text().strip()
            branches[branch_name] = oid
            
    return branches
