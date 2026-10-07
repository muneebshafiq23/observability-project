import os, uuid, requests
from flask import request
from common import create_app
app, log = create_app()
INV = os.getenv("INVENTORY_URL", "http://inventory-service:8000")
PAY = os.getenv("PAYMENT_URL", "http://payment-service:8000")
PRICE = {"laptop": 900, "phone": 600, "headphones": 80, "keyboard": 50}

@app.post("/orders")
def create_order():
    b = request.get_json(force=True)
    item, qty, mode = b.get("item"), int(b.get("qty", 1)), b.get("simulate", "none")
    r = requests.get(f"{INV}/stock/{item}", timeout=5)
    if r.status_code != 200:
        return {"error": "item not available"}, 400
    if r.json()["stock"] < qty:
        log.warning(f"not enough stock for {item}")
        return {"error": "insufficient stock"}, 409
    amount = PRICE.get(item, 10) * qty
    try:
        p = requests.post(f"{PAY}/pay", json={"amount": amount, "simulate": mode}, timeout=10)
    except requests.RequestException as e:
        log.error(f"payment call failed: {e}")
        return {"error": "payment unreachable"}, 502
    if p.status_code != 200:
        log.error(f"order failed at payment item={item} qty={qty}")
        return {"error": "payment failed"}, 502
    oid = str(uuid.uuid4())[:8]
    log.info(f"order {oid} created item={item} qty={qty} amount={amount}")
    return {"order_id": oid, "item": item, "qty": qty, "amount": amount}, 201
