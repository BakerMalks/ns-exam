import pytest
import logging

from typing import Callable, Dict, Optional

from Ammeters.base_ammeter import AmmeterEmulatorBase
from src.utils.result_manager import ResultManager, Sampler, NumericSamplerResult
from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter


STD_CUTOFF = 10

@pytest.mark.stability
@pytest.mark.circutor
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter], indirect=True)
def test_circutor_stability(result_manager, make_sampler, time_to_run, ammeter):
    sampling_kwargs = {"total_duration_seconds": time_to_run}
    res = _test_single_ammeter_stability(file_name="ammeter_result",
                                         result_manager=result_manager,
                                         make_sampler=make_sampler,
                                         sampling_kwargs=sampling_kwargs,
                                         ammeter=ammeter)
    assert res.std() <= STD_CUTOFF, "Standard deviation is to large for stable result"


@pytest.mark.stability
@pytest.mark.entes
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [EntesAmmeter], indirect=True)
def test_entes_stability(result_manager, make_sampler, time_to_run, ammeter):
    sampling_kwargs = {"total_duration_seconds": time_to_run}
    res = _test_single_ammeter_stability(file_name="ammeter_result",
                                         result_manager=result_manager,
                                         make_sampler=make_sampler,
                                         sampling_kwargs=sampling_kwargs,
                                         ammeter=ammeter)
    assert res.std() <= STD_CUTOFF, "Standard deviation is to large for stable result"


@pytest.mark.stability
@pytest.mark.greenlee
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("ammeter", [GreenleeAmmeter], indirect=True)
def test_greenlee_stability(result_manager, make_sampler, time_to_run, ammeter):
    sampling_kwargs = {"total_duration_seconds": time_to_run}
    res = _test_single_ammeter_stability(file_name="ammeter_result",
                                         result_manager=result_manager,
                                         make_sampler=make_sampler,
                                         sampling_kwargs=sampling_kwargs,
                                         ammeter=ammeter)
    assert res.std() <= STD_CUTOFF, "Standard deviation is to large for stable result"


@pytest.mark.stability
@pytest.mark.parametrize("time_to_run", [10, 30])
@pytest.mark.parametrize("sampling_frequency_hz", [1, 30])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter, EntesAmmeter, GreenleeAmmeter], indirect=True)
def test_ammeter_stability(result_manager, make_sampler, time_to_run, ammeter, sampling_frequency_hz):
    sampling_kwargs = {"total_duration_seconds": time_to_run,
                       "sampling_frequency_hz": sampling_frequency_hz}
    res = _test_single_ammeter_stability(file_name="ammeter_result",
                                         result_manager=result_manager,
                                         make_sampler=make_sampler,
                                         ammeter=ammeter,
                                         sampling_kwargs=sampling_kwargs)
    result_manager.plot_results
    # Plot
    title = ammeter.name.capitalize()
    value_label = "Current[A]"
    result_manager.plot_results(res, title=title, kind="scatter", value_label=value_label)
    result_manager.plot_results(res, title=title, kind="line", value_label=value_label)
    result_manager.plot_results(res, title=title, kind="hist", value_label=value_label)
    assert res.std() <= STD_CUTOFF, "Standard deviation is to large for stable result"


@pytest.mark.stability
@pytest.mark.parametrize("measurements_count", [100])
@pytest.mark.parametrize("sampling_frequency_hz", [1, 20])
@pytest.mark.parametrize("ammeter", [CircutorAmmeter, EntesAmmeter, GreenleeAmmeter], indirect=True)
def test_ammeter_stability_by_measurements_count(result_manager, make_sampler, measurements_count, ammeter, sampling_frequency_hz):
    sampling_kwargs = {"measurements_count": measurements_count,
                       "sampling_frequency_hz": sampling_frequency_hz}
    res = _test_single_ammeter_stability(file_name="ammeter_result",
                                         result_manager=result_manager,
                                         make_sampler=make_sampler,
                                         ammeter=ammeter,
                                         sampling_kwargs=sampling_kwargs)
    result_manager.plot_results
    # Plot
    title = ammeter.name.capitalize()
    value_label = "Current[A]"
    result_manager.plot_results(res, title=title, kind="scatter", value_label=value_label)
    result_manager.plot_results(res, title=title, kind="line", value_label=value_label)
    result_manager.plot_results(res, title=title, kind="hist", value_label=value_label)


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
    
    # Order results
    summaries = {}
    for ammeter_name, res in results.items():
        res.sample_name = ammeter_name
        result_manager.save_result(f"{ammeter_name}Result", res)
        res.get_summary()  # logs the human readable summary
        summaries[ammeter_name] = res.get_summary_dict()
    result_manager.save_json("summary", summaries)
    
    # Plot
    title = " vs ".join([a.name.capitalize() for a in ammeters])
    value_label = "Current[A]"
    result_manager.plot_results(*results.values(), title=title, kind="scatter", value_label=value_label)
    result_manager.plot_results(*results.values(), title=title, kind="line", value_label=value_label)
    result_manager.plot_results(*results.values(), title=title, kind="hist", value_label=value_label)
    #TODO 5 -Accuracy Assessment. Identify most reliable measurement method


def _test_single_ammeter_stability(file_name: str, result_manager: ResultManager,
                                   make_sampler: Callable[..., Sampler],
                                   ammeter: AmmeterEmulatorBase,
                                   sampling_kwargs: Optional[Dict[str, float]] = None) -> NumericSamplerResult:
    sampling_kwargs = sampling_kwargs if sampling_kwargs else {}
    sampler = make_sampler(**sampling_kwargs)
    logging.info(sampler)
    res: NumericSamplerResult = sampler.sample(ammeter.measure_current, result_class=NumericSamplerResult)
    logging.info(res)
    res.get_summary()  # logs the human readable summary
    result_manager.save_result(file_name, res, save_summary=True)
    return res
    
