import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import io

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QFrame, QTabWidget, QSpacerItem, QSizePolicy,
    QFormLayout, QDateEdit, QComboBox, QMessageBox, QFileDialog
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QDate

from views.dashboard import SidebarWidget, MatplotlibCanvas
from sesion import session

class ReportesView(QWidget):
    navigation_requested = Signal(str)  # Señal para solicitar navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
    
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
        title_label = QLabel("Reportes")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.content_layout.addWidget(title_label)
        
        # Tabs para los diferentes reportes
        self.tabs = QTabWidget()
        
        # Tab 1: Balance General
        self.tab_balance = QWidget()
        self.setup_tab_balance()
        self.tabs.addTab(self.tab_balance, "Balance General")
        
        # Tab 2: Ingresos y Egresos
        self.tab_ingresos_egresos = QWidget()
        self.setup_tab_ingresos_egresos()
        self.tabs.addTab(self.tab_ingresos_egresos, "Ingresos y Egresos")
        
        # Tab 3: Cuotas Pendientes
        self.tab_cuotas = QWidget()
        self.setup_tab_cuotas()
        self.tabs.addTab(self.tab_cuotas, "Cuotas Pendientes")
        
        # Tab 4: Libro Diario
        self.tab_libro = QWidget()
        self.setup_tab_libro()
        self.tabs.addTab(self.tab_libro, "Libro Diario")
        
        self.content_layout.addWidget(self.tabs)
        
        # Agregar al layout principal
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_widget)
    
    def setup_tab_balance(self):
        layout = QVBoxLayout(self.tab_balance)
        
        # Filtros
        filtros_layout = QHBoxLayout()
        
        # Desde
        desde_label = QLabel("Desde:")
        self.balance_desde_date = QDateEdit()
        self.balance_desde_date.setDate(QDate.currentDate().addMonths(-6))  # Últimos 6 meses por defecto
        self.balance_desde_date.setCalendarPopup(True)
        
        # Hasta
        hasta_label = QLabel("Hasta:")
        self.balance_hasta_date = QDateEdit()
        self.balance_hasta_date.setDate(QDate.currentDate())
        self.balance_hasta_date.setCalendarPopup(True)
        
        # Botón de generar
        self.balance_generar_btn = QPushButton("Generar y Descargar")
        self.balance_generar_btn.clicked.connect(self.on_generar_balance)
        
        filtros_layout.addWidget(desde_label)
        filtros_layout.addWidget(self.balance_desde_date)
        filtros_layout.addWidget(hasta_label)
        filtros_layout.addWidget(self.balance_hasta_date)
        filtros_layout.addWidget(self.balance_generar_btn)
        
        layout.addLayout(filtros_layout)
        
        # Métricas principales
        metricas_layout = QHBoxLayout()
        
        self.ingresos_label = QLabel("Ingresos Totales: $0.00")
        self.ingresos_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        
        self.egresos_label = QLabel("Egresos Totales: $0.00")
        self.egresos_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F44336;")
        
        self.balance_neto_label = QLabel("Balance Neto: $0.00")
        self.balance_neto_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        metricas_layout.addWidget(self.ingresos_label)
        metricas_layout.addWidget(self.egresos_label)
        metricas_layout.addWidget(self.balance_neto_label)
        
        layout.addLayout(metricas_layout)
        
        # Gráfico
        self.balance_canvas = MatplotlibCanvas(self, width=8, height=4, dpi=100)
        layout.addWidget(self.balance_canvas)
        
        # Tabla de detalle
        detalle_label = QLabel("Detalle del Balance")
        detalle_font = QFont()
        detalle_font.setPointSize(14)
        detalle_label.setFont(detalle_font)
        layout.addWidget(detalle_label)
        
        self.balance_table = QTableWidget()
        self.balance_table.setColumnCount(5)
        self.balance_table.setHorizontalHeaderLabels(["Fecha", "Cuenta", "Ingreso", "Egreso", "Saldo"])
        self.balance_table.horizontalHeader().setStretchLastSection(True)
        self.balance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.balance_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.balance_table)
        
        # Botón de exportar
        self.balance_exportar_btn = QPushButton("Exportar a Excel")
        self.balance_exportar_btn.clicked.connect(self.on_exportar_balance)
        layout.addWidget(self.balance_exportar_btn)
    
    def setup_tab_ingresos_egresos(self):
        layout = QVBoxLayout(self.tab_ingresos_egresos)
        
        # Selector de año
        anio_layout = QHBoxLayout()
        
        anio_label = QLabel("Seleccionar Año:")
        self.anio_combo = QComboBox()
        
        # Llenar combo con los últimos 5 años
        current_year = datetime.now().year
        for year in range(current_year - 4, current_year + 1):
            self.anio_combo.addItem(str(year), year)
        
        # Seleccionar año actual
        self.anio_combo.setCurrentIndex(4)  # Último elemento (año actual)
        
        # Botón de generar
        self.ie_generar_btn = QPushButton("Generar y Descargar")
        self.ie_generar_btn.clicked.connect(self.on_generar_ingresos_egresos)
        
        anio_layout.addWidget(anio_label)
        anio_layout.addWidget(self.anio_combo)
        anio_layout.addWidget(self.ie_generar_btn)
        anio_layout.addStretch()
        
        layout.addLayout(anio_layout)
        
        # Gráficos
        self.ie_canvas = MatplotlibCanvas(self, width=8, height=4, dpi=100)
        layout.addWidget(self.ie_canvas)
        
        self.balance_ie_canvas = MatplotlibCanvas(self, width=8, height=4, dpi=100)
        layout.addWidget(self.balance_ie_canvas)
        
        # Tabla de datos
        datos_label = QLabel("Datos Mensuales")
        datos_font = QFont()
        datos_font.setPointSize(14)
        datos_label.setFont(datos_font)
        layout.addWidget(datos_label)
        
        self.ie_table = QTableWidget()
        self.ie_table.setColumnCount(4)
        self.ie_table.setHorizontalHeaderLabels(["Mes", "Ingresos", "Egresos", "Balance"])
        self.ie_table.horizontalHeader().setStretchLastSection(True)
        self.ie_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ie_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.ie_table)
        
        # Totales
        totales_layout = QHBoxLayout()
        
        self.ie_total_ingresos_label = QLabel("Total Ingresos: $0.00")
        self.ie_total_ingresos_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        
        self.ie_total_egresos_label = QLabel("Total Egresos: $0.00")
        self.ie_total_egresos_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F44336;")
        
        self.ie_balance_total_label = QLabel("Balance Total: $0.00")
        self.ie_balance_total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        totales_layout.addWidget(self.ie_total_ingresos_label)
        totales_layout.addWidget(self.ie_total_egresos_label)
        totales_layout.addWidget(self.ie_balance_total_label)
        
        layout.addLayout(totales_layout)
        
        # Botón de exportar
        self.ie_exportar_btn = QPushButton("Exportar a Excel")
        self.ie_exportar_btn.clicked.connect(self.on_exportar_ingresos_egresos)
        layout.addWidget(self.ie_exportar_btn)
    
    def setup_tab_cuotas(self):
        layout = QVBoxLayout(self.tab_cuotas)
        
        # Métricas
        metricas_layout = QHBoxLayout()
        
        self.cuotas_pendientes_label = QLabel("Cuotas Pendientes: 0")
        self.cuotas_pendientes_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.monto_pendiente_label = QLabel("Monto Pendiente: $0.00")
        self.monto_pendiente_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        metricas_layout.addWidget(self.cuotas_pendientes_label)
        metricas_layout.addWidget(self.monto_pendiente_label)
        
        layout.addLayout(metricas_layout)
        
        # Gráfico
        self.cuotas_canvas = MatplotlibCanvas(self, width=8, height=4, dpi=100)
        layout.addWidget(self.cuotas_canvas)
        
        # Tabla de detalle
        detalle_label = QLabel("Detalle de Cuotas Pendientes")
        detalle_font = QFont()
        detalle_font.setPointSize(14)
        detalle_label.setFont(detalle_font)
        layout.addWidget(detalle_label)
        
        self.cuotas_table = QTableWidget()
        self.cuotas_table.setColumnCount(6)
        self.cuotas_table.setHorizontalHeaderLabels(["ID", "Fecha", "Árbitro", "Monto", "Monto Pagado", "Pendiente"])
        self.cuotas_table.horizontalHeader().setStretchLastSection(True)
        self.cuotas_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cuotas_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.cuotas_table)
        
        # Botón de generar y exportar
        buttons_layout = QHBoxLayout()
        
        self.cuotas_generar_btn = QPushButton("Generar y Descargar")
        self.cuotas_generar_btn.clicked.connect(self.on_generar_cuotas)
        
        self.cuotas_exportar_btn = QPushButton("Exportar a Excel")
        self.cuotas_exportar_btn.clicked.connect(self.on_exportar_cuotas)
        
        buttons_layout.addWidget(self.cuotas_generar_btn)
        buttons_layout.addWidget(self.cuotas_exportar_btn)
        
        layout.addLayout(buttons_layout)
    
    def setup_tab_libro(self):
        layout = QVBoxLayout(self.tab_libro)
        
        # Filtros
        filtros_layout = QHBoxLayout()
        
        # Desde
        desde_label = QLabel("Desde:")
        self.libro_desde_date = QDateEdit()
        self.libro_desde_date.setDate(QDate.currentDate().addDays(-30))  # Último mes por defecto
        self.libro_desde_date.setCalendarPopup(True)
        
        # Hasta
        hasta_label = QLabel("Hasta:")
        self.libro_hasta_date = QDateEdit()
        self.libro_hasta_date.setDate(QDate.currentDate())
        self.libro_hasta_date.setCalendarPopup(True)
        
        # Tipo
        tipo_label = QLabel("Tipo:")
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Todos", "Ingreso", "Egreso"])
        
        # Botón de búsqueda
        self.libro_buscar_btn = QPushButton("Buscar y Descargar")
        self.libro_buscar_btn.clicked.connect(self.on_buscar_libro)
        
        filtros_layout.addWidget(desde_label)
        filtros_layout.addWidget(self.libro_desde_date)
        filtros_layout.addWidget(hasta_label)
        filtros_layout.addWidget(self.libro_hasta_date)
        filtros_layout.addWidget(tipo_label)
        filtros_layout.addWidget(self.tipo_combo)
        filtros_layout.addWidget(self.libro_buscar_btn)
        
        layout.addLayout(filtros_layout)
        
        # Tabla de partidas
        self.libro_table = QTableWidget()
        self.libro_table.setColumnCount(8)
        self.libro_table.setHorizontalHeaderLabels(["ID", "Fecha", "Cuenta", "Detalle", "Ingreso", "Egreso", "Saldo", "Usuario"])
        self.libro_table.horizontalHeader().setStretchLastSection(True)
        self.libro_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.libro_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.libro_table)
        
        # Totales
        totales_layout = QHBoxLayout()
        
        self.libro_total_ingresos_label = QLabel("Total Ingresos: $0.00")
        self.libro_total_ingresos_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        
        self.libro_total_egresos_label = QLabel("Total Egresos: $0.00")
        self.libro_total_egresos_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F44336;")
        
        self.libro_balance_label = QLabel("Balance: $0.00")
        self.libro_balance_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        totales_layout.addWidget(self.libro_total_ingresos_label)
        totales_layout.addWidget(self.libro_total_egresos_label)
        totales_layout.addWidget(self.libro_balance_label)
        
        layout.addLayout(totales_layout)
        
        # Botón de exportar
        self.libro_exportar_btn = QPushButton("Exportar a Excel")
        self.libro_exportar_btn.clicked.connect(self.on_exportar_libro)
        layout.addWidget(self.libro_exportar_btn)
    
    def connect_signals(self):
        self.sidebar.navigation_requested.connect(self.navigation_requested)
    
    def refresh_data(self):
        """Carga los datos iniciales"""
        self.on_generar_balance()
        self.on_generar_ingresos_egresos()
        self.on_generar_cuotas()
        self.on_buscar_libro()
    
    # Métodos para Balance General
    def on_generar_balance(self):
        """Genera el reporte de balance general y lo descarga"""
        try:
            # Obtener fechas
            desde = self.balance_desde_date.date().toString("yyyy-MM-dd")
            hasta = self.balance_hasta_date.date().toString("yyyy-MM-dd")
            
            # Llamada a la API
            headers = session.get_headers()
            response = requests.get(
                f"{session.api_url}/reportes/balance",
                headers=headers,
                params={"fecha_desde": desde, "fecha_hasta": hasta}
            )
            
            if response.status_code == 200:
                balance_data = response.json()
                
                # Actualizar métricas
                ingresos_totales = balance_data.get('ingresos_totales', 0)
                egresos_totales = balance_data.get('egresos_totales', 0)
                balance_neto = balance_data.get('balance_neto', 0)
                
                self.ingresos_label.setText(f"Ingresos Totales: ${ingresos_totales:,.2f}")
                self.egresos_label.setText(f"Egresos Totales: ${egresos_totales:,.2f}")
                
                variacion = balance_data.get('variacion_porcentual', 0)
                variacion_text = f" ({variacion:+.1f}%)" if variacion != 0 else ""
                self.balance_neto_label.setText(f"Balance Neto: ${balance_neto:,.2f}{variacion_text}")
                
                # Gráfico de evolución del balance
                if 'historico' in balance_data and balance_data['historico']:
                    historico = balance_data['historico']
                    
                    # Limpiar el gráfico anterior
                    self.balance_canvas.axes.clear()
                    
                    # Configurar datos
                    fechas = [item.get('fecha', '') for item in historico]
                    balances = [item.get('balance_acumulado', 0) for item in historico]
                    
                    # Crear gráfico
                    self.balance_canvas.axes.plot(fechas, balances, 'o-', color='blue')
                    self.balance_canvas.axes.set_xlabel('Fecha')
                    self.balance_canvas.axes.set_ylabel('Balance Acumulado ($)')
                    self.balance_canvas.axes.set_title('Evolución del Balance')
                    
                    # Rotar etiquetas para mejor legibilidad
                    self.balance_canvas.axes.tick_params(axis='x', rotation=45)
                    
                    self.balance_canvas.fig.tight_layout()
                    self.balance_canvas.draw()
                
                # Tabla de detalle
                if 'detalle' in balance_data and balance_data['detalle']:
                    detalle = balance_data['detalle']
                    
                    # Limpiar tabla
                    self.balance_table.setRowCount(0)
                    
                    # Llenar tabla con datos
                    for row, item in enumerate(detalle):
                        self.balance_table.insertRow(row)
                        
                        # Fecha
                        fecha = datetime.strptime(item.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if item.get('fecha') else ''
                        self.balance_table.setItem(row, 0, QTableWidgetItem(fecha))
                        
                        # Cuenta
                        self.balance_table.setItem(row, 1, QTableWidgetItem(item.get('cuenta', '')))
                        
                        # Ingreso
                        ingreso = item.get('ingreso', 0)
                        ingreso_item = QTableWidgetItem(f"${ingreso:,.2f}")
                        ingreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.balance_table.setItem(row, 2, ingreso_item)
                        
                        # Egreso
                        egreso = item.get('egreso', 0)
                        egreso_item = QTableWidgetItem(f"${egreso:,.2f}")
                        egreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.balance_table.setItem(row, 3, egreso_item)
                        
                        # Saldo
                        saldo = item.get('saldo', 0)
                        saldo_item = QTableWidgetItem(f"${saldo:,.2f}")
                        saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.balance_table.setItem(row, 4, saldo_item)
                    
                    # Ajustar columnas
                    self.balance_table.resizeColumnsToContents()
                
                # Descargar automáticamente
                self.descargar_reporte_balance()
            else:
                QMessageBox.warning(self, "Error", "No se pudo obtener el balance")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar balance: {str(e)}")
    
    def descargar_reporte_balance(self):
        """Descarga automáticamente el reporte de balance en Excel"""
        try:
            # Verificar si hay datos para exportar
            if self.balance_table.rowCount() == 0:
                QMessageBox.warning(self, "Advertencia", "No hay datos para descargar")
                return
            
            # Definir nombre del archivo con fecha
            fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
            periodo = f"{self.balance_desde_date.date().toString('yyyyMMdd')}-{self.balance_hasta_date.date().toString('yyyyMMdd')}"
            nombre_archivo = f"Balance_{periodo}_{fecha_actual}.xlsx"
            
            # Ruta para guardar (en directorio de descargas por defecto)
            descargas_path = os.path.join(os.path.expanduser("~"), "Downloads")
            file_path = os.path.join(descargas_path, nombre_archivo)
            
            # Crear DataFrame con los datos de la tabla
            data = []
            for row in range(self.balance_table.rowCount()):
                row_data = {}
                for col in range(self.balance_table.columnCount()):
                    header = self.balance_table.horizontalHeaderItem(col).text()
                    item = self.balance_table.item(row, col)
                    row_data[header] = item.text() if item else ""
                data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # Guardar a Excel
            df.to_excel(file_path, index=False)
            
            QMessageBox.information(self, "Éxito", f"Reporte descargado exitosamente en {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al descargar reporte: {str(e)}")
    
    def on_exportar_balance(self):
        """Exporta el balance a Excel (permite seleccionar ubicación)"""
        try:
            # Verificar si hay datos para exportar
            if self.balance_table.rowCount() == 0:
                QMessageBox.warning(self, "Advertencia", "No hay datos para exportar")
                return
            
            # Seleccionar ruta para guardar
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options
            )
            
            if file_path:
                # Asegurar que tiene extensión .xlsx
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                
                # Crear DataFrame con los datos de la tabla
                data = []
                for row in range(self.balance_table.rowCount()):
                    row_data = {}
                    for col in range(self.balance_table.columnCount()):
                        header = self.balance_table.horizontalHeaderItem(col).text()
                        item = self.balance_table.item(row, col)
                        row_data[header] = item.text() if item else ""
                    data.append(row_data)
                
                df = pd.DataFrame(data)
                
                # Guardar a Excel
                df.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "Éxito", f"Datos exportados exitosamente a {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")
    
    # Métodos para Ingresos y Egresos
    def on_generar_ingresos_egresos(self):
        """Genera el reporte de ingresos y egresos y lo descarga"""
        try:
            # Obtener año seleccionado
            anio = self.anio_combo.currentData()
            
            # Llamada a la API
            headers = session.get_headers()
            response = requests.get(
                f"{session.api_url}/reportes/ingresos_egresos_mensuales",
                headers=headers,
                params={"anio": anio}
            )
            
            if response.status_code == 200:
                ie_data = response.json()
                
                if 'datos' in ie_data and ie_data['datos']:
                    datos = ie_data['datos']
                    
                    # Limpiar tablas y gráficos
                    self.ie_table.setRowCount(0)
                    self.ie_canvas.axes.clear()
                    self.balance_ie_canvas.axes.clear()
                    
                    # Configurar datos para gráficos
                    meses = [item.get('mes', '') for item in datos]
                    ingresos = [item.get('ingresos', 0) for item in datos]
                    egresos = [item.get('egresos', 0) for item in datos]
                    balances = [item.get('balance', 0) for item in datos]
                    
                    # Crear gráfico de barras para ingresos/egresos
                    x = range(len(meses))
                    width = 0.35
                    
                    self.ie_canvas.axes.bar([i - width/2 for i in x], ingresos, width, label='Ingresos', color='#4CAF50')
                    self.ie_canvas.axes.bar([i + width/2 for i in x], egresos, width, label='Egresos', color='#F44336')
                    
                    self.ie_canvas.axes.set_xlabel('Mes')
                    self.ie_canvas.axes.set_ylabel('Monto ($)')
                    self.ie_canvas.axes.set_title(f'Ingresos y Egresos Mensuales - {anio}')
                    self.ie_canvas.axes.set_xticks(x)
                    self.ie_canvas.axes.set_xticklabels(meses)
                    self.ie_canvas.axes.legend()
                    
                    self.ie_canvas.fig.tight_layout()
                    self.ie_canvas.draw()
                    
                    # Crear gráfico de barras para balance mensual
                    self.balance_ie_canvas.axes.bar(x, balances, color=[
                        '#4CAF50' if bal >= 0 else '#F44336' for bal in balances
                    ])
                    
                    self.balance_ie_canvas.axes.set_xlabel('Mes')
                    self.balance_ie_canvas.axes.set_ylabel('Balance ($)')
                    self.balance_ie_canvas.axes.set_title(f'Balance Mensual - {anio}')
                    self.balance_ie_canvas.axes.set_xticks(x)
                    self.balance_ie_canvas.axes.set_xticklabels(meses)
                    
                    self.balance_ie_canvas.fig.tight_layout()
                    self.balance_ie_canvas.draw()
                    
                    # Llenar tabla con datos
                    total_ingresos = 0
                    total_egresos = 0
                    
                    for row, item in enumerate(datos):
                        self.ie_table.insertRow(row)
                        
                        # Mes
                        self.ie_table.setItem(row, 0, QTableWidgetItem(item.get('mes', '')))
                        
                        # Ingresos
                        ingreso = item.get('ingresos', 0)
                        ingreso_item = QTableWidgetItem(f"${ingreso:,.2f}")
                        ingreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.ie_table.setItem(row, 1, ingreso_item)
                        
                        # Egresos
                        egreso = item.get('egresos', 0)
                        egreso_item = QTableWidgetItem(f"${egreso:,.2f}")
                        egreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.ie_table.setItem(row, 2, egreso_item)
                        
                        # Balance
                        balance = item.get('balance', 0)
                        balance_item = QTableWidgetItem(f"${balance:,.2f}")
                        balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.ie_table.setItem(row, 3, balance_item)
                        
                        # Acumular totales
                        total_ingresos += ingreso
                        total_egresos += egreso
                    
                    # Ajustar columnas
                    self.ie_table.resizeColumnsToContents()
                    
                    # Actualizar totales
                    self.ie_total_ingresos_label.setText(f"Total Ingresos: ${total_ingresos:,.2f}")
                    self.ie_total_egresos_label.setText(f"Total Egresos: ${total_egresos:,.2f}")
                    self.ie_balance_total_label.setText(f"Balance Total: ${total_ingresos - total_egresos:,.2f}")
                    
                    # Descargar automáticamente
                    self.descargar_reporte_ingresos_egresos()
                else:
                    QMessageBox.warning(self, "Advertencia", f"No hay datos disponibles para el año {anio}")
            else:
                QMessageBox.warning(self, "Error", "No se pudieron obtener los datos")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar reporte: {str(e)}")
    
    def descargar_reporte_ingresos_egresos(self):
        """Descarga automáticamente el reporte de ingresos y egresos en Excel"""
        try:
            # Verificar si hay datos para exportar
            if self.ie_table.rowCount() == 0:
                QMessageBox.warning(self, "Advertencia", "No hay datos para descargar")
                return
            
            # Definir nombre del archivo con fecha y año
            fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
            anio = self.anio_combo.currentData()
            nombre_archivo = f"Ingresos_Egresos_{anio}_{fecha_actual}.xlsx"
            
            # Ruta para guardar (en directorio de descargas por defecto)
            descargas_path = os.path.join(os.path.expanduser("~"), "Downloads")
            file_path = os.path.join(descargas_path, nombre_archivo)
            
            # Crear DataFrame con los datos de la tabla
            data = []
            for row in range(self.ie_table.rowCount()):
                row_data = {}
                for col in range(self.ie_table.columnCount()):
                    header = self.ie_table.horizontalHeaderItem(col).text()
                    item = self.ie_table.item(row, col)
                    row_data[header] = item.text() if item else ""
                data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # Guardar a Excel
            df.to_excel(file_path, index=False)
            
            QMessageBox.information(self, "Éxito", f"Reporte descargado exitosamente en {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al descargar reporte: {str(e)}")
    
    def on_exportar_ingresos_egresos(self):
        """Exporta el reporte de ingresos y egresos a Excel (permite seleccionar ubicación)"""
        try:
            # Verificar si hay datos para exportar
            if self.ie_table.rowCount() == 0:
                QMessageBox.warning(self, "Advertencia", "No hay datos para exportar")
                return
            
            # Seleccionar ruta para guardar
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options
            )
            
            if file_path:
                # Asegurar que tiene extensión .xlsx
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                
                # Crear DataFrame con los datos de la tabla
                data = []
                for row in range(self.ie_table.rowCount()):
                    row_data = {}
                    for col in range(self.ie_table.columnCount()):
                        header = self.ie_table.horizontalHeaderItem(col).text()
                        item = self.ie_table.item(row, col)
                        row_data[header] = item.text() if item else ""
                    data.append(row_data)
                
                df = pd.DataFrame(data)
                
                # Guardar a Excel
                df.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "Éxito", f"Datos exportados exitosamente a {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")
    
    # Métodos para Cuotas Pendientes
    def on_generar_cuotas(self):
        """Genera el reporte de cuotas pendientes y lo descarga"""
        try:
            # Llamada a la API
            headers = session.get_headers()
            url = f"{session.api_url}/reportes/cuotas_pendientes"
            
            print(f"Realizando petición GET a: {url}")
            
            response = requests.get(
                url,
                headers=headers
            )
            
            if response.status_code == 200:
                cuotas_data = response.json()
                
                # Manejar tanto si es un diccionario como si es una lista
                if isinstance(cuotas_data, dict):
                    cantidad = cuotas_data.get('cantidad_pendientes', 0)
                    monto_pendiente = cuotas_data.get('monto_total_pendiente', 0)
                    cuotas = cuotas_data.get('cuotas', [])
                elif isinstance(cuotas_data, list):
                    # Si es una lista, asumimos que es directamente la lista de cuotas
                    cuotas = cuotas_data
                    cantidad = len(cuotas)
                    monto_pendiente = sum(cuota.get('monto_pendiente', 0) for cuota in cuotas)
                else:
                    cuotas = []
                    cantidad = 0
                    monto_pendiente = 0
                
                self.cuotas_pendientes_label.setText(f"Cuotas Pendientes: {cantidad}")
                self.monto_pendiente_label.setText(f"Monto Pendiente: ${monto_pendiente:,.2f}")
                
                # Limpiar tabla
                self.cuotas_table.setRowCount(0)
                
                # Actualizar tabla si hay cuotas
                if cuotas:
                    # Crear gráfico para mostrar distribución de cuotas
                    self.cuotas_canvas.axes.clear()
                    
                    # Podemos agrupar por estado, árbitro o fecha
                    # Aquí agruparemos por árbitro como ejemplo
                    arbitros = {}
                    
                    for row, cuota in enumerate(cuotas):
                        self.cuotas_table.insertRow(row)
                        
                        # ID
                        cuota_id = cuota.get('id', '')
                        self.cuotas_table.setItem(row, 0, QTableWidgetItem(str(cuota_id)))
                        
                        # Fecha
                        fecha_str = cuota.get('fecha', '')
                        if fecha_str:
                            try:
                                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                            except:
                                fecha = fecha_str
                        else:
                            fecha = ''
                        self.cuotas_table.setItem(row, 1, QTableWidgetItem(fecha))
                        
                        # Árbitro
                        arbitro = cuota.get('arbitro', {}).get('nombre', '') if isinstance(cuota.get('arbitro', ''), dict) else cuota.get('arbitro', '')
                        self.cuotas_table.setItem(row, 2, QTableWidgetItem(arbitro))
                        
                        # Contabilizar para el gráfico
                        if arbitro in arbitros:
                            arbitros[arbitro] += 1
                        else:
                            arbitros[arbitro] = 1
                        
                        # Monto
                        monto = cuota.get('monto', 0)
                        monto_item = QTableWidgetItem(f"${monto:,.2f}")
                        monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.cuotas_table.setItem(row, 3, monto_item)
                        
                        # Monto Pagado
                        monto_pagado = cuota.get('monto_pagado', 0)
                        monto_pagado_item = QTableWidgetItem(f"${monto_pagado:,.2f}")
                        monto_pagado_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.cuotas_table.setItem(row, 4, monto_pagado_item)
                        
                        # Pendiente
                        pendiente = monto - monto_pagado
                        pendiente_item = QTableWidgetItem(f"${pendiente:,.2f}")
                        pendiente_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.cuotas_table.setItem(row, 5, pendiente_item)
                    
                    # Ajustar columnas
                    self.cuotas_table.resizeColumnsToContents()
                    
                    # Crear gráfico de pastel para cuotas por árbitro
                    labels = list(arbitros.keys())
                    sizes = list(arbitros.values())
                    
                    if labels:  # Verificar que hay datos para el gráfico
                        self.cuotas_canvas.axes.pie(
                            sizes, labels=labels, autopct='%1.1f%%',
                            startangle=90, shadow=True
                        )
                        self.cuotas_canvas.axes.set_title('Distribución de Cuotas Pendientes por Árbitro')
                        self.cuotas_canvas.axes.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                        self.cuotas_canvas.fig.tight_layout()
                        self.cuotas_canvas.draw()
                    
                    # Descargar automáticamente
                    self.descargar_reporte_cuotas()
                else:
                    self.cuotas_canvas.axes.clear()
                    self.cuotas_canvas.draw()
                    QMessageBox.information(self, "Información", "No hay cuotas pendientes")
                    
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron obtener las cuotas: {response.status_code}")
        except Exception as e:
            print(f"Error al generar reporte de cuotas: {e}")
            QMessageBox.critical(self, "Error", f"Error al generar reporte: {str(e)}")
    
    def descargar_reporte_cuotas(self):
        """Descarga automáticamente el reporte de cuotas pendientes en Excel"""
        try:
            # Verificar si hay datos para exportar
            if self.cuotas_table.rowCount() == 0:
                return
            
            # Definir nombre del archivo con fecha
            fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"Cuotas_Pendientes_{fecha_actual}.xlsx"
            
            # Ruta para guardar (en directorio de descargas por defecto)
            descargas_path = os.path.join(os.path.expanduser("~"), "Downloads")
            file_path = os.path.join(descargas_path, nombre_archivo)
            
            # Crear DataFrame con los datos de la tabla
            data = []
            for row in range(self.cuotas_table.rowCount()):
                row_data = {}
                for col in range(self.cuotas_table.columnCount()):
                    header = self.cuotas_table.horizontalHeaderItem(col).text()
                    item = self.cuotas_table.item(row, col)
                    row_data[header] = item.text() if item else ""
                data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # Guardar a Excel
            df.to_excel(file_path, index=False)
            
            QMessageBox.information(self, "Éxito", f"Reporte descargado exitosamente en {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al descargar reporte: {str(e)}")
    
    def on_exportar_cuotas(self):
        """Exporta el reporte de cuotas pendientes a Excel (permite seleccionar ubicación)"""
        try:
            # Verificar si hay datos para exportar
            if self.cuotas_table.rowCount() == 0:
                QMessageBox.warning(self, "Advertencia", "No hay datos para exportar")
                return
            
            # Seleccionar ruta para guardar
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options
            )
            
            if file_path:
                # Asegurar que tiene extensión .xlsx
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                
                # Crear DataFrame con los datos de la tabla
                data = []
                for row in range(self.cuotas_table.rowCount()):
                    row_data = {}
                    for col in range(self.cuotas_table.columnCount()):
                        header = self.cuotas_table.horizontalHeaderItem(col).text()
                        item = self.cuotas_table.item(row, col)
                        row_data[header] = item.text() if item else ""
                    data.append(row_data)
                
                df = pd.DataFrame(data)
                
                # Guardar a Excel
                df.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "Éxito", f"Datos exportados exitosamente a {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")
    
    # Métodos para Libro Diario
    def on_buscar_libro(self):
        """Busca partidas para el libro diario y descarga el reporte"""
        try:
            # Obtener filtros
            desde = self.libro_desde_date.date().toString("yyyy-MM-dd")
            hasta = self.libro_hasta_date.date().toString("yyyy-MM-dd")
            tipo = self.tipo_combo.currentText().lower()
            
            # Preparar parámetros
            params = {
                "skip": 0,
                "limit": 1000,
                "fecha_desde": desde,
                "fecha_hasta": hasta
            }
            
            # Agregar filtro por tipo si no es "todos"
            if tipo != "todos":
                params["tipo"] = tipo
            
            # Llamada a la API
            headers = session.get_headers()
            response = requests.get(
                f"{session.api_url}/partidas",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                partidas = response.json()
                
                # Limpiar tabla
                self.libro_table.setRowCount(0)
                
                # Variables para totales
                total_ingresos = 0
                total_egresos = 0
                
                # Llenar tabla con datos
                for row, partida in enumerate(partidas):
                    self.libro_table.insertRow(row)
                    
                    # ID
                    self.libro_table.setItem(row, 0, QTableWidgetItem(str(partida.get('id', ''))))
                    
                    # Fecha
                    fecha = datetime.strptime(partida.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if partida.get('fecha') else ''
                    self.libro_table.setItem(row, 1, QTableWidgetItem(fecha))
                    
                    # Cuenta
                    self.libro_table.setItem(row, 2, QTableWidgetItem(partida.get('cuenta', '')))
                    
                    # Detalle
                    self.libro_table.setItem(row, 3, QTableWidgetItem(partida.get('detalle', '')))
                    
                    # Ingreso
                    ingreso = partida.get('ingreso', 0)
                    ingreso_item = QTableWidgetItem(f"${ingreso:,.2f}")
                    ingreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.libro_table.setItem(row, 4, ingreso_item)
                    
                    # Egreso
                    egreso = partida.get('egreso', 0)
                    egreso_item = QTableWidgetItem(f"${egreso:,.2f}")
                    egreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.libro_table.setItem(row, 5, egreso_item)
                    
                    # Saldo
                    saldo = partida.get('saldo', 0)
                    saldo_item = QTableWidgetItem(f"${saldo:,.2f}")
                    saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.libro_table.setItem(row, 6, saldo_item)
                    
                    # Usuario
                    usuario = partida.get('usuario', {}).get('nombre', '') if partida.get('usuario') else ''
                    self.libro_table.setItem(row, 7, QTableWidgetItem(usuario))
                    
                    # Acumular totales
                    total_ingresos += ingreso
                    total_egresos += egreso
                
                # Ajustar columnas
                self.libro_table.resizeColumnsToContents()
                
                # Actualizar totales
                self.libro_total_ingresos_label.setText(f"Total Ingresos: ${total_ingresos:,.2f}")
                self.libro_total_egresos_label.setText(f"Total Egresos: ${total_egresos:,.2f}")
                self.libro_balance_label.setText(f"Balance: ${total_ingresos - total_egresos:,.2f}")
                
                # Descargar automáticamente
                self.descargar_libro_diario()
            else:
                QMessageBox.warning(self, "Error", "No se pudieron obtener las partidas")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al buscar partidas: {str(e)}")
    
    def descargar_libro_diario(self):
        """Descarga automáticamente el libro diario en Excel"""
        try:
            # Verificar si hay datos para exportar
            if self.libro_table.rowCount() == 0:
                QMessageBox.warning(self, "Advertencia", "No hay datos para descargar")
                return
            
            # Definir nombre del archivo con fecha y período
            fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
            periodo = f"{self.libro_desde_date.date().toString('yyyyMMdd')}-{self.libro_hasta_date.date().toString('yyyyMMdd')}"
            tipo = self.tipo_combo.currentText().lower()
            nombre_archivo = f"Libro_Diario_{tipo}_{periodo}_{fecha_actual}.xlsx"
            
            # Ruta para guardar (en directorio de descargas por defecto)
            descargas_path = os.path.join(os.path.expanduser("~"), "Downloads")
            file_path = os.path.join(descargas_path, nombre_archivo)
            
            # Crear DataFrame con los datos de la tabla
            data = []
            for row in range(self.libro_table.rowCount()):
                row_data = {}
                for col in range(self.libro_table.columnCount()):
                    header = self.libro_table.horizontalHeaderItem(col).text()
                    item = self.libro_table.item(row, col)
                    row_data[header] = item.text() if item else ""
                data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # Guardar a Excel
            df.to_excel(file_path, index=False)
            
            QMessageBox.information(self, "Éxito", f"Reporte descargado exitosamente en {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al descargar reporte: {str(e)}")
    
    def on_exportar_libro(self):
        """Exporta el libro diario a Excel (permite seleccionar ubicación)"""
        try:
            # Verificar si hay datos para exportar
            if self.libro_table.rowCount() == 0:
                QMessageBox.warning(self, "Advertencia", "No hay datos para exportar")
                return
            
            # Seleccionar ruta para guardar
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options
            )
            
            if file_path:
                # Asegurar que tiene extensión .xlsx
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                
                # Crear DataFrame con los datos de la tabla
                data = []
                for row in range(self.libro_table.rowCount()):
                    row_data = {}
                    for col in range(self.libro_table.columnCount()):
                        header = self.libro_table.horizontalHeaderItem(col).text()
                        item = self.libro_table.item(row, col)
                        row_data[header] = item.text() if item else ""
                    data.append(row_data)
                
                df = pd.DataFrame(data)
                
                # Guardar a Excel
                df.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "Éxito", f"Datos exportados exitosamente a {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")