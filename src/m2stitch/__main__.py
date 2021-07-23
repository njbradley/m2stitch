"""Command-line interface."""
import click

from .stitching import stitch_images


@click.command()
@click.version_option()
def main() -> None:
    """M2Stitch."""


if __name__ == "__main__":
    main(prog_name="m2stitch")  # pragma: no cover
