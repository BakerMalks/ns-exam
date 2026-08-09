import pytest
import pathlib
import logging
import shutil

from typing import Callable, Dict, List
from datetime import datetime

from src.utils.config import load_config
from src.utils.utils import AmmetterManager
from src.utils.result_manager import ResultManager, Sampler
from src.utils.logger import TIME_FORMAT
from Ammeters.base_ammeter import AmmeterEmulatorBase

BASE_FOLDER = pathlib.Path(".")
CONFIG_YAML = pathlib.Path(BASE_FOLDER, "config", "config.yaml")


# Hooks

def pytest_addoption(parser):
    # Add a custom group
    result_group = parser.getgroup("Result options", "Settings for result folder")
     
    # Add a custom command-line flag
    result_group.addoption(
        "--result-subfolder", "--rsf",
        action="store",
        default="",
        help="Target environment for tests (e.g. dev, staging, prod)"
    )
    result_group.addoption(
        "--compact-result", "--cr",
        action="store_true",
        default=False,
        help="Target environment for tests (e.g. dev, staging, prod)"
    )

def pytest_configure(config):
    configs = load_config(str(CONFIG_YAML))
    timestamp = datetime.now().strftime(TIME_FORMAT)
    
    # Set result folder
    main_result_path = pathlib.Path(BASE_FOLDER, configs["result_management"]["folder_name"])
    main_result_path.mkdir(exist_ok=True)
    default_result_path = pathlib.Path(main_result_path, timestamp)
    res_option = config.getoption("--result-subfolder")
    config.option.result_subfolder = pathlib.Path(main_result_path, res_option) if res_option else default_result_path
    config.option.result_subfolder.mkdir(exist_ok=True, parents=True)

    # Set the log file dynamically
    log_filename = "pytest.log"
    log_path = pathlib.Path(config.option.result_subfolder, log_filename)
    
    config.option.log_file = str(pathlib.Path(log_path, ))


# Session Scope

@pytest.fixture(scope="session")
def configs() -> Dict:
    """YAML config content

    Returns:
        Dict: dictonery generated from yaml config file
    """
    return load_config(str(CONFIG_YAML))


@pytest.fixture(scope="session")
def ammeter_manager(configs) -> AmmetterManager:
    """Manager for Ammeter servers.
    for keeping open acrose all the test suit.
    for dont open unneeded ammeters.

    Args:
        configs (Dict): config fixture

    Yields:
        AmmetterManager: manager
    """
    manager = AmmetterManager(configs["ammeters"])
    return manager  # To close the manager we can use yield function


@pytest.fixture(scope="session")
def result_manager(request, configs) -> ResultManager:
    manager = ResultManager(result_folder_path = request.config.option.result_subfolder, analysis_config=configs["analysis"])
    return manager

# Module Scope



# Function Scope

@pytest.fixture
def ammeter(request, ammeter_manager) -> AmmeterEmulatorBase:
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


@pytest.fixture
def ammeters(request, ammeter_manager) -> List[AmmeterEmulatorBase]:
    """For using ammeter in tests
    Used like:
        @pytest.mark.parametrize("ammeters", [[CircutorAmmeter, EntesAmmeter]], indirect=True)
    """
    # Check if is ammeter
    cls_list = request.param
    assert isinstance(cls_list, list), f"{cls_list} isnt a List"
    active_ammeters = []
    for cls in cls_list:
        assert issubclass(cls , AmmeterEmulatorBase), f"{cls} isnt an AmmeterEmulatorBase in a list"
        
        # Get active ammeter from manager
        active_ammeters.append(ammeter_manager.get(cls))

    return active_ammeters


@pytest.fixture
def make_sampler(configs) -> Callable[..., Sampler]:
    """Factory fixture for creating """
    sampelin_config = configs["testing"]["sampling"]
    def _factory(**overrides) -> Sampler:
        return Sampler(
            measurements_count=overrides.get("measurements_count", sampelin_config["measurements_count"]),
            total_duration_seconds=overrides.get("total_duration_seconds", sampelin_config["total_duration_seconds"]),
            sampling_frequency_hz=overrides.get("sampling_frequency_hz", sampelin_config["sampling_frequency_hz"])
        )
    return _factory

# Autouse

@pytest.fixture(autouse=True)
def override_log_name_with_test_name(request):
    """Overrides record.name with the running test name for ALL log calls."""
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        # Force the name field (%(name)s) to be the pytest test name
        record.name = request.node.name
        return record

    logging.setLogRecordFactory(record_factory)
    yield
    logging.setLogRecordFactory(old_factory)


@pytest.fixture(autouse=True)
def override_result_subfolder_with_test_name(request, result_manager: ResultManager):
    """Overrides sub_folder name with the running test name of current test"""
    folder_name = request.node.name.replace("]", "_").replace("[", "_").strip("_")

    result_manager.sub_folder = folder_name
    yield
    result_manager.reset_sub_folder()


@pytest.fixture(scope="session", autouse=True)
def global_teardown(request):
    # Setup code can go here (runs before any tests start)
    yield
    if request.config.getoption("--compact-result"):
        full_res_path: pathlib.Path = request.config.option.result_subfolder
        logging.info(f"Saving result in {full_res_path}.zip")
        shutil.make_archive(base_name=str(full_res_path), format='zip', root_dir=str(full_res_path), )
