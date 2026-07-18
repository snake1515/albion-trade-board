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
# ---------------------------------------------------------------------------
# ITEMS con campo "peso" (kg) agregado — reemplaza la lista ITEMS completa
# en app.py con esta versión.
#
# IMPORTANTE — honestidad sobre estos números:
# Los pesos son una ESTIMACIÓN mía basada en patrones típicos del juego
# (recursos crudos livianos, refinados un poco más pesados, equipo más
# pesado todavía), NO son datos extraídos del juego ni de un dump oficial.
# Antes de confiar en los cálculos de "unidades óptimas de carga", verifica
# el peso real de al menos 2-3 items que uses seguido: pasa el mouse sobre
# el item en tu inventario en el juego, el tooltip muestra el peso en kg.
# Si el número no coincide, ajusta esa línea aquí abajo — es solo un
# diccionario de Python, no hace falta tocar nada más.
# ---------------------------------------------------------------------------
ITEMS = [
    # --- Materias primas (livianas) ---
    {"id": "T4_ORE", "name": "Mineral T4", "tier": 4, "peso": 1.4},
    {"id": "T4_HIDE", "name": "Cuero crudo T4", "tier": 4, "peso": 1.4},
    {"id": "T4_FIBER", "name": "Fibra T4", "tier": 4, "peso": 1.4},
    {"id": "T4_WOOD", "name": "Madera T4", "tier": 4, "peso": 1.4},
    {"id": "T4_ROCK", "name": "Piedra T4", "tier": 4, "peso": 1.4},
    {"id": "T6_ORE", "name": "Mineral T6", "tier": 6, "peso": 2.1},
    {"id": "T6_HIDE", "name": "Cuero crudo T6", "tier": 6, "peso": 2.1},
    {"id": "T6_FIBER", "name": "Fibra T6", "tier": 6, "peso": 2.1},
    {"id": "T6_WOOD", "name": "Madera T6", "tier": 6, "peso": 2.1},
    {"id": "T6_ROCK", "name": "Piedra T6", "tier": 6, "peso": 2.1},
    {"id": "T8_ORE", "name": "Mineral T8", "tier": 8, "peso": 2.8},
    {"id": "T8_HIDE", "name": "Cuero crudo T8", "tier": 8, "peso": 2.8},
    {"id": "T8_FIBER", "name": "Fibra T8", "tier": 8, "peso": 2.8},
    {"id": "T8_WOOD", "name": "Madera T8", "tier": 8, "peso": 2.8},

    # --- Refinados (un poco más pesados que la materia prima) ---
    {"id": "T4_METALBAR", "name": "Lingote T4", "tier": 4, "peso": 1.9},
    {"id": "T4_LEATHER", "name": "Cuero curtido T4", "tier": 4, "peso": 1.9},
    {"id": "T4_CLOTH", "name": "Tela T4", "tier": 4, "peso": 1.9},
    {"id": "T4_PLANKS", "name": "Tablones T4", "tier": 4, "peso": 1.9},
    {"id": "T4_STONEBLOCK", "name": "Bloque de piedra T4", "tier": 4, "peso": 1.9},
    {"id": "T6_METALBAR", "name": "Lingote T6", "tier": 6, "peso": 2.8},
    {"id": "T6_LEATHER", "name": "Cuero curtido T6", "tier": 6, "peso": 2.8},
    {"id": "T6_CLOTH", "name": "Tela T6", "tier": 6, "peso": 2.8},
    {"id": "T6_PLANKS", "name": "Tablones T6", "tier": 6, "peso": 2.8},
    {"id": "T6_STONEBLOCK", "name": "Bloque de piedra T6", "tier": 6, "peso": 2.8},
    {"id": "T8_METALBAR", "name": "Lingote T8", "tier": 8, "peso": 3.7},
    {"id": "T8_LEATHER", "name": "Cuero curtido T8", "tier": 8, "peso": 3.7},
    {"id": "T8_CLOTH", "name": "Tela T8", "tier": 8, "peso": 3.7},
    {"id": "T8_PLANKS", "name": "Tablones T8", "tier": 8, "peso": 3.7},

    # --- Armas (más pesadas, una por slot) ---
    {"id": "T4_MAIN_SWORD", "name": "Espada T4", "tier": 4, "peso": 5.0},
    {"id": "T6_MAIN_SWORD", "name": "Espada T6", "tier": 6, "peso": 6.5},
    {"id": "T8_MAIN_SWORD", "name": "Espada T8", "tier": 8, "peso": 8.0},
    {"id": "T4_MAIN_AXE", "name": "Hacha T4", "tier": 4, "peso": 5.0},
    {"id": "T6_MAIN_AXE", "name": "Hacha T6", "tier": 6, "peso": 6.5},
    {"id": "T8_MAIN_AXE", "name": "Hacha T8", "tier": 8, "peso": 8.0},
    {"id": "T4_2H_BOW", "name": "Arco T4", "tier": 4, "peso": 5.5},
    {"id": "T6_2H_BOW", "name": "Arco T6", "tier": 6, "peso": 7.0},
    {"id": "T8_2H_BOW", "name": "Arco T8", "tier": 8, "peso": 8.5},
    {"id": "T4_2H_FIRESTAFF", "name": "Bastón de fuego T4", "tier": 4, "peso": 5.5},
    {"id": "T6_2H_FIRESTAFF", "name": "Bastón de fuego T6", "tier": 6, "peso": 7.0},
    {"id": "T8_2H_FIRESTAFF", "name": "Bastón de fuego T8", "tier": 8, "peso": 8.5},
    {"id": "T4_MAIN_HOLYSTAFF", "name": "Bastón sagrado T4", "tier": 4, "peso": 5.0},
    {"id": "T6_MAIN_HOLYSTAFF", "name": "Bastón sagrado T6", "tier": 6, "peso": 6.5},
    {"id": "T8_MAIN_HOLYSTAFF", "name": "Bastón sagrado T8", "tier": 8, "peso": 8.0},

    # --- Armaduras (piezas de torso, más pesadas) ---
    {"id": "T4_ARMOR_PLATE_SET1", "name": "Armadura placa T4", "tier": 4, "peso": 7.0},
    {"id": "T6_ARMOR_PLATE_SET1", "name": "Armadura placa T6", "tier": 6, "peso": 9.0},
    {"id": "T8_ARMOR_PLATE_SET1", "name": "Armadura placa T8", "tier": 8, "peso": 11.0},
    {"id": "T4_ARMOR_LEATHER_SET1", "name": "Armadura cuero T4", "tier": 4, "peso": 5.5},
    {"id": "T6_ARMOR_LEATHER_SET1", "name": "Armadura cuero T6", "tier": 6, "peso": 7.0},
    {"id": "T8_ARMOR_LEATHER_SET1", "name": "Armadura cuero T8", "tier": 8, "peso": 8.5},
    {"id": "T4_ARMOR_CLOTH_SET1", "name": "Armadura tela T4", "tier": 4, "peso": 4.0},
    {"id": "T6_ARMOR_CLOTH_SET1", "name": "Armadura tela T6", "tier": 6, "peso": 5.0},
    {"id": "T8_ARMOR_CLOTH_SET1", "name": "Armadura tela T8", "tier": 8, "peso": 6.0},

    # --- Cascos y botas (piezas más chicas, más livianas) ---
    {"id": "T4_HEAD_PLATE_SET1", "name": "Casco placa T4", "tier": 4, "peso": 3.0},
    {"id": "T6_HEAD_PLATE_SET1", "name": "Casco placa T6", "tier": 6, "peso": 3.8},
    {"id": "T8_HEAD_PLATE_SET1", "name": "Casco placa T8", "tier": 8, "peso": 4.6},
    {"id": "T4_SHOES_PLATE_SET1", "name": "Botas placa T4", "tier": 4, "peso": 3.0},
    {"id": "T6_SHOES_PLATE_SET1", "name": "Botas placa T6", "tier": 6, "peso": 3.8},
    {"id": "T8_SHOES_PLATE_SET1", "name": "Botas placa T8", "tier": 8, "peso": 4.6},

    # --- Consumibles (livianos, casi no varían por tier) ---
    {"id": "T4_POTION_HEAL", "name": "Poción de curación T4", "tier": 4, "peso": 0.6},
    {"id": "T6_POTION_HEAL", "name": "Poción de curación T6", "tier": 6, "peso": 0.6},
    {"id": "T8_POTION_HEAL", "name": "Poción de curación T8", "tier": 8, "peso": 0.6},
    {"id": "T4_MEAL_OMELETTE", "name": "Omelette T4", "tier": 4, "peso": 0.5},
    {"id": "T6_MEAL_OMELETTE", "name": "Omelette T6", "tier": 6, "peso": 0.5},
    {"id": "T8_MEAL_OMELETTE", "name": "Omelette T8", "tier": 8, "peso": 0.5},
    {"id": "T4_MEAL_SOUP", "name": "Sopa T4", "tier": 4, "peso": 0.5},
    {"id": "T6_MEAL_SOUP", "name": "Sopa T6", "tier": 6, "peso": 0.5},
    {"id": "T8_MEAL_SOUP", "name": "Sopa T8", "tier": 8, "peso": 0.5},
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

ITEMS_BY_ID = {i["id"]: i for i in ITEMS}
CITIES_BY_ID = {c["id"]: c for c in CITIES}


def unidades_optimas(peso_item_kg, capacidad_kg):
    if not peso_item_kg or peso_item_kg <= 0 or not capacidad_kg:
        return 0
    return int(capacidad_kg // peso_item_kg)

WEAPON_TYPES = [
    "Espada", "Hacha", "Maza", "Lanza", "Daga", "Arco", "Ballesta",
    "Bastón de fuego", "Bastón sagrado", "Bastón de la naturaleza",
    "Bastón arcano", "Bastón maldito", "Bastón doble", "Garras",
]

# ---------------------------------------------------------------------------
# Tips curados por arma (guías/foros de la comunidad, mid-2026 — no es un
# cálculo exacto, el meta cambia con cada parche de balance)
#
# Cambios en esta versión: se agregó la clave "variantes" a cada arma, con
# 2-4 armas específicas de esa categoría y una nota corta de por qué se usa
# cada una para farmeo/PvE en solitario. El resto de la estructura
# (rol, tips, contenido) se mantiene igual para no romper el frontend.
# ---------------------------------------------------------------------------
WEAPON_TIPS = {
    "Espada": {
        "rol": "Daño cuerpo a cuerpo versátil, buen AoE de farmeo con Crea-reyes.",
        "tips": [
            "El Crea-reyes es de las espadas más recomendadas para farmeo por su golpe en área al moverte entre packs de mobs.",
            "Dual Swords tiene mejor sustain 1v1 pero menos alcance de área que el Crea-reyes para limpiar grupos.",
        ],
        "variantes": [
            "Crea-reyes (Kingmaker): el estándar para farmeo en área, buen alcance al pasar entre mobs agrupados.",
            "Espada Doble (Dual Swords): más daño sostenido 1v1, mejor si el pack está disperso en vez de agrupado.",
            "Espada Reforzada (Claymore): golpe más lento pero pega más duro, opción si tu IP ya es alto y quieres matar más rápido mobs individuales.",
        ],
        "contenido": "Mist y mazmorras estáticas en solitario — buen punto de entrada al farmeo con daño en área.",
    },
    "Hacha": {
        "rol": "Daño explosivo alto, fuerte contra builds tanque.",
        "tips": [
            "El Hacha de Guerra tiene un buen reset de daño y es popular en Mist en solitario.",
            "Su alcance en área es más limitado que el de los bastones, así que rinde mejor contra mobs sueltos que contra packs grandes.",
        ],
        "variantes": [
            "Hacha de Guerra (Battleaxe): la más popular para farmeo solo, buen reset de habilidad para encadenar golpes.",
            "Hacha Carnicera (Halberd): más movilidad para reposicionarte entre mobs, algo más frágil.",
            "Hacha Infernal (Hellgate Axe): mayor daño sostenido, exige más precisión en el manejo.",
        ],
        "contenido": "Mist en solitario contra mobs individuales o grupos pequeños.",
    },
    "Maza": {
        "rol": "Control y sustain propio, útil si farmeas sin apoyo de curación externa.",
        "tips": [
            "Tiene curación propia, así que te permite farmear más tiempo sin depender tanto de pociones.",
            "No sobresale en daño de área masivo — rinde mejor en peleas contra pocos enemigos a la vez.",
        ],
        "variantes": [
            "Maza (Mace): la base, buen balance entre daño y curación propia.",
            "Maza Pesada (Heavy Mace): más control (aturdimiento), útil si te rodean varios mobs a la vez.",
            "Caitiff Warmace: más agresiva, menos sustain que la Maza base pero mata más rápido.",
        ],
        "contenido": "Mist en solitario de dificultad media.",
    },
    "Lanza": {
        "rol": "Build barata y perdonadora, buen alcance y movilidad.",
        "tips": [
            "Es de las builds más recomendadas para empezar a farmear en solitario por su bajo costo y facilidad de uso.",
            "Buena opción mientras no tengas mucha plata para invertir en equipo de tier alto.",
        ],
        "variantes": [
            "Lanza (Spear): la opción de entrada, barata y fácil de usar para principiantes.",
            "Alabarda (Glaive): más daño en área en el golpe cargado, sigue siendo accesible en costo.",
            "Mano de la Justicia (Hand of Justice): más orientada a curación/sustain propio, buena si te cuesta sobrevivir con la Lanza básica.",
        ],
        "contenido": "Mist Nivel 1-2 — ideal si tu IP todavía es bajo.",
    },
    "Daga": {
        "rol": "Alta movilidad y daño burst, pero frágil.",
        "tips": [
            "Tiene una curva de aprendizaje más alta, se recomienda más para jugadores con experiencia.",
            "No es de las primeras opciones para farmeo masivo de mobs por estar enfocada en objetivos individuales.",
        ],
        "variantes": [
            "Bloodletter: la daga más recomendada para farmeo en solitario, tiene un golpe en área que ayuda contra packs pequeños.",
            "Deathgivers: más burst contra un solo objetivo, pero sin el área de Bloodletter — mejor para élites que para packs.",
            "Furia Embridada (Bridled Fury): recompensa el manejo agresivo y encadenar golpes, curva de aprendizaje todavía más alta.",
        ],
        "contenido": "Mist en solitario contra élites o mobs sueltos, menos eficiente contra packs grandes.",
    },
    "Arco": {
        "rol": "Daño a distancia seguro, mantiene la distancia de los mobs.",
        "tips": [
            "El Longbow es de las builds más recomendadas para principiantes por lo segura que es a distancia.",
            "Buena opción si prefieres evitar el combate cuerpo a cuerpo mientras farmeas.",
        ],
        "variantes": [
            "Arco Largo (Longbow): la opción más segura para principiantes, mantiene distancia con facilidad.",
            "Arco de Guerra (Warbow): más daño por golpe cargado, pero te deja más expuesto mientras cargas.",
            "Arco de Badon (Bow of Badon): buen término medio, golpe en área decente sin sacrificar tanta seguridad como el Warbow.",
        ],
        "contenido": "Mist en solitario — opción defensiva y de bajo riesgo.",
    },
    "Ballesta": {
        "rol": "Daño a distancia con más burst que el arco, pero menos sostenido.",
        "tips": [
            "Rinde bien contra mobs individuales de alto valor.",
            "Menos eficiente que los bastones de área para limpiar packs grandes de mobs.",
        ],
        "variantes": [
            "Ballesta (Crossbow): la base, buen burst contra un objetivo a la vez.",
            "Culebrina (Culverin): más alcance y daño perforante, buena contra mobs de alta defensa.",
            "Ballesta Repetidora (Doublebarrel): dispara más rápido pero con menos daño por golpe, mejor contra mobs con poca vida.",
        ],
        "contenido": "Mist en solitario, mejor contra objetivos individuales.",
    },
    "Bastón de fuego": {
        "rol": "De los mejores para farmeo masivo por su daño en área.",
        "tips": [
            "Es de las armas más recomendadas específicamente para farmear packs grandes de mobs.",
            "Cuidado con el kite: si te rodean varios mobs a la vez puede ser arriesgado sin buena movilidad.",
        ],
        "variantes": [
            "Guadaña Infernal (Infernal Scythe): la referencia para farmeo masivo, buen drenaje de vida en área.",
            "Bastón de Fuego Salvaje (Wildfire Staff): más daño en área pura, menos sustain que la Guadaña Infernal.",
            "Gran Bastón de Fuego (Great Fire Staff): golpe cargado muy fuerte, mejor si los mobs llegan en oleadas espaciadas y no todos a la vez.",
        ],
        "contenido": "Mist Nivel 2-3 — farmeo de packs grandes de mobs.",
    },
    "Bastón sagrado": {
        "rol": "Curación pura, pensado para grupo más que para farmeo en solitario.",
        "tips": [
            "Es el arma principal si quieres jugar de curandero en mazmorras estáticas en grupo.",
            "En solitario no rinde tanto porque no tiene mucho daño propio.",
        ],
        "variantes": [
            "Bastón Divino (Divine Staff): el estándar de curandero en grupo, buen balance entre curación directa y en área.",
            "Bastón de Redención (Redemption Staff): más curación en área sostenida, popular en mazmorras con varios jugadores.",
            "Bastón Sagrado base (Holy Staff): opción de entrada, más barata, buena para aprender el rol antes de invertir en las anteriores.",
        ],
        "contenido": "Mazmorras estáticas en grupo como curandero — no recomendado para farmeo solo.",
    },
    "Bastón de la naturaleza": {
        "rol": "Curación híbrida con algo de daño propio, más flexible que el sagrado.",
        "tips": [
            "Puede curar y hacer algo de daño a la vez, lo que lo hace más viable en solitario que el bastón sagrado.",
            "Sigue rindiendo mejor en grupo que en solitario para mazmorras.",
        ],
        "variantes": [
            "Toque de la Naturaleza (Nature's Touch): el más equilibrado entre curación y daño propio, buena opción híbrida.",
            "Bastón Salvaje (Wild Staff): más orientado a curación en área para grupo.",
            "Bastón Corrupto (Blight Staff): agrega debuffs de veneno, útil si quieres aportar algo de control además de curar.",
        ],
        "contenido": "Mazmorras en grupo — farmeo en solitario limitado.",
    },
    "Bastón arcano": {
        "rol": "Control y debuffs, no es de las mejores opciones para farmeo solo.",
        "tips": [
            "Su fuerza está en controlar enemigos (ralentizar, aturdir), más útil en PvP o grupo que en farmeo.",
            "Para farmeo en solitario hay opciones más eficientes, como el bastón de fuego.",
        ],
        "variantes": [
            "Bastón Enigmático (Enigmatic Staff): el más usado para control en grupo, buenos debuffs de área.",
            "Bastón Ocultista (Occult Staff): más orientado a debilitar la defensa del objetivo, mejor en PvP que en farmeo.",
            "Bastón de Brujería (Witchwork Staff): agrega algo de sustain propio, ligeramente más viable en solitario que los otros dos.",
        ],
        "contenido": "Más orientado a PvP o grupo que a farmeo en solitario.",
    },
    "Bastón maldito": {
        "rol": "Daño sostenido con drenaje de vida.",
        "tips": [
            "El drenaje de vida ayuda a sobrevivir mientras farmeas sin depender tanto de pociones.",
            "Buen punto medio entre daño y sustain para farmeo en solitario.",
        ],
        "variantes": [
            "Bastón de Maldición Vital (Lifecurse Staff): el más recomendado para farmeo, buen drenaje de vida sostenido.",
            "Bastón Demoníaco (Demonic Staff): invoca ayuda temporal, útil contra packs más grandes.",
            "Bastón Maldito base (Cursed Staff): opción de entrada, menos sustain que el Lifecurse pero más barata.",
        ],
        "contenido": "Mist en solitario, dificultad media-alta gracias al sustain propio.",
    },
    "Bastón doble": {
        "rol": "Versátil, mezcla ofensiva con algo de utilidad.",
        "tips": [
            "Es de las opciones más versátiles entre los bastones para farmeo en solitario.",
            "No sobresale tanto en daño de área puro como el bastón de fuego.",
        ],
        "variantes": [
            "Bastón Acechante (Prowling Staff): buena movilidad e invisibilidad corta, útil para reposicionarte o escapar de un mob peligroso.",
            "Bastón de Doble Filo (Double Bladed Staff): más daño físico sostenido, la opción más ofensiva del grupo.",
            "Bastón del Profeta (Bastón similar tipo utilidad): prioriza control y utilidad sobre daño puro, opción defensiva.",
        ],
        "contenido": "Mist en solitario, buena opción generalista.",
    },
    "Garras": {
        "rol": "Alta movilidad y daño sostenido cuerpo a cuerpo, requiere buen manejo.",
        "tips": [
            "Tiene buena movilidad para esquivar mientras farmeas, pero exige más atención que un bastón de fuego.",
            "Curva de aprendizaje más alta — no es de las primeras recomendaciones para principiantes.",
        ],
        "variantes": [
            "Puños de Avalon (Fists of Avalon): las garras más recomendadas para farmeo, buen daño en área al encadenar golpes.",
            "Garras de Hierro (Iron Claws): más simples de usar, buena opción para aprender la categoría antes de subir a Fists of Avalon.",
            "Garras Voraces (Ravenous Claws): drenaje de vida propio, mejor sustain a cambio de algo menos de daño en área.",
        ],
        "contenido": "Mist en solitario, mejor para jugadores con más experiencia en movimiento y esquiva.",
    },
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
    return render_template(
        "index.html",
        items_json=json.dumps(ITEMS),
        cities_json=json.dumps(CITIES),
        weapons_json=json.dumps(WEAPON_TYPES),
        weapon_tips_json=json.dumps(WEAPON_TIPS),
    )


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


@app.route("/api/ordenes", methods=["GET", "POST"])
def api_ordenes():
    if request.method == "POST":
        body = request.get_json()
        item = ITEMS_BY_ID.get(body["item_id"])
        if not item:
            return jsonify({"error": "item no reconocido"}), 400
        nueva = {
            "item_id": item["id"],
            "item_name": item["name"],
            "city": body["city"],
            "tipo": body["tipo"],
            "precio": body["precio"],
            "cantidad": body.get("cantidad", 1),
        }
        res = supabase.table("seguimiento_ordenes").insert(nueva).execute()
        return jsonify(res.data), 201
    res = supabase.table("seguimiento_ordenes").select("*").order("fecha_creacion", desc=True).execute()
    return jsonify(res.data)


@app.route("/api/ordenes/<int:orden_id>/completar", methods=["POST"])
def api_ordenes_completar(orden_id):
    actual = supabase.table("seguimiento_ordenes").select("*").eq("id", orden_id).single().execute()
    if not actual.data:
        return jsonify({"error": "no encontrada"}), 404
    creado = datetime.fromisoformat(actual.data["fecha_creacion"].replace("Z", "+00:00"))
    ahora = datetime.now(timezone.utc)
    duracion_horas = round((ahora - creado).total_seconds() / 3600, 2)
    res = supabase.table("seguimiento_ordenes").update({
        "fecha_completada": ahora.isoformat(),
        "duracion_horas": duracion_horas,
    }).eq("id", orden_id).execute()
    return jsonify(res.data)


@app.route("/api/ordenes/<int:orden_id>", methods=["DELETE"])
def api_ordenes_delete(orden_id):
    supabase.table("seguimiento_ordenes").delete().eq("id", orden_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/compras", methods=["GET", "POST"])
def api_compras():
    if request.method == "POST":
        body = request.get_json()
        item = ITEMS_BY_ID.get(body["item_id"])
        if not item:
            return jsonify({"error": "item no reconocido"}), 400
        nueva = {
            "item_id": item["id"],
            "item_name": item["name"],
            "city": body["city"],
            "precio_oro": body["precio_oro"],
            "cantidad": body.get("cantidad", 1),
            "nota": body.get("nota") or None,
        }
        res = supabase.table("compras_manual").insert(nueva).execute()
        return jsonify(res.data), 201
    res = supabase.table("compras_manual").select("*").order("fecha_creacion", desc=True).execute()
    return jsonify(res.data)


@app.route("/api/compras/<int:compra_id>/vender", methods=["POST"])
def api_compras_vender(compra_id):
    res = supabase.table("compras_manual").update({
        "vendido": True,
        "fecha_vendida": datetime.now(timezone.utc).isoformat(),
    }).eq("id", compra_id).execute()
    return jsonify(res.data)


@app.route("/api/compras/<int:compra_id>", methods=["DELETE"])
def api_compras_delete(compra_id):
    supabase.table("compras_manual").delete().eq("id", compra_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/viajes", methods=["GET", "POST"])
def api_viajes():
    if request.method == "POST":
        body = request.get_json()
        origin = CITIES_BY_ID.get(body["origin"])
        dest = CITIES_BY_ID.get(body["dest"])
        if not origin or not dest:
            return jsonify({"error": "ciudad no reconocida"}), 400
        nuevo = {
            "origin": origin["id"],
            "origin_name": origin["name"],
            "dest": dest["id"],
            "dest_name": dest["name"],
            "montura": body["montura"],
            "incidente": bool(body.get("incidente", False)),
            "resultado": body.get("resultado") or None,
            "nota": body.get("nota") or None,
        }
        res = supabase.table("viajes_transporte").insert(nuevo).execute()
        return jsonify(res.data), 201
    res = supabase.table("viajes_transporte").select("*").order("fecha_creacion", desc=True).execute()
    return jsonify(res.data)


@app.route("/api/viajes/<int:viaje_id>", methods=["DELETE"])
def api_viajes_delete(viaje_id):
    supabase.table("viajes_transporte").delete().eq("id", viaje_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/perfil", methods=["GET", "POST"])
def api_perfil():
    if request.method == "POST":
        body = request.get_json()
        body["id"] = 1
        res = supabase.table("perfil_personaje").upsert(body).execute()
        return jsonify(res.data)
    res = supabase.table("perfil_personaje").select("*").eq("id", 1).single().execute()
    return jsonify(res.data or {})


@app.route("/api/builds")
def api_builds():
    res = supabase.table("builds_farmeo").select("*").order("tier").execute()
    return jsonify(res.data)


@app.route("/api/refrescar")
def api_refrescar():
    """Endpoint sin token, para el botón manual dentro de la propia página."""
    fetch_and_store_prices()
    return jsonify({"status": "ok"})


@app.route("/api/cron/actualizar-precios")
def api_cron_trigger():
    """Endpoint protegido por token, pensado para un cron externo (ej. cron-job.org)."""
    token = request.args.get("token", "")
    if CRON_SECRET and token != CRON_SECRET:
        return jsonify({"error": "no autorizado"}), 401
    fetch_and_store_prices()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))








































