import logging
import sys
from argparse import ArgumentParser, BooleanOptionalAction
from typing import NoReturn

from rich.console import Console as RichConsole
from rich.logging import RichHandler
from rich_argparse import ArgumentDefaultsRichHelpFormatter

import envix

from .commands import config, export, inject

logger = logging.getLogger(__name__)


class EnvixArgumentParser(ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        raise RuntimeError(message)


class App:
    @classmethod
    def run(cls, args: list[str] | None = None):
        verbose = "--verbose" in (args or sys.argv)

        try:
            logging.basicConfig(
                format="%(message)s",
                level=logging.INFO,
                handlers=[
                    RichHandler(
                        level=logging.DEBUG,
                        console=RichConsole(stderr=True),
                        show_time=False,
                        show_path=False,
                        rich_tracebacks=True,
                        markup=True,
                    )
                ],
            )
            logging.root.setLevel(logging.DEBUG if verbose else logging.INFO)

            formatter_class = ArgumentDefaultsRichHelpFormatter
            formatter_class.styles["argparse.default"] = "dark_orange"

            parser = EnvixArgumentParser(
                prog="envix",
                description="A tool to retrieve environment variables from the Secret Manager and execute commands.",
                formatter_class=formatter_class,
            )

            parser.add_argument(
                "--version",
                action="version",
                version=f"[argparse.prog]%(prog)s[/] {envix.__version__}",
            )

            parser.add_argument(
                "--verbose",
                action=BooleanOptionalAction,
                help="output verbose log.",
            )

            subparser = parser.add_subparsers(
                title="commands",
                metavar="COMMAND",
            )

            inject.add_subparser(subparser, formatter_class=parser.formatter_class)
            export.add_subparser(subparser, formatter_class=parser.formatter_class)
            config.add_subparser(subparser, formatter_class=parser.formatter_class)

            parser.set_defaults(handler=lambda _: parser.print_help())

            space = parser.parse_args(args)

            if hasattr(space, "handler"):
                space.handler(space)

            else:
                parser.print_help()

        except KeyboardInterrupt:
            print()
            logger.info("Cancelled by user 👋")

            sys.exit(1)

        except Exception as e:
            if verbose:
                logger.exception(e)

            else:
                logger.error(e)

            raise e
