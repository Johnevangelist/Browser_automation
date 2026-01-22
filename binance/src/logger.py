class Logger:
    def __init__(self, prefix=""):
        self.prefix = f"[{prefix}] " if prefix else ""
    
    def _print(self, msg, color=""):
        print(f"{color}{self.prefix}{msg}\033[0m")
    
    def info(self, msg):
        self._print(msg, "\033[94m")
    
    def success(self, msg):
        self._print(msg, "\033[92m")
    
    def warn(self, msg):
        self._print(msg, "\033[93m")
    
    def error(self, msg):
        self._print(msg, "\033[91m")
    
    def dim(self, msg):
        self._print(msg, "\033[90m")
    
    def header(self, msg):
        self._print(msg, "\033[1m\033[96m")