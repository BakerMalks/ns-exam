import pytest
import logging
import time

from typing import Callable

from Ammeters.base_ammeter import AmmeterEmulatorBase
from src.utils.result_manager import ResultManager, Sampler, SamplerResult, NumericSamplerResult
from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter


@pytest.mark.parametrize("random_numbers", [1,2,3,4])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter], indirect=True)
def test_try_run(configs, random_numbers, ammeter):
    assert random_numbers != 2
    if random_numbers == 1:
        logging.info(configs)
    logging.info(ammeter.measure_current())
    time.sleep(1)

# @pytest.mark.parametrize("ammeter", [pytest.param(GreenleeAmmeter, marks=pytest.mark.circutor)], indirect=True)

@pytest.mark.stability
@pytest.mark.circutor
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter], indirect=True)
def test_circutor_stability(request, result_manager, make_sampler, time_to_run, ammeter):
    test_name = request.node.name
    _test_single_ammeter_stability(file_name=test_name, result_manager=result_manager,
                                   make_sampler=make_sampler, time_to_run=time_to_run,
                                   ammeter=ammeter)


@pytest.mark.stability
@pytest.mark.entes
@pytest.mark.parametrize("ammeter", [EntesAmmeter], indirect=True)
def test_entes_stability(request, result_manager, make_sampler, time_to_run, ammeter):
    test_name = request.node.name
    _test_single_ammeter_stability(file_name=test_name, result_manager=result_manager,
                                   make_sampler=make_sampler, time_to_run=time_to_run,
                                   ammeter=ammeter)


@pytest.mark.stability
@pytest.mark.greenlee
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [GreenleeAmmeter], indirect=True)
def test_greenlee_stability(request, result_manager, make_sampler, time_to_run, ammeter):
    test_name = request.node.name
    _test_single_ammeter_stability(file_name=test_name, result_manager=result_manager,
                                   make_sampler=make_sampler, time_to_run=time_to_run,
                                   ammeter=ammeter)


@pytest.mark.stability
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter, EntesAmmeter, GreenleeAmmeter], indirect=True)
def test_ammeter_stability(request, result_manager, make_sampler, time_to_run, ammeter):
    test_name = request.node.name
    _test_single_ammeter_stability(file_name=test_name, result_manager=result_manager,
                                   make_sampler=make_sampler, time_to_run=time_to_run,
                                   ammeter=ammeter)


@pytest.mark.stability
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeters", [[CircutorAmmeter, EntesAmmeter],
                                      [CircutorAmmeter, GreenleeAmmeter],
                                      [EntesAmmeter, GreenleeAmmeter],
                                      [CircutorAmmeter, EntesAmmeter, GreenleeAmmeter]],
                         indirect=True, ids=lambda classes: "-".join(cls.name for cls in classes)
                         )
def test_ammeters_at_same_time_stability(request, result_manager, make_sampler, time_to_run, ammeters):
    test_name = request.node.name
    sampler = make_sampler(total_duration_seconds=time_to_run)
    
    # Build target
    targets = {}
    for ammeter in ammeters:
        targets[ammeter.name] = (ammeter.measure_current, (), {})
    
    # Run Sample
    results = sampler.sample_many(targets, NumericSamplerResult)
    for ammeter_name, res in results.items():
        result_manager.save_result(f"{test_name}_{ammeter_name}", res)
    
    # Order results
    

def _test_single_ammeter_stability(file_name: str, result_manager: ResultManager, make_sampler: Callable[..., Sampler], time_to_run: int, ammeter: AmmeterEmulatorBase):
    # ammeter.measure_current()
    sampler = make_sampler(total_duration_seconds=time_to_run)
    logging.info(sampler)
    res = sampler.sample(ammeter.measure_current, result_class=NumericSamplerResult)
    logging.info(res)
    result_manager.save_result(file_name, res)
    
