import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock

# Importa tutti i modelli e servizi necessari
from model.menu import MenuItem
from repository.menu_repository import MenuRepository
from service.menu_service import MenuService


# ======================================================================
# --- Test per il MenuService ---
# ======================================================================

@pytest.mark.asyncio
async def test_menu_service_decrement_quantity_succeeds():
    """
    TEST: Verifica che la quantità di un piatto venga decrementata correttamente.
    """
    # --- SETUP ---
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    initial_item = MenuItem(dish_id=dish_id, name="Pizza", price=10.0, available_quantity=5)

    # --- MOCKING ---
    mock_repo = MagicMock(spec=MenuRepository)
    mock_repo.get_menu_item = AsyncMock(return_value=initial_item)
    mock_repo.create_menu_item = AsyncMock() # Usato per sovrascrivere

    # --- ESECUZIONE ---
    menu_service = MenuService(menu_repo=mock_repo)
    result = await menu_service.decrement_item_quantity(kitchen_id, dish_id)

    # --- VERIFICA ---
    assert result is True
    mock_repo.get_menu_item.assert_called_once_with(kitchen_id, dish_id)
    mock_repo.create_menu_item.assert_called_once()
    saved_item = mock_repo.create_menu_item.call_args[0][1]
    assert saved_item.available_quantity == 4


@pytest.mark.asyncio
async def test_menu_service_decrement_quantity_fails_when_out_of_stock():
    """
    TEST: Verifica che il decremento fallisca se la quantità è zero.
    """
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    initial_item = MenuItem(dish_id=dish_id, name="Pizza", price=10.0, available_quantity=0)

    mock_repo = MagicMock(spec=MenuRepository)
    mock_repo.get_menu_item = AsyncMock(return_value=initial_item)
    mock_repo.create_menu_item = AsyncMock()

    menu_service = MenuService(menu_repo=mock_repo)
    result = await menu_service.decrement_item_quantity(kitchen_id, dish_id)

    assert result is False
    mock_repo.create_menu_item.assert_not_called() # Non deve provare a salvare