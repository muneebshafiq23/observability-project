from flask import Flask, jsonify, Response, request
import logging
import time
import os
import requests

from prometheus_client import Counter, Histogram, generate_latest

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


app = Flask(__name__)


# =========================
# OpenTelemetry Tracing
# =========================

resource = Resource.create({
    "service.name": "product-api"
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

# Incoming HTTP requests
FlaskInstrumentor().instrument_app(app)

# Outgoing HTTP requests
RequestsInstrumentor().instrument()


# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


# =========================
# Service Configuration
# =========================

ORDER_SERVICE_URL = os.getenv(
    "ORDER_SERVICE_URL",
    "http://order-service:5001"
)


# =========================
# Products
# =========================

products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 1200
    },
    {
        "id": 2,
        "name": "iPhone",
        "price": 999
    },
    {
        "id": 3,
        "name": "Headphones",
        "price": 150
    }
]


# =========================
# Prometheus Metrics
# =========================

REQUEST_COUNT = Counter(
    "product_api_requests_total",
    "Total requests received by Product API",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "product_api_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"]
)


# =========================
# Metrics Middleware
# =========================

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

    logging.info("Product API home requested")

    return jsonify({
        "service": "product-api",
        "message": "Product API is running"
    })


@app.route("/products")
def get_products():

    logging.info("Fetching all products")

    return jsonify(products)


@app.route("/products/<int:product_id>")
def get_product(product_id):

    logging.info(
        f"Fetching product with id={product_id}"
    )

    for product in products:

        if product["id"] == product_id:
            return jsonify(product)

    logging.warning(
        f"Product not found id={product_id}"
    )

    return jsonify({
        "error": "Product not found"
    }), 404


# =========================
# Checkout
# =========================

@app.route("/checkout")
def checkout():

    logging.info("Checkout request received")

    response = requests.get(
        f"{ORDER_SERVICE_URL}/orders"
    )

    return jsonify({
        "service": "product-api",
        "order_response": response.json()
    })


# =========================
# Health Check
# =========================

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "service": "product-api"
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
        port=5000
    )
