from flask import Flask, jsonify, Response, request, g, render_template_string
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
# OpenTelemetry
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

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# =========================
# Backend
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


@app.before_request
def start_timer():
    g.start_time = time.time()


@app.after_request
def record_metrics(response):

    # Do not count Prometheus scraping as application traffic
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
# Frontend UI
# =========================

@app.route("/")
def home():
    return render_template_string(UI)


# =========================
# Frontend API Proxy
# =========================

@app.route("/api/products")
def api_products():

    response = requests.get(
        f"{PRODUCT_API}/products",
        timeout=5
    )

    return Response(
        response.content,
        status=response.status_code,
        content_type="application/json"
    )


@app.route("/api/products/<int:product_id>")
def api_product(product_id):

    response = requests.get(
        f"{PRODUCT_API}/products/{product_id}",
        timeout=5
    )

    return Response(
        response.content,
        status=response.status_code,
        content_type="application/json"
    )


@app.route("/api/checkout")
def api_checkout():

    response = requests.get(
        f"{PRODUCT_API}/checkout",
        timeout=5
    )

    return Response(
        response.content,
        status=response.status_code,
        content_type="application/json"
    )


# =========================
# Health
# =========================

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "service": "frontend"
    })


# =========================
# Metrics
# =========================

@app.route("/metrics")
def metrics():

    return Response(
        generate_latest(),
        mimetype="text/plain"
    )


# =========================
# HTML / CSS / JavaScript
# =========================

UI = r"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>LUXE — Modern Store</title>


<style>

:root {

    --black: #171717;
    --gray: #777;
    --light: #f6f5f1;
    --border: #e9e7e2;
    --gold: #b28a3b;

}


* {
    box-sizing: border-box;
}


body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: var(--black);

    background: white;

}


/* ================= HEADER ================= */

header {

    height: 72px;

    border-bottom:
        1px solid var(--border);

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 0 6%;

    position: sticky;

    top: 0;

    background: white;

    z-index: 10;

}


.logo {

    font-family: Georgia, serif;

    font-size: 25px;

    letter-spacing: 5px;

}


.nav {

    display: flex;

    gap: 30px;

}


.nav a {

    color: #222;

    text-decoration: none;

    font-size: 14px;

}


.cart-button {

    border: none;

    background: none;

    cursor: pointer;

    font-size: 14px;

}


/* ================= HERO ================= */

.hero {

    margin: 0 6%;

    min-height: 500px;

    background:
        linear-gradient(
            100deg,
            #f0eee8,
            #faf9f6
        );

    display: flex;

    align-items: center;

    padding: 70px 8%;

    position: relative;

    overflow: hidden;

}


.hero::after {

    content: "";

    position: absolute;

    width: 430px;

    height: 430px;

    border-radius: 50%;

    right: 5%;

    top: 40px;

    background: #ddd8ce;

}


.hero-content {

    position: relative;

    z-index: 2;

    max-width: 550px;

}


.eyebrow {

    color: var(--gold);

    font-size: 11px;

    font-weight: bold;

    letter-spacing: 4px;

    text-transform: uppercase;

}


.hero h1 {

    font-family: Georgia, serif;

    font-size: 64px;

    line-height: 1;

    font-weight: normal;

    margin: 20px 0;

}


.hero p {

    color: #666;

    line-height: 1.7;

    max-width: 450px;

}


.shop-button {

    display: inline-block;

    margin-top: 18px;

    padding: 14px 25px;

    background: var(--black);

    color: white;

    text-decoration: none;

}


/* ================= PRODUCTS ================= */

.section {

    padding: 75px 6%;

}


.section-header {

    display: flex;

    justify-content: space-between;

    align-items: end;

    margin-bottom: 30px;

}


.section-header h2 {

    font-family: Georgia, serif;

    font-size: 38px;

    font-weight: normal;

    margin: 0;

}


.section-header span {

    color: var(--gray);

    font-size: 13px;

}


.product-grid {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 24px;

}


.product-card {

    border:
        1px solid var(--border);

    background: white;

}


.product-image {

    height: 280px;

    background:
        linear-gradient(
            135deg,
            #f2f0eb,
            #ddd9d0
        );

    display: flex;

    align-items: center;

    justify-content: center;

    font-family: Georgia, serif;

    font-size: 42px;

    color: #999;

}


