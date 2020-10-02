from abc import ABC, abstractmethod


class StopCondition(ABC):
    @abstractmethod
    def should_stop(self) -> bool:
        pass
