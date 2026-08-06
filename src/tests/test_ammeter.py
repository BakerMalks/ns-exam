import pytest
import logging

from typing import Callable

from Ammeters.base_ammeter import AmmeterEmulatorBase
from src.utils.result_manager import ResultManager, Sampler, NumericSamplerResult
from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter


@pytest.mark.stability
@pytest.mark.circutor
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter], indirect=True)
def test_circutor_stability(result_manager, make_sampler, time_to_run, ammeter):
    _test_single_ammeter_stability(file_name="ammeter_result", result_manager=result_manager,
                                   make_sampler=make_sampler, time_to_run=time_to_run,
                                   ammeter=ammeter)


@pytest.mark.stability
@pytest.mark.entes
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [EntesAmmeter], indirect=True)
def test_entes_stability(result_manager, make_sampler, time_to_run, ammeter):
    _test_single_ammeter_stability(file_name="ammeter_result", result_manager=result_manager,
                                   make_sampler=make_sampler, time_to_run=time_to_run,
                                   ammeter=ammeter)


@pytest.mark.stability
@pytest.mark.greenlee
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [GreenleeAmmeter], indirect=True)
def test_greenlee_stability(result_manager, make_sampler, time_to_run, ammeter):
    _test_single_ammeter_stability(file_name="ammeter_result", result_manager=result_manager,
                                   make_sampler=make_sampler, time_to_run=time_to_run,
                                   ammeter=ammeter)


@pytest.mark.stability
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter, EntesAmmeter, GreenleeAmmeter], indirect=True)
def test_ammeter_stability(result_manager, make_sampler, time_to_run, ammeter):
    _test_single_ammeter_stability(file_name="ammeter_result", result_manager=result_manager,
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
def test_ammeters_at_same_time_stability(result_manager, make_sampler, time_to_run, ammeters):
    sampler = make_sampler(total_duration_seconds=time_to_run)
    
    # Build target
    targets = {}
    for ammeter in ammeters:
        targets[ammeter.name] = (ammeter.measure_current, (), {})
    
    # Run Sample
    results = sampler.sample_many(targets, NumericSamplerResult)
    summaries = []
    for ammeter_name, res in results.items():
        res.sample_name = ammeter_name
        result_manager.save_result(f"{ammeter_name}Result", res)
        summaries.append(res.get_summary())
    result_manager.save_text("summary", "\n\n".join(summaries))
    
    # Order results
    

def _test_single_ammeter_stability(file_name: str, result_manager: ResultManager, make_sampler: Callable[..., Sampler], time_to_run: int, ammeter: AmmeterEmulatorBase):
    # ammeter.measure_current()
    sampler = make_sampler(total_duration_seconds=time_to_run)
    logging.info(sampler)
    res = sampler.sample(ammeter.measure_current, result_class=NumericSamplerResult)
    logging.info(res)
    result_manager.save_result(file_name, res)
    result_manager.save_text(file_name, res.get_summary())
    
