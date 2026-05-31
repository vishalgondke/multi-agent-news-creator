"""Run the full pipeline once from the CLI:  python -m app.orchestration.run_once"""
from __future__ import annotations

import asyncio
import logging
import sys

from app.orchestration.workflow import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main() -> None:
    with_video = "--no-video" not in sys.argv
    stats = asyncio.run(run_pipeline(with_video=with_video))
    print("\n=== Pipeline stats ===")
    for k, v in stats.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
