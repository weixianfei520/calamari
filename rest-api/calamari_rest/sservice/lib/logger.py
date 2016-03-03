import logging


logger = logging.getLogger("calamari_iscsi")

LOG_TYPE_CONFIG = "Config"
LOG_TYPE_ERROR = "Error"
LOG_TYPE_GENERAL = "General"


def setLevel(lvl):
    logger.setLevel(lvl)


def log(lvl, log_type, msg, *args, **kwargs):
    log_type_str = "[%s] " % log_type
    logger.log(lvl, log_type_str + msg, *args, **kwargs)

