import os
import json
import re
from datetime import datetime, timezone, timedelta
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
    {"id": "T4_ORE", "name": "Mineral de hierro T4", "tier": 4, "peso": 1.4},
    {"id": "T4_HIDE", "name": "Piel media T4", "tier": 4, "peso": 1.4},
    {"id": "T4_FIBER", "name": "Cáñamo T4", "tier": 4, "peso": 1.4},
    {"id": "T4_WOOD", "name": "Troncos de pino T4", "tier": 4, "peso": 1.4},
    {"id": "T4_ROCK", "name": "Travertino T4", "tier": 4, "peso": 1.4},
    {"id": "T1_WOOD", "name": "Troncos en bruto T1", "tier": 1, "peso": 0.35},
    {"id": "T2_WOOD", "name": "Troncos de abedul T2", "tier": 2, "peso": 0.7},
    {"id": "T3_WOOD", "name": "Troncos de castaño T3", "tier": 3, "peso": 1.05},
    {"id": "T5_WOOD", "name": "Troncos de cedro T5", "tier": 5, "peso": 1.75},
    {"id": "T4_WOOD_LEVEL1@1", "name": "Troncos de pino poco común T4", "tier": 4, "peso": 1.4},
    {"id": "T4_WOOD_LEVEL2@2", "name": "Troncos de pino raro T4", "tier": 4, "peso": 1.4},
    {"id": "T5_WOOD_LEVEL2@2", "name": "Troncos de cedro raro T5", "tier": 5, "peso": 1.75},
    {"id": "T6_ORE", "name": "Mineral de runita T6", "tier": 6, "peso": 2.1},
    {"id": "T6_HIDE", "name": "Piel fornida T6", "tier": 6, "peso": 2.1},
    {"id": "T6_FIBER", "name": "Algodón ambarino T6", "tier": 6, "peso": 2.1},
    {"id": "T6_WOOD", "name": "Troncos de roble rojo T6", "tier": 6, "peso": 2.1},
    {"id": "T6_ROCK", "name": "Pizarra T6", "tier": 6, "peso": 2.1},
    {"id": "T8_ORE", "name": "Mineral de adamantio T8", "tier": 8, "peso": 2.8},
    {"id": "T8_HIDE", "name": "Piel resistente T8", "tier": 8, "peso": 2.8},
    {"id": "T8_FIBER", "name": "Cáñamo fantasma T8", "tier": 8, "peso": 2.8},
    {"id": "T8_WOOD", "name": "Troncos de maderablanca T8", "tier": 8, "peso": 2.8},

    # --- Refinados (un poco más pesados que la materia prima) ---
    {"id": "T4_METALBAR", "name": "Lingote de acero T4", "tier": 4, "peso": 1.9},
    {"id": "T4_LEATHER", "name": "Cuero trabajado T4", "tier": 4, "peso": 1.9},
    {"id": "T4_CLOTH", "name": "Tela fina T4", "tier": 4, "peso": 1.9},
    {"id": "T4_PLANKS", "name": "Tablas de pino T4", "tier": 4, "peso": 1.9},
    {"id": "T4_STONEBLOCK", "name": "Bloque de travertino T4", "tier": 4, "peso": 1.9},
    {"id": "T6_METALBAR", "name": "Lingote de runita T6", "tier": 6, "peso": 2.8},
    {"id": "T6_LEATHER", "name": "Cuero endurecido T6", "tier": 6, "peso": 2.8},
    {"id": "T6_CLOTH", "name": "Tela suntuosa T6", "tier": 6, "peso": 2.8},
    {"id": "T6_PLANKS", "name": "Tablas de roble rojo T6", "tier": 6, "peso": 2.8},
    {"id": "T6_STONEBLOCK", "name": "Bloque de pizarra T6", "tier": 6, "peso": 2.8},
    {"id": "T8_METALBAR", "name": "Lingote de adamantio T8", "tier": 8, "peso": 3.7},
    {"id": "T8_LEATHER", "name": "Cuero fortalecido T8", "tier": 8, "peso": 3.7},
    {"id": "T8_CLOTH", "name": "Tela barroca T8", "tier": 8, "peso": 3.7},
    {"id": "T8_PLANKS", "name": "Tablas de maderablanca T8", "tier": 8, "peso": 3.7},

    # --- Armas (más pesadas, una por slot) ---
    {"id": "T4_MAIN_SWORD", "name": "Espada ancha T4", "tier": 4, "peso": 5.0},
    {"id": "T6_MAIN_SWORD", "name": "Espada ancha T6", "tier": 6, "peso": 6.5},
    {"id": "T8_MAIN_SWORD", "name": "Espada ancha T8", "tier": 8, "peso": 8.0},
    {"id": "T4_MAIN_AXE", "name": "Hacha de guerra T4", "tier": 4, "peso": 5.0},
    {"id": "T6_MAIN_AXE", "name": "Hacha de guerra T6", "tier": 6, "peso": 6.5},
    {"id": "T8_MAIN_AXE", "name": "Hacha de guerra T8", "tier": 8, "peso": 8.0},
    {"id": "T4_2H_BOW", "name": "Arco T4", "tier": 4, "peso": 5.5},
    {"id": "T6_2H_BOW", "name": "Arco T6", "tier": 6, "peso": 7.0},
    {"id": "T8_2H_BOW", "name": "Arco T8", "tier": 8, "peso": 8.5},
    {"id": "T4_2H_FIRESTAFF", "name": "Gran bastón ígneo T4", "tier": 4, "peso": 5.5},
    {"id": "T6_2H_FIRESTAFF", "name": "Gran bastón ígneo T6", "tier": 6, "peso": 7.0},
    {"id": "T8_2H_FIRESTAFF", "name": "Ira de Vendetta T8 (gran bastón ígneo)", "tier": 8, "peso": 8.5},
    {"id": "T4_MAIN_HOLYSTAFF", "name": "Bastón sagrado T4", "tier": 4, "peso": 5.0},
    {"id": "T6_MAIN_HOLYSTAFF", "name": "Bastón sagrado T6", "tier": 6, "peso": 6.5},
    {"id": "T8_MAIN_HOLYSTAFF", "name": "Bastón sagrado T8", "tier": 8, "peso": 8.0},

    # --- Armaduras (piezas de torso, más pesadas) ---
    {"id": "T4_ARMOR_PLATE_SET1", "name": "Armadura de soldado T4", "tier": 4, "peso": 7.0},
    {"id": "T6_ARMOR_PLATE_SET1", "name": "Armadura de soldado T6", "tier": 6, "peso": 9.0},
    {"id": "T8_ARMOR_PLATE_SET1", "name": "Armadura de soldado T8", "tier": 8, "peso": 11.0},
    {"id": "T4_ARMOR_LEATHER_SET1", "name": "Chaqueta de mercenario T4", "tier": 4, "peso": 5.5},
    {"id": "T6_ARMOR_LEATHER_SET1", "name": "Chaqueta de mercenario T6", "tier": 6, "peso": 7.0},
    {"id": "T8_ARMOR_LEATHER_SET1", "name": "Chaqueta de mercenario T8", "tier": 8, "peso": 8.5},
    {"id": "T4_ARMOR_CLOTH_SET1", "name": "Túnica de erudito T4", "tier": 4, "peso": 4.0},
    {"id": "T6_ARMOR_CLOTH_SET1", "name": "Túnica de erudito T6", "tier": 6, "peso": 5.0},
    {"id": "T8_ARMOR_CLOTH_SET1", "name": "Túnica de erudito T8", "tier": 8, "peso": 6.0},

    # --- Cascos y botas (piezas más chicas, más livianas) ---
    {"id": "T4_HEAD_PLATE_SET1", "name": "Casco de soldado T4", "tier": 4, "peso": 3.0},
    {"id": "T6_HEAD_PLATE_SET1", "name": "Casco de soldado T6", "tier": 6, "peso": 3.8},
    {"id": "T8_HEAD_PLATE_SET1", "name": "Casco de soldado T8", "tier": 8, "peso": 4.6},
    {"id": "T4_SHOES_PLATE_SET1", "name": "Botas de soldado T4", "tier": 4, "peso": 3.0},
    {"id": "T6_SHOES_PLATE_SET1", "name": "Botas de soldado T6", "tier": 6, "peso": 3.8},
    {"id": "T8_SHOES_PLATE_SET1", "name": "Botas de soldado T8", "tier": 8, "peso": 4.6},

    # --- Consumibles (livianos, casi no varían por tier) ---
    # Nota: las pociones de curación solo existen en tiers pares hasta T6 (no hay T8),
    # y las comidas no existen en todos los tiers — se ajustó a los IDs reales del juego.
    {"id": "T2_POTION_HEAL", "name": "Poción de curación menor T2", "tier": 2, "peso": 0.6},
    {"id": "T4_POTION_HEAL", "name": "Poción de curación T4", "tier": 4, "peso": 0.6},
    {"id": "T6_POTION_HEAL", "name": "Poción de curación mayor T6", "tier": 6, "peso": 0.6},
    {"id": "T3_MEAL_OMELETTE", "name": "Tortilla de pollo T3", "tier": 3, "peso": 0.5},
    {"id": "T5_MEAL_OMELETTE", "name": "Tortilla de ganso T5", "tier": 5, "peso": 0.5},
    {"id": "T7_MEAL_OMELETTE", "name": "Tortilla de cerdo T7", "tier": 7, "peso": 0.5},
    {"id": "T1_MEAL_SOUP", "name": "Sopa de zanahoria T1", "tier": 1, "peso": 0.5},
    {"id": "T3_MEAL_SOUP", "name": "Sopa de trigo T3", "tier": 3, "peso": 0.5},
    {"id": "T5_MEAL_SOUP", "name": "Sopa de col T5", "tier": 5, "peso": 0.5},
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

