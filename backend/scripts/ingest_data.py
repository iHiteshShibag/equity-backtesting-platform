#!/usr/bin/env python
"""
Data ingestion script for backtesting platform.
Run: python scripts/ingest_data.py
"""

import sys

from app.database import SessionLocal
from app.data.fetcher import fetch_and_store_prices
from app.data.fundamentals import fetch_fundamentals_yfinance


def main():
    db = SessionLocal()

    try:
        print("\n📊 Starting data ingestion...\n")

        print("1️⃣  Fetching historical price data (2015-present)...")
        fetch_and_store_prices(db, start="2015-01-01")

        print("\n2️⃣  Fetching fundamental data (via yfinance)...")
        fetch_fundamentals_yfinance(db)

        print("\n✅ Data ingestion complete!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()