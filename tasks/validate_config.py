import sys
import textwrap
from pathlib import Path

from envix.config import Config

PACKAGE_DIR = Path(__file__).resolve().parents[1]

errors: list[tuple[Path, Exception]] = []
# 開発の案件に使われている設定ファイルを読み込む
for config_filepath in PACKAGE_DIR.glob("**/*config*.yml"):
    try:
        Config.load(config_filepath)

    except Exception as e:
        errors.append((config_filepath, e))

if errors:
    for config_filepath, e in errors:
        print(
            f'Error: "{config_filepath}"\n{(textwrap.indent(str(e), 4 * " "))}',
            file=sys.stderr,
        )

    sys.exit(1)
