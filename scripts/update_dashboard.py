#!/usr/bin/env python3
"""Refresh the profile's live data: the port-themed stats SVG and the « Activité récente » section.

Run by .github/workflows/dashboard.yml. Needs GITHUB_TOKEN; uses METRICS_TOKEN instead when set
(a personal token lets the contribution counts include private contributions).
Only public repositories and public events are ever shown.
"""
import json
import os
import re
import sys
import urllib.request
from collections import OrderedDict
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_assets import FOAM, MONO, NAVY_0, NAVY_1, NAVY_2, NAVY_3, ORANGE, SAND, SANS  # noqa: E402

USER = "NotSayk"
ORG = "MiniGamesSayk"
# Repos whose code is mostly not mine (forks of big projects) are left out of the language stats.
LANG_EXCLUDE = {"MiniGamesSayk/OpenClaude"}
MAX_ACTIVITY = 8

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
STATS_SVG = ROOT / "assets" / "generated" / "stats.svg"
TZ = ZoneInfo("Europe/Paris")
MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

LANG_COLORS = {
    "TypeScript": "#3178C6", "JavaScript": "#E9C46A", "Java": "#E63946", "Python": "#2A9D8F",
    "PHP": "#6C5CE7", "HTML": ORANGE, "CSS": "#1D7FD1", "C": "#5A6B7D", "Shell": "#5FA04E",
    "Dockerfile": "#2496ED", "SQL": "#457B9D", "PLpgSQL": "#457B9D", "Batchfile": "#9AA7B6",
}

TOKEN = os.environ.get("METRICS_TOKEN") or os.environ.get("GITHUB_TOKEN", "")


# ---------------------------------------------------------------- GitHub API
def api(path, data=None):
    url = path if path.startswith("https://") else f"https://api.github.com/{path.lstrip('/')}"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", f"{USER}-profile-dashboard")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def try_api(path, default, data=None):
    try:
        return api(path, data)
    except Exception as exc:  # one failing endpoint must not sink the whole refresh
        print(f"warning: {path}: {exc}", file=sys.stderr)
        return default


def public_repos():
    repos = try_api(f"users/{USER}/repos?per_page=100&type=owner", [])
    repos += try_api(f"orgs/{ORG}/repos?per_page=100&type=public", [])
    return [r for r in repos if not r.get("private")]


CONTRIB_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def contributions():
    res = try_api("graphql", None, {"query": CONTRIB_QUERY, "variables": {"login": USER}})
    try:
        return res["data"]["user"]["contributionsCollection"]
    except (TypeError, KeyError):
        return None


# ---------------------------------------------------------------- numbers
def streaks(days):
    """Current and longest run of days with at least one contribution."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    current = 0
    today = date.today().isoformat()
    for i, d in enumerate(reversed(days)):
        if d["contributionCount"]:
            current += 1
        elif i == 0 and d["date"] == today:
            continue  # today isn't over yet
        else:
            break
    return current, longest


def languages(repos):
    totals = {}
    for r in repos:
        if r.get("fork") or r["full_name"] in LANG_EXCLUDE:
            continue
        for lang, size in try_api(f"repos/{r['full_name']}/languages", {}).items():
            totals[lang] = totals.get(lang, 0) + size
    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    top = [(lang, size / total) for lang, size in ranked[:6]]
    rest = sum(size for _, size in ranked[6:]) / total
    if rest > 0.005:
        top.append(("Autres", rest))
    return top


def fmt(n):
    return f"{n:,}".replace(",", " ")


# ---------------------------------------------------------------- stats SVG
def esc(text):
    """Escape for SVG text and Markdown link labels."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("[", "(").replace("]", ")")


