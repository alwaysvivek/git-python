from pathlib import Path
from src.dag.builder import DagBuilder, topological_sort
from src.dag.refs import resolve_head

def main():
    git_dir = Path(".git")
    if not git_dir.exists():
        print("No .git directory found. Run this from the root of a git repo.")
        return

    print("Building DAG...")
    builder = DagBuilder(git_dir)
    dag = builder.build_dag()
    print(f"Loaded {len(dag)} commits.")
    
    head_oid = resolve_head(git_dir)
    if head_oid:
        print(f"HEAD is at {head_oid[:7]}")

    print("\nLog (Topological Sort):")
    commits = topological_sort(dag)
    for node in commits:
        c = node.commit
        parents = " ".join(p[:7] for p in node.parents)
        print(f"* {node.oid[:7]} ({parents}) - {c.message.splitlines()[0]}")

if __name__ == "__main__":
    main()
