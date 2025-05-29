import sys
import logging

class Logger:
    _logger = None

    @staticmethod
    def init_logging(log_path):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        Logger._logger = logging.getLogger()
        sys.stdout = Logger._StreamToLogger(Logger._logger, logging.INFO)
        sys.stderr = Logger._StreamToLogger(Logger._logger, logging.ERROR)
    
    @staticmethod
    def info(message):
        if Logger._logger:
            Logger._logger.info(message)
        else:
            print(message)
    
    @staticmethod
    def error(message):
        if Logger._logger:
            Logger._logger.error(message)
        else:
            print(f"ERROR: {message}", file=sys.stderr)
    
    @staticmethod
    def debug(message):
        if Logger._logger:
            Logger._logger.debug(message)
    
    @staticmethod
    def warning(message):
        if Logger._logger:
            Logger._logger.warning(message)
        else:
            print(f"WARNING: {message}")

    class _StreamToLogger:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level

        def write(self, message):
            if message.strip():
                self.logger.log(self.level, message.strip())

        def flush(self):
            pass
