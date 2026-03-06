#!/usr/bin/env python3
"""Entry point for the GitHub fetch release notes skill."""

import sys

from github_fetch_release_notes.cli import main


if __name__ == "__main__":
    sys.exit(main())