# App ID de Albion Online en Steam. Se usa solo para traer sus anuncios
# oficiales (Steam News Hub) desde el botón "Traer noticias" de Eventos.
STEAM_APP_ID_ALBION = 761890

# Opcional: si configuras esta variable de entorno en Render con una API key
# gratuita de DeepL (deepl.com/pro#developer, capa free hasta 500.000
# caracteres/mes), las noticias importadas se traducen a español. Si no está
# configurada, se guardan en inglés (el idioma original de Steam) sin romper
# nada.
DEEPL_API_KEY = (os.environ.get("DEEPL_API_KEY") or "").strip()


ITEMS_BY_ID = {i["id"]: i for i in ITEMS}
CITIES_BY_ID = {c["id"]: c for c in CITIES}

# ---------------------------------------------------------------------------
# Recolección: bonus de ciudad por recurso.
#
# HONESTIDAD SOBRE ESTOS DATOS: esto sale de la wiki de Albion Online y de
# guías de comunidad consultadas en julio 2026, NO de un dump oficial del
# juego. Si un parche cambia estos bonus, hay que actualizar esto a mano.
#
# Dos cosas distintas que casi siempre son ciudades DIFERENTES:
#   - "biome"  -> mejor ciudad para RECOLECTAR el recurso crudo (primaria =
#                 más abundante en esa ciudad/zona, secundaria y terciaria
#                 también aparecen pero menos).
#   - "refino" -> mejor ciudad para REFINAR ese recurso (bonus de ~+40% de
#                 retorno de material al refinar ahí).
# Por diseño del juego casi nunca coinciden: recolectas en una ciudad y
# conviene transportar y refinar/vender en otra.
# ---------------------------------------------------------------------------
RAW_RESOURCE_LABELS = {
    "ORE": "Mineral",
    "HIDE": "Cuero crudo",
    "FIBER": "Fibra",
    "WOOD": "Madera",
    "ROCK": "Piedra",
}

GATHERING_BIOME = {
    "ORE":   {"primaria": "FortSterling", "secundaria": "Martlock",    "terciaria": "Bridgewatch"},
    "HIDE":  {"primaria": "Bridgewatch",  "secundaria": "Lymhurst",    "terciaria": "Thetford"},
    "FIBER": {"primaria": "Thetford",     "secundaria": "Bridgewatch", "terciaria": "FortSterling"},
    "WOOD":  {"primaria": "Lymhurst",     "secundaria": "Thetford",    "terciaria": "Martlock"},
    "ROCK":  {"primaria": "Martlock",     "secundaria": "FortSterling","terciaria": "Lymhurst"},
}

REFINING_BONUS_CITY = {
    "ORE": "Thetford",
    "HIDE": "Martlock",
    "FIBER": "Lymhurst",
    "WOOD": "FortSterling",
    "ROCK": "Bridgewatch",
}

# Nombre real del material crudo en cada tier (T2-T8), según los datos del
# juego (Albion Online 2D Database, consultado julio 2026). Esto es lo que
# ves literalmente en tu inventario/mercado.
GATHERING_TIER_NAMES = {
    "WOOD":  {2: "Troncos de abedul", 3: "Troncos de castaño", 4: "Troncos de pino", 5: "Troncos de cedro", 6: "Troncos de roble rojo", 7: "Troncos de cortezaceniza", 8: "Troncos de maderablanca"},
    "ORE":   {2: "Mineral de cobre", 3: "Mineral de estaño", 4: "Mineral de hierro", 5: "Mineral de titanio", 6: "Mineral de runita", 7: "Mineral de meteorito", 8: "Mineral de adamantio"},
    "FIBER": {2: "Algodón", 3: "Lino", 4: "Cáñamo", 5: "Duranta", 6: "Algodón ambarino", 7: "Lino solar", 8: "Cáñamo fantasma"},
    "HIDE":  {2: "Piel dura", 3: "Piel fina", 4: "Piel media", 5: "Piel pesada", 6: "Piel fornida", 7: "Piel gruesa", 8: "Piel resistente"},
    "ROCK":  {2: "Piedra caliza", 3: "Arenisca", 4: "Travertino", 5: "Granito", 6: "Pizarra", 7: "Basalto", 8: "Mármol"},
}

# Zona mínima donde se suele encontrar cada tier en el mundo abierto. Esto es
# consenso de guías de comunidad, NO una garantía exacta — el reparto real de
# recursos varía por región del mapa y cambia con parches.
GATHERING_TIER_ZONE = {
    1: "Zona inicial (cualquier ciudad/zona azul)",
    2: "Zona azul/verde", 3: "Zona azul/verde", 4: "Zona amarilla",
    5: "Zona amarilla/roja", 6: "Zona roja", 7: "Zona roja/Yermos", 8: "Yermos (zona negra)",
}

# Rangos reales de recolección de la Tabla del Destino que desbloquean la
# herramienta necesaria para recolectar cada tier. Fuente: wiki oficial de
# Albion Online (wiki.albiononline.com/wiki/Tiers), consultado julio 2026.
#
# Esto es lo que de verdad determina si PUEDES recolectar un tier o no —
# la especialización (maestria_recoleccion, ver arriba) solo da el bono de
# rendimiento UNA VEZ que ya desbloqueaste el rango. T1 no requiere rango.
GATHERING_RANKS = [
    {"id": "novato",       "nombre": "Novato",       "tier": 2},
    {"id": "aprendiz",     "nombre": "Aprendiz",     "tier": 3},
    {"id": "adepto",       "nombre": "Adepto",       "tier": 4},
    {"id": "experto",      "nombre": "Experto",      "tier": 5},
    {"id": "maestro",      "nombre": "Maestro",      "tier": 6},
    {"id": "gran_maestro", "nombre": "Gran Maestro", "tier": 7},
    {"id": "anciano",      "nombre": "Anciano",      "tier": 8},
]
GATHERING_RANK_TIER = {r["id"]: r["tier"] for r in GATHERING_RANKS}

