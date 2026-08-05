import logging

from socket import socket, AF_INET, SOCK_STREAM
from Ammeters.base_ammeter import AmmeterEmulatorBase


def request_current_from_ammeter(ammeter: AmmeterEmulatorBase, command: bytes):
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect(('localhost', ammeter.port))
        s.sendall(command)
        data = s.recv(1024)
        if data:
            logging.info(f"Received current measurement from port {ammeter.port}: {data.decode('utf-8')} A")
        else:
            logging.info("No data received.")

