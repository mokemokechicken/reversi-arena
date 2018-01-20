import argparse

from logging import getLogger

from .lib.logger import setup_logger
from .config import Config

logger = getLogger(__name__)

CMD_LIST = ['play']


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", help="what to do", choices=CMD_LIST)
    parser.add_argument("engine1", help="specify engine1 <engine1_name>:<depth>. ex) raz:5")
    parser.add_argument("engine2", help="specify engine2 <engine2_name>:<depth>. ex) ntest:5")
    parser.add_argument("-n", dest="n_play", help="how many times the engines play", default=1, type=int)
    parser.add_argument("-c", dest="config", help="path to engine file")
    parser.add_argument("-v", dest="verbose", help="output debug log", action="store_true")
    return parser


def setup(config: Config, args):
    config.resource.create_directories()
    config.opts.engine1 = args.engine1
    config.opts.engine2 = args.engine2
    config.opts.n_play = args.n_play

    if args.config:
        config.resource.engine_def_path = args.config
    setup_logger(config.resource.main_log_path, verbose=args.verbose)


def start():
    parser = create_parser()
    args = parser.parse_args()

    config = Config()
    setup(config, args)
    cmd = args.cmd

    if cmd == "play":
        from .arena import play
        return play.start(config)