# Consumibles de recolección más mencionados en guías de la comunidad. Sin
# números exactos de bono porque Sandbox Interactive no publica una tabla
# oficial verificable — es orientativo, no una promesa de rendimiento.
GATHERING_CONSUMABLES = [
    {"nombre": "Pastel de Cerdo", "tipo": "Comida", "efecto": "El más usado por recolectores: sube tu rendimiento de recolección y tu capacidad de carga durante 30 minutos."},
    {"nombre": "Pastel de Pescado", "tipo": "Comida", "efecto": "Da más resistencia frente a otros jugadores y velocidad de recolección."},
    {"nombre": "Pastel de Ojo Muerto Dos Picos", "tipo": "Comida", "efecto": "Ayuda contra control de multitudes y mejora el retorno de recursos — suele ser caro, a criterio propio."},
    {"nombre": "Poción de Gigantismo Mayor", "tipo": "Poción", "efecto": "Aumenta capacidad de carga y vida máxima — útil para sacar más material por viaje."},
    {"nombre": "Poción de Resistencia Mayor", "tipo": "Poción", "efecto": "Mejora tus defensas y resistencia a control de multitudes — para sobrevivir en zonas rojas/negras."},
    {"nombre": "Poción de Invisibilidad", "tipo": "Poción", "efecto": "Te vuelve invisible unos segundos — para escapar si te detectan en zona peligrosa."},
]

# Monturas con uso real de transporte (cargan peso extra). IDs verificados contra
# el catálogo de la API de Albion Online Data Project.
MOUNTS = [
    {"id": "T3_MOUNT_OX", "name": "Buey", "tier": 3},
    {"id": "T4_MOUNT_OX", "name": "Buey", "tier": 4},
    {"id": "T5_MOUNT_OX", "name": "Buey", "tier": 5},
    {"id": "T6_MOUNT_OX", "name": "Buey", "tier": 6},
    {"id": "T7_MOUNT_OX", "name": "Buey", "tier": 7},
    {"id": "T8_MOUNT_OX", "name": "Buey", "tier": 8},
    {"id": "T8_MOUNT_MAMMOTH_TRANSPORT", "name": "Mamut", "tier": 8},
    {"id": "T4_MOUNT_GIANTSTAG", "name": "Ciervo Gigante", "tier": 4},
    {"id": "T6_MOUNT_GIANTSTAG_MOOSE", "name": "Alce", "tier": 6},
    {"id": "T3_MOUNT_HORSE", "name": "Caballo", "tier": 3},
    {"id": "T4_MOUNT_HORSE", "name": "Caballo", "tier": 4},
    {"id": "T5_MOUNT_HORSE", "name": "Caballo", "tier": 5},
    {"id": "T6_MOUNT_HORSE", "name": "Caballo", "tier": 6},
    {"id": "T7_MOUNT_HORSE", "name": "Caballo", "tier": 7},
    {"id": "T8_MOUNT_HORSE", "name": "Caballo", "tier": 8},
    {"id": "T6_MOUNT_DIREWOLF", "name": "Huargo", "tier": 6},
    {"id": "T5_MOUNT_COUGAR_KEEPER@1", "name": "Garra Veloz", "tier": 5},
]


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

        historico_rows = [{
            "item_id": r["item_id"],
            "city": r["city"],
            "sell_price_min": r["sell_price_min"],
            "buy_price_max": r["buy_price_max"],
        } for r in rows]
        supabase.table("precios_historico").insert(historico_rows).execute()

        compute_and_store_margins(rows, cfg)

    fetch_and_store_mount_prices(host)
    fetch_and_store_volume(host)


def fetch_and_store_volume(host):
    """Trae el volumen de transacciones (item_count) desde AODP y lo guarda en
    volumen_historico. item_count = unidades COMPRAVENDIDAS en esa franja, no
    la cantidad disponible en el mercado ahora mismo (Albion no expone eso).
    Se corre junto al fetch principal, mismo cron cada hora / mismo botón manual.

    IMPORTANTE: guardamos la hora REAL de cada punto que reporta AODP (su
    campo "timestamp"), no la hora en que corrió este cron. Antes solo
    tomábamos el último punto y lo insertábamos con ts=ahora — si AODP no
    tenía actividad nueva de ese item, terminábamos re-guardando el mismo
    valor viejo con una fecha fresca cada vez, y la gráfica mostraba barras
    idénticas hora tras hora (parecía "volumen constante" siendo en realidad
    el mismo dato repetido). El upsert de abajo evita duplicar un punto que
    ya teníamos guardado."""
    item_ids = ",".join(i["id"] for i in ITEMS)
    city_names = ",".join(c["id"] for c in CITIES)
    url = (f"https://{host}/api/v2/stats/history/{item_ids}.json"
           f"?locations={city_names}&time-scale=1")

    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"Error consultando historial (volumen) AODP: {e}")
        return

    rows = []
    for rec in data:
        item_id = rec.get("item_id")
        city = rec.get("location")
        puntos = rec.get("data") or []
        if not item_id or not city or not puntos:
            continue
        # AODP puede devolver varias franjas ya calculadas en una sola llamada;
        # nos quedamos con las últimas 48 (~2 días a time-scale=1) para no
        # reescanear de más en cada corrida.
        for punto in puntos[-48:]:
            ts = punto.get("timestamp")
            if not ts:
                continue
            rows.append({
                "item_id": item_id,
                "city": city,
                "item_count": punto.get("item_count"),
                "avg_price": punto.get("avg_price"),
                "ts": ts,
            })

    # Postgres rechaza un upsert si DOS filas del mismo lote comparten la
    # llave del ON CONFLICT ("cannot affect row a second time") — y AODP
    # a veces sí repite el mismo (item_id, city, ts) dentro de una misma
    # respuesta. Nos quedamos con una sola fila por llave antes de enviar.
    dedup = {}
    for r in rows:
        dedup[(r["item_id"], r["city"], r["ts"])] = r
    rows = list(dedup.values())

    if rows:
        supabase.table("volumen_historico").upsert(rows, on_conflict="item_id,city,ts").execute()
        print(f"Guardado volumen: {len(rows)} puntos (item/ciudad/hora), duplicados ya existentes se ignoran.")


def fetch_and_store_mount_prices(host):
    """Trae precios de las monturas de transporte (Buey, Mamut, Ciervo Gigante, Alce, Caballo).
    Se corre junto al fetch principal (mismo cron cada hora / mismo botón manual)."""
    item_ids = ",".join(m["id"] for m in MOUNTS)
    city_names = ",".join(c["id"] for c in CITIES)
    url = f"https://{host}/api/v2/stats/prices/{item_ids}.json?locations={city_names}&qualities=1"

    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"Error consultando AODP (monturas): {e}")
        return

    rows = []
    for rec in data:
        rows.append({
            "item_id": rec["item_id"],
            "city": rec["city"],
            "sell_price_min": rec.get("sell_price_min") or None,
            "sell_price_min_date": rec.get("sell_price_min_date") or None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })

    if rows:
        supabase.table("precios_monturas").upsert(rows, on_conflict="item_id,city").execute()
        print(f"Guardados {len(rows)} registros de precios de monturas.")


def compute_and_store_margins(rows, cfg):
    """Calcula el mejor margen por item con la config actual y lo guarda en el historial."""
    by_item = {}
    for r in rows:
        by_item.setdefault(r["item_id"], {})[r["city"]] = r

    item_name_lookup = {i["id"]: i["name"] for i in ITEMS}
    city_name_lookup = {c["id"]: c["name"] for c in CITIES}
    riesgo = cfg.get("riesgo_ciudades", {})
    tax = float(cfg.get("impuesto", 4)) / 100
    setup_fee = float(cfg.get("tarifa_publicacion", 2.5)) / 100
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
                costo_compra = buy_price * (1 + setup_fee)
                ingreso_venta = sell_price * (1 - tax - setup_fee)
                margin = ingreso_venta - costo_compra
                margin_pct = (margin / costo_compra) * 100
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
        mounts_json=json.dumps(MOUNTS),
        gathering_biome_json=json.dumps(GATHERING_BIOME),
        refining_bonus_json=json.dumps(REFINING_BONUS_CITY),
        raw_resource_labels_json=json.dumps(RAW_RESOURCE_LABELS),
        gathering_tier_names_json=json.dumps(GATHERING_TIER_NAMES),
        gathering_tier_zone_json=json.dumps(GATHERING_TIER_ZONE),
        gathering_consumables_json=json.dumps(GATHERING_CONSUMABLES),
        gathering_ranks_json=json.dumps(GATHERING_RANKS),
    )


