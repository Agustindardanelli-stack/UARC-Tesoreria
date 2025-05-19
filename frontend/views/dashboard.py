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
# Asegúrate de tener esta importación al inicio del archivo
from PySide6.QtGui import QPixmap, QFont, QIcon, QColor, QBrush 
from PySide6.QtCore import Qt, Signal, QDateTime, QTimer , QEvent
from concurrent.futures import ThreadPoolExecutor


from .logo_loader import load_logo
from sesion import session

class SidebarWidget(QWidget):
    """Widget para la barra lateral con menú de navegación"""
    navigation_requested = Signal(str)  # Señal para solicitar navegación

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

        self.executor = ThreadPoolExecutor(max_workers=1)


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
            {"text": "Inicio", "value": "dashboard"},
            {"text": "Pagos", "value": "pagos"},
            {"text": "Cobranzas", "value": "cobranzas"},
            {"text": "Cuotas Societarias", "value": "socio_cuota"},
            {"text": "Importes", "value": "importes"},
            {"text": "Reportes", "value": "reportes"},
            {"text": "Config. Email", "value": "email_config"} ,
            {"text": "Agregar Socio","value": "add_user"}
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
        
        # Temporizador para la hora (cada 5 segundos es suficiente)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(5000)  # Actualizar cada 5 segundos
    
    # Eliminar la actualización automática de datos
    # self.data_timer = QTimer(self)
    # self.data_timer.timeout.connect(self.refresh_data)
    # self.data_timer.start(30000)
    
    # Cargar datos iniciales una sola vez
        self.refresh_data()
    def event(self, event):
        """Maneja eventos personalizados para actualizar datos"""
        if event.type() == QEvent.User + 1:  # Evento personalizado para actualización
            # Actualizar solo los datos relevantes sin recargar todo
            self.refresh_data()
            return True
        return super().event(event)
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
        title_label = QLabel("Inicio")
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
        
        # Botón de actualización manual
        refresh_btn = QPushButton("Actualizar datos")
        refresh_btn.clicked.connect(self.refresh_data)
        datetime_layout.addWidget(refresh_btn)
        
        # Botón de recalcular saldos
        recalcular_saldos_btn = QPushButton("Recalcular todos los saldos")
        recalcular_saldos_btn.clicked.connect(self.recalcular_todos_saldos)
        recalcular_saldos_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        datetime_layout.addWidget(recalcular_saldos_btn)
        
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
        self.partidas_label = QLabel("Todos los movimientos")
        partidas_font = QFont()
        partidas_font.setPointSize(16)
        self.partidas_label.setFont(partidas_font)
        self.content_layout.addWidget(self.partidas_label)
        
        # Crear la tabla con configuración para scroll
        self.partidas_table = QTableWidget()
        self.partidas_table.setColumnCount(8)
        self.partidas_table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Detalle", "Usuario que realizó", "Nº Comprobante", "Ingreso", "Egreso", "Saldo"
        ])
        self.partidas_table.horizontalHeader().setStretchLastSection(True)
        self.partidas_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.partidas_table.setAlternatingRowColors(True)
        
        # Configurar el scroll
        self.partidas_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.partidas_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Establecer una altura fija para mostrar un número limitado de filas
        self.partidas_table.setMinimumHeight(400)
        
        # Agregar la tabla al layout principal
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
         if not session.token:
              print("Sesión no iniciada. No se cargarán los datos del dashboard.")
              return
         self.load_balance_data()
         self.load_partidas_data()
         
         # Restaurar el estado del botón "Ver todos los movimientos"
         self.partidas_label.setText("Últimos movimientos")
    
    def on_show(self):
        """Se llama cuando el dashboard se muestra después del login"""
        self.update_time()

        # Mostrar valores temporales
        self.balance_indicator.findChildren(QLabel)[1].setText("Cargando...")
        self.ingresos_indicator.findChildren(QLabel)[1].setText("...")
        self.egresos_indicator.findChildren(QLabel)[1].setText("...")
        self.cuotas_indicator.findChildren(QLabel)[1].setText("...")

        # Ejecutar en segundo plano
        self.executor.submit(self.refresh_data)
        
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
                except Exception as e:
                    balance_actual = 0
                    ingresos_mes = 0
                    egresos_mes = 0
                 
                try:
                    ingresos_egresos_data = ingresos_egresos_response.json()
                except Exception as e:
                    ingresos_egresos_data = {"datos": []}
                
                try:
                    cuotas_pendientes_data = cuotas_pendientes_response.json()
                    # Comprobar si cuotas_pendientes_data es un diccionario
                    if isinstance(cuotas_pendientes_data, dict):
                        cuotas_pendientes = cuotas_pendientes_data.get('cantidad_pendientes', 0)
                    elif isinstance(cuotas_pendientes_data, list):
                        # Si es una lista, usar la longitud como cantidad de cuotas pendientes
                        cuotas_pendientes = len(cuotas_pendientes_data)
                    else:
                        cuotas_pendientes = 0
                except Exception as e:
                    cuotas_pendientes = 0
                
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
                
        except Exception as e:
            pass
    
    def load_partidas_data(self):
        """Carga todas las partidas disponibles con scroll automático"""
        try:
            headers = session.get_headers()
            
            # Cargar todas las partidas sin límite
            partidas_response = requests.get(
                f"{session.api_url}/partidas",
                headers=headers
            )
            
            # Procesar las partidas
            if partidas_response.status_code == 200:
                partidas_data = partidas_response.json()
                
                # Actualizar título con la cantidad de registros
                self.partidas_label.setText(f"Todos los movimientos ({len(partidas_data)} registros)")
                
                # Limpiar tabla
                self.partidas_table.setColumnCount(8)
                self.partidas_table.setHorizontalHeaderLabels([
                    "Fecha", "Tipo", "Detalle", "Usuario que realizó", "Nº Comprobante", "Ingreso", "Egreso", "Saldo"
                ])
                self.partidas_table.setRowCount(0)
                
                if partidas_data:
                    # Ordenar partidas por fecha (descendente) y luego por ID (descendente)
                    partidas_data.sort(key=lambda x: (x.get('fecha', ''), x.get('id', 0)), reverse=True)
                    
                    # Identificar todas las partidas que son cuotas societarias
                    cuotas_societarias = []
                    for item in partidas_data:
                        detalle = item.get('detalle', '').lower()
                        ingreso = item.get('ingreso', 0)
                        if 'cuota' in detalle and ingreso > 0:
                            cuotas_societarias.append(item.get('id'))
                    
                    # No calculamos los saldos manualmente, usamos los saldos del servidor
                    # que han sido calculados correctamente cuando se hizo el recálculo
                    
                    # Llenar la tabla con los datos
                    for row, partida_item in enumerate(partidas_data):
                        self.partidas_table.insertRow(row)
                        
                        # Fecha
                        fecha_str = partida_item.get('fecha', '')
                        fecha_display = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha_str else ''
                        self.partidas_table.setItem(row, 0, QTableWidgetItem(fecha_display))
                        
                        # Determinar tipo de movimiento (Ingreso, Egreso, Anulación o Ajuste)
                        ingreso = partida_item.get('ingreso', 0)
                        egreso = partida_item.get('egreso', 0)
                        
                        # Verificar primero si es anulación
                        if partida_item.get('tipo', '') == "anulacion":
                            tipo_movimiento = "ANULACIÓN"
                            color_fondo = QColor(255, 240, 230)  # Naranja claro para anulaciones
                        elif ingreso > 0 and egreso == 0:
                            tipo_movimiento = "INGRESO"
                            color_fondo = QColor(232, 245, 233)  # Verde claro para ingresos
                        elif egreso > 0 and ingreso == 0:
                            tipo_movimiento = "EGRESO"
                            color_fondo = QColor(255, 235, 238)  # Rojo claro para egresos
                        else:
                            tipo_movimiento = "AJUSTE"
                            color_fondo = QColor(255, 253, 231)  # Amarillo claro para ajustes
                        
                        # Aplicar color de fondo a todos los elementos de la fila
                        for col in range(8):
                            if not self.partidas_table.item(row, col):
                                self.partidas_table.setItem(row, col, QTableWidgetItem(""))
                            self.partidas_table.item(row, col).setBackground(QBrush(color_fondo))
                        
                        # Tipo de movimiento con formato especial
                        tipo_item = QTableWidgetItem(tipo_movimiento)
                        tipo_item.setTextAlignment(Qt.AlignCenter)
                        
                        # Establecer color del texto según el tipo de movimiento
                        if tipo_movimiento == "INGRESO":
                            tipo_item.setForeground(QBrush(QColor("#4CAF50")))  # Verde para ingresos
                        elif tipo_movimiento == "EGRESO":
                            tipo_item.setForeground(QBrush(QColor("#F44336")))  # Rojo para egresos
                        elif tipo_movimiento == "ANULACIÓN":
                            tipo_item.setForeground(QBrush(QColor("#FF9800")))  # Naranja para anulaciones
                        
                        tipo_item.setFont(QFont("Arial", 9, QFont.Bold))
                        self.partidas_table.setItem(row, 1, tipo_item)
                        
                        # Detalle
                        self.partidas_table.setItem(row, 2, QTableWidgetItem(partida_item.get('detalle', '')))
                        
                        # Usuario que realizó
                        usuario_obj = partida_item.get('usuario', {})
                        usuario_accion = usuario_obj.get('nombre', 'Sin registro') if usuario_obj else 'Sin registro'
                        self.partidas_table.setItem(row, 3, QTableWidgetItem(usuario_accion))
                        
                        # MODIFICADO: Usar recibo_factura si está disponible
                        # Número de comprobante
                        if partida_item.get('recibo_factura'):
                            # Si hay un número de comprobante ya asignado, usarlo
                            num_comprobante = partida_item.get('recibo_factura')
                        else:
                            # Si no hay, usar la lógica anterior como respaldo
                            if tipo_movimiento == "INGRESO" and ('cuota' in partida_item.get('detalle', '').lower()):
                                # Contador para cuotas societarias
                                if partida_item.get('id') in cuotas_societarias:
                                    posicion = cuotas_societarias.index(partida_item.get('id')) + 1
                                    num_recibo = str(len(cuotas_societarias) - posicion + 1)
                                    num_comprobante = f"C.S.-{num_recibo}"
                                else:
                                    num_comprobante = f"C.S.-{partida_item.get('id')}"
                            elif partida_item.get('cobranza_id'):
                                # Verificar si la cobranza está relacionada con una factura
                                cobranza_id = partida_item.get('cobranza_id')
                                # Intentar determinar si es una factura basándose en el detalle
                                detalle = partida_item.get('detalle', '').lower()
                                if 'factura' in detalle:
                                    num_comprobante = f"FAC/REC.A -{cobranza_id}"
                                else:
                                    num_comprobante = f"REC-{cobranza_id}"
                            elif partida_item.get('pago_id'):
                                # Verificar si el pago está relacionado con una factura
                                pago_id = partida_item.get('pago_id')
                                if pago_id:
                                    # Intentar determinar si es una factura basándose en el detalle
                                    detalle = partida_item.get('detalle', '').lower()
                                    if 'factura' in detalle:
                                        num_comprobante = f"FAC/REC.A - {pago_id}"
                                    else:
                                        num_comprobante = f"O.P-{pago_id}"
                                else:
                                    num_comprobante = f"O.P-{partida_item.get('id')}"
                            elif tipo_movimiento == "INGRESO":
                                num_comprobante = f"REC-{partida_item.get('id', '')}"
                            elif tipo_movimiento == "EGRESO":
                                num_comprobante = f"O.P-{partida_item.get('id', '')}"
                            elif tipo_movimiento == "ANULACIÓN":
                                num_comprobante = f"ANUL-{partida_item.get('id', '')}"
                            else:
                                num_comprobante = f"O.P-{partida_item.get('id', '')}"
                        
                        comprobante_item = QTableWidgetItem(num_comprobante)
                        comprobante_item.setTextAlignment(Qt.AlignCenter)
                        self.partidas_table.setItem(row, 4, comprobante_item)
                        
                        # Ingreso
                        ingreso_item = QTableWidgetItem(f"${ingreso:,.2f}")
                        ingreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        if ingreso > 0:
                            ingreso_item.setForeground(QBrush(QColor("#4CAF50")))  # Verde para ingresos
                            ingreso_item.setFont(QFont("Arial", 9, QFont.Bold))
                        self.partidas_table.setItem(row, 5, ingreso_item)
                        
                        # Egreso
                        egreso_item = QTableWidgetItem(f"${egreso:,.2f}")
                        egreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        if egreso > 0:
                            egreso_item.setForeground(QBrush(QColor("#F44336")))  # Rojo para egresos
                            egreso_item.setFont(QFont("Arial", 9, QFont.Bold))
                        self.partidas_table.setItem(row, 6, egreso_item)
                        
                        # Saldo - Usamos el saldo precalculado del servidor
                        saldo = partida_item.get('saldo', 0)
                        saldo_item = QTableWidgetItem(f"${saldo:,.2f}")
                        saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        saldo_item.setForeground(QBrush(QColor("#1565C0")))  # Azul oscuro
                        saldo_item.setFont(QFont("Arial", 9, QFont.Bold))
                        self.partidas_table.setItem(row, 7, saldo_item)
                    
                    # Ajustar columnas
                    self.partidas_table.resizeColumnsToContents()
                    
                    # Asegurarse de que la columna de saldo tenga un ancho mínimo
                    min_width = 150
                    if self.partidas_table.columnWidth(7) < min_width:
                        self.partidas_table.setColumnWidth(7, min_width)
                    
        except Exception as e:
            self.partidas_label.setText("Error en movimientos")
            print(f"Error al cargar partidas: {str(e)}")
            import traceback
            traceback.print_exc()

    def recalcular_todos_saldos(self):
        """Llama al endpoint de recálculo de saldos y recarga los datos"""
        try:
            from PySide6.QtWidgets import QMessageBox
            
            # Mensaje de confirmación
            respuesta = QMessageBox.question(
                self,
                "Confirmar recálculo",
                "¿Está seguro que desea recalcular todos los saldos? Este proceso puede tardar unos segundos.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                # Mostrar cursor de espera
                from PySide6.QtCore import Qt
                from PySide6.QtGui import QCursor
                self.setCursor(QCursor(Qt.WaitCursor))
                
                # Realizar la llamada a la API
                headers = session.get_headers()
                url = f"{session.api_url}/transacciones/recalcular-saldos"
                
                response = requests.post(url, headers=headers)
                
                # Restaurar cursor normal
                self.setCursor(QCursor(Qt.ArrowCursor))
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Mostrar mensaje de éxito
                    QMessageBox.information(
                        self,
                        "Saldos recalculados",
                        f"Se han recalculado correctamente {result.get('transacciones_actualizadas', 0)} saldos.",
                        QMessageBox.Ok
                    )
                    
                    # Actualizar datos
                    self.refresh_data()
                else:
                    # Mostrar mensaje de error
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"No se pudieron recalcular los saldos. Código: {response.status_code}",
                        QMessageBox.Ok
                    )
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Error al recalcular saldos: {str(e)}",
                QMessageBox.Ok
            )
            
            # Restaurar cursor normal en caso de error
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QCursor
            self.setCursor(QCursor(Qt.ArrowCursor))        

# Método para ser llamado cuando se vuelve al dashboard
def on_show(self):
    """Método que se llama cuando el dashboard se muestra después de navegar"""
    self.refresh_data()