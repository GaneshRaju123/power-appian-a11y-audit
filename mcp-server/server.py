#!/usr/bin/env python3
"""
Appian SAIL Source MCP Server

Connects directly to an Appian environment via the Deployment REST API,
exports application packages, parses the XML to extract SAIL definitions,
and exposes them as MCP tools for accessibility auditing.

Usage:
  Environment variables:
    APPIAN_URL       - Base URL (e.g., https://mysite.appiancloud.com)
    APPIAN_API_KEY   - API key with deployment permissions
    APPIAN_APP_UUID  - (Optional) Default application UUID to export
    APPIAN_LOCAL_ZIP - (Optional) Path to pre-exported ZIP file
    APPIAN_APP_NAME  - (Optional) Friendly name for the application

  The server caches exported packages locally in ~/.appian-sail-cache/
  so repeated queries don't re-export from Appian.
"""

import io
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Auto-install dependencies if missing (fallback for non-uv environments)
# ---------------------------------------------------------------------------
def _ensure_dependencies():
    """Install required packages if they're not available."""
    try:
        import mcp  # noqa: F401
        import httpx  # noqa: F401
    except ImportError:
        print("Installing dependencies (consider using 'uv run --with mcp[cli] --with httpx' instead)...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "mcp>=1.0.0", "httpx>=0.27.0"],
            stdout=sys.stderr, stderr=sys.stderr,
        )

_ensure_dependencies()

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APPIAN_URL = os.environ.get("APPIAN_URL", "")
APPIAN_API_KEY = os.environ.get("APPIAN_API_KEY", "")
APPIAN_APP_UUID = os.environ.get("APPIAN_APP_UUID", "")
CACHE_DIR = Path.home() / ".appian-sail-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# In-memory store of parsed objects
# ---------------------------------------------------------------------------
_objects: dict[str, dict] = {}
_loaded_apps: set[str] = set()

# ---------------------------------------------------------------------------
# Appian Deployment API helpers
# ---------------------------------------------------------------------------

async def _export_application(app_uuid: str) -> bytes:
    """Trigger an export via Appian Deployment API v2 and download the ZIP."""
    import asyncio
    import httpx

    base = APPIAN_URL.rstrip("/")
    url = f"{base}/suite/deployment-management/v2/deployments"
    headers = {
        "appian-api-key": APPIAN_API_KEY,
        "Action-Type": "export",
    }
    payload = {
        "exportType": "application",
        "uuids": [app_uuid],
        "name": f"a11y-audit-export-{int(time.time())}",
    }

    json_str = json.dumps(payload)

    async with httpx.AsyncClient(timeout=300) as client:
        # Appian v2 requires multipart/form-data with a 'json' field
        resp = await client.post(url, headers=headers, files={"json": (None, json_str)})
        print(f"[DEBUG] Export POST status: {resp.status_code}", file=sys.stderr)
        print(f"[DEBUG] Export POST body: {resp.text[:500]}", file=sys.stderr)
        if resp.status_code >= 400:
            raise RuntimeError(f"Export API returned {resp.status_code}: {resp.text}")
        result = resp.json()
        deploy_uuid = result["uuid"]

        for _ in range(60):
            status_resp = await client.get(f"{url}/{deploy_uuid}", headers={"appian-api-key": APPIAN_API_KEY})
            status_resp.raise_for_status()
            status_data = status_resp.json()
            status = status_data.get("status", "")
            print(f"[DEBUG] Export status: {status}", file=sys.stderr)
            if status in ("COMPLETED", "COMPLETED_WITH_EXPORT_ERRORS"):
                break
            if status == "FAILED":
                raise RuntimeError(f"Export failed: {status_data}")
            await asyncio.sleep(5)

        # Use /package-zip endpoint per Appian docs (not /download)
        pkg_url = status_data.get("packageZip", f"{url}/{deploy_uuid}/package-zip")
        print(f"[DEBUG] Downloading from: {pkg_url}", file=sys.stderr)
        download_resp = await client.get(pkg_url, headers={"appian-api-key": APPIAN_API_KEY})
        if download_resp.status_code >= 400:
            print(f"[DEBUG] Download failed: {download_resp.status_code} {download_resp.text[:500]}", file=sys.stderr)
        download_resp.raise_for_status()
        return download_resp.content


