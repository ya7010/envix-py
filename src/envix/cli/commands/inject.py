import os
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import Annotated, Any, cast

from pydantic import BaseModel

from envix.cli.field import ConfigFileValidator


class Args(BaseModel):
    command: str
    args: list[str]
    config_file: Annotated[Path | None, ConfigFileValidator]
    config_name: list[str] | None
    clear_environments: bool
    dotenv: list[Path] | None


def add_subparser(subparsers: "_SubParsersAction[Any]", **kwargs: Any) -> None:
    help = "Inject environment variables and execute the command."

    parser = cast(
        ArgumentParser,
        subparsers.add_parser(
            "inject",
            description=help,
            help=help,
            **kwargs,
        ),
    )

    parser.add_argument(
        "command",
        metavar="COMMAND",
    )

    parser.add_argument("args", metavar="ARGS", nargs="*")

    parser.add_argument(
        "--config-file",
        "--file",
        metavar="CONFIG_FILE",
        help="config file path.",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--config-name",
        "--config",
        metavar="CONFIG_NAME",
        help="user registered setting name.",
        type=str,
        nargs="*",
    )

    parser.add_argument(
        "--clear-environments",
        action="store_true",
        help="Running commands with no environment variables set.",
        default=False,
    )

    parser.add_argument(
        "--dotenv",
        metavar="DOTENV",
        help="Path to the .env file.",
        type=Path,
        default=None,
        nargs="*",
    )

    parser.set_defaults(handler=lambda space: inject_command(Args(**vars(space))))


def inject_command(args: Args) -> None:
    import asyncio
    import subprocess

    from dotenv import load_dotenv

    from envix.config.config import collect_config_filepaths
    from envix.exception import EnvixLoadEnvsError
    from envix.loader import load_secrets

    if args.clear_environments:
        os.environ.clear()

    _, errors = asyncio.run(
        load_secrets(collect_config_filepaths(args.config_file, args.config_name))
    )

    if args.dotenv == []:
        args.dotenv = [Path(".env")]

    for dotenv in args.dotenv or []:
        load_dotenv(dotenv, override=True)

    if errors:
        raise EnvixLoadEnvsError(errors)

    subprocess.call([args.command] + args.args, env={**os.environ})
