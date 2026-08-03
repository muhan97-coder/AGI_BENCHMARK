#!/usr/bin/env python3
"""Build docs/index.html from cards/*.json + results/leaderboard.json.

Self-contained static dashboard (no external requests — GitHub Pages ready).
Re-run after adding/editing cards: python3 tools/build_dashboard.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
OUT = ROOT / "docs" / "index.html"
LEADERBOARD = ROOT / "results" / "leaderboard.json"


def load_cards():
    rows = []
    for p in sorted(CARDS.glob("gc-*.json")):
        if p.name.startswith("REJECTED"):
            continue
        c = json.loads(p.read_text())
        goal = str(c.get("goal", ""))
        rows.append({
            "id": c.get("id"),
            "title": c.get("title"),
            "category": c.get("category"),
            "horizon": c.get("horizon"),
            "budget_usd": c.get("budget_usd"),
            "grader": (c.get("success_criteria") or {}).get("grader"),
            "risk": c.get("contamination_risk", "low"),
            "goal": goal if len(goal) <= 420 else goal[:417] + "...",
            "file": f"cards/{p.name}",
        })
    return rows


def load_leaderboard():
    try:
        return json.loads(LEADERBOARD.read_text()).get("entries", [])
    except (OSError, json.JSONDecodeError):
        return []


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AGI_BENCHMARK — process-first agent benchmark</title>
<style>
:root {
  --paper:#F7F8F6; --ink:#23272B; --muted:#5E676D; --line:#DDE2DF;
  --loop:#0B7A63; --loop-soft:#0B7A6314; --ok:#2E7D4F; --warn:#B7791F;
  --crit:#B3383E; --chip:#ECEFEC; --row:#FFFFFF;
}
@media (prefers-color-scheme: dark) { :root {
  --paper:#15181A; --ink:#E6E9E7; --muted:#98A29D; --line:#2A3033;
  --loop:#2FBFA0; --loop-soft:#2FBFA01F; --ok:#5CB87F; --warn:#D9A441;
  --crit:#E06C72; --chip:#20262A; --row:#1A1F22;
}}
:root[data-theme="dark"] {
  --paper:#15181A; --ink:#E6E9E7; --muted:#98A29D; --line:#2A3033;
  --loop:#2FBFA0; --loop-soft:#2FBFA01F; --ok:#5CB87F; --warn:#D9A441;
  --crit:#E06C72; --chip:#20262A; --row:#1A1F22;
}
:root[data-theme="light"] {
  --paper:#F7F8F6; --ink:#23272B; --muted:#5E676D; --line:#DDE2DF;
  --loop:#0B7A63; --loop-soft:#0B7A6314; --ok:#2E7D4F; --warn:#B7791F;
  --crit:#B3383E; --chip:#ECEFEC; --row:#FFFFFF;
}
* { box-sizing:border-box; }
body {
  margin:0; background:var(--paper); color:var(--ink);
  font:15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif;
}
.mono { font-family:ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        font-variant-numeric:tabular-nums; }
.wrap { max-width:1100px; margin:0 auto; padding:0 20px 80px; }
header.site { border-bottom:1px solid var(--line); padding:34px 0 22px; }
.eyebrow { text-transform:uppercase; letter-spacing:.14em; font-size:11px;
           color:var(--loop); font-weight:600; }
h1 { margin:6px 0 8px; font-size:30px; letter-spacing:-.01em; text-wrap:balance; }
.sub { color:var(--muted); max-width:62ch; margin:0; }
.stats { display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }
.stat { background:var(--chip); border:1px solid var(--line); border-radius:6px;
        padding:6px 12px; font-size:13px; }
.stat b { font-weight:650; }
section { margin-top:44px; }
h2 { font-size:19px; margin:0 0 4px; }
.h2row { display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }
.h2row .note { color:var(--muted); font-size:13px; }
.principles { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
              gap:14px; margin-top:14px; }
.principle { border:1px solid var(--line); border-left:3px solid var(--loop);
             background:var(--row); padding:14px 16px; border-radius:4px; }
.principle h3 { margin:0 0 6px; font-size:14.5px; }
.principle p { margin:0; color:var(--muted); font-size:13.5px; }
.filters { display:flex; flex-wrap:wrap; gap:8px; margin:16px 0 12px; align-items:center; }
.filters input[type=search] {
  flex:1 1 220px; padding:7px 10px; border:1px solid var(--line); border-radius:6px;
  background:var(--row); color:var(--ink); font:inherit;
}
.fchip { border:1px solid var(--line); background:var(--chip); color:var(--ink);
         border-radius:999px; padding:5px 12px; font-size:12.5px; cursor:pointer; }
.fchip[aria-pressed="true"] { background:var(--loop); border-color:var(--loop);
                              color:#fff; }
.fchip:focus-visible, .rowbtn:focus-visible, a:focus-visible {
  outline:2px solid var(--loop); outline-offset:2px; }
.tablewrap { overflow-x:auto; border:1px solid var(--line); border-radius:6px; }
table { border-collapse:collapse; width:100%; min-width:760px; background:var(--row); }
th { text-align:left; font-size:11.5px; text-transform:uppercase; letter-spacing:.08em;
     color:var(--muted); padding:10px 12px; border-bottom:1px solid var(--line);
     position:sticky; top:0; background:var(--row); }
td { padding:9px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
tr:last-child td { border-bottom:none; }
.rowbtn { all:unset; cursor:pointer; color:var(--loop); font-weight:600; }
.pill { display:inline-block; border-radius:999px; padding:1px 9px; font-size:11.5px;
        border:1px solid var(--line); background:var(--chip); white-space:nowrap; }
.pill.h1d { color:var(--ok); } .pill.h1w { color:var(--warn); } .pill.h1m { color:var(--crit); }
.goalrow td { background:var(--loop-soft); color:var(--ink); font-size:13.5px; }
.count { color:var(--muted); font-size:13px; margin:8px 2px; }
.empty { border:1px dashed var(--line); border-radius:6px; padding:22px; text-align:center;
         color:var(--muted); background:var(--row); }
.empty b { color:var(--ink); }
pre { background:var(--chip); border:1px solid var(--line); border-radius:6px;
      padding:14px; overflow-x:auto; font-size:12.5px; line-height:1.5; }
code { font-family:ui-monospace, Menlo, Consolas, monospace; }
footer { margin-top:60px; border-top:1px solid var(--line); padding-top:16px;
         color:var(--muted); font-size:13px; }
a { color:var(--loop); }
@media (prefers-reduced-motion: no-preference) {
  .goalrow { animation:fade .15s ease-out; }
  @keyframes fade { from { opacity:0; } }
}
</style>
</head>
<body>
<div class="wrap">

<header class="site">
  <div class="eyebrow">AGI_BENCHMARK · v1.0-beta</div>
  <h1>Score the loop, not just the outcome</h1>
  <p class="sub">A benchmark for long-horizon agent systems that grades the
  <strong>process</strong> — plan &rarr; verify &rarr; execute &rarr; re-verify —
  from machine-readable logs, alongside a fail-closed, machine-graded outcome.
  No LLM judges. No self-reporting.</p>
  <div class="stats mono">__STATS__</div>
</header>

<section>
  <div class="h2row"><h2>Why process-first</h2>
    <span class="note">an agent can be right for the wrong reasons — and wrong for the right ones</span></div>
  <div class="principles">
    <div class="principle"><h3>Outcome is a separate axis</h3>
      <p>A failed goal with a sound loop (honest verification, justified refusal)
      scores higher on process than a lucky pass with silent failures.</p></div>
    <div class="principle"><h3>Machine-graded only</h3>
      <p>Every success criterion is a sealed command with a numeric threshold.
      Grading is fail-closed: unparseable, timed-out, or invalid specs never pass.</p></div>
    <div class="principle"><h3>Logs are the evidence</h3>
      <p>Process metrics (planning, verification, honesty, recovery, autonomy,
      economy) are computed from execution logs — never from the agent's claims.</p></div>
  </div>
</section>

<section>
  <div class="h2row"><h2>Goal cards</h2>
    <span class="note">each card = one sealed long-horizon goal with a machine grader</span></div>
  <div class="filters">
    <input id="q" type="search" placeholder="Search id, title, goal&hellip;" aria-label="Search cards">
    <span id="catchips"></span>
    <span id="horchips"></span>
  </div>
  <div class="count mono" id="count"></div>
  <div class="tablewrap">
    <table>
      <thead><tr>
        <th>ID</th><th>Title</th><th>Category</th><th>Horizon</th>
        <th>Grader</th><th title="contamination risk">Contam.</th>
        <th style="text-align:right">Budget</th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
  </div>
</section>

<section>
  <div class="h2row"><h2>Leaderboard</h2>
    <span class="note">outcome pass-rate and six process axes, per agent system</span></div>
  <div id="board"></div>
  <p class="note" style="color:var(--muted); font-size:13px">Submit by PR: add your
  entry to <code>results/leaderboard.json</code> together with the episode logs that
  back every number. A neutral episode-log contract (v1) is in progress — until it
  lands, submissions are verified by re-running the sealed graders.</p>
</section>

<section>
  <h2>Run a card</h2>
<pre><code># validate the spec shape (no execution, $0)
python3 tools/goal_grader.py --dry-run cards/gc-300_swebench_single_django.json

# run the sealed grader from the repo root (workspace = cards/)
python3 tools/goal_grader.py cards/gc-300_swebench_single_django.json cards</code></pre>
</section>

<footer>
  AGI_BENCHMARK · goal cards are preregistered drafts (v0) — sealed sets are tagged.
  · <a href="https://github.com/muhan97-coder/AGI_BENCHMARK">source</a>
</footer>
</div>

<script>
const CARDS = __CARDS__;
const BOARD = __BOARD__;
const cats = [...new Set(CARDS.map(c => c.category))].sort();
const hors = ["1d", "1w", "1m"];
const state = { q: "", cat: null, hor: null, open: null };

const chips = (items, key, host) => {
  const el = document.getElementById(host);
  items.forEach(v => {
    const b = document.createElement("button");
    b.className = "fchip"; b.textContent = v;
    b.setAttribute("aria-pressed", "false");
    b.onclick = () => {
      state[key] = state[key] === v ? null : v;
      host === "catchips" ? null : null;
      document.querySelectorAll(`#${host} .fchip`).forEach(x =>
        x.setAttribute("aria-pressed", String(x.textContent === state[key])));
      render();
    };
    el.appendChild(b);
  });
};
chips(cats, "cat", "catchips");
chips(hors, "hor", "horchips");
document.getElementById("q").addEventListener("input", e => {
  state.q = e.target.value.toLowerCase(); render();
});

const esc = s => String(s ?? "").replace(/[&<>"]/g,
  m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));

const RISK = {
  low: ["low", ""],
  public_gold_exists: ["gold public", "color:var(--warn)"],
  derivable_from_assets: ["answers in repo", "color:var(--crit)"],
  answers_sealed: ["answers sealed", "color:var(--loop)"],
};
const riskPill = r => {
  const [label, style] = RISK[r] || [r, ""];
  return `<span class="pill" style="${style}" title="${esc(r)}">${esc(label)}</span>`;
};

function render() {
  const rows = document.getElementById("rows");
  rows.textContent = "";
  const hit = CARDS.filter(c =>
    (!state.cat || c.category === state.cat) &&
    (!state.hor || c.horizon === state.hor) &&
    (!state.q || (c.id + " " + c.title + " " + c.goal).toLowerCase().includes(state.q)));
  const range = hit.length
    ? ` · budget range $${Math.min(...hit.map(c => c.budget_usd || 0))}` +
      `–$${Math.max(...hit.map(c => c.budget_usd || 0))}`
    : "";
  document.getElementById("count").textContent =
    `${hit.length} / ${CARDS.length} cards${range}`;
  hit.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td class="mono"><button class="rowbtn" aria-expanded="${state.open===c.id}">${esc(c.id)}</button></td>` +
      `<td>${esc(c.title)}</td>` +
      `<td><span class="pill">${esc(c.category)}</span></td>` +
      `<td><span class="pill h${esc(c.horizon)}">${esc(c.horizon)}</span></td>` +
      `<td class="mono">${esc(c.grader)}</td>` +
      `<td>${riskPill(c.risk)}</td>` +
      `<td class="mono" style="text-align:right">$${esc(c.budget_usd)}</td>`;
    tr.querySelector("button").onclick = () => {
      state.open = state.open === c.id ? null : c.id; render();
    };
    rows.appendChild(tr);
    if (state.open === c.id) {
      const g = document.createElement("tr");
      g.className = "goalrow";
      g.innerHTML = `<td colspan="7"><strong class="mono">${esc(c.id)}</strong> — ` +
        `${esc(c.goal)} <span class="mono" style="color:var(--muted)">(${esc(c.file)})</span></td>`;
      rows.appendChild(g);
    }
  });
  if (!hit.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="7" style="color:var(--muted)">No cards match the current filter.</td>`;
    rows.appendChild(tr);
  }
}

function renderBoard() {
  const host = document.getElementById("board");
  if (!BOARD.length) {
    host.innerHTML = `<div class="empty"><b>No submissions yet.</b><br>
      The first baseline — <b>agent-one</b>, a self-improving agent loop on a
      budget worker model — is currently being measured (harness-run tier) and
      will be posted here.</div>`;
    return;
  }
  const axes = ["planning","verification","honesty","recovery","autonomy","economy"];
  // Worker and "bound by" sit next to the pass-rate on purpose. Spend rate is a
  // property of the worker (list prices span >100x across tiers), and a run whose
  // episodes were ended by the clock measures the runner rather than the agent.
  // A pass-rate shown without those two invites both misreadings.
  const AGENT_BOUND = ["green","budget"];
  const boundBy = e => {
    const b = (e.limits||{}).bound_by;
    if (!b) return ["—", "no limits block"];
    const tot = Object.values(b).reduce((x,y) => x + (Number(y)||0), 0);
    if (!tot) return ["—", "0 episodes labelled"];   // not 0% — a different fact
    const own = AGENT_BOUND.reduce((x,k) => x + (Number(b[k])||0), 0);
    const pct = Math.round(100*own/tot);
    return [`${pct}%`, Object.entries(b).filter(([,v]) => v)
      .map(([k,v]) => `${k} ${v}`).join(" · ")];
  };
  let h = `<div class="tablewrap"><table><thead><tr><th>Agent</th><th>Worker</th>` +
    `<th>Cards</th><th>Outcome pass</th><th title="share of episodes ended by ` +
    `success or by spending their budget, rather than by the runner's clock or ` +
    `turn cap">Agent-bound</th>` + axes.map(a => `<th>${a}</th>`).join("") +
    `<th style="text-align:right">USD</th></tr></thead><tbody>`;
  BOARD.forEach(e => {
    const [share, detail] = boundBy(e);
    h += `<tr><td>${esc(e.agent)}</td>` +
      `<td class="mono">${esc((e.models||{}).worker ?? "—")}</td>` +
      `<td class="mono">${esc(e.cards_attempted)}</td>` +
      `<td class="mono">${esc(e.outcome_pass)}</td>` +
      `<td class="mono" title="${esc(detail)}">${esc(share)}</td>` +
      axes.map(a => `<td class="mono">${esc((e.process||{})[a] ?? "—")}</td>`).join("") +
      `<td class="mono" style="text-align:right">$${esc(e.usd)}</td></tr>`;
  });
  host.innerHTML = h + "</tbody></table></div>";
}
render(); renderBoard();
</script>
</body>
</html>
"""


def main():
    cards = load_cards()
    stats = [
        f"<span class='stat'><b>{len(cards)}</b> goal cards</span>",
        f"<span class='stat'><b>{len({c['category'] for c in cards})}</b> categories</span>",
        "<span class='stat'><b>2-layer</b> scoring (outcome + process)</span>",
        "<span class='stat'><b>0</b> LLM judges</span>",
    ]
    out = (TEMPLATE
           .replace("__STATS__", "".join(stats))
           .replace("__CARDS__", json.dumps(cards, ensure_ascii=False))
           .replace("__BOARD__", json.dumps(load_leaderboard(), ensure_ascii=False)))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out)
    print(f"{OUT} written — {len(cards)} cards embedded, "
          f"{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
