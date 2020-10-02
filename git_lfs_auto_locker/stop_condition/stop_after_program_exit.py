import psutil

from stop_condition.stop_condition import StopCondition


class StopAfterProgramExit(StopCondition):
    def __init__(self, program_name: str):
        self.program_name = program_name

    def should_stop(self) -> bool:
        return self.program_name not in (process.name() for process in psutil.process_iter())
