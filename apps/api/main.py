"""
apps/api/main.py
===================
FastAPI web server for the Spanish EIT Automated Scorer.

Endpoints:
  GET  /health        — liveness check + rubric info
  POST /score         — score a JSON payload of items + responses
  POST /score_file    — same, but from a JSON file upload
  GET  /              — minimal browser UI (paste/upload JSON)
  GET  /ui/score      — HTML result view
  GET  /rubric        — return current rubric config as JSON

Run:
  eit-api --host 0.0.0.0 --port 8000
  eit-api --rubric path/to/custom_rubric.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel
    import uvicorn
    _FASTAPI = True
except ImportError:
    _FASTAPI = False

from eit_scorer.core.rubric    import load_rubric, RubricConfig
from eit_scorer.core.scoring   import score_response
from eit_scorer.data.models    import EITItem, EITResponse


# ─────────────────────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────────

class ItemPayload(BaseModel):
    item_id:    str
    reference:  str
    max_points: int = 4
    level:      Optional[str] = None
    domain:     Optional[str] = None

class ResponsePayload(BaseModel):
    participant_id: str
    item_id:        str
    response_text:  str
    human_rater_a:  Optional[float] = None
    human_rater_b:  Optional[float] = None
    meta:           dict[str, Any]   = {}

class ScoreRequest(BaseModel):
    items:     list[ItemPayload]
    responses: list[ResponsePayload]


# ─────────────────────────────────────────────────────────────
# SCORING HELPER
# ─────────────────────────────────────────────────────────────

def _run_scoring(items_list, responses_list, rubric: RubricConfig) -> list[dict]:
    items_map = {it.item_id: EITItem(**it.model_dump()) for it in items_list}
    results   = []
    for rp in responses_list:
        item = items_map.get(rp.item_id)
        if item is None:
            results.append({
                "error": f"item_id '{rp.item_id}' not found",
                "participant_id": rp.participant_id,
                "item_id": rp.item_id,
            })
            continue
        resp = EITResponse(
            participant_id=rp.participant_id,
            item_id=rp.item_id,
            response_text=rp.response_text,
            human_rater_a=rp.human_rater_a,
            human_rater_b=rp.human_rater_b,
            meta=rp.meta,
        )
        ss = score_response(item, resp, rubric)
        results.append({
            "participant_id":   ss.participant_id,
            "item_id":          ss.item_id,
            "response_text":    ss.response_text,
            "score":            ss.score,
            "max_points":       ss.max_points,
            "human_rater_a":    ss.human_rater_a,
            "human_rater_b":    ss.human_rater_b,
            "adjudicated":      ss.adjudicated,
            "fingerprint":      ss.trace.deterministic_fingerprint,
            "rule_fired":       ss.trace.applied_rule_ids[0] if ss.trace.applied_rule_ids else "",
            "total_edits":      ss.trace.total_edits,
            "content_subs":     ss.trace.content_subs,
            "overlap_ratio":    round(ss.trace.overlap_ratio, 4),
            "audit_trail":      ss.trace.audit(),
            "error_counts":     ss.trace.error_counts,
        })
    return results


# ─────────────────────────────────────────────────────────────
# HTML UI
# ─────────────────────────────────────────────────────────────

_HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EIT Scorer API</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Courier New',monospace;background:#0e0e10;color:#d4d4d4;padding:2rem}
  h1{color:#7dd3a0;font-size:1.5rem;margin-bottom:.5rem}
  .sub{color:#888;font-size:.85rem;margin-bottom:2rem}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
  label{display:block;color:#7dd3a0;font-size:.75rem;letter-spacing:.1em;
        text-transform:uppercase;margin-bottom:.4rem}
  textarea{width:100%;height:320px;background:#1a1a1e;color:#d4d4d4;
           border:1px solid #333;border-radius:6px;padding:.8rem;
           font-family:inherit;font-size:.82rem;resize:vertical}
  textarea:focus{outline:none;border-color:#7dd3a0}
  .btn{background:#7dd3a0;color:#0e0e10;border:none;padding:.7rem 1.6rem;
       border-radius:6px;font-family:inherit;font-weight:bold;font-size:.88rem;
       cursor:pointer;margin-top:.8rem;margin-right:.6rem}
  .btn:hover{background:#6bc490}
  .btn-sec{background:#1a1a1e;color:#7dd3a0;border:1px solid #7dd3a0}
  .btn-sec:hover{background:#7dd3a020}
  pre{background:#1a1a1e;border:1px solid #333;border-radius:6px;
      padding:1rem;font-size:.78rem;overflow:auto;max-height:400px;
      margin-top:1rem;white-space:pre-wrap;color:#b8c4bb}
  .badge{display:inline-block;background:#7dd3a020;color:#7dd3a0;
         border:1px solid #7dd3a0;border-radius:4px;
         padding:.1rem .5rem;font-size:.7rem;margin-left:.5rem}
  input[type=file]{display:none}
  .status{font-size:.78rem;color:#888;margin-top:.4rem}
</style>
</head>
<body>
<h1>Spanish EIT Automated Scorer <span class="badge">v1.0</span></h1>
<p class="sub">Deterministic · Rule-based · Reproducible &nbsp;|&nbsp;
   <a href="/docs" style="color:#7dd3a0">API Docs</a> &nbsp;|&nbsp;
   <a href="/health" style="color:#7dd3a0">Health</a> &nbsp;|&nbsp;
   <a href="/rubric" style="color:#7dd3a0">Rubric</a>
</p>

<div class="grid">
  <div>
    <label>JSON Payload (items + responses)</label>
    <textarea id="payload">{
  "items": [
    {"item_id": "s01", "reference": "El niño come una manzana roja", "max_points": 4}
  ],
  "responses": [
    {"participant_id": "P001", "item_id": "s01", "response_text": "El niño come manzana"},
    {"participant_id": "P002", "item_id": "s01", "response_text": "El niño come una manzana roja"},
    {"participant_id": "P003", "item_id": "s01", "response_text": ""},
    {"participant_id": "P004", "item_id": "s01", "response_text": "La niña comer manzanas"}
  ]
}</textarea>
    <button class="btn" onclick="scoreJSON()">Score JSON</button>
    <button class="btn btn-sec" onclick="document.getElementById('jfile').click()">Upload JSON File</button>
    <input type="file" id="jfile" accept=".json" onchange="scoreFile(this)">
    <div id="status" class="status"></div>
  </div>
  <div>
    <label>Results</label>
    <pre id="results">Results will appear here …</pre>
  </div>
</div>

<script>
async function scoreJSON() {
  const payload = document.getElementById('payload').value;
  document.getElementById('status').textContent = 'Scoring …';
  try {
    const r = await fetch('/score', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: payload
    });
    const d = await r.json();
    document.getElementById('results').textContent = JSON.stringify(d, null, 2);
    document.getElementById('status').textContent =
      `✓ ${d.scored?.length ?? 0} sentences scored`;
  } catch(e) {
    document.getElementById('results').textContent = 'Error: ' + e.message;
    document.getElementById('status').textContent = '✗ Error';
  }
}
async function scoreFile(input) {
  const file = input.files[0];
  if (!file) return;
  document.getElementById('status').textContent = 'Uploading …';
  const fd = new FormData();
  fd.append('file', file);
  try {
    const r = await fetch('/score_file', {method:'POST', body:fd});
    const d = await r.json();
    document.getElementById('results').textContent = JSON.stringify(d, null, 2);
    document.getElementById('status').textContent =
      `✓ ${d.scored?.length ?? 0} sentences scored from file`;
  } catch(e) {
    document.getElementById('results').textContent = 'Error: ' + e.message;
    document.getElementById('status').textContent = '✗ Error';
  }
}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# APP FACTORY
# ─────────────────────────────────────────────────────────────

def create_app(rubric_path: Optional[str | Path] = None) -> "FastAPI":
    if not _FASTAPI:
        raise RuntimeError("FastAPI not installed. Run: pip install fastapi uvicorn python-multipart")

    rubric_path = rubric_path or _default_rubric_path()
    rubric      = load_rubric(rubric_path)

    app = FastAPI(
        title="Spanish EIT Automated Scorer",
        description=(
            "Deterministic, rubric-driven automated scoring system for the "
            "Spanish Elicited Imitation Task."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── GET / ────────────────────────────────────────────────
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def ui():
        return HTMLResponse(_HTML_UI)

    # ── GET /health ──────────────────────────────────────────
    @app.get("/health", tags=["Status"])
    async def health():
        return {
            "ok":     True,
            "rubric": {"name": rubric.name, "version": rubric.version},
            "scale":  {"max_points_per_item": rubric.max_points},
        }

    # ── GET /rubric ──────────────────────────────────────────
    @app.get("/rubric", tags=["Reference"])
    async def get_rubric():
        return {
            "name":       rubric.name,
            "version":    rubric.version,
            "max_points": rubric.max_points,
            "n_rules":    len(rubric.rules),
            "rules": [
                {"id": r.rule_id, "description": r.description,
                 "when": r.when, "score": r.score}
                for r in rubric.rules
            ],
        }

    # ── POST /score ──────────────────────────────────────────
    @app.post("/score", tags=["Scoring"])
    async def score(req: ScoreRequest):
        try:
            scored = _run_scoring(req.items, req.responses, rubric)
            return {
                "scored": scored,
                "rubric": {"name": rubric.name, "version": rubric.version},
                "n":      len(scored),
            }
        except Exception as e:
            logger.error(f"Scoring error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ── POST /score_file ─────────────────────────────────────
    @app.post("/score_file", tags=["Scoring"])
    async def score_file(file: UploadFile = File(...)):
        if not file.filename.endswith(".json"):
            raise HTTPException(400, "Only .json files accepted")
        try:
            raw  = await file.read()
            data = json.loads(raw)
            req  = ScoreRequest(**data)
            scored = _run_scoring(req.items, req.responses, rubric)
            return {
                "scored": scored,
                "rubric": {"name": rubric.name, "version": rubric.version},
                "n":      len(scored),
            }
        except json.JSONDecodeError as e:
            raise HTTPException(400, f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"File scoring error: {e}", exc_info=True)
            raise HTTPException(500, str(e))

    # ── GET /ui/score (HTML result wrapper) ──────────────────
    @app.get("/ui/score", response_class=HTMLResponse, include_in_schema=False)
    async def ui_score():
        return HTMLResponse(_HTML_UI)

    return app


# ─────────────────────────────────────────────────────────────
# DEFAULT RUBRIC PATH
# ─────────────────────────────────────────────────────────────

def _default_rubric_path() -> Path:
    # apps/api/main.py → apps/ → project root → eit_scorer/config/
    return Path(__file__).parent.parent.parent / "eit_scorer" / "config" / "default_rubric.yaml"


# ─────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────

def run():
    parser = argparse.ArgumentParser(prog="eit-api",
        description="Start the EIT Scorer API server")
    parser.add_argument("--host",   default="0.0.0.0")
    parser.add_argument("--port",   default=8000, type=int)
    parser.add_argument("--rubric", default=None)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    app = create_app(args.rubric)

    print(f"\n  EIT Scorer API  —  http://{args.host}:{args.port}")
    print(f"  Docs            —  http://{args.host}:{args.port}/docs")
    print(f"  Rubric          —  http://{args.host}:{args.port}/rubric\n")

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    run()
