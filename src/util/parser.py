import argparse

def DevelopmentOverrideActionFactory(overrides):
    class DevelopmentOverrideAction(argparse.Action):
        ARG_OVERRIDES = overrides

        def __init__(self, option_strings, dest, help=None):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, ns, values, option_string=None):
            setattr(ns, self.dest, values)
            for dest, value in self.ARG_OVERRIDES:
                setattr(ns, dest, value)
    return DevelopmentOverrideAction

# Taken from https://github.com/python/cpython/blob/b4e5eeac267c436bb60776dc5be771d3259bd298/Lib/argparse.py#L856-L895
class BooleanOptionalAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest,
                 const=None,
                 default=None,
                 type=None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None):

        _option_strings = []
        for option_string in option_strings:
            _option_strings.append(option_string)

            if option_string.startswith('--'):
                option_string = '--no-' + option_string[2:]
                _option_strings.append(option_string)

        if help is not None and default is not None:
            help += f" (default: {default})"

        super().__init__(
            option_strings=_option_strings,
            dest=dest,
            nargs=0,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string in self.option_strings:
            setattr(namespace, self.dest, not option_string.startswith('--no-'))

    def format_usage(self):
        return ' | '.join(self.option_strings)

