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
        # Ajusta este valor para mostrar más o menos filas según necesites
        self.partidas_table.setMinimumHeight(400)
        
        # Agregar la tabla al layout principal
        self.content_layout.addWidget(self.partidas_table)
        
        # NO agregamos el botón para ver todos los movimientos
        
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
         
         # Reconectar el botón para cargar todos
        


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
                f"{session.api_url}/partidas",  # Sin parámetro limit para cargar todas
                headers=headers
            )
            
            # Luego obtenemos las transacciones para tener los saldos
            transacciones_response = requests.get(
                f"{session.api_url}/transacciones",  # Sin parámetro limit
                headers=headers
            )
            
            # Crear un diccionario de fechas y saldos de transacciones
            saldos_por_fecha = {}
            if transacciones_response.status_code == 200:
                transacciones_data = transacciones_response.json()
                # Ordenar transacciones por fecha y por ID
                transacciones_data.sort(key=lambda x: (x.get('fecha', ''), x.get('id', 0)))
                
                for transaccion in transacciones_data:
                    fecha = transaccion.get('fecha', '')
                    saldo = transaccion.get('saldo', 0)
                    # Guardamos el último saldo para cada fecha
                    saldos_por_fecha[fecha] = saldo
            
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
                    
                    # Obtener saldo actual del balance para usarlo como base
                    balance_actual = 0
                    try:
                        balance_response = requests.get(
                            f"{session.api_url}/reportes/balance",
                            headers=headers
                        )
                        if balance_response.status_code == 200:
                            balance_data = balance_response.json()
                            balance_actual = balance_data.get('saldo', 0)
                    except Exception as e:
                        print(f"Error al obtener balance: {str(e)}")
                    
                    # Contador para cuotas societarias
                    cuota_counter = 0
                    
                    # Identificar todas las partidas que son cuotas societarias
                    cuotas_societarias = []
                    for item in partidas_data:
                        detalle = item.get('detalle', '').lower()
                        ingreso = item.get('ingreso', 0)
                        if 'cuota' in detalle and ingreso > 0:
                            cuotas_societarias.append(item.get('id'))
                    
                    # Llenar tabla con datos
                    for row, partida_item in enumerate(partidas_data):
                        self.partidas_table.insertRow(row)
                        
                        # Fecha
                        fecha_str = partida_item.get('fecha', '')
                        fecha_display = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha_str else ''
                        self.partidas_table.setItem(row, 0, QTableWidgetItem(fecha_display))
                        
                        # Determinar tipo de movimiento (Ingreso, Egreso, Anulación o Ajuste)
                        ingreso = partida_item.get('ingreso', 0)
                        egreso = partida_item.get('egreso', 0)
                        
                        # CAMBIO AQUÍ: Verificar primero si es anulación
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
                        
                        # Número de comprobante - CÓDIGO MODIFICADO
                        num_comprobante = ""
                        
                        # Verificar si es un pago de cuota societaria basándose en el detalle
                        detalle = partida_item.get('detalle', '').lower()
                        if tipo_movimiento == "INGRESO" and ('cuota' in detalle):
                            # Contador para cuotas societarias
                            # Obtener la posición de esta cuota en la lista de cuotas encontradas
                            if partida_item.get('id') in cuotas_societarias:
                                # Encontrar la posición de este ID en la lista ordenada de cuotas
                                posicion = cuotas_societarias.index(partida_item.get('id')) + 1
                                # Usar el contador como número (comenzando desde el final para que sea 1, 2, 3...)
                                num_recibo = str(len(cuotas_societarias) - posicion + 1)
                                num_comprobante = f"C.S.-{num_recibo}"
                            else:
                                # Si por alguna razón no está en la lista, usar una numeración genérica
                                num_comprobante = f"C.S.-{partida_item.get('id')}"
                        elif partida_item.get('cobranza_id'):
                            # Otros ingresos asociados a cobranzas
                            num_comprobante = f"REC-{partida_item.get('cobranza_id')}"
                        elif partida_item.get('pago_id'):
                            # Pagos
                            num_comprobante = f"O.P-{partida_item.get('pago_id')}"
                        elif tipo_movimiento == "INGRESO":
                            # Otros ingresos sin ID de cobranza
                            num_comprobante = f"REC-{partida_item.get('id', '')}"
                        elif tipo_movimiento == "EGRESO":
                            # Egresos sin ID de pago
                            num_comprobante = f"O.P-{partida_item.get('id', '')}"
                        elif tipo_movimiento == "ANULACIÓN":
                            # Anulaciones
                            num_comprobante = f"ANUL-{partida_item.get('id', '')}"
                        else:
                            # Valor por defecto
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
                        
                        # Saldo - CÓDIGO CORREGIDO
                        saldo = 0
                        
                        if row == 0:
                            
                            saldo = balance_actual 
                            
                            # Actualizar este saldo en la base de datos para la partida más reciente
                            try:
                                if partida_item.get('id'):
                                    update_url = f"{session.api_url}/partidas/{partida_item.get('id')}"
                                    headers_update = session.get_headers()
                                    headers_update["Content-Type"] = "application/json"
                                    update_data = {"saldo": saldo}
                                    
                                    requests.put(update_url, headers=headers_update, json=update_data)
                                    print(f"Saldo actualizado para partida {partida_item.get('id')}: {saldo}")
                            except Exception as e:
                                print(f"Error al actualizar saldo: {str(e)}")
                        else:
                            try:
                                # Obtener saldo de la fila anterior
                                anterior_saldo_text = self.partidas_table.item(row-1, 7).text()
                                # Corregir el problema de reemplazo en el cálculo del saldo
                                anterior_saldo = float(anterior_saldo_text.replace('$', '').replace(',', ''))
                                
                                # El saldo de esta fila depende de si es un ingreso o egreso
                                if tipo_movimiento == "INGRESO":
                                    # Para filas anteriores a la primera, restar el ingreso
                                    # (ya que estamos retrocediendo en el tiempo)
                                    saldo = anterior_saldo + ingreso
                                elif tipo_movimiento == "EGRESO":
                                    # Para egresos, sumar el egreso (restamos en sentido inverso)
                                    saldo = anterior_saldo - egreso
                                else:
                                    # Para ajustes y anulaciones, no modificar el saldo
                                    saldo = anterior_saldo
                                    
                                # Si hay discrepancia con el saldo almacenado, actualizar BD
                                saldo_bd = partida_item.get('saldo', 0)
                                if abs(saldo - saldo_bd) > 0.01 and partida_item.get('id'):
                                    try:
                                        update_url = f"{session.api_url}/partidas/{partida_item.get('id')}"
                                        headers_update = session.get_headers()
                                        headers_update["Content-Type"] = "application/json"
                                        update_data = {"saldo": saldo}
                                        
                                        requests.put(update_url, headers=headers_update, json=update_data)
                                        print(f"Saldo corregido para partida {partida_item.get('id')}: {saldo}")
                                    except Exception as e:
                                        print(f"Error al actualizar saldo: {str(e)}")
                            except Exception as e:
                                # Si hay error al calcular, intentar usar saldo de BD
                                saldo = partida_item.get('saldo', 0)
                                print(f"Error al calcular saldo para fila {row}: {str(e)}")
                        
                        saldo_item = QTableWidgetItem(f"${saldo:,.2f}")
                        saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        # Agregar un color distintivo al saldo
                        saldo_item.setForeground(QBrush(QColor("#1565C0")))  # Azul oscuro
                        saldo_item.setFont(QFont("Arial", 9, QFont.Bold))
                        self.partidas_table.setItem(row, 7, saldo_item)
                    
                    # Ajustar columnas
                    self.partidas_table.resizeColumnsToContents()
                    
        except Exception as e:
            self.partidas_label.setText("Movimientos")
            print(f"Error al cargar partidas: {str(e)}")
# Método para ser llamado cuando se vuelve al dashboard
def on_show(self):
    """Método que se llama cuando el dashboard se muestra después de navegar"""
    self.refresh_data()