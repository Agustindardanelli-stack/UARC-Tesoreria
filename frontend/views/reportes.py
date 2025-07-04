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
    QFormLayout, QDateEdit, QComboBox, QMessageBox, QFileDialog, QGroupBox,
    QStyledItemDelegate, QHeaderView
)
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QLinearGradient, QBrush, QPainter
from PySide6.QtCore import Qt, Signal, QDate, QSize, QPoint, QRect

from views.dashboard import SidebarWidget, MatplotlibCanvas
from sesion import session

# Colores personalizados para una apariencia más profesional
class AppColors:
    PRIMARY = "#1976D2"  # Azul principal
    SECONDARY = "#388E3C"  # Verde para ingresos
    DANGER = "#D32F2F"  # Rojo para egresos
    WARNING = "#F57C00"  # Naranja para alertas
    BACKGROUND = "#F5F5F5"  # Fondo claro
    CARD_BG = "#FFFFFF"  # Fondo de tarjetas
    TEXT_PRIMARY = "#212121"  # Texto principal
    TEXT_SECONDARY = "#757575"  # Texto secundario
    BORDER = "#E0E0E0"  # Bordes

# Estilo para botones
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {AppColors.PRIMARY};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #1565C0;
    }}
    QPushButton:pressed {{
        background-color: #0D47A1;
    }}
"""

# Estilo para tablas
TABLE_STYLE = f"""
    QTableWidget {{
        background-color: {AppColors.CARD_BG};
        alternate-background-color: #F9F9F9;
        border: 1px solid {AppColors.BORDER};
        border-radius: 4px;
        gridline-color: {AppColors.BORDER};
    }}
    QHeaderView::section {{
        background-color: #E3F2FD;
        color: {AppColors.TEXT_PRIMARY};
        padding: 6px;
        font-weight: bold;
        border: none;
        border-bottom: 1px solid {AppColors.BORDER};
    }}
"""

# Estilo para GroupBox
GROUP_BOX_STYLE = f"""
    QGroupBox {{
        font-weight: bold;
        border: 1px solid {AppColors.BORDER};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 16px;
        background-color: {AppColors.CARD_BG};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        color: {AppColors.PRIMARY};
    }}
