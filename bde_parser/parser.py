from abc import ABC, abstractmethod

class Parser(ABC):

    @abstractmethod
    def get(self)->None:
        pass

    @abstractmethod
    def find(self)->None:
        pass
    
    @abstractmethod
    def find_all(self)->None:
        pass

    @abstractmethod
    def waitfor(self)->None:
        pass

    @abstractmethod
    def __del__(self)->None:
        pass