@app.route("/api/monturas")
def api_monturas():
    res = supabase.table("precios_monturas").select("*").execute()
    return jsonify(res.data)


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


@app.route("/api/precios/historial")
def api_precios_historial():
    """Serie de tiempo de precio (compra/venta) para un material, opcionalmente
    filtrada por ciudad. Alimenta la pestaña 'Histórico de precios'."""
    item_id = request.args.get("item_id")
    city = request.args.get("city")
    dias = int(request.args.get("dias", 30))
    if not item_id:
        return jsonify({"error": "item_id requerido"}), 400

    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    query = (supabase.table("precios_historico")
             .select("*")
             .eq("item_id", item_id)
             .gte("ts", desde)
             .order("ts"))
    if city:
        query = query.eq("city", city)
    res = query.execute()
    return jsonify(res.data)


@app.route("/api/precios/volumen")
def api_precios_volumen():
    """Serie de tiempo de volumen transado para un material. NO es cantidad
    disponible en el mercado — es cuántas unidades se compravendieron."""
    item_id = request.args.get("item_id")
    city = request.args.get("city")
    dias = int(request.args.get("dias", 30))
    if not item_id:
        return jsonify({"error": "item_id requerido"}), 400

    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    query = (supabase.table("volumen_historico")
             .select("*")
             .eq("item_id", item_id)
             .gte("ts", desde)
             .order("ts"))
    if city:
        query = query.eq("city", city)
    res = query.execute()
    return jsonify(res.data)


def _ultimo_margen_por_item():
    """Último registro de margenes_historico por item (el más reciente de cada uno)."""
    rows = (supabase.table("margenes_historico")
            .select("*")
            .order("ts", desc=True)
            .limit(1000)
            .execute().data or [])
    out = {}
    for r in rows:
        if r["item_id"] not in out:
            out[r["item_id"]] = r
    return out


@app.route("/api/ordenes/tiempos")
def api_ordenes_tiempos():
    """Tiempo real que tardaron en venderse TUS órdenes completadas
    (seguimiento_ordenes.duracion_horas). Es el único dato real de 'tiempo
    de venta' disponible — AODP no lo rastrea para nadie."""
    item_id = request.args.get("item_id")
    query = (supabase.table("seguimiento_ordenes")
             .select("*")
             .not_.is_("duracion_horas", "null"))
    if item_id:
        query = query.eq("item_id", item_id)
    res = query.execute()
    ordenes = res.data or []

    por_item = {}
    for o in ordenes:
        por_item.setdefault(o["item_id"], []).append(o["duracion_horas"])

    margenes = _ultimo_margen_por_item()

    resumen = []
    for iid, duraciones in por_item.items():
        promedio_horas = sum(duraciones) / len(duraciones)
        margen = margenes.get(iid)
        # Estimado: cruza TU tiempo real de venta con el margen más reciente del
        # historial. Ojo — el margen es de la mejor ruta general del item, no
        # necesariamente la misma ruta exacta de cada orden puntual.
        retorno_hora = round(margen["margin"] / promedio_horas, 2) if margen and promedio_horas > 0 else None
        resumen.append({
            "item_id": iid,
            "item_name": ITEMS_BY_ID.get(iid, {}).get("name", iid),
            "promedio_horas": round(promedio_horas, 1),
            "min_horas": round(min(duraciones), 1),
            "max_horas": round(max(duraciones), 1),
            "muestras": len(duraciones),
            "retorno_por_hora": retorno_hora,
        })

    return jsonify(sorted(resumen, key=lambda x: x["promedio_horas"]))


@app.route("/api/precios/sugerencias")
def api_precios_sugerencias():
    """Lista de qué comprar, combinando: margen más reciente por item (mejor
    ruta), qué tan activo está su mercado (volumen relativo frente al resto
    del catálogo) y, si existe, tu retorno real por hora (margen / tiempo
    real de venta de tus órdenes). Los items con volumen bajo se penalizan
    en el score en vez de ocultarse — igual pueden ser buena idea, solo con
    más riesgo de tardar en vender."""
    dias = int(request.args.get("dias", 7))
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()

    vol_rows = (supabase.table("volumen_historico")
                .select("item_id,item_count")
                .gte("ts", desde)
                .execute().data or [])
    vol_por_item = {}
    for r in vol_rows:
        if r.get("item_count") is None:
            continue
        vol_por_item.setdefault(r["item_id"], []).append(r["item_count"])
    promedio_vol_por_item = {iid: sum(v) / len(v) for iid, v in vol_por_item.items() if v}

    valores_ordenados = sorted(promedio_vol_por_item.values())

    def categoria_volumen(item_id):
        v = promedio_vol_por_item.get(item_id)
        if v is None or not valores_ordenados:
            return "sin_datos"
        percentil = sum(1 for x in valores_ordenados if x <= v) / len(valores_ordenados)
        if percentil <= 0.33:
            return "bajo"
        if percentil >= 0.66:
            return "alto"
        return "medio"

    margenes = _ultimo_margen_por_item()

    ordenes = (supabase.table("seguimiento_ordenes")
               .select("item_id,duracion_horas")
               .not_.is_("duracion_horas", "null")
               .execute().data or [])
    horas_por_item = {}
    for o in ordenes:
        horas_por_item.setdefault(o["item_id"], []).append(o["duracion_horas"])
    promedio_horas_por_item = {iid: sum(h) / len(h) for iid, h in horas_por_item.items() if h}

    sugerencias = []
    for item_id, margen in margenes.items():
        vol_cat = categoria_volumen(item_id)
        promedio_horas = promedio_horas_por_item.get(item_id)
        retorno_hora = round(margen["margin"] / promedio_horas, 2) if promedio_horas and promedio_horas > 0 else None

        score = retorno_hora if retorno_hora is not None else margen["margin_pct"]
        if score is not None:
            if vol_cat == "bajo":
                score = score * 0.5
            elif vol_cat == "sin_datos":
                score = score * 0.75

        sugerencias.append({
            "item_id": item_id,
            "item_name": margen["item_name"],
            "origin": margen["origin"],
            "dest": margen["dest"],
            "margin": margen["margin"],
            "margin_pct": margen["margin_pct"],
            "volumen_categoria": vol_cat,
            "promedio_horas_venta": round(promedio_horas, 1) if promedio_horas else None,
            "retorno_por_hora": retorno_hora,
            "score": round(score, 2) if score is not None else None,
        })

    sugerencias.sort(key=lambda s: (s["score"] is None, -(s["score"] or 0)))
    return jsonify(sugerencias)


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


