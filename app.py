from datetime import datetime
import hashlib
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

PRODUCTS = {
    "p1": {"name": "Wireless Headphones", "category": "Electronics", "price": 1499, "icon": "🎧", "description": "Clear sound for study sessions"},
    "p2": {"name": "Desk Lamp", "category": "Study essentials", "price": 899, "icon": "💡", "description": "Adjustable warm and cool light"},
    "p3": {"name": "Notebook Bundle", "category": "Stationery", "price": 299, "icon": "📚", "description": "Three notebooks for everyday notes"},
    "p4": {"name": "USB-C Hub", "category": "Electronics", "price": 1199, "icon": "🔌", "description": "Compact multi-port laptop hub"},
}

# These are fake demo credentials. Never put real credentials in frontend code.
EXPECTED_DEMO_KEY = "fake-store-integration-key-v1"
ACTIVE_DEMO_KEY = EXPECTED_DEMO_KEY
ORDERS = {}
EVENT_LOG = []
NEXT_ORDER_ID = 2001

def fingerprint(key):
    """Return a short, non-secret identifier for the UI."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:8].upper()

def mock_partner_api(order_id, api_key):
    """Local stand-in for a partner endpoint; no network request is made."""
    if api_key != EXPECTED_DEMO_KEY:
        return 401, {"error": "Unauthorized: invalid integration credential"}
    if order_id not in ORDERS:
        return 404, {"error": "Order not found"}
    return 200, {"accepted": True, "reference": f"PARTNER-{order_id}"}

def inspect_integration(order_id):
    status, body = mock_partner_api(order_id, ACTIVE_DEMO_KEY)
    mismatch = ACTIVE_DEMO_KEY != EXPECTED_DEMO_KEY
    detected = mismatch or status in (401, 403)
    event = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "order_id": order_id,
        "http_status": status,
        "detected": detected,
        "expected_fingerprint": fingerprint(EXPECTED_DEMO_KEY),
        "active_fingerprint": fingerprint(ACTIVE_DEMO_KEY),
        "message": (
            "Credential mismatch detected; partner confirmation was rejected."
            if detected else "Credential accepted; partner confirmation completed."
        ),
    }
    EVENT_LOG.insert(0, event)
    return event, body

@app.get("/")
def home():
    return render_template_string(PAGE, products=PRODUCTS)

@app.get("/api/products")
def product_list():
    return jsonify(PRODUCTS)

@app.post("/api/checkout")
def checkout():
    global NEXT_ORDER_ID, ACTIVE_DEMO_KEY
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    if not isinstance(items, list) or not items:
        return jsonify({"error": "Add a product to the cart before checkout."}), 400

    created = []
    for entry in items:
        if not isinstance(entry, dict):
            return jsonify({"error": "Invalid cart item."}), 400
        product = PRODUCTS.get(str(entry.get("product_id", "")))
        try:
            quantity = max(1, min(5, int(entry.get("quantity", 1))))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid quantity."}), 400
        if product is None:
            return jsonify({"error": "Product not found."}), 404
        order_id = NEXT_ORDER_ID
        NEXT_ORDER_ID += 1
        order = {
            "order_id": order_id,
            "item": product["name"] + (f" × {quantity}" if quantity > 1 else ""),
            "amount": product["price"] * quantity,
            "created": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "payment": "Simulated — no payment taken",
        }
        ORDERS[order_id] = order
        created.append(order)

    # Optional fault injection: emulate a backend credential being changed just
    # after local order placement. The UI never receives the key itself.
    simulate_change = bool(data.get("simulate_key_change", True))
    if simulate_change:
        ACTIVE_DEMO_KEY = "fake-store-integration-key-CHANGED"
    event, partner_response = inspect_integration(created[0]["order_id"])
    return jsonify({
        "orders": created,
        "partner_response": partner_response,
        "detector_event": event,
        "message": "Order placed in the demo store. No payment was taken.",
    })

@app.get("/api/status")
def get_status():
    return jsonify({
        "status": "mismatch" if ACTIVE_DEMO_KEY != EXPECTED_DEMO_KEY else "valid",
        "expected_fingerprint": fingerprint(EXPECTED_DEMO_KEY),
        "active_fingerprint": fingerprint(ACTIVE_DEMO_KEY),
        "events": EVENT_LOG[:10],
    })

@app.post("/api/repair-key")
def repair_key():
    global ACTIVE_DEMO_KEY
    ACTIVE_DEMO_KEY = EXPECTED_DEMO_KEY
    pending = next((event for event in EVENT_LOG if event["http_status"] in (401, 403)), None)
    retry = None
    if pending:
        retry, _ = inspect_integration(pending["order_id"])
    return jsonify({
        "status": "valid",
        "expected_fingerprint": fingerprint(EXPECTED_DEMO_KEY),
        "active_fingerprint": fingerprint(ACTIVE_DEMO_KEY),
        "retry": retry,
        "message": "Demo credential restored. The latest failed partner call was retried.",
    })

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AuthLens | Integration Key Monitor</title>
<style>
:root{--navy:#172337;--ink:#1b2838;--muted:#6b7785;--line:#e5e9ef;--bg:#f4f6f8;--blue:#355de8;--gold:#f4bd43;--red:#be3f48;--green:#167450}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Inter,system-ui,-apple-system,"Segoe UI",sans-serif}button,input{font:inherit}button{cursor:pointer}.top{background:#172337;color:white;padding:13px max(22px,calc((100% - 1160px)/2));display:flex;align-items:center;gap:20px}.brand{font-weight:850;font-size:21px;letter-spacing:-.6px;white-space:nowrap}.brand i{font-style:normal;color:#ffca55}.search{flex:1;display:flex;max-width:560px}.search input{width:100%;padding:10px 12px;border:0;border-radius:7px 0 0 7px;outline:0}.search button{border:0;background:var(--gold);padding:0 16px;border-radius:0 7px 7px 0;font-weight:800}.carttag{font-weight:700;white-space:nowrap}.subnav{background:#25354b;color:#dce4ef;padding:8px max(22px,calc((100% - 1160px)/2));display:flex;justify-content:space-between;font-size:12px}.wrap{max-width:1160px;margin:22px auto;padding:0 22px}.hero{background:linear-gradient(105deg,#eaf0ff,#f8faff 68%,#fff2cf);border:1px solid #dfe6f4;border-radius:15px;padding:24px 27px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;gap:15px}.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:.13em;color:var(--blue);font-weight:850}.hero h1{margin:5px 0 6px;font-size:27px;letter-spacing:-.7px}.hero p{margin:0;color:var(--muted)}.shield{width:74px;height:74px;border-radius:22px;background:white;display:grid;place-items:center;font-size:35px;box-shadow:0 6px 20px #344d8820}.section-title{display:flex;justify-content:space-between;align-items:end;margin:22px 0 12px}.section-title h2{margin:0;font-size:18px}.section-title span{font-size:12px;color:var(--muted)}.products{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}.product{background:white;border:1px solid var(--line);border-radius:12px;padding:15px;display:flex;flex-direction:column;min-height:218px}.product-icon{height:74px;background:#f4f6fa;border-radius:9px;display:grid;place-items:center;font-size:38px;margin-bottom:12px}.cat{color:var(--blue);font-size:10px;text-transform:uppercase;letter-spacing:.08em;font-weight:800}.product h3{font-size:14px;margin:4px 0}.product p{font-size:12px;color:var(--muted);margin:0 0 11px}.price-row{display:flex;justify-content:space-between;align-items:center;margin-top:auto}.price{font-weight:850;font-size:16px}.add{background:#fff5d9;border:1px solid #ecd58e;border-radius:7px;padding:7px 10px;font-weight:750;font-size:12px}.layout{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-top:18px}.panel{background:white;border:1px solid var(--line);border-radius:12px;padding:17px}.panel h2{margin:0 0 12px;font-size:16px}.cartrow,.orderrow,.eventrow{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--line);padding:10px 0;gap:10px}.cartrow small,.orderrow small{display:block;color:var(--muted);font-size:11px}.qty{display:flex;align-items:center;gap:8px}.qty button{border:1px solid var(--line);background:white;border-radius:5px;width:24px;height:24px}.total{border-top:1px solid var(--line);padding-top:12px;display:flex;justify-content:space-between;font-weight:800}.checkout{width:100%;border:0;border-radius:7px;background:var(--gold);padding:10px;font-weight:800;margin-top:12px}.checkout:disabled{opacity:.65}.empty{padding:18px 0;color:var(--muted);font-size:12px}.orderid{font-weight:800;color:var(--blue)}.statusbar{background:white;border:1px solid var(--line);border-radius:12px;padding:14px 17px;margin-top:18px;display:flex;align-items:center;justify-content:space-between;gap:12px}.statusleft{display:flex;align-items:center;gap:10px}.dot{width:11px;height:11px;border-radius:50%;background:var(--green)}.statusbar.bad .dot{background:var(--red)}.statusbar strong{display:block}.statusbar small{color:var(--muted)}.badge{border-radius:99px;padding:5px 9px;font-weight:800;font-size:11px;color:var(--green);background:#e8f6ef}.bad .badge{color:#a5333d;background:#fff0ef}.monitor{background:white;border:1px solid var(--line);border-radius:12px;padding:18px;margin-top:14px}.monitor-head{display:flex;justify-content:space-between;gap:12px;align-items:start}.monitor h2{margin:0;font-size:17px}.monitor p{color:var(--muted);font-size:12px;margin:4px 0 13px}.repair{border:0;background:var(--blue);color:white;padding:9px 12px;border-radius:7px;font-weight:750;white-space:nowrap}.repair:disabled{opacity:.6}.details{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.detail{padding:10px;background:#f6f8fb;border:1px solid var(--line);border-radius:8px}.detail small{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.06em}.detail b{display:block;margin-top:3px;font-size:13px}.notice{padding:12px;border-radius:8px;margin-top:12px;font-size:13px}.notice.bad{color:#972f38;background:#fff0ef;border:1px solid #f1ceca}.notice.good{color:#176947;background:#eaf7f1;border:1px solid #cbe6d8}.notice.neutral{color:#516174;background:#f3f5f8;border:1px solid var(--line)}.events{margin-top:13px}.eventrow{font-size:11px}.eventrow small{color:var(--muted)}.foot{margin:20px 0 30px;color:var(--muted);font-size:10px;text-align:center}.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);padding:11px 15px;color:white;background:#172337;border-radius:8px;box-shadow:0 6px 24px #0003;display:none;z-index:3}@media(max-width:850px){.products{grid-template-columns:repeat(2,1fr)}.top{flex-wrap:wrap}.search{order:3;flex-basis:100%;max-width:none}.layout{grid-template-columns:1fr}}@media(max-width:500px){.products{gap:8px}.product{padding:10px}.hero{padding:18px}.hero h1{font-size:22px}.shield{width:55px;height:55px;font-size:27px}.subnav{gap:8px;flex-wrap:wrap}.monitor-head{flex-direction:column}.details{grid-template-columns:1fr}}
</style></head><body>
<header class="top"><div class="brand">auth<i>lens</i> market</div><div class="search"><input id="search" placeholder="Search demo products" oninput="filterProducts()"><button onclick="filterProducts()">Search</button></div><div class="carttag">🛒 Cart <span id="cartcount">0</span></div></header>
<div class="subnav"><span>Shop &nbsp; Electronics &nbsp; Study essentials &nbsp; Stationery</span><span>Demo store · simulated checkout</span></div>
<main class="wrap">
<section class="hero"><div><div class="eyebrow">API integration monitoring demo</div><h1>Place an order. Watch the backend integration.</h1><p>After checkout, AuthLens checks whether the store’s partner API credential still works.</p></div><div class="shield">🔐</div></section>
<div class="section-title"><h2>Popular in the demo store</h2><span>Fictional products and prices</span></div>
<section class="products" id="products">{% for pid,p in products.items() %}<article class="product" data-name="{{ p.name|lower }}"><div class="product-icon">{{ p.icon }}</div><div class="cat">{{ p.category }}</div><h3>{{ p.name }}</h3><p>{{ p.description }}</p><div class="price-row"><span class="price">₹{{ p.price }}</span><button class="add" onclick="addToCart('{{ pid }}')">Add to cart</button></div></article>{% endfor %}</section>
<div class="layout"><section class="panel"><h2>Your cart <span id="cartcount2" style="color:#718096;font-size:12px;font-weight:500"></span></h2><div id="cart"></div><div id="cartfoot" hidden><div class="total"><span>Total</span><span id="carttotal"></span></div><label style="display:flex;align-items:start;gap:8px;margin-top:12px;font-size:11px;color:#596779"><input id="inject" type="checkbox" checked style="margin-top:3px"> Simulate backend API-key change immediately after booking</label><button class="checkout" onclick="checkout()">Place demo order · no payment</button></div></section>
<section class="panel"><h2>Order history</h2><div id="orders"><div class="empty">Your demo orders will appear here after checkout.</div></div></section></div>
<section id="statusbar" class="statusbar"><div class="statusleft"><span class="dot"></span><div><strong>Partner API credential</strong><small id="statusdetail">Waiting for the first order check</small></div></div><span id="statusbadge" class="badge">READY</span></section>
<section class="monitor"><div class="monitor-head"><div><h2>AuthLens backend monitor</h2><p>The demo key stays on the server. The page shows only short fingerprints, never the credential itself.</p></div><button class="repair" id="repair" onclick="repairKey()" hidden>Restore demo key & retry</button></div>
<div id="latest"><div class="notice neutral">Place an order to trigger the partner API call and credential check.</div></div><div class="events" id="events"></div></section>
<div class="foot">AuthLens Market · Local student prototype · No Amazon connection, real account, payment, or external API request.</div></main><div class="toast" id="toast"></div>
<script>
const products={{ products|tojson }};
let cart={};
function money(n){return '₹'+Number(n).toLocaleString('en-IN')}
function toast(msg){let t=document.getElementById('toast');t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',2700)}
function addToCart(id){cart[id]=(cart[id]||0)+1;renderCart();toast(products[id].name+' added to cart')}
function changeQty(id,delta){cart[id]=(cart[id]||0)+delta;if(cart[id]<=0)delete cart[id];renderCart()}
function renderCart(){let el=document.getElementById('cart'),keys=Object.keys(cart),count=keys.reduce((n,k)=>n+cart[k],0);document.getElementById('cartcount').textContent=count;document.getElementById('cartcount2').textContent=count?'('+count+' item'+(count===1?'':'s')+')':'';if(!keys.length){el.innerHTML='<div class="empty">Your cart is empty. Add a product to begin.</div>';document.getElementById('cartfoot').hidden=true;return}let total=0;el.innerHTML=keys.map(k=>{let p=products[k],q=cart[k];total+=p.price*q;return '<div class="cartrow"><div><b>'+p.name+'</b><small>'+money(p.price)+' each</small></div><div class="qty"><button class="dec" data-id="'+k+'">−</button><span>'+q+'</span><button class="inc" data-id="'+k+'">+</button></div></div>'}).join('');el.querySelectorAll('.dec').forEach(b=>b.onclick=()=>changeQty(b.dataset.id,-1));el.querySelectorAll('.inc').forEach(b=>b.onclick=()=>changeQty(b.dataset.id,1));document.getElementById('carttotal').textContent=money(total);document.getElementById('cartfoot').hidden=false}
function showEvent(ev){let bar=document.getElementById('statusbar'),bad=ev.detected;bar.classList.toggle('bad',bad);document.getElementById('statusbadge').textContent=bad?'MISMATCH DETECTED':'VALID';document.getElementById('statusdetail').textContent=bad?'Partner API rejected the post-booking request (HTTP '+ev.http_status+').':'Partner API accepted the order request (HTTP '+ev.http_status+').';document.getElementById('latest').innerHTML='<div class="notice '+(bad?'bad':'good')+'"><b>'+(bad?'Credential change detected after booking':'Integration check succeeded')+'</b><br>Order #'+ev.order_id+' was placed in the demo store. Partner confirmation '+(bad?'failed':'completed')+'. '+ev.message+'</div><div class="details"><div class="detail"><small>Mock partner response</small><b>HTTP '+ev.http_status+'</b></div><div class="detail"><small>Expected key fingerprint</small><b>'+ev.expected_fingerprint+'</b></div><div class="detail"><small>Active key fingerprint</small><b>'+ev.active_fingerprint+'</b></div></div>';document.getElementById('repair').hidden=!bad}
async function checkout(){let items=Object.keys(cart).map(k=>({product_id:k,quantity:cart[k]}));if(!items.length)return;let b=document.querySelector('.checkout');b.disabled=true;b.textContent='Placing order and checking API…';try{let r=await fetch('/api/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items,simulate_key_change:document.getElementById('inject').checked})});let d=await r.json();if(!r.ok)throw new Error(d.error||'Could not place order');cart={};renderCart();loadOrders();showEvent(d.detector_event);toast('Order #'+d.orders.map(o=>o.order_id).join(', #')+' placed · no payment taken')}catch(e){toast(e.message)}finally{b.disabled=false;b.textContent='Place demo order · no payment'}}
async function loadOrders(){let r=await fetch('/api/orders'),d=await r.json(),el=document.getElementById('orders');if(!d.length){el.innerHTML='<div class="empty">Your demo orders will appear here after checkout.</div>';return}el.innerHTML=d.map(o=>'<div class="orderrow"><div><b>'+o.item+'</b><small><span class="orderid">Order #'+o.order_id+'</span> · '+o.created+'</small></div><div style="text-align:right"><b>'+money(o.amount)+'</b><small>'+o.payment+'</small></div></div>').join('')}
async function repairKey(){let b=document.getElementById('repair');b.disabled=true;b.textContent='Restoring and retrying…';try{let r=await fetch('/api/repair-key',{method:'POST'}),d=await r.json();if(d.retry)showEvent(d.retry);else{document.getElementById('statusbar').classList.remove('bad');document.getElementById('statusbadge').textContent='VALID';document.getElementById('statusdetail').textContent='Demo integration credential restored.';document.getElementById('latest').innerHTML='<div class="notice good">'+d.message+'</div>'}toast(d.message)}finally{b.disabled=false;b.textContent='Restore demo key & retry'}}
function filterProducts(){let q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('.product').forEach(p=>p.style.display=p.dataset.name.includes(q)?'flex':'none')}
async function refreshStatus(){let r=await fetch('/api/status'),d=await r.json();if(d.events.length)showEvent(d.events[0])}
renderCart();loadOrders();refreshStatus();
</script></body></html>"""

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
