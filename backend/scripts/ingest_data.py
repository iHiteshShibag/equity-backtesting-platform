#!/usr/bin/env python
"""
Data ingestion script for backtesting platform.
Run: python scripts/ingest_data.py
"""

import sys

from app.db.session import SessionLocal
from app.modules.market_data.fetcher import fetch_and_store_prices
from app.modules.market_data.fundamentals_screener import fetch_fundamentals_screener


def main():
    db = SessionLocal()

    try:
        print("\n📊 Starting data ingestion...\n")

        print("1️⃣  Fetching historical price data (2015-present)...")
        fetch_and_store_prices(db, start="2015-01-01")

        print("\n2️⃣  Fetching historical fundamental data (via screener.in)...")
        fetch_fundamentals_screener(db)

        print("\n✅ Data ingestion complete!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()