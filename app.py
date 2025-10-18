import json, os
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse

app = FastAPI()
STATUS_FILE = "status.json"

INDEX_HTML = """
<!doctype html><meta name=viewport content="width=device-width, initial-scale=1">
<title>KEC Free Rooms</title>
<style>
body{font-family:system-ui,Segoe UI,Arial;margin:16px}
.header{display:flex;gap:8px;align-items:center;margin-bottom:12px}
.card{border:1px solid #ddd;border-radius:12px;padding:12px;margin:8px 0}
.badge{padding:2px 8px;border-radius:999px;font-size:12px}
.badge.green{background:#e6f4ea;color:#137333}
.badge.red{background:#fde8e8;color:#b91c1c}
.small{color:#666;font-size:12px}
</style>
<div class=header>
  <h2 style="margin:0">KEC Free Rooms</h2>
  <button id=refresh>Refresh</button>
  <span id=stamp class=small></span>
</div>
<div id=list></div>
<script>
function hhmm(iso){ if(!iso) return ""; const d=new Date(iso);
  return d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}); }
async function load(){
  const r=await fetch('/api/status'); const data=await r.json();
  const el=document.getElementById('list'); el.innerHTML='';
  data.forEach(item=>{
    const d=document.createElement('div'); d.className='card';
    const avail=item.available_now;
    const badge=avail?'<span class="badge green">Available</span>':'<span class="badge red">Busy</span>';
    const sub=avail?`Free until <b>${hhmm(item.free_until)}</b>`:`Busy until <b>${hhmm(item.busy_until)}</b>`;
    const next=(item.next_events||[]).slice(0,3).map(ev=>`${hhmm(ev.start)}–${hhmm(ev.end)}`).join(', ');
    d.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center">
      <h3 style="margin:0">${item.room}</h3>${badge}</div>
      <div>${sub}</div>${next?`<div class=small>Next: ${next}</div>`:''}`;
    el.appendChild(d);
  });
  document.getElementById('stamp').textContent = "Updated " + new Date().toLocaleTimeString();
}
document.getElementById('refresh').onclick=load; load(); setInterval(load, 60000);
</script>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML

@app.get("/api/status")
def status():
    if not os.path.exists(STATUS_FILE):
        return JSONResponse([])
    try:
        with open(STATUS_FILE) as f:
            data = json.load(f)
    except Exception:
        data = []
    return JSONResponse(data)

@app.get("/health")
def health():
    return {"ok": True}
