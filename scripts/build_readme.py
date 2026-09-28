"""Render README.md from scripts/README.template.md and the tool catalog below.

Usage: python scripts/build_readme.py

Badges come from shields.io. Logos resolve in this order:
  si:<slug>         Simple Icons slug (https://simpleicons.org)
  dv:<folder/file>  Devicon SVG, recolored to white and embedded as a data URI
  None              text-only badge (no logo exists in either catalog)
"""

from __future__ import annotations

import base64
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "scripts" / "README.template.md"
OUTPUT = ROOT / "README.md"
DEVICON_RAW = "https://raw.githubusercontent.com/devicons/devicon/master/icons/"
# GitHub's image proxy hex-encodes badge URLs; long embedded logos break the image.
MAX_LOGO_LENGTH = 2500
LIGHT_BACKGROUNDS = {"F7DF1E", "85EA2D", "FCC624", "23D96C", "3DDC84"}


PORTFOLIO_URL = "https://harp-andres.github.io/mi-portafolio/"
LINKEDIN_URL = "https://www.linkedin.com/in/andresrodriguezpisa-seniorqa/"
EMAIL = "andresrdrgzps05@gmail.com"
GITHUB_URL = "https://github.com/Harp-Andres"


@dataclass(frozen=True)
class Tool:
    label: str
    logo: str | None
    color: str
    link: str | None = None

    @property
    def ref(self) -> str:
        return "b-" + re.sub(r"[^a-z0-9]+", "-", self.label.lower()).strip("-")


@dataclass(frozen=True)
class StackGroup:
    """A stack section: skillicons.dev icons first, then badges for tools skillicons lacks."""

    title: str
    icons: tuple[str, ...]
    tools: tuple[Tool, ...]


CONTACT: list[Tool] = [
    Tool("Portafolio", "si:githubpages", "2563EB", PORTFOLIO_URL),
    Tool("LinkedIn", "dv:linkedin/linkedin-plain.svg", "0A66C2", LINKEDIN_URL),
    Tool("Email", "si:gmail", "EA4335", f"mailto:{EMAIL}"),
    Tool("GitHub", "si:github", "181717", GITHUB_URL),
    Tool("Repo mi-portafolio", "si:github", "111827", f"{GITHUB_URL}/mi-portafolio"),
]

# Icon ids must exist on skillicons.dev: unknown ids render as empty gaps.
STACK: list[StackGroup] = [
    StackGroup("Lenguajes", ("java", "js", "ts", "cs", "html", "css"), (
        Tool("SQL", "dv:azuresqldatabase/azuresqldatabase-plain.svg", "336791"),
    )),
    StackGroup("Automatización Web · Mobile · API", ("selenium", "cypress", "postman", "gherkin"), (
        Tool("Playwright", "dv:playwright/playwright-plain.svg", "2EAD33"),
        Tool("Appium", "si:appium", "EE376D"),
        Tool("Serenity BDD", None, "3C8D3F"),
        Tool("Katalon Studio", None, "00A35C"),
        Tool("REST Assured", None, "00A86B"),
        Tool("Karate", None, "E08A00"),
        Tool("SoapUI", None, "6D9E2E"),
        Tool("Swagger", "si:swagger", "85EA2D"),
        Tool("Cucumber", "si:cucumber", "23D96C"),
        Tool("JUnit 5", "si:junit5", "25A162"),
        Tool("TestNG", None, "C0392B"),
        Tool("Reqnroll", None, "512BD4"),
        Tool("Android", "dv:android/android-plain.svg", "1E8E3E"),
        Tool("iOS", "si:ios", "000000"),
        Tool("JMeter", "si:apachejmeter", "D22128"),
        Tool("Gatling", "si:gatling", "FF9E2A"),
        Tool("Allure Report", None, "FF7B00"),
    )),
    StackGroup("CI/CD · DevOps · Cloud · Azure", (
        "git", "github", "githubactions", "gitlab", "jenkins", "docker", "kubernetes", "linux", "aws", "azure",
    ), (
        Tool("Azure DevOps", "dv:azuredevops/azuredevops-plain.svg", "0078D7"),
        Tool("AKS", "si:kubernetes", "0078D4"),
        Tool("ACR", "dv:azure/azure-plain.svg", "005BA1"),
        Tool("SonarQube", "si:sonarqubeserver", "126ED3"),
        Tool("BrowserStack", "dv:browserstack/browserstack-plain.svg", "E66F32"),
        Tool("Sauce Labs", "si:saucelabs", "E2231A"),
        Tool("AWS Device Farm", "dv:amazonwebservices/amazonwebservices-plain-wordmark.svg", "232F3E"),
        Tool("GitHub Pages", "si:githubpages", "222222"),
    )),
    StackGroup("Build · Bases de datos", ("gradle", "maven", "nodejs", "mysql", "postgres", "mongodb"), (
        Tool("SQL Server", "dv:azuresqldatabase/azuresqldatabase-plain.svg", "CC2927"),
        Tool("Oracle", "dv:oracle/oracle-original.svg", "F80000"),
    )),
    StackGroup("IDEs · Consola · Virtualización", ("idea", "vscode", "powershell", "bash"), (
        Tool("VirtualBox", "si:virtualbox", "183A61"),
        Tool("VMware", "si:vmware", "607078"),
    )),
    StackGroup("IA & Productividad", (), (
        Tool("GitHub Copilot", "si:githubcopilot", "000000"),
        Tool("Claude", "si:claude", "D97757"),
        Tool("Cursor", "si:cursor", "000000"),
        Tool("MCP Playwright", "si:modelcontextprotocol", "1A1A1A"),
        Tool("Prompting avanzado", None, "7C3AED"),
    )),
    StackGroup("Gestión & Colaboración", (), (
        Tool("Jira", "si:jira", "0052CC"),
        Tool("Azure Boards", "dv:azuredevops/azuredevops-plain.svg", "0078D7"),
        Tool("Scrum", None, "6DB33F"),
        Tool("Kanban", None, "0079BF"),
        Tool("Screenplay + POM", None, "111827"),
    )),
]


