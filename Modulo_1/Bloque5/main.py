from aritmetica import sumar
import json

print("prueba de modulo de aritmetica")

print(sumar(5, 3))

# Crear json
respuesta_json = '{"texto": "Hola, soy una respuesta generada", "detalles": {"modelo": "nombre-del-modelo", "tokens": 12}}'
print(type(respuesta_json))
respuesta_dict = json.loads(respuesta_json)
print(type(respuesta_dict))
print(respuesta_dict)
print(respuesta_dict["texto"])
print(respuesta_dict["detalles"]["modelo"])

# una clave que no existe
# print(respuesta_dict["color"])
