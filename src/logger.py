from json import loads,load
import logging
from logging.handlers import SMTPHandler
from flask import logging as flogging
from config.config import global_config

class Logger:
    def __init__(self) -> None:
        """Intialize Logger"""
        self.__config = global_config

        logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        
        waitress_logger=logging.getLogger('waitress')
        waitress_logger.setLevel(logging.INFO)

        self.logger = logging.Logger("APP")
        self.logger.removeHandler(flogging.default_handler)
        self.logger.addHandler(waitress_logger)
    
    def getLogger(self):
        """Returns Logger"""
        return self.logger