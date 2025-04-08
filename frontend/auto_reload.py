import os
import time
import sys
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import psutil 

# Archivo principal de la app (usando Path para manejar rutas correctamente)
APP_FILE = Path("tesoreria_app.py").absolute()
# Obtener el directorio raíz del proyecto
ROOT_DIR = APP_FILE.parent

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, process):
        self.process = process
        self.last_modified = 0
        self.restart_pending = False
        # Lista de archivos a ignorar (puedes añadir más si es necesario)
        self.ignore_patterns = [
            "*.pyc", "*/__pycache__/*", "*.git/*", 
            "*/.idea/*", "*/.vscode/*", "*.log"
        ]
        
    def should_ignore(self, path):
        """Verifica si el archivo debe ser ignorado"""
        path_str = str(path).lower()
        return any(
            path_str.endswith(pattern.lower().strip("*")) or
            pattern.strip("*") in path_str
            for pattern in self.ignore_patterns
        )
    
    def restart_app(self):
        """Reinicia la aplicación de manera segura"""
        if self.restart_pending:
            return
            
        self.restart_pending = True
        print("🔄 Reiniciando aplicación...")
        
        try:
            # Terminar el proceso actual y todos sus hijos
            if self.process.poll() is None:  # Verificar si el proceso sigue vivo
                parent = psutil.Process(self.process.pid)
                
                # Terminar procesos hijos
                for child in parent.children(recursive=True):
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                
                # Terminar proceso principal
                self.process.terminate()
                
                # Esperar a que termine o matarlo si tarda demasiado
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("⚠️ Terminación suave falló, matando proceso...")
                    parent.kill()
                    
            # Esperar un momento para liberar recursos
            time.sleep(1)
            
            # Iniciar un nuevo proceso
            self.process = subprocess.Popen(
                [sys.executable, str(APP_FILE)],
                cwd=str(ROOT_DIR)  # Asegurar que se ejecuta desde el directorio correcto
            )
            print(f"✅ Aplicación reiniciada (PID: {self.process.pid})")
            
        except Exception as e:
            print(f"❌ Error al reiniciar la aplicación: {e}")
        finally:
            self.restart_pending = False

    def on_modified(self, event):
        # Solo procesar archivos regulares (no directorios)
        if not os.path.isfile(event.src_path):
            return
            
        # Prevenir múltiples reinicios por un solo cambio (debounce)
        if time.time() - self.last_modified < 1:
            return
            
        # Ignorar archivos que no deberían causar reinicio
        if self.should_ignore(event.src_path):
            return
                
        # Solo reiniciar si cambia un archivo .py
        if event.src_path.endswith(".py"):
            self.last_modified = time.time()
            print(f"🔄 {event.src_path} modificado.")
            self.restart_app()
            
    def on_created(self, event):
        # Manejar creación de nuevos archivos .py
        if event.src_path.endswith(".py") and not self.should_ignore(event.src_path):
            self.last_modified = time.time()
            print(f"🆕 {event.src_path} creado.")
            self.restart_app()


def signal_handler(sig, frame):
    """Maneja la señal de interrupción (Ctrl+C)"""
    print("\n🛑 Deteniendo monitoreo...")
    observer.stop()
    # Esperar a que el observador termine
    observer.join()
    # Terminar la aplicación
    if process.poll() is None:
        try:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                try:
                    child.terminate()
                except:
                    pass
            process.terminate()
        except:
            pass
    print("⏹️ Aplicación terminada")
    sys.exit(0)


if __name__ == "__main__":
    # Registrar manejador de señales para terminar limpiamente
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"🚀 Iniciando {APP_FILE} con recarga automática...")
    
    # Inicia la app desde el directorio correcto
    process = subprocess.Popen(
        [sys.executable, str(APP_FILE)],
        cwd=str(ROOT_DIR)
    )
    print(f"✅ Aplicación iniciada (PID: {process.pid})")
    
    # Configura el monitor de archivos
    event_handler = ReloadHandler(process)
    observer = Observer()
    # Monitorear el directorio del proyecto recursivamente
    observer.schedule(event_handler, path=str(ROOT_DIR), recursive=True)
    observer.start()
    
    print(f"👀 Monitoreando cambios en archivos .py en {ROOT_DIR}...")
    
    # Mantener script corriendo
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        # Esto será manejado por el signal_handler
        pass