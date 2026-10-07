import os, requests
from flask import request
from common import create_app
app, log = create_app()
ORDER = os.getenv("ORDER_URL", "http://order-service:8000")
INV = os.getenv("INVENTORY_URL", "http://inventory-service:8000")

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demo Shop</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Manrope:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#EDF0F3;--surface:#fff;--ink:#16213A;--muted:#5B6479;--line:#D5DAE3;--ivory:#F4F2EE;
--brass:#B88A3E;--ok:#8FD0A8;--err:#F0A3A3;--serif:"Instrument Serif",Georgia,serif;--sans:Manrope,system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5}
.wrap{max-width:1040px;margin:0 auto;padding:56px 24px 72px}
header{margin-bottom:40px}
h1{font-family:var(--serif);font-weight:400;font-size:clamp(40px,6vw,64px);line-height:1;margin:0 0 12px;letter-spacing:-.01em}
header p{margin:0;color:var(--muted);max-width:46ch}
.layout{display:grid;grid-template-columns:1.25fr 1fr;gap:32px;align-items:start}
h2{font-family:var(--serif);font-weight:400;font-size:26px;margin:0 0 16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.tile{all:unset;box-sizing:border-box;cursor:pointer;background:var(--surface);border:1px solid var(--line);
border-radius:14px;padding:22px 20px;display:flex;flex-direction:column;gap:6px;min-height:150px;transition:border-color .2s,box-shadow .2s}
.tile:hover{border-color:#aab2c2}
.tile:focus-visible,button:focus-visible,.step button:focus-visible{outline:2px solid var(--brass);outline-offset:3px}
.tile[aria-pressed=true]{border-color:var(--ink);box-shadow:0 0 0 1px var(--ink)}
.tile .name{font-family:var(--serif);font-size:28px;text-transform:capitalize}
.tile .price{font-size:18px;font-weight:600}
.tile .stock{margin-top:auto;color:var(--muted);font-size:13px}
.panel{background:var(--ink);color:var(--ivory);border-radius:18px;padding:32px 28px;position:sticky;top:24px}
.panel h2{color:var(--ivory)}
.row{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid #2c3a5c}
.row span{color:#b9c0d0;font-size:14px}
.step{display:flex;align-items:center;gap:14px}
.step button{all:unset;cursor:pointer;width:32px;height:32px;border-radius:50%;border:1px solid #4a5a82;text-align:center;line-height:30px;font-size:18px}
.step button:hover{border-color:var(--brass)}
.step output{min-width:20px;text-align:center;font-weight:600}
.total{display:flex;justify-content:space-between;align-items:baseline;padding:22px 0 20px}
.total b{font-family:var(--serif);font-weight:400;font-size:46px;line-height:1}
button.primary{width:100%;border:0;border-radius:10px;background:var(--brass);color:var(--ink);font:600 15px var(--sans);padding:15px;cursor:pointer;transition:filter .2s}
button.primary:hover:not(:disabled){filter:brightness(1.08)}
.sim{margin-top:22px}
.sim p{margin:0 0 8px;font-size:13px;color:#b9c0d0}
.sim div{display:flex;gap:8px}
button.ghost{flex:1;background:none;border:1px solid #4a5a82;color:var(--ivory);border-radius:10px;font:500 13px var(--sans);padding:11px 8px;cursor:pointer}
button.ghost:hover:not(:disabled){border-color:var(--brass)}
button:disabled{opacity:.5;cursor:not-allowed}
.result{margin-top:26px;padding-top:22px;border-top:1px solid #2c3a5c;font-size:14px;min-height:96px}
.result .empty{color:#b9c0d0}
.result .title{font-family:var(--serif);font-size:24px;margin-bottom:6px}
.result.ok .title{color:var(--ok)}.result.bad .title{color:var(--err)}
.result dl{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;margin:10px 0 0}
.result dt{color:#b9c0d0}.result dd{margin:0;text-align:right}
@media(max-width:820px){.layout{grid-template-columns:1fr}.panel{position:static}.wrap{padding-top:36px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head>
<body><div class="wrap">
<header><h1>Demo Shop</h1><p>Pick a product, choose how many, and place your order.</p></header>
<div class="layout">
<section><h2>Products</h2><div class="grid" id="grid"></div></section>
<aside class="panel" aria-live="polite">
<h2>Your order</h2>
<div class="row"><span>Product</span><strong id="sel">None selected</strong></div>
<div class="row"><span>Quantity</span><div class="step">
<button id="minus" aria-label="Decrease quantity">&minus;</button><output id="qty">1</output>
<button id="plus" aria-label="Increase quantity">+</button></div></div>
<div class="total"><span>Total</span><b id="total">$0</b></div>
<button class="primary" id="go" disabled>Place order</button>
<div class="sim"><p>Test scenarios</p><div>
<button class="ghost" id="slow" disabled>Slow payment</button>
<button class="ghost" id="fail" disabled>Failed payment</button></div></div>
<div class="result" id="result"><div class="empty">Your order confirmation will appear here.</div></div>
</aside></div></div>
<script>
const PRICE={laptop:900,phone:600,headphones:80,keyboard:50};
const $=id=>document.getElementById(id);
const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let sel=null,qty=1,stock={};
function refresh(){
  $('sel').textContent=sel?sel[0].toUpperCase()+sel.slice(1):'None selected';
  $('qty').textContent=qty;
  $('total').textContent=money(sel?PRICE[sel]*qty:0);
  ['go','slow','fail'].forEach(i=>$(i).disabled=!sel);
  document.querySelectorAll('.tile').forEach(t=>t.setAttribute('aria-pressed',t.dataset.name===sel));
}
fetch('/api/products').then(r=>r.json()).then(list=>{
  $('grid').innerHTML=list.map(p=>{stock[p.name]=p.stock;
    return `<button class="tile" data-name="${esc(p.name)}" aria-pressed="false"><span class="name">${esc(p.name)}</span>
    <span class="price">${money(PRICE[p.name]||0)}</span><span class="stock">${p.stock} in stock</span></button>`}).join('');
  document.querySelectorAll('.tile').forEach(t=>t.onclick=()=>{sel=t.dataset.name;qty=Math.min(qty,stock[sel]);refresh()});
}).catch(()=>{$('grid').textContent='Products could not be loaded. Refresh the page to try again.'});
$('minus').onclick=()=>{if(qty>1){qty--;refresh()}};
$('plus').onclick=()=>{if(sel&&qty<stock[sel]){qty++;refresh()}};
const MSG={'payment failed':'The payment was declined. Place the order again to retry.',
'insufficient stock':'There is not enough stock for that quantity.','item not available':'That product is not available.'};
async function order(mode){
  const btns=['go','slow','fail'].map($);btns.forEach(b=>b.disabled=true);
  const box=$('result');box.className='result';box.innerHTML='<div class="empty">Processing your order…</div>';
  const t0=performance.now();let status=0,data={};
  try{const r=await fetch('/api/order',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({item:sel,qty:qty,simulate:mode})});status=r.status;data=await r.json()}catch(e){data={error:'network'}}
  const ms=Math.round(performance.now()-t0);
  if(status===201){box.className='result ok';
    box.innerHTML=`<div class="title">Order confirmed</div><dl><dt>Order</dt><dd>${esc(data.order_id)}</dd>
    <dt>Items</dt><dd>${esc(data.qty)} &times; ${esc(data.item)}</dd><dt>Charged</dt><dd>${money(data.amount)}</dd>
    <dt>Time taken</dt><dd>${ms} ms</dd></dl>`}
  else{box.className='result bad';
    box.innerHTML=`<div class="title">Order not placed</div><div>${esc(MSG[data.error]||'The service could not be reached. Try again in a moment.')}</div>
    <dl><dt>Status</dt><dd>${status||'no response'}</dd><dt>Time taken</dt><dd>${ms} ms</dd></dl>`}
  refresh();
}
$('go').onclick=()=>order('none');$('slow').onclick=()=>order('slow');$('fail').onclick=()=>order('error');
</script></body></html>"""

@app.get("/")
def index():
    return PAGE

@app.get("/api/products")
def products():
    return requests.get(f"{INV}/products", timeout=5).json()

@app.post("/api/order")
def order():
    r = requests.post(f"{ORDER}/orders", json=request.get_json(force=True), timeout=15)
    log.info(f"order request finished status={r.status_code}")
    return r.content, r.status_code, {"Content-Type": "application/json"}
