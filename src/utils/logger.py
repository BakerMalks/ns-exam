import logging
import os
from datetime import datetime

TIME_FORMAT = "%Y%m%d_%H%M%S"

class TestNameFilter(logging.Filter):
    """Overrides logger name with current pytest test name."""
    def __init__(self, test_name: str):
        super().__init__()
        self.test_name = test_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.name = self.test_name  # Changes %(name)s in format strings
        return True

class TestLogger:
    def __init__(self, test_name: str):
        self._test_name = test_name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        הגדרת הלוגר עם פורמט מותאם וכתיבה לקובץ
        """
        # יצירת תיקיית הלוגים
        log_dir = "results/logs"
        os.makedirs(log_dir, exist_ok=True)

        # הגדרת שם הקובץ עם תאריך ומזהה הבדיקה
        timestamp = datetime.now().strftime(TIME_FORMAT)
        log_file = f"{log_dir}/{timestamp}_{self._test_name}.log"

        # הגדרת הלוגר
        logger = logging.getLogger(f"test_{self._test_name}")


        return logger

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message) 
