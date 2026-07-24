"""
Import data/files/FY27 - Budget.csv into the budget table.

Usage:
    uv run python import_budget_fy27.py
"""

import csv
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, text

from schema.database import engine
from schema.models import Budget

CSV_PATH = Path(__file__).parent / "data_files" / "FY27 - Budget.csv"

SKIPPED_GL_CODES = {"5002000-NEG"}


def _to_amount(value: str) -> float:
    return float(value.replace("$", "").replace(",", "").strip())


def _to_month(value: str) -> tuple[int, ...]:
    dt = datetime.strptime(value.strip(), "%d-%b-%Y")
    return dt.replace(day=1).date()


def _financial_year(month) -> str:
    fy_end_year = month.year + 1 if month.month >= 4 else month.year
    return f"FY{str(fy_end_year)[-2:]}"


def import_budget_fy27(session: Session) -> None:
    valid_gl_codes = {row[0] for row in session.exec(text("SELECT gl_code FROM costcentre")).all()}  # type: ignore

    inserted = skipped = 0

    with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            gl_code = (row.get("gl_code") or "").strip()
            if gl_code in SKIPPED_GL_CODES:
                skipped += 1
                continue
            if gl_code not in valid_gl_codes:
                skipped += 1
                continue

            month = _to_month(row["month"])

            session.add(Budget(
                gl_code=gl_code,
                financial_year=_financial_year(month),
                month=month,
                amount=_to_amount(row["amount"]),
                notes=(row.get("notes") or "").strip() or None,
            ))
            inserted += 1

    session.commit()
    print(f"Budget (FY27 CSV) — inserted: {inserted}, skipped: {skipped}")


if __name__ == "__main__":
    with Session(engine) as session:
        import_budget_fy27(session)
