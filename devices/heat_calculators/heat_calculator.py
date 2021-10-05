from abc import ABC
from abc import abstractmethod
import struct
import datetime




class UnknownParametrName(Exception):
    def __init__(self, message):
        self.message = message

class HeatCalculator(ABC):

    @abstractmethod
    def getSettings(self, parameters):
        ...

    @abstractmethod
    def getCurrentTime(self):
        ...

    @abstractmethod
    def getCurrentValues(self, parameters):
        ...

    @abstractmethod
    def getHourArchives(self, parameters, from_dt, to_dt):
        ...

    @abstractmethod
    def getDayArchives(self, parameters, from_dt, to_dt):
        ...

    @abstractmethod
    def getMonthArchives(self, parameters, from_dt, to_dt):
        ...
