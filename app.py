import os
import json
from datetime import datetime, timezone

import requests
from flask import Flask, render_template, jsonify, request
from supabase import create_client, Client
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
CRON_SECRET = os.environ.get("CRON_SECRET", "")  # opcional, protege el endpoint manual

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# Catálogo de items y ciudades (única fuente de verdad, se pasa al frontend)
# ---------------------------------------------------------------------------

ITEMS = [
    {"id": "T4_ORE", "name": "Mineral T4", "tier": 4}, {"id": "T4_METALBAR", "name": "Lingote T4", "tier": 4},
    {"id": "T4_HIDE", "name": "Cuero crudo T4", "tier": 4}, {"id": "T4_LEATHER", "name": "Cuero curtido T4", "tier": 4},
    {"id": "T4_FIBER", "name": "Fibra T4", "tier": 4}, {"id": "T4_CLOTH", "name": "Tela T4", "tier": 4},
    {"id": "T4_WOOD", "name": "Madera T4", "tier": 4}, {"id": "T4_PLANKS", "name": "Tablones T4", "tier": 4},
    {"id": "T4_ROCK", "name": "Piedra T4", "tier": 4}, {"id": "T4_STONEBLOCK", "name": "Bloque de piedra T4", "tier": 4},
    {"id": "T6_ORE", "name": "Mineral T6", "tier": 6}, {"id": "T6_METALBAR", "name": "Lingote T6", "tier": 6},
    {"id": "T6_HIDE", "name": "Cuero crudo T6", "tier": 6}, {"id": "T6_LEATHER", "name": "Cuero curtido T6", "tier": 6},
    {"id": "T6_FIBER", "name": "Fibra T6", "tier": 6}, {"id": "T6_CLOTH", "name": "Tela T6", "tier": 6},
    {"id": "T6_WOOD", "name": "Madera T6", "tier": 6}, {"id": "T6_PLANKS", "name": "Tablones T6", "tier": 6},
    {"id": "T6_ROCK", "name": "Piedra T6", "tier": 6}, {"id": "T6_STONEBLOCK", "name": "Bloque de piedra T6", "tier": 6},
    {"id": "T8_ORE", "name": "Mineral T8", "tier": 8}, {"id": "T8_METALBAR", "name": "Lingote T8", "tier": 8},
    {"id": "T8_HIDE", "name": "Cuero crudo T8", "tier": 8}, {"id": "T8_LEATHER", "name": "Cuero curtido T8", "tier": 8},
    {"id": "T8_FIBER", "name": "Fibra T8", "tier": 8}, {"id": "T8_CLOTH", "name": "Tela T8", "tier": 8},
    {"id": "T8_WOOD", "name": "Madera T8", "tier": 8}, {"id": "T8_PLANKS", "name": "Tablones T8", "tier": 8},
    {"id": "T4_MAIN_SWORD", "name": "Espada T4", "tier": 4}, {"id": "T6_MAIN_SWORD", "name": "Espada T6", "tier": 6}, {"id": "T8_MAIN_SWORD", "name": "Espada T8", "tier": 8},
    {"id": "T4_MAIN_AXE", "name": "Hacha T4", "tier": 4}, {"id": "T6_MAIN_AXE", "name": "Hacha T6", "tier": 6}, {"id": "T8_MAIN_AXE", "name": "Hacha T8", "tier": 8},
    {"id": "T4_2H_BOW", "name": "Arco T4", "tier": 4}, {"id": "T6_2H_BOW", "name": "Arco T6", "tier": 6}, {"id": "T8_2H_BOW", "name": "Arco T8", "tier": 8},
    {"id": "T4_2H_FIRESTAFF", "name": "Bastón de fuego T4", "tier": 4}, {"id": "T6_2H_FIRESTAFF", "name": "Bastón de fuego T6", "tier": 6}, {"id": "T8_2H_FIRESTAFF", "name": "Bastón de fuego T8", "tier": 8},
    {"id": "T4_MAIN_HOLYSTAFF", "name": "Bastón sagrado T4", "tier": 4}, {"id": "T6_MAIN_HOLYSTAFF", "name": "Bastón sagrado T6", "tier": 6}, {"id": "T8_MAIN_HOLYSTAFF", "name": "Bastón sagrado T8", "tier": 8},
    {"id": "T4_ARMOR_PLATE_SET1", "name": "Armadura placa T4", "tier": 4}, {"id": "T6_ARMOR_PLATE_SET1", "name": "Armadura placa T6", "tier": 6}, {"id": "T8_ARMOR_PLATE_SET1", "name": "Armadura placa T8", "tier": 8},
    {"id": "T4_ARMOR_LEATHER_SET1", "name": "Armadura cuero T4", "tier": 4}, {"id": "T6_ARMOR_LEATHER_SET1", "name": "Armadura cuero T6", "tier": 6}, {"id": "T8_ARMOR_LEATHER_SET1", "name": "Armadura cuero T8", "tier": 8},
    {"id": "T4_ARMOR_CLOTH_SET1", "name": "Armadura tela T4", "tier": 4}, {"id": "T6_ARMOR_CLOTH_SET1", "name": "Armadura tela T6", "tier": 6}, {"id": "T8_ARMOR_CLOTH_SET1", "name": "Armadura tela T8", "tier": 8},
    {"id": "T4_HEAD_PLATE_SET1", "name": "Casco placa T4", "tier": 4}, {"id": "T6_HEAD_PLATE_SET1", "name": "Casco placa T6", "tier": 6}, {"id": "T8_HEAD_PLATE_SET1", "name": "Casco placa T8", "tier": 8},
    {"id": "T4_SHOES_PLATE_SET1", "name": "Botas placa T4", "tier": 4}, {"id": "T6_SHOES_PLATE_SET1", "name": "Botas placa T6", "tier": 6}, {"id": "T8_SHOES_PLATE_SET1", "name": "Botas placa T8", "tier": 8},
    {"id": "T4_POTION_HEAL", "name": "Poción de curación T4", "tier": 4}, {"id": "T6_POTION_HEAL", "name": "Poción de curación T6", "tier": 6}, {"id": "T8_POTION_HEAL", "name": "Poción de curación T8", "tier": 8},
    {"id": "T4_MEAL_OMELETTE", "name": "Omelette T4", "tier": 4}, {"id": "T6_MEAL_OMELETTE", "name": "Omelette T6", "tier": 6}, {"id": "T8_MEAL_OMELETTE", "name": "Omelette T8", "tier": 8},
    {"id": "T4_MEAL_SOUP", "name": "Sopa T4", "tier": 4}, {"id": "T6_MEAL_SOUP", "name": "Sopa T6", "tier": 6}, {"id": "T8_MEAL_SOUP", "name": "Sopa T8", "tier": 8},
]

