from flask import Flask, jsonify, request, Response
import logging
import time
import uuid

from prometheus_client import Counter, Histogram, generate_latest

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor


app = Flask(__name__)


# =========================
# OpenTelemetry Tracing
# =========================

resource = Resource.create({
    "service.name": "order-service"
})

trace_provider = TracerProvider(
    resource=resource
)

otlp_exporter = OTLPSpanExporter(
    endpoint="http://172.31.20.203:4318/v1/traces"
)

trace_provider.add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

trace.set_tracer_provider(trace_provider)

FlaskInstrumentor().instrument_app(app)


# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


orders = {}


# =========================
# Prometheus Metrics
# =========================

REQUEST_COUNT = Counter(
    "order_service_requests_total",
    "Total requests received by Order Service",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "order_service_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"]
)


@app.before_request
def start_timer():

    request.start_time = time.time()


@app.after_request
def record_metrics(response):

    if request.path == "/metrics":
        return response

    duration = time.time() - request.start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        endpoint=request.path
    ).observe(duration)

    return response

# =========================
# Routes
# =========================

@app.route("/")
def home():

    logging.info("Order service home requested")

    return jsonify({
        "service": "order-service",
        "message": "Order Service is running"
    })


# =========================
# Get Orders
# =========================

@app.route("/orders", methods=["GET"])
def get_orders():

    logging.info("Fetching all orders")

    return jsonify({
        "service": "order-service",
        "orders": list(orders.values())
    })


# =========================
# Create Order
# =========================

@app.route("/orders", methods=["POST"])
def create_order():

    data = request.get_json()

    if not data or "product_id" not in data:

        logging.warning(
            "Order creation failed: product_id missing"
        )

        return jsonify({
            "error": "product_id is required"
        }), 400

    order_id = str(uuid.uuid4())

    order = {
        "order_id": order_id,
        "product_id": data["product_id"],
        "quantity": data.get("quantity", 1)
    }

    orders[order_id] = order

    logging.info(
        f"Order created successfully id={order_id}"
    )

    return jsonify(order), 201


# =========================
# Get Single Order
# =========================

@app.route("/orders/<order_id>")
def get_order(order_id):

    logging.info(
        f"Fetching order id={order_id}"
    )

    order = orders.get(order_id)

    if not order:

        logging.warning(
            f"Order not found id={order_id}"
        )

        return jsonify({
            "error": "Order not found"
        }), 404

    return jsonify(order)


# =========================
# Health
# =========================

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "service": "order-service"
    })


# =========================
# Metrics Endpoint
# =========================

@app.route("/metrics")
def metrics():

    return Response(
        generate_latest(),
        mimetype="text/plain"
    )


# =========================
# Start Application
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001
    )
