import os
from typing import get_type_hints, Union
from dotenv import load_dotenv

load_dotenv()

# Source from: https://www.doppler.com/blog/environment-variables-in-python

class AppConfigError(Exception):
    pass

def _parse_bool(val):
    return val if type(val) == bool else val.lower() in ['true', 't', '1', 'y']

class AppConfig:
    # Global Configs
    AI_LIST: str
    PYGAME_HIDE_SUPPORT_PROMPT: int = 1

    # CLI Configs
    VERBOSITY: bool = True
    DRAW: bool = False
    DRAW_RESULTS: bool = False
    STEP_BY_STEP: bool = False

    # PyGame Configs
    CELL_SIZE: int = 20
    FPS: int = 60

    # Experiment Configs
    RECORD: bool = True
    GAMES: int = 100

    def __init__(self, env):
        for field in get_type_hints(AppConfig):
            # Field will be skipped if not in all caps
            if not field.isupper():
                continue

            # Raise AppConfigError if required field not supplied
            default_value = getattr(self, field, None)
            if default_value is None and env.get(field) is None:
                raise AppConfigError('The {} field is required'.format(field))

            # Cast env var value to expected type and raise AppConfigError on failure
            try:
                var_type = get_type_hints(AppConfig)[field]
                if var_type == bool:
                    value = _parse_bool(env.get(field, default_value))
                else:
                    value = var_type(env.get(field, default_value))

                self.__setattr__(field, value)
            except ValueError:
                raise AppConfigError('Unable to cast value of "{}" to type "{}" for "{}" field'.format(
                    env[field],
                    var_type,
                    field
                )
            )


configuration = AppConfig(os.environ)