CITIES = [
    {"id": "Caerleon", "name": "Caerleon"},
    {"id": "Bridgewatch", "name": "Bridgewatch"},
    {"id": "Martlock", "name": "Martlock"},
    {"id": "Lymhurst", "name": "Lymhurst"},
    {"id": "FortSterling", "name": "Fort Sterling"},
    {"id": "Thetford", "name": "Thetford"},
    {"id": "Brecilien", "name": "Brécilien"},
]

SERVER_HOSTS = {
    "west": "west.albion-online-data.com",
    "europe": "europe.albion-online-data.com",
    "east": "east.albion-online-data.com",
}


# ---------------------------------------------------------------------------
# Lógica del cron: trae precios de AODP, los guarda, calcula márgenes
# ---------------------------------------------------------------------------

def fetch_and_store_prices():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Iniciando fetch de precios...")

    cfg = get_config()
    server = cfg.get("servidor", "west")
    host = SERVER_HOSTS.get(server, SERVER_HOSTS["west"])

    item_ids = ",".join(i["id"] for i in ITEMS)
    city_names = ",".join(c["id"] for c in CITIES)
    url = f"https://{host}/api/v2/stats/prices/{item_ids}.json?locations={city_names}&qualities=1"

    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"Error consultando AODP: {e}")
        return

    rows = []
    for rec in data:
        rows.append({
            "item_id": rec["item_id"],
            "city": rec["city"],
            "sell_price_min": rec.get("sell_price_min") or None,
            "sell_price_min_date": rec.get("sell_price_min_date") or None,
            "buy_price_max": rec.get("buy_price_max") or None,
            "buy_price_max_date": rec.get("buy_price_max_date") or None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })

    if rows:
        supabase.table("precios_actuales").upsert(rows, on_conflict="item_id,city").execute()
        print(f"Guardados {len(rows)} registros de precios.")

    compute_and_store_margins(rows, cfg)


