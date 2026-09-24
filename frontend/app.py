from flask import Flask, jsonify, Response, request, g
import requests
import logging
import time

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
    "service.name": "frontend"
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

# Instrument incoming Flask requests
FlaskInstrumentor().instrument_app(app)

# Instrument outgoing HTTP requests
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

PRODUCT_API = "http://product-api:5000"


# =========================
# Prometheus Metrics
# =========================

REQUEST_COUNT = Counter(
    "frontend_requests_total",
    "Total number of requests received by frontend",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "frontend_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"]
)


# =========================
# Metrics Middleware
# =========================

@app.before_request
def start_timer():

    g.start_time = time.time()


@app.after_request
def record_metrics(response):

    if request.path == "/metrics":
        return response

    duration = time.time() - g.start_time

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
# Application Routes
# =========================

@app.route("/")
def home():

    logging.info("Frontend home page requested")

    return jsonify({
        "service": "frontend",
        "message": "Welcome to Simple E-Commerce"
    })


@app.route("/products")
def products():

    logging.info("Requesting products from Product API")

    response = requests.get(
        f"{PRODUCT_API}/products"
    )

    return jsonify({
        "service": "frontend",
        "products": response.json()
    })


# =========================
# Checkout
# =========================

@app.route("/checkout")
def checkout():

    logging.info("Checkout request received")

    response = requests.get(
        f"{PRODUCT_API}/checkout"
    )

    return jsonify({
        "service": "frontend",
        "checkout": response.json()
    })


# =========================
# Health Check
# =========================

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "service": "frontend"
    })


# =========================
# Prometheus Endpoint
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
        port=8080
    )