"""

# Delegado personalizado para celdas numéricas en tablas
class MoneyDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() in [1, 2, 3]:  # Columnas con valores monetarios (Ingresos, Egresos, Balance)
            value = index.data()
            if value and "$" in value:
                # Extraer el valor numérico y determinar si es positivo/negativo
                try:
                    num_value = float(value.replace('$', '').replace(',', ''))
                    color = QColor(AppColors.SECONDARY) if num_value >= 0 else QColor(AppColors.DANGER)
                    
                    # Configurar el estilo del texto
                    option.palette.setColor(QPalette.Text, color)
                except:
                    pass
        
        super().paint(painter, option, index)

# Clase principal para la vista de reportes mejorada
class ReportesView(QWidget):
    navigation_requested = Signal(str)  # Señal para solicitar navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
        
        # Aplicar estilo general
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AppColors.BACKGROUND};
                color: {AppColors.TEXT_PRIMARY};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {AppColors.TEXT_PRIMARY};
            }}
            QComboBox {{
                padding: 5px;
                border: 1px solid {AppColors.BORDER};
                border-radius: 4px;
                background-color: white;
                min-width: 100px;
            }}
            QDateEdit {{
                padding: 5px;
                border: 1px solid {AppColors.BORDER};
                border-radius: 4px;
                background-color: white;
                min-width: 120px;
            }}
        """)
    
    def setup_ui(self):
        # Layout principal
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.setFixedWidth(200)
        
        # Widget de contenido
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(16)
        
        # Encabezado con título y descripción
        header_layout = QVBoxLayout()
        
        # Título con estilo moderno
        title_label = QLabel("Reportes Financieros")
        title_font = QFont("Segoe UI", 22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Descripción
        desc_label = QLabel("Visualización de ingresos, egresos y registro de operaciones")
        desc_label.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 14px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(desc_label)
        header_layout.addSpacing(20)
        
        self.content_layout.addLayout(header_layout)
        
        # Tabs para los diferentes reportes con estilo mejorado
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {AppColors.BORDER};
                border-radius: 4px;
                background-color: {AppColors.CARD_BG};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: #E8E8E8;
                color: {AppColors.TEXT_PRIMARY};
                border: 1px solid {AppColors.BORDER};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 150px;
                padding: 10px 15px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {AppColors.CARD_BG};
                border-bottom: 1px solid {AppColors.CARD_BG};
            }}
            QTabBar::tab:!selected {{
                margin-top: 2px;
            }}
        """)
        
        # Tab 1: Ingresos y Egresos
        self.tab_ingresos_egresos = QWidget()
        self.setup_tab_ingresos_egresos()
        self.tabs.addTab(self.tab_ingresos_egresos, "Ingresos y Egresos")
        
        # Tab 2: Libro Diario
        self.tab_libro = QWidget()
        self.setup_tab_libro()
        self.tabs.addTab(self.tab_libro, "Libro Diario")
        
        self.content_layout.addWidget(self.tabs)
        
        # Agregar al layout principal
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_widget)
    
    def setup_tab_ingresos_egresos(self):
        layout = QVBoxLayout(self.tab_ingresos_egresos)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Sección de filtros en un card
        filtros_card = QGroupBox("Período de Análisis")
        filtros_card.setStyleSheet(GROUP_BOX_STYLE)
        filtros_layout = QHBoxLayout(filtros_card)
        
        # Selector de año con estilo mejorado
        anio_label = QLabel("Seleccionar Año:")
        anio_label.setStyleSheet("font-weight: bold;")
        self.anio_combo = QComboBox()
        self.anio_combo.setFixedWidth(120)
        
        # Llenar combo con los últimos 5 años
        current_year = datetime.now().year
        for year in range(current_year - 4, current_year + 1):
            self.anio_combo.addItem(str(year), year)
        
        # Seleccionar año actual
        self.anio_combo.setCurrentIndex(4)  # Último elemento (año actual)
        
        # Botón de generar con ícono
        self.ie_generar_btn = QPushButton("Generar Reporte")
        self.ie_generar_btn.setStyleSheet(BUTTON_STYLE)
        self.ie_generar_btn.setMinimumWidth(150)
        self.ie_generar_btn.clicked.connect(self.on_generar_ingresos_egresos)
        
        filtros_layout.addWidget(anio_label)
        filtros_layout.addWidget(self.anio_combo)
        filtros_layout.addStretch()
        filtros_layout.addWidget(self.ie_generar_btn)
        
        layout.addWidget(filtros_card)
        
        # Card para los gráficos
        graficos_card = QGroupBox("Visualización Gráfica")
        graficos_card.setStyleSheet(GROUP_BOX_STYLE)
        graficos_layout = QVBoxLayout(graficos_card)
        
        # Gráficos mejorados
        self.ie_canvas = MatplotlibCanvas(self, width=8, height=3.5, dpi=100)
        self.balance_ie_canvas = MatplotlibCanvas(self, width=8, height=3.5, dpi=100)
        
        graficos_layout.addWidget(self.ie_canvas)
        graficos_layout.addWidget(self.balance_ie_canvas)
        
        layout.addWidget(graficos_card)
        
        # Card para los datos tabulares
        datos_card = QGroupBox("Datos Mensuales")
        datos_card.setStyleSheet(GROUP_BOX_STYLE)
        datos_layout = QVBoxLayout(datos_card)
        
        # Tabla con estilo mejorado
        self.ie_table = QTableWidget()
        self.ie_table.setColumnCount(4)
        self.ie_table.setHorizontalHeaderLabels(["Mes", "Ingresos", "Egresos", "Balance"])
        self.ie_table.setStyleSheet(TABLE_STYLE)
        self.ie_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ie_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ie_table.setAlternatingRowColors(True)
        self.ie_table.setItemDelegate(MoneyDelegate())
        
        datos_layout.addWidget(self.ie_table)
        
        layout.addWidget(datos_card)
        
        # Card para los totales
        totales_card = QGroupBox("Resumen Anual")
        totales_card.setStyleSheet(GROUP_BOX_STYLE)
        totales_layout = QHBoxLayout(totales_card)
        
        # Totales con diseño mejorado
        self.ie_total_ingresos_label = QLabel("Total Ingresos: $0.00")
        self.ie_total_ingresos_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {AppColors.SECONDARY};")
        
        self.ie_total_egresos_label = QLabel("Total Egresos: $0.00")
        self.ie_total_egresos_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {AppColors.DANGER};")
        
        self.ie_balance_total_label = QLabel("Balance Total: $0.00")
        self.ie_balance_total_label.setStyleSheet(f"font-size: 18px; font-weight: bold;")
        
        totales_layout.addWidget(self.ie_total_ingresos_label)
        totales_layout.addStretch()
        totales_layout.addWidget(self.ie_total_egresos_label)
        totales_layout.addStretch()
        totales_layout.addWidget(self.ie_balance_total_label)
        
        layout.addWidget(totales_card)
        
        # Botón de exportar al final
        self.ie_exportar_btn = QPushButton("Exportar a Excel")
        self.ie_exportar_btn.setStyleSheet(f"""
            {BUTTON_STYLE}
            background-color: {AppColors.SECONDARY};
        """)
        self.ie_exportar_btn.setMinimumWidth(200)
        self.ie_exportar_btn.clicked.connect(self.on_exportar_ingresos_egresos)
        
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        export_layout.addWidget(self.ie_exportar_btn)
        export_layout.addStretch()
        
        layout.addLayout(export_layout)
    
    def setup_tab_libro(self):
        layout = QVBoxLayout(self.tab_libro)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Card para los filtros
        filtros_card = QGroupBox("Filtros de Búsqueda")
        filtros_card.setStyleSheet(GROUP_BOX_STYLE)
        filtros_layout = QHBoxLayout(filtros_card)
        
        # Desde con mejor estilo
        desde_label = QLabel("Desde:")
        desde_label.setStyleSheet("font-weight: bold;")
        self.libro_desde_date = QDateEdit()
        self.libro_desde_date.setFixedWidth(130)
        self.libro_desde_date.setDate(QDate.currentDate().addDays(-30))  # Último mes por defecto
        self.libro_desde_date.setCalendarPopup(True)
        
        # Hasta con mejor estilo
        hasta_label = QLabel("Hasta:")
        hasta_label.setStyleSheet("font-weight: bold;")
        self.libro_hasta_date = QDateEdit()
        self.libro_hasta_date.setFixedWidth(130)
        self.libro_hasta_date.setDate(QDate.currentDate())
        self.libro_hasta_date.setCalendarPopup(True)
        
        # Tipo con mejor estilo
        tipo_label = QLabel("Tipo:")
        tipo_label.setStyleSheet("font-weight: bold;")
        self.tipo_combo = QComboBox()
        self.tipo_combo.setFixedWidth(120)
        self.tipo_combo.addItems(["Todos", "Ingreso", "Egreso"])
        
        # Botón de búsqueda mejorado
        self.libro_buscar_btn = QPushButton("Buscar")
        self.libro_buscar_btn.setStyleSheet(BUTTON_STYLE)
        self.libro_buscar_btn.setMinimumWidth(120)
        self.libro_buscar_btn.clicked.connect(self.on_buscar_libro)
        
        filtros_layout.addWidget(desde_label)
        filtros_layout.addWidget(self.libro_desde_date)
        filtros_layout.addSpacing(10)
        filtros_layout.addWidget(hasta_label)
        filtros_layout.addWidget(self.libro_hasta_date)
        filtros_layout.addSpacing(10)
        filtros_layout.addWidget(tipo_label)
        filtros_layout.addWidget(self.tipo_combo)
        filtros_layout.addStretch()
        filtros_layout.addWidget(self.libro_buscar_btn)
        
        layout.addWidget(filtros_card)
        
        # Card para la tabla
        tabla_card = QGroupBox("Libro Diario")
        tabla_card.setStyleSheet(GROUP_BOX_STYLE)
        tabla_layout = QVBoxLayout(tabla_card)
        
        # Tabla mejorada
        self.libro_table = QTableWidget()
        self.libro_table.setColumnCount(10)
        self.libro_table.setHorizontalHeaderLabels([
            "ID", "Fecha", "Cuenta", "Detalle", "Nº Comprobante", 
            "Ingreso", "Egreso", "Saldo", "Usuario", "Descripción"
        ])
        self.libro_table.setStyleSheet(TABLE_STYLE)
        self.libro_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.libro_table.setAlternatingRowColors(True)
        self.libro_table.setItemDelegate(MoneyDelegate())
        
        # Configurar el ancho de las columnas
        self.libro_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.libro_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Fecha
        self.libro_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Cuenta
        self.libro_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Detalle
        self.libro_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Ingreso
        self.libro_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Egreso
        self.libro_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Saldo
        self.libro_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Usuario
        
        tabla_layout.addWidget(self.libro_table)
        
        layout.addWidget(tabla_card)
        
        # Card para los totales
        totales_card = QGroupBox("Resumen del Período")
        totales_card.setStyleSheet(GROUP_BOX_STYLE)
        totales_layout = QHBoxLayout(totales_card)
        
        # Totales mejorados
        self.libro_total_ingresos_label = QLabel("Total Ingresos: $0.00")
        self.libro_total_ingresos_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {AppColors.SECONDARY};")
        
        self.libro_total_egresos_label = QLabel("Total Egresos: $0.00")
        self.libro_total_egresos_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {AppColors.DANGER};")
        
        self.libro_balance_label = QLabel("Balance: $0.00")
        self.libro_balance_label.setStyleSheet(f"font-size: 18px; font-weight: bold;")
        
        totales_layout.addWidget(self.libro_total_ingresos_label)
        totales_layout.addStretch()
        totales_layout.addWidget(self.libro_total_egresos_label)
        totales_layout.addStretch()
        totales_layout.addWidget(self.libro_balance_label)
        
        layout.addWidget(totales_card)
        
        # Botón de exportar mejorado
        self.libro_exportar_btn = QPushButton("Exportar a Excel")
        self.libro_exportar_btn.setStyleSheet(f"""
            {BUTTON_STYLE}
            background-color: {AppColors.SECONDARY};
        """)
        self.libro_exportar_btn.setMinimumWidth(200)
        self.libro_exportar_btn.clicked.connect(self.on_exportar_libro)
        
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        export_layout.addWidget(self.libro_exportar_btn)
        export_layout.addStretch()
        
        layout.addLayout(export_layout)
    
    def connect_signals(self):
        self.sidebar.navigation_requested.connect(self.navigation_requested)
    
    def refresh_data(self):
        """Carga los datos iniciales"""
        self.on_generar_ingresos_egresos()
        self.on_buscar_libro()
    
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
                    
                    # Configurar datos para gráficos con mejor estilo
                    meses = [item.get('nombre_mes', '') for item in datos]
                    ingresos = [item.get('ingresos', 0) for item in datos]
                    egresos = [item.get('egresos', 0) for item in datos]
                    balances = [item.get('balance', 0) for item in datos]
                    
                    # Crear gráfico de barras para ingresos/egresos con mejor estilo
                    x = range(len(meses))
                    width = 0.35
                    
                    # Colores más atractivos
                    ingreso_color = AppColors.SECONDARY
                    egreso_color = AppColors.DANGER
                    
                    # Configurar fondo y estilo
                    self.ie_canvas.fig.patch.set_facecolor('#FFFFFF')
                    self.ie_canvas.axes.set_facecolor('#F8F9FA')
                    
                    # Crear barras
                    self.ie_canvas.axes.bar([i - width/2 for i in x], ingresos, width, label='Ingresos', color=ingreso_color, alpha=0.8)
                    self.ie_canvas.axes.bar([i + width/2 for i in x], egresos, width, label='Egresos', color=egreso_color, alpha=0.8)
                    
                    # Líneas de cuadrícula suaves
                    self.ie_canvas.axes.grid(True, linestyle='--', alpha=0.3)
                    
                    # Etiquetas y títulos
                    self.ie_canvas.axes.set_xlabel('Mes', fontweight='bold')
                    self.ie_canvas.axes.set_ylabel('Monto ($)', fontweight='bold')
                    self.ie_canvas.axes.set_title(f'Ingresos y Egresos Mensuales - {anio}', fontsize=14, fontweight='bold')
                    self.ie_canvas.axes.set_xticks(x)
                    self.ie_canvas.axes.set_xticklabels(meses, rotation=45, ha='right')
                    self.ie_canvas.axes.legend(frameon=True, fancybox=True, shadow=True)
                    
                    # Ajustar diseño
                    self.ie_canvas.fig.tight_layout()
                    self.ie_canvas.draw()
                    
                    # Crear gráfico de barras para balance mensual con mejor estilo
                    # Configurar fondo y estilo
                    self.balance_ie_canvas.fig.patch.set_facecolor('#FFFFFF')
                    self.balance_ie_canvas.axes.set_facecolor('#F8F9FA')
                    
                    # Crear barras con colores condicionales
                    bars = self.balance_ie_canvas.axes.bar(x, balances, color=[
                        AppColors.SECONDARY if bal >= 0 else AppColors.DANGER for bal in balances
                    ], alpha=0.8)
                    
                    # Añadir valores sobre las barras
                    for bar in bars:
                        height = bar.get_height()
                        y_pos = height + 0.05 * max(abs(min(balances)), max(balances)) if height >= 0 else height - 0.1 * max(abs(min(balances)), max(balances))
                        self.balance_ie_canvas.axes.text(bar.get_x() + bar.get_width()/2., y_pos,
                                f'${abs(height):,.0f}',
                                ha='center', va='bottom' if height >= 0 else 'top', rotation=0,
                                color='black', fontsize=8)
                    
                    # Líneas de cuadrícula suaves
                    self.balance_ie_canvas.axes.grid(True, linestyle='--', alpha=0.3)
                    
                    # Etiquetas y títulos
                    self.balance_ie_canvas.axes.set_xlabel('Mes', fontweight='bold')
                    self.balance_ie_canvas.axes.set_ylabel('Balance ($)', fontweight='bold')
                    self.balance_ie_canvas.axes.set_title(f'Balance Mensual - {anio}', fontsize=14, fontweight='bold')
                    self.balance_ie_canvas.axes.set_xticks(x)
                    self.balance_ie_canvas.axes.set_xticklabels(meses, rotation=45, ha='right')
                    
                    # Ajustar diseño
                    self.balance_ie_canvas.fig.tight_layout()
                    self.balance_ie_canvas.draw()
                    
                    # Llenar tabla con datos
                    total_ingresos = 0
                    total_egresos = 0
                    
                    for row, item in enumerate(datos):
                        self.ie_table.insertRow(row)
                        
                        # Mes
                        self.ie_table.setItem(row, 0, QTableWidgetItem(item.get('nombre_mes', '')))
                        
                        # Ingresos
                        ingreso = item.get('ingresos', 0)
                        ingreso_item = QTableWidgetItem(f"${ingreso:,.2f}")
                        ingreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        if ingreso > 0:
                            ingreso_item.setForeground(QColor(AppColors.SECONDARY))
                        self.ie_table.setItem(row, 1, ingreso_item)
                        
                        # Egresos
                        egreso = item.get('egresos', 0)
                        egreso_item = QTableWidgetItem(f"${egreso:,.2f}")
                        egreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        if egreso > 0:
                            egreso_item.setForeground(QColor(AppColors.DANGER))
                        self.ie_table.setItem(row, 2, egreso_item)
                        
                        # Balance
                        balance = item.get('balance', 0)
                        balance_item = QTableWidgetItem(f"${balance:,.2f}")
                        balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        if balance >= 0:
                            balance_item.setForeground(QColor(AppColors.SECONDARY))
                        else:
                            balance_item.setForeground(QColor(AppColors.DANGER))
                        self.ie_table.setItem(row, 3, balance_item)
                        
                        # Acumular totales
                        total_ingresos += ingreso
                        total_egresos += egreso
                    
                    # Ajustar columnas
                    self.ie_table.resizeColumnsToContents()
                    
                    # Actualizar totales
                    self.ie_total_ingresos_label.setText(f"Total Ingresos: ${total_ingresos:,.2f}")
                    self.ie_total_egresos_label.setText(f"Total Egresos: ${total_egresos:,.2f}")
                    
                    balance_total = total_ingresos - total_egresos
                    balance_color = AppColors.SECONDARY if balance_total >= 0 else AppColors.DANGER
                    self.ie_balance_total_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {balance_color};")
                    self.ie_balance_total_label.setText(f"Balance Total: ${balance_total:,.2f}")
                    
                    # LÍNEA ELIMINADA: self.descargar_reporte_ingresos_egresos()
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
            
            # Verificar si el directorio existe, y si no, crear uno alternativo
            if not os.path.exists(descargas_path):
                # Intentar crear el directorio
                try:
                    os.makedirs(descargas_path)
                    print(f"Directorio creado: {descargas_path}")
                except Exception as e:
                    print(f"No se pudo crear el directorio de descargas: {str(e)}")
                    # Usar un directorio alternativo (el directorio actual)
                    descargas_path = os.getcwd()
                    print(f"Usando directorio alternativo: {descargas_path}")
            
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
            
            # Crear un escritor de Excel con formato
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Ingresos y Egresos', index=False)
            
            # Obtener el libro y la hoja de trabajo
            workbook = writer.book
            worksheet = writer.sheets['Ingresos y Egresos']
            
            # Definir formatos para las celdas
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D9EAD3',
                'border': 1
            })
            
            money_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1
            })
            
            # Aplicar formatos
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                column_len = max(df[value].astype(str).str.len().max(), len(value) + 2)
                worksheet.set_column(col_num, col_num, column_len)
            
            # Aplicar formato monetario a las columnas de montos
            for col_num, column in enumerate(df.columns):
                if "Ingresos" in column or "Egresos" in column or "Balance" in column:
                    # Aplicar formato monetario a la columna
                    for row_num in range(1, len(df) + 1):
                        cell_value = df.iloc[row_num-1][column]
                        if isinstance(cell_value, str) and '$' in cell_value:
                            # Convertir de string a número para formato
                            numeric_value = float(cell_value.replace('$', '').replace(',', ''))
                            worksheet.write(row_num, col_num, numeric_value, money_format)
            
            # Guardar el archivo
            writer.close()
            
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
            anio = self.anio_combo.currentData()
            default_name = f"Ingresos_Egresos_{anio}.xlsx"
            
            # Obtener directorio existente
            descargas_path = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(descargas_path):
                descargas_path = os.getcwd()
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Excel", os.path.join(descargas_path, default_name), 
                "Excel Files (*.xlsx);;All Files (*)", options=options
            )
            
            if file_path:
                # Asegurar que tiene extensión .xlsx
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                
                # Verificar si el directorio destino existe
                destino_path = os.path.dirname(file_path)
                if not os.path.exists(destino_path):
                    try:
                        os.makedirs(destino_path)
                    except Exception as e:
                        # Si no se puede crear, volver al directorio de trabajo
                        nuevo_path = os.path.join(os.getcwd(), os.path.basename(file_path))
                        QMessageBox.warning(self, "Advertencia", 
                            f"No se puede guardar en la ruta especificada. Se guardará en: {nuevo_path}")
                        file_path = nuevo_path
                
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
                
                # Crear un escritor de Excel con formato
                writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
                df.to_excel(writer, sheet_name='Ingresos y Egresos', index=False)
                
                # Obtener el libro y la hoja de trabajo
                workbook = writer.book
                worksheet = writer.sheets['Ingresos y Egresos']
                
                # Definir formatos para las celdas
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D9EAD3',
                    'border': 1
                })
                
                money_format = workbook.add_format({
                    'num_format': '$#,##0.00',
                    'border': 1
                })
                
                # Aplicar formatos
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    column_len = max(df[value].astype(str).str.len().max(), len(value) + 2)
                    worksheet.set_column(col_num, col_num, column_len)
                
                # Aplicar formato monetario a las columnas de montos
                for col_num, column in enumerate(df.columns):
                    if "Ingresos" in column or "Egresos" in column or "Balance" in column:
                        # Aplicar formato monetario a la columna
                        for row_num in range(1, len(df) + 1):
                            cell_value = df.iloc[row_num-1][column]
                            if isinstance(cell_value, str) and '$' in cell_value:
                                # Convertir de string a número para formato
                                numeric_value = float(cell_value.replace('$', '').replace(',', ''))
                                worksheet.write(row_num, col_num, numeric_value, money_format)
                
                # Guardar el archivo
                writer.close()
                
                QMessageBox.information(self, "Éxito", f"Datos exportados exitosamente a {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")

    
    # Métodos para Libro Diario
    def on_buscar_libro(self):
        """Busca partidas para el libro diario ordenadas por ID"""
        try:
            desde = self.libro_desde_date.date().toString("yyyy-MM-dd")
            hasta = self.libro_hasta_date.date().toString("yyyy-MM-dd")
            tipo = self.tipo_combo.currentText().lower()

            QMessageBox.information(self, "Procesando", "Obteniendo datos del libro diario, espere un momento...")

            params = {
                "skip": 0,
                "limit": 1000,
                "fecha_desde": desde,
                "fecha_hasta": hasta
            }
            if tipo != "todos":
                params["tipo"] = tipo

            headers = session.get_headers()
            response = requests.get(f"{session.api_url}/partidas", headers=headers, params=params)

            if response.status_code == 200:
                partidas = response.json()

                for partida in partidas:
                    partida['id_numeric'] = int(partida.get('id', 0))
                partidas = sorted(partidas, key=lambda x: (x.get('fecha', ''), x.get('id_numeric', 0)), reverse=True)

                self.libro_table.setRowCount(0)
                self.libro_table.setColumnCount(10)
                self.libro_table.setHorizontalHeaderLabels([
                    "ID", "Fecha", "Cuenta", "Detalle", "Nº Comprobante",
                    "Ingreso", "Egreso", "Saldo", "Usuario", "Descripción"
                ])

                total_ingresos = 0
                total_egresos = 0

                for row, partida in enumerate(partidas):
                    self.libro_table.insertRow(row)

                    id_item = QTableWidgetItem(str(partida.get('id', '')))
                    id_item.setTextAlignment(Qt.AlignCenter)
                    self.libro_table.setItem(row, 0, id_item)

                    fecha = datetime.strptime(partida.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if partida.get('fecha') else ''
                    fecha_item = QTableWidgetItem(fecha)
                    fecha_item.setTextAlignment(Qt.AlignCenter)
                    self.libro_table.setItem(row, 1, fecha_item)

                    cuenta = "INGRESO" if partida.get('ingreso', 0) > 0 else "EGRESO"
                    cuenta_item = QTableWidgetItem(cuenta)
                    cuenta_item.setTextAlignment(Qt.AlignCenter)
                    self.libro_table.setItem(row, 2, cuenta_item)

                    # Detalle (ya viene con nombre del usuario desde backend)
                    self.libro_table.setItem(row, 3, QTableWidgetItem(partida.get('detalle', '')))

                    # Nº Comprobante
                    if partida.get('recibo_factura'):
                        nro_comprobante = partida.get('recibo_factura')
                    else:
                        if partida.get('tipo') == 'anulacion':
                            nro_comprobante = f"ANUL-{partida.get('id')}"
                        elif partida.get('egreso', 0) > 0:
                            nro_comprobante = f"O.P-{partida.get('id')}"
                        elif partida.get('cuenta') == "INGRESOS" and "cuota" in partida.get("detalle", "").lower():
                            nro_comprobante = f"C.S-{partida.get('id')}"
                        else:
                            nro_comprobante = f"REC-{partida.get('id')}"
                    comprobante_item = QTableWidgetItem(nro_comprobante)
                    comprobante_item.setTextAlignment(Qt.AlignCenter)
                    self.libro_table.setItem(row, 4, comprobante_item)

                    ingreso = partida.get('ingreso', 0)
                    ingreso_item = QTableWidgetItem(f"${ingreso:,.2f}")
                    ingreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.libro_table.setItem(row, 5, ingreso_item)

                    egreso = partida.get('egreso', 0)
                    egreso_item = QTableWidgetItem(f"${egreso:,.2f}")
                    egreso_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.libro_table.setItem(row, 6, egreso_item)

                    saldo = partida.get('saldo', 0)
                    saldo_item = QTableWidgetItem(f"${saldo:,.2f}")
                    saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.libro_table.setItem(row, 7, saldo_item)

                    usuario = partida.get('usuario', {}).get('nombre', '') if partida.get('usuario') else partida.get('usuario_auditoria', '')
                    self.libro_table.setItem(row, 8, QTableWidgetItem(usuario))

                    # Descripción
                    descripcion = partida.get('descripcion', '')
                    descripcion_item = QTableWidgetItem(descripcion)
                    descripcion_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.libro_table.setItem(row, 9, descripcion_item)

                    total_ingresos += ingreso
                    total_egresos += egreso

                self.libro_table.resizeColumnsToContents()
                self.libro_total_ingresos_label.setText(f"Total Ingresos: ${total_ingresos:,.2f}")
                self.libro_total_egresos_label.setText(f"Total Egresos: ${total_egresos:,.2f}")
                balance = total_ingresos - total_egresos
                color = "#388E3C" if balance >= 0 else "#D32F2F"
                self.libro_balance_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
                self.libro_balance_label.setText(f"Balance: ${balance:,.2f}")

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
            
            # Verificar si el directorio existe, y si no, crear uno alternativo
            if not os.path.exists(descargas_path):
                # Intentar crear el directorio
                try:
                    os.makedirs(descargas_path)
                    print(f"Directorio creado: {descargas_path}")
                except Exception as e:
                    print(f"No se pudo crear el directorio de descargas: {str(e)}")
                    # Usar un directorio alternativo (el directorio actual)
                    descargas_path = os.getcwd()
                    print(f"Usando directorio alternativo: {descargas_path}")
            
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
            
            
            try:
            
                df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
                # Ordenar por ID de forma descendente (de mayor a menor)
                df = df.sort_values(by='ID', ascending=False)
                print("Datos ordenados por ID correctamente")
            except Exception as e:
                print(f"Error al ordenar por ID: {str(e)}")
                # Si hay error en ordenamiento, continuar sin ordenar
            
            # Crear un escritor de Excel con formato
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Libro Diario', index=False)
            
            # Obtener el libro y la hoja de trabajo
            workbook = writer.book
            worksheet = writer.sheets['Libro Diario']
            
            # Definir formatos para las celdas
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D9EAD3',
                'border': 1
            })
            
            money_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1
            })
            
            date_format = workbook.add_format({
                'num_format': 'dd/mm/yyyy',
                'border': 1
            })
            
            # Aplicar formatos
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                column_len = max(df[value].astype(str).str.len().max(), len(value) + 2)
                worksheet.set_column(col_num, col_num, column_len)
            
            # Aplicar formato monetario a las columnas de montos
            for col_num, column in enumerate(df.columns):
                if "Ingreso" in column or "Egreso" in column or "Saldo" in column:
                    # Aplicar formato monetario a la columna
                    for row_num in range(1, len(df) + 1):
                        cell_value = df.iloc[row_num-1][column]
                        if isinstance(cell_value, str) and '$' in cell_value:
                            # Convertir de string a número para formato
                            numeric_value = float(cell_value.replace('$', '').replace(',', ''))
                            worksheet.write(row_num, col_num, numeric_value, money_format)
            
            # Guardar el archivo
            writer.close()
            
            QMessageBox.information(self, "Éxito", f"Reporte descargado exitosamente en {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al descargar reporte: {str(e)}")

        
    # También modificar la función on_exportar_libro() para ordenar por ID

    def on_exportar_libro(self):
        """Exporta el libro diario a Excel (permite seleccionar ubicación)"""
        try:
            # Verificar si hay datos para exportar
            if self.libro_table.rowCount() == 0:
                QMessageBox.warning(self, "Advertencia", "No hay datos para exportar") 
                return
            
            # Seleccionar ruta para guardar
            options = QFileDialog.Options()
            periodo = f"{self.libro_desde_date.date().toString('yyyyMMdd')}-{self.libro_hasta_date.date().toString('yyyyMMdd')}"
            default_name = f"Libro_Diario_{periodo}.xlsx"
            
            # Obtener directorio existente
            descargas_path = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(descargas_path):
                descargas_path = os.getcwd()
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Excel", os.path.join(descargas_path, default_name), 
                "Excel Files (*.xlsx);;All Files (*)", options=options
            )
            
            if file_path:
                # Asegurar que tiene extensión .xlsx
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                    
                # Verificar si el directorio destino existe
                destino_path = os.path.dirname(file_path)
                if not os.path.exists(destino_path):
                    try:
                        os.makedirs(destino_path)
                    except Exception as e:
                        # Si no se puede crear, volver al directorio de trabajo
                        nuevo_path = os.path.join(os.getcwd(), os.path.basename(file_path))
                        QMessageBox.warning(self, "Advertencia", 
                            f"No se puede guardar en la ruta especificada. Se guardará en: {nuevo_path}")
                        file_path = nuevo_path
                
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
                
                # NUEVA SECCIÓN: Ordenar el DataFrame por ID (descendente)
                try:
                    # Convertir columna ID a numérico para ordenamiento correcto
                    df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
                    # Ordenar por ID de forma descendente (de mayor a menor)
                    df = df.sort_values(by='ID', ascending=False)
                    print("Datos ordenados por ID correctamente")
                except Exception as e:
                    print(f"Error al ordenar por ID: {str(e)}")
                    # Si hay error en ordenamiento, continuar sin ordenar
                
                # Crear un escritor de Excel con formato
                writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
                df.to_excel(writer, sheet_name='Libro Diario', index=False)
                
                # Obtener el libro y la hoja de trabajo
                workbook = writer.book
                worksheet = writer.sheets['Libro Diario']
                
                # Definir formatos para las celdas
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D9EAD3',
                    'border': 1
                })
                
                money_format = workbook.add_format({
                    'num_format': '$#,##0.00',
                    'border': 1
                })
                
                # Aplicar formatos
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    column_len = max(df[value].astype(str).str.len().max(), len(value) + 2)
                    worksheet.set_column(col_num, col_num, column_len)
                
                # Aplicar formato monetario a las columnas de montos
                for col_num, column in enumerate(df.columns):
                    if "Ingreso" in column or "Egreso" in column or "Saldo" in column:
                        # Aplicar formato monetario a la columna
                        for row_num in range(1, len(df) + 1):
                            cell_value = df.iloc[row_num-1][column]
                            if isinstance(cell_value, str) and '$' in cell_value:
                                # Convertir de string a número para formato
                                numeric_value = float(cell_value.replace('$', '').replace(',', ''))
                                worksheet.write(row_num, col_num, numeric_value, money_format)
                
                # Guardar el archivo
                writer.close()
                
                QMessageBox.information(self, "Éxito", f"Datos exportados exitosamente a {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")