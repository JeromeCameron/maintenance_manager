from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.expense as expenses
from schema.database import get_session
from schema.models import Budget, CostCentre

budget_router = APIRouter(prefix="/api/budgets", tags=["Budget"])
cost_centre_router = APIRouter(prefix="/api/cost-centres", tags=["CostCentre"])


# ------------------------------------------------------------------
# Budget endpoints


@budget_router.get(
    "", status_code=status.HTTP_200_OK, response_model=list[Budget], tags=["Budget"]
)
async def get_budgets(session: Session = Depends(get_session)):
    results = expenses.get_budgets(session)
    return results


@budget_router.get(
    "/{budget_id}",
    status_code=status.HTTP_200_OK,
    response_model=Budget,
    tags=["Budget"],
)
async def get_budget(budget_id: int, session: Session = Depends(get_session)) -> Budget:
    budget = expenses.get_budget(session, budget_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )
    return budget


@budget_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=Budget, tags=["Budget"]
)
async def add_budget(budget: Budget, session: Session = Depends(get_session)):
    result = expenses.add_budget(session, budget)
    return result


@budget_router.put(
    "/{budget_id}",
    status_code=status.HTTP_200_OK,
    response_model=Budget,
    tags=["Budget"],
)
async def update_budget(
    budget_id: int, data: Budget, session: Session = Depends(get_session)
):
    budget = expenses.update_budget(session, budget_id, data)
    if budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )
    return budget


@budget_router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Budget"])
async def delete_budget(budget_id: int, session: Session = Depends(get_session)):
    deleted = expenses.delete_budget(session, budget_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )


# ------------------------------------------------------------------
# Cost Centre endpoints


@cost_centre_router.get(
    "", status_code=status.HTTP_200_OK, response_model=list[CostCentre], tags=["CostCentre"]
)
async def get_cost_centres(session: Session = Depends(get_session)):
    results = expenses.get_cost_centres(session)
    return results


@cost_centre_router.get(
    "/{gl_code}",
    status_code=status.HTTP_200_OK,
    response_model=CostCentre,
    tags=["CostCentre"],
)
async def get_cost_centre(gl_code: str, session: Session = Depends(get_session)) -> CostCentre:
    cost_centre = expenses.get_cost_centre(session, gl_code)
    if not cost_centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cost centre not found"
        )
    return cost_centre


@cost_centre_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=CostCentre, tags=["CostCentre"]
)
async def add_cost_centre(cost_centre: CostCentre, session: Session = Depends(get_session)):
    result = expenses.add_cost_centre(session, cost_centre)
    return result


@cost_centre_router.put(
    "/{gl_code}",
    status_code=status.HTTP_200_OK,
    response_model=CostCentre,
    tags=["CostCentre"],
)
async def update_cost_centre(
    gl_code: str, data: CostCentre, session: Session = Depends(get_session)
):
    cost_centre = expenses.update_cost_centre(session, gl_code, data)
    if cost_centre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cost centre not found"
        )
    return cost_centre


@cost_centre_router.delete("/{gl_code}", status_code=status.HTTP_204_NO_CONTENT, tags=["CostCentre"])
async def delete_cost_centre(gl_code: str, session: Session = Depends(get_session)):
    deleted = expenses.delete_cost_centre(session, gl_code)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cost centre not found"
        )


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
