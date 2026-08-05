import pytest
import pathlib

from src.utils.config import load_config
from src.utils.Utils import AmmetterManager
from src.utils.result_manager import ResultManager
from Ammeters.base_ammeter import AmmeterEmulatorBase

BASE_FOLDER = pathlib.Path(".")
CONFIG_YAML = pathlib.Path(BASE_FOLDER, "config", "config.yaml")

# Session Scope

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
    # Close manager
    pass


@pytest.fixture(scope="session")
def result_manager(configs):
    result_folder = pathlib.Path(BASE_FOLDER, configs["result_management"]["folder_name"])
    result_folder.mkdir(exist_ok=True)
    manager = ResultManager(result_folder)
    yield manager
    # Close manager
    pass

# Module Scope



# Function Scope

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
