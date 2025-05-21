import os
import sys
from datetime import datetime
import pandas as pd
import requests
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QFrame, QTabWidget, QSpacerItem, QSizePolicy,QDialog,
    QFormLayout, QLineEdit, QDateEdit, QComboBox, QMessageBox, QDoubleSpinBox,
    QApplication ,QRadioButton, QButtonGroup
)
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap
from PySide6.QtCore import Qt, Signal, QDate

from views.dashboard import SidebarWidget
from sesion import session

class CobranzasView(QWidget):
    navigation_requested = Signal(str)  # Señal para solicitar navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals() 
        self.usuarios = []
        self.retenciones = []
        # No llamamos a refresh_data() aquí para evitar problemas de autenticación
    
    def showEvent(self, event):
        """Se ejecuta cuando el widget se hace visible"""
        super().showEvent(event)
        # Cargar datos cuando el widget se hace visible
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
        title_label = QLabel("Gestión de Cobranzas")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        self.content_layout.addWidget(title_label)
        
        # Tabs para las diferentes secciones
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background-color: #fff;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #fff;
                border-bottom: 1px solid #fff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Tab 1: Registrar Cobranza
        self.tab_registrar = QWidget()
        self.setup_tab_registrar()
        self.tabs.addTab(self.tab_registrar, "Registrar Cobranza")
        
        # Tab 2: Listar Cobranzas
        self.tab_listar = QWidget()
        self.setup_tab_listar()
        self.tabs.addTab(self.tab_listar, "Listar Cobranzas")
        
        # Tab 3: Buscar Cobranza
        self.tab_buscar = QWidget()
        self.setup_tab_buscar()
        self.tabs.addTab(self.tab_buscar, "Buscar Cobranza")
        
        self.content_layout.addWidget(self.tabs)
        
        # Agregar al layout principal
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_widget)
    
    def setup_tab_registrar(self):
            layout = QVBoxLayout(self.tab_registrar)
            
            # Formulario para registrar cobranza
            form_layout = QFormLayout()
            form_layout.setSpacing(15)  # Aumentado el espaciado para mejor legibilidad
            form_layout.setContentsMargins(25, 25, 25, 25)  # Aumentado los márgenes
            
            # Estilos mejorados para etiquetas
            label_style = """
                font-weight: 600; 
                color: #2c3e50;
                font-size: 14px;
                padding: 4px 0;
                font-family: 'Segoe UI', Arial, sans-serif;
            """
            
            # Estilos mejorados para widgets de entrada (sin box-shadow)
            input_style = """
                QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox {
                    padding: 10px;
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    background-color: #f9f9f9;
                    font-size: 13px;
                    min-height: 24px;
                }
                QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                    border: 1px solid #3498db;
                    background-color: #fff;
                }
            """
            
            # Selector de tipo de documento
            tipo_documento_label = QLabel("Tipo de Documento:")
            tipo_documento_label.setStyleSheet(label_style)
            
            # Contenedor para los radio buttons
            tipo_doc_container = QWidget()
            tipo_doc_layout = QHBoxLayout(tipo_doc_container)
            tipo_doc_layout.setContentsMargins(0, 0, 0, 0)
            tipo_doc_layout.setSpacing(25)  # Más espacio entre botones
            
            # Radio buttons para tipo de documento
            self.rb_recibo = QRadioButton("Recibo")
            self.rb_factura = QRadioButton("Factura/Recibo")
            self.rb_recibo.setChecked(True)  # Por defecto, recibo
            
            # Agrupar los radio buttons
            self.tipo_doc_group = QButtonGroup()
            self.tipo_doc_group.addButton(self.rb_recibo, 1)
            self.tipo_doc_group.addButton(self.rb_factura, 2)
            
            # Conectar el evento de cambio a la función existente
            # Primero definimos la función que actualiza el texto del botón
            def on_tipo_documento_changed(button):
                # Mostrar u ocultar campos según la selección
                is_factura = button == self.rb_factura
                
                self.factura_label.setVisible(is_factura)
                self.factura_edit.setVisible(is_factura)
                self.razon_social_label.setVisible(is_factura)
                self.razon_social_edit.setVisible(is_factura)
                
                # Cambiar el texto del botón según el tipo seleccionado
                if is_factura:
                    self.registrar_btn.setText("Registrar Factura")
                else:
                    self.registrar_btn.setText("Registrar Cobranza")
            
            # Definimos on_tipo_documento_changed como un método de esta clase
            self.on_tipo_documento_changed = on_tipo_documento_changed
            
            # Conectamos el botón al método que acabamos de definir
            self.tipo_doc_group.buttonClicked.connect(self.on_tipo_documento_changed)
            
            # Estilo mejorado para los radio buttons (sin propiedades no soportadas)
            radio_style = """
                QRadioButton {
                    font-size: 14px;
                    color: #2c3e50;
                    font-weight: 500;
                    padding: 5px;
                }
                QRadioButton::indicator {
                    width: 20px;
                    height: 20px;
                }
            """
            self.rb_recibo.setStyleSheet(radio_style)
            self.rb_factura.setStyleSheet(radio_style)
            
            tipo_doc_layout.addWidget(self.rb_recibo)
            tipo_doc_layout.addWidget(self.rb_factura)
            tipo_doc_layout.addStretch()
            
            form_layout.addRow(tipo_documento_label, tipo_doc_container)
            
            # Selección de árbitro
            arbitro_label = QLabel("Pagador/Cobrador:")
            arbitro_label.setStyleSheet(label_style)
            self.arbitro_combo_registrar = QComboBox()
            self.arbitro_combo_registrar.setPlaceholderText("Seleccione un árbitro")
            self.arbitro_combo_registrar.setStyleSheet(input_style)
            form_layout.addRow(arbitro_label, self.arbitro_combo_registrar)
            
            # Fecha
            fecha_label = QLabel("Fecha:")
            fecha_label.setStyleSheet(label_style)
            self.fecha_edit = QDateEdit()
            self.fecha_edit.setDate(QDate.currentDate())
            self.fecha_edit.setCalendarPopup(True)
            self.fecha_edit.setStyleSheet(input_style)
            form_layout.addRow(fecha_label, self.fecha_edit)
            
            # Número de Factura/Recibo (oculto por defecto)
            self.factura_label = QLabel("Número de Factura/Recibo:")
            self.factura_label.setStyleSheet(label_style)
            self.factura_edit = QLineEdit()
            self.factura_edit.setPlaceholderText("Ingrese número de factura...")
            self.factura_edit.setStyleSheet(input_style)
            form_layout.addRow(self.factura_label, self.factura_edit)
            
            # Razón Social (oculto por defecto)
            self.razon_social_label = QLabel("Razón Social:")
            self.razon_social_label.setStyleSheet(label_style)
            self.razon_social_edit = QLineEdit()
            self.razon_social_edit.setPlaceholderText("Ingrese razón social...")
            self.razon_social_edit.setStyleSheet(input_style)
            form_layout.addRow(self.razon_social_label, self.razon_social_edit)
            
            # Tipo de Retención
            retencion_label = QLabel("Tipo de Retención:")
            retencion_label.setStyleSheet(label_style)
            self.retencion_combo = QComboBox()
            self.retencion_combo.setPlaceholderText("Seleccione una retención")
            self.retencion_combo.currentIndexChanged.connect(self.on_retencion_changed)
            self.retencion_combo.setStyleSheet(input_style)
            form_layout.addRow(retencion_label, self.retencion_combo)
            
            # Monto
            monto_label = QLabel("Monto:")
            monto_label.setStyleSheet(label_style)
            self.monto_spin = QDoubleSpinBox()
            self.monto_spin.setRange(0, 999999.99)
            self.monto_spin.setSingleStep(100)
            self.monto_spin.setPrefix("$ ")
            self.monto_spin.setDecimals(2)
            self.monto_spin.setStyleSheet(input_style)
            form_layout.addRow(monto_label, self.monto_spin)
            
            # Descripción/Notas
            notas_label = QLabel("Descripción/Notas:")
            notas_label.setStyleSheet(label_style)
            self.notas_edit = QLineEdit()
            self.notas_edit.setPlaceholderText("Ingrese detalles adicionales...")
            self.notas_edit.setStyleSheet(input_style)
            form_layout.addRow(notas_label, self.notas_edit)
            
            # Botón de registro mejorado
            self.registrar_btn = QPushButton("Registrar Cobranza")
            self.registrar_btn.clicked.connect(self.on_registrar_cobranza)
            button_style = """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 5px;
                    padding: 12px 25px;
                    min-width: 180px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1c6ea4;
                }
            """
            self.registrar_btn.setStyleSheet(button_style)
            
            layout.addLayout(form_layout)
            
            # Centrar botón y espacio adicional
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(self.registrar_btn)
            button_layout.addStretch()
            
            layout.addSpacing(15)  # Espacio antes del botón
            layout.addLayout(button_layout)
            layout.addStretch()
            
            # Inicializar estado de campos de factura (ocultos al inicio)
            self.factura_label.setVisible(False)
            self.factura_edit.setVisible(False)
            self.razon_social_label.setVisible(False)
            self.razon_social_edit.setVisible(False)
            
    def setup_tab_listar(self):
        layout = QVBoxLayout(self.tab_listar)
        
        # Filtros
        filtros_layout = QHBoxLayout()
        filtros_layout.setContentsMargins(10, 10, 10, 10)
        filtros_layout.setSpacing(10)
        
        # Estilos para los widgets
        label_style = "font-weight: bold; color: #2c3e50;"
        input_style = """
            QDateEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QDateEdit:focus {
                border: 1px solid #4e73df;
                background-color: #fff;
            }
        """
        button_style = """
            QPushButton {
                background-color: #4e73df;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #2e59d9;
            }
            QPushButton:pressed {
                background-color: #1c45bc;
            }
        """
        
        # Desde
        desde_label = QLabel("Desde:")
        desde_label.setStyleSheet(label_style)
        self.desde_date = QDateEdit()
        self.desde_date.setDate(QDate.currentDate().addDays(-30))  # Último mes por defecto
        self.desde_date.setCalendarPopup(True)
        self.desde_date.setStyleSheet(input_style)
        
        # Hasta
        hasta_label = QLabel("Hasta:")
        hasta_label.setStyleSheet(label_style)
        self.hasta_date = QDateEdit()
        self.hasta_date.setDate(QDate.currentDate())
        self.hasta_date.setCalendarPopup(True)
        self.hasta_date.setStyleSheet(input_style)
        
        # Botón de búsqueda
        self.buscar_btn = QPushButton("Buscar")
        self.buscar_btn.clicked.connect(self.on_buscar_cobranzas)
        self.buscar_btn.setStyleSheet(button_style)
        
        filtros_layout.addWidget(desde_label)
        filtros_layout.addWidget(self.desde_date)
        filtros_layout.addWidget(hasta_label)
        filtros_layout.addWidget(self.hasta_date)
        filtros_layout.addWidget(self.buscar_btn)
        
        layout.addLayout(filtros_layout)
        
        # Tabla de cobranzas
        self.cobranzas_table = QTableWidget()
        self.cobranzas_table.setColumnCount(7)  # 7 columnas
        self.cobranzas_table.setHorizontalHeaderLabels(["ID", "Fecha", "Árbitro", "Retención", "Tipo de Retención", "Monto", "Descripción"])
        self.cobranzas_table.horizontalHeader().setStretchLastSection(True)
        self.cobranzas_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cobranzas_table.setAlternatingRowColors(True)
        self.cobranzas_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fff;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #4e73df;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #bdd7fa;
                color: #000;
            }
        """)
        
        # Configurar scroll
        self.cobranzas_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.cobranzas_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        layout.addWidget(self.cobranzas_table)
        
        # Label para total
        self.total_label = QLabel("Total de cobranzas: $0.00")
        self.total_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px; padding: 10px;")
        self.total_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.total_label)
    
    def setup_tab_buscar(self):
        layout = QVBoxLayout(self.tab_buscar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Estilos
        label_style = "font-weight: bold; color: black;"
        input_style = """
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: ;
                min-width: 250px;
            }
            QComboBox:focus {
                border: 1px solid #4e73df;
                background-color: #fff;
            }
            /* Estilos para eliminar el hover */
            QComboBox QAbstractItemView {
                border: 1px solid #ddd;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: transparent;
                color: black;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4e73df;
                color: black;
            }
        """

        button_style = """
            QPushButton {
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """

        search_button_style = button_style + """
            background-color: #4e73df;
            color: black;
        """

        edit_button_style = button_style + """
            background-color: #f6c23e;
            color: white;
        """

        delete_button_style = button_style + """
            background-color: #e74a3b;
            color: white;
        """
        
        # Campo de búsqueda
        busqueda_layout = QHBoxLayout()
        busqueda_layout.setContentsMargins(0, 0, 0, 0)
        busqueda_layout.setSpacing(10)
        
        # Etiqueta de búsqueda
        busqueda_label = QLabel("Seleccionar árbitro:")
        busqueda_label.setStyleSheet(label_style)
        
        # Combo para seleccionar árbitro
        self.arbitro_combo_buscar = QComboBox()
        self.arbitro_combo_buscar.setStyleSheet(input_style)
        self.arbitro_combo_buscar.setPlaceholderText("Seleccione un árbitro")
        
        # Botón de búsqueda
        self.search_btn = QPushButton("Buscar")
        self.search_btn.setIcon(QIcon.fromTheme("search"))
        self.search_btn.clicked.connect(self.on_buscar_cobranza)
        self.search_btn.setStyleSheet(search_button_style)
        
        # Botones de Editar y Eliminar
        self.edit_btn = QPushButton("Editar")
        self.edit_btn.clicked.connect(self.on_editar_cobranza)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet(edit_button_style)
        
        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.clicked.connect(self.on_eliminar_cobranza)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet(delete_button_style)
        
        # Agregar widgets al layout
        busqueda_layout.addWidget(busqueda_label)
        busqueda_layout.addWidget(self.arbitro_combo_buscar)
        busqueda_layout.addWidget(self.search_btn)
        busqueda_layout.addWidget(self.edit_btn)
        busqueda_layout.addWidget(self.delete_btn)
        
        layout.addLayout(busqueda_layout)
        
        # Añadir tabla para mostrar todas las cobranzas del usuario
        self.cobranzas_usuario_table = QTableWidget()
        self.cobranzas_usuario_table.setColumnCount(6)
        self.cobranzas_usuario_table.setHorizontalHeaderLabels(["ID", "Fecha", "Retención", "Monto", "Descripción", "Acciones"])
        self.cobranzas_usuario_table.horizontalHeader().setStretchLastSection(True)
        self.cobranzas_usuario_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cobranzas_usuario_table.setAlternatingRowColors(True)
        self.cobranzas_usuario_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fff;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #4e73df;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #bdd7fa;
                color: #000;
            }
        """)
        self.cobranzas_usuario_table.itemClicked.connect(self.on_cobranza_selected)
        
        layout.addWidget(self.cobranzas_usuario_table)
        
        # Título de resultados
        self.resultado_title = QLabel("Detalles de la Cobranza")
        resultado_font = QFont()
        resultado_font.setPointSize(16)
        resultado_font.setBold(True)
        self.resultado_title.setFont(resultado_font)
        self.resultado_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        self.resultado_title.setVisible(False)
        layout.addWidget(self.resultado_title)
        
        # Contenedor para resultados
        self.resultado_container = QWidget()
        self.resultado_container.setStyleSheet("""
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        """)
        self.resultado_layout = QVBoxLayout(self.resultado_container)
        self.resultado_layout.setContentsMargins(15, 15, 15, 15)
        self.resultado_layout.setSpacing(10)
        
        # Línea separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #dee2e6;")
        self.resultado_layout.addWidget(separator)
        
        # Detalles en dos columnas
        detalles_layout = QHBoxLayout()
        detalles_layout.setContentsMargins(0, 10, 0, 0)
        detalles_layout.setSpacing(30)
        
        # Columna 1
        col1_layout = QVBoxLayout()
        col1_layout.setSpacing(15)
        self.id_label = QLabel()
        self.fecha_label = QLabel()
        self.monto_label = QLabel()
        
        # Aplicar estilos a los labels
        detail_style = "font-size: 14px; margin-bottom: 5px;"
        self.id_label.setStyleSheet(detail_style)
        self.fecha_label.setStyleSheet(detail_style)
        self.monto_label.setStyleSheet(detail_style)
        
        col1_layout.addWidget(self.id_label)
        col1_layout.addWidget(self.fecha_label)
        col1_layout.addWidget(self.monto_label)
        col1_layout.addStretch()
        
        # Columna 2
        col2_layout = QVBoxLayout()
        col2_layout.setSpacing(15)
        self.arbitro_label = QLabel()
        self.retencion_label = QLabel()
        self.descripcion_label = QLabel()
        
        # Aplicar estilos
        self.arbitro_label.setStyleSheet(detail_style)
        self.retencion_label.setStyleSheet(detail_style)
        self.descripcion_label.setStyleSheet(detail_style)
        self.descripcion_label.setWordWrap(True)
        
        col2_layout.addWidget(self.arbitro_label)
        col2_layout.addWidget(self.retencion_label)
        col2_layout.addWidget(self.descripcion_label)
        col2_layout.addStretch()
        
        detalles_layout.addLayout(col1_layout)
        detalles_layout.addLayout(col2_layout)
        
        self.resultado_layout.addLayout(detalles_layout)
        
        layout.addWidget(self.resultado_container)
        self.resultado_container.setVisible(False)
        
        # Agregar un espaciador para empujar todo hacia arriba
        layout.addStretch()
    
    def connect_signals(self):
        self.sidebar.navigation_requested.connect(self.navigation_requested)
    
    def refresh_data(self):
        """Carga los datos iniciales"""
        try:
            self.cargar_usuarios()
            self.cargar_retenciones()
            self.on_buscar_cobranzas()
        except Exception as e:
            print(f"Error en refresh_data: {str(e)}")

    def cargar_usuarios(self):
        """Carga la lista de usuarios desde la API y los ordena alfabéticamente"""
        try:
            headers = session.get_headers()
            url = f"{session.api_url}/usuarios"
            print(f"Realizando petición GET a: {url}")
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Obtener usuarios de la API
                self.usuarios = response.json()
                print(f"Usuarios cargados: {len(self.usuarios)}")
                
                # Ordenar usuarios alfabéticamente por nombre
                self.usuarios.sort(key=lambda x: x['nombre'].lower())
                
                # Actualizar AMBOS combo box de árbitros
                # 1. Combo de la pestaña "Registrar Cobranza"
                self.arbitro_combo_registrar.clear()
                # 2. Combo de la pestaña "Buscar Cobranza"
                self.arbitro_combo_buscar.clear()
                
                for usuario in self.usuarios:
                    # Agregar al combo de registrar
                    self.arbitro_combo_registrar.addItem(f"{usuario['nombre']}", usuario['id'])
                    # Agregar al combo de buscar
                    self.arbitro_combo_buscar.addItem(f"{usuario['nombre']}", usuario['id'])
                
                print("Combos de árbitros actualizados correctamente (ordenados alfabéticamente)")
            elif response.status_code == 401:
                print("Error de autenticación al cargar usuarios")
            else:
                print(f"Error al cargar usuarios: {response.text}")
        except Exception as e:
            print(f"Excepción al cargar usuarios: {str(e)}")
        
    def cargar_retenciones(self):
        """Carga la lista de retenciones desde la API"""
        try:
            headers = session.get_headers()
            url = f"{session.api_url}/retenciones/"  # Agregamos la barra al final
            print(f"Realizando petición GET a: {url}")
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                self.retenciones = response.json()
                print(f"Retenciones cargadas: {len(self.retenciones)}")
                
                # Actualizar combo box
                self.retencion_combo.clear()
                for retencion in self.retenciones:
                    self.retencion_combo.addItem(
                        f"{retencion['nombre']} (${retencion['monto']})", 
                        retencion['id']
                    )
            else:
                print(f"Error al cargar retenciones: {response.text}")
        except Exception as e:
            print(f"Excepción al cargar retenciones: {str(e)}")
    
    def on_retencion_changed(self, index):
        """Actualiza el monto basado en la retención seleccionada"""
        if index >= 0 and index < len(self.retenciones):
            retencion_id = self.retencion_combo.itemData(index)
            retencion = next((r for r in self.retenciones if r['id'] == retencion_id), None)
            if retencion:
                self.monto_spin.setValue(retencion['monto'])
                
    def on_registrar_cobranza(self):
        """Maneja el evento de clic en Registrar Cobranza"""
        # Validar campos
        if self.arbitro_combo_registrar.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Por favor seleccione un árbitro")
            return
        
        if self.monto_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "El monto debe ser mayor a cero")
            return
        
        # Determinar tipo de documento seleccionado
        tipo_documento = "recibo"
        if self.rb_factura.isChecked():
            tipo_documento = "factura"
            # Validar campos adicionales para facturas
            if not self.factura_edit.text().strip():
                QMessageBox.warning(self, "Error", "Por favor ingrese el número de factura")
                return
            if not self.razon_social_edit.text().strip():
                QMessageBox.warning(self, "Error", "Por favor ingrese la razón social")
                return
        
        # Obtener datos
        usuario_id = self.arbitro_combo_registrar.currentData()
        fecha = self.fecha_edit.date().toString("yyyy-MM-dd")
        numero_factura = self.factura_edit.text().strip() if self.rb_factura.isChecked() else ""
        razon_social = self.razon_social_edit.text().strip() if self.rb_factura.isChecked() else ""
        monto = self.monto_spin.value()
        notas = self.notas_edit.text().strip()
        
        # Crear objeto de cobranza
        cobranza_data = {
            "usuario_id": usuario_id,
            "fecha": fecha,
            "monto": monto,
            "tipo_documento": tipo_documento
        }
        
        # Agregar campos adicionales para facturas
        if tipo_documento == "factura":
            cobranza_data["numero_factura"] = numero_factura
            cobranza_data["razon_social"] = razon_social
        
        # Solo agregar retencion_id si se ha seleccionado una retención
        if self.retencion_combo.currentIndex() >= 0:
            retencion_id = self.retencion_combo.currentData()
            cobranza_data["retencion_id"] = retencion_id
        
        # Agregar notas si no está vacío
        if notas:
            cobranza_data["descripcion"] = notas
        
        try:
            # Enviar solicitud para crear cobranza
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            url = f"{session.api_url}/cobranzas"
            print(f"Realizando petición POST a: {url}")
            print(f"Datos: {json.dumps(cobranza_data)}")
            
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(cobranza_data)
            )
            
            if response.status_code == 200 or response.status_code == 201:
                cobranza_respuesta = response.json()
                
                # Verificar el tipo de documento
                if tipo_documento == "recibo":
                    # Para RECIBOS: verificar si se envió el recibo por email
                    if cobranza_respuesta.get("email_enviado", False):
                        QMessageBox.information(
                            self, 
                            "Éxito", 
                            f"Cobranza registrada exitosamente.\nRecibo enviado por email a {cobranza_respuesta.get('email_destinatario')}"
                        )
                    else:
                        # Si no se envió el recibo, dar la opción de enviarlo manualmente
                        arbitro_id = self.arbitro_combo_registrar.currentData()
                        arbitro_nombre = self.arbitro_combo_registrar.currentText()
                        arbitro_email = None
                        
                        # Buscar el email del árbitro
                        for usuario in self.usuarios:
                            if usuario.get('id') == arbitro_id:
                                arbitro_email = usuario.get('email')
                                break
                        
                        if arbitro_email:
                            respuesta = QMessageBox.question(
                                self,
                                "Enviar Recibo",
                                f"¿Desea enviar el recibo al email de {arbitro_nombre} ({arbitro_email})?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes
                            )
                            
                            if respuesta == QMessageBox.Yes:
                                self.enviar_recibo_manualmente(cobranza_respuesta.get("id"), arbitro_email)
                        else:
                            QMessageBox.information(
                                self, 
                                "Éxito", 
                                "Cobranza registrada exitosamente.\nNo se pudo enviar el recibo por email porque el árbitro no tiene email registrado."
                            )
                else:
                    # Para FACTURAS: solo informar que se registró, sin mencionar emails
                    QMessageBox.information(
                        self, 
                        "Éxito", 
                        "Factura registrada exitosamente."
                    )
                
                # Limpiar formulario
                self.arbitro_combo_registrar.setCurrentIndex(-1)
                self.fecha_edit.setDate(QDate.currentDate())
                self.rb_recibo.setChecked(True)  # Restablecer a recibo
                self.factura_edit.clear()
                self.razon_social_edit.clear()
                self.factura_label.setVisible(False)
                self.factura_edit.setVisible(False)
                self.razon_social_label.setVisible(False)
                self.razon_social_edit.setVisible(False)
                self.retencion_combo.setCurrentIndex(-1)
                self.monto_spin.setValue(0)
                self.notas_edit.clear()
                
                # Actualizar lista de cobranzas
                self.on_buscar_cobranzas()
            else:
                error_msg = "Error al registrar la cobranza"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                print(f"Error al registrar cobranza: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar cobranza: {str(e)}")
    
    def on_buscar_cobranzas(self):
        """Busca cobranzas según los filtros seleccionados"""
        try:
            # Preparar parámetros
            desde = self.desde_date.date().toString("yyyy-MM-dd")
            hasta = self.hasta_date.date().toString("yyyy-MM-dd")
            
            params = {
                "skip": 0,
                "limit": 100
            }
            
            # Obtener cobranzas
            headers = session.get_headers()
            url = f"{session.api_url}/cobranzas"
            print(f"Realizando petición GET a: {url}")
            print(f"Parámetros: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                # La respuesta puede ser directamente una lista o un diccionario con una lista
                data = response.json()
                cobranzas_data = []
                
                # Verificar el tipo de datos recibidos
                if isinstance(data, list):
                    # La respuesta ya es una lista de cobranzas
                    cobranzas_data = data
                elif isinstance(data, dict):
                    # La respuesta es un diccionario
                    if "data" in data:
                        cobranzas_data = data["data"]
                    elif "cobranzas" in data:
                        cobranzas_data = data["cobranzas"]
                
                if not isinstance(cobranzas_data, list):
                    raise ValueError("No se pudo obtener una lista de cobranzas de la respuesta")

                print(f"Cobranzas cargadas: {len(cobranzas_data)}")

                # Filtrar por fecha (si la API no lo hace)
                cobranzas_filtradas = [
                    cobranza for cobranza in cobranzas_data
                    if desde <= cobranza.get("fecha", "") <= hasta
                ]

                # Limpiar tabla
                self.cobranzas_table.setRowCount(0)

                # Llenar tabla con datos
                total_cobranzas = 0
                for row, cobranza in enumerate(cobranzas_filtradas):
                    self.cobranzas_table.insertRow(row)

                    # ID
                    id_item = QTableWidgetItem(str(cobranza.get("id", "")))
                    id_item.setTextAlignment(Qt.AlignCenter)
                    self.cobranzas_table.setItem(row, 0, id_item)

                    # Fecha
                    fecha = datetime.strptime(cobranza.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if cobranza.get('fecha') else ''
                    fecha_item = QTableWidgetItem(fecha)
                    fecha_item.setTextAlignment(Qt.AlignCenter)
                    self.cobranzas_table.setItem(row, 1, fecha_item)

                    # Árbitro - Intentar diferentes estructuras de datos
                    arbitro = ""
                    # Método 1: usuario es un objeto con propiedad nombre
                    if isinstance(cobranza.get("usuario"), dict) and "nombre" in cobranza.get("usuario", {}):
                        arbitro = cobranza.get("usuario", {}).get("nombre", "")
                    # Método 2: usuario_nombre como campo directo
                    elif "usuario_nombre" in cobranza:
                        arbitro = cobranza.get("usuario_nombre", "")
                    # Método 3: nombre_usuario como campo directo
                    elif "nombre_usuario" in cobranza:
                        arbitro = cobranza.get("nombre_usuario", "")
                    # Método 4: tenemos usuario_id pero necesitamos buscar el nombre
                    elif "usuario_id" in cobranza and self.usuarios:
                        usuario_id = cobranza.get("usuario_id")
                        for usuario in self.usuarios:
                            if usuario.get("id") == usuario_id:
                                arbitro = usuario.get("nombre", "")
                                break
                    
                    self.cobranzas_table.setItem(row, 2, QTableWidgetItem(arbitro))
                    
                    # Tipo de documento
                    tipo_doc = "Recibo"
                    if cobranza.get("tipo_documento") == "factura":
                        tipo_doc = "Factura/Recibo"
                    self.cobranzas_table.setItem(row, 3, QTableWidgetItem(tipo_doc))
                    
                    # Número de Factura
                    numero_factura = cobranza.get("numero_factura", "")
                    self.cobranzas_table.setItem(row, 4, QTableWidgetItem(numero_factura))
                    
                    # Razón Social
                    razon_social = cobranza.get("razon_social", "")
                    self.cobranzas_table.setItem(row, 5, QTableWidgetItem(razon_social))
                    
                    # Retención
                    retencion_data = cobranza.get("retencion") or {}
                    retencion = retencion_data.get("nombre", "")
                    self.cobranzas_table.setItem(row, 6, QTableWidgetItem(retencion))
                    
                    # Tipo de Retención
                    tipo_retencion = retencion_data.get("tipo", "")  # Obtener el tipo de retención
                    self.cobranzas_table.setItem(row, 7, QTableWidgetItem(tipo_retencion))
                    
                    # Monto
                    monto = cobranza.get("monto", 0)
                    monto_item = QTableWidgetItem(f"${monto:,.2f}")
                    monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.cobranzas_table.setItem(row, 8, monto_item)
                    
                    # Descripción
                    descripcion = cobranza.get("descripcion", "")
                    self.cobranzas_table.setItem(row, 9, QTableWidgetItem(descripcion))
                    
                    # Acumular total
                    total_cobranzas += monto
                
                # Actualizar total
                self.total_label.setText(f"Total de cobranzas: ${total_cobranzas:,.2f}")
                
                # Ajustar columnas
                self.cobranzas_table.resizeColumnsToContents()
            elif response.status_code == 401:
                print("Error de autenticación al cargar cobranzas")
                # No mostrar mensaje aquí para no ser intrusivo
            else:
                print(f"Error al cargar cobranzas: {response.text}")
        except Exception as e:
            print(f"Excepción al buscar cobranzas: {str(e)}")
    
    def on_buscar_cobranza(self):
        """Busca todas las cobranzas para el usuario seleccionado y las muestra en una tabla"""
        # Verificar si se ha seleccionado un árbitro
        if self.arbitro_combo_buscar.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Por favor seleccione un árbitro")
            return
        
        try:
            # Mostrar indicador de carga
            self.resultado_title.setText("Buscando...")
            self.resultado_title.setVisible(True)
            QApplication.processEvents()  # Actualizar la interfaz
            
            # Obtener ID del usuario seleccionado
            usuario_id = self.arbitro_combo_buscar.currentData()
            usuario_nombre = self.arbitro_combo_buscar.currentText()
            
            print(f"Buscando cobranzas para: {usuario_nombre} (ID: {usuario_id})")
            
            headers = session.get_headers()
            
            # Buscar todas las cobranzas
            all_url = f"{session.api_url}/cobranzas"
            all_response = requests.get(all_url, headers=headers)
            
            if all_response.status_code == 200:
                todas_cobranzas = all_response.json()
                
                # Filtrar cobranzas para este usuario
                cobranzas_usuario = []
                
                if isinstance(todas_cobranzas, list):
                    for cobranza in todas_cobranzas:
                        # Verificar diferentes formas de identificar al usuario
                        if cobranza.get("usuario_id") == usuario_id:
                            cobranzas_usuario.append(cobranza)
                        elif isinstance(cobranza.get("usuario"), dict) and cobranza.get("usuario", {}).get("id") == usuario_id:
                            cobranzas_usuario.append(cobranza)
                        # También verificar por nombre (menos preciso pero útil como respaldo)
                        elif isinstance(cobranza.get("usuario"), dict) and usuario_nombre.lower() in cobranza.get("usuario", {}).get("nombre", "").lower():
                            cobranzas_usuario.append(cobranza)
                
                if not cobranzas_usuario:
                    # Intento alternativo: buscar directamente por usuario_id
                    url = f"{session.api_url}/cobranzas"
                    params = {"usuario_id": usuario_id}
                    
                    response = requests.get(url, headers=headers, params=params)
                    print(f"URL: {url}, Parámetros: {params}, Código de respuesta: {response.status_code}")
                    
                    if response.status_code == 200:
                        cobranzas = response.json()
                        
                        # Si nos devuelve una lista, usar todos los elementos
                        if isinstance(cobranzas, list) and len(cobranzas) > 0:
                            cobranzas_usuario = cobranzas
                
                if not cobranzas_usuario:
                    QMessageBox.information(self, "No encontrado", 
                        f"No se encontraron cobranzas para el árbitro: {usuario_nombre}")
                    self.resultado_title.setVisible(False)
                    self.resultado_container.setVisible(False)
                    self.cobranzas_usuario_table.setRowCount(0)
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
                    return
                
                # Limpiar la tabla existente
                self.cobranzas_usuario_table.setRowCount(0)
                
                # Llenar la tabla con los resultados
                for row, cobranza in enumerate(cobranzas_usuario):
                    self.cobranzas_usuario_table.insertRow(row)
                    
                    # ID
                    id_item = QTableWidgetItem(str(cobranza.get("id", "")))
                    id_item.setTextAlignment(Qt.AlignCenter)
                    self.cobranzas_usuario_table.setItem(row, 0, id_item)
                    
                    # Fecha
                    fecha_str = cobranza.get('fecha', '')
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha_str else 'No disponible'
                    fecha_item = QTableWidgetItem(fecha)
                    fecha_item.setTextAlignment(Qt.AlignCenter)
                    self.cobranzas_usuario_table.setItem(row, 1, fecha_item)
                    
                    # Retención
                    retencion = "No disponible"
                    if isinstance(cobranza.get('retencion'), dict):
                        retencion = cobranza.get('retencion', {}).get('nombre', 'No disponible')
                    self.cobranzas_usuario_table.setItem(row, 2, QTableWidgetItem(retencion))
                    
                    # Monto
                    monto = cobranza.get("monto", 0)
                    monto_item = QTableWidgetItem(f"${monto:,.2f}")
                    monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.cobranzas_usuario_table.setItem(row, 3, monto_item)
                    
                    # Descripción
                    descripcion = cobranza.get("descripcion", "")
                    if not descripcion:
                        descripcion = "Sin descripción"
                    self.cobranzas_usuario_table.setItem(row, 4, QTableWidgetItem(descripcion))
                    
                    # Botón de detalles en la última columna
                    ver_btn = QPushButton("Ver")
                    ver_btn.setStyleSheet("""
                        background-color: #4e73df;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 5px 10px;
                    """)
                    # Conectar el botón con la función que muestra los detalles
                    cobranza_id = cobranza.get("id")
                    ver_btn.clicked.connect(lambda checked=False, c_id=cobranza_id: self.cargar_detalles_cobranza(c_id))
                    self.cobranzas_usuario_table.setCellWidget(row, 5, ver_btn)
                    
                # Ajustar el tamaño de las columnas
                self.cobranzas_usuario_table.resizeColumnsToContents()
                
                # Mostrar un mensaje de éxito con la cantidad de cobranzas encontradas
                self.resultado_title.setText(f"Cobranzas para: {usuario_nombre} ({len(cobranzas_usuario)})")
                self.resultado_title.setStyleSheet("color: #2c3e50; font-weight: bold;")
                self.resultado_title.setVisible(True)
                
                # Ocultar el panel de detalles hasta que se seleccione una cobranza
                self.resultado_container.setVisible(False)
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron cargar las cobranzas. Código: {all_response.status_code}")
        except Exception as e:
            # Mostrar error y ocultar elementos
            print(f"Error en la búsqueda: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al buscar: {str(e)}")
            self.resultado_title.setVisible(False)
            self.resultado_container.setVisible(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)


    def on_cobranza_selected(self, item):
        """Maneja el evento de clic en una fila de la tabla"""
        # Obtener la fila seleccionada
        row = item.row()
        
        # Obtener el ID de la cobranza en la primera columna
        cobranza_id = self.cobranzas_usuario_table.item(row, 0).text()
        
        # Cargar los detalles de esta cobranza
        self.cargar_detalles_cobranza(cobranza_id)

    def cargar_detalles_cobranza(self, cobranza_id):
        """Carga los detalles de una cobranza específica por su ID"""
        try:
            # Obtener los detalles de la cobranza seleccionada
            headers = session.get_headers()
            url = f"{session.api_url}/cobranzas/{cobranza_id}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                self.cobranza_actual = response.json()
                
                # Mostrar los detalles de la cobranza
                self.mostrar_detalles_cobranza()
                
                # Aplicar estilos muy destacados a los botones
                self.edit_btn.setStyleSheet("""
                    background-color: #FF9500;
                    color: white;
                    font-weight: bold;
                    border: 2px solid #E68200;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 14px;
                    min-width: 100px;
                    min-height: 40px;
                """)
                
                self.delete_btn.setStyleSheet("""
                    background-color: #FF3B30;
                    color: white;
                    font-weight: bold;
                    border: 2px solid #D81E06;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 14px;
                    min-width: 100px;
                    min-height: 40px;
                """)
                
                # IMPORTANTE: Asegurarse que los botones sean visibles y habilitados
                self.edit_btn.setVisible(True)
                self.edit_btn.setEnabled(True)
                self.delete_btn.setVisible(True)
                self.delete_btn.setEnabled(True)
                
                # Asegurarse de que los botones están en el layout principal y visibles
                # Si los botones están en el busqueda_layout, asegurarse de que están visibles
                for i in range(self.tab_buscar.layout().count()):
                    item = self.tab_buscar.layout().itemAt(i)
                    if item and item.widget() == self.edit_btn.parentWidget():
                        item.widget().setVisible(True)
                
                # Forzar actualización de la interfaz
                QApplication.processEvents()
                
                print("Botones habilitados y visibles con colores llamativos")
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron cargar los detalles. Código: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar detalles: {str(e)}")


    def mostrar_detalles_cobranza(self):
        """Muestra los detalles de la cobranza actual en el panel de detalles"""
        # Verificar que tenemos una cobranza seleccionada
        if not hasattr(self, 'cobranza_actual'):
            return
        
        # Actualizar el título
        self.resultado_title.setText("Detalles de la Cobranza")
        self.resultado_title.setStyleSheet("color: #2c3e50; font-weight: bold;")
        self.resultado_title.setVisible(True)
        self.resultado_container.setVisible(True)
        
        # Formatear fecha
        fecha_str = self.cobranza_actual.get('fecha', '')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha_str else 'No disponible'
        
        # Obtener información del árbitro
        arbitro_nombre = "No disponible"
        if isinstance(self.cobranza_actual.get('usuario'), dict):
            usuario_obj = self.cobranza_actual.get('usuario', {})
            if 'nombre' in usuario_obj:
                arbitro_nombre = usuario_obj.get('nombre', 'No disponible')
        
        # Obtener información de retención
        retencion_nombre = "No disponible"
        retencion = self.cobranza_actual.get('retencion', {})
        if isinstance(retencion, dict):
            retencion_nombre = retencion.get('nombre', 'No disponible')
        
        # Obtener tipo de documento, número de factura y razón social
        tipo_doc = "Recibo"
        if self.cobranza_actual.get('tipo_documento') == 'factura':
            tipo_doc = "Factura/Recibo"
        
        numero_factura = self.cobranza_actual.get('numero_factura', 'No disponible')
        razon_social = self.cobranza_actual.get('razon_social', 'No disponible')
        
        # Obtener monto
        monto = self.cobranza_actual.get('monto', 0)
        
        # Obtener descripción
        descripcion = self.cobranza_actual.get('descripcion', '')
        if not descripcion:
            descripcion = "Sin descripción"
        
        # Aplicar estilos
        estilo_titulo = "font-weight: bold; color: #2c3e50;"
        estilo_valor = "color: #3498db;"
        
        # Mostrar la información con estilos
        self.id_label.setText(f"<span style='{estilo_titulo}'>ID de la Cobranza:</span> <span style='{estilo_valor}'>{self.cobranza_actual.get('id')}</span>")
        self.fecha_label.setText(f"<span style='{estilo_titulo}'>Fecha:</span> <span style='{estilo_valor}'>{fecha}</span>")
        self.factura_label.setText(f"<span style='{estilo_titulo}'>Número de Factura:</span> <span style='{estilo_valor}'>{numero_factura}</span>")
        self.monto_label.setText(f"<span style='{estilo_titulo}'>Monto:</span> <span style='{estilo_valor}'>${monto:,.2f}</span>")
        self.arbitro_label.setText(f"<span style='{estilo_titulo}'>Árbitro:</span> <span style='{estilo_valor}'>{arbitro_nombre}</span>")
        self.razon_social_label.setText(f"<span style='{estilo_titulo}'>Razón Social:</span> <span style='{estilo_valor}'>{razon_social}</span>")
        self.retencion_label.setText(f"<span style='{estilo_titulo}'>Retención:</span> <span style='{estilo_valor}'>{retencion_nombre}</span>")
        self.descripcion_label.setText(f"<span style='{estilo_titulo}'>Descripción:</span> <span style='{estilo_valor}'>{descripcion}</span>")
        
        # Ajustar visibilidad de campos según tipo de documento
        is_factura = self.cobranza_actual.get('tipo_documento') == 'factura'
        self.factura_label.setVisible(is_factura)
        self.razon_social_label.setVisible(is_factura)

    def on_editar_cobranza(self):
        """Abre un diálogo para editar la cobranza seleccionada"""
        if not hasattr(self, 'cobranza_actual'):
            QMessageBox.warning(self, "Error", "Primero seleccione una cobranza")
            return
        
        try:
            # Obtener datos actualizados directamente de la API
            headers = session.get_headers()
            url = f"{session.api_url}/cobranzas/{self.cobranza_actual['id']}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Actualizar con datos frescos
                self.cobranza_actual = response.json()
        except Exception as e:
            print(f"Error al obtener datos actualizados: {str(e)}")
            
        # Abrir diálogo de edición con los datos actuales
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Cobranza")
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLabel {
                font-weight: bold;
                color: #2c3e50;
            }
            QDateEdit, QDoubleSpinBox, QLineEdit, QRadioButton {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#save {
                background-color: #4e73df;
                color: white;
            }
            QPushButton#save:hover {
                background-color: #2e59d9;
            }
            QPushButton#cancel {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                color: #2c3e50;
            }
            QPushButton#cancel:hover {
                background-color: #e9ecef;
            }
        """)
        layout = QFormLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Tipo de documento
        tipo_doc_label = QLabel("Tipo de Documento:")
        tipo_doc_container = QWidget()
        tipo_doc_layout = QHBoxLayout(tipo_doc_container)
        tipo_doc_layout.setContentsMargins(0, 0, 0, 0)
        
        rb_recibo = QRadioButton("Recibo")
        rb_factura = QRadioButton("Factura/Recibo")
        
        # Establecer selección según el valor actual
        es_factura = self.cobranza_actual.get('tipo_documento') == 'factura'
        rb_factura.setChecked(es_factura)
        rb_recibo.setChecked(not es_factura)
        
        tipo_doc_group = QButtonGroup()
        tipo_doc_group.addButton(rb_recibo)
        tipo_doc_group.addButton(rb_factura)
        
        tipo_doc_layout.addWidget(rb_recibo)
        tipo_doc_layout.addWidget(rb_factura)
        tipo_doc_layout.addStretch()
        
        layout.addRow(tipo_doc_label, tipo_doc_container)
        
        # Campos editables
        fecha_edit = QDateEdit()
        fecha_edit.setDate(QDate.fromString(self.cobranza_actual['fecha'], "yyyy-MM-dd"))
        fecha_edit.setCalendarPopup(True)
        
        # Campos para número de factura y razón social
        factura_edit = QLineEdit()
        factura_edit.setText(self.cobranza_actual.get('numero_factura', ''))
        
        razon_social_edit = QLineEdit()
        razon_social_edit.setText(self.cobranza_actual.get('razon_social', ''))
        
        # Mostrar/ocultar campos según tipo de documento
        factura_label = QLabel("Número de Factura:")
        razon_social_label = QLabel("Razón Social:")
        
        factura_label.setVisible(es_factura)
        factura_edit.setVisible(es_factura)
        razon_social_label.setVisible(es_factura)
        razon_social_edit.setVisible(es_factura)
    
    # Función para mostrar/ocultar campos al cambiar tipo de documento
        def on_tipo_cambio():
            es_factura_nueva = rb_factura.isChecked()
            factura_label.setVisible(es_factura_nueva)
            factura_edit.setVisible(es_factura_nueva)
            razon_social_label.setVisible(es_factura_nueva)
            razon_social_edit.setVisible(es_factura_nueva)
        
        # Conectar evento
        rb_recibo.toggled.connect(on_tipo_cambio)
        rb_factura.toggled.connect(on_tipo_cambio)
        
        # Campos para el resto de información
        monto_spin = QDoubleSpinBox()
        monto_spin.setRange(0, 999999.99)
        monto_spin.setValue(float(self.cobranza_actual.get('monto', 0)))
        monto_spin.setPrefix("$ ")
        monto_spin.setDecimals(2)
        
        descripcion_edit = QLineEdit()
        descripcion_edit.setText(self.cobranza_actual.get('descripcion', ''))
        
        # Añadir campos al layout
        layout.addRow("Fecha:", fecha_edit)
        layout.addRow(factura_label, factura_edit)
        layout.addRow(razon_social_label, razon_social_edit)
        layout.addRow("Monto:", monto_spin)
        layout.addRow("Descripción:", descripcion_edit)
        
        # Botones
        btn_layout = QHBoxLayout()
        guardar_btn = QPushButton("Guardar")
        guardar_btn.setObjectName("save")
        cancelar_btn = QPushButton("Cancelar")
        cancelar_btn.setObjectName("cancel")
        
        btn_layout.addWidget(cancelar_btn)
        btn_layout.addWidget(guardar_btn)
        
        layout.addRow("", btn_layout)
        
        # Determinar tipo de documento para guardarlo
        def tipo_documento_seleccionado():
            if rb_factura.isChecked():
                return "factura"
            return "recibo"
        
        # Conectar botones a acciones
        guardar_btn.clicked.connect(lambda: self.guardar_edicion_cobranza(
            dialog, 
            self.cobranza_actual['id'], 
            fecha_edit.date().toString("yyyy-MM-dd"),
            tipo_documento_seleccionado(),
            factura_edit.text() if rb_factura.isChecked() else "",
            razon_social_edit.text() if rb_factura.isChecked() else "",
            monto_spin.value(),
            descripcion_edit.text()
        ))
        cancelar_btn.clicked.connect(dialog.reject)
        
        # Ajustar tamaño y mostrar diálogo
        dialog.setMinimumWidth(400)
        dialog.exec()
        # Conectar evento


    def guardar_edicion_cobranza(self, dialog, cobranza_id, fecha, tipo_documento, numero_factura, razon_social, monto, descripcion):
        """Guarda los cambios de la cobranza editada"""
        try:
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            url = f"{session.api_url}/cobranzas/{cobranza_id}"
            
            datos_actualizacion = {
                "fecha": fecha,
                "monto": monto,
                "descripcion": descripcion,
                "tipo_documento": tipo_documento
            }
            
            # Agregar campos adicionales para facturas
            if tipo_documento == "factura":
                if not numero_factura:
                    QMessageBox.warning(self, "Error", "Por favor ingrese el número de factura")
                    return False
                if not razon_social:
                    QMessageBox.warning(self, "Error", "Por favor ingrese la razón social")
                    return False
                    
                datos_actualizacion["numero_factura"] = numero_factura
                datos_actualizacion["razon_social"] = razon_social
            
            # Mantener el ID de retención actual
            if hasattr(self, 'cobranza_actual') and 'retencion_id' in self.cobranza_actual and self.cobranza_actual['retencion_id'] is not None:
                datos_actualizacion["retencion_id"] = self.cobranza_actual['retencion_id']
            
            # Obtener monto anterior para saber si hubo cambio
            monto_anterior = 0
            if hasattr(self, 'cobranza_actual') and 'monto' in self.cobranza_actual:
                monto_anterior = float(self.cobranza_actual.get('monto', 0))
            
            response = requests.put(url, headers=headers, json=datos_actualizacion)
            
            if response.status_code == 200:
                cobranza_actualizada = response.json()
                QMessageBox.information(self, "Éxito", "Cobranza actualizada correctamente")
                dialog.accept()
                
                # Verificar si cambió el monto para actualizar saldos
                if abs(monto - monto_anterior) > 0.01:
                    # Solicitar recálculo de saldos
                    recalcular_url = f"{session.api_url}/transacciones/recalcular-saldos"
                    recalcular_response = requests.post(recalcular_url, headers=headers)
                    
                    if recalcular_response.status_code == 200:
                        print("Saldos recalculados correctamente")
                    else:
                        print(f"Error al recalcular saldos: {recalcular_response.status_code}")
                
                # Actualizar la tabla de cobranzas y los detalles
                # Volvemos a buscar cobranzas para actualizar la tabla
                usuario_id = self.arbitro_combo_buscar.currentData()
                if usuario_id:
                    self.on_buscar_cobranza()
                    
                    # Después de actualizar la tabla, cargar los detalles de la cobranza editada
                    self.cargar_detalles_cobranza(cobranza_id)
                
                # Emitir señal para que el dashboard se actualice si está visible
                from PySide6.QtCore import QEvent, QCoreApplication
                event = QEvent(QEvent.Type(QEvent.User + 1))  # Evento personalizado
                QCoreApplication.postEvent(self.parent(), event)
                
                return True
            else:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar. Código: {response.status_code}")
                return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar: {str(e)}")
            return False


    def on_eliminar_cobranza(self):
        """Elimina la cobranza seleccionada"""
        if not hasattr(self, 'cobranza_actual'):
            QMessageBox.warning(self, "Error", "Primero seleccione una cobranza")
            return
        
        respuesta = QMessageBox.question(
            self, 
            "Confirmar Eliminación", 
            f"¿Está seguro de eliminar la cobranza #{self.cobranza_actual['id']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            try:
                headers = session.get_headers()
                url = f"{session.api_url}/cobranzas/{self.cobranza_actual['id']}"
                
                # Guardar el ID del usuario y de cobranza antes de eliminarla
                usuario_id = self.arbitro_combo_buscar.currentData()
                cobranza_id = self.cobranza_actual['id']
                
                # Guardar el monto actual para saber cuánto se está eliminando
                monto_eliminado = float(self.cobranza_actual.get('monto', 0))
                
                response = requests.delete(url, headers=headers)
                
                if response.status_code == 200:
                    QMessageBox.information(self, "Éxito", "Cobranza eliminada correctamente")
                    
                    # Primero solicitar recálculo de saldos
                    recalcular_url = f"{session.api_url}/transacciones/recalcular-saldos"
                    recalcular_response = requests.post(recalcular_url, headers=headers)
                    
                    if recalcular_response.status_code == 200:
                        print("Saldos recalculados correctamente después de eliminar")
                    else:
                        print(f"Error al recalcular saldos: {recalcular_response.status_code}")
                    
                    # Ocultar el panel de detalles
                    self.resultado_container.setVisible(False)
                    
                    # Deshabilitar botones
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
                    
                    # Actualizar la tabla de cobranzas para mostrar los cambios
                    if usuario_id:
                        self.on_buscar_cobranza()
                    
                    # Importar aquí para evitar problemas de importación circular
                    from PySide6.QtCore import QTimer, QEvent, QCoreApplication
                    
                    # Función para actualizar después del retraso
                    def actualizar_dashboard_despues_delay():
                        # Emitir señal para que el dashboard se actualice si está visible
                        event = QEvent(QEvent.Type(QEvent.User + 1))  # Evento personalizado
                        QCoreApplication.postEvent(self.parent(), event)
                    
                    # Crear un temporizador de un solo disparo
                    timer = QTimer(self)  # Hacerlo hijo de self para evitar que se elimine
                    timer.setSingleShot(True)
                    timer.timeout.connect(actualizar_dashboard_despues_delay)
                    timer.start(500)  # Esperar 500ms antes de actualizar
                    
                    # Guardar una referencia al timer para evitar que sea eliminado por el GC
                    self._update_timer = timer
                    
                else:
                    QMessageBox.warning(
                        self, 
                        "Error", 
                        f"No se pudo eliminar la cobranza. Código: {response.status_code}"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")
    # Método adicional para inicializar después del login (si lo prefieres usar en lugar de showEvent)
    def initialize_after_login(self):
        """Método para inicializar datos después del login (alternativa a showEvent)"""
        self.refresh_data()