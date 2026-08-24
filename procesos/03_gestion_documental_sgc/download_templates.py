import urllib.request
import os

def download_file(url, filename):
    print(f"Descargando {filename} desde {url}...")
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"¡Descargado exitosamente! Guardado en {os.path.abspath(filename)}")
    except Exception as e:
        print(f"Error al descargar {filename}: {e}")

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    
    # 1. Descargar Plantilla de Procedimiento
    url_procedimiento = "https://docs.google.com/document/d/1Xo89UONmHpq4vuLQw2q1441H1mhDN2ylGHbYs0Cgtew/export?format=docx"
    download_file(url_procedimiento, "templates/plantilla_procedimiento.docx")
    
    # 2. Descargar Plantilla de Norma
    url_norma = "https://docs.google.com/document/d/15af38Na4vo31XAhxaa8csFb0jgrK4t9QSw2rLNHNDCo/export?format=docx"
    download_file(url_norma, "templates/plantilla_norma.docx")
