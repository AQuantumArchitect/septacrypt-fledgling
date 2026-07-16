"""CLI: python -m septacrypt_fledgling.cli serve --port 7777 [--debug]"""
from __future__ import annotations

import argparse

from .server.app import serve


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="septacrypt-fledgling")
    sub = parser.add_subparsers(dest="command", required=True)
    p_serve = sub.add_parser("serve", help="run the JSON-over-HTTP game server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=7777)
    p_serve.add_argument("--debug", action="store_true", help="validate every render payload")
    args = parser.parse_args(argv)

    if args.command == "serve":
        serve(args.host, args.port, debug=args.debug)


if __name__ == "__main__":
    main()
