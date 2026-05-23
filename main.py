from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.asset import router as asset_router, asset_model_router, baler_router, asset_scores_router
from routers.depot import router as depot_router
from routers.downtime import router as downtime_router, downtime_cause_router
from routers.expense import budget_router, cost_centre_router
from routers.inspection import (
    inspection_template_router,
    inspection_template_item_router,
    inspection_router,
    inspection_result_router,
)
from routers.inventory import (
    part_category_router,
    part_router,
    equipment_part_router,
    part_supplier_router,
    stock_level_router,
    stock_transaction_router,
)
from routers.invoice import router as invoice_router
from routers.maintenance import pm_plan_router, asset_pm_router
from routers.po import router as po_router
from routers.supplier import router as supplier_router
from routers.user import router as user_router
from routers.utility import router as utility_router
from routers.workOrders import router as work_order_router, work_order_part_router

app = FastAPI(title="Maintenance Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Assets
app.include_router(asset_router)
app.include_router(asset_model_router)
app.include_router(baler_router)
app.include_router(asset_scores_router)

# Locations / Depots
app.include_router(depot_router)

# Work Orders
app.include_router(work_order_router)
app.include_router(work_order_part_router)

# Downtime
app.include_router(downtime_cause_router)
app.include_router(downtime_router)

# Maintenance
app.include_router(pm_plan_router)
app.include_router(asset_pm_router)

# Inspections
app.include_router(inspection_template_router)
app.include_router(inspection_template_item_router)
app.include_router(inspection_router)
app.include_router(inspection_result_router)

# Inventory
app.include_router(part_category_router)
app.include_router(part_router)
app.include_router(equipment_part_router)
app.include_router(part_supplier_router)
app.include_router(stock_level_router)
app.include_router(stock_transaction_router)

# Finance
app.include_router(po_router)
app.include_router(invoice_router)
app.include_router(budget_router)
app.include_router(cost_centre_router)

# People / Orgs
app.include_router(supplier_router)
app.include_router(user_router)

# Utility
app.include_router(utility_router)
