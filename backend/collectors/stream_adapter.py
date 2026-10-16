from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional

class BaseLogCollector(ABC):
    """Abstract interface for server syslog ingestion adapters."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to log source (socket, file, or API)."""
        pass

    @abstractmethod
    def stream_logs(self) -> Iterator[str]:
        """Yield incoming log records as strings."""
        pass

    @abstractmethod
    def close(self):
        """Clean up connection handles."""
        pass

class FileTailCollector(BaseLogCollector):
    """Adapter for reading logs from a designated server log file."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._file_handle = None

    def connect(self) -> bool:
        try:
            self._file_handle = open(self.file_path, "r", encoding="utf-8", errors="replace")
            return True
        except Exception:
            return False

    def stream_logs(self) -> Iterator[str]:
        if not self._file_handle:
            return
        for line in self._file_handle:
            if line.strip():
                yield line.strip()

    def close(self):
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
