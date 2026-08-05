import time

import numpy as np

from logger import logging
from typing import Any, Dict
from dataclasses import dataclass, field

@dataclass
class SamplingResult:
    samples: Dict[float, Any] = field(default_factory=dict)
    initiate_sample_timer: bool = True
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
    
    def print_measurments(self):
        print(str(self.samples))
    
    @property
    def sample_count(self) -> int:
        return len(self.samples)


@dataclass
class NumericSamplingResult(SamplingResult):
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
       return np.std(list(self.samples.values()), ddof=ddof)


@dataclass
class Sampling:
    measurment_count: int = -1  # -1 is dont sample
    test_duration: float = -1.0  # -1 is dont sample. measurment_count take priority if both set
    sample_frequency: float = 1000.0  # time in ms between pampeling if multiple samples are needed. 

    def __post_init__(self):
        # frequency must be positive
        if self.sample_frequency < 1: 
            self.sample_frequency = 1000.0
    
    def sample(self, sample_function, *args, result_class: type[SamplingResult] = SamplingResult, **kwargs):
        samples = result_class()
        if self.measurment_count >= 0:
            start_time = time.perf_counter()
            for _ in range(self.measurment_count):
                time_before_sample = time.perf_counter()
                samples.add_sample(sample_function(*args, **kwargs))
                # To ensure precise measurment intervals we sleep remaining time after sample function ends
                sleep_time = self.sample_frequency - (time.perf_counter() - time_before_sample)
                time.sleep(max(sleep_time,0))  # if sleep time gets negative

        elif self.test_duration >= 0:
            start_time = time.perf_counter()
            # `:=` operator was added in python 3.8
            while (time_before_sample := time.perf_counter()) < self.test_duration + start_time:
                samples.add_sample(sample_function(*args, **kwargs))
                # To ensure precise measurment intervals we sleep remaining time after sample function ends
                sleep_time = self.sample_frequency - (time.perf_counter() - time_before_sample)
                time.sleep(sleep_time)  # if sleep time gets negative

        return samples