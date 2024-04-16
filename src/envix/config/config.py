import os
from logging import getLogger
from pathlib import Path
from typing import Self

from pydantic import RootModel

from envix.exception import EnvixConfigFileExtensionError, EnvixConfigFileNotFound

from .v1.config import ConfigV1

logger = getLogger(__name__)


class Config(RootModel):
    root: ConfigV1

    @classmethod
    def load(cls, filepath: Path | None) -> Self:
        import tomllib

        if not (filepath := filepath or _find_config_file()):
            raise EnvixConfigFileNotFound(Path(os.getcwd()))

        if not filepath.exists():
            raise EnvixConfigFileNotFound(filepath)

        match filepath.suffix:
            case ".toml":
                with open(filepath, "rb") as f:
                    return cls.model_validate(tomllib.load(f))

            case ".yaml" | ".yml":
                import yaml

                with open(filepath, "rb") as f:
                    return cls.model_validate(yaml.safe_load(f))

            case ".json":
                import json

                with open(filepath, "rb") as f:
                    return cls.model_validate(json.load(f))

            case _:
                raise EnvixConfigFileExtensionError(filepath)


def _find_config_file() -> Path | None:
    import os
    from pathlib import Path

    cwd = Path(os.getcwd())

    for directory in (cwd, *cwd.parents):
        for filename in ("envix.toml", "envix.yaml", "envix.yml", "envix.json"):
            config_filepath = directory / filename
            if config_filepath.exists():
                logger.debug(f"Found config file: {config_filepath}")
                return config_filepath
