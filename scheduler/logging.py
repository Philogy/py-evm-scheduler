import logging
import sys

# Setting up the base logger
log: logging.Logger = logging.getLogger()
log.setLevel(logging.DEBUG)  # Log everything to the file

# File handler which logs even debug messages
fh = logging.FileHandler('log.txt', mode='w')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s: %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

# Console handler
ch = logging.StreamHandler()
ch_formatter = logging.Formatter('%(levelname)s: %(message)s')
ch.setFormatter(ch_formatter)

# Logic to set log level based on sys.argv
if '--log-level' in sys.argv:
    log_level_index = sys.argv.index('--log-level') + 1
    if log_level_index < len(sys.argv):
        log_level_str = sys.argv[log_level_index].upper()
        if log_level_str in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            ch.setLevel(getattr(logging, log_level_str))
        else:
            log.error(f"Invalid log level: {log_level_str}")
    else:
        log.error("No log level specified after '--log-level'")
else:
    # default to warning if no log level is specified
    ch.setLevel(logging.WARNING)

log.addHandler(ch)