def _parse_zip(zip_bytes: bytes, app_name: str = "app") -> dict[str, dict]:
    """Parse an Appian export ZIP and extract SAIL definitions from XMLs.

    Appian export ZIPs have this structure:
      content/   -> interfaces, rules, constants, decisions, integrations, etc.
                    Each XML is a <contentHaul> with a child element whose tag
                    name indicates the type (rule, interface, constant, ...).
      processModel/    -> process models (<processModelHaul>)
      recordType/      -> record types (<recordTypeHaul>)
      webApi/          -> web APIs (<webApiHaul>)
      connectedSystem/ -> connected systems
      site/            -> sites
      datatype/        -> CDTs (.xsd files)
      dataStore/       -> data stores
      group/           -> groups
      application/     -> application metadata
    """
    objects = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if not name.endswith(".xml"):
                continue
            try:
                raw = zf.read(name).decode("utf-8", errors="replace")
                tree = ET.fromstring(raw)
            except ET.ParseError:
                continue

            folder = name.split("/")[0] if "/" in name else ""
            root_tag = _local_tag(tree.tag)

            # --- content/ folder: the main bucket for rules, interfaces, etc.
            if folder == "content" and root_tag == "contentHaul":
                obj = _parse_content_haul(tree, name, app_name)
                if obj:
                    objects[obj["name"]] = obj
                continue

            # --- processModel/ folder
            if folder == "processModel" and root_tag == "processModelHaul":
                obj = _parse_generic_haul(tree, "process_model_port", "Process Model", name, app_name)
                if obj:
                    objects[obj["name"]] = obj
                continue

            # --- recordType/ folder
            if folder == "recordType" and root_tag == "recordTypeHaul":
                obj = _parse_generic_haul(tree, "recordType", "Record Type", name, app_name)
                if obj:
                    objects[obj["name"]] = obj
                continue

            # --- webApi/ folder
            if folder == "webApi":
                obj = _parse_generic_haul(tree, "webApi", "Web API", name, app_name)
                if obj:
                    objects[obj["name"]] = obj
                continue

            # --- connectedSystem/ folder
            if folder == "connectedSystem":
                obj = _parse_generic_haul(tree, "connectedSystem", "Connected System", name, app_name)
                if obj:
                    objects[obj["name"]] = obj
                continue

            # --- site/ folder
            if folder == "site":
                obj = _parse_generic_haul(tree, "site", "Site", name, app_name)
                if obj:
                    objects[obj["name"]] = obj
                continue

            # --- dataStore/ folder
            if folder == "dataStore":
                obj = _parse_generic_haul(tree, "dataStore", "Data Store", name, app_name)
                if obj:
                    objects[obj["name"]] = obj
                continue

            # --- group/ folder (skip — not useful for SAIL auditing)
            # --- application/ folder (skip)
            # --- aiSkill/, aiAgent/ (skip)

    return objects


# ---------------------------------------------------------------------------
# Content-haul parser (handles rule, interface, constant, decision, etc.)
# ---------------------------------------------------------------------------

# Map from XML child element tag -> friendly type name
_CONTENT_TYPE_MAP = {
    "interface": "Interface",
    "rule": "Expression Rule",
    "constant": "Constant",
    "decision": "Decision",
    "outboundIntegration": "Integration",
    "document": "Document",
    "folder": "Folder",
    "rulesFolder": "Rules Folder",
    "file": "File",
    "communityKnowledgeCenter": "Knowledge Center",
    "typedValue": "Typed Value",
}


