# ============================================================
# VOCABULARIO DEL ESPANOL REDUCIDO
# Las claves son palabras en minusculas. Las tuplas indican:
#   determinantes, sustantivos, adjetivos -> (genero, numero)
#   verbos -> (tiempo, numero), siempre en tercera persona
# Para ampliar el parser, agregar palabras en estas listas.
# ============================================================

DETERMINANTES = {
    "el": ("masculino", "singular"),
    "la": ("femenino", "singular"),
    "los": ("masculino", "plural"),
    "las": ("femenino", "plural"),
    "un": ("masculino", "singular"),
    "una": ("femenino", "singular"),
    "unos": ("masculino", "plural"),
    "unas": ("femenino", "plural"),
}

SUSTANTIVOS = {
    "niño": ("masculino", "singular"),
    "niños": ("masculino", "plural"),
    "niña": ("femenino", "singular"),
    "niñas": ("femenino", "plural"),
    "perro": ("masculino", "singular"),
    "perros": ("masculino", "plural"),
    "perra": ("femenino", "singular"),
    "perras": ("femenino", "plural"),
    "gato": ("masculino", "singular"),
    "gatos": ("masculino", "plural"),
    "gata": ("femenino", "singular"),
    "gatas": ("femenino", "plural"),
    "maestro": ("masculino", "singular"),
    "maestros": ("masculino", "plural"),
    "maestra": ("femenino", "singular"),
    "maestras": ("femenino", "plural"),
    "libro": ("masculino", "singular"),
    "libros": ("masculino", "plural"),
    "parque": ("masculino", "singular"),
    "parques": ("masculino", "plural"),
    "jardín": ("masculino", "singular"),
    "jardines": ("masculino", "plural"),
    "árbol": ("masculino", "singular"),
    "árboles": ("masculino", "plural"),
    "casa": ("femenino", "singular"),
    "casas": ("femenino", "plural"),
    "mesa": ("femenino", "singular"),
    "mesas": ("femenino", "plural"),
    "flor": ("femenino", "singular"),
    "flores": ("femenino", "plural"),
    "carta": ("femenino", "singular"),
    "cartas": ("femenino", "plural"),
    "pelota": ("femenino", "singular"),
    "pelotas": ("femenino", "plural"),
}

ADJETIVOS = {
    "alto": ("masculino", "singular"),
    "altos": ("masculino", "plural"),
    "alta": ("femenino", "singular"),
    "altas": ("femenino", "plural"),
    "pequeño": ("masculino", "singular"),
    "pequeños": ("masculino", "plural"),
    "pequeña": ("femenino", "singular"),
    "pequeñas": ("femenino", "plural"),
    "rojo": ("masculino", "singular"),
    "rojos": ("masculino", "plural"),
    "roja": ("femenino", "singular"),
    "rojas": ("femenino", "plural"),
    "nuevo": ("masculino", "singular"),
    "nuevos": ("masculino", "plural"),
    "nueva": ("femenino", "singular"),
    "nuevas": ("femenino", "plural"),
    "bonito": ("masculino", "singular"),
    "bonitos": ("masculino", "plural"),
    "bonita": ("femenino", "singular"),
    "bonitas": ("femenino", "plural"),
}

VERBOS = {
    "lee": ("presente", "singular"),
    "leen": ("presente", "plural"),
    "leyó": ("pasado", "singular"),
    "leyeron": ("pasado", "plural"),
    "mira": ("presente", "singular"),
    "miran": ("presente", "plural"),
    "miró": ("pasado", "singular"),
    "miraron": ("pasado", "plural"),
    "compra": ("presente", "singular"),
    "compran": ("presente", "plural"),
    "compró": ("pasado", "singular"),
    "compraron": ("pasado", "plural"),
    "busca": ("presente", "singular"),
    "buscan": ("presente", "plural"),
    "buscó": ("pasado", "singular"),
    "buscaron": ("pasado", "plural"),
    "lleva": ("presente", "singular"),
    "llevan": ("presente", "plural"),
    "llevó": ("pasado", "singular"),
    "llevaron": ("pasado", "plural"),
    "encuentra": ("presente", "singular"),
    "encuentran": ("presente", "plural"),
    "encontró": ("pasado", "singular"),
    "encontraron": ("pasado", "plural"),
    "visita": ("presente", "singular"),
    "visitan": ("presente", "plural"),
    "visitó": ("pasado", "singular"),
    "visitaron": ("pasado", "plural"),
    "come": ("presente", "singular"),
    "comen": ("presente", "plural"),
    "comió": ("pasado", "singular"),
    "comieron": ("pasado", "plural"),
}

ADVERBIOS = ["hoy", "ayer", "siempre", "rápidamente", "lentamente"]

PREPOSICIONES = ["a", "con", "de", "en", "para", "sobre", "bajo"]
