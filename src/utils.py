import logging


def set_up_logger(logger_name, level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(level)
    # Levels: debug, info, warning, error, critical
    formatter = logging.Formatter(
        '%(levelname)8s -- %(name)-15s line %(lineno)-4s: %(message)s')
    logger.handlers[0].setFormatter(formatter)
    return logger
