import logging
import threading
import time


from src.utils.config import load_config
from Ammeters.base_ammeter import AmmeterEmulatorBase
from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.client import request_current_from_ammeter


def run_emulator(emulator: AmmeterEmulatorBase):
    emulator.start_server()
    

if __name__ == "__main__":
    logging.basicConfig()
    # Start each ammeter in a separate thread
    config = load_config("./config/config.yaml")
    greenlee = GreenleeAmmeter(config["ammeters"]["greenlee"]["port"])
    entes = EntesAmmeter(config["ammeters"]["entes"]["port"])
    circutor = CircutorAmmeter(config["ammeters"]["circutor"]["port"])
    ammeters = [greenlee, entes, circutor]
    for ammeter in ammeters:
        threading.Thread(target=run_emulator, args=[ammeter], daemon=True).start()

    time.sleep(5)
    
    request_current_from_ammeter(greenlee, greenlee.get_current_command)  # Request from Greenlee Ammeter
    request_current_from_ammeter(entes, entes.get_current_command)  # Request from ENTES Ammeter
    request_current_from_ammeter(circutor, circutor.get_current_command)  # Request from CIRCUTOR Ammeter

    pass
