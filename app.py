import os, json, re, time, hmac, secrets, threading, ssl, socket
import urllib.request, urllib.error
from collections import deque
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, render_template, render_template_string, request, session, redirect, abort
from dotenv import load_dotenv
from extensions import db, migrate
from models import Artist, Album, Collection, CollectionItem, RandomEntry, Experiment, SiteSetting
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, RunRealtimeReportRequest,
    FilterExpression, FilterExpressionList, Filter, OrderBy)

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# PostgreSQL is supplied by Railway through DATABASE_URL. A local SQLite
# fallback keeps development possible without requiring a cloud database.
database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    database_url = "sqlite:///" + os.path.join(BASE, "ebstian-local.db")

app.config.update(
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
)
db.init_app(app)
migrate.init_app(app, db)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Falta SECRET_KEY. Configúrala en el entorno antes de iniciar Flask.")
app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.getenv("RAILWAY_ENVIRONMENT")),
    PERMANENT_SESSION_LIFETIME=__import__("datetime").timedelta(hours=12),
)

PASSWORD = os.getenv("APP_PASSWORD", "")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
DEFAULT_EVENTS = ["view_item_list", "view_item", "add_to_cart", "view_cart",
                  "begin_checkout", "generate_lead", "search", "submit_review"]
_cache, _client = {}, None


def client():
    global _client
    if _client is None:
        raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if raw:
            creds = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
            _client = BetaAnalyticsDataClient(credentials=creds)
        else:  # usa GOOGLE_APPLICATION_CREDENTIALS (ruta al .json) o gcloud auth application-default
            _client = BetaAnalyticsDataClient()
    return _client


SITES_FILE = os.getenv("SITES_FILE", os.path.join(BASE, "sites.json"))
_lock = threading.Lock()


def load_sites():
    try:
        with open(SITES_FILE, encoding="utf-8") as f:
            return json.load(f)["sites"]
    except FileNotFoundError:
        return []


def save_sites(sites):
    with _lock:
        tmp = SITES_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"sites": sites}, f, indent=2, ensure_ascii=False)
        os.replace(tmp, SITES_FILE)
    _cache.clear()


def sa_email():
    try:
        raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not raw:
            with open(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""), encoding="utf-8") as f:
                raw = f.read()
        return json.loads(raw).get("client_email", "")
    except Exception:
        return ""


def get_site(site_id):
    return {s["id"]: s for s in load_sites()}.get(site_id or "")


def _filter(site, events=None):
    parts = []
    if site.get("hostname"):
        parts.append(FilterExpression(filter=Filter(
            field_name="hostName",
            string_filter=Filter.StringFilter(value=site["hostname"], match_type=Filter.StringFilter.MatchType.EXACT))))
    if events:
        parts.append(FilterExpression(filter=Filter(
            field_name="eventName", in_list_filter=Filter.InListFilter(values=events))))
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else FilterExpression(and_group=FilterExpressionList(expressions=parts))


def _rows(res, dims, mets):
    rows = []
    for r in res.rows:
        row = {d: v.value for d, v in zip(dims, r.dimension_values)}
        row.update({m: float(v.value) for m, v in zip(mets, r.metric_values)})
        rows.append(row)
    return rows


