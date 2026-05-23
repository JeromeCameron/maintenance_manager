from sqlmodel import Session

import crud.depot as depot_crud
from schema.models import Location, LocationType


def make_location(name: str = "Main Depot") -> Location:
    return Location(
        name=name,
        parish="Kingston",
        supervisor="John Smith",
        contact_no="876-555-0001",
        typ=LocationType.depot,
    )


class TestDepot:
    def test_add_depot(self, session: Session):
        location = depot_crud.add_depot(session, make_location())
        assert location.location_id is not None
        assert location.name == "Main Depot"

    def test_get_depots_empty(self, session: Session):
        assert depot_crud.get_depots(session) == []

    def test_get_depots(self, session: Session):
        depot_crud.add_depot(session, make_location("Depot A"))
        depot_crud.add_depot(session, make_location("Depot B"))
        assert len(depot_crud.get_depots(session)) == 2

    def test_get_depot(self, session: Session):
        added = depot_crud.add_depot(session, make_location())
        result = depot_crud.get_depot(session, added.location_id)
        assert result is not None
        assert result.location_id == added.location_id

    def test_get_depot_not_found(self, session: Session):
        assert depot_crud.get_depot(session, 999) is None

    def test_update_depot(self, session: Session):
        added = depot_crud.add_depot(session, make_location())
        updated = make_location()
        updated.supervisor = "Jane Doe"
        result = depot_crud.update_depot(session, added.location_id, updated)
        assert result is not None
        assert result.supervisor == "Jane Doe"

    def test_update_depot_not_found(self, session: Session):
        assert depot_crud.update_depot(session, 999, make_location()) is None

    def test_delete_depot(self, session: Session):
        added = depot_crud.add_depot(session, make_location())
        assert depot_crud.delete_depot(session, added.location_id) is True
        assert depot_crud.get_depot(session, added.location_id) is None

    def test_delete_depot_not_found(self, session: Session):
        assert depot_crud.delete_depot(session, 999) is False
