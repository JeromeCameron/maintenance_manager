from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Location


def get_depots(session: Session) -> Sequence[Location]:
    statement = select(Location)
    results = session.exec(statement).all()
    return results


def get_depot(session: Session, location_id: int) -> Optional[Location]:
    depot = session.get(Location, location_id)
    return depot


def add_depot(session: Session, location: Location) -> Location:
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


def update_depot(
    session: Session, location_id: int, data: Location
) -> Optional[Location]:
    db_location: Optional[Location] = session.get(Location, location_id)

    if db_location is None:
        return None

    location = data.model_dump(exclude_unset=True)
    for key, value in location.items():
        setattr(db_location, key, value)

    session.add(db_location)
    session.commit()
    session.refresh(db_location)
    return db_location


def delete_depot(session: Session, location_id: int) -> bool:
    location = session.get(Location, location_id)
    if location is None:
        return False
    session.delete(location)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
