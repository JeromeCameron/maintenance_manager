from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Budget, CostCentre
from utils.utils import clean_update_payload


def get_budgets(session: Session) -> Sequence[Budget]:
    statement = select(Budget)
    results = session.exec(statement).all()
    return results


def get_budget(session: Session, id: int) -> Optional[Budget]:
    budget = session.get(Budget, id)
    return budget


def add_budget(session: Session, budget: Budget) -> Budget:
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


def update_budget(session: Session, id: int, data: Budget) -> Optional[Budget]:
    db_budget: Optional[Budget] = session.get(Budget, id)

    if db_budget is None:
        return None

    budget = clean_update_payload(data.model_dump(exclude_unset=True))
    for key, value in budget.items():
        setattr(db_budget, key, value)

    session.add(db_budget)
    session.commit()
    session.refresh(db_budget)
    return db_budget


def delete_budget(session: Session, id: int) -> bool:
    budget = session.get(Budget, id)
    if budget is None:
        return False
    session.delete(budget)
    session.commit()
    return True


# ------------------------------------------------------------------
# Cost Centres


def get_cost_centres(session: Session) -> Sequence[CostCentre]:
    statement = select(CostCentre)
    results = session.exec(statement).all()
    return results


def get_cost_centre(session: Session, gl_code: str) -> Optional[CostCentre]:
    cost_centre = session.get(CostCentre, gl_code)
    return cost_centre


def add_cost_centre(session: Session, budget: CostCentre) -> CostCentre:
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


def update_cost_centre(
    session: Session, gl_code: str, data: CostCentre
) -> Optional[CostCentre]:
    db_cost_centre: Optional[CostCentre] = session.get(CostCentre, gl_code)

    if db_cost_centre is None:
        return None

    cost_centre = clean_update_payload(data.model_dump(exclude_unset=True))
    for key, value in cost_centre.items():
        setattr(db_cost_centre, key, value)

    session.add(db_cost_centre)
    session.commit()
    session.refresh(db_cost_centre)
    return db_cost_centre


def delete_cost_centre(session: Session, gl_code: str) -> bool:
    cost_centre = session.get(CostCentre, gl_code)
    if cost_centre is None:
        return False
    session.delete(cost_centre)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
