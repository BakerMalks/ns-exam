import pytest
import logging
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter

@pytest.mark.parametrize("random_numbers", [1,2,3,4])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter], indirect=True)
def test_try_run(configs, random_numbers, ammeter):
    assert random_numbers != 2
    if random_numbers == 1:
        print(configs)
    logging.info(ammeter.measure_current())
    time.sleep(1)