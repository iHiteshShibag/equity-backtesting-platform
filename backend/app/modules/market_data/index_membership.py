from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_active_tickers(db: Session, index_name: str, as_of: date) -> set[str]:
    """Tickers that were members of `index_name` on `as_of`, per the
    point-in-time index_memberships table (see index_membership_seed.py for
    how it's populated). Returns an empty set (meaning "don't filter") if no
    db session is available, e.g. engine unit tests exercising pure logic
    without a database."""
    if db is None:
        return set()

    rows = db.execute(
        text("""
            SELECT ticker FROM index_memberships
            WHERE index_name = :index_name
              AND start_date <= :as_of
              AND (end_date IS NULL OR end_date >= :as_of)
        """),
        {"index_name": index_name, "as_of": as_of},
    ).fetchall()
    return {r[0] for r in rows}
