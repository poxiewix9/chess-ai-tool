from argparse import ArgumentParser

from komodo.chessbuddy.lib.welcome import welcome


def main() -> None:
    parser = get_argument_parser()
    args = parser.parse_args()
    print(welcome(args.name))


def get_argument_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("name", help="Whom to greet")
    return parser


if __name__ == "__main__":
    main()
