from logging import StreamHandler, basicConfig, DEBUG, INFO, getLogger, Formatter


def setup_logger(log_filename, verbose=False):
    format_str = '%(asctime)s@%(name)s %(levelname)s # %(message)s'
    level = DEBUG if verbose else INFO
    basicConfig(filename=log_filename, level=level, format=format_str)
    stream_handler = StreamHandler()
    stream_handler.setFormatter(Formatter(format_str))
    getLogger().addHandler(stream_handler)