.product-info {

    padding: 20px;

}


.product-info h3 {

    margin: 0 0 7px;

    font-size: 17px;

}


.product-info p {

    margin: 0;

    color: #888;

    font-size: 13px;

}


.price {

    margin-top: 15px;

    font-weight: bold;

}


.product-actions {

    display: flex;

    gap: 8px;

    margin-top: 15px;

}


.product-actions button {

    flex: 1;

    padding: 11px;

    border:
        1px solid #ddd;

    background: white;

    cursor: pointer;

}


.product-actions .add {

    background: var(--black);

    color: white;

    border-color: var(--black);

}


/* ================= CART ================= */

.cart-drawer {

    position: fixed;

    right: -430px;

    top: 0;

    width: 430px;

    max-width: 100%;

    height: 100%;

    background: white;

    z-index: 20;

    box-shadow:
        -10px 0 30px #0001;

    padding: 30px;

    transition: 0.3s;

}


.cart-drawer.open {

    right: 0;

}


.close {

    float: right;

    border: none;

    background: none;

    font-size: 24px;

    cursor: pointer;

}


.cart-drawer h2 {

    font-family: Georgia, serif;

    font-size: 32px;

    font-weight: normal;

}


.cart-item {

    display: flex;

    justify-content: space-between;

    padding: 16px 0;

    border-bottom:
        1px solid var(--border);

}


.cart-total {

    display: flex;

    justify-content: space-between;

    margin: 25px 0;

    font-weight: bold;

}


.checkout-button {

    width: 100%;

    padding: 15px;

    background: var(--black);

    color: white;

    border: none;

    cursor: pointer;

}


}


/* ================= MODAL ================= */

.modal {

    display: none;

    position: fixed;

    inset: 0;

    background: #0008;

    margin-top: 40px;
    z-index: 30;
    color: #888;



    align-items: center;


    justify-content: center;

}


.modal.show {

    display: flex;

}


.modal-box {

    background: white;

    padding: 40px;

    width: 500px;

    max-width: 90%;

}


.modal-box h2 {

    font-family: Georgia, serif;

    font-size: 32px;

    font-weight: normal;

}


/* ================= FOOTER ================= */

footer {

    padding: 40px 6%;

    border-top:
        1px solid var(--border);

    color: #888;

    font-size: 12px;

}


/* ================= MOBILE ================= */

@media(max-width: 800px) {

    .nav {
        display: none;
    }

    .hero {

        margin: 0;

        min-height: 450px;

        padding: 50px 7%;

    }

    .hero h1 {
        font-size: 48px;
    }

    .hero::after {
        opacity: 0.3;
        right: -150px;
    }

    .product-grid {
        grid-template-columns: 1fr;
    }

    .section {
        padding: 50px 6%;
    }

}

</style>

</head>


<body>


<!-- HEADER -->

<header>

    <div class="logo">
        LUXE
    </div>


    <nav class="nav">

        <a href="#home">
            Home
        </a>

        <a href="#products">
            Shop
        </a>

    </nav>


    <button
        class="cart-button"
        onclick="openCart()"
    >

        Cart
        (<span id="cart-count">0</span>)

    </button>

</header>



<!-- HERO -->

<main id="home">

<section class="hero">

    <div class="hero-content">

        <div class="eyebrow">
            Curated essentials
        </div>


        <h1>

            Simple things.
            <br>
            Beautifully made.

        </h1>


        <p>

            Discover a refined collection
            of everyday technology and
            essentials, selected for people
            who value quality and clean design.

        </p>


        <a
            href="#products"
            class="shop-button"
        >

            Shop collection

        </a>

    </div>

</section>



<!-- PRODUCTS -->

<section
    class="section"
    id="products"
>

    <div class="section-header">

        <h2>
            Featured products
        </h2>

        <span id="product-count">
            Loading...
        </span>

    </div>


    <div
        class="product-grid"
        id="product-grid"
    >

    </div>

</section>

</main>



<!-- CART -->

<div
    class="cart-drawer"
    id="cart-drawer"
>

    <button
        class="close"
        onclick="closeCart()"
    >
        ×
    </button>


    <h2>
        Your Cart
    </h2>


    <div id="cart-items">

    </div>


    <div class="cart-total">

        <span>
            Total
        </span>

        <span>
            $
            <span id="cart-total">
                0.00
            </span>
        </span>

    </div>


    <button
        class="checkout-button"
        onclick="checkout()"
    >

        Continue to checkout

    </button>

