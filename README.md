# Ammeter Emulators

This project provides emulators for different types of ammeters: Greenlee, ENTES, and CIRCUTOR. Each ammeter emulator runs on a separate thread and can respond to current measurement requests.

## Project Structure

- `Ammeters/`
  - `main.py`: Main script to start the ammeter emulators and request current measurements.
  - `Circutor_Ammeter.py`: Emulator for the CIRCUTOR ammeter.
  - `Entes_Ammeter.py`: Emulator for the ENTES ammeter.
  - `Greenlee_Ammeter.py`: Emulator for the Greenlee ammeter.
  - `base_ammeter.py`: Base class for all ammeter emulators.
  - `client.py`: Client to request current measurements from the ammeter emulators.
- `config/`
  - `config.yaml`: Configuration file for the ammeter emulators.
- `examples/`
  - `run_test.py`: super lyze example for run test **don't use it**.
- `src/`
  - `tests/`
    - `test_ammeter.py`: test files
  - `testing/`
    - `AmmeterTester.py`: Class to test the ammeter emulators.
  - `utils/`
    - `config.py`: Configuration settings.
    - `logger.py`: Logging setup.
    - `Utils.py`: Utility functions, including `generate_random_float`.

# Ammeter Emulators

## Greenlee Ammeter

- **Port**: 5000
- **Command**: `MEASURE_GREENLEE -get_measurement`
- **Measurement Logic**: Calculates current using voltage (1V - 10V) and (0.1Ω - 100Ω).
- **Measurement method** : Ohm's Law: I = V / R

## ENTES Ammeter

- **Port**: 5001
- **Command**: `MEASURE_ENTES -get_data`
- **Measurement Logic**: Calculates current using magnetic field strength (0.01T - 0.1T) and calibration factor (500 - 2000).
- **Measurement method** : Hall Effect: I = B * K

## CIRCUTOR Ammeter

- **Port**: 5002
- **Command**: `MEASURE_CIRCUTOR -get_measurement`
- **Measurement Logic**: Calculates current using voltage values (0.1V - 1.0V) over a number of samples and a random time step (0.001s - 0.01s).
- **Measurement method** : Rogowski Coil Integration: I = ∫V dt

## Usage

To start the virtual environment, run the `setup_env.py` script:
```sh
python setup_env.py
# PowerShell activation
.\.venv\Scripts\Activate.ps1
# Windows cmd activation
.venv\Scripts\activate.bat
# Linux activation
source .venv/bin/activate
```

To start the ammeter emulators and request current measurements, run the `main.py` script:
```sh
python main.py
```

To run all tests:
```sh
pytest
```

To run all tests and show logs:
```sh
pytest -s
```

To Run a subset of the tests by mark:
```sh
pytest -s -m "greenlee"
```

To Run a subset of the tests by test function fingerprint:
```sh
pytest -s -k "test_run_as"
# will run all the test that has test_run_as in there name. exemple:
# will run test_run_as_python, aaa_test_run_as_ssaas
# wont run test_r_un_as
```

To Run all test in subfolder / file:
```sh
pytest -s src\\tests\\test_ammeter.py
# will run all the test that has test_run_as in there name. exemple:
# will run test_run_as_python, aaa_test_run_as_ssaas
# wont run test_r_un_as
```

To Run a single test:
```sh
pytest -s src\\tests\\test_ammeter.py::test_run_as_python
```

To Change Log and result subfolder
To Run a single test:
```sh
pytest -s src\\tests\\test_ammeter.py::test_run_as_python --result-subfolder MyRun
# will be saved at a folder named MyRun in the "result_management:folder_name" folder from yaml
```