import logging
import json

from datetime import datetime

class StreamFormatter(logging.Formatter):
    
    color = {
        'DEBUG': '\x1b[38;21m',
        'INFO': '\x1b[38;5;39m',
        'WARNING': '\x1b[38;5;226m',
        'ERROR': '\x1b[38;5;196m',
        'reset': "\x1b[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        asctime = datetime.utcnow().strftime('%Y-%m-%Y %H:%M:%S')
        msg = record.getMessage()
        
        module_information = ''
        
        funcname = ''
        if record.funcName != '<module>':
            funcname = f"/{record.funcName}"
        
        lineno = record.lineno
        if hasattr(record, 'exc_info') and record.exc_info:  
            lineno = record.exc_info[2].tb_lineno
        
        module_information = f"[{lineno}.{record.filename}{funcname}]"
        
        if record.levelname == 'DEBUG':
            msg_icon = '[~]'
        elif record.levelname == 'INFO':
            msg_icon = '[>]'
        else:
            msg_icon = '[!]'

        return self.color[record.levelname] + f"{asctime} {module_information} {msg_icon} {msg}" + self.color['reset']

    def set_color(self, color:str):
        self._color = color

class JsonFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "file": record.filename,
            "function": record.funcName,
            "line": record.lineno, 
            "level": record.levelname,
            "msg": record.getMessage(),
            "created_time": datetime.utcnow().strftime('%d.%m.%Y[%H:%M:%S]'),
        }

        if hasattr(record, 'exc_info') and record.exc_info:  
            payload['stack_trace'] = self.formatException(record.exc_info)
        
        return json.dumps(payload)
        


def create_logger(log_file: str, log_dir: str = 'log'):  
    if not log_file.endswith('.json'):
        log_file += ".json"

    log_path = f"{log_dir}/{log_file}"

    logger = logging.getLogger(log_path)
    logger.setLevel(logging.DEBUG)
    
    stream_handler=logging.StreamHandler()
    stream_handler.setFormatter(StreamFormatter())
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger