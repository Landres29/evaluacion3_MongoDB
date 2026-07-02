import json
from datetime import datetime
from pymongo import MongoClient

def conectar():
    """ [INDICADOR 3.1.1.I.1] Aplica filtros básicos para conectarse correctamente a MongoDB """
    try:
        # Intentamos conectar con un timeout de 3 segundos
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMs=3000)
        client.server_info() # Fuerza la validación de la conexión activa
        db = client["certamen3"]
        return db
    except Exception as e:
        print(f"\n[Error Crítico de Conexión] No se pudo conectar a MongoDB: {e}")
        print("Asegúrate de que el servicio de MongoDB esté iniciado.")
        exit(1)

# ==========================================
# CONFIGURACIÓN INICIAL / RESET DE DATOS
# ==========================================
def cargar_datos(db):
    print("\n  Cargando datos maestros en MongoDB...")
    db.invitados.drop()
    db.eventos.drop()

    try:
        # Carga de Invitados con su nombre de archivo correcto
        with open("invitados.json", "r", encoding="utf-8") as f:
            invitados = json.load(f)
        db.invitados.insert_many(invitados)
        print(f"  ✔  Colección 'invitados' poblada: {len(invitados)} registros.")

        # Carga de Eventos con su nombre de archivo correcto
        with open("eventos.json", "r", encoding="utf-8") as f:
            eventos = json.load(f)
        
        # Corrección de tipo de datos: Convertir Strings ISO a BSON Date nativos de MongoDB
        for ev in eventos:
            if "fecha" in ev and isinstance(ev["fecha"], str):
                fecha_limpia = ev["fecha"].replace("Z", "")
                ev["fecha"] = datetime.fromisoformat(fecha_limpia)

        db.eventos.insert_many(eventos)
        print(f"  ✔  Colección 'eventos' poblada: {len(eventos)} registros.")

        # Optimización mediante Índices
        db.invitados.create_index("rut", unique=True)
        db.eventos.create_index("codigo", unique=True)
        db.eventos.create_index("invitados.rut")
        print("  ✔  Índices de optimización y unicidad creados con éxito.")
    except FileNotFoundError as e:
        print(f"\n  [Error] Archivo JSON no encontrado: {e}")
        print("  Asegúrate de que 'invitados.json' y 'eventos.json' estén en esta misma carpeta.")
    except Exception as e:
        print(f"\n  [Error] Error al indexar o cargar: {e}")
    pausar()


# ==========================================
# UTILIDADES DE INTERFAZ Y SEGURIDAD
# ==========================================
def separar(titulo=""):
    ancho = 65
    if titulo:
        print(f"\n{'-'*ancho}")
        print(f" {titulo.upper()}")
        print(f"{'-'* ancho}")
    else:
        print(f"{'-'* ancho}")

def cabeza():
    print("\n"+"="*65)
    print("        SISTEMA DE GESTIÓN DE EVENTOS E INVITADOS - INACAP")
    print("               EVALUACIÓN CERTAMEN N°3 (MÁXIMO PUNTAJE)")
    print("=" * 65)

def pausar():
    input("\n Presiona [Enter] para continuar...")


# ==========================================
# FUNCIONES EJECUTORAS (PUNTOS DE LA RÚBRICA)
# ==========================================

def op1_listar_todos_eventos(db):
    """ [INDICADOR 3.1.1.I.2] Requerimiento 1: Lista todos los eventos """
    separar("Indicador 3.1.1.I.2 · Todos los Eventos Registrados")
    try:
        # Consultar la colección proyectando solo los campos solicitados de forma ordenada
        eventos = db.eventos.find({}, {"codigo": 1, "nombre": 1, "fecha": 1, "lugar": 1, "categoria": 1, "_id": 0}).sort("fecha", 1)
        total = 0
        for ev in eventos:
            fecha_str = ev["fecha"].strftime("%d/%m/%Y %H:%M") if isinstance(ev["fecha"], datetime) else str(ev["fecha"])
            print(f"\n  Código   : {ev['codigo']}")
            print(f"  Nombre   : {ev['nombre']}")
            print(f"  Fecha    : {fecha_str}")
            print(f"  Lugar    : {ev['lugar']}")
            print(f"  Categoría: {ev['categoria']}")
            separar()
            total += 1
        print(f"\n  Total de eventos listados en sistema: {total}")
    except Exception as e:
        print(f"  [Error] Falló la consulta de listado: {e}")
    pausar()

def op2_filtrar_por_categoria(db):
    """ [INDICADOR 3.1.1.I.3] Selecciona filtros adecuados según criterios específicos """
    separar("Indicador 3.1.1.I.3 · Consultar Eventos por Categoría")
    try:
        categorias = db.eventos.distinct("categoria")
        print(f"  Categorías activas en el sistema: {', '.join(categorias)}")
        
        # [3.1.4.I.10] Validación de entrada
        cat_buscar = input("\n  Ingrese la categoría exacta a filtrar: ").strip().lower()
        if not cat_buscar:
            print("  [Validación] El campo de búsqueda no puede estar vacío.")
            pausar()
            return

        eventos = db.eventos.find({"categoria": cat_buscar}, {"codigo": 1, "nombre": 1, "fecha": 1, "lugar": 1, "_id": 0})
        total = 0
        for ev in eventos:
            fecha_str = ev["fecha"].strftime("%d/%m/%Y %H:%M") if isinstance(ev["fecha"], datetime) else str(ev["fecha"])
            print(f"\n  [{ev['codigo']}] {ev['nombre']} | Lugar: {ev['lugar']} | Fecha: {fecha_str}")
            total += 1
        
        if total == 0:
            print(f"\n  No se encontraron registros bajo la categoría '{cat_buscar}'.")
    except Exception as e:
        print(f"  [Error] Ocurrió un error en el filtrado: {e}")
    pausar()

def op3_buscar_invitado_nombre_parcial(db):
    """ [INDICADOR 3.1.2.I.4] Requerimiento 2: Lista invitados filtrando por nombre parcial (case-insensitive) """
    separar("Indicador 3.1.2.I.4 · Buscar Invitado por Nombre Parcial (Regex)")
    
    termino = input("\n  Escriba el nombre (o fragmento) a buscar: ").strip()
    if len(termino) < 2:
        print("  [Validación] Ingrese al menos 2 caracteres para realizar la búsqueda con Regex.")
        pausar()
        return

    try:
        # $options: "i" garantiza el comportamiento Case-Insensitive (ignora mayúsculas/minúsculas)
        invitados = db.invitados.find(
            {"nombre": {"$regex": termino, "$options": "i"}}, 
            {"rut": 1, "nombre": 1, "correo": 1, "empresa": 1, "estado": 1, "_id": 0}
        )
        total = 0
        for inv in invitados:
            print(f"\n  {inv['nombre']} ({inv['rut']}) - Estado Cuenta: [{inv['estado'].upper()}]")
            print(f"  Correo : {inv['correo']} | Empresa: {inv['empresa']}")
            total += 1
        print(f"\n  Total de開coincidencias encontradas: {total}")
    except Exception as e:
        print(f"  [Error] Error al procesar la expresión regular: {e}")
    pausar()

def op4_buscar_por_dominio_correo(db):
    """ [INDICADOR 3.1.2.I.5] Aplica expresiones regulares para filtrar invitados por dominio de correo """
    separar("Indicador 3.1.2.I.5 · Filtrar por Dominio de Correo Electrónico")
    
    dominio = input("\n  Ingrese dominio corporativo (ej: empresa.cl, inacap.cl): ").strip().lower()
    if not dominio:
        print("  [Validación] Debe especificar un dominio.")
        pausar()
        return
    
    try:
        # El ancla '$' al final de la expresión regular obliga a que la cadena termine exactamente en @dominio
        patron_regex = f"@{dominio}$"
        invitados = db.invitados.find(
            {"correo": {"$regex": patron_regex, "$options": "i"}}, 
            {"rut": 1, "nombre": 1, "correo": 1, "empresa": 1, "_id": 0}
        )
        total = 0
        for inv in invitados:
            print(f"\n  • Nombre: {inv['nombre']:<25} RUT: {inv['rut']:<13} Correo: {inv['correo']}")
            total += 1
        print(f"\n  Total de cuentas asociadas al dominio '@{dominio}': {total}")
    except Exception as e:
        print(f"  [Error] Error en expresión regular de dominio: {e}")
    pausar()

def op5_busqueda_subdocumentos_confirmacion(db):
    """ [INDICADOR 3.1.3.I.6] Ejecuta búsquedas en subdocumentos (array invitados dentro de eventos) """
    separar("Indicador 3.1.3.I.6 · Listar Confirmados de un Evento (Subdocumentos)")
    
    cod_evento = input("\n  Ingrese el código del evento (ej: EVT-2025-001): ").strip().upper()
    try:
        # Recuperamos el evento y su lista de subdocumentos interna
        evento = db.eventos.find_one({"codigo": cod_evento}, {"nombre": 1, "invitados": 1, "_id": 0})
        if not evento:
            print(f"  [Error] El evento con código '{cod_evento}' no existe.")
            pausar()
            return
        
        print(f"\n  Evento seleccionado: {evento['nombre']}")
        # Filtramos la lista interna de subdocumentos mediante Python list comprehensions
        confirmados = [i for i in evento.get("invitados", []) if i["estado"] == "confirmado"]
        
        if not confirmados:
            print("  No existen subdocumentos con estado 'confirmado' para este evento.")
        else:
            print(f"  Subdocumentos de Invitados Confirmados hallados ({len(confirmados)}):\n")
            for conf in confirmados:
                # Cruzamos el RUT del subdocumento para traer sus datos personales completos de la otra colección
                inv_maestro = db.invitados.find_one({"rut": conf["rut"]}, {"nombre": 1, "empresa": 1, "_id": 0})
                nombre_inv = inv_maestro["nombre"] if inv_maestro else "Sin Registro Maestro"
                print(f"  -> RUT: {conf['rut']:<14} | Check-in: {str(conf['checkin']):<5} | Nombre: {nombre_inv}")
    except Exception as e:
        print(f"  [Error] Error al leer subdocumentos estructurados: {e}")
    pausar()

def op6_top3_eventos_agregacion(db):
    """ [INDICADOR 3.1.3.I.7] Requerimiento 4: Obtiene Top 3 eventos mediante consultas de agregación """
    separar("Indicador 3.1.3.I.7 · Pipeline de Agregación: Top 3 Eventos")
    try:
        # Construcción detallada del Pipeline de Agregación solicitado por la rúbrica
        pipeline = [
            {"$unwind": "$invitados"}, # Descompone el array de subdocumentos
            {"$match": {"invitados.estado": "confirmado"}}, # Filtra por criterios específicos
            {"$group": { # Agrupa calculando la métrica mediante sumadores aritméticos
                "_id": "$codigo",
                "nombre": {"$first": "$nombre"},
                "lugar": {"$first": "$lugar"},
                "total_confirmados": {"$sum": 1}
            }},
            {"$sort": {"total_confirmados": -1}}, # Ordenamiento descendente
            {"$limit": 3} # Restricción a las mejores 3 posiciones
        ]
        
        resultados = list(db.eventos.aggregate(pipeline))
        if not resultados:
            print("  No hay suficientes datos analíticos para procesar el ranking.")
        else:
            for posicion, ev in enumerate(resultados, 1):
                print(f"  Rank #{posicion} | [{ev['_id']}] {ev['nombre']}")
                print(f"          Ubicación: {ev['lugar']} | Total Confirmados: {ev['total_confirmados']}\n")
    except Exception as e:
        print(f"  [Error] Falló la ejecución del Framework de Agregación: {e}")
    pausar()

def op7_validar_acceso_lookup(db):
    """ [INDICADOR 3.1.4.I.8] Requerimiento 3: Valida acceso cruzando información con $lookup """
    separar("Indicador 3.1.4.I.8 · Validación Cruzada Relacional mediante $lookup")
    
    cod_evento = input("\n  Código del Evento a evaluar: ").strip().upper()
    rut_invitado = input("  RUT del Invitado a evaluar : ").strip()
    
    if not cod_evento or not rut_invitado:
        print("  [Validación] Ambos campos son estrictamente requeridos para efectuar el Join.")
        pausar()
        return

    try:
        # Pipeline complejo usando $lookup para unir físicamente documentos de colecciones distintas en caliente
        pipeline = [
            {"$match": {"codigo": cod_evento}},
            {"$unwind": "$invitados"},
            {"$match": {"invitados.rut": rut_invitado}},
            {"$lookup": {
                "from": "invitados",
                "localField": "invitados.rut",
                "foreignField": "rut",
                "as": "perfil_maestro"
            }},
            {"$unwind": "$perfil_maestro"},
            {"$project": {
                "_id": 0,
                "evento": "$nombre",
                "estado_en_evento": "$invitados.estado",
                "nombre_completo": "$perfil_maestro.nombre",
                "estado_cuenta": "$perfil_maestro.estado"
            }}
        ]
        
        resultado = list(db.eventos.aggregate(pipeline))
        print()
        if resultado:
            datos = resultado[0]
            print(f"  Resultado del Cruce de Datos ($lookup):")
            print(f"  - Invitado     : {datos['nombre_completo']}")
            print(f"  - Evento Target: {datos['evento']}")
            print(f"  - Condición Reg: {datos['estado_en_evento'].upper()}")
            print(f"  - Cuenta Global: {datos['estado_cuenta'].upper()}")
            
            # Validación lógica de reglas de negocio cruzadas
            if datos['estado_en_evento'] == "confirmado" and datos['estado_cuenta'] == "activo":
                print("\n  >>> [✔] ACCESO TOTALMENTE PERMITIDO AL EVENTO <<<")
            else:
                print("\n  >>> [✘] ACCESO DENEGADO: Cuenta bloqueada o estado no confirmado <<<")
        else:
            print("  >>> [✘] ACCESO DENEGADO: El RUT ingresado no está asignado a este evento <<<")
            
    except Exception as e:
        print(f"  [Error] Error al procesar el Stage de combinación ($lookup): {e}")
    pausar()


