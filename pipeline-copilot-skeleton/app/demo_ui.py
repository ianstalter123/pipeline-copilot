"""Recording-friendly views of saved replies; decisions use the existing API."""
from html import escape
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from app.store import connect

STYLE = '''<style>
*{box-sizing:border-box}body{font:17px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#19322c;background:#f3f5f0;margin:0}main{max-width:1150px;margin:32px auto;padding:0 28px}nav{display:flex;gap:20px;margin-bottom:24px}a{color:#16644e}h1{font-size:32px;letter-spacing:-1px;margin:10px 0}h2{font-size:20px;margin:0 0 12px}p{margin:8px 0}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:2px;color:#537168}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{background:white;border:1px solid #d6dfd5;border-radius:14px;padding:24px;margin-bottom:20px}.badge{display:inline-block;background:#dceee0;padding:4px 10px;border-radius:8px;font-size:14px}pre{white-space:pre-wrap;font:inherit;margin:12px 0}textarea{width:100%;min-height:260px;font:inherit;padding:14px;border:1px solid #b4c5b9;border-radius:8px}button,.button{border:0;border-radius:7px;background:#165c46;color:white;padding:10px 16px;cursor:pointer;font:inherit;text-decoration:none;display:inline-block}button.secondary{background:#e7ece4;color:#19322c}button:disabled{opacity:.5;cursor:default}dt{font-size:12px;text-transform:uppercase;color:#537168;margin-top:12px}dd{margin:2px 0}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #d6dfd5}.muted{color:#537168;font-size:14px}#status{min-height:26px} @media(max-width:800px){.grid{grid-template-columns:1fr}}</style>'''
def e(value):
    return escape(str(value)) if value is not None else 'Not captured'
def page(title, body):
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+'</title>'+STYLE+'<main><nav><a href="/demo">Demo overview</a><a href="/">Inbox</a><a href="/funnel">Funnel</a><a href="/leads">Lead Finder</a><a href="/demo/eval">Evaluation</a></nav>'+body+'</main></html>'
def rows(sql, params=()):
    import sqlite3
    conn=connect()
    conn.row_factory=sqlite3.Row
    try: return conn.execute(sql,params).fetchall()
    finally: conn.close()
