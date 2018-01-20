About
=======

Evaluation reversi AIs which implement [NBoard Protocol](https://github.com/weltyc/ntest/blob/master/instructions/Protocol.htm).

Requirements
-----------

* Python >= 3.6

Setup
=======

Install Libraries
-------------
```bash
pip install -r requirements.txt
```

Write engine.yml
-------------

Write `engine.yml` which defines how to execute external NBoard Engines.

```yaml
<engine name>:
  working_dir: <path to working dir>
  command: <execute command>
  env:  # environment variables. Optional.
    KEY1: VALUE1
    KEY2: VALUE2
```

Usage
=======

```bash
python src/reversi_arena/run.py -n <number of battles> play <engine1 name>:<depth> <engine2 name>:<depth>
```

### ex)

```bash
python src/reversi_arena/run.py -n 10 play raz:1 ntest:1
```

All game moves are written in `data/ggf/*.ggf`.
They can be loaded by [NBoard](http://www.orbanova.com/nboard/).