def limpiar_bbcode(texto):
    """Steam devuelve el cuerpo de la noticia en BBCode, no en texto plano.
    Quita imágenes, videos y etiquetas de formato para que no se cuelen URLs
    crudas de imagen dentro de las notas."""
    if not texto:
        return ""
    t = texto
    t = re.sub(r"\[img\].*?\[/img\]", "", t, flags=re.I | re.S)
    t = re.sub(r"\[previewyoutube[^\]]*\].*?\[/previewyoutube\]", "", t, flags=re.I | re.S)
    t = re.sub(r"\[url=[^\]]*\](.*?)\[/url\]", r"\1", t, flags=re.I | re.S)
    t = re.sub(r"\[/?[a-zA-Z0-9\*]+(=[^\]]*)?\]", "", t)  # [b] [/b] [h1] [list] [*] etc.
    # Por si queda una URL de imagen suelta como texto plano (sin corchetes)
    t = re.sub(r"(https?:)?//\S+\.(jpg|jpeg|png|gif|webp)\b", "", t, flags=re.I)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def traducir_es(texto):
    """Traduce a español con DeepL si hay DEEPL_API_KEY configurada en las
    variables de entorno de Render. Sin la key, o si la llamada falla por
    cualquier motivo, devuelve el texto original (inglés) sin romper nada."""
    if not DEEPL_API_KEY or not texto:
        return texto
    # Las keys del plan free de DeepL siempre terminan en ":fx" y usan
    # api-free.deepl.com; cualquier otra key (Pro) usa api.deepl.com. Un 403
    # Forbidden casi siempre es justo esto: pegarle al host que no es.
    host = "api-free.deepl.com" if DEEPL_API_KEY.endswith(":fx") else "api.deepl.com"
    try:
        resp = requests.post(
            f"https://{host}/v2/translate",
            headers={"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"},
            data={"text": texto, "target_lang": "ES"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["translations"][0]["text"]
    except requests.exceptions.HTTPError as e:
        print(f"Traducción DeepL falló ({host}), se deja en inglés: {e} — respuesta: {resp.text[:300]}")
        return texto
    except Exception as e:
        print(f"Traducción DeepL falló ({host}), se deja en inglés: {e}")
        return texto


@app.route("/api/eventos/actualizar", methods=["POST"])
def api_eventos_actualizar():
    """Trae los anuncios oficiales recientes del Steam News Hub de Albion Online
    y los agrega como eventos, sin duplicar. Es la fuente más confiable con
    acceso público que encontré — el sitio oficial y el foro de Albion bloquean
    el scraping directo con protección anti-bot, así que no se puede leer de ahí."""
    try:
        res = requests.get(
            "https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/",
            # maxlength=0 = contenido completo sin truncar a la mitad de una
            # etiqueta BBCode (eso era lo que dejaba URLs de imagen colgando).
            # Truncamos nosotros mismos, ya limpio, más abajo.
            params={"appid": STEAM_APP_ID_ALBION, "count": 15, "maxlength": 0, "format": "json"},
            timeout=15,
        )
        res.raise_for_status()
        items = (res.json().get("appnews") or {}).get("newsitems") or []
    except Exception as e:
        return jsonify({"error": f"No se pudo consultar Steam: {e}"}), 502

    existentes = (supabase.table("eventos_economia")
                  .select("fuente_id")
                  .not_.is_("fuente_id", "null")
                  .execute().data or [])
    ids_existentes = {e["fuente_id"] for e in existentes}

    def clasificar(titulo, contenido):
        """Heurística simple por palabras clave en el texto ORIGINAL en inglés
        (antes de traducir) — no es perfecta, edítalo a mano en Supabase si
        alguna queda mal clasificada."""
        texto = f"{titulo} {contenido}".lower()
        if any(p in texto for p in ["hotfix", "bugfix", "bug fix"]):
            return "parche", "bajo"
        if "expansion" in texto:
            return "expansion", "alto"
        if any(p in texto for p in ["season", "anniversary"]):
            return "evento", "alto"
        if any(p in texto for p in ["patch", "update", "balance", "nerf", "buff"]):
            return "parche", "medio"
        return "evento", "medio"

    nuevos = []
    for item in items:
        gid = str(item.get("gid") or "")
        titulo_en = (item.get("title") or "").strip()
        if not gid or not titulo_en or gid in ids_existentes:
            continue

        contenido_en = limpiar_bbcode(item.get("contents") or "")
        fecha = datetime.fromtimestamp(item.get("date", 0), tz=timezone.utc).date().isoformat()
        tipo, impacto = clasificar(titulo_en, contenido_en)

        resumen_en = contenido_en[:350]
        recortado = len(contenido_en) > 350

        titulo = traducir_es(titulo_en)
        resumen = traducir_es(resumen_en)
        notas = resumen + ("..." if recortado else "")
        if item.get("url"):
            notas = f"{notas}\n{item['url']}"

        nuevos.append({
            "fecha": fecha, "titulo": titulo, "tipo": tipo, "impacto": impacto,
            "notas": notas, "fuente": "steam", "fuente_id": gid,
        })
        ids_existentes.add(gid)  # por si Steam repite el mismo gid en la misma respuesta

    if nuevos:
        supabase.table("eventos_economia").insert(nuevos).execute()

    return jsonify({"agregados": len(nuevos), "revisados": len(items)})


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


def _ganancia_venta(venta, precio_oro):
    """Ganancia de una venta parcial, calculada siempre al vuelo a partir del
    precio_venta guardado — así, si editas el precio de una venta pendiente,
    la ganancia se recalcula sola en el próximo GET, sin tener que tocar
    ninguna columna aparte."""
    precio_venta_neto = float(venta["precio_venta"]) * (1 - float(venta.get("tax_pct") or 0) / 100)
    return round((precio_venta_neto - float(precio_oro)) * float(venta["cantidad"]), 2)


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
            "city_compra": body.get("city_compra") or None,
            "city": body["city"],
            "precio_oro": body["precio_oro"],
            "cantidad": body.get("cantidad", 1),
            "nota": body.get("nota") or None,
            "origen": body.get("origen") if body.get("origen") in ("compra", "recoleccion") else "compra",
        }
        res = supabase.table("compras_manual").insert(nueva).execute()
        compra_id = res.data[0]["id"]

        # "ya_comprado" = True (default) es el caso simple: compraste instantáneo,
        # ya tienes las unidades en la mano — se registra de una vez como una
        # ejecución completa. False = es una ORDEN que se va a ir llenando de a
        # poco (ej. "puse orden de compra de 100 pociones a 1580") — se crea el
        # registro sin ninguna ejecución todavía; las vas agregando con
        # /comprar a medida que el juego confirme fills, y puedes seguir
        # ajustando "precio_oro" y "cantidad" de la orden mientras tanto sin
        # perder el precio real al que ya compraste cada parte.
        if body.get("ya_comprado", True):
            supabase.table("compras_ejecuciones").insert({
                "compra_id": compra_id,
                "cantidad": nueva["cantidad"],
                "precio_pagado": nueva["precio_oro"],
            }).execute()

        return jsonify(res.data), 201

    compras = supabase.table("compras_manual").select("*").order("fecha_creacion", desc=True).execute().data
    if not compras:
        return jsonify([])

    ids = [c["id"] for c in compras]
    ventas_res = supabase.table("compras_ventas").select("*").in_("compra_id", ids).order("fecha", desc=True).execute()
    ventas_por_compra = {}
    for v in ventas_res.data:
        ventas_por_compra.setdefault(v["compra_id"], []).append(v)

    ejecuciones_res = supabase.table("compras_ejecuciones").select("*").in_("compra_id", ids).order("fecha", desc=True).execute()
    ejecuciones_por_compra = {}
    for e in ejecuciones_res.data:
        ejecuciones_por_compra.setdefault(e["compra_id"], []).append(e)

    # Cada compra trae su lista de ventas parciales Y su lista de ejecuciones
    # de compra (puede estar vacía cualquiera de las dos), con los totales ya
    # calculados para que el frontend no tenga que hacer la cuenta.
    #
    # Lado COMPRA:
    # - cantidad_comprada = unidades que YA se pagaron de verdad (suma de
    #   ejecuciones). Es lo único que realmente tienes en la mano.
    # - cantidad_pendiente_compra = lo que falta por llenar de la orden.
    # - precio_promedio_compra = costo real ponderado de lo comprado (puede
    #   diferir de "precio_oro" si ajustaste el precio a mitad de camino,
    #   ej. 18 uds a 1580 + el resto a 1583) — es la base real para calcular
    #   ganancia al vender, no el precio nominal con el que arrancó la orden.
    #
    # Lado VENTA (igual que antes):
    # - cantidad_comprometida = unidades con ALGUNA venta registrada, sea
    #   "pendiente" (ya listada, esperando que se venda) o "vendida"
    #   (confirmada). Reserva el stock para que no se pueda vender dos veces.
    # - "vendido" (cerrada por completo) solo es true cuando ya se compró
    #   todo Y no queda nada sin listar Y no queda ninguna venta sin confirmar.
    for c in compras:
        ejecuciones = ejecuciones_por_compra.get(c["id"], [])
        cantidad_comprada = sum(float(e["cantidad"]) for e in ejecuciones)
        costo_total_comprado = sum(float(e["cantidad"]) * float(e["precio_pagado"]) for e in ejecuciones)
        precio_promedio_compra = round(costo_total_comprado / cantidad_comprada, 4) if cantidad_comprada > 0 else float(c["precio_oro"])
        c["ejecuciones"] = ejecuciones
        c["cantidad_comprada"] = cantidad_comprada
        c["cantidad_pendiente_compra"] = round(float(c["cantidad"]) - cantidad_comprada, 6)
        c["costo_total_comprado"] = round(costo_total_comprado, 2)
        c["precio_promedio_compra"] = precio_promedio_compra

        ventas = ventas_por_compra.get(c["id"], [])
        confirmadas = [v for v in ventas if v.get("estado") == "vendida"]
        pendientes_v = [v for v in ventas if v.get("estado") != "vendida"]
        cantidad_comprometida = sum(float(v["cantidad"]) for v in ventas)
        c["ventas"] = ventas
        c["cantidad_vendida"] = sum(float(v["cantidad"]) for v in confirmadas)
        c["cantidad_pendiente_venta"] = sum(float(v["cantidad"]) for v in pendientes_v)
        c["cantidad_restante"] = round(float(c["cantidad"]) - cantidad_comprometida, 6)
        # "disponible_para_vender" limita a lo que REALMENTE ya está comprado —
        # no puedes listar para venta lo que la orden de compra aún no ha llenado.
        c["cantidad_disponible_venta"] = round(cantidad_comprada - cantidad_comprometida, 6)
        c["ganancia_acumulada"] = round(sum(_ganancia_venta(v, precio_promedio_compra) for v in confirmadas), 2)
        c["ganancia_pendiente_estimada"] = round(sum(_ganancia_venta(v, precio_promedio_compra) for v in pendientes_v), 2)
        c["vendido"] = (
            c["cantidad_pendiente_compra"] <= 0.0001
            and c["cantidad_restante"] <= 0.0001
            and c["cantidad_pendiente_venta"] <= 0.0001
        )

    return jsonify(compras)


@app.route("/api/compras/<int:compra_id>", methods=["PATCH"])
def api_compras_editar(compra_id):
    """Edita la orden de compra en sí: precio_oro (precio VIGENTE para lo que
    falta comprar) y/o cantidad (total deseado), además de ciudad/nota. No
    toca lo que ya se compró — eso queda guardado tal cual en
    compras_ejecuciones con el precio real que se pagó en su momento."""
    actual = supabase.table("compras_manual").select("*").eq("id", compra_id).single().execute()
    if not actual.data:
        return jsonify({"error": "no encontrada"}), 404

    body = request.get_json(silent=True) or {}
    cambios = {}
    if "precio_oro" in body:
        cambios["precio_oro"] = body["precio_oro"]
    if "cantidad" in body:
        ya_comprada = sum(float(e["cantidad"]) for e in
                           supabase.table("compras_ejecuciones").select("cantidad").eq("compra_id", compra_id).execute().data)
        if float(body["cantidad"]) < ya_comprada - 0.0001:
            return jsonify({"error": f"ya se compraron {ya_comprada} unidades, la cantidad total no puede bajar de eso"}), 400
        cambios["cantidad"] = body["cantidad"]
    if "city_compra" in body:
        cambios["city_compra"] = body["city_compra"] or None
    if "city" in body:
        cambios["city"] = body["city"]
    if "nota" in body:
        cambios["nota"] = body["nota"] or None
    if not cambios:
        return jsonify({"error": "nada que actualizar"}), 400

    res = supabase.table("compras_manual").update(cambios).eq("id", compra_id).execute()
    return jsonify(res.data)


@app.route("/api/compras/<int:compra_id>/comprar", methods=["POST"])
def api_compras_comprar(compra_id):
    """Registra que se llenó (total o parcialmente) la orden de compra — ej.
    'de las 100 que pedí, ya me vendieron 18 a 1580'. A diferencia de las
    ventas, una ejecución de compra ya es un hecho consumado apenas la
    registras (no tiene estado pendiente/confirmada): en Albion, cuando te
    llenan una orden de compra, la plata sale y el item llega en el mismo
    momento."""
    body = request.get_json(silent=True) or {}
    precio_pagado = body.get("precio_pagado")
    if precio_pagado is None:
        return jsonify({"error": "precio_pagado requerido"}), 400

    compra = supabase.table("compras_manual").select("*").eq("id", compra_id).single().execute()
    if not compra.data:
        return jsonify({"error": "no encontrada"}), 404

    cantidad_total = float(compra.data["cantidad"])
    ejecuciones_existentes = supabase.table("compras_ejecuciones").select("cantidad").eq("compra_id", compra_id).execute().data
    ya_comprada = sum(float(e["cantidad"]) for e in ejecuciones_existentes)
    pendiente = round(cantidad_total - ya_comprada, 6)

    cantidad = float(body.get("cantidad") or pendiente)
    if cantidad <= 0:
        return jsonify({"error": "esta orden ya se llenó por completo"}), 400
    if cantidad - pendiente > 0.0001:
        return jsonify({"error": f"solo faltan {pendiente} unidades por comprar en esta orden, no se pueden registrar {cantidad}"}), 400

    ejecucion = {"compra_id": compra_id, "cantidad": cantidad, "precio_pagado": precio_pagado}
    res = supabase.table("compras_ejecuciones").insert(ejecucion).execute()
    return jsonify(res.data), 201


@app.route("/api/compras/ejecuciones/<int:ejecucion_id>", methods=["PATCH"])
def api_compras_ejecucion_editar(ejecucion_id):
    """Corrige la cantidad y/o el precio pagado de una ejecución ya
    registrada, por si te equivocaste al anotarla."""
    ejecucion = supabase.table("compras_ejecuciones").select("*").eq("id", ejecucion_id).single().execute()
    if not ejecucion.data:
        return jsonify({"error": "no encontrada"}), 404

    body = request.get_json(silent=True) or {}
    cambios = {}
    if "precio_pagado" in body:
        cambios["precio_pagado"] = body["precio_pagado"]
    if "cantidad" in body:
        compra = supabase.table("compras_manual").select("cantidad").eq("id", ejecucion.data["compra_id"]).single().execute()
        otras = supabase.table("compras_ejecuciones").select("cantidad").eq("compra_id", ejecucion.data["compra_id"]).neq("id", ejecucion_id).execute().data
        ya_otras = sum(float(e["cantidad"]) for e in otras)
        if ya_otras + float(body["cantidad"]) - float(compra.data["cantidad"]) > 0.0001:
            return jsonify({"error": "esa cantidad excede el total de la orden de compra"}), 400
        cambios["cantidad"] = body["cantidad"]
    if not cambios:
        return jsonify({"error": "nada que actualizar"}), 400

    res = supabase.table("compras_ejecuciones").update(cambios).eq("id", ejecucion_id).execute()
    return jsonify(res.data)


@app.route("/api/compras/ejecuciones/<int:ejecucion_id>", methods=["DELETE"])
def api_compras_ejecucion_delete(ejecucion_id):
    supabase.table("compras_ejecuciones").delete().eq("id", ejecucion_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/compras/<int:compra_id>/vender", methods=["POST"])
def api_compras_vender(compra_id):
    """Registra una venta parcial como 'pendiente' — es decir, "puse la orden
    de venta a este precio", no "ya me pagaron". El precio se puede seguir
    editando mientras siga pendiente; confírmala con /marcar-vendida cuando
    de verdad se venda en el juego."""
    body = request.get_json(silent=True) or {}
    precio_venta = body.get("precio_venta")
    tax_pct = body.get("tax_pct", 0)  # % de impuesto de mercado, viene del input "atb-tax" del frontend
    if precio_venta is None:
        return jsonify({"error": "precio_venta requerido"}), 400

    actual = supabase.table("compras_manual").select("*").eq("id", compra_id).single().execute()
    if not actual.data:
        return jsonify({"error": "no encontrada"}), 404

    # El tope real para vender es lo que YA se compró de verdad (ejecuciones),
    # no el tamaño nominal de la orden — no puedes vender lo que aún no llenan.
    ejecuciones = supabase.table("compras_ejecuciones").select("cantidad, precio_pagado").eq("compra_id", compra_id).execute().data
    cantidad_comprada = sum(float(e["cantidad"]) for e in ejecuciones)
    costo_total = sum(float(e["cantidad"]) * float(e["precio_pagado"]) for e in ejecuciones)
    precio_promedio_compra = (costo_total / cantidad_comprada) if cantidad_comprada > 0 else float(actual.data["precio_oro"])

    ventas_existentes = supabase.table("compras_ventas").select("cantidad").eq("compra_id", compra_id).execute().data
    ya_comprometida = sum(float(v["cantidad"]) for v in ventas_existentes)  # pendientes + vendidas, todas reservan stock
    restante = round(cantidad_comprada - ya_comprometida, 6)

    # Si no mandan cantidad, se asume que están listando todo lo que queda disponible.
    cantidad = float(body.get("cantidad") or restante)
    if cantidad <= 0:
        return jsonify({"error": "no queda cantidad disponible para vender (revisa si ya se compró — no puedes vender lo que la orden aún no ha llenado)"}), 400
    if cantidad - restante > 0.0001:
        return jsonify({"error": f"solo quedan {restante} unidades disponibles para vender, no se pueden vender {cantidad}"}), 400

    venta = {
        "compra_id": compra_id,
        "cantidad": cantidad,
        "precio_venta": precio_venta,
        "tax_pct": tax_pct,
        "estado": "pendiente",
        # "ganancia" es NOT NULL en la tabla — se sigue mandando como foto
        # inicial para cumplir esa restricción, pero NO es la fuente de
        # verdad: el GET siempre recalcula al vuelo con _ganancia_venta()
        # usando el precio_venta actual Y el precio_promedio_compra actual,
        # así que editar cualquiera de los dos después no requiere tocar esta
        # columna para que el número mostrado sea correcto.
        "ganancia": _ganancia_venta({"precio_venta": precio_venta, "tax_pct": tax_pct, "cantidad": cantidad}, precio_promedio_compra),
    }
    res = supabase.table("compras_ventas").insert(venta).execute()
    return jsonify(res.data), 201


@app.route("/api/compras/ventas/<int:venta_id>", methods=["PATCH"])
def api_compras_venta_editar(venta_id):
    """Edita el precio (y opcionalmente la cantidad) de una venta parcial
    mientras siga 'pendiente' — para cuando hay que ir bajando el precio de
    la misma orden de venta. Una vez confirmada 'vendida', el precio queda fijo."""
    venta = supabase.table("compras_ventas").select("*").eq("id", venta_id).single().execute()
    if not venta.data:
        return jsonify({"error": "no encontrada"}), 404
    if venta.data.get("estado") == "vendida":
        return jsonify({"error": "esta venta ya está confirmada como vendida — no se puede editar el precio"}), 400

    body = request.get_json(silent=True) or {}
    cambios = {}
    if "precio_venta" in body:
        cambios["precio_venta"] = body["precio_venta"]
    if "cantidad" in body:
        cambios["cantidad"] = body["cantidad"]
    if not cambios:
        return jsonify({"error": "nada que actualizar"}), 400

    compra = supabase.table("compras_manual").select("precio_oro").eq("id", venta.data["compra_id"]).single().execute()
    venta_actualizada = {**venta.data, **cambios}
    cambios["ganancia"] = _ganancia_venta(venta_actualizada, compra.data["precio_oro"])

    res = supabase.table("compras_ventas").update(cambios).eq("id", venta_id).execute()
    return jsonify(res.data)


@app.route("/api/compras/ventas/<int:venta_id>/marcar-vendida", methods=["POST"])
def api_compras_venta_marcar_vendida(venta_id):
    """Confirma que una venta pendiente de verdad se vendió en el juego —
    el precio queda fijo desde este momento."""
    res = supabase.table("compras_ventas").update({
        "estado": "vendida",
        "fecha_vendida": datetime.now(timezone.utc).isoformat(),
    }).eq("id", venta_id).execute()
    if not res.data:
        return jsonify({"error": "no encontrada"}), 404
    return jsonify(res.data)


@app.route("/api/compras/ventas/<int:venta_id>/marcar-pendiente", methods=["POST"])
def api_compras_venta_marcar_pendiente(venta_id):
    """Por si confirmaste una venta por error — la regresa a 'pendiente' para
    poder editar el precio de nuevo."""
    res = supabase.table("compras_ventas").update({
        "estado": "pendiente",
        "fecha_vendida": None,
    }).eq("id", venta_id).execute()
    if not res.data:
        return jsonify({"error": "no encontrada"}), 404
    return jsonify(res.data)


@app.route("/api/compras/ventas/<int:venta_id>", methods=["DELETE"])
def api_compras_venta_delete(venta_id):
    venta = supabase.table("compras_ventas").select("*").eq("id", venta_id).single().execute()
    if not venta.data:
        return jsonify({"error": "no encontrada"}), 404
    supabase.table("compras_ventas").delete().eq("id", venta_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/compras/<int:compra_id>", methods=["DELETE"])
def api_compras_delete(compra_id):
    supabase.table("compras_ventas").delete().eq("compra_id", compra_id).execute()
    supabase.table("compras_ejecuciones").delete().eq("compra_id", compra_id).execute()
    supabase.table("compras_manual").delete().eq("id", compra_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/compras/<int:compra_id>/estado", methods=["POST"])
def api_compras_estado(compra_id):
    """Cancelar una compra (o reactivarla) sin borrar nada — las ventas
    parciales que ya tenga se conservan, porque dependen de esta compra."""
    body = request.get_json(silent=True) or {}
    estado = body.get("estado")
    if estado not in ("en_ejecucion", "cancelado"):
        return jsonify({"error": "estado inválido, debe ser 'en_ejecucion' o 'cancelado'"}), 400
    res = supabase.table("compras_manual").update({"estado": estado}).eq("id", compra_id).execute()
    if not res.data:
        return jsonify({"error": "no encontrada"}), 404
    return jsonify(res.data)


@app.route("/api/capital", methods=["GET", "POST"])
def api_capital():
    """Ledger de capital dedicado a trading: aportes (ej. plata que sale de
    convertir oro) y retiros (ej. plata que sacas de vuelta a otra cosa).
    No mueve nada de compras/ventas — es solo el registro de "cuánta plata
    le he dedicado a esto en total", para poder calcular cuánta queda libre."""
    if request.method == "POST":
        body = request.get_json() or {}
        tipo = body.get("tipo")
        monto = body.get("monto")
        if tipo not in ("aporte", "retiro"):
            return jsonify({"error": "tipo debe ser 'aporte' o 'retiro'"}), 400
        if not monto or float(monto) <= 0:
            return jsonify({"error": "monto debe ser mayor a 0"}), 400
        nuevo = {
            "tipo": tipo,
            "monto": float(monto),
            "nota": body.get("nota") or None,
        }
        res = supabase.table("capital_movimientos").insert(nuevo).execute()
        return jsonify(res.data), 201

    movimientos = supabase.table("capital_movimientos").select("*").order("fecha", desc=True).execute().data or []
    return jsonify(movimientos)


@app.route("/api/capital/<int:mov_id>", methods=["DELETE"])
def api_capital_delete(mov_id):
    supabase.table("capital_movimientos").delete().eq("id", mov_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/inventario", methods=["GET", "POST"])
def api_inventario():
    if request.method == "POST":
        body = request.get_json() or {}
        item = ITEMS_BY_ID.get(body.get("item_id"))
        if not item:
            return jsonify({"error": "item no reconocido"}), 400
        if not body.get("ciudad_banco"):
            return jsonify({"error": "ciudad_banco requerida"}), 400
        nuevo = {
            "item_id": item["id"],
            "item_name": item["name"],
            "ciudad_banco": body["ciudad_banco"],
            "cantidad": body.get("cantidad", 1),
            "precio_compra": body["precio_compra"],
            "nota": body.get("nota") or None,
        }
        res = supabase.table("inventario").insert(nuevo).execute()
        return jsonify(res.data), 201

    filas = (supabase.table("inventario").select("*")
             .order("fecha_creacion", desc=True).execute().data or [])

    # Precio de mercado actual en la MISMA ciudad donde está guardado cada item,
    # para poder calcular el % de cambio contra lo que pagaste.
    precios = (supabase.table("precios_actuales").select("*").execute().data or [])
    precio_por_item_ciudad = {(p["item_id"], p["city"]): p for p in precios}

    resultado = []
    for f in filas:
        precio_actual_row = precio_por_item_ciudad.get((f["item_id"], f["ciudad_banco"]))
        precio_actual = precio_actual_row["sell_price_min"] if precio_actual_row else None
        precio_compra = float(f["precio_compra"])
        pct_cambio = None
        if precio_actual is not None and precio_compra > 0:
            pct_cambio = round(((precio_actual - precio_compra) / precio_compra) * 100, 1)
        resultado.append({
            **f,
            "precio_actual": precio_actual,
            "pct_cambio": pct_cambio,
            "valor_total_compra": round(precio_compra * float(f["cantidad"]), 2),
            "valor_total_actual": round(precio_actual * float(f["cantidad"]), 2) if precio_actual is not None else None,
        })
    return jsonify(resultado)


@app.route("/api/inventario/<int:inv_id>", methods=["PATCH"])
def api_inventario_editar(inv_id):
    """Editar cantidad, precio de compra, ciudad o nota de un registro existente."""
    body = request.get_json() or {}
    campos_permitidos = {"cantidad", "precio_compra", "ciudad_banco", "nota"}
    cambios = {k: v for k, v in body.items() if k in campos_permitidos}
    if not cambios:
        return jsonify({"error": "nada que actualizar"}), 400
    res = supabase.table("inventario").update(cambios).eq("id", inv_id).execute()
    return jsonify(res.data)


@app.route("/api/inventario/<int:inv_id>", methods=["DELETE"])
def api_inventario_delete(inv_id):
    supabase.table("inventario").delete().eq("id", inv_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/sesiones-recoleccion", methods=["GET", "POST"])
def api_sesiones_recoleccion():
    """Una sesión de recolección = una salida. Puede tener varios materiales/tiers
    distintos adentro (registro_recoleccion), cada uno con su propio precio
    consultado en el momento en que se agregó."""
    if request.method == "POST":
        body = request.get_json() or {}
        nueva = {
            "hora_inicio": body.get("hora_inicio") or datetime.now(timezone.utc).isoformat(),
            "nota": body.get("nota") or None,
        }
        res = supabase.table("sesiones_recoleccion").insert(nueva).execute()
        return jsonify(res.data), 201
    # Se trae cada sesión con sus items recolectados anidados (join vía FK).
    res = (
        supabase.table("sesiones_recoleccion")
        .select("*, registro_recoleccion(*)")
        .order("hora_inicio", desc=True)
        .execute()
    )
    return jsonify(res.data)


@app.route("/api/sesiones-recoleccion/<int:sesion_id>/cerrar", methods=["POST"])
def api_sesiones_recoleccion_cerrar(sesion_id):
    res = supabase.table("sesiones_recoleccion").update({
        "hora_fin": datetime.now(timezone.utc).isoformat(),
    }).eq("id", sesion_id).execute()
    return jsonify(res.data)


@app.route("/api/sesiones-recoleccion/<int:sesion_id>/reparacion", methods=["POST"])
def api_sesiones_recoleccion_reparacion(sesion_id):
    """Se llama después de cerrada la sesión — normalmente solo sabes cuánto
    costó reparar cuando ya llegaste a la ciudad, no en el momento de cerrar."""
    body = request.get_json(silent=True) or {}
    costo_reparacion = body.get("costo_reparacion", 0) or 0
    res = supabase.table("sesiones_recoleccion").update({
        "costo_reparacion": costo_reparacion,
    }).eq("id", sesion_id).execute()
    return jsonify(res.data)


@app.route("/api/sesiones-recoleccion/<int:sesion_id>", methods=["DELETE"])
def api_sesiones_recoleccion_delete(sesion_id):
    # ON DELETE CASCADE en el schema se lleva los registros de esa sesión también.
    supabase.table("sesiones_recoleccion").delete().eq("id", sesion_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/recolecciones", methods=["GET", "POST"])
def api_recolecciones():
    if request.method == "POST":
        body = request.get_json()
        item = ITEMS_BY_ID.get(body["item_id"])
        if not item:
            return jsonify({"error": "item no reconocido"}), 400
        if not body.get("sesion_id"):
            return jsonify({"error": "falta sesion_id — primero inicia una sesión de recolección"}), 400
        nueva = {
            "sesion_id": body["sesion_id"],
            "item_id": item["id"],
            "item_name": item["name"],
            "tier": item["tier"],
            "cantidad": body.get("cantidad", 1),
            "ciudad_zona": body.get("ciudad_zona") or None,
            "precio_unitario": body.get("precio_unitario"),
            "precio_total": body.get("precio_total"),
            "precio_consultado_en": body.get("precio_consultado_en") or None,
            "nota": body.get("nota") or None,
        }
        res = supabase.table("registro_recoleccion").insert(nueva).execute()
        return jsonify(res.data), 201
    res = supabase.table("registro_recoleccion").select("*").order("fecha_creacion", desc=True).execute()
    return jsonify(res.data)


@app.route("/api/recolecciones/<int:reg_id>", methods=["DELETE"])
def api_recolecciones_delete(reg_id):
    supabase.table("registro_recoleccion").delete().eq("id", reg_id).execute()
    return jsonify({"deleted": True})


@app.route("/api/recolecciones/<int:reg_id>/vender", methods=["POST"])
def api_recolecciones_vender(reg_id):
    """Marca un material recolectado como vendido, con el precio REAL logrado
    (no el estimado que se guardó al recolectarlo). No usa capital de
    inversión — esto es ingreso de farmeo, se cuenta aparte en Inversión."""
    body = request.get_json(silent=True) or {}
    precio_venta_real = body.get("precio_venta_real")
    if precio_venta_real is None or float(precio_venta_real) < 0:
        return jsonify({"error": "precio_venta_real requerido"}), 400
    res = supabase.table("registro_recoleccion").update({
        "estado": "vendido",
        "precio_venta_real": float(precio_venta_real),
        "fecha_vendida": datetime.now(timezone.utc).isoformat(),
    }).eq("id", reg_id).execute()
    if not res.data:
        return jsonify({"error": "no encontrado"}), 404
    return jsonify(res.data)


@app.route("/api/recolecciones/<int:reg_id>/revertir", methods=["POST"])
def api_recolecciones_revertir(reg_id):
    """Por si marcaste una venta por error — la regresa a 'pendiente'."""
    res = supabase.table("registro_recoleccion").update({
        "estado": "pendiente",
        "precio_venta_real": None,
        "fecha_vendida": None,
    }).eq("id", reg_id).execute()
    if not res.data:
        return jsonify({"error": "no encontrado"}), 404
    return jsonify(res.data)


@app.route("/api/precio-vivo/<item_id>")
def api_precio_vivo(item_id):
    """Consulta el precio ACTUAL directo a la API del Albion Data Project para
    un solo item, en todas las ciudades — sin pasar por la tabla cacheada de
    precios_actuales (que solo se actualiza con el cron cada hora). Se usa al
    agregar cada material a una sesión de recolección, para que la
    rentabilidad de esa sesión se calcule con un precio realmente fresco."""
    item = ITEMS_BY_ID.get(item_id)
    if not item:
        return jsonify({"error": "item no reconocido"}), 404
    cfg = get_config()
    host = SERVER_HOSTS.get(cfg.get("servidor", "west"), SERVER_HOSTS["west"])
    city_names = ",".join(c["id"] for c in CITIES)
    url = f"https://{host}/api/v2/stats/prices/{item_id}.json?locations={city_names}&qualities=1"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        return jsonify({"error": f"No se pudo consultar el precio en vivo: {e}"}), 502
    return jsonify({"consultado_en": datetime.now(timezone.utc).isoformat(), "precios": data})


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











