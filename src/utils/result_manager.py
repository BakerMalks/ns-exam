import time
import pathlib
import csv
import concurrent.futures
import logging

import numpy as np

from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple, Type, TypeVar, Union
from dataclasses import dataclass, field

from src.utils.logger import TIME_FORMAT

T = TypeVar("T")
MAX_SAMPLEING_FREQUENCY = 0.001


@dataclass
class SamplerResult:
    samples: Dict[float, Any] = field(default_factory=dict)
    initiate_sample_timer: bool = True
    sample_name: str = ""
    _init_time: float = 0.0
    
    def __post_init__(self):
        if self.initiate_sample_timer:
            self.start_timer()
    
    def start_timer(self):
        if self._init_time > 0:
            # Choose if a raise error should be used (probbly a good idea as this is for developing help)
            logging.error("Result sampler timer was already initiated")
        else:
            self._init_time = time.perf_counter()
    
    def add_sample(self, value):
        self.samples[time.perf_counter() - self._init_time] = value
    
    def get_summery(self, print_log: bool = True, add_sample_type: bool = True, split_literal: str = "", *args, **kwargs) -> str:
        """Returns a string thet sums up the results of the sample

        Args:
            print_log (bool, optional): Log the summery. Defaults to True.
            add_sample_type (bool, optional): Should log the type value of the sample (int / str / ...). Defaults to True.
            split_literal (str, optional): the split between the summery lines. Defaults "" will mean '\n - '.

        Returns:
            str: _description_
        """
        summery_list = [self._get_summery_header()]
        summery_list.extend(self._get_summery_body(add_sample_type))
        split_literal = split_literal if split_literal else '\n - '
        summery = split_literal.join(summery_list)
        if print_log:
            logging.info(summery)
        return summery
        
    def _get_summery_body(self, add_sample_type: bool = True) -> List[str]:
        body = []
        body.append(f"Sample count: {self.sample_count}")
        if add_sample_type:
            sample_types = set(str(type(value)) for value in self.samples.values())
            body.append(f"""Sample types: {", ".join(sample_types)}""")
        return body
            
    def _get_summery_header(self) -> str:
            return f"""Sample {self.sample_name + " " if self.sample_name else ""}Results:"""
    
    @property
    def sample_count(self) -> int:
        return len(self.samples)
    
    def get_csv(self, sample_colume_name: str = "Sample", use_sample_index: bool = False, *args, **kwargs):
        data = []
        index_colume_name = "Index" if use_sample_index else "Time"
        i = 0
        for key, value in self.samples.items():
            data.append({index_colume_name: i if use_sample_index else key, sample_colume_name: value})
            i += 1
        return data


@dataclass
class NumericSamplerResult(SamplerResult):
    samples: Dict[float, float] = field(default_factory=dict)
    
    def max(self) -> float:
        return max(self.samples.values())

    def min(self) -> float:
        return min(self.samples.values())

    def mean(self) -> float:
        return sum(self.samples.values()) / self.sample_count

    def median(self) -> float:
        return list(self.samples.values())[self.sample_count // 2]

    def std(self, ddof: float = 0) -> float:
        """Standard deviation 

        Args:
            ddof (float, optional): Means Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents the number of elements. Defaults to 0.

        Returns:
            float: standard deviation
        """
        return np.std(list(self.samples.values()), ddof=ddof)
   
    def _get_summery_body(self, add_sample_type: bool = True) -> List[str]:
        body = super()._get_summery_body(add_sample_type)
        body.append(f"Max: {self.max()}")
        body.append(f"Min: {self.min()}")
        body.append(f"Mean: {self.mean()}")
        body.append(f"Median: {self.median()}")
        body.append(f"STD (ddof=0): {self.max()}")
        return body
        

@dataclass
class Sampler:
    measurements_count: int = -1  # -1 is dont sample
    total_duration_seconds: float = -1.0  # -1 is dont sample. measurements_count take priority if both set
    sampling_frequency_hz: float = MAX_SAMPLEING_FREQUENCY

    def __post_init__(self):
        # frequency must be positive
        if self.sampling_frequency_hz < 0: 
            self.sampling_frequency_hz = MAX_SAMPLEING_FREQUENCY
    
    def sample(self, sample_function: Callable[..., T], *args, result_class: type[SamplerResult] = SamplerResult, **kwargs) -> SamplerResult:
        samples = result_class()
        target_period = 1.0 / self.sampling_frequency_hz
        if self.measurements_count > 0:
            start_time = time.perf_counter()
            for _ in range(self.measurements_count):
                time_before_sample = time.perf_counter()
                samples.add_sample(sample_function(*args, **kwargs))
                # To ensure precise measurment intervals we sleep remaining time after sample function ends
                elapsed = time.perf_counter() - time_before_sample
                sleep_time = target_period - elapsed
                time.sleep(max(sleep_time, 0.0))  # if sleep time gets negative

        elif self.total_duration_seconds > 0:
            start_time = time.perf_counter()
            # `:=` operator was added in python 3.8
            while (time_before_sample := time.perf_counter()) < self.total_duration_seconds + start_time:
                samples.add_sample(sample_function(*args, **kwargs))
                # To ensure precise measurment intervals we sleep remaining time after sample function ends
                elapsed = time.perf_counter() - time_before_sample
                sleep_time = target_period - elapsed
                time.sleep(max(sleep_time, 0.0))  # if sleep time gets negative

        return samples
    
    def sample_many(
        self,
        targets: Dict[str, Tuple[Callable[..., Any], Tuple[Any, ...], Dict[str, Any]]],
        result_class: Type[SamplerResult] = SamplerResult
    ) -> Dict[str, SamplerResult]:
        """
        Samples multiple functions concurrently using a thread pool.
        
        `targets` format: 
        {
           "sensor_1": (read_func, (arg1,), {"kwarg1": val}),
           "sensor_2": (read_func_2, (), {})
        }
        """
        results: Dict[str, SamplerResult] = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(targets)) as executor:
            future_to_name = {}
            for name, (func, args, kwargs) in targets.items():
                future = executor.submit(self.sample, func, *args, result_class=result_class, **kwargs)
                future_to_name[future] = name
            for future in concurrent.futures.as_completed(future_to_name):
                name = future_to_name[future]
                results[name] = future.result()
        
        return results


class ResultManager:
    def __init__(self, result_folder_path: Union[str, pathlib.Path] = "."):  # can also write str | pathlib.Path in ptrhon 3.10+
        now = datetime.now()  # can use utc to avoid multi timezone 
        formatted_time = now.strftime(TIME_FORMAT)
        self.folder_path: pathlib.Path = pathlib.Path(result_folder_path, formatted_time)
        if self.folder_path.exists():
            pass  # maybe add error here
        else:
            self.folder_path.mkdir()
        
    def save_result(self, file_name: str, result: SamplerResult, *args, save_summery=False, **kwargs):
        data = result.get_csv(*args, **kwargs)
        self.save_csv(file_name, data)
        if save_summery:
            self.save_text(file_name, result.get_summery(print_log=False, *args, **kwargs))
    
    def save_csv(self, file_name: str, data: List[Dict[float, Any]]):
        headers = data[0].keys()
        path = pathlib.Path(self.folder_path, file_name)
        path = path if path.suffix == ".csv" else path.with_suffix(".csv")
        with open(str(path), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()  # Writes the column names
            writer.writerows(data)  # Writes all rows at once
    
    def save_text(self, file_name: str, data: str):
        path = pathlib.Path(self.folder_path, file_name)
        path = path if path.suffix == ".txt" else path.with_suffix(".txt")
        with open(str(path), "w", newline="") as f:
            f.write(data)
