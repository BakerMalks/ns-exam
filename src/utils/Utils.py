import random
import socket
import time
from logger import logging

from dataclasses import dataclass, field
from threading import Thread
from typing import Any, Dict

from Ammeters.base_ammeter import AmmeterEmulatorBase


def generate_random_float(min_value: float, max_value: float) -> float:
    """Generate a random float between min_value and max_value."""
    return random.uniform(min_value, max_value)


class AmmetterManager:
    def __init__(self, ammeter_configs: Dict[str, Dict]):
        self._ammeter_configs = ammeter_configs
        self._running_ammeters = []

    def get(self, ammeter_type: type[AmmeterEmulatorBase]):
        """Returns an ammeter instance. Starts server in a thread if not already running."""

        port = self._ammeter_configs[ammeter_type.name]["port"]
        # If already started in this session, return existing details
        if ammeter_type in self._running_ammeters:
            return ammeter_type(port)

        # Create new thread if it was not started yet
        t = Thread(target=ammeter_type(port).start_server, daemon=True)
        t.start()

        # Wait until port is actually listening
        timeout = 5.0
        start = time.perf_counter()
        while not is_port_open("localhost", port):
            if time.time() - start > timeout:
                raise RuntimeError(
                    f"Timed out starting '{ammeter_type}'"
                )
            time.sleep(0.05)

        self._running_ammeters.append(ammeter_type)
        return ammeter_type(port)


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

@dataclass
class NumericSamplingResult(SamplingResult):
    samples: Dict[float, float] = field(default_factory=dict)

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


def is_port_open(host: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0
