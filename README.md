# 🧾 UARC - Tesorería

Sistema de gestión contable y administrativa para una agrupación de árbitros, desarrollado en Python. Permite registrar ingresos, egresos, pagos de retenciones, y generar reportes, simulando el funcionamiento de un libro diario.

## 📌 Características Principales

- Gestión de ingresos y egresos.
- Registro de pagos y cobranzas por usuario.
- Categorización de movimientos (retenciones, campeonatos, seguros, etc.).
- Dashboard con resumen financiero.
- Filtros por fecha y usuario.
- Control de acceso para diferentes perfiles (Tesorero, Presidente).
- Backup y restauración de base de datos.

## 🛠️ Tecnologías Utilizadas

- **Python 3**
- **SQLite** como base de datos
- **PyQt5** para la interfaz gráfica de usuario
- **FastAPI / Flask** (si hay backend web, aclarar aquí)
- **Render.com** para despliegue (si aplica)

## 📂 Estructura del Proyecto

UARC-Tesoreria/
├── backend/ # Lógica del servidor (si aplica)
├── frontend/ # Interfaz gráfica con PyQt5
├── bd_backup.sql # Respaldo de base de datos
├── render.yaml # Configuración para despliegue (Render)
└── README.md

bash
Copiar
Editar

## 🚀 Instalación y Ejecución

1. Clona el repositorio:

```bash
git clone https://github.com/Agustindardanelli-stack/UARC-Tesoreria.git
cd UARC-Tesoreria
Crea y activa un entorno virtual (opcional pero recomendado):

bash
Copiar
Editar
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
Instala las dependencias:

bash
Copiar
Editar
pip install -r requirements.txt
Ejecuta la app:

bash
Copiar
Editar
python frontend/main.py
🔐 Roles y Accesos
Presidente / Tesorero: Acceso total al sistema.

Árbitros: Solo pueden consultar sus movimientos o realizar pagos.

Usuarios sin acceso: Registrados para el libro diario, pero sin uso interactivo.

📊 Funcionalidades del Libro Diario
Visualización automática de ingresos y egresos.

Registro de todos los movimientos.

Cálculo automático de saldos.

Exportación de reportes.

📌 Estado del Proyecto
✅ En desarrollo activo
📅 Última actualización: junio 2025

🤝 Contribuciones
¿Querés colaborar? ¡Bienvenido! Abrí un issue o hacé un pull request.

🧑 Autor
Agustín Dardanelli
🔗 GitHub

nginx
Copiar
Editar

Si necesitás que te ayude con más archivos o detalles, avisame.