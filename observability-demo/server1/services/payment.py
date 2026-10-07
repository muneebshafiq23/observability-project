import random, time
from flask import request
from common import create_app
app, log = create_app()

@app.post("/pay")
def pay():
    body = request.get_json(force=True)
    mode = body.get("simulate", "none")
    if mode == "slow":
        time.sleep(random.uniform(1.5, 3))
    else:
        time.sleep(random.uniform(0.05, 0.3))
    if mode == "error" or random.random() < 0.05:
        log.error(f"payment declined for amount={body.get('amount')}")
        return {"error": "payment failed"}, 500
    log.info(f"payment ok amount={body.get('amount')}")
    return {"status": "paid"}