def fetch(url: str, attempts: int = 4) -> str:
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                return response.read().decode("utf-8")
        except OSError:
            if attempt == attempts:
                raise
            time.sleep(attempt)
    raise RuntimeError(url)


def white_svg(svg: str, decimals: int) -> str:
    svg = re.sub(r"<\?xml.*?\?>|<!--.*?-->|<metadata.*?</metadata>", "", svg, flags=re.S)
    svg = re.sub(r'\sfill="(?!none)[^"]*"', "", svg)
    svg = re.sub(r"fill:\s*(?!none)[^;\"]+;?", "", svg)
    def rounded(match: re.Match[str]) -> str:
        glued = match.start() > 0 and svg[match.start() - 1] in "0123456789."
        return (" " if glued else "") + f"{float(match.group()):.{decimals}f}"

    svg = re.sub(r"\d*\.\d+", rounded, svg)
    svg = re.sub(r">\s+<", "><", re.sub(r"\s+", " ", svg)).strip()
    return re.sub(r"<svg\b", '<svg fill="#ffffff"', svg, count=1)


def devicon_data_uri(path: str) -> str:
    source = fetch(DEVICON_RAW + path)
    for decimals in (1, 0):
        encoded = base64.b64encode(white_svg(source, decimals).encode()).decode()
        data_uri = urllib.parse.quote(f"data:image/svg+xml;base64,{encoded}", safe="")
        if len(data_uri) <= MAX_LOGO_LENGTH:
            return data_uri
    print(f"warning: {path} logo is {len(data_uri)} chars even rounded, rendering it without logo")
    return ""


def logo_params(tool: Tool, cache: dict[str, str]) -> str:
    if tool.logo is None:
        return ""
    kind, value = tool.logo.split(":", 1)
    if kind == "si":
        logo_color = "black" if tool.color in LIGHT_BACKGROUNDS else "white"
        return f"&logo={value}&logoColor={logo_color}"
    if value not in cache:
        cache[value] = devicon_data_uri(value)
    return f"&logo={cache[value]}" if cache[value] else ""


def badge_url(tool: Tool, cache: dict[str, str]) -> str:
    text = urllib.parse.quote(tool.label.replace("-", "--").replace("_", "__"), safe="")
    return f"https://img.shields.io/badge/{text}-{tool.color}?style=for-the-badge{logo_params(tool, cache)}"


def render_group(group: StackGroup) -> str:
    parts = [f"### {group.title}"]
    if group.icons:
        icons = ",".join(group.icons)
        parts.append(
            '<p align="center">\n'
            f'  <img src="https://skillicons.dev/icons?i={icons}&perline={len(group.icons)}" alt="{group.title}" />\n'
            "</p>"
        )
    badges = " ".join(f"![{t.label}][{t.ref}]" for t in group.tools)
    parts.append(f'<div align="center">\n\n{badges}\n\n</div>')
    return "\n\n".join(parts)


def render() -> str:
    tools = CONTACT + [tool for group in STACK for tool in group.tools]
    unique = {tool.ref: tool for tool in tools}
    if len(unique) != len(tools):
        raise ValueError("A tool is listed twice; each tool belongs to one stack group")
    cache: dict[str, str] = {}
    contact = " ".join(f"[![{t.label}][{t.ref}]]({t.link})" for t in CONTACT)
    refs = [f"[{ref}]: {badge_url(tool, cache)}" for ref, tool in sorted(unique.items())]
    values = {
        "{{CONTACT_BADGES}}": contact,
        "{{STACK}}": "\n\n".join(render_group(group) for group in STACK),
        "{{BADGE_REFS}}": "\n".join(refs),
        "{{PORTFOLIO_URL}}": PORTFOLIO_URL,
        "{{LINKEDIN_URL}}": LINKEDIN_URL,
        "{{EMAIL}}": EMAIL,
    }
    readme = TEMPLATE.read_text(encoding="utf-8")
    for placeholder, value in values.items():
        readme = readme.replace(placeholder, value)
    return readme


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"README.md written ({OUTPUT.stat().st_size} bytes)")
