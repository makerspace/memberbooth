import argparse
from enum import Enum, unique
from typing import Any, Sequence


@unique
class ArgparseEnum(Enum):
    @classmethod
    def from_string(cls: Any, s: str) -> Any:
        try:
            return cls(s)
        except Exception as e:
            s = s.lower()
            for im in cls:
                if im.value.lower() == s or im.name.lower() == s:
                    return im
            raise e

    def __str__(self) -> Any:
        return self.value


def DevelopmentOverrideActionFactory(overrides: Sequence[tuple[str, str | bool]]) -> type[argparse.Action]:
    class DevelopmentOverrideAction(argparse.Action):
        ARG_OVERRIDES = overrides

        def __init__(self, option_strings: Sequence[str], dest: str, help: str | None = None) -> None:
            super().__init__(option_strings, dest, default=False, nargs=0)

        def __call__(self, parser: Any, ns: Any, values: Any, option_string: str | None = None) -> None:
            setattr(ns, self.dest, True)
            for dest, value in self.ARG_OVERRIDES:
                setattr(ns, dest, value)

    return DevelopmentOverrideAction


# Taken from https://github.com/python/cpython/blob/b4e5eeac267c436bb60776dc5be771d3259bd298/Lib/argparse.py#L856-L895
def BooleanOptionalActionFactory(assertive_prefix: str="use-", deassertive_prefix: str="no-") -> type[argparse.Action]:
    def format_prefix(prefix: str) -> str:
        if not prefix.startswith("--"):
            prefix = "--" + prefix
        if not prefix.endswith("-"):
            prefix = prefix + "-"
        return prefix

    assertive_prefix = format_prefix(assertive_prefix)
    deassertive_prefix = format_prefix(deassertive_prefix)

    class BooleanOptionalAction(argparse.Action):
        def __init__(self,
                     option_strings: Sequence[str],
                     dest: str,
                     const: Any = None,
                     default: Any = None,
                     choices: Sequence[Any] | None = None,
                     required: bool = False,
                     help: str | None = None,
                     metavar: str | None = None):

            assert isinstance(default, bool), "Default value must be of bool type"

            self.assertive_prefix = assertive_prefix
            self.deassertive_prefix = deassertive_prefix

            _option_strings = []
            for option_string in option_strings:
                if not option_string.startswith('--'):
                    raise ValueError("BooleanOptionalAction must be an optional argument (i.e. start with --)")

                optname = option_string[2:]

                if option_string.startswith(self.assertive_prefix):
                    self.assertive_opt = option_string
                    self.deassertive_opt = deassertive_prefix + optname[len(self.assertive_prefix):]
                elif option_string.startswith(self.deassertive_prefix):
                    self.assertive_opt = assertive_prefix + optname[len(self.deassertive_prefix):]
                    self.deassertive_opt = option_string
                else:
                    self.assertive_opt = assertive_prefix + optname
                    self.deassertive_opt = deassertive_prefix + optname

                if default:
                    _option_strings.append(self.deassertive_opt)
                    _option_strings.append(self.assertive_opt)
                else:
                    _option_strings.append(self.assertive_opt)
                    _option_strings.append(self.deassertive_opt)

            if help is not None and default is not None:
                help += f" (default: {default})"

            super().__init__(
                option_strings=_option_strings,
                dest=dest,
                nargs=0,
                default=default,
                type=bool,
                choices=choices,
                required=required,
                help=help,
                metavar=metavar)

        def __call__(self, parser: Any, namespace: Any, values: str |  Sequence[Any] | None, option_string: str | None = None) -> None:
            if option_string in self.option_strings and option_string is not None:
                setattr(namespace, self.dest, not option_string.startswith(self.deassertive_prefix))

        def format_usage(self) -> str:
            return ' | '.join(self.option_strings)

    return BooleanOptionalAction
