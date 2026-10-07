import random, time
from common import create_app
app, log = create_app()
STOCK = {"laptop": 25, "phone": 40, "headphones": 100, "keyboard": 60}

@app.get("/products")
def products():
    time.sleep(random.uniform(0.005, 0.03))
    return [{"name": k, "stock": v} for k, v in STOCK.items()]

@app.get("/stock/<item>")
def stock(item):
    time.sleep(random.uniform(0.01, 0.08))
    if item not in STOCK:
        log.warning(f"unknown item {item}")
        return {"error": "unknown item"}, 404
    log.info(f"stock check {item}={STOCK[item]}")
    return {"item": item, "stock": STOCK[item]}