</div>



<!-- ORDER MODAL -->

<div
    class="modal"
    id="order-modal"
>

    <div class="modal-box">

        <h2>
            Order received
        </h2>

        <p>
            Checkout completed successfully.
            Your request was sent to the
            Order Service.
        </p>


        <button
            class="checkout-button"
            onclick="closeModal()"
        >

            Continue shopping

        </button>

    </div>

</div>



<footer>

    LUXE — Modern E-Commerce Demo

</footer>



<script>

let products = [];

let cart = [];


function money(value) {

    return Number(value).toLocaleString(
        undefined,
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );

}


/* =========================
   LOAD PRODUCTS
========================= */

async function loadProducts() {

    try {

        const response =
            await fetch("/api/products");

        products =
            await response.json();


        document.getElementById(
            "product-count"
        ).textContent =
            products.length + " products";


        const grid =
            document.getElementById(
                "product-grid"
            );


        grid.innerHTML =
            products.map(
                (product, index) => `

                <article class="product-card">

                    <div class="product-image">

                        ${String(index + 1).padStart(2, "0")}

                    </div>


                    <div class="product-info">

                        <h3>
                            ${product.name}
                        </h3>


                        <p>
                            Premium collection
                            · In stock
                        </p>


                        <div class="price">

                            $
                            ${money(product.price)}

                        </div>


                        <div class="product-actions">

                            <button
                                onclick="viewProduct(${product.id})"
                            >

                                Details

                            </button>


                            <button
                                class="add"
                                onclick="addToCart(${product.id})"
                            >

                                Add to cart

                            </button>

                        </div>

                    </div>

                </article>

            `
            ).join("");


    } catch (error) {

        document.getElementById(
            "product-grid"
        ).innerHTML =

            "<p>Unable to load products.</p>";

        console.error(error);

    }

}


/* =========================
   PRODUCT DETAILS
========================= */

async function viewProduct(id) {

    const response =
        await fetch(
            "/api/products/" + id
        );


    const product =
        await response.json();


    alert(
        product.name +
        "\n\nPrice: $" +
        money(product.price)
    );

}


/* =========================
   ADD TO CART
========================= */

function addToCart(id) {

    const product =
        products.find(
            item => item.id === id
        );


    if (!product) {
        return;
    }


    cart.push(product);

    updateCart();

    openCart();

}


/* =========================
   UPDATE CART
========================= */

function updateCart() {

    document.getElementById(
        "cart-count"
    ).textContent =
        cart.length;


    const container =
        document.getElementById(
            "cart-items"
        );


    if (cart.length === 0) {

        container.innerHTML =
            '<div class="empty">Your cart is empty.</div>';

    } else {

        container.innerHTML =
            cart.map(
                product => `

                <div class="cart-item">

                    <span>
                        ${product.name}
                    </span>

                    <span>
                        $${money(product.price)}
                    </span>

                </div>

            `
            ).join("");

    }


    const total =
        cart.reduce(
            (sum, product) =>
                sum + Number(product.price),
            0
        );


    document.getElementById(
        "cart-total"
    ).textContent =
        money(total);

}


/* =========================
   CART OPEN / CLOSE
========================= */

function openCart() {

    document.getElementById(
        "cart-drawer"
    ).classList.add("open");

}


function closeCart() {

    document.getElementById(
        "cart-drawer"
    ).classList.remove("open");

}


/* =========================
   CHECKOUT
========================= */

async function checkout() {

    if (cart.length === 0) {

        alert(
            "Your cart is empty."
        );

        return;

    }


    try {

        const response =
            await fetch(
                "/api/checkout"
            );


        if (!response.ok) {

            throw new Error(
                "Checkout failed"
            );

        }


        await response.json();


        cart = [];

        updateCart();

        closeCart();


        document.getElementById(
            "order-modal"
        ).classList.add("show");


    } catch (error) {

        alert(
            "Checkout failed. Please try again."
        );

        console.error(error);

    }

}


function closeModal() {

    document.getElementById(
        "order-modal"
    ).classList.remove("show");

}


/* =========================
   START
========================= */

loadProducts();

updateCart();

</script>


</body>

</html>
"""


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