def _parse_content_haul(tree: ET.Element, filepath: str, app_name: str) -> Optional[dict]:
    """Parse a <contentHaul> XML and extract the design object."""
    for child in tree:
        tag = _local_tag(child.tag)
        obj_type = _CONTENT_TYPE_MAP.get(tag)
        if obj_type is None:
            continue

        obj_name = _child_text(child, "name") or Path(filepath).stem
        obj_uuid = _child_text(child, "uuid") or ""
        definition = _child_text(child, "definition") or ""
        description = _child_text(child, "description") or ""

        # Skip folders, documents, files, typed values without definitions
        if tag in ("folder", "rulesFolder", "file", "document",
                   "communityKnowledgeCenter", "typedValue") and not definition:
            return None

        return {
            "name": obj_name, "uuid": obj_uuid, "type": obj_type,
            "definition": definition, "description": description,
            "app": app_name, "file": filepath,
        }
    return None


def _parse_generic_haul(tree: ET.Element, inner_tag: str, obj_type: str,
                        filepath: str, app_name: str) -> Optional[dict]:
    """Parse a *Haul XML (processModelHaul, recordTypeHaul, etc.)."""
    inner = tree.find(inner_tag)
    if inner is None:
        # Try namespace-aware search
        for child in tree:
            if _local_tag(child.tag) == inner_tag:
                inner = child
                break
    if inner is None:
        return None

    # For recordType, name may be an attribute
    obj_name = inner.get("name") or _child_text(inner, "name") or Path(filepath).stem
    obj_uuid = inner.get(_ns_attr("uuid")) or _child_text(inner, "uuid") or ""
    definition = _child_text(inner, "definition") or ""
    description = _child_text(inner, "description") or ""

    return {
        "name": obj_name, "uuid": obj_uuid, "type": obj_type,
        "definition": definition, "description": description,
        "app": app_name, "file": filepath,
    }


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def _local_tag(tag: str) -> str:
    """Strip namespace from an XML tag: '{ns}local' -> 'local'."""
    return tag.split("}")[-1] if "}" in tag else tag


def _ns_attr(attr: str) -> str:
    """Return namespaced attribute for Appian's common namespace."""
    return f"{{http://www.appian.com/ae/types/2009}}{attr}"


def _child_text(el: ET.Element, tag: str) -> Optional[str]:
    """Find direct child element by local tag name and return its text."""
    # Try direct find first (no namespace)
    child = el.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    # Try with Appian namespace
    child = el.find(f"{{http://www.appian.com/ae/types/2009}}{tag}")
    if child is not None and child.text:
        return child.text.strip()
    # Fallback: iterate direct children
    for c in el:
        if _local_tag(c.tag) == tag and c.text:
            return c.text.strip()
    return None


# ---------------------------------------------------------------------------
# Cache & loading helpers
# ---------------------------------------------------------------------------

def _cache_path(app_uuid: str) -> Path:
    return CACHE_DIR / f"{app_uuid}.zip"


def _load_from_cache(app_uuid: str, app_name: str) -> bool:
    cp = _cache_path(app_uuid)
    if cp.exists():
        _objects.update(_parse_zip(cp.read_bytes(), app_name))
        _loaded_apps.add(app_uuid)
        return True
    return False


async def _ensure_loaded(app_uuid: str, app_name: str = "app"):
    if app_uuid in _loaded_apps:
        return
    if _load_from_cache(app_uuid, app_name):
        return
    zip_bytes = await _export_application(app_uuid)
    _cache_path(app_uuid).write_bytes(zip_bytes)
    _objects.update(_parse_zip(zip_bytes, app_name))
    _loaded_apps.add(app_uuid)


def _load_local_zip(zip_path: str, app_name: str = "app") -> int:
    p = Path(zip_path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"ZIP not found: {p}")
    objs = _parse_zip(p.read_bytes(), app_name)
    _objects.update(objs)
    _loaded_apps.add(f"local:{p.name}")
    return len(objs)


def _load_preexisting_cache():
    for zp in CACHE_DIR.glob("*.zip"):
        app_id = zp.stem
        if app_id not in _loaded_apps:
            _objects.update(_parse_zip(zp.read_bytes(), app_id))
            _loaded_apps.add(app_id)


# ---------------------------------------------------------------------------
# Pre-load on startup
# ---------------------------------------------------------------------------
_load_preexisting_cache()

