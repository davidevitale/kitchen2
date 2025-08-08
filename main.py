import uvicorn
from fastapi import FastAPI
from api.kitchen_api import router as kitchen_router, kitchen_service
from api.menu_api import router as menu_router, menu_service

from repository.avail_rep import AvailabilityRepository
from repository.MenuRepository import MenuRepository
from service.kitchen_service import KitchenService
from service.menu_service import MenuService

app = FastAPI()

# Inizializza repository e service
availability_repo = AvailabilityRepository()
menu_repo = MenuRepository()

kitchen_svc = KitchenService(availability_repo)
menu_svc = MenuService(menu_repo)

# Assegna service alle API
kitchen_service = kitchen_svc
menu_service = menu_svc

app.include_router(kitchen_router, prefix="/api")
app.include_router(menu_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
