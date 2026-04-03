"""Command-line interface for award_pynder."""

from __future__ import annotations

import logging
import sys

import click

from award_pynder.search import search_awards
from award_pynder.sources import SOURCE_REGISTRY


@click.command()
@click.argument("keywords", nargs=-1, required=True)
@click.option(
    "--sources",
    "-s",
    default=None,
    help=(
        "Comma-separated list of sources to search. "
        f"Available: {', '.join(sorted(SOURCE_REGISTRY.keys()))}"
    ),
)
@click.option(
    "--from-date",
    "-f",
    default="2019-01-01",
    help="Start date for search (YYYY-MM-DD). Default: 2019-01-01",
)
@click.option(
    "--to-date",
    "-t",
    default=None,
    help="End date for search (YYYY-MM-DD). Default: today",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output CSV file path. Default: print to stdout",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output with progress bars",
)
def main(
    keywords: tuple[str, ...],
    sources: str | None,
    from_date: str,
    to_date: str | None,
    output: str | None,
    verbose: bool,
) -> None:
    """Search for grant awards across multiple funding databases.

    Provide one or more KEYWORDS to search for. You can also pass a path
    to a CSV file containing keywords (one per line).

    Examples:
        award-pynder "climate change" --sources nsf,nih --from-date 2020-01-01

        award-pynder "machine learning" "data science" -s nsf -o results.csv
    """
    if verbose:
        logging.basicConfig(level=logging.INFO)

    # Parse sources
    source_list = None
    if sources:
        source_list = [s.strip() for s in sources.split(",")]

    # Run search
    keyword_list = list(keywords)
    df = search_awards(
        keywords=keyword_list,
        sources=source_list,
        from_date=from_date,
        to_date=to_date,
        verbose=verbose,
    )

    # Output results
    if df.empty:
        click.echo("No results found.", err=True)
        sys.exit(0)

    if output:
        df.to_csv(output, index=False)
        click.echo(f"Wrote {len(df)} results to {output}", err=True)
    else:
        click.echo(df.to_csv(index=False))


if __name__ == "__main__":
    main()