local_zip = os.environ.get("APPIAN_LOCAL_ZIP")
if local_zip:
    _app_name = os.environ.get("APPIAN_APP_NAME", "app")
    try:
        _count = _load_local_zip(local_zip, _app_name)
        print(f"Pre-loaded {_count} objects from {local_zip}", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"Warning: {e}", file=sys.stderr)

# ---------------------------------------------------------------------------
# MCP Server (FastMCP API)
# ---------------------------------------------------------------------------

mcp = FastMCP("appian-sail-source")


@mcp.tool()
async def load_application(app_uuid: str = "", app_name: str = "app", local_zip: str = "") -> str:
    """Export and load an Appian application by UUID, or load from a local ZIP file."""
    if local_zip:
        count = _load_local_zip(local_zip, app_name)
        return f"Loaded {count} objects from local ZIP: {local_zip}"

    uuid = app_uuid or APPIAN_APP_UUID
    if not uuid:
        return "Error: Provide app_uuid or set APPIAN_APP_UUID env var."
    if not APPIAN_URL or not APPIAN_API_KEY:
        return "Error: Set APPIAN_URL and APPIAN_API_KEY env vars for live export."

    await _ensure_loaded(uuid, app_name)
    count = sum(1 for o in _objects.values() if o.get("app") == app_name)
    return f"Loaded {count} objects from application '{app_name}' ({uuid})."


@mcp.tool()
def list_objects(object_type: str = "", name_pattern: str = "") -> str:
    """List all loaded Appian design objects. Optionally filter by type or name pattern."""
    filtered = list(_objects.values())
    if object_type:
        filtered = [o for o in filtered if o["type"].lower() == object_type.lower()]
    if name_pattern:
        regex = re.compile(name_pattern, re.IGNORECASE)
        filtered = [o for o in filtered if regex.search(o["name"])]

    if not filtered:
        return "No objects found matching criteria."

    lines = [f"Found {len(filtered)} objects:\n"]
    for o in sorted(filtered, key=lambda x: x["name"]):
        has_def = "yes" if o.get("definition") else "no"
        lines.append(f"  [{o['type']}] {o['name']} (SAIL: {has_def})")
    return "\n".join(lines)


@mcp.tool()
def get_sail_code(object_name: str) -> str:
    """Get the SAIL definition (source code) of a specific Appian object."""
    obj = _objects.get(object_name)
    if not obj:
        matches = [o for n, o in _objects.items() if object_name.lower() in n.lower()]
        if len(matches) == 1:
            obj = matches[0]
        elif len(matches) > 1:
            names = [m["name"] for m in matches[:10]]
            return "Multiple matches found. Be more specific:\n" + "\n".join(names)

    if not obj:
        return f"Object '{object_name}' not found."

    definition = obj.get("definition", "")
    if not definition:
        return f"Object '{obj['name']}' found ({obj['type']}) but has no SAIL definition."

    return f"# {obj['name']} ({obj['type']})\n# UUID: {obj['uuid']}\n# App: {obj['app']}\n\n{definition}"


@mcp.tool()
def search_objects(query: str, object_type: str = "") -> str:
    """Search loaded objects by name, type, or content.

    Automatically maps a!componentName to SYSTEM_SYSRULES_componentName
    so searches work against Appian export XML.
    """
    q = query.lower()
    search_terms = [q]
    if query.startswith("a!"):
        sail_name = query[2:]
        search_terms.append(f"system_sysrules_{sail_name}".lower())

    results = []
    for o in _objects.values():
        if object_type and o["type"].lower() != object_type.lower():
            continue
        searchable = (o["name"].lower() + " " + o.get("description", "").lower()
                      + " " + o.get("definition", "").lower())
        if any(term in searchable for term in search_terms):
            results.append(o)

    if not results:
        return f"No objects matching '{query}'."

    lines = [f"Found {len(results)} objects matching '{query}':\n"]
    for o in sorted(results, key=lambda x: x["name"])[:50]:
        lines.append(f"  [{o['type']}] {o['name']}")
    if len(results) > 50:
        lines.append(f"  ... and {len(results) - 50} more")
    return "\n".join(lines)


