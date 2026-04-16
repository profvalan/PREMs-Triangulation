"""
Generate interactive D3.js chord diagram as a standalone HTML file.
Hover/click to reveal live linking between Avlijas themes and co-occurrence
clusters, with keyword-level detail and three view modes.
"""
import pandas as pd, json, html

df = pd.read_csv("/home/claude/data_4themes.csv")

# --- keyword → cluster lookup (edit to match your Biblioshiny output) ---
k2c = {
    "quality of care":"Healthcare Quality","quality of health care":"Healthcare Quality",
    "quality improvement":"Healthcare Quality","quality in health care":"Healthcare Quality",
    "patient safety":"Healthcare Quality","value-based healthcare":"Healthcare Quality",
    "HCAHPS":"Healthcare Quality","patient-centered care":"Healthcare Quality",
    "person-centred care":"Healthcare Quality",
    "health services research":"Adult Healthcare Services","general practice":"Adult Healthcare Services",
    "primary care":"Adult Healthcare Services","emergency department":"Adult Healthcare Services",
    "access":"Adult Healthcare Services","telehealth":"Adult Healthcare Services",
    "telemedicine":"Adult Healthcare Services","covid-19":"Adult Healthcare Services",
    "diabetes":"Risk Factors","cancer":"Risk Factors","breast cancer":"Risk Factors",
    "rehabilitation":"Risk Factors",
    "mental health":"Psychotherapy","psychiatry":"Psychotherapy",
    "schizophrenia":"Psychotherapy","self-management":"Psychotherapy",
    "patient-reported outcome":"Measurement Validation","measurement":"Measurement Validation",
    "psychometrics":"Measurement Validation","questionnaire":"Measurement Validation",
    "patient reported experience measure":"Measurement Validation",
    "patient experience":"Measurement Validation","patient satisfaction":"Measurement Validation",
    "satisfaction":"Measurement Validation","patient engagement":"Measurement Validation",
    "patient":"Healthcare Disparities","communication":"Healthcare Disparities",
    "quality of life":"Healthcare Disparities",
    "children":"Paediatric Cancer Decision-Making","oncology":"Paediatric Cancer Decision-Making",
}
df["Cluster"] = df["Target"].map(k2c)

themes = ["External & Internal Hospital Processes","Patient Dependent Features",
          "Hospital Staff Interactions","Hospital Staff-Patient Interactions"]
clusters = ["Healthcare Quality","Adult Healthcare Services","Risk Factors",
            "Psychotherapy","Measurement Validation","Healthcare Disparities",
            "Paediatric Cancer Decision-Making"]

# Matrix + keyword list per cell
matrix = [[0]*len(clusters) for _ in themes]
keywords = {}
for _, r in df.iterrows():
    i, j = themes.index(r["Source"]), clusters.index(r["Cluster"])
    matrix[i][j] += 1
    keywords.setdefault(f"{i}-{j}", []).append(r["Target"])

theme_colors   = ["#E8833A","#3C3754","#7A6B8C","#B38AA8"]
cluster_colors = ["#8E4A9E","#4A9E6B","#D4B948","#4A6FA5",
                  "#C5422B","#7A5230","#D88BA8"]

