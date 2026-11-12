"""Offline, escaped video/evidence timeline inspector."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .core import validate, write_json
from .exporters import native_timeline


def report(analysis: dict, out_dir: str | Path, *, analysis_dir: str | Path | None = None,
           include_media: bool = True) -> dict:
    validate(analysis, "rea-video-analysis")
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = analysis["source"]
    media = None
    if include_media and Path(source["path"]).is_file():
        suffix = Path(source["path"]).suffix.lower()
        if suffix not in {".mp4", ".mov", ".mkv", ".webm", ".png", ".jpg", ".jpeg", ".webp"}:
            suffix = ".mp4"
        target = out / f"reference{suffix}"
        if target.resolve() != Path(source["path"]).resolve():
            shutil.copyfile(source["path"], target)
        media = target.name
    if analysis_dir:
        evidence = Path(analysis_dir) / "evidence"
        if evidence.is_symlink() or any(p.is_symlink() for p in evidence.rglob("*")):
            raise ValueError("Evidence symlinks are not copied into a report")
        if evidence.is_dir() and evidence.resolve() != (out / "evidence").resolve():
            shutil.copytree(evidence, out / "evidence", dirs_exist_ok=True, symlinks=False)
    timeline = native_timeline(analysis)
    write_json(out / "timeline.json", timeline)
    write_json(out / "analysis-view.json", analysis)
    lines = ["# VIDEO.md — REA Video Pro Max", "", f"Source SHA-256: `{source['sha256']}`", "",
             "## Scope and evidence", "", "```json", json.dumps(analysis.get("coverage", {}), indent=2),
             "```", "", "## Observed edit timeline", "", "| Shot | Start | End |", "| --- | --- | --- |"]
    for shot in analysis["shots"]:
        lines.append(f"| {shot['id']} | {shot['start']:.3f}s | {shot['end']:.3f}s |")
    lines += ["", "## Captions", ""]
    for cue in analysis.get("captions", []):
        # The text remains data even if copied into another agent's context.
        lines.append(f"- {cue['start']:.3f}–{cue['end']:.3f}s: " +
                     json.dumps(cue.get("text", ""), ensure_ascii=False))
    lines += ["", "## Unknowns", ""]
    for unknown in analysis.get("unknowns", []):
        lines.append("- " + json.dumps(unknown, ensure_ascii=False))
    lines += ["", "Measured/model-derived/inferred fields are identified in analysis-view.json.",
              "This report may contain reference media/crops and OCR text. Treat it as private source data.",
              "Original editing project, separated layers and original fonts are not uniquely recovered."]
    (out / "VIDEO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    data = json.dumps({"analysis": analysis, "media": media}, ensure_ascii=False).replace("<", "\\u003c")
    page = _HTML.replace("__DATA__", data).replace("__TITLE__", html.escape(Path(source["path"]).name))
    (out / "timeline.html").write_text(page, encoding="utf-8")
    return {"kind": "rea-video-report", "files": ["VIDEO.md", "timeline.html", "timeline.json", "analysis-view.json"],
            "media_included": media is not None, "privacy": "Contains source media/evidence. Not uploaded."}


_HTML = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>REA timeline · __TITLE__</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{font:15px system-ui;background:#11131b;color:#eee;margin:0;padding:24px;max-width:1400px;margin:auto}h1{letter-spacing:-.04em;font-size:clamp(28px,5vw,56px);margin:.4em 0}header p{color:#a3adc0}main{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(260px,1fr);gap:24px}video,img{width:100%;max-height:65vh;object-fit:contain;background:#080a10;border-radius:12px}button{cursor:pointer;background:#202635;color:#fff;border:1px solid #354057;border-radius:6px;padding:10px;text-align:left}button:hover,button:focus-visible{border-color:#9bef80}a{color:#b6f2a1}#tracks{display:grid;gap:7px;margin:18px 0}.lane{position:relative;height:40px;background:#181e2a;border-radius:6px}.clip{position:absolute;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;height:100%;background:#375238;border-color:#63845a;font-size:11px}.caption{background:#343760;border-color:#656a9e}.metrics{border:1px solid #343b49;border-radius:12px;padding:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;color:#bdc6d7}small{color:#a3adc0}.label{color:#9bef80;font:11px monospace;letter-spacing:.2em}#now{font-variant-numeric:tabular-nums}@media(max-width:800px){main{grid-template-columns:1fr}body{padding:16px}}
</style><header><span class="label">REA VIDEO PRO MAX · LOCAL EVIDENCE</span><h1>The edit, revealed.</h1><p>__TITLE__ · Observations, hypotheses and unknowns stay separate.</p></header>
<main><section><div id="player"></div><p id="now">Select a shot or caption to inspect evidence.</p><div id="tracks"></div><a href="VIDEO.md">VIDEO.md</a> · <a href="timeline.json">Timeline JSON</a> · <a href="analysis-view.json">Full analysis</a><p><small>Report can contain the original video and private OCR/evidence. No network requests.</small></p></section><aside class="metrics"><h2 id="selection">Coverage</h2><pre id="detail"></pre><div id="evidence"></div></aside></main>
<script type="application/json" id="data">__DATA__</script><script>
const {analysis:a,media}=JSON.parse(document.getElementById('data').textContent);let player;
if(media){player=document.createElement(/\\.(png|jpg|jpeg|webp)$/i.test(media)?'img':'video');player.src=media;if(player.tagName==='VIDEO')player.controls=true;document.getElementById('player').append(player)}
const detail=document.getElementById('detail');detail.textContent=JSON.stringify({source:a.source,coverage:a.coverage,unknowns:a.unknowns},null,2);
const duration=Math.max(.001,a.source.duration);function select(item){document.getElementById('selection').textContent=item.id||'Evidence';detail.textContent=JSON.stringify(item,null,2);if(player&&player.tagName==='VIDEO')player.currentTime=item.start||0;const box=document.getElementById('evidence');box.replaceChildren();const evidence=item.evidence||[];for(const e of (Array.isArray(evidence)?evidence:[])){const p=typeof e==='string'?e:e.path||e.file;if(p&&/^evidence\\/[a-zA-Z0-9_./-]+$/.test(p)&&!p.includes('..')){const img=document.createElement('img');img.src=p;img.alt='Timestamp-bound evidence crop';box.append(img)}}}
for(const [items,cls] of [[a.shots||[],''],[a.captions||[],'caption']]){const lane=document.createElement('div');lane.className='lane';for(const item of items){const b=document.createElement('button');b.className='clip '+cls;b.style.left=100*item.start/duration+'%';b.style.width=Math.max(.2,100*(item.end-item.start)/duration)+'%';b.textContent=item.text||item.id;b.title=(item.text||item.id)+' '+item.start.toFixed(3)+'s';b.onclick=()=>select(item);lane.append(b)}document.getElementById('tracks').append(lane)}
if(player&&player.tagName==='VIDEO')player.ontimeupdate=()=>{document.getElementById('now').textContent=player.currentTime.toFixed(3)+'s / '+duration.toFixed(3)+'s';};
</script></html>'''