def run(site, dims, mets, start, end, limit=10, order=None, events=None):
    req = RunReportRequest(
        property=f"properties/{site['property_id']}",
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in mets],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimension_filter=_filter(site, events), limit=limit)
    if order:
        req.order_bys = [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order), desc=True)]
    elif "date" in dims:
        req.order_bys = [OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))]
    elif "hour" in dims:
        req.order_bys = [OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"))]
    return _rows(client().run_report(req), dims, mets)


def rt(site, dims, mets, limit=10):
    res = client().run_realtime_report(RunRealtimeReportRequest(
        property=f"properties/{site['property_id']}", limit=limit,
        dimensions=[Dimension(name=d) for d in dims], metrics=[Metric(name=m) for m in mets]))
    return _rows(res, dims, mets)


def gather(jobs):
    out, errors = {}, {}

    def safe(k, fn):
        try:
            out[k] = fn()
        except Exception as ex:
            out[k], errors[k] = None, str(ex)[:300]

    with ThreadPoolExecutor(max_workers=8) as pool:
        for k, fn in jobs.items():
            pool.submit(safe, k, fn)
    out["errors"], out["updated"] = errors, int(time.time())
    return out


def build(site, days):
    s, e = f"{days}daysAgo", "today"
    ps, pe = f"{days * 2}daysAgo", f"{days + 1}daysAgo"
    K = ["activeUsers", "newUsers", "sessions", "screenPageViews", "engagementRate", "averageSessionDuration"]
    ev = site.get("events", DEFAULT_EVENTS)
    return gather({
        "kpis": lambda: run(site, [], K, s, e, 1),
        "prev": lambda: run(site, [], K, ps, pe, 1),
        "daily": lambda: run(site, ["date"], ["activeUsers", "sessions", "screenPageViews"], s, e, 400),
        "pages": lambda: run(site, ["pagePath"], ["screenPageViews"], s, e, 10, "screenPageViews"),
        "channels": lambda: run(site, ["sessionDefaultChannelGroup"], ["sessions"], s, e, 8, "sessions"),
        "devices": lambda: run(site, ["deviceCategory"], ["activeUsers"], s, e, 5, "activeUsers"),
        "geo": lambda: run(site, ["country", "region", "city"], ["activeUsers"], s, e, 120, "activeUsers"),
        "hours": lambda: run(site, ["hour"], ["sessions"], s, e, 24),
        "events": lambda: run(site, ["eventName"], ["eventCount"], s, e, 25, "eventCount", ev),
        "items": lambda: run(site, ["itemName"], ["itemsViewed", "itemsAddedToCart"], s, e, 10, "itemsViewed"),
        "searches": lambda: run(site, ["searchTerm"], ["eventCount"], s, e, 10, "eventCount"),
    })


def build_live(site):
    return gather({
        "total": lambda: rt(site, [], ["activeUsers"], 1),
        "minutes": lambda: rt(site, ["minutesAgo"], ["activeUsers"], 30),
        "pages": lambda: rt(site, ["unifiedPagePathScreen"], ["activeUsers"], 8),
        "cities": lambda: rt(site, ["city"], ["activeUsers"], 8),
        "events": lambda: rt(site, ["eventName"], ["eventCount"], 10),
    })


def _token_ok():
    site = get_site(request.args.get("site") or (request.view_args or {}).get("site_id"))
    tok = (site or {}).get("share_token")
    return bool(tok) and hmac.compare_digest(request.args.get("t", ""), tok)


@app.before_request
def guard():
    """Public routes stay public; ST Monitor and its APIs require a session.

    Client reports remain accessible only with their individual share token.
    """
    public_endpoints = {"home", "login", "static", "manifest", "sw"}

    if request.endpoint in public_endpoints:
        return

    if request.endpoint in ("client_report", "api_report") and _token_ok():
        return

    # Fail closed: a missing APP_PASSWORD must never expose private services.
    if not PASSWORD:
        if request.path.startswith("/api/"):
            return jsonify(error="Autenticación no configurada"), 503
        abort(503)

    if session.get("ok"):
        return

    if request.path.startswith("/api/"):
        return jsonify(error="Sesión expirada"), 401

    return redirect("/login")


LOGIN = """<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Entrar</title>
<style>body{font-family:system-ui,sans-serif;background:#0A101C;color:#E8EEF8;display:grid;place-items:center;min-height:100vh;margin:0}
form{display:grid;gap:12px;width:min(320px,88vw)}h1{font-size:22px;margin:0 0 4px}
input,button{padding:14px;border-radius:10px;border:1px solid #1E2A40;font-size:16px}
input{background:#111A2B;color:inherit}button{background:#4C8DFF;color:#06122B;font-weight:700;border:0;cursor:pointer}
p{color:#F5B544;margin:0;font-size:14px}</style>
<form method="post"><h1>ST Monitor</h1>{% if err %}<p>Contraseña incorrecta</p>{% endif %}
<input type="password" name="password" placeholder="Contraseña" autofocus required><button>Entrar</button></form>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if not PASSWORD:
        abort(503, description="Configura APP_PASSWORD en las variables de entorno.")
    if session.get("ok"):
        return redirect("/private")
    if request.method == "POST":
        if hmac.compare_digest(request.form.get("password", ""), PASSWORD):
            session["ok"] = True
            session.permanent = True
            return redirect("/private")
        return render_template_string(LOGIN, err=True), 401
    return render_template_string(LOGIN, err=False)


@app.route("/")
def home():
    """Public Ebstian homepage."""
    # Accept only Spotify embed targets from Spotify itself. The operator can
    # provide a playlist, album, or artist URL through SPOTIFY_URL in Railway.
    spotify_embed_url = None
    spotify_url = os.getenv("SPOTIFY_URL", "").strip()
    if spotify_url:
        parsed = urlparse(spotify_url)
        match = re.match(r"^/(playlist|album|artist|show|episode)/([A-Za-z0-9]+)$", parsed.path)
        if parsed.scheme == "https" and parsed.hostname == "open.spotify.com" and match:
            spotify_embed_url = f"https://open.spotify.com/embed/{match.group(1)}/{match.group(2)}?utm_source=generator"
    return render_template("index.html", spotify_embed_url=spotify_embed_url)


@app.route("/private")
def dashboard():
    """Private ST Monitor dashboard."""
    sites = [
        {k: s.get(k) for k in ("id", "name", "url")}
        | {"token": s.get("share_token", "")}
        for s in load_sites()
    ]
    return render_template("dashboard.html", sites=sites, client=None)


@app.route("/reporte/<site_id>")
def client_report(site_id):
    site = get_site(site_id) or abort(404)
    public = [{k: site.get(k) for k in ("id", "name", "url")}]
    return render_template("dashboard.html", sites=public, client={"site": site_id, "t": request.args.get("t", "")})


@app.route("/api/report")
def api_report():
    site = get_site(request.args.get("site"))
    if not site:
        return jsonify(error="Sitio no encontrado en sites.json"), 404
    days = min(max(int(request.args.get("days", 28)), 1), 365)
    key = (site["id"], days)
    hit = _cache.get(key)
    if hit and not request.args.get("refresh") and time.time() - hit[0] < CACHE_TTL:
        return jsonify(hit[1])
    data = build(site, days)
    if not data["errors"].get("kpis"):
        _cache[key] = (time.time(), data)
    return jsonify(data)


@app.route("/api/live")
def api_live():
    site = get_site(request.args.get("site"))
    if not site:
        return jsonify(error="Sitio no encontrado en sites.json"), 404
    hit = _cache.get(("live", site["id"]))
    if hit and time.time() - hit[0] < 20:
        return jsonify(hit[1])
    data = build_live(site)
    _cache[("live", site["id"])] = (time.time(), data)
    return jsonify(data)


_health, _ssl, _hist = {}, {}, {}


def ssl_days(host):
    hit = _ssl.get(host)
    if hit and time.time() - hit[0] < 21600:  # se revisa cada 6 horas
        return hit[1]
    try:
        with socket.create_connection((host, 443), timeout=6) as raw:
            with ssl.create_default_context().wrap_socket(raw, server_hostname=host) as s:
                days = int((ssl.cert_time_to_seconds(s.getpeercert()["notAfter"]) - time.time()) // 86400)
    except Exception:
        days = None
    _ssl[host] = (time.time(), days)
    return days


def check_site(site):
    """¿El sitio responde? Cuenta como en línea si contesta con un código menor a 500."""
    url = site.get("url") or ""
    if not url:
        return {"up": None}
    hit = _health.get(site["id"])
    if hit and time.time() - hit[0] < 45:
        return hit[1]
    t0, res, code = time.time(), {}, None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ST-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            code = r.status
    except urllib.error.HTTPError as ex:
        code = ex.code
    except Exception as ex:
        res["error"] = str(getattr(ex, "reason", ex))[:80]
    res.update(code=code, up=code is not None and code < 500,
               ms=int((time.time() - t0) * 1000) if code is not None else None)
    host = urlparse(url).hostname
    if url.startswith("https") and host:
        res["ssl_days"] = ssl_days(host)
    h = _hist.setdefault(site["id"], deque(maxlen=20))
    h.append(res["up"])
    res["hist"] = list(h)
    _health[site["id"]] = (time.time(), res)
    return res


def site_overview(site, days):
    s, e = f"{days}daysAgo", "today"
    ps, pe = f"{days * 2}daysAgo", f"{days + 1}daysAgo"
    K = ["activeUsers", "sessions", "screenPageViews"]
    out = gather({
        "kpis": lambda: run(site, [], K, s, e, 1),
        "prev": lambda: run(site, [], K, ps, pe, 1),
        "daily": lambda: run(site, ["date"], ["activeUsers"], s, e, 400),
        "leads": lambda: run(site, ["eventName"], ["eventCount"], s, e, 1, None, ["generate_lead"]),
        "live": lambda: None if site.get("hostname") else rt(site, [], ["activeUsers"], 1),
        "health": lambda: check_site(site),
    })
    out.update(id=site["id"], name=site["name"], url=site.get("url", ""))
    return out


@app.route("/api/overview")
def api_overview():
    days = min(max(int(request.args.get("days", 28)), 1), 365)
    hit = _cache.get(("ov", days))
    if hit and not request.args.get("refresh") and time.time() - hit[0] < 45:
        return jsonify(hit[1])
    sites = load_sites()
    with ThreadPoolExecutor(max_workers=6) as pool:
        res = list(pool.map(lambda s: site_overview(s, days), sites))
    data = {"sites": res, "updated": int(time.time())}
    _cache[("ov", days)] = (time.time(), data)
    return jsonify(data)


def _clean(d, old=None):
    name = str(d.get("name", "")).strip()[:60]
    pid = re.sub(r"\D", "", str(d.get("property_id", "")))
    if not name or not pid:
        return None, "Falta el nombre o el Property ID (solo números)."
    url = str(d.get("url", "")).strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    site = {"id": (old or {}).get("id") or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "sitio",
            "name": name, "url": url, "property_id": pid,
            "share_token": (old or {}).get("share_token") or secrets.token_urlsafe(12)}
    if str(d.get("hostname", "")).strip():
        site["hostname"] = str(d["hostname"]).strip()
    events = [e for e in re.split(r"[,\s]+", str(d.get("events", ""))) if e]
    if events:
        site["events"] = events
    return site, None


@app.route("/api/sites", methods=["GET", "POST"])
def api_sites():
    sites = load_sites()
    if request.method == "GET":
        return jsonify(sites=sites, sa_email=sa_email(), default_events=DEFAULT_EVENTS)
    body = request.get_json(silent=True) or {}
    old = next((s for s in sites if s["id"] == body.get("id")), None)
    site, err = _clean(body, old)
    if err:
        return jsonify(error=err), 400
    if old:
        sites[sites.index(old)] = site
    else:
        ids, base, n = {s["id"] for s in sites}, site["id"], 2
        while site["id"] in ids:
            site["id"], n = f"{base}-{n}", n + 1
        sites.append(site)
    save_sites(sites)
    try:
        run(site, [], ["activeUsers"], "7daysAgo", "today", 1)
        test = "ok"
    except Exception as ex:
        test = str(ex)[:300]
    return jsonify(site=site, test=test)


@app.route("/api/sites/<site_id>", methods=["DELETE"])
def api_site_delete(site_id):
    save_sites([s for s in load_sites() if s["id"] != site_id])
    return jsonify(ok=True)


@app.route("/api/sites/<site_id>/token", methods=["POST"])
def api_site_token(site_id):
    sites = load_sites()
    for s in sites:
        if s["id"] == site_id:
            s["share_token"] = secrets.token_urlsafe(12)
    save_sites(sites)
    return jsonify(sites=sites)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/manifest.webmanifest")
def manifest():
    icons = [{"src": f"/static/icon-{n}.png", "sizes": f"{n}x{n}", "type": "image/png", "purpose": "any maskable"} for n in (192, 512)]
    return jsonify(name="ST Monitor", short_name="ST Monitor", start_url="/", display="standalone",
                   background_color="#0A101C", theme_color="#2563EB", lang="es", icons=icons)


SW = """self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(clients.claim()));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);
if(e.request.method!=='GET'||u.origin!==location.origin||!u.pathname.startsWith('/static/'))return;
e.respondWith(caches.open('st-v1').then(async c=>(await c.match(e.request))||fetch(e.request).then(r=>{c.put(e.request,r.clone());return r})))});"""


@app.route("/sw.js")
def sw():
    return app.response_class(SW, mimetype="application/javascript", headers={"Cache-Control": "no-cache"})


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", "5000")))