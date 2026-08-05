import pytest
import logging
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter


@pytest.mark.parametrize("random_numbers", [1,2,3,4])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter], indirect=True)
def test_try_run(configs, random_numbers, ammeter):
    assert random_numbers != 2
    if random_numbers == 1:
        print(configs)
    logging.info(ammeter.measure_current())
    time.sleep(1)

# @pytest.mark.parametrize("ammeter", [pytest.param(GreenleeAmmeter, marks=pytest.mark.circutor)], indirect=True)

@pytest.mark.stability
@pytest.mark.circutor
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter], indirect=True)
def test_circutor_stability(time_to_run, ammeter):
    pass


@pytest.mark.stability
@pytest.mark.entes
@pytest.mark.parametrize("ammeter", [EntesAmmeter], indirect=True)
def test_entes_stability():
    pass


@pytest.mark.stability
@pytest.mark.greenlee
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [GreenleeAmmeter], indirect=True)
def test_greenlee_stability():
    pass
