from pathlib import Path
import pytest
from src.dag.builder import DagBuilder, topological_sort
from src.git_objects.models import CommitObject

# Mock the parser read_object to avoid needing real files
import src.dag.builder as builder_module

# Create a mock objects store
mock_objects = {}

def mock_read_object(oid, git_dir):
    if oid in mock_objects:
        obj = mock_objects[oid]
        obj.oid = oid
        return obj
    raise ValueError(f"Object {oid} not found")

@pytest.fixture(autouse=True)
def patch_parser(monkeypatch):
    monkeypatch.setattr(builder_module, "read_object", mock_read_object)
    mock_objects.clear()

def create_commit(oid, parent_oids, message=""):
    c = CommitObject(
        tree_oid="tree",
        parent_oids=parent_oids,
        author="Me",
        committer="Me",
        message=message
    )
    mock_objects[oid] = c
    return c

def test_dag_builder_simple_chain(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)
    
    # C1 <- C2 <- C3 (HEAD)
    create_commit("1111", [])
    create_commit("2222", ["1111"])
    create_commit("3333", ["2222"])
    
    (git_dir / "HEAD").write_text("3333")
    
    builder = DagBuilder(git_dir)
    dag = builder.build_dag()
    
    assert len(dag) == 3
    assert dag["3333"].parents == ["2222"]
    assert dag["2222"].parents == ["1111"]
    assert dag["2222"].children == {"3333"}
    assert dag["1111"].children == {"2222"}

def test_topological_sort_merge(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)
    
    # C1 <- C2
    # C1 <- C3
    # C2, C3 <- C4 (Merge)
    create_commit("11", [], "Initial")
    create_commit("22", ["11"], "Feature")
    create_commit("33", ["11"], "Main fix")
    create_commit("44", ["22", "33"], "Merge")
    
    (git_dir / "HEAD").write_text("44")
    
    builder = DagBuilder(git_dir)
    dag = builder.build_dag()
    
    sorted_commits = topological_sort(dag)
    oids = [n.oid for n in sorted_commits]
    
    # Valid order: C4 comes first. C1 comes last.
    # C2 and C3 can be in any order between C4 and C1.
    assert oids[0] == "44"
    assert oids[-1] == "11"
    assert "22" in oids
    assert "33" in oids
