from argparse import Action, ArgumentParser

class ParsePlayerAction(Action):
    def __init__(self, *args, **kwargs):
        Action.__init__(self, *args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if 2 < len(values) < 7:
            setattr(namespace, self.dest, values)
        else:
            raise ValueError("VtES expects three to six players")

def main():
    parser = ArgumentParser()
    subcommands = parser.add_subparsers()

    add = subcommands.add_parser("add")
    add.add_argument("players", action=ParsePlayerAction, nargs='*')

    parser.parse_args()


if __name__ == "__main__":
    main()
