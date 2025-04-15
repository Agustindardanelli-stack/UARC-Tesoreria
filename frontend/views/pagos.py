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
        
        # Monto
        self.monto_spin = QDoubleSpinBox()
        self.monto_spin.setRange(0, 999999.99)
        self.monto_spin.setSingleStep(100)
        self.monto_spin.setPrefix("$ ")
        self.monto_spin.setDecimals(2)
        form_layout.addRow("Monto:", self.monto_spin)
        
        # Descripción/Notas (Nuevo)
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
        self.pagos_table.setColumnCount(5)  # 5 columnas
        self.pagos_table.setHorizontalHeaderLabels(["ID", "Fecha", "Árbitro", "Monto", "Descripción"])
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
        
        # Etiqueta de búsqueda
        busqueda_label = QLabel("Buscar:")
        
        # Combo para seleccionar tipo de búsqueda
        self.tipo_busqueda_combo = QComboBox()
        self.tipo_busqueda_combo.addItems(["Por ID", "Por Árbitro", "Por Descripción"])
        
        # Campo de búsqueda
        self.busqueda_input = QLineEdit()
        self.busqueda_input.setPlaceholderText("Ingrese término de búsqueda...")
        
        # Botón de búsqueda
        self.search_btn = QPushButton("Buscar")
        self.search_btn.clicked.connect(self.on_buscar_pago_id)
        
        # Botones de Editar y Eliminar
        self.edit_btn = QPushButton("Editar")
        self.edit_btn.clicked.connect(self.on_editar_pago)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.clicked.connect(self.on_eliminar_pago)
        self.delete_btn.setEnabled(False)
        
        # Agregar widgets al layout
        busqueda_layout.addWidget(busqueda_label)
        busqueda_layout.addWidget(self.tipo_busqueda_combo)
        busqueda_layout.addWidget(self.busqueda_input)
        busqueda_layout.addWidget(self.search_btn)
        busqueda_layout.addWidget(self.edit_btn)
        busqueda_layout.addWidget(self.delete_btn)
        
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
        self.descripcion_label = QLabel()  # Nuevo label
        col2_layout.addWidget(self.arbitro_label)
        col2_layout.addWidget(self.descripcion_label)
        
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
        self.on_buscar_pagos()
    
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
                
                # Actualizar combo box
                self.arbitro_combo.clear()
                for usuario in self.usuarios:
                    self.arbitro_combo.addItem(f"{usuario['nombre']}", usuario['id'])
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron cargar los usuarios. Status code: {response.status_code}")
                print(f"Error al cargar usuarios: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar usuarios: {str(e)}")
    
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
    
    
    def on_buscar_pago_id(self):
        """Busca un pago por diferentes criterios"""
        tipo_busqueda = self.tipo_busqueda_combo.currentText()
        termino_busqueda = self.busqueda_input.text().strip()
        
        if not termino_busqueda:
            QMessageBox.warning(self, "Error", "Ingrese un término de búsqueda")
            return
        
        try:
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
                    self.resultado_title.setVisible(True)
                    self.resultado_container.setVisible(True)
                    
                    # Formatear fecha
                    fecha = datetime.strptime(self.pago_actual.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if self.pago_actual.get('fecha') else ''
                    
                    # Asignar valores a los labels
                    self.id_label.setText(f"<b>ID del Pago:</b> {self.pago_actual.get('id')}")
                    self.fecha_label.setText(f"<b>Fecha:</b> {fecha}")
                    self.monto_label.setText(f"<b>Monto:</b> ${self.pago_actual.get('monto', 0):,.2f}")
                    
                    # Obtener nombre del árbitro
                    usuario = self.pago_actual.get("usuario", {})
                    arbitro_nombre = usuario.get("nombre", "")
                    self.arbitro_label.setText(f"<b>Árbitro:</b> {arbitro_nombre}")
                    
                    # Obtener descripción
                    descripcion = self.pago_actual.get("descripcion", "")
                    self.descripcion_label.setText(f"<b>Descripción:</b> {descripcion}")
                    
                    # Habilitar botones de editar y eliminar
                    self.edit_btn.setEnabled(True)
                    self.delete_btn.setEnabled(True)
                else:
                    QMessageBox.information(self, "Búsqueda", "No se encontraron resultados")
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
            else:
                QMessageBox.warning(self, "Error", f"Error en la búsqueda. Código: {response.status_code}")
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en la búsqueda: {str(e)}")
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def on_editar_pago(self):
        """Abre un diálogo para editar el pago seleccionado"""
        if not hasattr(self, 'pago_actual'):
            QMessageBox.warning(self, "Error", "Primero realice una búsqueda")
            return
        
        # Abrir diálogo de edición con los datos actuales
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Pago")
        layout = QFormLayout(dialog)
        
        # Campos editables
        fecha_edit = QDateEdit()
        fecha_edit.setDate(QDate.fromString(self.pago_actual['fecha'], "yyyy-MM-dd"))
        
        monto_spin = QDoubleSpinBox()
        monto_spin.setValue(self.pago_actual['monto'])
        monto_spin.setRange(0, 999999.99)
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
        cancelar_btn = QPushButton("Cancelar")
        btn_layout.addWidget(guardar_btn)
        btn_layout.addWidget(cancelar_btn)
        layout.addRow(btn_layout)
        
        guardar_btn.clicked.connect(lambda: self.guardar_edicion_pago(
            dialog, 
            self.pago_actual['id'], 
            fecha_edit.date().toString("yyyy-MM-dd"),
            monto_spin.value(),
            descripcion_edit.text()
        ))
        cancelar_btn.clicked.connect(dialog.reject)
        
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
            
            response = requests.put(url, headers=headers, json=datos_actualizacion)
            
            if response.status_code == 200:
                QMessageBox.information(self, "Éxito", "Pago actualizado correctamente")
                dialog.accept()
                # Actualizar la vista de detalles
                self.on_buscar_pago_id()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar. Código: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar: {str(e)}")

    def on_eliminar_pago(self):
            """Elimina el pago seleccionado"""
            if not hasattr(self, 'pago_actual'):
                QMessageBox.warning(self, "Error", "Primero realice una búsqueda")
                return
            
            respuesta = QMessageBox.question(
                self, 
                "Confirmar Eliminación", 
                "¿Está seguro de eliminar este pago?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                try:
                    headers = session.get_headers()
                    url = f"{session.api_url}/pagos/{self.pago_actual['id']}"
                    
                    response = requests.delete(url, headers=headers)
                    
                    if response.status_code == 200:
                        QMessageBox.information(self, "Éxito", "Pago eliminado correctamente")
                        # Limpiar campos
                        self.busqueda_input.clear()
                        self.resultado_container.setVisible(False)
                        self.resultado_title.setVisible(False)
                        
                        # Deshabilitar botones
                        self.edit_btn.setEnabled(False)
                        self.delete_btn.setEnabled(False)
                        
                        # Actualizar lista de pagos
                        self.on_buscar_pagos()
                    else:
                        QMessageBox.warning(
                            self, 
                            "Error", 
                            f"No se pudo eliminar el pago. Código: {response.status_code}"
                        )
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")
                
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
                    self.pagos_table.setItem(row, 0, QTableWidgetItem(str(pago.get("id", ""))))

                    # Fecha
                    fecha = datetime.strptime(pago.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if pago.get('fecha') else ''
                    self.pagos_table.setItem(row, 1, QTableWidgetItem(fecha))

                    # Árbitro
                    usuario = pago.get("usuario") or {}
                    arbitro = usuario.get("nombre", "")
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
                QMessageBox.warning(self, "Error", f"No se pudieron cargar los pagos. Status code: {response.status_code}")
                print(f"Error al cargar pagos: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al buscar pagos: {str(e)}")