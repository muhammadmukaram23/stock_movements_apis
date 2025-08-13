from fastapi import FastAPI
# from app.routers import airlines,aircraft_types,countries,cities,airports,routes,flights,flight_schedules,flight_prices,users,passenger_profiles,bookings,booking_items,payment_transactions,user_searches,reviews,promotions,user_sessions
from app.routers import roles
from app.routers import branches
from app.routers import categories
from app.routers import users
from app.routers import item
from app.routers import inventory
from app.routers import stock_movement
from app.routers import transfer_requests
from app.routers import dispatch_slip
from app.routers import receiving_slips
from app.routers import reports
from app.routers import dashboard_activity
from app.routers import filter_query
app = FastAPI(
    title="Nrtc API",
    description="API NRTC",
    version="v0"
)
# app.include_router(airlines.router)
app.include_router(roles.router)
app.include_router(branches.router)
app.include_router(categories.router)
app.include_router(users.router)
app.include_router(item.router)
app.include_router(inventory.router)
app.include_router(stock_movement.router)
app.include_router(transfer_requests.router)
app.include_router(dispatch_slip.router)
app.include_router(receiving_slips.router)
app.include_router(reports.router)
app.include_router(dashboard_activity.router)
app.include_router(filter_query.router)