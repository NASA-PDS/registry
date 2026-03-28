#!/usr/bin/env python3
"""Generate a human-readable Markdown document from a Postman collection JSON file."""

import json
import re
import sys
from pathlib import Path


TESTRAIL_BASE_URL = "https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/"
GITHUB_BASE_URL = "https://github.com/"


def extract_testrail_ids(test_script: str) -> list[str]:
    """Extract TestRail case IDs (e.g. C2488906) from a test script string."""
    return re.findall(r"\bC\d{5,}\b", test_script)


def extract_test_names(test_script: str) -> list[tuple[str, list[str]]]:
    """Return list of (test_name, [testrail_ids]) from pm.test() calls."""
    results = []
    for match in re.finditer(r'pm\.test\(\s*["\']([^"\']+)["\']', test_script):
        name = match.group(1)
        ids = re.findall(r"\bC\d{5,}\b", name)
        # Strip leading IDs from the display name
        display = re.sub(r"^(C\d+\s+)+", "", name).strip()
        results.append((display, ids))
    return results


def extract_github_refs(name: str) -> list[str]:
    """Extract GitHub issue refs like NASA-PDS/registry-api#494 from a string."""
    return re.findall(r"NASA-PDS/[\w-]+#\d+", name)


def build_url(request: dict) -> str:
    """Reconstruct a readable URL from a Postman request object."""
    url_obj = request.get("url", {})
    if isinstance(url_obj, str):
        return url_obj
    raw = url_obj.get("raw", "")
    # Substitute path variables with their values
    for var in url_obj.get("variable", []):
        raw = raw.replace(f":{var['key']}", var.get("value", f":{var['key']}"))
    return raw


def get_accept_header(request: dict) -> str | None:
    for h in request.get("header", []):
        if h.get("key", "").lower() == "accept":
            return h.get("value")
    return None


def render_request(item: dict, depth: int, lines: list[str]) -> None:
    """Render a single request item as Markdown."""
    name = item.get("name", "Unnamed")
    request = item.get("request", {})
    method = request.get("method", "GET")
    url = build_url(request)
    accept = get_accept_header(request)

    heading = "#" * (depth + 1)
    lines.append(f"{heading} `{method}` {name}\n")

    # GitHub issue links
    gh_refs = extract_github_refs(name)
    if gh_refs:
        link_parts = []
        for ref in gh_refs:
            repo, issue = ref.split("#")
            link_parts.append(f"[{ref}]({GITHUB_BASE_URL}{repo}/issues/{issue})")
        lines.append("**GitHub:** " + " · ".join(link_parts) + "\n")

    lines.append(f"**URL:** `{url}`\n")

    if accept:
        lines.append(f"**Accept:** `{accept}`\n")

    # Test assertions
    all_test_lines: list[str] = []
    for event in item.get("event", []):
        if event.get("listen") == "test":
            script = event.get("script", {})
            exec_lines = script.get("exec", [])
            if isinstance(exec_lines, list):
                all_test_lines.extend(exec_lines)
            else:
                all_test_lines.append(exec_lines)

    if all_test_lines:
        test_script = "\n".join(all_test_lines)
        tests = extract_test_names(test_script)
        if tests:
            lines.append("**Tests:**\n")
            for display, ids in tests:
                if ids:
                    id_links = ", ".join(
                        f"[{i}]({TESTRAIL_BASE_URL}{i[1:]})" for i in ids
                    )
                    lines.append(f"- {display} ({id_links})")
                else:
                    lines.append(f"- {display}")
            lines.append("")

    lines.append("---\n")


def render_folder(item: dict, depth: int, lines: list[str]) -> None:
    """Recursively render a folder (item with sub-items)."""
    heading = "#" * (depth + 1)
    lines.append(f"{heading} {item['name']}\n")
    desc = item.get("description", "")
    if desc:
        lines.append(f"{desc}\n")
    for child in item.get("item", []):
        render_item(child, depth + 1, lines)


def render_item(item: dict, depth: int, lines: list[str]) -> None:
    if "item" in item:
        render_folder(item, depth, lines)
    else:
        render_request(item, depth, lines)


def generate_toc(items: list[dict], depth: int = 0) -> list[str]:
    """Generate a simple table of contents."""
    toc = []
    for item in items:
        indent = "  " * depth
        anchor = re.sub(r"[^\w\s-]", "", item["name"].lower()).strip()
        anchor = re.sub(r"[\s]+", "-", anchor)
        if "item" in item:
            toc.append(f"{indent}- [{item['name']}](#{anchor})")
            toc.extend(generate_toc(item["item"], depth + 1))
        else:
            method = item.get("request", {}).get("method", "GET")
            toc.append(f"{indent}- [`{method}`] [{item['name']}](#{anchor})")
    return toc


def main(input_path: Path, output_path: Path) -> None:
    with open(input_path) as f:
        collection = json.load(f)

    info = collection.get("info", {})
    name = info.get("name", "Postman Collection")
    description = info.get("description", "")
    items = collection.get("item", [])

    lines: list[str] = []

    lines.append(f"# {name}\n")
    if description:
        lines.append(f"{description}\n")

    lines.append(
        "> Auto-generated from `postman_collection.json`. Do not edit manually.\n"
    )
    lines.append("")

    lines.append("## Table of Contents\n")
    lines.extend(generate_toc(items))
    lines.append("")

    lines.append("---\n")

    for item in items:
        render_item(item, 1, lines)

    output_path.write_text("\n".join(lines) + "\n")
    print(f"Written to {output_path}")


if __name__ == "__main__":
    here = Path(__file__).parent
    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "postman_collection.json"
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_suffix(".md")
    main(input_file, output_file)
