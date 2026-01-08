from web.routes.auth import router as auth_router
from web.routes.dashboard import router as dashboard_router
from web.routes.marking import router as marking_router
from web.routes.batch import router as batch_router

__all__ = ["auth_router", "dashboard_router", "marking_router", "batch_router"]
