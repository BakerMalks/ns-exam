import random
import socket
import time

from threading import Thread
from typing import Dict

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
            if time.perf_counter() - start > timeout:
                raise RuntimeError(
                    f"Timed out starting '{ammeter_type}'"
                )
            time.sleep(0.05)

        self._running_ammeters.append(ammeter_type)
        return ammeter_type(port)


def is_port_open(host: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0
