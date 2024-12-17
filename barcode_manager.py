import os
import cv2
from barcode import Code128
from barcode.writer import ImageWriter
from pyzbar.pyzbar import decode
from PIL import Image
import qrcode
import mysql.connector

# Configuración de la conexión a MySQL
DB_CONFIG = {
    "host": "localhost",
    "user": "salogod",
    "password": "117200513",
    "database": "productos_db",
    "port": 3360  # Asegúrate de que el puerto es correcto
}

try:
    # Crear conexión a la base de datos
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Crear la base de datos y tabla si no existen
    cursor.execute("CREATE DATABASE IF NOT EXISTS productos_db")
    cursor.execute("USE productos_db")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS productos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            producto VARCHAR(255) NOT NULL,
            descripcion TEXT NOT NULL,
            imagen LONGBLOB
        )
        """
    )

    # Función para convertir imagen a blob
    def imagen_a_blob(ruta):
        with open(ruta, "rb") as file:
            return file.read()

    # Función para guardar imagen desde blob
    def guardar_imagen_desde_blob(blob, ruta):
        with open(ruta, "wb") as file:
            file.write(blob)

    # Función para generar un código de barras
    def generar_codigo_barras(producto, descripcion):
        # Generar el código de barras y guardarlo como imagen
        codigo_barras = Code128(producto, writer=ImageWriter())
        filename = f"{producto}.png"
        codigo_barras.save(filename)

        # Guardar en la base de datos
        imagen_blob = imagen_a_blob(filename)
        cursor.execute(
            "INSERT INTO productos (producto, descripcion, imagen) VALUES (%s, %s, %s)",
            (producto, descripcion, imagen_blob)
        )
        connection.commit()
        print(f"Código de barras generado para '{producto}' y guardado como '{filename}'.")

    # Función para generar un código QR
    def generar_codigo_qr(producto, descripcion):
        # Generar el código QR y guardarlo como imagen
        qr = qrcode.QRCode(
            version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4
        )
        qr.add_data(producto)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        filename = f"{producto}_qr.png"
        img.save(filename)

        # Guardar en la base de datos
        imagen_blob = imagen_a_blob(filename)
        cursor.execute(
            "INSERT INTO productos (producto, descripcion, imagen) VALUES (%s, %s, %s)",
            (producto, descripcion, imagen_blob)
        )
        connection.commit()
        print(f"Código QR generado para '{producto}' y guardado como '{filename}'.")

    # Función para escanear un código de barras o QR
    def escanear_codigo():
        cap = cv2.VideoCapture(0)
        print("Apunta la cámara al código de barras o QR...")
        while True:
            _, frame = cap.read()
            for barcode in decode(frame):
                data = barcode.data.decode("utf-8")
                cap.release()
                cv2.destroyAllWindows()
                print(f"Código detectado: {data}")

                # Buscar en la base de datos
                cursor.execute("SELECT producto, descripcion, imagen FROM productos WHERE producto = %s", (data,))
                result = cursor.fetchone()
                if result:
                    producto, descripcion, imagen_blob = result
                    print(f"Producto: {producto}, Descripción: {descripcion}")
                    
                    # Guardar imagen desde blob
                    filename = f"{producto}_desde_db.png"
                    guardar_imagen_desde_blob(imagen_blob, filename)
                    print(f"Imagen recuperada y guardada como '{filename}'.")
                    return

                print("Producto no encontrado en la base de datos. ¿Deseas darlo de alta? (s/n)")
                opcion = input().lower()
                if opcion == "s":
                    descripcion = input("Descripción del producto: ")
                    cursor.execute(
                        "INSERT INTO productos (producto, descripcion) VALUES (%s, %s)",
                        (data, descripcion)
                    )
                    connection.commit()
                    print("Producto agregado a la base de datos.")
                return

            cv2.imshow("Escaneo de código", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

    # Menú principal
    while True:
        print("\nOpciones:")
        print("1. Generar código de barras")
        print("2. Generar código QR")
        print("3. Escanear código")
        print("4. Salir")
        opcion = input("Elige una opción: ")

        if opcion == "1":
            producto = input("Nombre del producto: ")
            descripcion = input("Descripción del producto: ")
            generar_codigo_barras(producto, descripcion)
        elif opcion == "2":
            producto = input("Nombre del producto: ")
            descripcion = input("Descripción del producto: ")
            generar_codigo_qr(producto, descripcion)
        elif opcion == "3":
            escanear_codigo()
        elif opcion == "4":
            print("Adiós.")
            break
        else:
            print("Opción no válida.")

except mysql.connector.Error as err:
    print(f"Error al conectar con MySQL: {err}")

finally:
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'connection' in locals() and connection.is_connected():
        connection.close()
