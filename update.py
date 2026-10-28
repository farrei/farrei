"""Atualiza as metricas dos SVGs com dados reais da API do GitHub."""
import datetime, json, os, re, urllib.request

USER = "farrei"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def api(path):
    req = urllib.request.Request("https://api.github.com" + path)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as r:
        return json.load(r), r.headers

def owned_repos():
    repos, page = [], 1
    while True:
        data, _ = api(f"/users/{USER}/repos?type=owner&per_page=100&page={page}")
        repos += data
        if len(data) < 100:
            return repos
        page += 1

def commit_count(repo):
    # per_page=1 + header Link: o numero da ultima pagina e o total de commits
    try:
        data, h = api(f"/repos/{USER}/{repo}/commits?author={USER}&per_page=1")
    except urllib.error.HTTPError:  # repo vazio
        return 0
    m = re.search(r'page=(\d+)>; rel="last"', h.get("Link", ""))
    return int(m.group(1)) if m else len(data)

def main():
    repos = [r for r in owned_repos() if not r["fork"]]
    langs = set()
    for r in repos:
        data, _ = api(f"/repos/{USER}/{r['name']}/languages")
        langs.update(data)
    values = {
        "repos": len(repos),
        "commits": sum(commit_count(r["name"]) for r in repos),
        "tests": 12,
        "langs": len(langs),
        "updated": datetime.date.today().strftime("%d/%m/%Y"),
    }
    for f in ("dark_mode.svg", "light_mode.svg"):
        svg = open(f, encoding="utf-8").read()
        for k, v in values.items():
            svg = re.sub(rf'(<tspan id="{k}">)[^<]*(</tspan>)', rf"\g<1>{v}\g<2>", svg)
        open(f, "w", encoding="utf-8").write(svg)
    print(values)

if __name__ == "__main__":
    main()
