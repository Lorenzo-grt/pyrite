"""Empty timelines keep their machine envelope on both CLI surfaces (#1947)."""

import json

import pytest
import yaml
from typer.testing import CliRunner

from pyrite.read_cli import app as read_app


def run(world, surface, *args):
    if surface == "read":
        result = CliRunner().invoke(read_app, ["timeline", *args])
    else:
        result = world.cli("timeline", "-k", "test-kb", *args)
    assert result.exit_code == 0, result.output
    return result.stdout


@pytest.mark.parametrize("surface", ["main", "read"])
@pytest.mark.parametrize("fmt", ["json", "yaml", "csv", "markdown"])
def test_empty_timeline_machine_formats(cli_world, surface, fmt):
    output = run(cli_world(), surface, "--format", fmt)
    if fmt == "json":
        assert json.loads(output) == {"count": 0, "events": []}
    elif fmt == "yaml":
        assert yaml.safe_load(output) == {"count": 0, "events": []}
    elif fmt == "csv":
        assert output.strip() == ""
    else:
        assert output.strip() == "# Timeline (0 events)"


def test_main_default_is_json(cli_world):
    assert json.loads(run(cli_world(), "main")) == {"count": 0, "events": []}


@pytest.mark.control(reason="empty rich output remains unchanged")
@pytest.mark.parametrize("surface", ["main", "read"])
def test_empty_rich_keeps_sentence(cli_world, surface):
    assert "No timeline events found." in run(cli_world(), surface, "--format", "rich")


@pytest.mark.control(reason="read CLI keeps its rich default")
def test_read_default_is_rich(cli_world):
    assert "No timeline events found." in run(cli_world(), "read")


@pytest.mark.control(reason="dated entries keep their existing envelope")
@pytest.mark.parametrize("surface", ["main", "read"])
def test_nonempty_timeline(cli_world, surface):
    world = cli_world()
    world.add_entry(
        "test-kb", "---\nid: event-one\ntitle: One\ntype: event\ndate: '2026-06-01'\n---\nBody.\n"
    )
    world.index()
    data = json.loads(run(world, surface, "--format", "json"))
    assert data["count"] == 1
    assert data["events"][0]["id"] == "event-one"
