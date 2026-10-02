from __future__ import annotations

from f2m.core.exceptions import F2MCliError
from f2m.cli.models import CliArgs, CliCommand, ConfigAction, OutputFormat


def parse_args(argv: list[str]) -> CliArgs:
    """
    Parse command-line argument vector into a typed CliArgs instance.

    Enforces flag extraction, mutual exclusivity, alias resolution,
    and missing/invalid argument validation according to Phase 4 contracts.
    """
    if not argv:
        return CliArgs(command=CliCommand.MENU)

    tokens: list[str] = list(argv)
    output_format: OutputFormat = OutputFormat.HUMAN
    has_json = False
    has_plain = False
    no_color = False
    config_path: str | None = None
    wants_help = False
    wants_version = False

    cleaned_tokens: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "--json":
            has_json = True
            i += 1
        elif token == "--plain":
            has_plain = True
            i += 1
        elif token == "--no-color":
            no_color = True
            i += 1
        elif token == "--config":
            if i + 1 < len(tokens):
                config_path = tokens[i + 1]
                i += 2
            else:
                raise F2MCliError("Option --config requires an argument", exit_code=2)
        elif token.startswith("--config="):
            config_path = token.split("=", 1)[1]
            i += 1
        elif token in ("--help", "-h"):
            wants_help = True
            i += 1
        elif token in ("--version", "-V"):
            wants_version = True
            i += 1
        else:
            cleaned_tokens.append(token)
            i += 1

    if has_json and has_plain:
        raise F2MCliError("Cannot combine --json and --plain options", exit_code=2)

    if has_json:
        output_format = OutputFormat.JSON
    elif has_plain:
        output_format = OutputFormat.PLAIN

    if not cleaned_tokens:
        if wants_help:
            return CliArgs(command=CliCommand.HELP, format=output_format, no_color=no_color, config_path=config_path)
        if wants_version:
            return CliArgs(command=CliCommand.VERSION, format=output_format, no_color=no_color, config_path=config_path)
        if output_format != OutputFormat.HUMAN:
            raise F2MCliError("A command is required when using --json or --plain", exit_code=2)
        return CliArgs(command=CliCommand.MENU, no_color=no_color, config_path=config_path)

    cmd_raw = cleaned_tokens[0].lower()
    rest = cleaned_tokens[1:]

    # Resolve subcommand and aliases
    if cmd_raw in ("help", "--help", "-h"):
        command = CliCommand.HELP
        query = rest[0].lower() if rest else None
        return CliArgs(command=command, format=output_format, query=query, no_color=no_color, config_path=config_path)

    if cmd_raw in ("version", "--version", "-V"):
        return CliArgs(command=CliCommand.VERSION, format=output_format, no_color=no_color, config_path=config_path)

    if wants_help:
        # e.g., f2m search --help -> help for search
        return CliArgs(command=CliCommand.HELP, format=output_format, query=cmd_raw, no_color=no_color, config_path=config_path)

    if cmd_raw in ("search", "s"):
        command = CliCommand.SEARCH
        query = " ".join(rest).strip() if rest else None
        if output_format != OutputFormat.HUMAN and not query:
            raise F2MCliError("Search query is required in non-interactive mode", exit_code=2)
        return CliArgs(command=command, format=output_format, query=query, no_color=no_color, config_path=config_path, raw_args=rest)

    if cmd_raw == "url":
        command = CliCommand.URL
        if not rest:
            raise F2MCliError("usage: f2m url <post-url>", exit_code=2)
        url_arg = rest[0].strip()
        if not url_arg:
            raise F2MCliError("usage: f2m url <post-url>", exit_code=2)
        return CliArgs(command=command, format=output_format, url=url_arg, no_color=no_color, config_path=config_path, raw_args=rest)

    if cmd_raw in ("categories", "cat", "c"):
        return CliArgs(command=CliCommand.CATEGORIES, format=output_format, no_color=no_color, config_path=config_path, raw_args=rest)

    if cmd_raw in ("config", "cfg"):
        command = CliCommand.CONFIG
        if rest:
            sub = rest[0].lower()
            if sub == "get":
                if len(rest) < 2 or not rest[1].strip():
                    raise F2MCliError("usage: f2m config get <key>", exit_code=2)
                return CliArgs(
                    command=command,
                    format=output_format,
                    config_action=ConfigAction.GET,
                    config_key=rest[1].strip(),
                    no_color=no_color,
                    config_path=config_path,
                    raw_args=rest,
                )
            if sub == "set":
                if len(rest) < 3 or not rest[1].strip():
                    raise F2MCliError("usage: f2m config set <key> <value>", exit_code=2)
                val = " ".join(rest[2:]).strip()
                return CliArgs(
                    command=command,
                    format=output_format,
                    config_action=ConfigAction.SET,
                    config_key=rest[1].strip(),
                    config_val=val,
                    no_color=no_color,
                    config_path=config_path,
                    raw_args=rest,
                )
        return CliArgs(
            command=command,
            format=output_format,
            config_action=ConfigAction.SHOW,
            no_color=no_color,
            config_path=config_path,
            raw_args=rest,
        )

    if cmd_raw in ("test", "t"):
        return CliArgs(command=CliCommand.TEST, format=output_format, no_color=no_color, config_path=config_path, raw_args=rest)

    raise F2MCliError(f"unknown command '{cleaned_tokens[0]}'", exit_code=2)
