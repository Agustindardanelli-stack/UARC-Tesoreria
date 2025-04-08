import os
import sys
from datetime import datetime
import pandas as pd
import requests
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QSplitter, QFrame, QTabWidget, QSpacerItem, QSizePolicy,
    QFormLayout, QLineEdit, QDateEdit, QComboBox, QMessageBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QDate

from views.dashboard import SidebarWidget
from sesion import session

class PagosView(QWidget):
    navigation_requested = Signal(str)  # Señal para solicitar navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
        self.usuarios = []
        self.retenciones = []
   
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
        self.content_layout.addWidget(title_label)
        
        # Tabs para las diferentes secciones
        self.tabs = QTabWidget()
        
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
        
        # Selección de árbitro
        self.arbitro_combo = QComboBox()
        self.arbitro_combo.setPlaceholderText("Seleccione un árbitro")
        form_layout.addRow("Pagador/Cobrador:", self.arbitro_combo)
        
        # Fecha
        self.fecha_edit = QDateEdit()
        self.fecha_edit.setDate(QDate.currentDate())
        self.fecha_edit.setCalendarPopup(True)
        form_layout.addRow("Fecha:", self.fecha_edit)
        
        # Tipo de Retención
        self.retencion_combo = QComboBox()
        self.retencion_combo.setPlaceholderText("Seleccione una retención")
        self.retencion_combo.currentIndexChanged.connect(self.on_retencion_changed)
        form_layout.addRow("Tipo de Retención:", self.retencion_combo)
        
        # Monto
        self.monto_spin = QDoubleSpinBox()
        self.monto_spin.setRange(0, 999999.99)
        self.monto_spin.setSingleStep(100)
        self.monto_spin.setPrefix("$ ")
        self.monto_spin.setDecimals(2)
        form_layout.addRow("Monto:", self.monto_spin)
        
        # Notas
        self.notas_edit = QLineEdit()
        self.notas_edit.setPlaceholderText("Ingrese detalles adicionales...")
        form_layout.addRow("Descripción/Notas:", self.notas_edit)
        
        # Botón de registro
        self.registrar_btn = QPushButton("Registrar Pago")
        self.registrar_btn.clicked.connect(self.on_registrar_pago)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.registrar_btn)
    
    def setup_tab_listar(self):
        layout = QVBoxLayout(self.tab_listar)
        
        # Filtros
        filtros_layout = QHBoxLayout()
        
        # Desde
        desde_label = QLabel("Desde:")
        self.desde_date = QDateEdit()
        self.desde_date.setDate(QDate.currentDate().addDays(-30))  # Último mes por defecto
        self.desde_date.setCalendarPopup(True)
        
        # Hasta
        hasta_label = QLabel("Hasta:")
        self.hasta_date = QDateEdit()
        self.hasta_date.setDate(QDate.currentDate())
        self.hasta_date.setCalendarPopup(True)
        
        # Botón de búsqueda
        self.buscar_btn = QPushButton("Buscar")
        self.buscar_btn.clicked.connect(self.on_buscar_pagos)
        
        filtros_layout.addWidget(desde_label)
        filtros_layout.addWidget(self.desde_date)
        filtros_layout.addWidget(hasta_label)
        filtros_layout.addWidget(self.hasta_date)
        filtros_layout.addWidget(self.buscar_btn)
        
        layout.addLayout(filtros_layout)
        
        # Tabla de pagos
        self.pagos_table = QTableWidget()
        self.pagos_table.setColumnCount(5)
        self.pagos_table.setHorizontalHeaderLabels(["ID", "Fecha", "Árbitro", "Retención", "Monto"])
        self.pagos_table.horizontalHeader().setStretchLastSection(True)
        self.pagos_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.pagos_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.pagos_table)
        
        # Label para total
        self.total_label = QLabel("Total de pagos: $0.00")
        layout.addWidget(self.total_label)
    
    def setup_tab_buscar(self):
        layout = QVBoxLayout(self.tab_buscar)
        
        # Campo de búsqueda
        busqueda_layout = QHBoxLayout()
        
        self.id_search = QLineEdit()
        self.id_search.setPlaceholderText("Ingrese ID del pago...")
        
        self.search_btn = QPushButton("Buscar")
        self.search_btn.clicked.connect(self.on_buscar_pago_id)
        
        busqueda_layout.addWidget(QLabel("Buscar por ID:"))
        busqueda_layout.addWidget(self.id_search)
        busqueda_layout.addWidget(self.search_btn)
        
        layout.addLayout(busqueda_layout)
        
        # Contenedor para resultados
        self.resultado_container = QWidget()
        self.resultado_layout = QVBoxLayout(self.resultado_container)
        
        # Título de resultados
        self.resultado_title = QLabel("Detalles del Pago")
        resultado_font = QFont()
        resultado_font.setPointSize(16)
        self.resultado_title.setFont(resultado_font)
        self.resultado_title.setVisible(False)
        self.resultado_layout.addWidget(self.resultado_title)
        
        # Detalles en dos columnas
        detalles_layout = QHBoxLayout()
        
        # Columna 1
        col1_layout = QVBoxLayout()
        self.id_label = QLabel()
        self.fecha_label = QLabel()
        self.monto_label = QLabel()
        col1_layout.addWidget(self.id_label)
        col1_layout.addWidget(self.fecha_label)
        col1_layout.addWidget(self.monto_label)
        
        # Columna 2
        col2_layout = QVBoxLayout()
        self.arbitro_label = QLabel()
        self.retencion_label = QLabel()
        col2_layout.addWidget(self.arbitro_label)
        col2_layout.addWidget(self.retencion_label)
        
        detalles_layout.addLayout(col1_layout)
        detalles_layout.addLayout(col2_layout)
        
        self.resultado_layout.addLayout(detalles_layout)
        
        layout.addWidget(self.resultado_container)
        self.resultado_container.setVisible(False)
    
    def connect_signals(self):
        self.sidebar.navigation_requested.connect(self.navigation_requested)
    
    def refresh_data(self):
        """Carga los datos iniciales"""
        self.cargar_usuarios()
        self.cargar_retenciones()
        self.on_buscar_pagos()
    
    def cargar_usuarios(self):
        """Carga la lista de usuarios desde la API"""
        try:
            headers = session.get_headers()
            # Asegúrate de que la URL coincida exactamente con la del backend
            url = f"{session.api_url}/usuarios"  # Sin barra al final
            print(f"Realizando petición GET a: {url}")
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                self.usuarios = response.json()
                print(f"Usuarios cargados: {len(self.usuarios)}")
                
                # Actualizar combo box
                self.arbitro_combo.clear()
                for usuario in self.usuarios:
                    self.arbitro_combo.addItem(f"{usuario['nombre']}", usuario['id'])
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron cargar los usuarios. Status code: {response.status_code}")
                print(f"Error al cargar usuarios: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar usuarios: {str(e)}")
    
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
                QMessageBox.warning(self, "Error", f"No se pudieron cargar las retenciones. Status code: {response.status_code}")
                print(f"Error al cargar retenciones: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar retenciones: {str(e)}")
    
    def on_retencion_changed(self, index):
        """Actualiza el monto basado en la retención seleccionada"""
        if index >= 0 and index < len(self.retenciones):
            retencion_id = self.retencion_combo.itemData(index)
            retencion = next((r for r in self.retenciones if r['id'] == retencion_id), None)
            if retencion:
                self.monto_spin.setValue(retencion['monto'])
    
    def on_registrar_pago(self):
        """Maneja el evento de clic en Registrar Pago"""
        # Validar campos
        if self.arbitro_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Por favor seleccione un árbitro")
            return
        
        if self.retencion_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Por favor seleccione una retención")
            return
        
        if self.monto_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "El monto debe ser mayor a cero")
            return
        
        # Obtener datos
        usuario_id = self.arbitro_combo.currentData()
        fecha = self.fecha_edit.date().toString("yyyy-MM-dd")
        retencion_id = self.retencion_combo.currentData()
        monto = self.monto_spin.value()
        
        # Crear objeto de pago
        pago_data = {
            "usuario_id": usuario_id,
            "fecha": fecha,
            "monto": monto,
            "retencion_id": retencion_id
        }
        
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
                QMessageBox.information(self, "Éxito", "Pago registrado exitosamente")
                
                # Limpiar formulario
                self.arbitro_combo.setCurrentIndex(-1)
                self.fecha_edit.setDate(QDate.currentDate())
                self.retencion_combo.setCurrentIndex(-1)
                self.monto_spin.setValue(0)
                self.notas_edit.clear()
                
                # Actualizar lista de pagos
                self.on_buscar_pagos()
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
                pagos_data = response.json()
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
                    self.pagos_table.setItem(row, 0, QTableWidgetItem(str(pago.get("id", ""))))
                    
                    # Fecha
                    fecha = datetime.strptime(pago.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if pago.get('fecha') else ''
                    self.pagos_table.setItem(row, 1, QTableWidgetItem(fecha))
                    
                    # Árbitro
                    arbitro = pago.get("usuario", {}).get("nombre", "")
                    self.pagos_table.setItem(row, 2, QTableWidgetItem(arbitro))
                    
                    # Retención
                    retencion = pago.get("retencion", {}).get("nombre", "")
                    self.pagos_table.setItem(row, 3, QTableWidgetItem(retencion))
                    
                    # Monto
                    monto = pago.get("monto", 0)
                    monto_item = QTableWidgetItem(f"${monto:,.2f}")
                    monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.pagos_table.setItem(row, 4, monto_item)
                    
                    # Acumular total
                    total_pagos += monto
                
                # Actualizar total
                self.total_label.setText(f"Total de pagos: ${total_pagos:,.2f}")
                
                # Ajustar columnas
                self.pagos_table.resizeColumnsToContents()
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron cargar los pagos. Status code: {response.status_code}")
                print(f"Error al cargar pagos: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al buscar pagos: {str(e)}")
    
    def on_buscar_pago_id(self):
        """Busca un pago por su ID"""
        pago_id = self.id_search.text().strip()
        
        if not pago_id.isdigit():
            QMessageBox.warning(self, "Error", "Por favor ingrese un ID válido")
            return
        
        try:
            # Obtener pago por ID
            headers = session.get_headers()
            url = f"{session.api_url}/pagos/{pago_id}"
            print(f"Realizando petición GET a: {url}")
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                pago = response.json()
                print(f"Pago cargado: {pago}")
                
                # Mostrar detalles
                self.resultado_title.setVisible(True)
                self.resultado_container.setVisible(True)
                
                # Formatear fecha
                fecha = datetime.strptime(pago.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if pago.get('fecha') else ''
                
                # Asignar valores a los labels
                self.id_label.setText(f"<b>ID del Pago:</b> {pago.get('id')}")
                self.fecha_label.setText(f"<b>Fecha:</b> {fecha}")
                self.monto_label.setText(f"<b>Monto:</b> ${pago.get('monto', 0):,.2f}")
                self.arbitro_label.setText(f"<b>Árbitro:</b> {pago.get('usuario', {}).get('nombre', '')}")
                self.retencion_label.setText(f"<b>Retención:</b> {pago.get('retencion', {}).get('nombre', '')}")
            else:
                self.resultado_container.setVisible(False)
                QMessageBox.warning(self, "No encontrado", f"No se encontró ningún pago con ID {pago_id}. Status code: {response.status_code}")
                print(f"Error al buscar pago por ID: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al buscar pago: {str(e)}")