# ==========================================
# MENÚ CON INTERFAZ BASADO EN LA RÚBRICA
# ==========================================
def menu_principal(db):
    """ [INDICADOR 3.1.4.I.9] Organiza el código en una aplicación Python estructurada con menú """
    while True:
        cabeza()
        print("\n  Selecciona la opción de evaluación correspondiente:\n")
        print("  [1] [3.1.1.I.2] Listar TODOS los eventos en el sistema")
        print("  [2] [3.1.1.I.3] Filtro Avanzado: Consultar eventos por Categoría")
        print("  [3] [3.1.2.I.4] Buscar invitados por Nombre Parcial (Regex Case-Insensitive)")
        print("  [4] [3.1.2.I.5] Filtro Expresión Regular: Buscar por Dominio de Correo")
        print("  [5] [3.1.3.I.6] Búsqueda Anidada: Listar confirmados en Subdocumentos")
        print("  [6] [3.1.3.I.7] Top 3 Eventos con más Confirmados (Framework de Agregación)")
        print("  [7] [3.1.4.I.8] Validar Acceso de Invitado mediante Cruce de Colecciones ($lookup)")
        print("  -----------------------------------------------------------------")
        print("  [8] [Herramienta] Cargar / Resetear Base de Datos ('certamen3')")
        print("  [0] Salir de la Aplicación")
        
        # [3.1.4.I.10] Sanitización y Validación del menú
        opcion = input("\n  Escriba el número de opción: ").strip()
        
        if opcion == "1":   op1_listar_todos_eventos(db)
        elif opcion == "2": op2_filtrar_por_categoria(db)
        elif opcion == "3": op3_buscar_invitado_nombre_parcial(db)
        elif opcion == "4": op4_buscar_por_dominio_correo(db)
        elif opcion == "5": op5_busqueda_subdocumentos_confirmacion(db)
        elif opcion == "6": op6_top3_eventos_agregacion(db)
        elif opcion == "7": op7_validar_acceso_lookup(db)
        elif opcion == "8": cargar_datos(db)
        elif opcion == "0":
            print("\n  Aplicación finalizada correctamente. ¡Éxito en tu Certamen!")
            break
        else:
            print("\n  [Alerta] Opción inválida. Digite un número entre 0 y 8.")
            pausar()

if __name__ == "__main__":
    # Inicialización del aplicativo
    db_mongo = conectar()
    menu_principal(db_mongo)



"""Plantilla 1: Para consultas de FILTROS (Coincidencia exacta)
La usas si te pide buscar valores fijos. Ej: "Buscar eventos en el 'Auditorio A'" o "Invitados con estado 'activo'".

Python"""
def opcion_filtro_inacap(db):
    separar("Consulta de Filtros Básicos")
    
    # 1. Capturamos el dato que te dicte la profesora en el examen
    valor_buscar = input("Ingrese el valor exacto a filtrar: ").strip()
    
    try:
        # 2. LA ESTRUCTURA DEL FILTRO
        filtro = {
            "categoria": valor_buscar  # <=== CAMBIAR AQUÍ: Reemplaza "categoria" por el campo que te pida la profe (ej: "lugar", "estado", "empresa")
        }
        
        # 3. Se ejecuta la consulta (No cambies db.eventos a menos que te pida buscar en la colección db.invitados)
        resultados = db.eventos.find(filtro)  # <=== CAMBIAR AQUÍ: Si te pide buscar invitados directos, cambia db.eventos por db.invitados
        
        print("\nResultados encontrados:")
        for doc in resultados:
            # 4. Mostrar los datos en pantalla
            print(f" -> {doc['nombre']}") # <=== CAMBIAR AQUÍ: Cambia "nombre" por el campo que quieras mostrar (ej: doc['lugar'] o doc['correo'])
            
    except Exception as e:
        print(f" Error en la consulta: {e}")
    pausar()
