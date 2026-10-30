"""
Dataset sintético etiquetado de prueba para la evaluación del Bloque 16.
Contiene casos de soporte con su correspondiente lista de tokens o conceptos esperados.
"""

CASOS_EVALUACION = [
    {
        "id": "caso_1",
        "descripcion": "Error de autenticacion en login",
        "entrada": "Error 401 en el login de produccion desde Santiago",
        "referencia_esperada": ["error", "401", "login", "produccion", "santiago"]
    },
    {
        "id": "caso_2",
        "descripcion": "Reinicio de contrasena de usuario",
        "entrada": "Solicitud de reinicio de clave para el usuario Juan Perez",
        "referencia_esperada": ["solicitud", "reinicio", "clave", "juan", "perez"]
    },
    {
        "id": "caso_3",
        "descripcion": "Caida de servicio o timeout",
        "entrada": "Timeout 504 al consultar la base de datos de clientes",
        "referencia_esperada": ["timeout", "504", "base", "datos", "clientes"]
    },
    {
        "id": "caso_4",
        "descripcion": "Consulta de facturacion mensual",
        "entrada": "Requiero la factura del mes de octubre para contabilidad",
        "referencia_esperada": ["factura", "mes", "octubre", "contabilidad"]
    },
    {
        "id": "caso_5",
        "descripcion": "Bloqueo de cuenta por intentos fallidos",
        "entrada": "Usuario bloqueado tras 5 intentos fallidos de acceso",
        "referencia_esperada": ["usuario", "bloqueado", "5", "intentos", "acceso"]
    }
]
