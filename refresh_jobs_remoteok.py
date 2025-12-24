#!/usr/bin/env python3
"""Fetch real jobs from RemoteOK and overwrite data/job_listings.json."""

from core.job_fetcher import JobFetcher


def main() -> None:
    fetcher = JobFetcher()
    print("Fetching real jobs from RemoteOK...")
    result = fetcher.fetch_and_save(
        source="remoteok",
        tags=["python", "sql", "ml"],
        limit=50,
        append=False,
    )
    print("Result:", result)
    print("Job data path:", fetcher.data_path)


if __name__ == "__main__":
    main()
