mensaje1=" HOLA MUndo   "
mensaje2="holA mUNDO"
# # upper convierte a MAYUSCULAS
# print(mensaje1.upper())
# print(mensaje2.upper())
# # lower convierte a minusculas
# print(mensaje1.lower())
# print(mensaje2.lower())
# # capitalize convierte la primera letra en Mayuscula
# print(mensaje2.capitalize())

mensaje1=mensaje1.lower()
mensaje2=mensaje2.lower()

# # strip elimina los espacios en blanco al inicio y final del texto
# print(mensaje1.strip())
# print(mensaje2.strip())

mensaje1=mensaje1.strip()
mensaje2=mensaje2.strip()



print(f"comparando [{mensaje1}] con [{mensaje2}]")
if mensaje1 == mensaje2:

    print("SON IGUALES")
else:
    print("SON DISTINTOS")

