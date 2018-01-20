import os


def _project_dir():
    d = os.path.dirname
    return d(d(d(os.path.abspath(__file__))))


def _data_dir():
    return os.path.join(_project_dir(), "data")


class Config:
    def __init__(self):
        self.resource = ResourceConfig()
        self.opts = Options()


class Options:
    def __init__(self):
        self.n_play = 1
        self.engine1 = None
        self.engine2 = None


class ResourceConfig:
    def __init__(self):
        self.project_dir = os.environ.get("PROJECT_DIR", _project_dir())
        self.data_dir = os.environ.get("DATA_DIR", _data_dir())
        self.log_dir = os.path.join(self.project_dir, "logs")
        self.main_log_path = os.path.join(self.log_dir, "main.log")
        self.engine_def_path = os.path.join(self.project_dir, "engine.yml")
        self.ggf_dir = os.path.join(self.data_dir, "ggf")

    def create_directories(self):
        dirs = [self.project_dir, self.data_dir, self.log_dir, self.ggf_dir]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
