"""Mock Logger class for testing purposes. Currently only used to delete the log file."""

from pathlib import Path

from payload.data_handling.logger import Logger


class MockLogger(Logger):
    """
    This class has the same functionality as the Logger class, but simply removes the log file it
    generates after the logger has stopped. We use this class in the tests to avoid cluttering the
    filesystem with log files. Additionally, this helps mimic the behavior of the real logger, which
    can be computationally expensive.
    """

    __slots__ = ("delete_log_file", "_log_process")

    def __init__(self, log_file_path: Path, delete_log_file: bool = True):
        """
        Initializes the mock logger object. Behaves the same as the Logger class, but deletes the
        log file after stopping the logger.
        :param log_file_path: The path to the log file to.
        :param delete_log_file: True if the log file should be deleted after the logger stops.
        """
        super().__init__(log_file_path)
        self.delete_log_file = delete_log_file
        self._log_process.name = "Mock Logger Process"

    def stop(self):
        """
        Stops the logger and deletes the log file if the delete_log_file attribute is True.
        """
        super().stop()
        if self.delete_log_file:
            self.log_path.unlink()