def render_stats(c, repos, langs):
    W, H = 1200, 540
    days = [d for w in c["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    current, longest = streaks(days)
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    tiles = [
        ("CONTRIBUTIONS", fmt(c["contributionCalendar"]["totalContributions"]), "sur 12 mois", ORANGE),
        ("COMMITS", fmt(c["totalCommitContributions"]), "sur 12 mois", "#2A9D8F"),
        ("PULL REQUESTS", fmt(c["totalPullRequestContributions"]), "sur 12 mois", "#457B9D"),
        ("SÉRIE ACTUELLE", f"{current} j", f"record : {longest} j", "#E63946"),
        ("DÉPÔTS PUBLICS", fmt(len(repos)), f"{USER} + {ORG}", "#6C5CE7"),
        ("ÉTOILES", fmt(stars), "reçues", "#D4A017"),
    ]
    tw, th, gap, x0 = 178, 104, 12, 30
    tile_svg = ""
    for i, (label, value, sub, color) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        ribs = "".join(
            f'<rect x="{x + k}" y="74" width="3" height="{th - 8}" fill="#000" fill-opacity=".12"/>' for k in range(10, tw - 6, 12)
        )
        tile_svg += f'''
    <g class="drop" style="animation-delay:{0.1 + i * 0.12:.2f}s">
      <rect x="{x}" y="70" width="{tw}" height="{th}" rx="4" fill="{color}"/>{ribs}
      <rect x="{x + 8}" y="78" width="{tw - 16}" height="{th - 16}" rx="4" fill="{NAVY_0}" fill-opacity=".62"/>
      <text x="{x + tw/2}" y="99" text-anchor="middle" font-family="{MONO}" font-size="11" font-weight="700" fill="{SAND}" letter-spacing="1">{label}</text>
      <text x="{x + tw/2}" y="136" text-anchor="middle" font-family="{SANS}" font-size="30" font-weight="800" fill="#FFFFFF">{esc(value)}</text>
      <text x="{x + tw/2}" y="158" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{FOAM}" fill-opacity=".75">{esc(sub)}</text>
    </g>'''

    # weekly "tide" of contributions
    weeks = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in c["contributionCalendar"]["weeks"]]
    cx0, cx1, cy0, cy1 = 40, W - 40, 230, 340
    peak = max(weeks) or 1
    step = (cx1 - cx0) / max(len(weeks) - 1, 1)
    pts = [(cx0 + i * step, cy1 - (v / peak) * (cy1 - cy0)) for i, v in enumerate(weeks)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{line} L{cx1},{cy1} L{cx0},{cy1} Z"
    months, seen = "", set()
    for i, w in enumerate(c["contributionCalendar"]["weeks"]):
        first = w["contributionDays"][0]["date"]
        m = int(first[5:7])
        if m not in seen and i > 0 and int(first[8:10]) <= 7:
            seen.add(m)
            months += f'<text x="{cx0 + i * step:.1f}" y="{cy1 + 20}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{FOAM}" fill-opacity=".6">{MONTHS[m - 1]}</text>'
    best = max(range(len(weeks)), key=lambda i: weeks[i])
    bx, by = pts[best]

    # cargo by language
    lx0, lx1, ly = 40, W - 40, 420
    bar, legend, x = "", "", lx0
    for i, (lang, share) in enumerate(langs):
        w = (lx1 - lx0) * share
        color = LANG_COLORS.get(lang, "#9AA7B6")
        ribs = "".join(f'<rect x="{x + k:.1f}" y="{ly + 4}" width="2.5" height="36" fill="#000" fill-opacity=".14"/>' for k in range(8, int(w) - 4, 10))
        bar += f'<g class="drop" style="animation-delay:{0.6 + i * 0.1:.2f}s"><rect x="{x:.1f}" y="{ly}" width="{max(w - 3, 1):.1f}" height="44" rx="3" fill="{color}"/>{ribs}</g>'
        col, row = i % 4, i // 4
        lgx, lgy = lx0 + col * 285, ly + 78 + row * 26
        legend += (
            f'<rect x="{lgx}" y="{lgy - 11}" width="14" height="14" rx="2" fill="{color}"/>'
            f'<text x="{lgx + 22}" y="{lgy}" font-family="{SANS}" font-size="15" fill="#FFFFFF">{esc(lang)}'
            f'<tspan font-family="{MONO}" font-size="13" fill="{SAND}"> {share * 100:.1f} %</tspan></text>'
        )
        x += w

    updated = datetime.now(TZ)
    stamp = f"mis à jour le {updated.day} {MONTHS[updated.month - 1]} {updated.year}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Statistiques GitHub de {USER} : {', '.join(f'{t[0].lower()} {t[1]}' for t in tiles)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{NAVY_0}"/><stop offset="1" stop-color="{NAVY_1}"/>
    </linearGradient>
    <linearGradient id="tide" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{ORANGE}" stop-opacity=".55"/><stop offset="1" stop-color="{ORANGE}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
    <clipPath id="reveal"><rect x="0" y="0" width="0" height="{H}"><animate attributeName="width" from="0" to="{W}" dur="1.6s" begin=".3s" fill="freeze"/></rect></clipPath>
  </defs>
  <style>
    .drop {{ animation: drop .8s cubic-bezier(.3,1.4,.5,1) both; }}
    @keyframes drop {{ from {{ transform: translateY(-40px); opacity: 0; }} to {{ transform: none; opacity: 1; }} }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <text x="30" y="44" font-family="{MONO}" font-size="14" font-weight="700" fill="{SAND}" letter-spacing="2">CAPITAINERIE · TABLEAU DE BORD DU PORT</text>
    <text x="{W - 30}" y="44" text-anchor="end" font-family="{MONO}" font-size="12" fill="{FOAM}" fill-opacity=".6">{stamp}</text>
    {tile_svg}
    <text x="40" y="216" font-family="{MONO}" font-size="12" font-weight="700" fill="{SAND}" letter-spacing="1">MARÉE DES CONTRIBUTIONS · PAR SEMAINE</text>
    <line x1="{cx0}" y1="{cy1}" x2="{cx1}" y2="{cy1}" stroke="{NAVY_3}" stroke-width="2"/>
    <g clip-path="url(#reveal)">
      <path d="{area}" fill="url(#tide)"/>
      <path d="{line}" fill="none" stroke="{ORANGE}" stroke-width="2.5" stroke-linejoin="round"/>
      <circle cx="{bx:.1f}" cy="{by:.1f}" r="5" fill="#FFFFFF"/>
      <text x="{min(max(bx, 120), W - 120):.1f}" y="{by - 12:.1f}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#FFFFFF">pic : {weeks[best]} contributions</text>
    </g>
    {months}
    <text x="40" y="404" font-family="{MONO}" font-size="12" font-weight="700" fill="{SAND}" letter-spacing="1">CARGAISON PAR LANGAGE · DÉPÔTS PUBLICS</text>
    {bar}
    {legend}
    <rect x="0" y="{H - 8}" width="{W}" height="8" fill="{NAVY_2}"/>
  </g>
</svg>
'''


# ---------------------------------------------------------------- activity
def link(repo):
    return f"[{repo}](https://github.com/{repo})"


def describe(e):
    """One French line for an event, or None to skip it."""
    p, repo = e.get("payload", {}), e["repo"]["name"]
    t = e["type"]
    if t == "PushEvent":
        return None  # pushes are grouped separately
    if t == "CreateEvent":
        kind = p.get("ref_type")
        if kind == "repository":
            return f"🆕 Création du dépôt {link(repo)}"
        if kind == "tag":
            return f"🏷️ Tag `{p.get('ref')}` sur {link(repo)}"
        return None
    if t == "PullRequestEvent":
        pr = p.get("pull_request", {})
        action = p.get("action")
        if action == "closed":
            action = "merged" if pr.get("merged") else "closed"
        verb = {"opened": "ouverte", "merged": "fusionnée", "closed": "fermée", "reopened": "rouverte"}.get(action)
        if not verb:
            return None
        title = f"#{pr.get('number', '')} {pr.get('title', '')}".strip()
        return f"🔀 PR {verb} sur {link(repo)} : [{esc(title)}]({pr.get('html_url', '')})"
    if t == "IssuesEvent":
        verb = {"opened": "ouverte", "closed": "fermée"}.get(p.get("action"))
        if not verb:
            return None
        issue = p.get("issue", {})
        return f"📌 Issue {verb} sur {link(repo)} : [#{issue.get('number', '')} {esc(issue.get('title', ''))}]({issue.get('html_url', '')})"
    if t == "ReleaseEvent" and p.get("action") == "published":
        rel = p.get("release", {})
        return f"🚀 Version [{esc(rel.get('tag_name', ''))}]({rel.get('html_url', '')}) publiée sur {link(repo)}"
    if t == "PublicEvent":
        return f"📢 {link(repo)} est maintenant public"
    if t == "ForkEvent":
        return f"🍴 Fork de {link(repo)}"
    if t == "WatchEvent":
        return f"⭐ Étoile ajoutée à {link(repo)}"
    return None


def activity_lines():
    events = try_api(f"users/{USER}/events/public?per_page=100", [])
    events += try_api(f"orgs/{ORG}/events?per_page=100", [])
    uniq = {e["id"]: e for e in events if e.get("public")}
    ordered = sorted(uniq.values(), key=lambda e: e["created_at"], reverse=True)

    entries = OrderedDict()  # key -> [when, text]; pushes on one repo the same day are merged
    for e in ordered:
        when = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")).astimezone(TZ)
        repo = e["repo"]["name"]
        if e["type"] == "PushEvent":
            key = ("push", repo, when.date())
            commits = e.get("payload", {}).get("size") or len(e.get("payload", {}).get("commits") or [])
            entry = entries.setdefault(key, [when, 0, 0])
            entry[1] += 1
            entry[2] += commits
        else:
            text = describe(e)
            if text:
                entries[(e["id"],)] = [when, text]
        if len(entries) >= MAX_ACTIVITY:
            break

    lines = []
    for key, entry in entries.items():
        when = entry[0]
        if key[0] == "push":
            pushes, commits = entry[1], entry[2]
            if commits:
                what = f"{commits} commit{'s' if commits > 1 else ''} poussé{'s' if commits > 1 else ''}"
            else:
                what = f"{pushes} push{'s' if pushes > 1 else ''}"
            text = f"⬆️ {what} sur {link(key[1])}"
        else:
            text = entry[1]
        lines.append(f"- `{when.day:02d} {MONTHS[when.month - 1]}` {text}")
    return lines or ["_Aucune activité publique récente._"]


def update_readme(lines):
    text = README.read_text()
    block = "<!--START_SECTION:activity-->\n" + "\n".join(lines) + "\n<!--END_SECTION:activity-->"
    new = re.sub(r"<!--START_SECTION:activity-->.*?<!--END_SECTION:activity-->", lambda _: block, text, flags=re.S)
    README.write_text(new)


def main():
    repos = public_repos()
    c = contributions()
    if c and repos:
        STATS_SVG.parent.mkdir(parents=True, exist_ok=True)
        STATS_SVG.write_text(render_stats(c, repos, languages(repos)))
    else:
        print("warning: stats unavailable, keeping the previous stats.svg", file=sys.stderr)
    update_readme(activity_lines())


if __name__ == "__main__":
    main()
