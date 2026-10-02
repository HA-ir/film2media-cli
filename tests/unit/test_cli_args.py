import pytest
from f2m.cli.models import CliCommand, ConfigAction, OutputFormat
from f2m.cli.parser import parse_args
from f2m.core.exceptions import F2MCliError


def test_parse_args_bare_invocation():
    args = parse_args([])
    assert args.command == CliCommand.MENU
    assert args.format == OutputFormat.HUMAN


def test_parse_args_help_flags():
    for flag in ("--help", "-h", "help"):
        args = parse_args([flag])
        assert args.command == CliCommand.HELP


def test_parse_args_version_flags():
    for flag in ("--version", "-V", "version"):
        args = parse_args([flag])
        assert args.command == CliCommand.VERSION


def test_parse_args_global_flags_placement():
    # Flag preceding command
    args1 = parse_args(["--json", "search", "Inception"])
    assert args1.command == CliCommand.SEARCH
    assert args1.format == OutputFormat.JSON
    assert args1.query == "Inception"

    # Flag following command
    args2 = parse_args(["search", "Inception", "--json"])
    assert args2.command == CliCommand.SEARCH
    assert args2.format == OutputFormat.JSON
    assert args2.query == "Inception"

    # Plain flag
    args3 = parse_args(["url", "https://example.com/post/", "--plain"])
    assert args3.command == CliCommand.URL
    assert args3.format == OutputFormat.PLAIN
    assert args3.url == "https://example.com/post/"


def test_parse_args_mutual_exclusivity_conflict():
    with pytest.raises(F2MCliError) as exc_info:
        parse_args(["search", "Inception", "--json", "--plain"])
    assert exc_info.value.exit_code == 2
    assert "Cannot combine --json and --plain" in str(exc_info.value)


def test_parse_args_search_multi_token_query():
    args = parse_args(["search", "breaking", "bad", "2008"])
    assert args.command == CliCommand.SEARCH
    assert args.query == "breaking bad 2008"


def test_parse_args_search_missing_query_non_interactive():
    with pytest.raises(F2MCliError) as exc_info:
        parse_args(["search", "--json"])
    assert exc_info.value.exit_code == 2


def test_parse_args_url_missing_argument():
    with pytest.raises(F2MCliError) as exc_info:
        parse_args(["url"])
    assert exc_info.value.exit_code == 2


def test_parse_args_config_subcommands():
    # Dump
    args1 = parse_args(["config"])
    assert args1.command == CliCommand.CONFIG
    assert args1.config_action == ConfigAction.SHOW

    # Get
    args2 = parse_args(["config", "get", "base_url"])
    assert args2.command == CliCommand.CONFIG
    assert args2.config_action == ConfigAction.GET
    assert args2.config_key == "base_url"

    # Set
    args3 = parse_args(["config", "set", "proxy", "http://127.0.0.1:8080"])
    assert args3.command == CliCommand.CONFIG
    assert args3.config_action == ConfigAction.SET
    assert args3.config_key == "proxy"
    assert args3.config_val == "http://127.0.0.1:8080"


def test_parse_args_config_missing_parameters():
    with pytest.raises(F2MCliError) as exc_info:
        parse_args(["config", "get"])
    assert exc_info.value.exit_code == 2

    with pytest.raises(F2MCliError) as exc_info2:
        parse_args(["config", "set", "proxy"])
    assert exc_info2.value.exit_code == 2


def test_parse_args_alias_resolution():
    assert parse_args(["s", "avatar"]).command == CliCommand.SEARCH
    assert parse_args(["cat"]).command == CliCommand.CATEGORIES
    assert parse_args(["c"]).command == CliCommand.CATEGORIES
    assert parse_args(["cfg"]).command == CliCommand.CONFIG
    assert parse_args(["t"]).command == CliCommand.TEST


def test_parse_args_unknown_command():
    with pytest.raises(F2MCliError) as exc_info:
        parse_args(["foobar"])
    assert exc_info.value.exit_code == 2
    assert "unknown command 'foobar'" in str(exc_info.value)
