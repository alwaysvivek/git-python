# Git Internals: How TinyGit Works

TinyGit is not just a wrapper around the `git` CLI; it implements core Git concepts in Python to demonstrate a deep understanding of version control internals.

## The Object Model

Git is a content-addressable filesystem. TinyGit models this in `src/git_objects/models.py`.

### 1. Blobs (Binary Large Objects)
- **Purpose**: Store file content.
- **Structure**: `blob <size>\0<content>`
- **Python Class**: `BlobObject`
- **Behavior**: TinyGit reads raw bytes, but creates a wrapper that can hide content for binary files or large views to keep the UI clean.

### 2. Trees (Directories)
- **Purpose**: Store directory structures and filenames.
- **Structure**: A list of entries: `<mode> <name>\0<sha1>`
- **Python Class**: `TreeObject`
- **Behavior**: TinyGit parses the binary tree format using `TreeObject.deserialize`. It handles the recursive nature of Git trees (trees pointing to other trees).

### 3. Commits (Snapshots)
- **Purpose**: Snapshot of a tree at a point in time, with metadata.
- **Structure**:
  ```text
  tree <tree_sha1>
  parent <parent_sha1>
  author <name> <email> <timestamp>
  committer <name> <email> <timestamp>

  <message>
  ```
- **Python Class**: `CommitObject`
- **Behavior**: TinyGit builds the commit DAG (Directed Acyclic Graph) by linking `CommitObject`s via their `parent_oids`.

## The DAG Builder (`src/dag/builder.py`)

To visualize the graph, TinyGit walks the commit history:
1.  Starts from references in `.git/refs/heads` (branches).
2.  Traverses `parent` pointers recursively.
3.  Topologically sorts commits to ensure children appear before parents (time flow).

## API & Service Layer

-   **`GitService` (`src/api/service.py`)**: The core logic. It orchestrates reading objects, updating HEAD, and effectively acts as the "Git command" runner.
-   **`main.py`**: A FastAPI application that exposes this logic to the React frontend.

## Frontend Visualization

The React frontend uses `react-force-graph-2d` to render the DAG data provided by the backend, allowing for interactive exploration of the commit history.
