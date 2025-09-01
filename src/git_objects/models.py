from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
import hashlib

@dataclass
class GitObject(ABC):
    oid: Optional[str] = field(default=None, init=False)

    @property
    @abstractmethod
    def type(self) -> bytes:
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: bytes) -> "GitObject":
        pass

    def compute_oid(self) -> str:
        """Computes and sets the SHA-1 hash of the object."""
        data = self.serialize()
        header = f"{self.type.decode()} {len(data)}".encode() + b"\x00"
        full_content = header + data
        self.oid = hashlib.sha1(full_content).hexdigest()
        return self.oid

@dataclass
class BlobObject(GitObject):
    data: bytes

    @property
    def type(self) -> bytes:
        return b"blob"

    def serialize(self) -> bytes:
        return self.data

    @classmethod
    def deserialize(cls, data: bytes) -> "BlobObject":
        return cls(data=data)

@dataclass
class TreeEntry:
    mode: bytes
    name: str
    oid: str

@dataclass
class TreeObject(GitObject):
    entries: List[TreeEntry] = field(default_factory=list)

    @property
    def type(self) -> bytes:
        return b"tree"

    def serialize(self) -> bytes:
        output = b""
        # Sort entries by name for canonical representation (Git sorts in a specific way, simplified here to name)
        # Git sorting is slightly weird: directories are sorted as if they end with /, files as is.
        # We will do a simple sort for now.
        sorted_entries = sorted(self.entries, key=lambda e: e.name)
        
        for entry in sorted_entries:
            # Mode name\0hash (binary)
            import binascii
            oid_bytes = binascii.unhexlify(entry.oid)
            output += entry.mode + b" " + entry.name.encode() + b"\x00" + oid_bytes
        return output

    @classmethod
    def deserialize(cls, data: bytes) -> "TreeObject":
        entries = []
        i = 0
        import binascii
        while i < len(data):
            # Find the space between mode and name
            space_idx = data.find(b" ", i)
            if space_idx == -1:
                break
            mode = data[i:space_idx]
            
            # Find the null byte between name and hash
            null_idx = data.find(b"\x00", space_idx)
            if null_idx == -1:
                break
            name = data[space_idx+1:null_idx].decode()
            
            # Read 20 bytes for SHA-1
            oid_bytes = data[null_idx+1:null_idx+21]
            oid = binascii.hexlify(oid_bytes).decode()
            
            entries.append(TreeEntry(mode=mode, name=name, oid=oid))
            i = null_idx + 21
            
        return cls(entries=entries)

@dataclass
class CommitObject(GitObject):
    tree_oid: str
    parent_oids: List[str]
    author: str
    committer: str
    message: str
    
    @property
    def type(self) -> bytes:
        return b"commit"

    def serialize(self) -> bytes:
        lines = []
        lines.append(f"tree {self.tree_oid}".encode())
        for p in self.parent_oids:
            lines.append(f"parent {p}".encode())
        lines.append(f"author {self.author}".encode())
        lines.append(f"committer {self.committer}".encode())
        lines.append(b"")
        lines.append(self.message.encode())
        
        return b"\n".join(lines)

    @classmethod
    def deserialize(cls, data: bytes) -> "CommitObject":
        content = data.decode()
        lines = content.split("\n")
        
        tree_oid = ""
        parent_oids = []
        author = ""
        committer = ""
        message_lines = []
        
        i = 0
        # Parse headers
        while i < len(lines):
            line = lines[i]
            if not line:
                # Empty line indicates end of headers
                i += 1
                break
            
            if line.startswith("tree "):
                tree_oid = line[5:]
            elif line.startswith("parent "):
                parent_oids.append(line[7:])
            elif line.startswith("author "):
                author = line[7:]
            elif line.startswith("committer "):
                committer = line[10:]
            i += 1
            
        # The rest is the message
        message = "\n".join(lines[i:])
        
        return cls(
            tree_oid=tree_oid,
            parent_oids=parent_oids,
            author=author,
            committer=committer,
            message=message
        )
