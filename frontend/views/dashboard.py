import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QSplitter, QFrame, QTabWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QPixmap, QFont, QIcon
from PySide6.QtCore import Qt, Signal, QDateTime, QTimer
from .logo_loader import load_logo
from sesion import session

class SidebarWidget(QWidget):
    """Widget para la barra lateral con menú de navegación"""
    navigation_requested = Signal(str)  # Señal para solicitar navegación

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)

        # Logo
        self.logo_label = QLabel()
        load_logo(self.logo_label, "UarcLogo.png", 200, 200)
        layout.addWidget(self.logo_label)

        # Título
        title_label = QLabel("Tesorería UARC")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Información del usuario
        # ...
        if session.user_info:
            user_label = QLabel(f"<b>Usuario:</b> {session.user_info['nombre']}")
            user_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(user_label)
            
            rol_label = QLabel(f"<b>Rol:</b> {session.user_info.get('rol', 'No especificado')}")
            rol_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(rol_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Título de navegación
        nav_label = QLabel("Navegación")
        nav_font = QFont()
        nav_font.setPointSize(14)
        nav_label.setFont(nav_font)
        layout.addWidget(nav_label)
        
        # Botones de navegación
        buttons_data = [
            {"text": "Dashboard", "value": "dashboard"},
            {"text": "Pagos", "value": "pagos"},
            {"text": "Cobranzas", "value": "cobranzas"},
            {"text": "Cuotas Societarias", "value": "socio_cuota"},
            {"text": "Importes", "value": "importes"},
            {"text": "Reportes", "value": "reportes"},
            {"text": "Config. Email", "value": "email_config"} ,
            {"text": "Agregar Usuario","value": "add_user"}
        ]
        
        for btn_data in buttons_data:
                btn = QPushButton(btn_data["text"])
                btn.clicked.connect(lambda checked=False, v=btn_data["value"]: self.navigation_requested.emit(v))
                layout.addWidget(btn)
        # Espaciador
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        
        # Botón de cierre de sesión
        logout_btn = QPushButton("Cerrar Sesión")
        logout_btn.clicked.connect(lambda: self.navigation_requested.emit("logout"))
        layout.addWidget(logout_btn)


class IndicatorWidget(QWidget):
    """Widget para mostrar indicadores numéricos"""
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setup_ui(title, value)
    
    def setup_ui(self, title, value):
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # Estilo
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QLabel {
                padding: 5px;
            }
        """)


class MatplotlibCanvas(FigureCanvas):
    """Clase para mostrar gráficos de matplotlib en Qt"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.tight_layout()


class DashboardView(QWidget):
    navigation_requested = Signal(str)  # Señal para solicitar navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
        
        # Temporizador para la hora
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Actualizar cada segundo
        
        # NUEVO: Temporizador para actualizar datos cada 30 segundos
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.refresh_data)
        self.data_timer.start(30000)  # Actualizar cada 30 segundos
        
        # Cargar datos iniciales
        self.refresh_data()
    
    def setup_ui(self):
        # Layout principal
        self.main_layout = QHBoxLayout(self)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.setFixedWidth(200)
        
        # Widget de contenido
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # Título
        title_label = QLabel("Dashboard de Tesorería")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.content_layout.addWidget(title_label)
        
        # Hora y fecha
        datetime_layout = QHBoxLayout()
        self.date_label = QLabel(f"<b>Fecha actual:</b> {datetime.now().strftime('%d/%m/%Y')}")
        self.time_label = QLabel(f"<b>Hora actual:</b> {datetime.now().strftime('%H:%M:%S')}")
        datetime_layout.addWidget(self.date_label)
        datetime_layout.addWidget(self.time_label)
        self.content_layout.addLayout(datetime_layout)
        
        # NUEVO: Botón de actualización manual
        refresh_btn = QPushButton("Actualizar datos")
        refresh_btn.clicked.connect(self.refresh_data)
        datetime_layout.addWidget(refresh_btn)
        
        # Indicadores
        indicators_layout = QHBoxLayout()
        self.balance_indicator = IndicatorWidget("Balance Actual", "$0.00")
        self.ingresos_indicator = IndicatorWidget("Ingresos del Mes", "$0.00")
        self.egresos_indicator = IndicatorWidget("Egresos del Mes", "$0.00")
        self.cuotas_indicator = IndicatorWidget("Cuotas Pendientes", "0")
        
        indicators_layout.addWidget(self.balance_indicator)
        indicators_layout.addWidget(self.ingresos_indicator)
        indicators_layout.addWidget(self.egresos_indicator)
        indicators_layout.addWidget(self.cuotas_indicator)
        self.content_layout.addLayout(indicators_layout)
        
        # Tabla de partidas recientes
        self.partidas_label = QLabel("Últimos movimientos")
        partidas_font = QFont()
        partidas_font.setPointSize(16)
        self.partidas_label.setFont(partidas_font)
        self.content_layout.addWidget(self.partidas_label)
        
        self.partidas_table = QTableWidget()
        self.partidas_table.setColumnCount(6)
        self.partidas_table.setHorizontalHeaderLabels(["Fecha", "Cuenta", "Detalle", "Ingreso", "Egreso", "Saldo"])
        self.partidas_table.horizontalHeader().setStretchLastSection(True)
        self.partidas_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.partidas_table.setAlternatingRowColors(True)
        self.content_layout.addWidget(self.partidas_table)
        
        # Agregar al layout principal
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_widget)
    
    def connect_signals(self):
        self.sidebar.navigation_requested.connect(self.navigation_requested)
    
    def update_time(self):
        """Actualiza la hora mostrada"""
        self.time_label.setText(f"<b>Hora actual:</b> {datetime.now().strftime('%H:%M:%S')}")
    
    def refresh_data(self):
        """Actualiza los datos del dashboard"""
        print("Actualizando datos del dashboard...")  # NUEVO: Mensaje de depuración
        self.load_balance_data()
        self.load_partidas_data()
    
    def load_balance_data(self):
        """Carga los datos del balance"""
        try:
            # Obtener balance
            headers = session.get_headers()
            balance_response = requests.get(
                f"{session.api_url}/reportes/balance",
                headers=headers
            )
            
            # Obtener ingresos/egresos mensuales
            ingresos_egresos_response = requests.get(
                f"{session.api_url}/reportes/ingresos_egresos_mensuales", 
                headers=headers
            )
            
            # Obtener cuotas pendientes
            cuotas_pendientes_response = requests.get(
                f"{session.api_url}/reportes/cuotas_pendientes",
                headers=headers
            )
            
            if (balance_response.status_code == 200 and 
                ingresos_egresos_response.status_code == 200 and 
                cuotas_pendientes_response.status_code == 200):
                
                # Procesar respuestas con manejo de diferentes formatos
                try:
                    balance_data = balance_response.json()
                    # Adaptación a la estructura de la respuesta real
                    if isinstance(balance_data, dict):
                        balance_actual = balance_data.get('saldo', 0)
                        ingresos_mes = balance_data.get('ingresos', 0)
                        egresos_mes = balance_data.get('egresos', 0)
                    else:
                        balance_actual = 0
                        ingresos_mes = 0
                        egresos_mes = 0
                        print("WARNING: balance_data no es un diccionario, es:", type(balance_data))
                except Exception as e:
                    balance_actual = 0
                    ingresos_mes = 0
                    egresos_mes = 0
                    print(f"Error al procesar balance_data: {e}")  
                 
                try:
                    ingresos_egresos_data = ingresos_egresos_response.json()
                except Exception as e:
                    ingresos_egresos_data = {"datos": []}
                    print(f"Error al procesar ingresos_egresos_data: {e}")
                
                try:
                    cuotas_pendientes_data = cuotas_pendientes_response.json()
                    # Comprobar si cuotas_pendientes_data es un diccionario
                    if isinstance(cuotas_pendientes_data, dict):
                        cuotas_pendientes = cuotas_pendientes_data.get('cantidad_pendientes', 0)
                    elif isinstance(cuotas_pendientes_data, list):
                        # Si es una lista, usar la longitud como cantidad de cuotas pendientes
                        cuotas_pendientes = len(cuotas_pendientes_data)
                        print("Cuotas pendientes es una lista, usando su longitud como cantidad.")
                    else:
                        cuotas_pendientes = 0
                        print("WARNING: cuotas_pendientes_data no es un diccionario ni una lista, es:", type(cuotas_pendientes_data))
                except Exception as e:
                    cuotas_pendientes = 0
                    print(f"Error al procesar cuotas_pendientes_data: {e}")
                
                # Actualizar indicadores - Encontrar todos los QLabel hijos de cada indicador
                balance_labels = self.balance_indicator.findChildren(QLabel)
                ingresos_labels = self.ingresos_indicator.findChildren(QLabel)
                egresos_labels = self.egresos_indicator.findChildren(QLabel)
                cuotas_labels = self.cuotas_indicator.findChildren(QLabel)
                
                # El segundo label (índice 1) es el que muestra el valor
                if len(balance_labels) > 1:
                    balance_labels[1].setText(f"${balance_actual:,.2f}")
                if len(ingresos_labels) > 1:
                    ingresos_labels[1].setText(f"${ingresos_mes:,.2f}")
                if len(egresos_labels) > 1:
                    egresos_labels[1].setText(f"${egresos_mes:,.2f}")
                if len(cuotas_labels) > 1:
                    cuotas_labels[1].setText(f"{cuotas_pendientes}")
                
                # NUEVO: Mensaje de éxito
                print("Datos de balance actualizados correctamente")
                
        except Exception as e:
            print(f"Error al cargar datos del balance: {e}")
    
    def load_partidas_data(self):
        """Carga las últimas partidas"""
        try:
            headers = session.get_headers()
            partidas_response = requests.get(
                f"{session.api_url}/partidas?limit=10",
                headers=headers
            )
            
            if partidas_response.status_code == 200:
                partidas_data = partidas_response.json()
                
                # Limpiar tabla
                self.partidas_table.setRowCount(0)
                
                if partidas_data:
                    # Llenar tabla con datos
                    for row, partida in enumerate(partidas_data):
                        self.partidas_table.insertRow(row)
                        
                        # Fecha
                        fecha = datetime.strptime(partida.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if partida.get('fecha') else ''
                        self.partidas_table.setItem(row, 0, QTableWidgetItem(fecha))
                        
                        # Cuenta
                        self.partidas_table.setItem(row, 1, QTableWidgetItem(partida.get('cuenta', '')))
                        
                        # Detalle
                        self.partidas_table.setItem(row, 2, QTableWidgetItem(partida.get('detalle', '')))
                        
                        # Ingreso
                        ingreso_item = QTableWidgetItem(f"${partida.get('ingreso', 0):,.2f}")
                        ingreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.partidas_table.setItem(row, 3, ingreso_item)
                        
                        # Egreso
                        egreso_item = QTableWidgetItem(f"${partida.get('egreso', 0):,.2f}")
                        egreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.partidas_table.setItem(row, 4, egreso_item)
                        
                        # Saldo
                        saldo_item = QTableWidgetItem(f"${partida.get('saldo', 0):,.2f}")
                        saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.partidas_table.setItem(row, 5, saldo_item)
                    
                    # Ajustar columnas
                    self.partidas_table.resizeColumnsToContents()
                    
                    # NUEVO: Mensaje de éxito
                    print("Partidas actualizadas correctamente")
                else:
                    print("No se encontraron partidas para mostrar")
            else:
                print(f"Error al obtener partidas: {partidas_response.status_code}")
                
        except Exception as e:
            print(f"Error al cargar partidas: {e}")
    
    # NUEVO: Método para ser llamado cuando se vuelve al dashboard
    def on_show(self):
        """Método que se llama cuando el dashboard se muestra después de navegar"""
        self.refresh_data()