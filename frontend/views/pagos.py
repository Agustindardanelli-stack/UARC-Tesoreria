import os
import sys
from datetime import datetime
import pandas as pd
import requests
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QSplitter, QFrame, QTabWidget, QSpacerItem, QSizePolicy,
    QFormLayout, QLineEdit, QDateEdit, QComboBox, QMessageBox, QSpinBox, QDoubleSpinBox,
    QApplication , QDialog
)
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap
from PySide6.QtCore import Qt, Signal, QDate, QEvent, QCoreApplication

from views.dashboard import SidebarWidget
from sesion import session

class PagosView(QWidget):
    navigation_requested = Signal(str)  # Señal para solicitar navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
        self.usuarios = []
   
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
        title_label = QLabel("Gestión de Pagos")
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
        
        # Tab 1: Registrar Pago
        self.tab_registrar = QWidget()
        self.setup_tab_registrar()
        self.tabs.addTab(self.tab_registrar, "Registrar Pago")
        
        # Tab 2: Listar Pagos
        self.tab_listar = QWidget()
        self.setup_tab_listar()
        self.tabs.addTab(self.tab_listar, "Listar Pagos")
        
        # Tab 3: Buscar Pago
        self.tab_buscar = QWidget()
        self.setup_tab_buscar()
        self.tabs.addTab(self.tab_buscar, "Buscar Pago")
        
        self.content_layout.addWidget(self.tabs)
        
        # Agregar al layout principal
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_widget)
    
    def setup_tab_registrar(self):
        layout = QVBoxLayout(self.tab_registrar)
        
        # Formulario para registrar pago
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # Estilos para etiquetas
        label_style = "font-weight: bold; color: #2c3e50;"
        
        # Estilos para widgets de entrada
        input_style = """
            QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #4e73df;
                background-color: #fff;
            }
        """
        
        # Selección de árbitro
        arbitro_label = QLabel("Pagador/Cobrador:")
        arbitro_label.setStyleSheet(label_style)
        self.arbitro_combo = QComboBox()
        self.arbitro_combo.setPlaceholderText("Seleccione un árbitro")
        self.arbitro_combo.setStyleSheet(input_style)
        form_layout.addRow(arbitro_label, self.arbitro_combo)
        
        # Fecha
        fecha_label = QLabel("Fecha:")
        fecha_label.setStyleSheet(label_style)
        self.fecha_edit = QDateEdit()
        self.fecha_edit.setDate(QDate.currentDate())
        self.fecha_edit.setCalendarPopup(True)
        self.fecha_edit.setStyleSheet(input_style)
        form_layout.addRow(fecha_label, self.fecha_edit)
        
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
        
        # Botón de registro
        self.registrar_btn = QPushButton("Registrar Pago")
        self.registrar_btn.clicked.connect(self.on_registrar_pago)
        self.registrar_btn.setStyleSheet("""
            QPushButton {
                background-color: #4e73df;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #2e59d9;
            }
            QPushButton:pressed {
                background-color: #1c45bc;
            }
        """)
        
        layout.addLayout(form_layout)
        
        # Centrar botón
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.registrar_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()

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
        self.buscar_btn.clicked.connect(self.on_buscar_pagos)
        self.buscar_btn.setStyleSheet(button_style)
        
        filtros_layout.addWidget(desde_label)
        filtros_layout.addWidget(self.desde_date)
        filtros_layout.addWidget(hasta_label)
        filtros_layout.addWidget(self.hasta_date)
        filtros_layout.addWidget(self.buscar_btn)
        
        layout.addLayout(filtros_layout)
        
        # Tabla de pagos
        self.pagos_table = QTableWidget()
        self.pagos_table.setColumnCount(5)  # 5 columnas
        self.pagos_table.setHorizontalHeaderLabels(["ID", "Fecha", "Árbitro", "Monto", "Descripción"])
        self.pagos_table.horizontalHeader().setStretchLastSection(True)
        self.pagos_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.pagos_table.setAlternatingRowColors(True)
        self.pagos_table.setStyleSheet("""
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
        self.pagos_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.pagos_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        layout.addWidget(self.pagos_table)
        
        # Label para total
        self.total_label = QLabel("Total de pagos: $0.00")
        self.total_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px; padding: 10px;")
        self.total_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.total_label)




    def on_buscar_pagos_usuario(self):
        """Busca todos los pagos para el usuario seleccionado y los muestra en una tabla"""
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
            
            print(f"Buscando pagos para: {usuario_nombre} (ID: {usuario_id})")
            
            headers = session.get_headers()
            
            # Buscar todos los pagos
            all_url = f"{session.api_url}/pagos"
            all_response = requests.get(all_url, headers=headers)
            
            if all_response.status_code == 200:
                todos_pagos = all_response.json()
                
                # Filtrar pagos para este usuario
                pagos_usuario = []
                
                if isinstance(todos_pagos, list):
                    for pago in todos_pagos:
                        # Verificar diferentes formas de identificar al usuario
                        if pago.get("usuario_id") == usuario_id:
                            pagos_usuario.append(pago)
                        elif isinstance(pago.get("usuario"), dict) and pago.get("usuario", {}).get("id") == usuario_id:
                            pagos_usuario.append(pago)
                        # También verificar por nombre (menos preciso pero útil como respaldo)
                        elif isinstance(pago.get("usuario"), dict) and usuario_nombre.lower() in pago.get("usuario", {}).get("nombre", "").lower():
                            pagos_usuario.append(pago)
                
                if not pagos_usuario:
                    # Intento alternativo: buscar directamente por usuario_id
                    url = f"{session.api_url}/pagos"
                    params = {"usuario_id": usuario_id}
                    
                    response = requests.get(url, headers=headers, params=params)
                    print(f"URL: {url}, Parámetros: {params}, Código de respuesta: {response.status_code}")
                    
                    if response.status_code == 200:
                        pagos = response.json()
                        
                        # Si nos devuelve una lista, usar todos los elementos
                        if isinstance(pagos, list) and len(pagos) > 0:
                            pagos_usuario = pagos
                
                if not pagos_usuario:
                    QMessageBox.information(self, "No encontrado", 
                        f"No se encontraron pagos para el árbitro: {usuario_nombre}")
                    self.resultado_title.setVisible(False)
                    self.resultado_container.setVisible(False)
                    self.pagos_usuario_table.setRowCount(0)
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
                    return
                
                # Limpiar la tabla existente
                self.pagos_usuario_table.setRowCount(0)
                
                # Llenar la tabla con los resultados
                for row, pago in enumerate(pagos_usuario):
                    self.pagos_usuario_table.insertRow(row)
                    
                    # ID
                    id_item = QTableWidgetItem(str(pago.get("id", "")))
                    id_item.setTextAlignment(Qt.AlignCenter)
                    self.pagos_usuario_table.setItem(row, 0, id_item)
                    
                    # Fecha
                    fecha_str = pago.get('fecha', '')
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha_str else 'No disponible'
                    fecha_item = QTableWidgetItem(fecha)
                    fecha_item.setTextAlignment(Qt.AlignCenter)
                    self.pagos_usuario_table.setItem(row, 1, fecha_item)
                    
                    # Árbitro
                    arbitro = ""
                    if isinstance(pago.get("usuario"), dict) and "nombre" in pago.get("usuario", {}):
                        arbitro = pago.get("usuario", {}).get("nombre", "")
                    elif "usuario_nombre" in pago:
                        arbitro = pago.get("usuario_nombre", "")
                    self.pagos_usuario_table.setItem(row, 2, QTableWidgetItem(arbitro))
                    
                    # Monto
                    monto = pago.get("monto", 0)
                    monto_item = QTableWidgetItem(f"${monto:,.2f}")
                    monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.pagos_usuario_table.setItem(row, 3, monto_item)
                    
                    # Descripción
                    descripcion = pago.get("descripcion", "")
                    if not descripcion:
                        descripcion = "Sin descripción"
                    self.pagos_usuario_table.setItem(row, 4, QTableWidgetItem(descripcion))
                    
                    # Botón de Ver en la última columna
                    ver_btn = QPushButton("Ver")
                    ver_btn.setStyleSheet("""
                        background-color: #4e73df;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 5px 10px;
                    """)
                    # Conectar el botón con la función que muestra los detalles
                    pago_id = pago.get("id")
                    ver_btn.clicked.connect(lambda checked=False, p_id=pago_id: self.cargar_detalles_pago(p_id))
                    self.pagos_usuario_table.setCellWidget(row, 5, ver_btn)
                    
                # Ajustar el tamaño de las columnas
                self.pagos_usuario_table.resizeColumnsToContents()
                
                # Mostrar un mensaje de éxito con la cantidad de pagos encontrados
                self.resultado_title.setText(f"Pagos para: {usuario_nombre} ({len(pagos_usuario)})")
                self.resultado_title.setStyleSheet("color: #2c3e50; font-weight: bold;")
                self.resultado_title.setVisible(True)
                
                # Ocultar el panel de detalles hasta que se seleccione un pago
                self.resultado_container.setVisible(False)
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron cargar los pagos. Código: {all_response.status_code}")
        except Exception as e:
            # Mostrar error y ocultar elementos
            print(f"Error en la búsqueda: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al buscar: {str(e)}")
            self.resultado_title.setVisible(False)
            self.resultado_container.setVisible(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)    
    
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
            color: black;
            font-weight: bold;
            border: 2px solid #E68200;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 14px;
            min-width: 100px;
            min-height: 40px;
        """

        delete_button_style = button_style + """
            background-color: #e74a3b;
            color: black;
            font-weight: bold;
            border: 2px solid #D81E06;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 14px;
            min-width: 100px;
            min-height: 40px;
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
        self.search_btn.clicked.connect(self.on_buscar_pagos_usuario)
        self.search_btn.setStyleSheet(search_button_style)
        
        # Botones de Editar y Eliminar
        self.edit_btn = QPushButton("Editar")
        self.edit_btn.clicked.connect(self.on_editar_pago)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet(edit_button_style)
        
        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.clicked.connect(self.on_eliminar_pago)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet(delete_button_style)
        
        # Agregar widgets al layout
        busqueda_layout.addWidget(busqueda_label)
        busqueda_layout.addWidget(self.arbitro_combo_buscar)
        busqueda_layout.addWidget(self.search_btn)
        
        layout.addLayout(busqueda_layout)
        
        # Añadir tabla para mostrar todos los pagos del usuario
        self.pagos_usuario_table = QTableWidget()
        self.pagos_usuario_table.setColumnCount(6)
        self.pagos_usuario_table.setHorizontalHeaderLabels(["ID", "Fecha", "Árbitro", "Monto", "Descripción", "Acciones"])
        self.pagos_usuario_table.horizontalHeader().setStretchLastSection(True)
        self.pagos_usuario_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.pagos_usuario_table.setAlternatingRowColors(True)
        self.pagos_usuario_table.setStyleSheet("""
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
        self.pagos_usuario_table.itemClicked.connect(self.on_pago_selected)
        
        layout.addWidget(self.pagos_usuario_table)
        
        # Botones de edición/eliminación
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)
        botones_layout.setContentsMargins(0, 15, 0, 15)
        
        botones_layout.addWidget(self.edit_btn)
        botones_layout.addWidget(self.delete_btn)
        botones_layout.addStretch()
        
        layout.addLayout(botones_layout)
        
        # Título de resultados
        self.resultado_title = QLabel("Detalles del Pago")
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
        self.descripcion_label = QLabel()
        
        # Aplicar estilos
        self.arbitro_label.setStyleSheet(detail_style)
        self.descripcion_label.setStyleSheet(detail_style)
        self.descripcion_label.setWordWrap(True)
        
        col2_layout.addWidget(self.arbitro_label)
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
            self.on_buscar_pagos()
        except Exception as e:
            print(f"Error en refresh_data: {str(e)}")
    
    def on_pago_selected(self, item):
        """Maneja el evento de clic en una fila de la tabla"""
        # Obtener la fila seleccionada
        row = item.row()
        
        # Obtener el ID del pago en la primera columna
        pago_id = self.pagos_usuario_table.item(row, 0).text()
        
        # Cargar los detalles de este pago
        self.cargar_detalles_pago(pago_id)

    def cargar_detalles_pago(self, pago_id):
        """Carga los detalles de un pago específico por su ID"""
        try:
            # Obtener los detalles del pago seleccionado
            headers = session.get_headers()
            url = f"{session.api_url}/pagos/{pago_id}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                self.pago_actual = response.json()
                
                # Mostrar los detalles del pago
                self.mostrar_detalles_pago()
                
                # Habilitar botones de editar y eliminar y asegurar que son visibles
                self.edit_btn.setVisible(True)
                self.edit_btn.setEnabled(True)
                self.delete_btn.setVisible(True)
                self.delete_btn.setEnabled(True)
                
                # Forzar actualización de la interfaz
                QApplication.processEvents()
                
                print("Botones habilitados y visibles")
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron cargar los detalles. Código: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar detalles: {str(e)}")


    def mostrar_detalles_pago(self):
        """Muestra los detalles del pago actual en el panel de detalles"""
        # Verificar que tenemos un pago seleccionado
        if not hasattr(self, 'pago_actual'):
            return
        
        # Mostrar el panel de detalles
        self.resultado_title.setText("Detalles del Pago")
        self.resultado_title.setStyleSheet("color: #2c3e50; font-weight: bold;")
        self.resultado_title.setVisible(True)
        self.resultado_container.setVisible(True)
        print(f"fecha_str: {self.pago_actual.get('fecha', '')}")
        print(f"monto: {self.pago_actual.get('monto', 0)}")
        
        # Formatear fecha
        fecha_str = self.pago_actual.get('fecha', '')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha_str else 'No disponible'
        
        # Obtener información del árbitro
        arbitro_nombre = "No disponible"
        if isinstance(self.pago_actual.get('usuario'), dict):
            usuario_obj = self.pago_actual.get('usuario', {})
            if 'nombre' in usuario_obj:
                arbitro_nombre = usuario_obj.get('nombre', 'No disponible')
        
        # Obtener monto
        monto = self.pago_actual.get('monto', 0)
        
        # Obtener descripción
        descripcion = self.pago_actual.get('descripcion', '')
        if not descripcion:
            descripcion = "Sin descripción"
        
        # Aplicar estilos
        estilo_titulo = "font-weight: bold; color: #2c3e50;"
        estilo_valor = "color: #3498db;"
        
        # Mostrar la información con estilos
        self.id_label.setText(f"<span style='{estilo_titulo}'>ID del Pago:</span> <span style='{estilo_valor}'>{self.pago_actual.get('id')}</span>")
        self.fecha_label.setText(f"<span style='{estilo_titulo}'>Fecha:</span> <span style='{estilo_valor}'>{fecha}</span>")
        self.arbitro_label.setText(f"<span style='{estilo_titulo}'>Árbitro:</span> <span style='{estilo_valor}'>{arbitro_nombre}</span>")
        self.monto_label.setText(f"<span style='{estilo_titulo}'>Monto:</span> <span style='{estilo_valor}'>${monto:,.2f}</span>")
        self.descripcion_label.setText(f"<span style='{estilo_titulo}'>Descripción:</span> <span style='{estilo_valor}'>{descripcion}</span>")   

    def cargar_usuarios(self):
        """Carga la lista de usuarios desde la API"""
        try:
            headers = session.get_headers()
            url = f"{session.api_url}/usuarios"  # Sin barra al final
            print(f"Realizando petición GET a: {url}")
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                self.usuarios = response.json()
                print(f"Usuarios cargados: {len(self.usuarios)}")
                
                # Actualizar combo box de registrar pagos
                self.arbitro_combo.clear()
                for usuario in self.usuarios:
                    self.arbitro_combo.addItem(f"{usuario['nombre']}", usuario['id'])
                    
                # Actualizar combo box de buscar pagos
                self.arbitro_combo_buscar.clear()
                for usuario in self.usuarios:
                    self.arbitro_combo_buscar.addItem(f"{usuario['nombre']}", usuario['id'])
            else:
                print(f"Error al cargar usuarios: {response.text}")
        except Exception as e:
            print(f"Excepción al cargar usuarios: {str(e)}")
    
    def on_registrar_pago(self):
        """Maneja el evento de clic en Registrar Pago"""
        # Validar campos
        if self.arbitro_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Por favor seleccione un árbitro")
            return
        
        if self.monto_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "El monto debe ser mayor a cero")
            return
        
        # Obtener datos
        usuario_id = self.arbitro_combo.currentData()
        fecha = self.fecha_edit.date().toString("yyyy-MM-dd")
        monto = self.monto_spin.value()
        notas = self.notas_edit.text().strip()
        
        # Crear objeto de pago
        pago_data = {
            "usuario_id": usuario_id,
            "fecha": fecha,
            "monto": monto
        }
        
        # Agregar notas si no está vacío
        if notas:
            pago_data["descripcion"] = notas
        
        try:
            # Enviar solicitud para crear pago
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            url = f"{session.api_url}/pagos"
            print(f"Realizando petición POST a: {url}")
            print(f"Datos: {json.dumps(pago_data)}")
            
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(pago_data)
            )
            
            if response.status_code == 200 or response.status_code == 201:
                pago_respuesta = response.json()
                
                # Verificar si se envió el recibo por email
                if pago_respuesta.get("email_enviado", False):
                    QMessageBox.information(
                        self, 
                        "Éxito", 
                        f"Pago registrado exitosamente.\nRecibo enviado por email a {pago_respuesta.get('email_destinatario')}"
                    )
                else:
                    # Si no se envió el recibo, dar la opción de enviarlo manualmente
                    arbitro_id = self.arbitro_combo.currentData()
                    arbitro_nombre = self.arbitro_combo.currentText()
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
                            self.enviar_recibo_manualmente(pago_respuesta.get("id"), arbitro_email)
                    else:
                        QMessageBox.information(
                            self, 
                            "Éxito", 
                            "Pago registrado exitosamente.\nNo se pudo enviar el recibo por email porque el árbitro no tiene email registrado."
                        )
                
                # Limpiar formulario
                self.arbitro_combo.setCurrentIndex(-1)
                self.fecha_edit.setDate(QDate.currentDate())
                self.monto_spin.setValue(0)
                self.notas_edit.clear()
                
                # Actualizar lista de pagos
                self.on_buscar_pagos()

                # Emitir señal para que el dashboard se actualice si está visible
                event = QEvent(QEvent.Type(QEvent.User + 1))  # Evento personalizado
                QCoreApplication.postEvent(self.parent(), event)
            else:
                error_msg = "Error al registrar el pago"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                print(f"Error al registrar pago: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar pago: {str(e)}")

    def enviar_recibo_manualmente(self, pago_id, email):
        """Envía un recibo manualmente usando la API"""
        try:
            # Enviar solicitud para reenviar recibo
            headers = session.get_headers()
            
            url = f"{session.api_url}/pagos/{pago_id}/reenviar-orden"
            params = {"email": email}
            
            response = requests.post(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success", False):
                    QMessageBox.information(self, "Éxito", "Recibo enviado exitosamente")
                else:
                    QMessageBox.warning(self, "Advertencia", f"No se pudo enviar el recibo: {result.get('message', '')}")
            else:
                error_msg = "Error al enviar el recibo"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al enviar recibo: {str(e)}")
    
    def on_buscar_pagos(self):
        """Busca pagos según los filtros seleccionados"""
        try:
            # Preparar parámetros
            desde = self.desde_date.date().toString("yyyy-MM-dd")
            hasta = self.hasta_date.date().toString("yyyy-MM-dd")
            
            params = {
                "skip": 0,
                "limit": 100
            }
            
            # Obtener pagos
            headers = session.get_headers()
            url = f"{session.api_url}/pagos"
            print(f"Realizando petición GET a: {url}")
            print(f"Parámetros: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                # La respuesta puede ser directamente una lista o un diccionario con una lista
                data = response.json()
                pagos_data = []
                
                # Verificar el tipo de datos recibidos
                if isinstance(data, list):
                    # La respuesta ya es una lista de pagos
                    pagos_data = data
                elif isinstance(data, dict):
                    # La respuesta es un diccionario
                    if "data" in data:
                        pagos_data = data["data"]
                    elif "pagos" in data:
                        pagos_data = data["pagos"]
                
                if not isinstance(pagos_data, list):
                    raise ValueError("No se pudo obtener una lista de pagos de la respuesta")

                print(f"Pagos cargados: {len(pagos_data)}")

                # Filtrar por fecha (si la API no lo hace)
                pagos_filtrados = [
                    pago for pago in pagos_data
                    if desde <= pago.get("fecha", "") <= hasta
                ]

                # Limpiar tabla
                self.pagos_table.setRowCount(0)

                # Llenar tabla con datos
                total_pagos = 0
                for row, pago in enumerate(pagos_filtrados):
                    self.pagos_table.insertRow(row)

                    # ID
                    id_item = QTableWidgetItem(str(pago.get("id", "")))
                    id_item.setTextAlignment(Qt.AlignCenter)
                    self.pagos_table.setItem(row, 0, id_item)

                    # Fecha
                    fecha = datetime.strptime(pago.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if pago.get('fecha') else ''
                    fecha_item = QTableWidgetItem(fecha)
                    fecha_item.setTextAlignment(Qt.AlignCenter)
                    self.pagos_table.setItem(row, 1, fecha_item)

                    # Árbitro - Intentar diferentes estructuras de datos
                    arbitro = ""
                    # Método 1: usuario es un objeto con propiedad nombre
                    if isinstance(pago.get("usuario"), dict) and "nombre" in pago.get("usuario", {}):
                        arbitro = pago.get("usuario", {}).get("nombre", "")
                    # Método 2: usuario_nombre como campo directo
                    elif "usuario_nombre" in pago:
                        arbitro = pago.get("usuario_nombre", "")
                    # Método 3: nombre_usuario como campo directo
                    elif "nombre_usuario" in pago:
                        arbitro = pago.get("nombre_usuario", "")
                    # Método 4: tenemos usuario_id pero necesitamos buscar el nombre
                    elif "usuario_id" in pago and self.usuarios:
                        usuario_id = pago.get("usuario_id")
                        for usuario in self.usuarios:
                            if usuario.get("id") == usuario_id:
                                arbitro = usuario.get("nombre", "")
                                break
                    
                    self.pagos_table.setItem(row, 2, QTableWidgetItem(arbitro))
                    
                    # Monto
                    monto = pago.get("monto", 0)
                    monto_item = QTableWidgetItem(f"${monto:,.2f}")
                    monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.pagos_table.setItem(row, 3, monto_item)
                    
                    # Descripción
                    descripcion = pago.get("descripcion", "")
                    self.pagos_table.setItem(row, 4, QTableWidgetItem(descripcion))
                    
                    # Acumular total
                    total_pagos += monto
                
                # Actualizar total
                self.total_label.setText(f"Total de pagos: ${total_pagos:,.2f}")
                
                # Ajustar columnas
                self.pagos_table.resizeColumnsToContents()
            else:
                print(f"Error al cargar pagos: {response.text}")
        except Exception as e:
            print(f"Excepción al buscar pagos: {str(e)}")


        
    def on_buscar_pago_id(self):
        """Busca un pago por diferentes criterios"""
        tipo_busqueda = self.tipo_busqueda_combo.currentText()
        termino_busqueda = self.busqueda_input.text().strip()
        
        if not termino_busqueda:
            QMessageBox.warning(self, "Error", "Ingrese un término de búsqueda")
            return
        
        try:
            # Mostrar indicador de carga
            self.resultado_title.setText("Buscando...")
            self.resultado_title.setVisible(True)
            self.resultado_container.setVisible(True)
            QApplication.processEvents()  # Actualizar la interfaz
            
            headers = session.get_headers()
            
            # Construir parámetros de búsqueda según el tipo
            if tipo_busqueda == "Por ID":
                url = f"{session.api_url}/pagos/{termino_busqueda}"
                response = requests.get(url, headers=headers)
            elif tipo_busqueda == "Por Árbitro":
                url = f"{session.api_url}/pagos"
                params = {"usuario_nombre": termino_busqueda}
                response = requests.get(url, headers=headers, params=params)
            elif tipo_busqueda == "Por Descripción":
                url = f"{session.api_url}/pagos"
                params = {"descripcion": termino_busqueda}
                response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                datos = response.json()
                if datos:
                    # Tomar el primer resultado si es una lista
                    self.pago_actual = datos[0] if isinstance(datos, list) else datos
                    
                    # Mostrar detalles
                    self.resultado_title.setText("Detalles del Pago")
                    self.resultado_title.setStyleSheet("color: #2c3e50; font-weight: bold;")
                    self.resultado_title.setVisible(True)
                    self.resultado_container.setVisible(True)
                    
                    # Formatear fecha
                    fecha_str = self.pago_actual.get('fecha', '')
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha_str else 'No disponible'
                    
                    # Obtener nombre del árbitro
                    arbitro_nombre = "No disponible"
                    usuario = self.pago_actual.get("usuario", {})
                    if isinstance(usuario, dict) and "nombre" in usuario:
                        arbitro_nombre = usuario.get("nombre", "No disponible")
                    
                    # Obtener monto
                    monto = self.pago_actual.get('monto', 0)
                    
                    # Obtener descripción
                    descripcion = self.pago_actual.get("descripcion", "")
                    if not descripcion:
                        descripcion = "Sin descripción"
                    
                    # Aplicar estilos a los labels para mejorar la presentación
                    estilo_titulo = "font-weight: bold; color: #2c3e50;"
                    estilo_valor = "color: #3498db;"
                    
                    # Mostrar la información con estilos
                    self.id_label.setText(f"<span style='{estilo_titulo}'>ID del Pago:</span> <span style='{estilo_valor}'>{self.pago_actual.get('id')}</span>")
                    self.fecha_label.setText(f"<span style='{estilo_titulo}'>Fecha:</span> <span style='{estilo_valor}'>{fecha}</span>")
                    self.arbitro_label.setText(f"<span style='{estilo_titulo}'>Árbitro:</span> <span style='{estilo_valor}'>{arbitro_nombre}</span>")
                    self.monto_label.setText(f"<span style='{estilo_titulo}'>Monto:</span> <span style='{estilo_valor}'>${monto:,.2f}</span>")
                    self.descripcion_label.setText(f"<span style='{estilo_titulo}'>Descripción:</span> <span style='{estilo_valor}'>{descripcion}</span>")
                    
                    # Estilizar el contenedor
                    self.resultado_container.setStyleSheet("""
                        background-color: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 5px;
                        padding: 10px;
                    """)
                    
                    # Habilitar botones de editar y eliminar
                    self.edit_btn.setEnabled(True)
                    self.delete_btn.setEnabled(True)
                    
                    # Hacer que los botones sean visibles con estilos destacados
                    self.edit_btn.setStyleSheet("""
                        background-color: #f6c23e;
                        color: white;
                        font-weight: bold;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 15px;
                        min-width: 80px;
                        min-height: 36px;
                    """)
                    
                    self.delete_btn.setStyleSheet("""
                        background-color: #e74a3b;
                        color: white;
                        font-weight: bold;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 15px;
                        min-width: 80px;
                        min-height: 36px;
                    """)
                    
                    # Asegurarse de que los botones están en el layout y son visibles
                    self.edit_btn.show()
                    self.delete_btn.show()
                else:
                    QMessageBox.information(self, "Búsqueda", "No se encontraron resultados")
                    self.resultado_title.setVisible(False)
                    self.resultado_container.setVisible(False)
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
            else:
                QMessageBox.warning(self, "Error", f"Error en la búsqueda. Código: {response.status_code}")
                self.resultado_title.setVisible(False)
                self.resultado_container.setVisible(False)
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
        except Exception as e:
            print(f"Error en la búsqueda: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error en la búsqueda: {str(e)}")
            self.resultado_title.setVisible(False)
            self.resultado_container.setVisible(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def on_editar_pago(self):
        """Abre un diálogo para editar el pago seleccionado"""
        if not hasattr(self, 'pago_actual'):
            QMessageBox.warning(self, "Error", "Primero seleccione un pago")
            return
        
        try:
            # Obtener datos actualizados directamente de la API
            headers = session.get_headers()
            url = f"{session.api_url}/pagos/{self.pago_actual['id']}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Actualizar con datos frescos
                self.pago_actual = response.json()
        except Exception as e:
            print(f"Error al obtener datos actualizados: {str(e)}")
            
        # Abrir diálogo de edición con los datos actuales
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Pago")
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLabel {
                font-weight: bold;
                color: #2c3e50;
            }
            QDateEdit, QDoubleSpinBox, QLineEdit {
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
        
        # Campos editables
        fecha_edit = QDateEdit()
        fecha_edit.setDate(QDate.fromString(self.pago_actual['fecha'], "yyyy-MM-dd"))
        fecha_edit.setCalendarPopup(True)
        
        # Asegurarse de que el monto sea un número flotante
        monto = float(self.pago_actual.get('monto', 0))
        print(f"Monto obtenido de la API: {monto}")
        
        monto_spin = QDoubleSpinBox()
        monto_spin.setValue(monto)
        monto_spin.setRange(0, 999999.99)
        monto_spin.setSingleStep(100)
        monto_spin.setPrefix("$ ")
        monto_spin.setDecimals(2)
        
        descripcion_edit = QLineEdit()
        descripcion_edit.setText(self.pago_actual.get('descripcion', ''))
        
        layout.addRow("Fecha:", fecha_edit)
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
        
        guardar_btn.clicked.connect(lambda: self.guardar_edicion_pago(
            dialog, 
            self.pago_actual['id'], 
            fecha_edit.date().toString("yyyy-MM-dd"),
            monto_spin.value(),
            descripcion_edit.text()
        ))
        cancelar_btn.clicked.connect(dialog.reject)
        
        dialog.setMinimumWidth(400)
        dialog.exec()

    def guardar_edicion_pago(self, dialog, pago_id, fecha, monto, descripcion):
        """Guarda los cambios del pago editado"""
        try:
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            url = f"{session.api_url}/pagos/{pago_id}"
            
            datos_actualizacion = {
                "fecha": fecha,
                "monto": monto,
                "descripcion": descripcion
            }
            
            # Obtener monto anterior para saber si hubo cambio
            monto_anterior = 0
            if hasattr(self, 'pago_actual') and 'monto' in self.pago_actual:
                monto_anterior = float(self.pago_actual.get('monto', 0))
            
            response = requests.put(url, headers=headers, json=datos_actualizacion)
            
            if response.status_code == 200:
                pago_actualizado = response.json()
                QMessageBox.information(self, "Éxito", "Pago actualizado correctamente")
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
                
                # Actualizar la tabla de pagos y los detalles
                # Volvemos a buscar pagos para actualizar la tabla
                usuario_id = self.arbitro_combo_buscar.currentData()
                if usuario_id:
                    self.on_buscar_pagos_usuario()
                    
                    # Después de actualizar la tabla, cargar los detalles del pago editado
                    self.cargar_detalles_pago(pago_id)
                
                # Emitir señal para que el dashboard se actualice si está visible
                event = QEvent(QEvent.Type(QEvent.User + 1))  # Evento personalizado
                QCoreApplication.postEvent(self.parent(), event)
            else:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar. Código: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar: {str(e)}")
    def on_eliminar_pago(self):
        """Elimina el pago seleccionado"""
        if not hasattr(self, 'pago_actual'):
            QMessageBox.warning(self, "Error", "Primero seleccione un pago")
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar el pago #{self.pago_actual['id']}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            try:
                headers = session.get_headers()
                url = f"{session.api_url}/pagos/{self.pago_actual['id']}"

                usuario_id = self.arbitro_combo_buscar.currentData()
                pago_id = self.pago_actual['id']
                monto_eliminado = float(self.pago_actual.get('monto', 0))

                response = requests.delete(url, headers=headers)

                if response.status_code == 200:
                    QMessageBox.information(self, "Éxito", "Pago eliminado correctamente")

                    # Registrar movimiento de anulación
                    partida_data = {
                        "tipo": "anulacion",
                        "detalle": f"ELIMINACIÓN Pago - {session.user_info['nombre']} (ID: {pago_id})",
                        "usuario_id": session.user_info['id'],
                        "pago_id": pago_id,  # 👈 clave: que este campo esté bien
                        "ingreso": 0,
                        "egreso": monto_eliminado,  # El monto eliminado se registra como egreso
                        "fecha": datetime.now().strftime("%Y-%m-%d")
                    }

                    # Registrar la anulación en el sistema de partidas
                    partida_url = f"{session.api_url}/partidas"
                    partida_response = requests.post(partida_url, headers=headers, json=partida_data)

                    if partida_response.status_code in (200, 201):
                        print("Anulación registrada en partidas correctamente")
                    else:
                        print(f"Error al registrar anulación en partidas: {partida_response.status_code}")

                    # Recalcular saldos
                    recalcular_url = f"{session.api_url}/transacciones/recalcular-saldos"
                    recalcular_response = requests.post(recalcular_url, headers=headers)

                    if recalcular_response.status_code == 200:
                        print("Saldos recalculados correctamente después de eliminar")
                    else:
                        print(f"Error al recalcular saldos: {recalcular_response.status_code}")

                    self.resultado_container.setVisible(False)
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)

                    if usuario_id:
                        self.on_buscar_pagos_usuario()

                    from PySide6.QtCore import QTimer, QEvent, QCoreApplication

                    def actualizar_dashboard_despues_delay():
                        event = QEvent(QEvent.Type(QEvent.User + 1))
                        QCoreApplication.postEvent(self.parent(), event)

                    timer = QTimer(self)
                    timer.setSingleShot(True)
                    timer.timeout.connect(actualizar_dashboard_despues_delay)
                    timer.start(500)
                    self._update_timer = timer

                    self.on_buscar_pagos()

                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"No se pudo eliminar el pago. Código: {response.status_code}"
                    )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")



    # Método adicional para inicializar después del login
    def initialize_after_login(self):
        """Método para inicializar datos después del login"""
        self.refresh_data()    




                                              