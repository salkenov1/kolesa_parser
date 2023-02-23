import toml

from pathlib import Path

__dir__ = str(Path(__file__).parent.absolute())
__config_path__ = f"{__dir__}/config.toml"

config = toml.load(__config_path__)