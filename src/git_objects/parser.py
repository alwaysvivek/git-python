import zlib
import subprocess
from pathlib import Path
from .models import GitObject, BlobObject, TreeObject, CommitObject

def read_object(oid: str, git_dir: Path = Path(".git")) -> GitObject:
    """Read an object from the git directory by its SHA-1 hash."""
    if len(oid) != 40:
        raise ValueError(f"Invalid Object ID: {oid}")

    path = git_dir / "objects" / oid[:2] / oid[2:]
    if not path.exists():
        # Fallback: Try to read from git (handles packed objects)
        try:
            # 1. Get type
            # Use --git-dir to be explicit and avoid cwd issues
            cmd_type = ["git", "--git-dir", str(git_dir), "cat-file", "-t", oid]
            type_proc = subprocess.run(
                cmd_type,
                capture_output=True,
                check=True
            )
            obj_type = type_proc.stdout.strip()
            
            # 2. Get content (raw)
            cmd_content = ["git", "--git-dir", str(git_dir), "cat-file", obj_type.decode(), oid]
            content_proc = subprocess.run(
                cmd_content,
                capture_output=True,
                check=True
            )
            raw_data = content_proc.stdout
            
            obj: GitObject
            if obj_type == b"blob":
                obj = BlobObject(data=raw_data)
            elif obj_type == b"tree":
                # Tree parsing from raw cat-file output is tricky because 
                # cat-file tree returns parsed text OR raw?? 
                # 'git cat-file tree <oid>' returns RAW binary if we use type name
                # Let's verify... 'git cat-file -p' is pretty.
                # 'git cat-file tree' is RAW.
                obj = TreeObject.deserialize(raw_data)
            elif obj_type == b"commit":
                obj = CommitObject.deserialize(raw_data)
            else:
                raise ValueError(f"Unknown object type: {obj_type}")
                
            obj.oid = oid
            return obj
            
        except subprocess.CalledProcessError as e:
            # If git fails too, then it's really gone
            # Log the stderr for debugging
            stderr_msg = e.stderr.decode() if e.stderr else "No stderr"
            raise FileNotFoundError(f"Object {oid} not found in {path} or packfiles. Git Error: {stderr_msg}")

    with open(path, "rb") as f:
        compressed_data = f.read()
        
    raw_data = zlib.decompress(compressed_data)
    
    # Parse header
    # format: "type size\0content"
    null_idx = raw_data.find(b"\x00")
    if null_idx == -1:
        raise ValueError("Invalid object format (no null byte)")
        
    header = raw_data[:null_idx]
    content = raw_data[null_idx+1:]
    
    type_str, size_str = header.split(b" ")
    # size = int(size_str) # Optional check
    
    obj: GitObject
    if type_str == b"blob":
        obj = BlobObject.deserialize(content)
    elif type_str == b"tree":
        obj = TreeObject.deserialize(content)
    elif type_str == b"commit":
        obj = CommitObject.deserialize(content)
    else:
        raise ValueError(f"Unknown object type: {type_str}")
        
    obj.oid = oid
    return obj

def enumerate_objects(git_dir: Path = Path(".git")) -> list[str]:
    """Yields all object IDs found in the .git/objects/ directory."""
    objects_dir = git_dir / "objects"
    if not objects_dir.exists():
        return []
        
    oids = []
    # .git/objects/XX/YYYY...
    for subdir in objects_dir.iterdir():
        if subdir.is_dir() and len(subdir.name) == 2:
            try:
                # Check if it's hex
                int(subdir.name, 16)
            except ValueError:
                continue
                
            for file in subdir.iterdir():
                if file.is_file():
                    oid = subdir.name + file.name
                    oids.append(oid)
    return oids
