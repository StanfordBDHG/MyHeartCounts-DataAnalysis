"""Command-line interface for myheartcounts-ds."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def generate_types_command(args: argparse.Namespace) -> int:
    """Execute the generate-types command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    from myheartcounts_ds.client import MHC4Client
    from myheartcounts_ds.config import MHCConfig
    from myheartcounts_ds.typegen import (
        discover_types_from_client,
        get_default_output_path,
        write_enum_file,
    )

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_default_output_path()

    # Create config and client
    if args.project:
        config = MHCConfig(project_id=args.project)
    else:
        config = MHCConfig.from_env()

    print(f"Connecting to project: {config.project_id}")
    client = MHC4Client(config=config)

    # Discover types
    print(f"Discovering observation types (sampling up to {args.user_limit} users)...")
    try:
        discovered_types = discover_types_from_client(
            client, user_limit=args.user_limit
        )
    except Exception as e:
        print(f"Error discovering types: {e}", file=sys.stderr)
        return 1

    if not discovered_types:
        print("Warning: No observation types discovered.", file=sys.stderr)
        print("This might indicate an authentication or permissions issue.")
        return 1

    print(f"Discovered {len(discovered_types)} observation types")

    # Group by category for summary
    categories: dict[str, int] = {}
    for dt in discovered_types:
        categories[dt.category] = categories.get(dt.category, 0) + 1

    for category, count in sorted(categories.items()):
        print(f"  - {category}: {count} types")

    # Write the enum file
    print(f"\nWriting enum to: {output_path}")
    try:
        write_enum_file(discovered_types, output_path, project_id=config.project_id)
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        return 1

    print("Done!")
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="mhc-ds",
        description="MyHeartCounts Data Science CLI tools",
    )
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Available commands",
    )

    # generate-types command
    gen_parser = subparsers.add_parser(
        "generate-types",
        help="Discover observation types from Firestore and generate enum",
        description=(
            "Queries the Firestore database to discover all HealthObservation "
            "types and generates a Python enum file with full IDE support."
        ),
    )
    gen_parser.add_argument(
        "--project",
        "-p",
        metavar="PROJECT",
        help=(
            "Firebase project ID to connect to. "
            "If not specified, uses MHC_PROJECT_ID environment variable "
            "or defaults to som-rit-phi-mhc-prod."
        ),
    )
    gen_parser.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help=(
            "Output path for the generated enum file. "
            "Defaults to the typegen/generated_types.py in the package."
        ),
    )
    gen_parser.add_argument(
        "--user-limit",
        "-n",
        type=int,
        default=100,
        metavar="N",
        help=(
            "Maximum number of users to sample when discovering types. "
            "Higher values find more types but take longer. Default: 100"
        ),
    )
    gen_parser.set_defaults(func=generate_types_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
