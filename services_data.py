"""
Datos del negocio LavaExpress La 43.
Atiende motos, carros, camionetas y vans.
"""

NOMBRE_NEGOCIO = "LavaExpress La 43"

HORARIO_ATENCION = "Todos los días de 8:00 AM a 8:00 PM (incluidos domingos y festivos)"

UBICACION = (
    "📍 Carrera 43 N 69-27, Manrique Central, Medellín\n"
    "Ver en mapa: https://maps.app.goo.gl/PmptaF8yAGWijrWH9"
)

METODOS_PAGO = "Efectivo y transferencia bancaria."

NUMERO_DUENO = "573183751236"

BASE_URL = "https://lavaexpress-bot.onrender.com"

MAX_CITAS_POR_HORA = 2

# Tipos de vehículo disponibles
TIPOS_VEHICULO = ["moto", "carro", "camioneta", "van", "taxi"]

# Precios: { servicio: { tipo_vehiculo: precio } }
SERVICIOS = {
    "moto": {
        "Super Premium + Cerámico (1 año)": 150000,
        "Super Premium + Cerámico (3 años)": 250000,
        "Super Premium + Cerámico (5 años)": 300000,
        "Full Polichado": 70000,
        "Full Lavado y Brillado con Cera": 35000,
        "Lavado Semi Full": 30000,
        "Lavado Tradicional": 25000,
    },
    "carro": {
        "Sencilla": 25000,
        "Semi": 33000,
        "Lavado Full + Motor + Brillado + Restauración externa": 100000,
        "Lavado + Brillado": 70000,
        "Lavado + Motor": 80000,
        "Lavado + Chasis": 80000,
        "Lavado + Motor + Chasis": 120000,
        "Lavado + Desmanchado + Brillo con Cera": 120000,
        "Lavado Full + Polichada completa": 300000,
        "Lavado + Limpieza profunda interior + Restauración": 90000,
        "Lavado + Limpieza profunda interior + Techo + Restauración": 120000,
        "Lavado + Over Hall": 250000,
        "Servicio Premium Completo": 400000,
        "Limpieza Profunda Interior": 140000,
    },
    "camioneta": {
        "Sencilla": 40000,
        "Semi": 60000,
        "Lavado Full + Motor + Brillado + Restauración externa": 120000,
        "Lavado + Brillado": 80000,
        "Lavado + Motor": 100000,
        "Lavado + Chasis": 100000,
        "Lavado + Motor + Chasis": 150000,
        "Lavado + Desmanchado + Brillo con Cera": 150000,
        "Lavado Full + Polichada completa": 350000,
        "Lavado + Limpieza profunda interior + Restauración": 100000,
        "Lavado + Limpieza profunda interior + Techo + Restauración": 150000,
        "Lavado + Over Hall": 300000,
        "Servicio Premium Completo": 600000,
        "Limpieza Profunda Interior": 150000,
    },
    "van": {
        "Sencilla": 50000,
        "Semi": 60000,
        "Lavado Full + Motor + Brillado + Restauración externa": 120000,
        "Lavado + Brillado": 80000,
        "Lavado + Motor": 100000,
        "Lavado + Chasis": 100000,
        "Lavado + Motor + Chasis": 150000,
        "Lavado + Desmanchado + Brillo con Cera": 150000,
        "Lavado Full + Polichada completa": 350000,
        "Lavado + Limpieza profunda interior + Restauración": 100000,
        "Lavado + Limpieza profunda interior + Techo + Restauración": 150000,
        "Lavado + Over Hall": 300000,
        "Servicio Premium Completo": 600000,
        "Limpieza Profunda Interior": 150000,
    },
    "taxi": {
    "Sencilla": 16000,
    "Semi": 25000,
    "Lavado Full + Motor + Brillado + Restauración externa": 85000,
    "Lavado + Brillado": 59500,
    "Lavado + Motor": 68000,
    "Lavado + Chasis": 68000,
    "Lavado + Motor + Chasis": 102000,
    "Lavado + Desmanchado + Brillo con Cera": 102000,
    "Limpieza Profunda Interior": 119000,
    },
}

