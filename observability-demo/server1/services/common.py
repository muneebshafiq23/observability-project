import os, time, json, logging, sys
from flask import Flask, request, g, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

SERVICE = os.getenv("SERVICE_NAME", "app")
REQS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
LAT = Histogram("http_request_duration_seconds", "HTTP latency", ["method", "route"],
                buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10))


class JsonFormatter(logging.Formatter):
    def format(self, r):
        d = {"ts": self.formatTime(r, "%Y-%m-%dT%H:%M:%S"), "level": r.levelname,
             "service": SERVICE, "message": r.getMessage()}
        ctx = trace.get_current_span().get_span_context()
        if ctx.is_valid:
            d["trace_id"] = format(ctx.trace_id, "032x")
            d["span_id"] = format(ctx.span_id, "016x")
        d.update(getattr(r, "extra_fields", {}))
        return json.dumps(d)


def create_app():
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    log = logging.getLogger("app")
    log.handlers = [h]
    log.setLevel(logging.INFO)
    log.propagate = False

    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE}))
    ep = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://alloy:4318")
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=ep + "/v1/traces")))
    trace.set_tracer_provider(provider)

    app = Flask(SERVICE)
    FlaskInstrumentor().instrument_app(app, excluded_urls="metrics,health")
    RequestsInstrumentor().instrument()

    @app.before_request
    def _start():
        g.t0 = time.time()

    @app.after_request
    def _end(resp):
        if request.path in ("/metrics", "/health"):
            return resp
        route = request.url_rule.rule if request.url_rule else "unmatched"
        dur = time.time() - g.t0
        REQS.labels(request.method, route, str(resp.status_code)).inc()
        LAT.labels(request.method, route).observe(dur)
        lvl = logging.ERROR if resp.status_code >= 500 else logging.INFO
        log.log(lvl, f"{request.method} {route} -> {resp.status_code} in {dur*1000:.0f}ms")
        return resp

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app, log
