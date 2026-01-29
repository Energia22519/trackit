import time
import json
import os
import time
import json
import os
import sys
import subprocess

# --- AUTO-INSTALADOR DE DEPENDENCIAS ---
def instalar_y_cargar(paquete):
    try:
        # Intentamos importar el paquete
        __import__(paquete)
    except ImportError:
        print(f"🔧 Instalando librería necesaria: {paquete}...")
        # Si falla, usamos pip para instalarlo
        subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode", "colorama", "pillow"])
        print(f"✅ {paquete} instalado correctamente.\n")

# Verificamos las librerías externas
# Nota: qrcode a veces necesita 'pillow' para generar imágenes, lo instalamos por si acaso
instalar_y_cargar("qrcode")
instalar_y_cargar("colorama")

# --- AHORA SÍ, IMPORTAMOS NORMALMENTE ---
import qrcode
from colorama import init, Fore, Style

init() # Iniciar colores

ARCHIVO_DATOS = "trackit_db.json"
ARCHIVO_EMPLEADOS = "empleados_db.json" # <--- NUEVO ARCHIVO

# --- FUNCIONES DE MEMORIA (INVENTARIO) ---
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, "r") as archivo:
                return json.load(archivo)
        except json.JSONDecodeError:
            return []
    return []

def guardar_datos(lista_actual):
    with open(ARCHIVO_DATOS, "w") as archivo:
        json.dump(lista_actual, archivo, indent=4)
    print("💾 Datos guardados.")

# --- NUEVA SECCIÓN: GESTIÓN DE RRHH ---
def inicializar_empleados_demo():
    """Si no existe la base de datos de empleados, crea una de prueba"""
    if not os.path.exists(ARCHIVO_EMPLEADOS):
        datos_demo = [
            {"id": "001", "nombre": "Ana Lopez", "departamento": "Direccion"},
            {"id": "002", "nombre": "Carlos Ruiz", "departamento": "IT"},
            {"id": "003", "nombre": "Maria Garcia", "departamento": "Marketing"},
            {"id": "004", "nombre": "David Villa", "departamento": "Ventas"}
        ]
        with open(ARCHIVO_EMPLEADOS, "w") as archivo:
            json.dump(datos_demo, archivo, indent=4)

def cargar_empleados():
    """Carga la lista de empleados autorizados"""
    if os.path.exists(ARCHIVO_EMPLEADOS):
        with open(ARCHIVO_EMPLEADOS, "r") as archivo:
            return json.load(archivo)
    return []

def validar_empleado(nombre_buscado):
    """Busca si el empleado existe en la base de datos de RRHH"""
    empleados = cargar_empleados()
    for emp in empleados:
        # Comparamos en minúsculas para evitar errores (ana == Ana)
        if emp["nombre"].lower() == nombre_buscado.lower():
            return emp # Devolvemos el diccionario completo del empleado
    return None # Si no lo encuentra

# --- INICIALIZACIÓN ---
inventario = cargar_datos()
inicializar_empleados_demo() # Creamos empleados falsos si es la primera vez

# --- FUNCIONES DEL SISTEMA ---
def registrar_activo():
    print(Fore.CYAN + "\n--- NUEVO ACTIVO ---" + Style.RESET_ALL)
    tipo = input("Tipo (PC/Monitor/Móvil): ").strip().capitalize()
    modelo = input("Modelo: ").strip()
    serial = input("Número de Serie: ").strip().upper()

    print("🖨️  Generando etiqueta digital...")
    contenido_qr = f"Propiedad de TrackIT\nTipo: {tipo}\nSerial: {serial}"
    img = qrcode.make(contenido_qr)
    
    nombre_carpeta = "etiquetas_qr"
    if not os.path.exists(nombre_carpeta):
        os.makedirs(nombre_carpeta)

    ruta_completa = os.path.join(nombre_carpeta, f"qr_{serial}.png")
    img.save(ruta_completa)

    nuevo_equipo = {
        "tipo": tipo,
        "modelo": modelo,
        "serial": serial,
        "estado": "Disponible",
        "asignado_a": "Almacén", # Por defecto
        "departamento": "N/A"    # Nuevo campo
    }
    
    inventario.append(nuevo_equipo)
    guardar_datos(inventario) 
    print(Fore.GREEN + f"✅ Activo registrado. Etiqueta en: {ruta_completa}" + Style.RESET_ALL)

