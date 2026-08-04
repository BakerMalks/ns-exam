import threading
import time

from Ammeters.base_ammeter import AmmeterEmulatorBase
from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.client import request_current_from_ammeter


def run_emulator(emulator: AmmeterEmulatorBase):
    emulator.start_server()
    

if __name__ == "__main__":
    # Start each ammeter in a separate thread
    greenlee = GreenleeAmmeter(5001)
    entes = EntesAmmeter(5002)
    circutor = CircutorAmmeter(5003)
    ammeters = [greenlee, entes, circutor]
    for ammeter in ammeters:
        threading.Thread(target=run_emulator, args=[ammeter], daemon=True).start()

    # This section is commented out because it shouldn't work.
    # Read the README.md file as well as the source code if you need, and fix the problem.

    # Wait for the servers to start, if you have problem restarting the servers between runs try increasing sleep time.
    time.sleep(5)
    request_current_from_ammeter(greenlee, greenlee.get_current_command)  # Request from Greenlee Ammeter
    request_current_from_ammeter(entes, entes.get_current_command)  # Request from ENTES Ammeter
    request_current_from_ammeter(circutor, circutor.get_current_command)  # Request from CIRCUTOR Ammeter

    pass
