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


@dataclass(frozen=True)
class Tool:
    label: str
    logo: str | None
    color: str
    link: str | None = None

    @property
    def ref(self) -> str:
        return "b-" + re.sub(r"[^a-z0-9]+", "-", self.label.lower()).strip("-")


CONTACT: list[Tool] = [
    Tool("Portafolio", "si:githubpages", "2563EB", PORTFOLIO_URL),
    Tool("LinkedIn", "dv:linkedin/linkedin-plain.svg", "0A66C2", LINKEDIN_URL),
    Tool("Email", "si:gmail", "EA4335", f"mailto:{EMAIL}"),
]

CATALOG: list[tuple[str, list[Tool]]] = [
    ("🌐 Automatización Web", [
        Tool("Selenium", "si:selenium", "43B02A"),
        Tool("Playwright", "dv:playwright/playwright-plain.svg", "2EAD33"),
        Tool("Cypress", "si:cypress", "17202C"),
        Tool("Serenity BDD", None, "3C8D3F"),
        Tool("HTML5", "si:html5", "E34F26"),
        Tool("CSS", "si:css", "663399"),
    ]),
    ("📱 Automatización Mobile", [
        Tool("Appium", "si:appium", "EE376D"),
        Tool("Android", "dv:android/android-plain.svg", "1E8E3E"),
        Tool("iOS", "si:ios", "000000"),
        Tool("BrowserStack", "dv:browserstack/browserstack-plain.svg", "E66F32"),
        Tool("Sauce Labs", "si:saucelabs", "E2231A"),
        Tool("AWS Device Farm", "dv:amazonwebservices/amazonwebservices-plain-wordmark.svg", "232F3E"),
    ]),
    ("🔌 API & Backend Testing", [
        Tool("REST Assured", None, "00A86B"),
        Tool("Karate", None, "E08A00"),
        Tool("Postman", "si:postman", "FF6C37"),
        Tool("SoapUI", None, "6D9E2E"),
        Tool("Swagger", "si:swagger", "85EA2D"),
    ]),
    ("🥒 BDD & Frameworks", [
        Tool("Cucumber", "si:cucumber", "23D96C"),
        Tool("Reqnroll", None, "512BD4"),
        Tool("JUnit 5", "si:junit5", "25A162"),
        Tool("TestNG", None, "C0392B"),
        Tool("Katalon Studio", None, "00A35C"),
    ]),
    ("⚡ Performance", [
        Tool("JMeter", "si:apachejmeter", "D22128"),
        Tool("Gatling", "si:gatling", "FF9E2A"),
    ]),
    ("🚀 CI/CD & DevOps", [
        Tool("GitHub Actions", "si:githubactions", "2088FF"),
        Tool("GitLab CI", "si:gitlab", "FC6D26"),
        Tool("Jenkins", "si:jenkins", "D24939"),
        Tool("Azure DevOps", "dv:azuredevops/azuredevops-plain.svg", "0078D7"),
        Tool("Docker", "si:docker", "2496ED"),
        Tool("Git", "si:git", "F05032"),
        Tool("SonarQube", "si:sonarqubeserver", "126ED3"),
    ]),
    ("☁️ Azure & Contenedores", [
        Tool("Azure", "dv:azure/azure-plain.svg", "0078D4"),
        Tool("AKS", "si:kubernetes", "0078D4"),
        Tool("ACR", "dv:azure/azure-plain.svg", "005BA1"),
        Tool("Kubernetes", "si:kubernetes", "326CE5"),
    ]),
    ("💻 Lenguajes", [
        Tool("Java", "si:openjdk", "ED8B00"),
        Tool("JavaScript", "si:javascript", "F7DF1E"),
        Tool("TypeScript", "si:typescript", "3178C6"),
        Tool("C#", "dv:csharp/csharp-plain.svg", "512BD4"),
        Tool("SQL", "dv:azuresqldatabase/azuresqldatabase-plain.svg", "336791"),
    ]),
    ("🗄️ Bases de datos", [
        Tool("SQL Server", "dv:azuresqldatabase/azuresqldatabase-plain.svg", "CC2927"),
        Tool("MySQL", "si:mysql", "4479A1"),
        Tool("Oracle", "dv:oracle/oracle-original.svg", "F80000"),
        Tool("PostgreSQL", "si:postgresql", "4169E1"),
        Tool("MongoDB", "si:mongodb", "47A248"),
    ]),
    ("🧱 Build & Reporting", [
        Tool("Gradle", "si:gradle", "02303A"),
        Tool("Maven", "si:apachemaven", "C71A36"),
        Tool("Node.js", "si:nodedotjs", "339933"),
        Tool("Allure Report", None, "FF7B00"),
        Tool("GitHub Pages", "si:githubpages", "222222"),
    ]),
    ("🤖 IA aplicada a QA", [
        Tool("GitHub Copilot", "si:githubcopilot", "000000"),
        Tool("Cursor", "si:cursor", "000000"),
        Tool("Claude", "si:claude", "D97757"),
        Tool("MCP Playwright", "si:modelcontextprotocol", "1A1A1A"),
    ]),
    ("📋 Gestión ágil", [
        Tool("Jira", "si:jira", "0052CC"),
        Tool("Azure Boards", "dv:azuredevops/azuredevops-plain.svg", "0078D7"),
        Tool("Scrum", None, "6DB33F"),
        Tool("Kanban", None, "0079BF"),
    ]),
    ("🖥️ Entornos & Scripting", [
        Tool("PowerShell", "dv:powershell/powershell-plain.svg", "5391FE"),
        Tool("Bash", "si:gnubash", "4EAA25"),
        Tool("Linux", "si:linux", "FCC624"),
        Tool("VirtualBox", "si:virtualbox", "183A61"),
        Tool("VMware", "si:vmware", "607078"),
        Tool("IntelliJ IDEA", "si:intellijidea", "000000"),
        Tool("VS Code", "dv:vscode/vscode-plain.svg", "007ACC"),
    ]),
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


def render() -> str:
    tools = CONTACT + [tool for _, group in CATALOG for tool in group]
    unique = {tool.ref: tool for tool in tools}
    cache: dict[str, str] = {}
    contact = " ".join(f"[![{t.label}][{t.ref}]]({t.link})" for t in CONTACT)
    table = ["| Especialidad | Herramientas |", "| :-- | :-- |"]
    table += [
        f"| **{category}** | " + " ".join(f"![{t.label}][{t.ref}]" for t in group) + " |"
        for category, group in CATALOG
    ]
    refs = [f"[{ref}]: {badge_url(tool, cache)}" for ref, tool in sorted(unique.items())]
    values = {
        "{{CONTACT_BADGES}}": contact,
        "{{TOOLS_TABLE}}": "\n".join(table),
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
