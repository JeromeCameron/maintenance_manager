from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from auth.dependencies import admin_on_write, get_current_user, write_on_write
from auth.rate_limit import limiter
from routers.asset import asset_model_router, asset_scores_router
from routers.asset import router as asset_router
from routers.auth import router as auth_router
from routers.commodity_rates import router as commodity_rate_router
from routers.depot import router as depot_router
from routers.downtime import downtime_cause_router
from routers.downtime import router as downtime_router
from routers.expense import budget_router, cost_centre_router
from routers.inspection import (
    inspection_result_router,
    inspection_router,
    inspection_template_item_router,
    inspection_template_router,
)
from routers.inventory import (
    equipment_part_router,
    part_category_router,
    part_router,
    part_supplier_router,
    stock_level_router,
    stock_transaction_router,
)
from routers.invoice import router as invoice_router
from routers.issues import router as issue_router
from routers.maintenance import asset_pm_router, pm_plan_router
from routers.po import router as po_router
from routers.supplier import router as supplier_router
from routers.user import router as user_router, self_router as user_self_router
from routers.utility import router as utility_router
from routers.reports import router as reports_router
from routers.workOrders import router as work_order_router
from routers.workOrders import work_order_part_router

app = FastAPI(title="Maintenance Manager API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://10.20.10.50:3000",
        "http://100.66.114.121",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public
app.include_router(auth_router)

# Self-service endpoints: any authenticated user (must be registered before admin-gated routers)
app.include_router(user_self_router, dependencies=[Depends(get_current_user)])

# Admin writes: assets, locations, suppliers, budgets, users
app.include_router(asset_router, dependencies=[Depends(admin_on_write)])
app.include_router(asset_model_router, dependencies=[Depends(admin_on_write)])
app.include_router(asset_scores_router, dependencies=[Depends(admin_on_write)])
app.include_router(depot_router, dependencies=[Depends(admin_on_write)])
app.include_router(supplier_router, dependencies=[Depends(admin_on_write)])
app.include_router(budget_router, dependencies=[Depends(admin_on_write)])
app.include_router(cost_centre_router, dependencies=[Depends(admin_on_write)])
app.include_router(user_router, dependencies=[Depends(admin_on_write)])

# User + admin writes: work orders, downtime, inspections, inventory, finance
app.include_router(work_order_router, dependencies=[Depends(write_on_write)])
app.include_router(issue_router, dependencies=[Depends(write_on_write)])
app.include_router(work_order_part_router, dependencies=[Depends(write_on_write)])
app.include_router(downtime_cause_router, dependencies=[Depends(write_on_write)])
app.include_router(downtime_router, dependencies=[Depends(write_on_write)])
app.include_router(pm_plan_router, dependencies=[Depends(write_on_write)])
app.include_router(asset_pm_router, dependencies=[Depends(write_on_write)])
app.include_router(inspection_template_router, dependencies=[Depends(write_on_write)])
app.include_router(
    inspection_template_item_router, dependencies=[Depends(write_on_write)]
)
app.include_router(inspection_router, dependencies=[Depends(write_on_write)])
app.include_router(inspection_result_router, dependencies=[Depends(write_on_write)])
app.include_router(part_category_router, dependencies=[Depends(write_on_write)])
app.include_router(part_router, dependencies=[Depends(write_on_write)])
app.include_router(equipment_part_router, dependencies=[Depends(write_on_write)])
app.include_router(part_supplier_router, dependencies=[Depends(write_on_write)])
app.include_router(stock_level_router, dependencies=[Depends(write_on_write)])
app.include_router(stock_transaction_router, dependencies=[Depends(write_on_write)])
app.include_router(po_router, dependencies=[Depends(write_on_write)])
app.include_router(invoice_router, dependencies=[Depends(write_on_write)])

app.include_router(commodity_rate_router, dependencies=[Depends(admin_on_write)])

# Reports — any authenticated
app.include_router(reports_router, dependencies=[Depends(get_current_user)])

# Utility — any authenticated
app.include_router(utility_router, dependencies=[Depends(get_current_user)])