@mcp.tool()
def get_interfaces_using_component(component: str) -> str:
    """Find all interfaces that use a specific SAIL component (e.g., a!gridField).

    Handles both standard SAIL names (a!gridField) and Appian export internal
    names (SYSTEM_SYSRULES_gridField). The exported XML uses internal names
    like #"SYSTEM_SYSRULES_gridField_v2" instead of a!gridField.
    """
    # Build search terms: the user-provided name + the SYSTEM_SYSRULES variant
    search_terms = [component.lower()]
    if component.startswith("a!"):
        # a!gridField -> SYSTEM_SYSRULES_gridField (also match _v2 etc.)
        sail_name = component[2:]  # strip "a!"
        search_terms.append(f"system_sysrules_{sail_name}".lower())
    elif "system_sysrules_" in component.lower():
        # Already an internal name, also try a! form
        base = component.lower().replace("system_sysrules_", "")
        # Strip version suffix like _v2
        base = re.sub(r"_v\d+$", "", base)
        search_terms.append(f"a!{base}")

    matches = []
    for o in _objects.values():
        if o["type"] != "Interface":
            continue
        defn = o.get("definition", "").lower()
        if any(term in defn for term in search_terms):
            matches.append(o["name"])

    if not matches:
        return f"No interfaces found using '{component}'."

    return f"Interfaces using {component} ({len(matches)}):\n" + "\n".join(sorted(matches))

@mcp.tool()
async def get_a11y_checklist() -> str:
    """Fetch the latest accessibility checklist from the Aurora Design System.

    Returns the live checklist from https://appian-design.github.io/aurora/accessibility/checklist/
    This is the authoritative source maintained by the Appian Accessibility team.
    Falls back to a cached version if the fetch fails.
    """
    import httpx

    AURORA_URL = "https://appian-design.github.io/aurora/accessibility/checklist/"
    cache_file = CACHE_DIR / "aurora-a11y-checklist.txt"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(AURORA_URL)
            resp.raise_for_status()
            html = resp.text

        # Parse the HTML to extract checklist rules as structured text
        rules = _parse_aurora_checklist(html)
        if rules:
            cache_file.write_text(rules, encoding="utf-8")
            return rules
    except Exception as e:
        print(f"[WARN] Failed to fetch Aurora checklist: {e}", file=sys.stderr)

    # Fallback to cached version
    if cache_file.exists():
        print("[INFO] Using cached Aurora checklist", file=sys.stderr)
        return cache_file.read_text(encoding="utf-8")

    return "Error: Could not fetch Aurora checklist and no cached version available."


def _parse_aurora_checklist(html: str) -> str:
    """Parse the Aurora checklist HTML page into structured text rules."""
    import re as _re

    # The Aurora page outputs rules as text blocks with category headers.
    # Strip HTML tags to get clean text, preserving structure.
    # Remove script/style blocks
    text = _re.sub(r'<script[^>]*>.*?</script>', '', html, flags=_re.DOTALL | _re.IGNORECASE)
    text = _re.sub(r'<style[^>]*>.*?</style>', '', text, flags=_re.DOTALL | _re.IGNORECASE)
    # Replace <br> and block-level tags with newlines
    text = _re.sub(r'<br\s*/?>', '\n', text, flags=_re.IGNORECASE)
    text = _re.sub(r'</(div|p|li|tr|h[1-6])>', '\n', text, flags=_re.IGNORECASE)
    # Strip remaining tags
    text = _re.sub(r'<[^>]+>', ' ', text)
    # Decode common HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    # Collapse whitespace within lines but preserve line breaks
    lines = []
    for line in text.split('\n'):
        cleaned = ' '.join(line.split())
        if cleaned:
            lines.append(cleaned)

    result = '\n'.join(lines)
    header = (
        "# Appian A11y Checklist (Aurora Design System)\n"
        "# Source: https://appian-design.github.io/aurora/accessibility/checklist/\n"
        "# This is the authoritative checklist maintained by the Appian Accessibility team.\n\n"
    )
    return header + result



if __name__ == "__main__":
    mcp.run()