def register_demo_routes(app):
    @app.get('/demo', response_class=HTMLResponse)
    def demo():
        counts=rows('SELECT (SELECT COUNT(*) FROM replies) AS replies,(SELECT COUNT(*) FROM classifications) AS classified,(SELECT COUNT(*) FROM extractions) AS extracted,(SELECT COUNT(*) FROM drafts) AS drafted')[0]
        classes=rows('SELECT reply_class,COUNT(*) AS n FROM classifications GROUP BY reply_class ORDER BY n DESC')
        decisions=rows('SELECT decision,COUNT(*) AS n FROM drafts GROUP BY decision')
        return page('Pipeline Copilot', '<div class="eyebrow">Pipeline Copilot · synthetic demo data</div><h1>Every reply gets a next step.</h1><p>Multilingual sales triage with human review.</p><div class="card"><h2>Saved pipeline results</h2><p>'+ ' &nbsp; · &nbsp; '.join(f'<b>{counts[k]}</b> {k}' for k in counts.keys())+'</p></div><div class="grid"><div class="card"><h2>Reply funnel</h2>'+''.join(f'<p>{e(r["reply_class"])} <b>{r["n"]}</b></p>' for r in classes)+'</div><div class="card"><h2>Review queue</h2>'+''.join(f'<p>{e(r["decision"])} <b>{r["n"]}</b></p>' for r in decisions)+'<p class="muted">Approval records a decision. This prototype does not send email.</p><h2 style="margin-top:28px">Demo walkthrough</h2><p><a href="/replies/2">1. English · meeting-ready</a></p><p><a href="/replies/20">2. Spanish · meeting-ready</a></p><p><a href="/replies/26">3. Chinese · meeting-ready</a></p><p><a href="/demo/eval">4. Model evaluation</a></p><p><a href="/leads">5. Lead Finder proof</a></p></div></div>')
    @app.get('/replies/{reply_id}', response_class=HTMLResponse)
    def detail(reply_id: int):
        found=rows('SELECT r.*,c.reply_class,c.confidence,x.budget_signal,x.timeline,x.pain_point,x.decision_maker,x.next_step,d.id AS draft_id,d.draft_text,d.decision FROM replies r LEFT JOIN classifications c ON c.reply_id=r.id LEFT JOIN extractions x ON x.reply_id=r.id LEFT JOIN drafts d ON d.reply_id=r.id WHERE r.id=? ORDER BY d.id DESC LIMIT 1',(reply_id,))
        if not found: raise HTTPException(404,'Reply not found')
        r=found[0]
        extraction=''.join(f'<dt>{label}</dt><dd>{e(r[key])}</dd>' for key,label in [('budget_signal','Budget'),('timeline','Timeline'),('pain_point','Pain point'),('decision_maker','Decision-maker'),('next_step','Next step')])
        body=f'<div class="eyebrow">Saved reply · {e(r["external_id"])} · {e(r["language"])}</div><h1>{e(r["subject"])}</h1><p><span class="badge">{e(r["reply_class"])}</span> <span class="muted">Confidence {e(r["confidence"])}</span></p><div class="grid"><section><div class="card"><h2>Incoming reply</h2><p class="muted">{e(r["sender"])}</p><pre>{e(r["body"])}</pre></div><div class="card"><h2>Extracted signals</h2><dl>{extraction}</dl></div></section><section class="card"><h2>Human review</h2><p>Decision: <b id="decision">{e(r["decision"])}</b></p><p class="muted">Review the draft in the sender’s language. Approval saves your decision; no email is sent by this prototype.</p>'
        if r['draft_id'] is not None:
            body+=f'<label for="draft" class="muted">Draft reply</label><textarea id="draft">{e(r["draft_text"])}</textarea><p><button data-decision="approved">Approve</button> <button class="secondary" data-decision="edited">Save edit</button> <button class="secondary" data-decision="rejected">Reject</button></p><p id="status" role="status" aria-live="polite"></p>'
            body+='''<script>
const originalDraft = document.querySelector('#draft').value;
document.querySelectorAll('[data-decision]').forEach(button=>button.onclick=async()=>{
 const status=document.querySelector('#status'),buttons=document.querySelectorAll('[data-decision]');
 const decision=button.dataset.decision, draft=document.querySelector('#draft').value;
 if(decision==='approved' && draft!==originalDraft){status.textContent='Use Save edit to record changes before approving. Reload the page afterward to approve the saved draft.';return;}
 buttons.forEach(b=>b.disabled=true);status.textContent='Saving…';
 try{const payload={decision};if(decision==='edited')payload.text=draft;
 const response=await fetch('/api/drafts/DRAFT_ID/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
 if(!response.ok)throw new Error('Could not save decision. Please try again.');
 const result=await response.json();document.querySelector('#decision').textContent=result.decision;status.textContent='Decision saved. No email sent.';
 }catch(error){status.textContent=error.message;}finally{buttons.forEach(b=>b.disabled=false);}
});</script>'''.replace('DRAFT_ID',str(r['draft_id']))
        else: body+='<p>No saved draft.</p>'
        return page('Reply '+str(reply_id),body+'</section></div>')
    @app.get('/demo/eval', response_class=HTMLResponse)
    def evaluation():
        return page('Model evaluation','<div class="eyebrow">Reported results · November 2, 2026</div><h1>Same 30 replies. Two models.</h1><div class="card"><table><thead><tr><th>Model</th><th>Accuracy</th><th>Mean latency</th></tr></thead><tbody><tr><td>Muse Spark 1.3</td><td><b>26/30 · 86.7%</b></td><td>5.3 seconds</td></tr><tr><td>Llama 3.1 8B · local Ollama</td><td><b>21/30 · 70.0%</b></td><td>0.66 seconds</td></tr></tbody></table><p>Spark median: 3.0 seconds. Two API stalls increased its mean.</p><p class="muted">Source: repository README. Classification-only comparison on a small synthetic dataset; these are saved results, not a live benchmark. Local label spellings were canonicalized before scoring.</p></div><div class="card"><h2>Human approval stays in the loop.</h2><p>All 30 replies have saved extractions and drafts. Reply and outreach decisions are stored for human review.</p><p class="muted">Slack alerts require a configured webhook; otherwise they are logged. Email sending is not implemented.</p></div>')