DESCRIPCIONES_SERVICIOS = {
    "Super Premium + Cerámico (1 año)": (
        "Lavado full, desengrasado profundo de cada rincón de tu moto, restauración de partes negras "
        "con producto premium X5, desmanchada, pulida y aplicación de recubrimiento cerámico premium. "
        "Garantía de 1 año. Tiempo aproximado: 2 días."
    ),
    "Super Premium + Cerámico (3 años)": (
        "Lavado full, desengrasado profundo de cada rincón de tu moto, restauración de partes negras "
        "con producto premium X5, desmanchada, pulida y aplicación de recubrimiento cerámico premium. "
        "Garantía de 3 años. Tiempo aproximado: 2 días."
    ),
    "Super Premium + Cerámico (5 años)": (
        "Lavado full, desengrasado profundo de cada rincón de tu moto, restauración de partes negras "
        "con producto premium X5, desmanchada, pulida y aplicación de recubrimiento cerámico premium. "
        "Garantía de 5 años. Tiempo aproximado: 2 días."
    ),
    "Full Polichado": (
        "Lavado full, desengrasado profundo de cada rincón de tu moto, restauración de partes negras "
        "con producto premium X5, desmanchada, pulida y brillada. "
        "Tiempo aproximado: 2 horas."
    ),
    "Full Lavado y Brillado con Cera": (
        "Lavado full, desengrasado profundo de cada rincón de tu moto, restauración de partes negras "
        "con producto premium X5, desmanchada básica y aplicación de cera protectora. "
        "Tiempo aproximado: 2 horas."
    ),
    "Lavado Semi Full": (
        "Lavado full, desengrasado profundo de cada rincón de tu moto, restauración de partes negras "
        "con producto premium teflón. "
        "Tiempo aproximado: 1 hora."
    ),
    "Lavado Tradicional": (
        "Lavado full y desengrasado profundo de cada rincón de tu moto. "
        "Tiempo aproximado: 1 hora."
    ),
    "Limpieza Profunda Interior": (
        "Ideal si tu vehículo tiene suciedad acumulada, manchas, malos olores o simplemente quieres "
        "devolverle la sensación de vehículo nuevo. Incluye: lavado completo, aspirado profundo, "
        "limpieza de sillas, tapicería y alfombras, limpieza de tablero, puertas y compartimientos, "
        "restauración básica de plásticos interiores. "
        "Tiempo aproximado: 2-3 horas."
    ),
    "Servicio Premium Completo": (
        "Lavado + Over Hall + Polichado completo + Motor + Chasis. "
        "El servicio más completo disponible. Tiempo aproximado: 2 días."
    ),
    "Lavado + Over Hall": (
    "Desmonte total de todo el interior del vehículo incluyendo: silletería, alfombra, "
    "paneles plásticos, maleta y llanta de repuesto. Lavado a profundidad de cada parte "
    "interna, full aspirado, restauración con producto premium de carteras y tablero, "
    "limpieza profunda del techo interno. Adicional: lavado full general de todo el "
    "vehículo con shampoo de pH neutro. "
    "Tiempo aproximado: 2 días."
    ),
    "Lavado + Motor": (
    "Lavado de motor con técnicas profesionales garantizando el cuidado del motor y su "
    "funcionamiento. Se utilizan productos profesionales y 100% amigables con tu vehículo "
    "y el medio ambiente. Contamos con lavado en seco y lavado a presión, ambas técnicas "
    "100% garantizadas."
),
}

IMAGENES_SERVICIOS = {}  # Se agregan cuando estén disponibles las fotos


def formatear_precios(tipo_vehiculo: str) -> str:
    servicios = SERVICIOS.get(tipo_vehiculo, {})
    if not servicios:
        return "No encontré servicios para ese tipo de vehículo."
    lineas = []
    for nombre, precio in servicios.items():
        if precio is not None:
            precio_fmt = f"${precio:,}".replace(",", ".") + " COP"
        else:
            precio_fmt = "Según cotización"
        lineas.append(f"• {nombre}: {precio_fmt}")
    return "\n".join(lineas)


def url_imagen_servicio(nombre_servicio: str) -> str | None:
    archivo = IMAGENES_SERVICIOS.get(nombre_servicio)
    if not archivo:
        return None
    return f"{BASE_URL}/static/{archivo}"
