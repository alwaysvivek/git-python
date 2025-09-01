import zlib
import pytest
from src.git_objects.models import BlobObject, TreeObject, CommitObject, TreeEntry
from src.git_objects.parser import read_object

def test_blob_serialization():
    data = b"hello world"
    blob = BlobObject(data)
    assert blob.serialize() == data
    assert blob.type == b"blob"
    
    # Compute OID
    oid = blob.compute_oid()
    # echo -n "blob 11\0hello world" | shasum
    # 3b18e512dba79e4c8300dd08aeb37f8e728b8dad
    assert oid == "95d09f2b10159347eece71399a7e2e907ea3df4f"
    assert blob.oid == "95d09f2b10159347eece71399a7e2e907ea3df4f"

def test_blob_deserialization():
    data = b"hello world"
    blob = BlobObject.deserialize(data)
    assert blob.data == data

def test_tree_serialization():
    # Mock entries
    entry = TreeEntry(mode=b"100644", name="file.txt", oid="3b18e512dba79e4c8300dd08aeb37f8e728b8dad")
    tree = TreeObject(entries=[entry])
    
    serialized = tree.serialize()
    # Mode name\0hash
    expected = b"100644 file.txt\x00" + b"\x3b\x18\xe5\x12\xdb\xa7\x9e\x4c\x83\x00\xdd\x08\xae\xb3\x7f\x8e\x72\x8b\x8d\xad"
    assert serialized == expected

def test_tree_deserialization():
    # 20 bytes for hash
    oid_bytes = b"\x3b\x18\xe5\x12\xdb\xa7\x9e\x4c\x83\x00\xdd\x08\xae\xb3\x7f\x8e\x72\x8b\x8d\xad"
    data = b"100644 file.txt\x00" + oid_bytes
    
    tree = TreeObject.deserialize(data)
    assert len(tree.entries) == 1
    assert tree.entries[0].name == "file.txt"
    assert tree.entries[0].mode == b"100644"
    assert tree.entries[0].oid == "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"

def test_commit_serialization():
    commit = CommitObject(
        tree_oid="abc",
        parent_oids=["def"],
        author="Me <me@example.com> 1234567890 -0500",
        committer="Me <me@example.com> 1234567890 -0500",
        message="Initial commit"
    )
    
    data = commit.serialize()
    assert b"tree abc" in data
    assert b"parent def" in data
    assert b"author Me" in data
    assert b"Initial commit" in data

def test_commit_deserialization():
    data = (
        b"tree abc\n"
        b"parent def\n"
        b"author Me <me@example.com>\n"
        b"committer Me <me@example.com>\n"
        b"\n"
        b"Initial commit"
    )
    commit = CommitObject.deserialize(data)
    assert commit.tree_oid == "abc"
    assert commit.parent_oids == ["def"]
    assert commit.message == "Initial commit"

def test_read_object_real_file(tmp_path):
    git_dir = tmp_path / ".git"
    objects_dir = git_dir / "objects"
    objects_dir.mkdir(parents=True)
    
    # Create a real blob object
    content = b"hello world"
    header = b"blob 11\0"
    store = header + content
    oid = "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"
    
    obj_dir = objects_dir / oid[:2]
    obj_dir.mkdir()
    obj_file = obj_dir / oid[2:]
    
    compressed = zlib.compress(store)
    with open(obj_file, "wb") as f:
        f.write(compressed)
        
    # Read it back using parser
    obj = read_object(oid, git_dir)
    assert isinstance(obj, BlobObject)
    assert obj.data == content
    assert obj.oid == oid

def test_enumerate_objects(tmp_path):
    git_dir = tmp_path / ".git"
    objects_dir = git_dir / "objects"
    objects_dir.mkdir(parents=True)
    
    # Create two objects
    # Object 1: 3b...
    (objects_dir / "3b").mkdir()
    (objects_dir / "3b" / "18e512dba79e4c8300dd08aeb37f8e728b8dad").touch()
    
    # Object 2: ab...
    (objects_dir / "ab").mkdir()
    (objects_dir / "ab" / "cdef12345678901234567890123456789012").touch()
    
    from src.git_objects.parser import enumerate_objects
    oids = enumerate_objects(git_dir)
    
    assert len(oids) == 2
    assert "3b18e512dba79e4c8300dd08aeb37f8e728b8dad" in oids
    assert "abcdef12345678901234567890123456789012" in oids
