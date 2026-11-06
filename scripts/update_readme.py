"""Rewrite the NOTES and UPDATED blocks of README.md from the field-notes repo.

Usage: python scripts/update_readme.py <path-to-field-notes-checkout> [README.md]

A note is any .md file in field-notes outside _meta/ and other than README.md.
Its title is the first '# ' heading; its date is the commit that first added it.
"""
import datetime as dt
import pathlib
import re
import subprocess
import sys

NOTES_REPO_URL = "https://github.com/Esther-chepunton/field-notes/blob/main/"
LIMIT = 5


def first_added(repo: pathlib.Path, rel: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), "log", "--diff-filter=A", "--follow",
         "--format=%cs", "--", rel],
        capture_output=True, text=True, check=False,
    ).stdout.split()
    return out[-1] if out else dt.date.today().isoformat()


def collect(repo: pathlib.Path):
    notes = []
    for path in repo.rglob("*.md"):
        rel = path.relative_to(repo).as_posix()
        if rel.lower() == "readme.md" or rel.startswith(("_meta/", ".")):
            continue
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else path.stem.replace("-", " ")
        topic = rel.split("/")[0] if "/" in rel else "misc"
        notes.append((first_added(repo, rel), title, topic, rel))
    notes.sort(key=lambda n: (n[0], n[3]), reverse=True)
    return notes[:LIMIT]


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:START -->)(.*?)(<!-- {name}:END -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"marker {name} not found in README")
    return pattern.sub(lambda m: m.group(1) + body + m.group(3), text)


def main():
    repo = pathlib.Path(sys.argv[1])
    readme = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "README.md")
    notes = collect(repo)
    if notes:
        lines = [f"- `{d}` **[{t}]({NOTES_REPO_URL}{r})** · <sub>{topic}</sub>"
                 for d, t, topic, r in notes]
        body = "\n" + "\n".join(lines) + "\n"
    else:
        body = "\n- *Notes will appear here automatically.*\n"
    text = readme.read_text(encoding="utf-8")
    text = replace_block(text, "NOTES", body)
    stamp = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).strftime("%d %b %Y, %H:%M EAT")
    text = replace_block(text, "UPDATED", f"Last synced: {stamp}")
    readme.write_text(text, encoding="utf-8")
    print(f"wrote {len(notes)} notes")


if __name__ == "__main__":
    main()
