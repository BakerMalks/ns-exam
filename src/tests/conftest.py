import pytest
import pathlib

from src.utils.config import load_config
from src.utils.Utils import AmmetterManager
from Ammeters.base_ammeter import AmmeterEmulatorBase

CONFIG_YAML = pathlib.Path("config", "config.yaml")


@pytest.fixture(scope="session")
def configs():
    """YAML config content

    Returns:
        Dict: dictonery generated from yaml config file
    """
    return load_config(str(CONFIG_YAML))


@pytest.fixture(scope="session")
def ammeter_manager(configs):
    """Manager for Ammeter servers.
    for keeping open acrose all the test suit.
    for dont open unneeded ammeters.

    Args:
        configs (Dict): config fixture

    Yields:
        AmmetterManager: manager
    """
    manager = AmmetterManager(configs["ammeters"])
    yield manager


@pytest.fixture
def ammeter(request, ammeter_manager):
    """For using ammeter in tests
    Used like:
        @pytest.mark.parametrize("ammeter", [CircutorAmmeter], indirect=True)
    """
    # Check if is ammeter
    cls = request.param
    assert issubclass(cls , AmmeterEmulatorBase), f"{cls} isnt an AmmeterEmulatorBase"
    
    # Get active ammeter from manager
    active_ammeter = ammeter_manager.get(cls)
    return active_ammeter
    