"""Plantilla 2: Para consultas de EXPRESIONES REGULARES ($regex)
La usas si te pide búsquedas parciales. Ej: "Nombres que empiecen con 'Ma'" o "Correos que terminen en '@inacap.cl'".

Python"""
def opcion_regex_inacap(db):
    separar("Consulta con Expresiones Regulares ($regex)")
    texto_parcial = input("Ingrese el texto parcial a buscar: ").strip()
    
    try:
        # 2. LA ESTRUCTURA REGEX
        filtro_regex = {
            "nombre": {  # <=== CAMBIAR AQUÍ: Reemplaza "nombre" por el campo de texto a evaluar (ej: "correo", "rut", "empresa")
                "$regex": f"^{texto_parcial}", # <=== TORPEDO DE CLASES: Deja el '^' si te pide "que empiece con". Borra el '^' si te pide "que contenga". Pon un '$' al final si te pide "que termine en" (ej: f"{texto_parcial}$")
                "$options": "i" # La 'i' de INACAP: No la toques, sirve para ignorar mayúsculas/minúsculas
            }
        }
        
        # 3. Se ejecuta la consulta
        resultados = db.eventos.find(filtro_regex) # <=== CAMBIAR AQUÍ: Si te pide buscar en invitados maestros, cambia db.eventos por db.invitados
        
        print("\nResultados coincidentes:")
        for doc in resultados:
            # 4. Mostrar los datos en pantalla
            print(f" -> {doc['nombre']}") # <=== CAMBIAR AQUÍ: Cambia "nombre" por la propiedad que quieras listar en la terminal
            
    except Exception as e:
        print(f" Error en la consulta: {e}")
    pausar()
"""Plantilla 3: Para subconsultas con $lookup (Cruzar colecciones)
La usas si te pide relacionar datos de ambas colecciones a la vez. Ej: "Mostrar el nombre real del invitado y el nombre del evento al que asiste".

Python"""
def opcion_lookup_inacap(db):
    separar("Subconsulta Relacional ($lookup)")
    try:
        # 1. EL PIPELINE (La lista de etapas)
        pipeline = [
            # Etapa A: Desarmamos el array interno de invitados que está en los eventos
            {"$unwind": "$invitados"}, # No lo toques, es obligatorio para abrir el array RUT por RUT
            
            # Etapa B: El $lookup (El JOIN de base de datos)
            {"$lookup": {
                "from": "invitados",           # <=== REVISAR: Es la colección foránea. En tu certamen se llama "invitados", no deberías cambiarlo.
                "localField": "invitados.rut",  # <=== REVISAR: El campo clave en el subdocumento del evento.
                "foreignField": "rut",          # <=== REVISAR: El campo clave coincidente en la colección de invitados.
                "as": "info_invitado"           # <=== REVISAR: El nombre de la "caja" temporal donde se guarda el cruce. Puedes dejarlo así.
            }},
            
            # Etapa C: Aplanamos el array que nos devolvió el $lookup para poder leerlo directo
            {"$unwind": "$info_invitado"}, # No lo toques, es obligatorio en la materia de INACAP
            
            # Etapa D: EL FILTRO POST-CRUCE (Opcional por si la profe te pide algo específico)
            # EJEMPLO: Si te dice "solo de la empresa INACAP", descomentas la línea de abajo:
            # {"$match": {"info_invitado.empresa": "INACAP"}}, # <=== CAMBIAR AQUÍ: Si te pide filtrar tras el cruce, cambia "info_invitado.empresa" por el campo físico (ej: "info_invitado.estado" o "lugar")
            
            # Etapa E: Limpieza de campos ($project)
            {"$project": {
                "_id": 0, # Deja el 0 para ocultar el código feo de Mongo
                "Evento": "$nombre",                  # <=== CAMBIAR AQUÍ: Crea los nombres que quieras. "$nombre" es el nombre del evento.
                "NombreInvitado": "$info_invitado.nombre", # <=== CAMBIAR AQUÍ: "$info_invitado.nombre" trae el nombre real desde la otra colección.
                "RutInvitado": "$info_invitado.rut"   # <=== CAMBIAR AQUÍ: Agrega o quita los campos que te pida listar la profesora.
            }}
        ]
        
        # 2. Se ejecuta con .aggregate() y se convierte a lista obligatoriamente
        resultados = list(db.eventos.aggregate(pipeline))
        
        print("\nDatos cruzados obtenidos con éxito:")
        for doc in resultados:
            # 3. Se imprimen usando los nombres exactos que inventaste arriba en la Etapa E ($project)
            print(f" -> Evento: {doc['Evento']} | Asiste: {doc['NombreInvitado']} (RUT: {doc['RutInvitado']})") # <=== CAMBIAR AQUÍ: Modifica el texto del print usando las claves que pusiste en el $project
            
    except Exception as e:
        print(f" Error en subconsulta: {e}")
    pausar()

