from pathlib import Path
from src.dag.refs import resolve_head, get_branches

def test_resolve_head(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)
    
    # Simple HEAD
    (git_dir / "HEAD").write_text("ref: refs/heads/main")
    (git_dir / "refs" / "heads").mkdir(parents=True)
    (git_dir / "refs" / "heads" / "main").write_text("1234"*10)
    
    assert resolve_head(git_dir) == "1234"*10

def test_resolve_detached_head(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)
    
    # Detached HEAD
    oid = "abcd"*10
    (git_dir / "HEAD").write_text(oid)
    
    assert resolve_head(git_dir) == oid

def test_get_branches(tmp_path):
    git_dir = tmp_path / ".git"
    heads_dir = git_dir / "refs" / "heads"
    heads_dir.mkdir(parents=True)
    
    (heads_dir / "main").write_text("1111"*10)
    (heads_dir / "feat" / "new-feature").parent.mkdir()
    (heads_dir / "feat" / "new-feature").write_text("2222"*10)
    
    branches = get_branches(git_dir)
    assert branches["main"] == "1111"*10
    assert branches["feat/new-feature"] == "2222"*10