def ver_inventario():
    print("\n" + "="*70)
    # Hemos añadido la columna USUARIO
    print(f"{'TIPO':<10} | {'MODELO':<15} | {'SERIAL':<10} | {'USUARIO (DEP)'}")
    print("-" * 70)
    
    for equipo in inventario:
        # Formato: Nombre (Departamento)
        info_usuario = f"{equipo['asignado_a']}"
        if equipo['asignado_a'] != "Almacén":
             info_usuario += f" ({equipo.get('departamento', 'N/A')})"
             
        print(f"{equipo['tipo']:<10} | {equipo['modelo']:<15} | {equipo['serial']:<10} | {info_usuario}")
    print("="*70 + "\n")

def asignar_equipo():
    print(Fore.CYAN + "\n--- ASIGNACIÓN DE EQUIPOS ---" + Style.RESET_ALL)
    serial_buscar = input("Introduce el SERIAL del equipo: ").strip().upper()
    
    # 1. Buscamos el equipo
    equipo_encontrado = None
    for equipo in inventario:
        if equipo["serial"] == serial_buscar:
            equipo_encontrado = equipo
            break
    
    if not equipo_encontrado:
        print(Fore.RED + "❌ Error: Equipo no encontrado." + Style.RESET_ALL)
        return # Salimos de la función si no hay equipo

    # 2. Si el equipo existe, pedimos el usuario y VALIDAMOS
    print(Fore.YELLOW + f"Equipo seleccionado: {equipo_encontrado['modelo']}" + Style.RESET_ALL)
    nombre_usuario = input("¿A qué empleado se le entrega? (Nombre y Apellido): ").strip()
    
    # --- AQUÍ ESTÁ LA MAGIA DE LA VALIDACIÓN ---
    empleado_valido = validar_empleado(nombre_usuario)
    
    if empleado_valido:
        # Si existe, sacamos sus datos reales del JSON de RRHH
        nombre_real = empleado_valido["nombre"]
        depto_real = empleado_valido["departamento"]
        
        equipo_encontrado["estado"] = "En Uso"
        equipo_encontrado["asignado_a"] = nombre_real
        equipo_encontrado["departamento"] = depto_real # Guardamos también el dep.
        
        guardar_datos(inventario)
        print(Fore.GREEN + f"✅ Asignado correctamente a {nombre_real} del departamento de {depto_real}." + Style.RESET_ALL)
    else:
        # Si no existe
        print(Fore.RED + "❌ ACCESO DENEGADO: Este empleado no figura en la base de datos de RRHH." + Style.RESET_ALL)
        print("Sugerencia: Prueba con 'Ana Lopez' o 'Carlos Ruiz' (Usuarios Demo).")

# --- MENÚ PRINCIPAL ---
def iniciar_trackit():
    print(f"🚀 Iniciando TrackIT v3.0... (Conexión RRHH Activa)")
    time.sleep(1)

    while True:
        print("\n--- MENÚ GESTIÓN IT ---")
        print("1. Registrar nuevo equipo")
        print("2. Ver inventario completo")
        print("3. Asignar equipo (Con validación RRHH)")
        print("4. Salir")
        
        opcion = input("Selecciona una opción: ")

        if opcion == "1":
            registrar_activo()
        elif opcion == "2":
            if not inventario:
                print("⚠️ Inventario vacío.")
            else:
                ver_inventario()
        elif opcion == "3":
            asignar_equipo()
        elif opcion == "4":
            print("Cerrando sistema...")
            break
        else:
            print("Opción no válida.")

iniciar_trackit()