payload = {
    "themes": themes, "clusters": clusters,
    "matrix": matrix, "keywords": keywords,
    "themeColors": theme_colors, "clusterColors": cluster_colors,
}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Figure 7 — Triangulation (Interactive)</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  :root{
    --bg:#fafaf7; --ink:#1a1a1a; --muted:#6b6b6b; --rule:#e0ddd5;
    --conv:#2d7a3d; --comp:#c47d0e; --sil:#a33030;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
       background:var(--bg);color:var(--ink);line-height:1.45}
  header{padding:24px 32px 8px;border-bottom:1px solid var(--rule)}
  h1{font-size:20px;margin:0 0 4px;font-weight:700;letter-spacing:-.01em}
  .sub{color:var(--muted);font-size:13px;margin:0}
  .layout{display:grid;grid-template-columns:1fr 320px;gap:24px;padding:20px 32px 32px}
  #chart{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:12px;min-height:720px;position:relative}
  .controls{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
  .mode{padding:6px 14px;border:1px solid var(--rule);background:#fff;border-radius:20px;
        font-size:12px;cursor:pointer;color:var(--muted);font-weight:500;transition:all .15s}
  .mode:hover{background:#f5f2ec}
  .mode.active{background:var(--ink);color:#fff;border-color:var(--ink)}
  .side{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:18px;
        height:fit-content;position:sticky;top:20px;max-height:calc(100vh - 40px);overflow-y:auto}
  .side h3{font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
  .side .target{font-size:15px;font-weight:600;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
  .connection{padding:10px 0;border-bottom:1px dashed var(--rule)}
  .connection:last-child{border-bottom:none}
  .conn-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
  .conn-name{font-weight:600;font-size:13px}
  .conn-count{font-size:11px;background:#f0ede5;padding:2px 8px;border-radius:10px;color:var(--muted)}
  .badge{display:inline-block;font-size:10px;padding:1px 6px;border-radius:3px;
         font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-left:6px}
  .conv{background:#d8ebde;color:var(--conv)}
  .comp{background:#f5e5c8;color:var(--comp)}
  .sil{background:#efd5d5;color:var(--sil)}
  .kws{font-size:12px;color:var(--muted);line-height:1.6}
  .kw{display:inline-block;background:#f5f2ec;padding:2px 7px;margin:2px;border-radius:3px;font-size:11px}
  .empty{color:var(--muted);font-size:13px;font-style:italic;padding:24px 0;text-align:center}
  .legend{position:absolute;bottom:16px;left:16px;background:rgba(255,255,255,.95);
          padding:10px 14px;border:1px solid var(--rule);border-radius:6px;font-size:11px}
  .legend .row{display:flex;align-items:center;gap:6px;margin:2px 0}
  .legend .dot{width:10px;height:10px;border-radius:50%}
  svg{display:block;margin:0 auto}
  .group text{font-size:10px;font-weight:600;fill:var(--ink)}
  .group.muted{opacity:.15}
  .ribbon{transition:opacity .2s}
  .ribbon.muted{opacity:.05}
  .ribbon.highlight{opacity:.95}
  .label-theme{font-weight:700}
  .footer-note{font-size:11px;color:var(--muted);padding:0 32px 24px}
</style>
</head>
<body>
<header>
  <h1>Figure 7 — Triangulation: Avlijas Themes × Co-occurrence Clusters</h1>
  <p class="sub">Hover or click any arc to see connections · Click ribbons for keyword detail</p>
</header>

<div class="layout">
  <div id="chart">
    <div class="controls">
      <button class="mode active" data-mode="all">All connections</button>
      <button class="mode" data-mode="conv">Convergence (strong)</button>
      <button class="mode" data-mode="comp">Complementarity (weak)</button>
      <button class="mode" data-mode="sil">Silence (absent)</button>
    </div>
    <svg id="svg"></svg>
    <div class="legend">
      <div class="row"><span class="badge conv">Conv</span>≥ 3 shared keywords</div>
      <div class="row"><span class="badge comp">Comp</span>1–2 shared keywords</div>
      <div class="row"><span class="badge sil">Silence</span>0 shared — opportunity</div>
    </div>
  </div>

  <div class="side" id="panel">
    <h3>Detail</h3>
    <div class="empty">Hover or click any arc<br>or ribbon to see detail</div>
  </div>
</div>

<p class="footer-note">Outer arc width = total shared keywords for that entity. Ribbon width = keywords shared between a theme and a cluster. Themes (top): Avlijas et al. (2023) 20-attribute concept analysis grouped into 4 themes. Clusters (bottom): VOSviewer co-occurrence network, K=7.</p>

<script>
const DATA = __PAYLOAD__;
const {themes, clusters, matrix, keywords, themeColors, clusterColors} = DATA;
const N_T = themes.length, N_C = clusters.length, N = N_T + N_C;
const labels = [...themes, ...clusters];
const colors = [...themeColors, ...clusterColors];
const isTheme = i => i < N_T;

// Build symmetric matrix for d3.chord
const full = Array.from({length:N}, () => new Array(N).fill(0));
for (let i=0;i<N_T;i++)
  for (let j=0;j<N_C;j++){
    full[i][N_T+j] = matrix[i][j];
    full[N_T+j][i] = matrix[i][j];
  }

const W = 1020, H = 860, outer = 260, inner = 244;
const svg = d3.select("#svg")
              .attr("viewBox", [-W/2, -H/2 - 20, W, H + 20])
              .attr("width", "100%").attr("height", H + 20).style("max-width", W + "px");
const root = svg.append("g");

const chord = d3.chord().padAngle(0.04).sortSubgroups(d3.descending).sortChords(d3.descending);
const arc = d3.arc().innerRadius(inner).outerRadius(outer);
const ribbon = d3.ribbon().radius(inner - 2);

const chords = chord(full);

// Groups (arcs)
const groups = root.append("g").selectAll("g").data(chords.groups).join("g")
  .attr("class", d => "group g" + d.index);

groups.append("path")
  .attr("d", arc)
  .attr("fill", d => colors[d.index])
  .attr("stroke", "#fff")
  .attr("stroke-width", 1)
  .style("cursor","pointer")
  .on("mouseenter", (_,d) => highlight(d.index))
  .on("mouseleave", () => resetHighlight())
  .on("click", (_,d) => showEntity(d.index));

groups.append("text")
  .each(d => d.angle = (d.startAngle + d.endAngle)/2)
  .attr("dy", ".35em")
  .attr("class", d => isTheme(d.index) ? "label-theme" : "")
  .attr("transform", d => `
    rotate(${d.angle*180/Math.PI - 90})
    translate(${outer + 10})
    ${d.angle > Math.PI ? "rotate(180)" : ""}
  `)
  .attr("text-anchor", d => d.angle > Math.PI ? "end" : null)
  .text(d => labels[d.index])
  .style("pointer-events","none");

// Ribbons
const ribbons = root.append("g").attr("fill-opacity", 0.7).selectAll("path")
  .data(chords).join("path")
  .attr("class", d => `ribbon r-${d.source.index} r-${d.target.index}`)
  .attr("d", ribbon)
  .attr("fill", d => {
    const themeIdx = isTheme(d.source.index) ? d.source.index : d.target.index;
    return colors[themeIdx];
  })
  .attr("stroke", "#fff").attr("stroke-width", 0.5)
  .style("cursor","pointer")
  .on("mouseenter", (_,d) => {
    const ti = isTheme(d.source.index) ? d.source.index : d.target.index;
    const ci = isTheme(d.source.index) ? d.target.index - N_T : d.source.index - N_T;
    showRibbon(ti, ci);
  })
  .on("mouseleave", () => resetHighlight())
  .on("click", (_,d) => {
    const ti = isTheme(d.source.index) ? d.source.index : d.target.index;
    const ci = isTheme(d.source.index) ? d.target.index - N_T : d.source.index - N_T;
    showRibbon(ti, ci, true);
  });

// Interaction helpers
function highlight(idx){
  root.selectAll(".group").classed("muted", d => d.index !== idx);
  root.selectAll(".ribbon").classed("muted", true).classed("highlight", false);
  root.selectAll(`.ribbon.r-${idx}`).classed("muted", false).classed("highlight", true);
  showEntity(idx);
}
function resetHighlight(){
  root.selectAll(".group").classed("muted", false);
  root.selectAll(".ribbon").classed("muted", false).classed("highlight", false);
}
function classify(n){ return n >= 3 ? "conv" : n >= 1 ? "comp" : "sil"; }
function label(cls){ return {conv:"Convergence", comp:"Complementarity", sil:"Silence"}[cls]; }

function showEntity(idx){
  const panel = document.getElementById("panel");
  const name = labels[idx];
  const theme = isTheme(idx);
  const connections = [];
  if (theme){
    matrix[idx].forEach((n, ci) => connections.push({name: clusters[ci], n, key: `${idx}-${ci}`}));
  } else {
    const tIdx = idx - N_T;
    matrix.forEach((row, ti) => connections.push({name: themes[ti], n: row[tIdx], key: `${ti}-${tIdx}`}));
  }
  connections.sort((a,b) => b.n - a.n);
  let html = `<h3>${theme ? "Avlijas Theme" : "Co-occurrence Cluster"}</h3>`;
  html += `<div class="target">${name}</div>`;
  html += connections.map(c => {
    const cls = classify(c.n);
    const kws = (keywords[c.key]||[]).map(k => `<span class="kw">${k}</span>`).join("");
    return `<div class="connection">
      <div class="conn-head">
        <span class="conn-name">${c.name}<span class="badge ${cls}">${label(cls)}</span></span>
        <span class="conn-count">${c.n} shared</span>
      </div>
      <div class="kws">${kws || '<em>No shared keywords — frontier opportunity</em>'}</div>
    </div>`;
  }).join("");
  panel.innerHTML = html;
}

function showRibbon(ti, ci, lock){
  // Highlight just this ribbon pair
  root.selectAll(".group").classed("muted", d => d.index !== ti && d.index !== (ci + N_T));
  root.selectAll(".ribbon").classed("muted", true).classed("highlight", false);
  root.selectAll(`.ribbon.r-${ti}.r-${ci+N_T}`).classed("muted", false).classed("highlight", true);
  const n = matrix[ti][ci];
  const cls = classify(n);
  const kws = (keywords[`${ti}-${ci}`]||[]).map(k => `<span class="kw">${k}</span>`).join("");
  document.getElementById("panel").innerHTML = `
    <h3>Connection</h3>
    <div class="target">${themes[ti]} ↔ ${clusters[ci]}<span class="badge ${cls}">${label(cls)}</span></div>
    <div class="connection">
      <div class="conn-head"><span class="conn-name">Shared keywords</span><span class="conn-count">${n}</span></div>
      <div class="kws">${kws || '<em>No shared keywords — silence / frontier opportunity for future PREMs research</em>'}</div>
    </div>`;
}

// Mode buttons
document.querySelectorAll(".mode").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".mode").forEach(x => x.classList.remove("active"));
  b.classList.add("active");
  const m = b.dataset.mode;
  root.selectAll(".ribbon").classed("muted", false).classed("highlight", false);
  if (m === "all") return;
  root.selectAll(".ribbon").each(function(d){
    const ti = isTheme(d.source.index) ? d.source.index : d.target.index;
    const ci = (isTheme(d.source.index) ? d.target.index : d.source.index) - N_T;
    const n = matrix[ti][ci];
    const cls = classify(n);
    d3.select(this).classed("muted", cls !== m);
  });
  // For "sil" mode, also show silence cells as dashed overlays
  if (m === "sil"){
    // draw dashed silence arcs between empty cells
    root.selectAll(".silence-line").remove();
    for (let ti=0;ti<N_T;ti++) for (let ci=0;ci<N_C;ci++){
      if (matrix[ti][ci] === 0){
        const g1 = chords.groups[ti], g2 = chords.groups[ci + N_T];
        const a1 = (g1.startAngle + g1.endAngle)/2 - Math.PI/2;
        const a2 = (g2.startAngle + g2.endAngle)/2 - Math.PI/2;
        const x1 = Math.cos(a1)*inner, y1 = Math.sin(a1)*inner;
        const x2 = Math.cos(a2)*inner, y2 = Math.sin(a2)*inner;
        root.append("path").attr("class","silence-line")
          .attr("d", `M${x1},${y1} Q0,0 ${x2},${y2}`)
          .attr("stroke","#a33030").attr("stroke-width", 1).attr("stroke-dasharray","3,4")
          .attr("fill","none").attr("opacity", 0.5);
      }
    }
  } else {
    root.selectAll(".silence-line").remove();
  }
}));
</script>
</body></html>"""

HTML = HTML.replace("__PAYLOAD__", json.dumps(payload))
with open("/home/claude/figure7_interactive.html","w") as f:
    f.write(HTML)
print("✓ Interactive HTML written → figure7_interactive.html")
print(f"   Size: {len(HTML):,} bytes")