def compute_and_store_margins(rows, cfg):
    """Calcula el mejor margen por item con la config actual y lo guarda en el historial."""
    by_item = {}
    for r in rows:
        by_item.setdefault(r["item_id"], {})[r["city"]] = r

    item_name_lookup = {i["id"]: i["name"] for i in ITEMS}
    city_name_lookup = {c["id"]: c["name"] for c in CITIES}
    riesgo = cfg.get("riesgo_ciudades", {})
    tax = float(cfg.get("impuesto", 4)) / 100
    min_margin = float(cfg.get("margen_minimo", 0))

    snapshots = []
    for item_id, city_data in by_item.items():
        best = None
        for origin_id, o in city_data.items():
            for dest_id, d in city_data.items():
                if origin_id == dest_id:
                    continue
                buy_price = o.get("sell_price_min")
                sell_price = d.get("buy_price_max")
                if not buy_price or not sell_price or buy_price <= 0:
                    continue

                revenue = sell_price * (1 - tax)
                margin = revenue - buy_price
                margin_pct = (margin / buy_price) * 100
                avg_risk = (riesgo.get(origin_id, 30) + riesgo.get(dest_id, 30)) / 2
                score = margin * (1 - avg_risk / 150)

                if margin < min_margin:
                    continue
                if best is None or score > best["score"]:
                    best = {
                        "item_id": item_id,
                        "item_name": item_name_lookup.get(item_id, item_id),
                        "origin": city_name_lookup.get(origin_id, origin_id),
                        "dest": city_name_lookup.get(dest_id, dest_id),
                        "margin": round(margin, 2),
                        "margin_pct": round(margin_pct, 2),
                        "score": score,
                    }
        if best:
            snapshots.append({k: v for k, v in best.items() if k != "score"})

    if snapshots:
        supabase.table("margenes_historico").insert(snapshots).execute()
        print(f"Guardado historial de margen para {len(snapshots)} items.")


def get_config():
    res = supabase.table("config_usuario").select("*").eq("id", 1).single().execute()
    return res.data or {}


# ---------------------------------------------------------------------------
# Scheduler interno (cron que vive dentro del proceso, se duerme con Render
# igual que en dian-facturas — no requiere ningún servicio externo)
# ---------------------------------------------------------------------------

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_prices, "interval", hours=1, id="fetch_prices_job")
scheduler.start()


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", items_json=json.dumps(ITEMS), cities_json=json.dumps(CITIES))


@app.route("/api/precios")
def api_precios():
    res = supabase.table("precios_actuales").select("*").execute()
    return jsonify(res.data)


@app.route("/api/historial")
def api_historial():
    item_id = request.args.get("item_id")
    query = supabase.table("margenes_historico").select("*").order("ts", desc=True).limit(30)
    if item_id:
        query = query.eq("item_id", item_id)
    res = query.execute()
    return jsonify(res.data)


@app.route("/api/eventos", methods=["GET", "POST"])
def api_eventos():
    if request.method == "POST":
        body = request.get_json()
        nuevo = {
            "fecha": body["fecha"],
            "titulo": body["titulo"],
            "tipo": body["tipo"],
            "impacto": body["impacto"],
            "notas": body.get("notas", ""),
        }
        res = supabase.table("eventos_economia").insert(nuevo).execute()
        return jsonify(res.data), 201

    res = supabase.table("eventos_economia").select("*").order("fecha", desc=True).execute()
    return jsonify(res.data)


@app.route("/api/eventos/<int:evento_id>", methods=["DELETE"])
def api_eventos_delete(evento_id):
    supabase.table("eventos_economia").delete().eq("id", evento_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        body = request.get_json()
        body["id"] = 1
        res = supabase.table("config_usuario").upsert(body).execute()
        return jsonify(res.data)

    return jsonify(get_config())


@app.route("/api/cron/actualizar-precios")
def api_cron_trigger():
    """Endpoint para forzar una actualización manual (botón en la UI)."""
    token = request.args.get("token", "")
    if CRON_SECRET and token != CRON_SECRET:
        return jsonify({"error": "no autorizado"}), 401
    fetch_and_store_prices()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
