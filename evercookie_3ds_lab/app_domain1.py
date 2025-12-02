from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
import requests
import json

app = FastAPI()

IDENTSERVER = "http://identserver.local:8001"


# Главная

@app.get("/", response_class=HTMLResponse)
async def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>Evercookie 3DS Lab</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; }
            a { color: #4b32c3; }
            ul { line-height: 1.6; }
        </style>
    </head>
    <body>
        <h1>Evercookie + 3DS Method Lab</h1>
        <p>Стенд для проверки поведения cross-origin iframe и same-origin proxy.</p>
        <ul>
            <li><a href="/test-cross">Стенд A: CROSS-ORIGIN iframe (3rd-party, 3DS Method)</a></li>
            <li><a href="/test-proxy">Стенд B: SAME-ORIGIN PROXY iframe (как Stape/Taggrs)</a></li>
            <li><a href="/view-logs">Логи identserver (каналы хранения)</a></li>
            <li><a href="/test-results">Результаты автотестов Safari vs Chrome</a></li>
        </ul>
    </body>
    </html>
    """
    return HTMLResponse(html)


# STAND A: CROSS-ORIGIN

@app.get("/test-cross", response_class=HTMLResponse)
async def test_cross():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>Стенд A — CROSS-ORIGIN iframe</title>
        <style>
            body {{ font-family: -apple-system,BlinkMacSystemFont,sans-serif; padding: 20px; }}
            #uid-box {{ margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
            pre {{ font-size: 12px; background: #f7f7fb; padding: 10px; border-radius: 6px; overflow-x:auto; }}
        </style>
    </head>
    <body>
        <h1>Стенд A — CROSS-ORIGIN iframe (identserver.local)</h1>
        <p>Эмулируем реальный 3DS Method: iframe загружает third-party домен.</p>

        <iframe
            src="{IDENTSERVER}/3ds-method-cross"
            style="width:0;height:0;border:0;visibility:hidden"
            sandbox="allow-scripts allow-same-origin">
        </iframe>

        <div id="uid-box">
            <p><strong>UID:</strong> <span id="uid-value">жду…</span></p>
            <p><strong>mode:</strong> <span id="mode-value">?</span></p>
            <pre id="channels">{{}}</pre>
        </div>

        <script>
        window.addEventListener("message", function(event) {{
            if (!event.data || event.data.type !== "DEVICE_ID") return;
            document.getElementById("uid-value").textContent = event.data.id || "(пусто)";
            document.getElementById("mode-value").textContent = event.data.mode || "";
            document.getElementById("channels").textContent =
                JSON.stringify(event.data.channels, null, 2);
            console.log("CROSS DEVICE_ID:", event.data);
        }});
        </script>

        <p><a href="/">Назад</a></p>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ---------- STAND B: SAME-ORIGIN PROXY ----------

@app.get("/proxy-cache.png")
async def proxy_cache():
    """
    Проксируем PNG с identserver, но под доменом domain1.local.
    Это имитация Same-Origin/Own CDN подхода.
    """
    r = requests.get(f"{IDENTSERVER}/cache.png", timeout=5)
    resp = Response(content=r.content, media_type="image/png")
    for h in ["ETag", "Cache-Control", "Expires"]:
        if h in r.headers:
            resp.headers[h] = r.headers[h]
    return resp


@app.get("/3ds-method-proxy", response_class=HTMLResponse)
async def three_ds_method_proxy():
    """
    3DS Method, но уже как first-party (domain1.local).
    Всё выполняется здесь, логируем на identserver.
    """
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>3DS Method - PROXY</title>
</head>
<body>
<script>
// --- IndexedDB helpers ---
function idb_get(dbName, storeName, key) {{
    return new Promise((resolve) => {{
        const req = indexedDB.open(dbName, 1);
        req.onupgradeneeded = () => {{
            let db = req.result;
            db.createObjectStore(storeName);
        }};
        req.onsuccess = () => {{
            let db = req.result;
            const tx = db.transaction(storeName, "readonly");
            const store = tx.objectStore(storeName);
            const r = store.get(key);
            r.onsuccess = () => resolve(r.result || null);
            r.onerror = () => resolve(null);
        }};
        req.onerror = () => resolve(null);
    }});
}}

function idb_set(dbName, storeName, key, value) {{
    return new Promise((resolve) => {{
        const req = indexedDB.open(dbName, 1);
        req.onupgradeneeded = () => {{
            let db = req.result;
            db.createObjectStore(storeName);
        }};
        req.onsuccess = () => {{
            let db = req.result;
            const tx = db.transaction(storeName, "readwrite");
            const store = tx.objectStore(storeName);
            store.put(value, key);
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => resolve(false);
        }};
        req.onerror = () => resolve(false);
    }});
}}

// --- PNG cache через proxy-cache.png ---
class PNGCache {{
    constructor(endpoint) {{
        this.endpoint = endpoint;
        this.canvasWidth = 200;
    }}
    loadUID() {{
        return new Promise((resolve) => {{
            const img = new Image();
            img.onload = () => {{
                const canvas = document.createElement("canvas");
                canvas.width = this.canvasWidth;
                canvas.height = 1;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0);
                const pix = ctx.getImageData(0, 0, this.canvasWidth, 1).data;
                let uid = "";
                for (let i = 0; i < pix.length; i += 4) {{
                    const r = pix[i], g = pix[i+1], b = pix[i+2];
                    if (r === 0 && g === 0 && b === 0) break;
                    uid += String.fromCharCode(r);
                    if (g !== 0) uid += String.fromCharCode(g);
                    if (b !== 0) uid += String.fromCharCode(b);
                }}
                resolve(uid || null);
            }};
            img.onerror = () => resolve(null);
            img.src = "/proxy-cache.png";
        }});
    }}
}}

(async () => {{
    let cookieVal = null;
    try {{
        const m = document.cookie.match(/device_id=([^;]+)/);
        if (m) cookieVal = m[1];
    }} catch(e) {{}}

    let lsVal = null;
    try {{ lsVal = localStorage.getItem("device_id"); }} catch(e){{}}

    let ssVal = null;
    try {{ ssVal = sessionStorage.getItem("device_id"); }} catch(e){{}}

    let idbVal = null;
    try {{ idbVal = await idb_get("evercookieDB","store","device_id"); }} catch(e){{}}

    const png = new PNGCache("/proxy-cache.png");
    let pngVal = null;
    try {{ pngVal = await png.loadUID(); }} catch(e){{}}

    const candidates = [cookieVal, lsVal, ssVal, idbVal, pngVal].filter(Boolean);
    let finalUID = candidates.length > 0 ? candidates[0] : null;
    if (!finalUID) {{
        finalUID = pngVal || Math.random().toString(16).slice(2, 18);
    }}

    try {{ document.cookie = "device_id=" + finalUID + "; path=/; SameSite=Lax"; }} catch(e){{}}
    try {{ localStorage.setItem("device_id", finalUID); }} catch(e){{}}
    try {{ sessionStorage.setItem("device_id", finalUID); }} catch(e){{}}
    try {{ await idb_set("evercookieDB","store","device_id", finalUID); }} catch(e){{}}

    const channels = {{
        cookie: cookieVal,
        localStorage: lsVal,
        sessionStorage: ssVal,
        indexedDB: idbVal,
        pngCache: pngVal
    }};

    window.parent.postMessage({{
        type: "DEVICE_ID",
        id: finalUID,
        mode: "proxy",
        channels
    }}, "*");

    fetch("{IDENTSERVER}/log", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{
            uid: finalUID,
            mode: "proxy",
            channels,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        }})
    }}).catch(()=>{{}});
)();
</script>
</body>
</html>
"""
    return HTMLResponse(html)


@app.get("/test-proxy", response_class=HTMLResponse)
async def test_proxy():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>Стенд B — SAME-ORIGIN PROXY iframe</title>
        <style>
            body { font-family: -apple-system,BlinkMacSystemFont,sans-serif; padding: 20px; }
            #uid-box { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
            pre { font-size: 12px; background: #f7f7fb; padding: 10px; border-radius: 6px; overflow-x:auto; }
        </style>
    </head>
    <body>
        <h1>Стенд B — SAME-ORIGIN PROXY iframe</h1>
        <p>Здесь iframe first-party (domain1.local), а PNG тянется через proxy.</p>

        <iframe
            src="/3ds-method-proxy"
            style="width:0;height:0;border:0;visibility:hidden"
            sandbox="allow-scripts allow-same-origin">
        </iframe>

        <div id="uid-box">
            <p><strong>UID:</strong> <span id="uid-value">жду…</span></p>
            <p><strong>mode:</strong> <span id="mode-value">?</span></p>
            <pre id="channels">{{}}</pre>
        </div>

        <script>
        window.addEventListener("message", function(event) {
            if (!event.data || event.data.type !== "DEVICE_ID") return;
            document.getElementById("uid-value").textContent = event.data.id || "(пусто)";
            document.getElementById("mode-value").textContent = event.data.mode || "";
            document.getElementById("channels").textContent =
                JSON.stringify(event.data.channels, null, 2);
            console.log("PROXY DEVICE_ID:", event.data);
        });
        </script>

        <p><a href="/">Назад</a></p>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ---------- Просмотр логов ----------

@app.get("/view-logs", response_class=HTMLResponse)
def view_logs():
    try:
        r = requests.get(f"{IDENTSERVER}/logs", timeout=5)
        logs = r.json()
    except:
        logs = []

    rows = ""
    for log in logs:
        rows += f"""
        <tr>
            <td>{log.get("timestamp","")}</td>
            <td>{log.get("mode","")}</td>
            <td>{log.get("uid","")}</td>
            <td><pre>{json.dumps(log.get("channels"), indent=2, ensure_ascii=False)}</pre></td>
            <td>{log.get("userAgent","")}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>Логи identserver</title>
        <style>
            body {{ font-family: -apple-system,BlinkMacSystemFont,sans-serif; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
            th, td {{ border: 1px solid #ddd; padding: 6px; vertical-align: top; }}
            th {{ background: #f5f5fa; }}
            pre {{ margin: 0; white-space: pre-wrap; word-break: break-all; }}
        </style>
    </head>
    <body>
        <h1>Логи identserver</h1>
        <table>
            <tr>
                <th>Время</th>
                <th>mode</th>
                <th>UID</th>
                <th>Каналы</th>
                <th>User-Agent</th>
            </tr>
            {rows or "<tr><td colspan='5'>Пока нет логов</td></tr>"}
        </table>
        <p><a href="/">Назад</a></p>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ---------- Страница результатов автотестов + график ----------

@app.get("/test-results", response_class=HTMLResponse)
def test_results_page():
    try:
        r = requests.get(f"{IDENTSERVER}/test-results", timeout=5)
        results = r.json()
    except:
        results = []

    # Таблица
    table_rows = ""
    chart_points = []

    for row in results:
        browser = row.get("browser")
        stand = row.get("stand")
        uid1 = row.get("uid1")
        uid2 = row.get("uid2")
        stable = "OK" if uid1 and uid2 and uid1 == uid2 else "CHANGED"

        table_rows += f"""
        <tr>
            <td>{browser}</td>
            <td>{stand}</td>
            <td>{uid1}</td>
            <td>{uid2}</td>
            <td>{stable}</td>
        </tr>
        """

        chart_points.append({
            "label": f"{browser} {stand}",
            "value": 1 if stable == "OK" else 0
        })

    chart_json = json.dumps(chart_points, ensure_ascii=False)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>Результаты автотестов</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: -apple-system,BlinkMacSystemFont,sans-serif; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 6px; font-size: 13px; }}
            th {{ background: #f5f5fa; }}
            #chart-container {{ max-width: 700px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>Результаты автотестов Safari vs Chrome</h1>
        <p>1 = UID стабильный между двумя запусками, 0 = UID изменился.</p>

        <div id="chart-container">
            <canvas id="resultsChart"></canvas>
        </div>

        <table>
            <tr>
                <th>Браузер</th>
                <th>Стенд</th>
                <th>UID (1 запуск)</th>
                <th>UID (2 запуск)</th>
                <th>Стабильность</th>
            </tr>
            {table_rows or "<tr><td colspan='5'>Пока нет результатов</td></tr>"}
        </table>

        <p><a href="/">Назад</a></p>

        <script>
        const chartData = {chart_json};

        const labels = chartData.map(p => p.label);
        const values = chartData.map(p => p.value);

        const ctx = document.getElementById('resultsChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{
                    label: 'Стабильность UID (1 = стабильный)',
                    data: values
                }}]
            }},
            options: {{
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1,
                            callback: function(value) {{
                                return value === 1 ? '1 (стабилен)' : '0 (меняется)';
                            }}
                        }},
                        max: 1
                    }}
                }}
            }}
        }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)
