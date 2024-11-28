from argparse import ArgumentParser, Namespace

from core import __version__, DefaultConfig
from core.launcher import Launcher


def start(options: Namespace):
    """运行程序"""
    return Launcher(config=options.config).start()


def get_options() -> Namespace:
    """获取命令参数"""
    parser = ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the program")
    run_parser.set_defaults(handle=start)
    # run_parser.add_argument("-p", "--port", dest="port", type=str, default=6778, help="IP port")
    # run_parser.add_argument("-a", "--address", dest="address", default="0.0.0.0", help="IP address")
    run_parser.add_argument("-c", "--config", dest="config", default=DefaultConfig, help="configuration file path")

    options = parser.parse_args()
    return options if options.command else run_parser.parse_args()


def main():
    options = get_options()
    return options.handle(options)
