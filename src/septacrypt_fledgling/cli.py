"""CLI: python -m septacrypt_fledgling.cli serve --port 7777 [--debug]"""
from __future__ import annotations

import argparse
import sys

from .server.app import serve


def main(argv=None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "play":
        from .play import main as play_main

        play_main(argv[1:])
        return

    parser = argparse.ArgumentParser(prog="septacrypt-fledgling")
    sub = parser.add_subparsers(dest="command", required=True)
    p_serve = sub.add_parser("serve", help="run the JSON-over-HTTP game server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=7777)
    p_serve.add_argument("--debug", action="store_true", help="validate every render payload")
    sub.add_parser("play", help="play STAR POD from the terminal (see: play --help)")
    args = parser.parse_args(argv)

    if args.command == "serve":
        serve(args.host, args.port, debug=args.debug)


if __name__ == "__main__":
    main()
