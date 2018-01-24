import asyncio
import os
import re
from collections import namedtuple
from subprocess import Popen, PIPE

from logging import getLogger

from reversi_arena.config import Config
import yaml

from reversi_arena.lib.ggf import convert_move_to_action
from reversi_arena.lib.nonblocking_stream_reader import NonBlockingStreamReader

logger = getLogger(__name__)

GoResponse = namedtuple("GoResponse", "action move_str")


class NBoardEngineClient:
    def __init__(self, config: Config, engine_name, depth):
        self.config = config
        self.engine_name = engine_name
        self.depth = depth
        self.my_name = f"{engine_name}:{depth}"
        self.status = ""
        self._engines = {}
        self._process = None  # type: Popen
        self._stdout_reader = None  # type: NonBlockingStreamReader
        self._stderr_reader = None  # type: NonBlockingStreamReader
        self._communication_logger = getLogger(self.my_name)
        self._ping_idx = 0
        self._handlers = [
            (re.compile(r'set myname(.*)'), self._set_myname),
            (re.compile(r'status(.*)'), self._set_status),
            ]

    def _check_definition(self):
        if not self._engines:
            with open(self.config.resource.engine_def_path, "rt") as f:
                self._engines = yaml.load(f)
        return self.engine_name in self._engines

    def connect(self):
        if not self._check_definition():
            raise RuntimeError(f"engine {self.engine_name} is not defined")

        self._process = self._create_process()
        self._stdout_reader = NonBlockingStreamReader(self._process.stdout).start()
        self._stderr_reader = NonBlockingStreamReader(self._process.stderr).start()
        self._send("nboard 2")

    def set_game(self, ggf: str):
        self._send(f"set game {ggf}")
        self._send(f"set depth {self.depth}")

    async def go(self) -> GoResponse:
        await self.ping()
        self._send("go")
        move = await self._wait_for_message(re.compile(r"=== .+"))
        move = move[4:]
        items = move.split('/')
        action = convert_move_to_action(items[0])
        return GoResponse(action=action, move_str=move)

    async def ping(self):
        self._ping_idx += 1
        self._send(f"ping {self._ping_idx}")
        await self._wait_for_message(re.compile(f'^pong {self._ping_idx}$'))

    async def _wait_for_message(self, wait_for=None, timeout=0.001):
        while True:
            self._check_stderr()
            message = self._stdout_reader.readline(timeout)
            if message is None:
                if not wait_for:
                    return
                await asyncio.sleep(0.1)
                continue
            if isinstance(message, bytes):
                message = message.decode("utf8")
            message = message.strip()
            self._recv(message)
            if message and wait_for and wait_for.search(message):
                return message

    def _check_stderr(self):
        while True:
            line = self._stderr_reader.readline()
            if line is None:
                break
            if isinstance(line, bytes):
                line = line.decode("utf8")
            line = line.rstrip()
            if not self._stderr_reader.closed:
                self._communication_logger.debug(line)
            else:
                self._communication_logger.warning(line)

    def announce_move(self, response: GoResponse):
        self._send(f"move {response.move_str}")

    def _send(self, message):
        self._communication_logger.debug("send > " + message)
        self._process.stdin.write(f"{message}\n".encode("utf8"))
        self._process.stdin.flush()

    def _recv(self, message):
        self._communication_logger.debug(f"recv < {message}")
        self._handle_message(message)

    def _create_process(self):
        engine_def = self._engines[self.engine_name]
        command = engine_def["command"]
        env = engine_def.get("env")

        # prepend ./ for relative path
        if isinstance(command, str):
            if not os.path.isabs(command):
                command = "./" + command
        elif isinstance(command, list):
            if not os.path.isabs(command[0]):
                command[0] = "./" + command[0]
        else:
            raise ValueError(f"command must be str or list but {type(command)}")

        return Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=engine_def["working_dir"], env=env)

    def _handle_message(self, message):
        for regexp, func in self._handlers:
            if self._scan(message, regexp, func):
                return

    def _scan(self, message, regexp, func):
        match = regexp.match(message)
        if match:
            func(*match.groups())
            return True
        return False

    def _set_myname(self, name):
        self.my_name = name.strip()
        logger.debug(f"myname={self.my_name}")

    def _set_status(self, status):
        self.status = status.strip()
        logger.debug(f"status={self.status}")
