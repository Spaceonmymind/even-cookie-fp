from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
import secrets
import json
import os

app = FastAPI()

LOGFILE = "logs.jsonl"
TEST_RESULTS_FILE = "test_results.json"


# Утилиты

def generate_uid() -> str:
    return secrets.token_hex(16)


def uid_to_png(uid: str, width: int = 200, height: int = 1) -> bytes:
    """
    Кодируем UID (ascii-строка) в PNG: 3 символа на пиксель.
    Остальные пиксели заполняем (0,0,0) как маркер конца.
    """
    img = Image.new("RGB", (width, height), (255, 255, 255))
    pixels = img.load()

    data = uid.encode("ascii")
    i = 0
    for x in range(width):
        if i >= len(data):
            pixels[x, 0] = (0, 0, 0)
            continue
        r = data[i] if i < len(data) else 0
        g = data[i + 1] if i + 1 < len(data) else 0
        b = data[i + 2] if i + 2 < len(data) else 0
        pixels[x, 0] = (r, g, b)
        i += 3

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@app.get("/cache.png")
async def cache_png(request: Request):
    """
    Third-party ресурс с длинным кэшем.
    Safari / Chrome кэшируют его по URL + ETag (partitioned).
    """
    etag_header = request.headers.get("if-none-match")
    if etag_header:
        uid = etag_header.strip().strip('"')
    else:
        uid = generate_uid()

    png_bytes = uid_to_png(uid)

    resp = Response(png_bytes, media_type="image/png")
    resp.headers["ETag"] = f'"{uid}"'
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    resp.headers["Expires"] = (
        datetime.utcnow() + timedelta(days=365)
    ).strftime("%a, %d %b %Y %H:%M:%S GMT")
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

@app.get("/3ds-method-cross", response_class=HTMLResponse)
async def three_ds_method_cross():
    """
    Страница, которую загружает cross-origin iframe у domain1.
    Здесь мы пробуем cookie/localStorage/sessionStorage/IndexedDB/PNG
    и постим результат в родителя + логируем.
    """
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>3DS Method - CROSS</title>
</head>
<body>
<script>
// --- IndexedDB helpers ---
function idb_get(dbName, storeName, key) {
    return new Promise((resolve) => {
        const req = indexedDB.open(dbName, 1);
        req.onupgradeneeded = () => {
            let db = req.result;
            db.createObjectStore(storeName);
        };
        req.onsuccess = () => {
            let db = req.result;
            const tx = db.transaction(storeName, "readonly");
            const store = tx.objectStore(storeName);
            const r = store.get(key);
            r.onsuccess = () => resolve(r.result || null);
            r.onerror = () => resolve(null);
        };
        req.onerror = () => resolve(null);
    });
}

function idb_set(dbName, storeName, key, value) {
    return new Promise((resolve) => {
        const req = indexedDB.open(dbName, 1);
        req.onupgradeneeded = () => {
            let db = req.result;
            db.createObjectStore(storeName);
        };
        req.onsuccess = () => {
            let db = req.result;
            const tx = db.transaction(storeName, "readwrite");
            const store = tx.objectStore(storeName);
            store.put(value, key);
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => resolve(false);
        };
        req.onerror = () => resolve(false);
    });
}

// --- PNG cache ---
class PNGCache {
    constructor(endpoint) {
        this.endpoint = endpoint;
        this.canvasWidth = 200;
    }
    loadUID() {
        return new Promise((resolve) => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
                const canvas = document.createElement("canvas");
                canvas.width = this.canvasWidth;
                canvas.height = 1;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0);
                const pix = ctx.getImageData(0, 0, this.canvasWidth, 1).data;
                let uid = "";
                for (let i = 0; i < pix.length; i += 4) {
                    const r = pix[i], g = pix[i+1], b = pix[i+2];
                    if (r === 0 && g === 0 && b === 0) break;
                    uid += String.fromCharCode(r);
                    if (g !== 0) uid += String.fromCharCode(g);
                    if (b !== 0) uid += String.fromCharCode(b);
                }
                resolve(uid || null);
            };
            img.onerror = () => resolve(null);
            img.src = "/cache.png";
        });
    }
}

// --- main ---
(async () => {
    let cookieVal = null;
    try {
        const m = document.cookie.match(/device_id=([^;]+)/);
        if (m) cookieVal = m[1];
    } catch(e) {}

    let lsVal = null;
    try { lsVal = localStorage.getItem("device_id"); } catch(e){}

    let ssVal = null;
    try { ssVal = sessionStorage.getItem("device_id"); } catch(e){}

    let idbVal = null;
    try { idbVal = await idb_get("evercookieDB","store","device_id"); } catch(e){}

    const png = new PNGCache("/cache.png");
    let pngVal = null;
    try { pngVal = await png.loadUID(); } catch(e){}

    const candidates = [cookieVal, lsVal, ssVal, idbVal, pngVal].filter(Boolean);
    let finalUID = candidates.length > 0 ? candidates[0] : null;
    if (!finalUID) {
        // PNG-значение предпочтительнее, если оно есть
        finalUID = pngVal || Math.random().toString(16).slice(2, 18);
    }

    try { document.cookie = "device_id=" + finalUID + "; path=/; SameSite=None; Secure"; } catch(e){}
    try { localStorage.setItem("device_id", finalUID); } catch(e){}
    try { sessionStorage.setItem("device_id", finalUID); } catch(e){}
    try { await idb_set("evercookieDB","store","device_id", finalUID); } catch(e){}

    const channels = {
        cookie: cookieVal,
        localStorage: lsVal,
        sessionStorage: ssVal,
        indexedDB: idbVal,
        pngCache: pngVal
    };

    // postMessage родителю
    window.parent.postMessage({
        type: "DEVICE_ID",
        id: finalUID,
        mode: "cross",
        channels
    }, "*");

    // лог на сервер
    fetch("/log", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            uid: finalUID,
            mode: "cross",
            channels,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        })
    }).catch(()=>{});
})();
</script>
</body>
</html>
"""
    return HTMLResponse(html)

@app.post("/log")
async def write_log(request: Request):
    data = await request.json()
    line = json.dumps(data, ensure_ascii=False)
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    resp = JSONResponse({"status": "ok"})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.get("/logs")
async def get_logs():
    if not os.path.exists(LOGFILE):
        return []
    out = []
    with open(LOGFILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except:
                pass
    return out

@app.post("/save-test-result")
async def save_test_result(request: Request):
    data = await request.json()

    if os.path.exists(TEST_RESULTS_FILE):
        try:
            with open(TEST_RESULTS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except:
            existing = []
    else:
        existing = []

    existing.append(data)

    with open(TEST_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    resp = JSONResponse({"status": "saved"})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.get("/test-results")
async def get_test_results():
    if not os.path.exists(TEST_RESULTS_FILE):
        return []
    with open(TEST_RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
