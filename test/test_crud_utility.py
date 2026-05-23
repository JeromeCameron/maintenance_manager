from datetime import date

from sqlmodel import Session

import crud.utility as utility_crud
from schema.models import Holidays


def make_holiday(name: str = "Independence Day") -> Holidays:
    return Holidays(name=name, holiday_date=date(2025, 8, 6))


class TestHolidays:
    def test_add_holiday(self, session: Session):
        holiday = utility_crud.add_holiday(session, make_holiday())
        assert holiday.holiday_id is not None
        assert holiday.name == "Independence Day"

    def test_get_holidays_empty(self, session: Session):
        assert utility_crud.get_holidays(session) == []

    def test_get_holidays(self, session: Session):
        utility_crud.add_holiday(session, make_holiday("Holiday A"))
        utility_crud.add_holiday(session, make_holiday("Holiday B"))
        assert len(utility_crud.get_holidays(session)) == 2

    def test_get_holiday(self, session: Session):
        added = utility_crud.add_holiday(session, make_holiday())
        result = utility_crud.get_holiday(session, added.holiday_id)
        assert result is not None
        assert result.holiday_id == added.holiday_id

    def test_get_holiday_not_found(self, session: Session):
        assert utility_crud.get_holiday(session, 999) is None

    def test_update_holiday(self, session: Session):
        added = utility_crud.add_holiday(session, make_holiday())
        updated = make_holiday()
        updated.name = "New Year's Day"
        result = utility_crud.update_holiday(session, added.holiday_id, updated)
        assert result is not None
        assert result.name == "New Year's Day"

    def test_update_holiday_not_found(self, session: Session):
        assert utility_crud.update_holiday(session, 999, make_holiday()) is None

    def test_delete_holiday(self, session: Session):
        added = utility_crud.add_holiday(session, make_holiday())
        assert utility_crud.delete_holiday(session, added.holiday_id) is True
        assert utility_crud.get_holiday(session, added.holiday_id) is None

    def test_delete_holiday_not_found(self, session: Session):
        assert utility_crud.delete_holiday(session, 999) is False
