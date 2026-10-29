"""Gera assets/stats.svg com dados reais da API do GitHub.

Uso (precisa do GitHub CLI autenticado):  python scripts/gerar_estatisticas.py
"""
import collections
import datetime
import json
import pathlib
import subprocess

USER = "Ak4ai"
# Arquivos de terceiros embutidos que distorceriam a conta de linguagens.
IGNORAR = {("Stremio_For_Gamepad", "JavaScript")}
CORES = {
    "JavaScript": "#f1e05a", "Rust": "#dea584", "Python": "#3572a5", "TypeScript": "#3178c6",
    "HTML": "#e34c26", "CSS": "#8b5cf6", "Slint": "#2379f4", "TeX": "#3d6117",
    "C++": "#f34b7d", "Java": "#b07219", "C": "#9aa4b2", "Shell": "#89e051",
}


def gh(*args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    return out.stdout


query = (
    '{user(login:"%s"){followers{totalCount} contributionsCollection{totalCommitContributions '
    "totalPullRequestContributions contributionCalendar{totalContributions}} "
    "pullRequests(states:MERGED){totalCount}}}" % USER
)
u = json.loads(gh("api", "graphql", "-f", "query=" + query))["data"]["user"]
repos = json.loads(gh("api", "--paginate", f"users/{USER}/repos?per_page=100&type=owner"))
proprios = [r for r in repos if not r["fork"]]

langs = collections.Counter()
for r in proprios:
    for lang, size in json.loads(gh("api", f"repos/{USER}/{r['name']}/languages") or "{}").items():
        if (r["name"], lang) not in IGNORAR:
            langs[lang] += size
total = sum(langs.values()) or 1
top = langs.most_common(6)

stats = [
    (str(len(proprios)), "repositórios públicos"),
    (str(sum(r["stargazers_count"] for r in proprios)), "estrelas recebidas"),
    (f"{u['contributionsCollection']['contributionCalendar']['totalContributions']:,}".replace(",", "."), "contribuições em 12 meses"),
    (f"{u['contributionsCollection']['totalCommitContributions']:,}".replace(",", "."), "commits em 12 meses"),
    (str(u["pullRequests"]["totalCount"]), "pull requests aceitos"),
    (str(u["followers"]["totalCount"]), "seguidores"),
]

W, H = 1200, 330
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Estatísticas do GitHub">',
    '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1020"/><stop offset="1" stop-color="#1a1440"/></linearGradient>'
    '<linearGradient id="t" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5eead4"/><stop offset="1" stop-color="#a78bfa"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="17" fill="none" stroke="#ffffff" stroke-opacity="0.12"/>',
    '<text x="48" y="58" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="24" font-weight="700" fill="#ffffff">GitHub em números</text>',
    '<rect x="48" y="70" width="90" height="4" rx="2" fill="url(#t)"/>',
]
for i, (valor, rotulo) in enumerate(stats):
    x = 48 + (i % 3) * 190
    y = 140 + (i // 3) * 98
    parts.append(f'<text x="{x}" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="40" font-weight="700" fill="#5eead4">{valor}</text>')
    parts.append(f'<text x="{x}" y="{y+26}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="15" fill="#cbd5e1">{rotulo}</text>')

parts.append('<text x="700" y="58" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="24" font-weight="700" fill="#ffffff">Linguagens mais usadas</text>')
parts.append('<rect x="700" y="70" width="90" height="4" rx="2" fill="url(#t)"/>')
for i, (lang, size) in enumerate(top):
    pct = 100 * size / total
    y = 112 + i * 33
    cor = CORES.get(lang, "#94a3b8")
    parts.append(f'<text x="700" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="16" fill="#e2e8f0">{lang}</text>')
    parts.append(f'<rect x="830" y="{y-13}" width="260" height="12" rx="6" fill="#ffffff" fill-opacity="0.08"/>')
    parts.append(f'<rect x="830" y="{y-13}" width="{max(6, 260*pct/100/ (top[0][1]/total)):.1f}" height="12" rx="6" fill="{cor}"/>')
    parts.append(f'<text x="1100" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="15" fill="#cbd5e1">{pct:.1f}%</text>')

hoje = datetime.date.today().strftime("%d/%m/%Y")
parts.append(f'<text x="48" y="{H-22}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" fill="#94a3b8">Dados da API do GitHub, atualizados em {hoje}. Linguagens por bytes nos repositórios públicos próprios.</text>')
parts.append("</svg>")

destino = pathlib.Path(__file__).resolve().parent.parent / "assets" / "stats.svg"
destino.write_text("\n".join(parts), encoding="utf-8")
print("ok", destino, stats, top)
