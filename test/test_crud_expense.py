from datetime import date

from sqlmodel import Session

import crud.expense as expense_crud
from schema.models import Budget, CostCentre


def make_cost_centre(gl_code: str = "GL-001") -> CostCentre:
    return CostCentre(gl_code=gl_code, description="Operations")


def make_budget(gl_code: str | None = None) -> Budget:
    return Budget(
        gl_code=gl_code,
        financial_year="2025/2026",
        month=date(2025, 4, 1),
        amount=50000.00,
    )


class TestCostCentre:
    def test_add_cost_centre(self, session: Session):
        cc = expense_crud.add_cost_centre(session, make_cost_centre())
        assert cc.gl_code == "GL-001"

    def test_get_cost_centres_empty(self, session: Session):
        assert expense_crud.get_cost_centres(session) == []

    def test_get_cost_centres(self, session: Session):
        expense_crud.add_cost_centre(session, make_cost_centre("GL-001"))
        expense_crud.add_cost_centre(session, make_cost_centre("GL-002"))
        assert len(expense_crud.get_cost_centres(session)) == 2

    def test_get_cost_centre(self, session: Session):
        expense_crud.add_cost_centre(session, make_cost_centre())
        result = expense_crud.get_cost_centre(session, "GL-001")
        assert result is not None
        assert result.gl_code == "GL-001"

    def test_get_cost_centre_not_found(self, session: Session):
        assert expense_crud.get_cost_centre(session, "MISSING") is None

    def test_update_cost_centre(self, session: Session):
        expense_crud.add_cost_centre(session, make_cost_centre())
        updated = make_cost_centre()
        updated.description = "Maintenance"
        result = expense_crud.update_cost_centre(session, "GL-001", updated)
        assert result is not None
        assert result.description == "Maintenance"

    def test_update_cost_centre_not_found(self, session: Session):
        assert expense_crud.update_cost_centre(session, "MISSING", make_cost_centre()) is None

    def test_delete_cost_centre(self, session: Session):
        expense_crud.add_cost_centre(session, make_cost_centre())
        assert expense_crud.delete_cost_centre(session, "GL-001") is True
        assert expense_crud.get_cost_centre(session, "GL-001") is None

    def test_delete_cost_centre_not_found(self, session: Session):
        assert expense_crud.delete_cost_centre(session, "MISSING") is False


class TestBudget:
    def test_add_budget(self, session: Session):
        budget = expense_crud.add_budget(session, make_budget())
        assert budget.id is not None
        assert budget.financial_year == "2025/2026"
        assert budget.amount == 50000.00

    def test_get_budgets_empty(self, session: Session):
        assert expense_crud.get_budgets(session) == []

    def test_get_budgets(self, session: Session):
        expense_crud.add_budget(session, make_budget())
        expense_crud.add_budget(session, make_budget())
        assert len(expense_crud.get_budgets(session)) == 2

    def test_get_budget(self, session: Session):
        added = expense_crud.add_budget(session, make_budget())
        result = expense_crud.get_budget(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_budget_not_found(self, session: Session):
        assert expense_crud.get_budget(session, 999) is None

    def test_update_budget(self, session: Session):
        added = expense_crud.add_budget(session, make_budget())
        updated = make_budget()
        updated.amount = 75000.00
        result = expense_crud.update_budget(session, added.id, updated)
        assert result is not None
        assert result.amount == 75000.00

    def test_update_budget_not_found(self, session: Session):
        assert expense_crud.update_budget(session, 999, make_budget()) is None

    def test_delete_budget(self, session: Session):
        added = expense_crud.add_budget(session, make_budget())
        assert expense_crud.delete_budget(session, added.id) is True
        assert expense_crud.get_budget(session, added.id) is None

    def test_delete_budget_not_found(self, session: Session):
        assert expense_crud.delete_budget(session, 999) is False
