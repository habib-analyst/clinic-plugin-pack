"""Tests for the clinic-plugin-pack build.

Covers: manifest shape (per KILLGATE.md's documented official format),
packed-skill fidelity to the typed source, the validator (must pass
clean), and a live MCP stdio session against the packed server exactly
as .mcp.json registers it.
"""
import json
import os
import re
import subprocess
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugin")
SERVER = os.path.join(PLUGIN, "mcp", "clinic_mcp_server.py")

EXPECTED_SKILLS = {
    "find-doctor": "doctors_search",
    "book-appointment": "appointment_book",
    "reschedule-appointment": "appointment_reschedule",
    "cancel-appointment": "appointment_cancel",
}


def load_manifest():
    with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def skill_frontmatter(name):
    path = os.path.join(PLUGIN, "skills", name, "SKILL.md")
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "no frontmatter in %s" % path
    return yaml.safe_load(m.group(1)), text


# ---------------------------------------------------------------- manifest

def test_manifest_required_fields():
    man = load_manifest()
    assert man["name"] == "clinic-plugin-pack"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", man["name"])
    assert man["description"].strip()
    assert man["author"]["name"] == "Habib Ur Rehman"
    assert man["version"] == "0.1.0"  # version of the source pack


def test_validator_passes_clean():
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "validate_plugin.py")],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "35/35 checks passed" in r.stdout
    assert "0 dangling" in r.stdout


# ------------------------------------------------------------------- skills

@pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
def test_skill_file_matches_source(skill):
    fm, text = skill_frontmatter(skill)
    assert fm["name"] == skill
    # the packc source description leads the packed description
    src = open(os.path.join(PLUGIN, "src", "clinic.pack"),
               encoding="utf-8").read()
    block = re.search(r"skill\s+%s\s*\{(.*?)\n\}" % re.escape(skill),
                      src, re.DOTALL).group(1)
    src_desc = re.search(r'description:\s*"([^"]+)"', block).group(1)
    assert fm["description"].startswith(src_desc)
    # every declared trigger is carried into the packed skill
    triggers = re.findall(r'"([^"]+)"', re.search(
        r"trigger:\s*\[(.*?)\]", block, re.DOTALL).group(1))
    for t in triggers:
        assert t in fm["description"], (skill, t)
        assert t in text
    # the skill names its MCP tool and the escalation policy
    assert "`%s`" % EXPECTED_SKILLS[skill] in text
    assert "human_only" in text
    assert "confirm" in text


def test_all_source_skills_packed():
    packed = sorted(os.listdir(os.path.join(PLUGIN, "skills")))
    assert packed == sorted(EXPECTED_SKILLS)


# ---------------------------------------------------------------------- MCP

def mcp_session(requests):
    proc = subprocess.Popen(
        [sys.executable, SERVER], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, text=True)
    out, _ = proc.communicate(
        "".join(json.dumps(r) + "\n" for r in requests), timeout=30)
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def rpc(method, params=None, rid=1):
    return {"jsonrpc": "2.0", "id": rid, "method": method,
            "params": params or {}}


def test_mcp_initialize_and_tools_list():
    init, listing = mcp_session([rpc("initialize", rid=1),
                                 rpc("tools/list", rid=2)])
    assert init["result"]["pack"] == "clinic"
    assert init["result"]["version"] == "0.1.0"
    names = [t["name"] for t in listing["result"]["tools"]]
    assert sorted(names) == sorted(EXPECTED_SKILLS.values())
    for t in listing["result"]["tools"]:
        assert t["description"] and t["inputSchema"]["type"] == "object"


def test_mcp_call_valid_and_invalid():
    ok, bad_type, missing, unknown = mcp_session([
        rpc("tools/call", {"name": "doctors_search",
                           "arguments": {"specialty": "cardiology",
                                         "day": "monday"}}, rid=1),
        rpc("tools/call", {"name": "doctors_search",
                           "arguments": {"specialty": 42}}, rid=2),
        rpc("tools/call", {"name": "appointment_book",
                           "arguments": {"doctor": "Dr Ahmed"}}, rid=3),
        rpc("tools/call", {"name": "nope", "arguments": {}}, rid=4),
    ])
    payload = json.loads(ok["result"]["content"][0]["text"])
    assert payload["tool"] == "doctors_search"
    assert "error" not in ok
    assert bad_type["error"]["code"] == -32602
    assert "validation" in bad_type["error"]["message"]
    assert missing["error"]["code"] == -32602
    assert unknown["error"]["code"] == -32602


def test_mcp_config_points_at_packed_server():
    cfg = json.load(open(os.path.join(PLUGIN, ".mcp.json"),
                         encoding="utf-8"))
    (entry,) = cfg["mcpServers"].values()
    assert entry["command"] == "python3"
    rel = entry["args"][0].replace("${CLAUDE_PLUGIN_ROOT}", "").lstrip("/")
    assert os.path.isfile(os.path.join(PLUGIN, rel))
    assert os.path.join(PLUGIN, rel) == SERVER
