from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.depot as depots
from schema.database import get_session
from schema.models import Location

router = APIRouter(prefix="/api/depots", tags=["Depot"])


@router.get(
    "", status_code=status.HTTP_200_OK, response_model=list[Location], tags=["Depot"]
)
async def get_depots(session: Session = Depends(get_session)):
    results = depots.get_depots(session)
    return results


@router.get(
    "/{location_id}",
    status_code=status.HTTP_200_OK,
    response_model=Location,
    tags=["Depot"],
)
async def get_depot(location_id: str, session: Session = Depends(get_session)) -> Location:
    depot = depots.get_depot(session, location_id)
    if not depot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Depot not found"
        )
    return depot


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=Location, tags=["Depot"]
)
async def add_depot(location: Location, session: Session = Depends(get_session)):
    result = depots.add_depot(session, location)
    return result


@router.put(
    "/{location_id}",
    status_code=status.HTTP_200_OK,
    response_model=Location,
    tags=["Depot"],
)
async def update_depot(
    location_id: str, data: Location, session: Session = Depends(get_session)
):
    depot = depots.update_depot(session, location_id, data)
    if depot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Depot not found"
        )
    return depot


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Depot"])
async def delete_depot(location_id: str, session: Session = Depends(get_session)):
    deleted = depots.delete_depot(session, location_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Depot not found"
        )


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
