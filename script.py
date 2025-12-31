import argparse
from pathlib import Path

from rich.console import Console

# from src import (
#     clone_repos,
#     compare_snapshots,
#     create_snapshot_dir,
#     get_snapshots,
#     load_config,
# )


# def run() -> None:
#     parser = argparse.ArgumentParser(description="GitHub Snapshot and Diff Tool")
#     subparsers = parser.add_subparsers(dest="command", required=True)

#     pull_parser = subparsers.add_parser(
#         "pull", help="Pull repositories and create a snapshot"
#     )
#     pull_parser.add_argument(
#         "--config-file",
#         default="links.json",
#         help="Path to JSON file containing repo links",
#     )
#     pull_parser.add_argument(
#         "--snapshots-base-dir", default="snapshots", help="Base directory for snapshots"
#     )

#     compare_parser = subparsers.add_parser("compare", help="Compare two snapshot IDs")
#     compare_parser.add_argument("snapshot1", help="First snapshot ID")
#     compare_parser.add_argument("snapshot2", help="Second snapshot ID")
#     compare_parser.add_argument(
#         "--snapshots-base-dir", default="snapshots", help="Base directory for snapshots"
#     )
#     compare_parser.add_argument(
#         "-v", "--verbose", action="store_true", help="Show full git diff output"
#     )
#     compare_parser.add_argument(
#         "--name", help="Name of the specific repository to compare"
#     )

#     args = parser.parse_args()
#     snapshots_base_dir = Path(args.snapshots_base_dir)
#     snapshots_base_dir.mkdir(exist_ok=True)

#     console = Console()
#     if args.command == "pull":
#         repos = load_config(args.config_file)
#         snapshot_dir, snapshot_id = create_snapshot_dir(snapshots_base_dir)
#         clone_repos(repos, snapshot_dir)
#         console.print(f"[green]Snapshot {snapshot_id} saved in {snapshot_dir}[/]")
#     elif args.command == "compare":
#         snapshots = get_snapshots(snapshots_base_dir)
#         snapshot1 = next(
#             (s for s in snapshots if f"snapshot-{args.snapshot1}-" in s), None
#         )
#         snapshot2 = next(
#             (s for s in snapshots if f"snapshot-{args.snapshot2}-" in s), None
#         )

#         if snapshot1 and snapshot2:
#             if args.name:
#                 compare_snapshots(
#                     snapshot1, snapshot2, snapshots_base_dir, args.verbose, args.name
#                 )
#             else:
#                 compare_snapshots(
#                     snapshot1, snapshot2, snapshots_base_dir, args.verbose
#                 )
#         else:
#             console.print("[red]Invalid snapshot IDs[/]")


# if __name__ == "__main__":
#     run()