"""cd desktop, cd EVALUACION3_MONGODB
   pip install pymongo
    python nombre_archivo.py """














def consulta_1_correos_confirmados(db):
    separar("Consulta 1: Correos de Invitados Confirmados ($lookup)")
    
    # 1. Capturamos el nombre del evento que te pida la profesora
    nombre_evento = input("  Ingrese el nombre del evento (ej: Expo Inacap): ").strip()
    
    try:
        # 2. El Pipeline con todas las etapas de la materia de INACAP
        pipeline = [
            # Etapa A: Filtramos para quedarnos SOLO con el evento que escribió la profe
            {"$match": {"nombre": {"$regex": nombre_evento, "$options": "i"}}},
            
            # Etapa B: Desarmamos el array de invitados interno del evento
            {"$unwind": "$invitados"},
            
            # Etapa C: Filtramos para dejar SOLO los que están "confirmado" en el evento
            {"$match": {"invitados.estado": "confirmado"}},
            
            # Etapa D: El $lookup para traer los datos reales (como el correo) desde la colección invitados
            {"$lookup": {
                "from": "invitados",
                "localField": "invitados.rut",
                "foreignField": "rut",
                "as": "perfil_maestro"
            }},
            
            # Etapa E: Aplanamos el array que nos devolvió el lookup
            {"$unwind": "$perfil_maestro"},
            
            # Etapa F: Limpiamos la pantalla con $project para mostrar solo lo pedido
            {"$project": {
                "_id": 0,
                "Evento": "$nombre",
                "Invitado": "$perfil_maestro.nombre",
                "Correo": "$perfil_maestro.correo"
            }}
        ]
        
        # 3. Ejecutamos la agregación y la pasamos a una lista
        resultados = list(db.eventos.aggregate(pipeline))
        
        if not resultados:
            print(f"\n  No se encontraron invitados confirmados para el evento '{nombre_evento}'.")
        else:
            print("\n  Invitados Confirmados y sus Correos:")
            for doc in resultados:
                print(f"  • Evento: {doc['Evento']} | {doc['Invitado']} -> Correo: {doc['Correo']}")
                
    except Exception as e:
        print(f"  [Error] Falló la subconsulta: {e}")
    pausar()


















    def consulta_2_categoria_evento(db):
    separar("Consulta 2: Categoría del Evento (Filtro)")
    
    # 1. Capturamos el nombre del evento
    nombre_evento = input("  Ingrese el nombre del evento a consultar: ").strip()
    
    try:
        # 2. Creamos el filtro usando una Expresión Regular por si no lo escribe exacto
        filtro = {
            "nombre": {"$regex": nombre_evento, "$options": "i"}
        }
        
        # 3. Ejecutamos con .find() y proyectamos solo el nombre y la categoría
        resultados = db.eventos.find(filtro, {"nombre": 1, "categoria": 1, "_id": 0})
        
        # Convertimos a lista para saber si encontró algo
        lista_resultados = list(resultados)
        
        if len(lista_resultados) == 0:
            print(f"\n  No se encontró ningún evento con el nombre '{nombre_evento}'.")
        else:
            print("\n  Resultados de la búsqueda:")
            for ev in lista_resultados:
                print(f"  • Evento: {ev['nombre']} | Categoría: {ev['categoria'].upper()}")
                
    except Exception as e:
        print(f"  [Error] Falló el filtro: {e}")
    pausar()
