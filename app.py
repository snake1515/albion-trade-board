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





