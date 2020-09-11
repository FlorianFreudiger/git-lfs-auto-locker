from abc import ABC, abstractmethod


class Notificator(ABC):
    @abstractmethod
    def show_info(self, message) -> None:
        pass

    @abstractmethod
    def show_warning(self, message) -> None:
        pass

    @abstractmethod
    def show_error(self, message) -> None:
        pass
