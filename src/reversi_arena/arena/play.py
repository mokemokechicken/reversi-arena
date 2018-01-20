import os
from logging import getLogger

import asyncio

from datetime import datetime

from reversi_arena.arena.nboard_engine_client import NBoardEngineClient, GoResponse
from reversi_arena.config import Config
from reversi_arena.env.reversi_env import ReversiEnv, Winner
from reversi_arena.lib.ggf import make_ggf_string

logger = getLogger(__name__)


def start(config: Config):
    return PlayManager(config).start()


class PlayManager:
    def __init__(self, config: Config):
        self.config = config
        self.clients = []  # type: list[NBoardEngineClient]
        self.stats = None  # type: dict[NBoardEngineClient, Stats]
        self.move_records = []  # type: list[GoResponse]
        self.ggf_path = None

    def start(self):
        logger.debug("start")
        self.clients.append(self.create_client(self.config.opts.engine1))
        self.clients.append(self.create_client(self.config.opts.engine2))
        self.stats = {
            self.clients[0]: Stats(),
            self.clients[1]: Stats(),
        }
        for c in self.clients:
            c.connect()

        self.play_loop()

    def play_loop(self):
        n_play = self.config.opts.n_play
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.ggf_path = os.path.join(self.config.resource.ggf_dir, f'{now}.ggf')

        event_loop = asyncio.get_event_loop()
        for play_idx in range(1, n_play+1):
            event_loop.run_until_complete(self.play(play_idx))

    async def play(self, play_idx):
        logger.info(f"start play index={play_idx}")
        if play_idx % 2 == 1:
            move_order = [self.clients[0], self.clients[1]]
        else:
            move_order = [self.clients[1], self.clients[0]]

        env = ReversiEnv().reset()
        self.init_game(move_order)
        for move_idx in range(120):
            if env.done:
                break
            turn_client = move_order[move_idx % 2]
            response = await turn_client.go()
            if response.action is not None:
                env.step(response.action)
            self.record_action(response)

            for c in move_order:
                c.announce_move(response)

        self.finish_game(env, move_order)

    def init_game(self, move_order):
        logger.debug("init game")
        ggf = make_ggf_string(black_name=move_order[0].my_name, white_name=move_order[1].my_name)
        for c in move_order:
            c.set_game(ggf)
        self.move_records = []

    def finish_game(self, env, move_order):
        """

        :param ReversiEnv env:
        :param list[NBoardEngineClient] move_order:
        :return:
        """
        logger.info(f"{env.winner}: {env.board.number_of_black_and_white}")
        black_results = self.stats[move_order[0]].black
        white_results = self.stats[move_order[1]].white

        if env.winner == Winner.black:
            black_results.win += 1
            white_results.lose += 1
        elif env.winner == Winner.white:
            black_results.lose += 1
            white_results.win += 1
        else:
            black_results.draw += 1
            white_results.draw += 1

        r = []
        for c in self.clients:
            r.append(f"{c.my_name}:{self.stats[c]}")
        logger.info(" | ".join(r))

        bc, wc = env.board.number_of_black_and_white
        ggf = make_ggf_string(move_order[0].my_name, move_order[1].my_name,
                              moves=[x.move_str for x in self.move_records],
                              result=f"{bc-wc:+d}")
        with open(self.ggf_path, "at") as f:
            f.write(ggf + "\n")
            f.flush()

    def record_action(self, go_response: GoResponse):
        self.move_records.append(go_response)

    def create_client(self, engine_str):
        e = engine_str.split(":")
        name = e[0]
        if len(e) == 1:
            depth = 1
        else:
            depth = int(e[1])
        return NBoardEngineClient(self.config, name, depth)


class Results:
    win = lose = draw = 0


class Stats:
    def __init__(self):
        self.black = Results()
        self.white = Results()

    def __str__(self):
        b = self.black
        w = self.white
        return f"Black[{b.win}/{b.lose}/{b.draw}]White[{w.win}/{w.lose}/{w.draw}]"
