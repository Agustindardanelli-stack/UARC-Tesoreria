import os
import sys
from datetime import datetime
import pandas as pd
import requests
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QFrame, QTabWidget, QSpacerItem, QSizePolicy,
    QFormLayout, QLineEdit, QDateEdit, QComboBox, QMessageBox, QDoubleSpinBox,
    QCheckBox, QRadioButton, QButtonGroup
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal, QDate, QTimer

from views.dashboard import SidebarWidget
from sesion import session

class SocioCuotaView(QWidget):
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
        title_label = QLabel("Gestión de Cuotas Societarias")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.content_layout.addWidget(title_label)
        
        # Tabs para las diferentes secciones
        self.tabs = QTabWidget()
        
        # Tab 1: Registrar Cuota
        self.tab_registrar = QWidget()
        self.setup_tab_registrar()
        self.tabs.addTab(self.tab_registrar, "Registrar Cuota")
        
        # Tab 2: Listar Cuotas
        self.tab_listar = QWidget()
        self.setup_tab_listar()
        self.tabs.addTab(self.tab_listar, "Listar Cuotas")
        
        # Tab 3: Pagar Cuota
        self.tab_pagar = QWidget()
        self.setup_tab_pagar()
        self.tabs.addTab(self.tab_pagar, "Pagar Cuota")
        
        self.content_layout.addWidget(self.tabs)
        
        # Agregar al layout principal
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_widget)
    
    def setup_tab_registrar(self):
        layout = QVBoxLayout(self.tab_registrar)
        
        # Formulario para registrar cuota
        form_layout = QFormLayout()
        
        # Selección de árbitro
        self.arbitro_combo = QComboBox()
        self.arbitro_combo.setPlaceholderText("Seleccione un árbitro")
        self.arbitro_combo.setEditable(False)  # Hazlo no editable para mostrar menú desplegable
        self.arbitro_combo.setMaxVisibleItems(15)  # Muestra más elementos visibles
        
        # Botón para mostrar desplegable
        self.mostrar_desplegable_btn = QPushButton("▼")
        self.mostrar_desplegable_btn.setMaximumWidth(30)
        self.mostrar_desplegable_btn.clicked.connect(self.mostrar_desplegable)
        
        # Crear un layout horizontal para el combo y el botón
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.arbitro_combo)
        combo_layout.addWidget(self.mostrar_desplegable_btn)
        
        # Añadir al form_layout
        form_layout.addRow("Árbitro:", combo_layout)
        
        # Opción para todos los usuarios
        self.todos_usuarios_check = QCheckBox("Generar para todos los usuarios")
        self.todos_usuarios_check.stateChanged.connect(self.on_todos_usuarios_changed)
        form_layout.addRow("", self.todos_usuarios_check)
        
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
        
        # Botón de registro
        self.registrar_btn = QPushButton("Registrar Cuota")
        self.registrar_btn.clicked.connect(self.on_registrar_cuota)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.registrar_btn)
    
    def setup_tab_listar(self):
        layout = QVBoxLayout(self.tab_listar)
        
        # Filtros
        filtros_layout = QHBoxLayout()
        
        # Estado de cuota
        estado_label = QLabel("Estado:")
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Todas", "Pendientes", "Pagadas"])
        
        # Árbitro
        arbitro_label = QLabel("Árbitro:")
        self.arbitro_filtro_combo = QComboBox()
        self.arbitro_filtro_combo.setPlaceholderText("Todos")
        
        # Botón de búsqueda
        self.buscar_btn = QPushButton("Buscar")
        self.buscar_btn.clicked.connect(self.on_buscar_cuotas)
        
        filtros_layout.addWidget(estado_label)
        filtros_layout.addWidget(self.estado_combo)
        filtros_layout.addWidget(arbitro_label)
        filtros_layout.addWidget(self.arbitro_filtro_combo)
        filtros_layout.addWidget(self.buscar_btn)
        
        layout.addLayout(filtros_layout)
        
        # Tabla de cuotas
        self.cuotas_table = QTableWidget()
        self.cuotas_table.setColumnCount(6)
        self.cuotas_table.setHorizontalHeaderLabels(["ID", "Fecha", "Árbitro", "Monto", "Estado", "Monto Pagado"])
        self.cuotas_table.horizontalHeader().setStretchLastSection(True)
        self.cuotas_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cuotas_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.cuotas_table)
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        
        self.total_cuotas_label = QLabel("Total cuotas: 0")
        self.cuotas_pagadas_label = QLabel("Cuotas pagadas: 0")
        self.cuotas_pendientes_label = QLabel("Cuotas pendientes: 0")
        
        stats_layout.addWidget(self.total_cuotas_label)
        stats_layout.addWidget(self.cuotas_pagadas_label)
        stats_layout.addWidget(self.cuotas_pendientes_label)
        
        layout.addLayout(stats_layout)
        
        # Monto total y pendiente
        montos_layout = QHBoxLayout()
        
        self.monto_total_label = QLabel("Monto total: $0.00")
        self.monto_pendiente_label = QLabel("Monto pendiente: $0.00")
        
        montos_layout.addWidget(self.monto_total_label)
        montos_layout.addWidget(self.monto_pendiente_label)
        
        layout.addLayout(montos_layout)

    def on_buscar_cuotas(self):
        """Busca cuotas según los filtros seleccionados"""
        try:
            # Preparar parámetros
            estado = self.estado_combo.currentText()
            
            # Mapear valores de UI a valores esperados por la API
            if estado == "Todas":
                estado_filter = None
            elif estado == "Pendientes":
                estado_filter = False
            elif estado == "Pagadas":
                estado_filter = True
            
            # Obtener el ID del árbitro seleccionado (si hay uno)
            arbitro_id = None
            if self.arbitro_filtro_combo.currentIndex() > 0:  # Si no es "Todos"
                arbitro_id = self.arbitro_filtro_combo.currentData()
            
            # Construir parámetros de consulta
            params = {
                "skip": 0,
                "limit": 100
            }
            
            # Añadir filtros opcionales solo si están seleccionados
            if estado_filter is not None:
                params["pagado"] = estado_filter
            
            # Construir URL base
            if arbitro_id:
                url = f"{session.api_url}/cuotas/usuario/{arbitro_id}"
            else:
                url = f"{session.api_url}/cuotas"
            
            # Obtener cuotas
            headers = session.get_headers()
            print(f"Realizando petición GET a: {url}")
            print(f"Parámetros: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                cuotas_data = response.json()
                print(f"Cuotas cargadas: {len(cuotas_data)}")
                
                # Limpiar tabla
                self.cuotas_table.setRowCount(0)
                
                # Estadísticas
                total_cuotas = len(cuotas_data)
                cuotas_pagadas = 0
                cuotas_pendientes = 0
                monto_total = 0
                monto_pendiente = 0
                
                # Llenar tabla con datos
                for row, cuota in enumerate(cuotas_data):
                    self.cuotas_table.insertRow(row)
                    
                    # ID
                    self.cuotas_table.setItem(row, 0, QTableWidgetItem(str(cuota.get("id", ""))))
                    
                    # Fecha
                    fecha_str = cuota.get('fecha', '')
                    fecha_display = ""
                    if fecha_str:
                        try:
                            fecha_display = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except:
                            fecha_display = fecha_str
                    
                    self.cuotas_table.setItem(row, 1, QTableWidgetItem(fecha_display))
                    
                    # Árbitro
                    arbitro = ""
                    if isinstance(cuota.get("usuario"), dict):
                        arbitro = cuota.get("usuario", {}).get("nombre", "")
                    
                    self.cuotas_table.setItem(row, 2, QTableWidgetItem(arbitro))
                    
                    # Monto
                    monto = cuota.get("monto", 0)
                    monto_item = QTableWidgetItem(f"${monto:,.2f}")
                    monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.cuotas_table.setItem(row, 3, monto_item)
                    
                    # Estado
                    pagado = cuota.get("pagado", False)
                    estado_text = "Pagada" if pagado else "Pendiente"
                    estado_item = QTableWidgetItem(estado_text)
                    if not pagado:
                        estado_item.setForeground(Qt.red)
                    else:
                        estado_item.setForeground(Qt.darkGreen)
                    
                    self.cuotas_table.setItem(row, 4, estado_item)
                    
                    # Monto Pagado
                    monto_pagado = cuota.get("monto_pagado", 0)
                    monto_pagado_item = QTableWidgetItem(f"${monto_pagado:,.2f}")
                    monto_pagado_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.cuotas_table.setItem(row, 5, monto_pagado_item)
                    
                    # Actualizar estadísticas
                    monto_total += monto
                    if pagado:
                        cuotas_pagadas += 1
                    else:
                        cuotas_pendientes += 1
                        monto_pendiente += monto - monto_pagado
                
                # Actualizar labels de estadísticas
                self.total_cuotas_label.setText(f"Total cuotas: {total_cuotas}")
                self.cuotas_pagadas_label.setText(f"Cuotas pagadas: {cuotas_pagadas}")
                self.cuotas_pendientes_label.setText(f"Cuotas pendientes: {cuotas_pendientes}")
                
                self.monto_total_label.setText(f"Monto total: ${monto_total:,.2f}")
                self.monto_pendiente_label.setText(f"Monto pendiente: ${monto_pendiente:,.2f}")
                
                # Ajustar columnas
                self.cuotas_table.resizeColumnsToContents()
            else:
                error_msg = "No se pudieron cargar las cuotas"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.warning(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                print(f"Error al cargar cuotas: {response.text}")
        except Exception as e:
            print(f"Excepción al buscar cuotas: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al buscar cuotas: {str(e)}")    
    
    def setup_tab_pagar(self):
        layout = QVBoxLayout(self.tab_pagar)
        
        # Campo de búsqueda por usuario (en lugar de por ID)
        busqueda_layout = QHBoxLayout()
        
        # ComboBox para seleccionar usuario
        self.usuario_search_combo = QComboBox()
        self.usuario_search_combo.setPlaceholderText("Seleccione un árbitro")
        self.usuario_search_combo.setEditable(False)
        self.usuario_search_combo.setMaxVisibleItems(15)
        
        self.search_btn = QPushButton("Buscar")
        self.search_btn.clicked.connect(self.on_buscar_cuotas_usuario)
        
        busqueda_layout.addWidget(QLabel("Buscar por Árbitro:"))
        busqueda_layout.addWidget(self.usuario_search_combo)
        busqueda_layout.addWidget(self.search_btn)
        
        layout.addLayout(busqueda_layout)
        
        # Tabla de cuotas del usuario seleccionado
        self.cuotas_usuario_table = QTableWidget()
        self.cuotas_usuario_table.setColumnCount(5)
        self.cuotas_usuario_table.setHorizontalHeaderLabels(["ID", "Fecha", "Monto", "Estado", "Monto Pagado"])
        self.cuotas_usuario_table.horizontalHeader().setStretchLastSection(True)
        self.cuotas_usuario_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cuotas_usuario_table.setAlternatingRowColors(True)
        self.cuotas_usuario_table.clicked.connect(self.on_seleccionar_cuota)
        
        layout.addWidget(self.cuotas_usuario_table)
        
        # Contenedor para resultados y formulario de pago
        self.resultado_container = QWidget()
        self.resultado_layout = QVBoxLayout(self.resultado_container)
        
        # Título de resultados
        self.resultado_title = QLabel("Detalles de la Cuota")
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
        self.arbitro_label = QLabel()
        col1_layout.addWidget(self.id_label)
        col1_layout.addWidget(self.fecha_label)
        col1_layout.addWidget(self.arbitro_label)
        
        # Columna 2
        col2_layout = QVBoxLayout()
        self.monto_label = QLabel()
        self.estado_label = QLabel()
        self.monto_pagado_label = QLabel()
        col2_layout.addWidget(self.monto_label)
        col2_layout.addWidget(self.estado_label)
        col2_layout.addWidget(self.monto_pagado_label)
        
        detalles_layout.addLayout(col1_layout)
        detalles_layout.addLayout(col2_layout)
        
        self.resultado_layout.addLayout(detalles_layout)
        
        # Formulario de pago
        self.pago_form = QWidget()
        pago_layout = QVBoxLayout(self.pago_form)
        
        pago_title = QLabel("Realizar Pago")
        pago_title_font = QFont()
        pago_title_font.setPointSize(14)
        pago_title.setFont(pago_title_font)
        pago_layout.addWidget(pago_title)
        
        pago_form_layout = QFormLayout()
        
        self.monto_a_pagar_spin = QDoubleSpinBox()
        self.monto_a_pagar_spin.setRange(0.01, 999999.99)
        self.monto_a_pagar_spin.setSingleStep(100)
        self.monto_a_pagar_spin.setPrefix("$ ")
        self.monto_a_pagar_spin.setDecimals(2)
        pago_form_layout.addRow("Monto a Pagar:", self.monto_a_pagar_spin)
        
        self.pagar_btn = QPushButton("Registrar Pago")
        self.pagar_btn.clicked.connect(self.on_pagar_cuota)
        
        pago_layout.addLayout(pago_form_layout)
        pago_layout.addWidget(self.pagar_btn)
        
        self.resultado_layout.addWidget(self.pago_form)
        self.pago_form.setVisible(False)
        
        layout.addWidget(self.resultado_container)
        self.resultado_container.setVisible(False)
    
    def connect_signals(self):
        self.sidebar.navigation_requested.connect(self.navigation_requested)
    
    def refresh_data(self):
        """Carga los datos iniciales"""
        self.cargar_usuarios()
        self.on_buscar_cuotas()
    
    def mostrar_desplegable(self):
        """Muestra manualmente el desplegable del combo de árbitros"""
        self.arbitro_combo.showPopup()
    
        
    def on_todos_usuarios_changed(self, state):
        """Maneja el cambio en el checkbox de todos los usuarios"""
        self.arbitro_combo.setEnabled(not bool(state))
    
    def on_registrar_cuota(self):
        """Maneja el evento de clic en Registrar Cuota"""
        # Validar campos
        if not self.todos_usuarios_check.isChecked() and self.arbitro_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Por favor seleccione un árbitro o marque la opción para todos")
            return
        
        if self.monto_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "El monto debe ser mayor a cero")
            return
        
        # Obtener datos comunes
        fecha = self.fecha_edit.date().toString("yyyy-MM-dd")
        monto = self.monto_spin.value()
        
        if self.todos_usuarios_check.isChecked():
            # Registrar cuota para todos los usuarios
            success_count = 0
            error_count = 0
            
            for usuario in self.usuarios:
                # Crear objeto de cuota
                cuota_data = {
                    "usuario_id": usuario["id"],
                    "fecha": fecha,
                    "monto": monto,
                    "pagado": False,
                    "monto_pagado": 0
                }
                
                try:
                    # Enviar solicitud para crear cuota
                    headers = session.get_headers()
                    headers["Content-Type"] = "application/json"
                    
                    url = f"{session.api_url}/cuotas"
                    response = requests.post(
                        url,
                        headers=headers,
                        data=json.dumps(cuota_data)
                    )
                    
                    if response.status_code == 200 or response.status_code == 201:
                        success_count += 1
                    else:
                        error_count += 1
                        print(f"Error al registrar cuota para usuario {usuario['id']}: {response.text}")
                except Exception as e:
                    error_count += 1
                    print(f"Excepción al registrar cuota para usuario {usuario['id']}: {str(e)}")
            
            if success_count > 0:
                QMessageBox.information(self, "Éxito", f"Se registraron {success_count} cuotas exitosamente")
                
                # Limpiar formulario
                self.arbitro_combo.setCurrentIndex(-1)
                self.fecha_edit.setDate(QDate.currentDate())
                self.monto_spin.setValue(0)
                self.todos_usuarios_check.setChecked(False)
                
                # Actualizar lista de cuotas
                self.on_buscar_cuotas()
            
            if error_count > 0:
                QMessageBox.warning(self, "Advertencia", f"No se pudieron registrar {error_count} cuotas")
        else:
            # Registrar cuota para un solo usuario
            usuario_id = self.arbitro_combo.currentData()
            
            # Crear objeto de cuota
            cuota_data = {
                "usuario_id": usuario_id,
                "fecha": fecha,
                "monto": monto,
                "pagado": False,
                "monto_pagado": 0
            }
            
            try:
                # Enviar solicitud para crear cuota
                headers = session.get_headers()
                headers["Content-Type"] = "application/json"
                
                url = f"{session.api_url}/cuotas"
                print(f"Realizando petición POST a: {url}")
                print(f"Datos: {json.dumps(cuota_data)}")
                
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(cuota_data)
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    QMessageBox.information(self, "Éxito", "Cuota registrada exitosamente")
                    
                    # Limpiar formulario
                    self.arbitro_combo.setCurrentIndex(-1)
                    self.fecha_edit.setDate(QDate.currentDate())
                    self.monto_spin.setValue(0)
                    
                    # Actualizar lista de cuotas
                    self.on_buscar_cuotas()
                else:
                    error_msg = "Error al registrar la cuota"
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            error_msg = error_data["detail"]
                    except:
                        pass
                    QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                    print(f"Error al registrar cuota: {response.text}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al registrar cuota: {str(e)}")
    
    def on_pagar_cuota(self):
        """Registra el pago de una cuota"""
        if not hasattr(self, 'current_cuota'):
            QMessageBox.warning(self, "Error", "Primero debe buscar una cuota")
            return
        
        monto_a_pagar = self.monto_a_pagar_spin.value()
        
        if monto_a_pagar <= 0:
            QMessageBox.warning(self, "Error", "El monto a pagar debe ser mayor a cero")
            return
        
        try:
            # Enviar solicitud para pagar la cuota
            headers = session.get_headers()
            
            url = f"{session.api_url}/cuotas/{self.current_cuota['id']}/pagar"
            print(f"Realizando petición PUT a: {url}")
            
            # Enviar monto_pagado como parámetro de consulta (query parameter)
            params = {"monto_pagado": monto_a_pagar}
            print(f"Parámetros: {params}")
            
            response = requests.put(
                url,
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                cuota_respuesta = response.json()
                
                # Verificar si se envió el recibo por email
                if cuota_respuesta.get("email_enviado", False):
                    QMessageBox.information(
                        self, 
                        "Éxito", 
                        f"Pago registrado exitosamente.\nRecibo enviado por email a {cuota_respuesta.get('email_destinatario')}"
                    )
                else:
                    # Si no se envió el recibo, dar la opción de enviarlo manualmente
                    usuario_id = self.current_cuota.get('usuario_id')
                    if not usuario_id and isinstance(self.current_cuota.get('usuario'), dict):
                        usuario_id = self.current_cuota.get('usuario', {}).get('id')
                    
                    if usuario_id:
                        usuario_nombre = None
                        usuario_email = None
                        
                        # Buscar el nombre y email del usuario
                        for usuario in self.usuarios:
                            if usuario.get('id') == usuario_id:
                                usuario_nombre = usuario.get('nombre')
                                usuario_email = usuario.get('email')
                                break
                        
                        if usuario_email:
                            respuesta = QMessageBox.question(
                                self,
                                "Enviar Recibo",
                                f"¿Desea enviar el recibo al email de {usuario_nombre} ({usuario_email})?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes
                            )
                            
                            if respuesta == QMessageBox.Yes:
                                self.enviar_recibo_manualmente(cuota_respuesta.get("id"), usuario_email)
                        else:
                            QMessageBox.information(
                                self, 
                                "Éxito", 
                                "Pago registrado exitosamente.\nNo se pudo enviar el recibo por email porque el socio no tiene email registrado."
                            )
                    else:
                        QMessageBox.information(self, "Éxito", "Pago registrado exitosamente.")
                
                # Actualizar vista
                if hasattr(self, 'on_buscar_cuotas_usuario') and hasattr(self, 'usuario_search_combo'):
                    # Si estamos usando la nueva interfaz de búsqueda por usuario
                    self.on_buscar_cuotas_usuario()
                else:
                    # Si seguimos usando la búsqueda por ID
                    self.on_buscar_cuota_id()
                    
                self.on_buscar_cuotas()  # Actualizar lista general de cuotas
                
            else:
                error_msg = "Error al registrar el pago"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                print(f"Error al registrar pago de cuota: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar pago: {str(e)}")

    # Añadir esta función para enviar recibos manualmente
    def enviar_recibo_manualmente(self, cuota_id, email):
        """Envía un recibo manualmente usando la API"""
        try:
            # Enviar solicitud para reenviar recibo
            headers = session.get_headers()
            
            url = f"{session.api_url}/cuotas/{cuota_id}/reenviar-recibo"
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
    
    def cargar_usuarios(self):
        """Carga la lista de usuarios desde la API"""
        try:
            # Verificar que haya token antes de hacer la petición
            if not session.token:
                print("No hay token de sesión para cargar usuarios")
                return
                
            headers = session.get_headers()
            url = f"{session.api_url}/usuarios"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                self.usuarios = response.json()
                print(f"Usuarios cargados: {len(self.usuarios)}")
                
                # Actualizar combo box principal - con texto de depuración
                self.arbitro_combo.clear()
                print("Limpiado ComboBox")
                for usuario in self.usuarios:
                    self.arbitro_combo.addItem(f"{usuario['nombre']}", usuario['id'])
                    print(f"Añadido usuario: {usuario['nombre']}")
                
                # Verificar estado del checkbox para habilitar/deshabilitar combo
                self.arbitro_combo.setEnabled(not self.todos_usuarios_check.isChecked())
                print(f"Estado de habilitado del ComboBox: {self.arbitro_combo.isEnabled()}")
                
                # Actualizar combo box de filtro
                self.arbitro_filtro_combo.clear()
                self.arbitro_filtro_combo.addItem("Todos", 0)
                for usuario in self.usuarios:
                    self.arbitro_filtro_combo.addItem(f"{usuario['nombre']}", usuario['id'])
                    
                # Actualizar combo de búsqueda de la pestaña pagar
                self.usuario_search_combo.clear()
                for usuario in self.usuarios:
                    self.usuario_search_combo.addItem(f"{usuario['nombre']}", usuario['id'])
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron cargar los usuarios. Status code: {response.status_code}")
                print(f"Error al cargar usuarios: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar usuarios: {str(e)}")
            print(f"Excepción en cargar_usuarios: {str(e)}")

    def on_buscar_cuotas_usuario(self):
        """Busca cuotas según el usuario seleccionado"""
        # Verificar si se seleccionó un usuario
        if self.usuario_search_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Por favor seleccione un árbitro")
            return
        
        # Obtener ID del usuario seleccionado
        usuario_id = self.usuario_search_combo.currentData()
        usuario_nombre = self.usuario_search_combo.currentText()
        
        try:
            # Construir la URL
            url = f"{session.api_url}/cuotas/usuario/{usuario_id}"
            headers = session.get_headers()
            
            print(f"Buscando cuotas para usuario {usuario_id}: {usuario_nombre}")
            
            # Realizar la petición
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Procesar los resultados
                cuotas_data = response.json()
                print(f"Cuotas encontradas: {len(cuotas_data)}")
                
                # Limpiar la tabla
                self.cuotas_usuario_table.setRowCount(0)
                
                # Llenar la tabla con los resultados
                for row, cuota in enumerate(cuotas_data):
                    self.cuotas_usuario_table.insertRow(row)
                    
                    # ID
                    self.cuotas_usuario_table.setItem(row, 0, QTableWidgetItem(str(cuota.get("id", ""))))
                    
                    # Fecha
                    fecha_str = cuota.get('fecha', '')
                    fecha_display = ""
                    if fecha_str:
                        try:
                            fecha_display = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except:
                            fecha_display = fecha_str
                    
                    self.cuotas_usuario_table.setItem(row, 1, QTableWidgetItem(fecha_display))
                    
                    # Monto
                    monto = cuota.get("monto", 0)
                    monto_item = QTableWidgetItem(f"${monto:,.2f}")
                    monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.cuotas_usuario_table.setItem(row, 2, monto_item)
                    
                    # Estado
                    pagado = cuota.get("pagado", False)
                    estado = "Pagada" if pagado else "Pendiente"
                    estado_item = QTableWidgetItem(estado)
                    if not pagado:
                        estado_item.setForeground(Qt.red)
                    else:
                        estado_item.setForeground(Qt.darkGreen)
                    
                    self.cuotas_usuario_table.setItem(row, 3, estado_item)
                    
                    # Monto Pagado
                    monto_pagado = cuota.get("monto_pagado", 0)
                    monto_pagado_item = QTableWidgetItem(f"${monto_pagado:,.2f}")
                    monto_pagado_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.cuotas_usuario_table.setItem(row, 4, monto_pagado_item)
                
                # Ajustar columnas
                self.cuotas_usuario_table.resizeColumnsToContents()
                
                # Ocultar el detalle hasta que se seleccione una cuota específica
                self.resultado_container.setVisible(False)
            else:
                error_msg = "No se pudieron cargar las cuotas"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.warning(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                print(f"Error al cargar cuotas por usuario: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al buscar cuotas: {str(e)}")

    def on_seleccionar_cuota(self, index):
        """Maneja el evento de seleccionar una cuota de la tabla"""
        row = index.row()
        cuota_id = self.cuotas_usuario_table.item(row, 0).text()
        
        try:
            # Obtener cuota por ID
            headers = session.get_headers()
            url = f"{session.api_url}/cuotas/{cuota_id}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                cuota = response.json()
                self.current_cuota = cuota  # Guardar para referencia
                
                # Mostrar detalles
                self.resultado_title.setVisible(True)
                self.resultado_container.setVisible(True)
                
                # Formatear fecha
                fecha = datetime.strptime(cuota.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if cuota.get('fecha') else ''
                
                # Asignar valores a los labels
                self.id_label.setText(f"<b>ID de la Cuota:</b> {cuota.get('id')}")
                self.fecha_label.setText(f"<b>Fecha:</b> {fecha}")
                self.arbitro_label.setText(f"<b>Árbitro:</b> {cuota.get('usuario', {}).get('nombre', '') if cuota.get('usuario') else 'No asignado'}")
                self.monto_label.setText(f"<b>Monto:</b> ${cuota.get('monto', 0):,.2f}")
                
                pagado = cuota.get("pagado", False)
                estado_text = "Pagada" if pagado else "Pendiente"
                estado_color = "green" if pagado else "red"
                
                self.estado_label.setText(f"<b>Estado:</b> <span style='color:{estado_color};'>{estado_text}</span>")
                self.monto_pagado_label.setText(f"<b>Monto Pagado:</b> ${cuota.get('monto_pagado', 0):,.2f}")
                
                # Mostrar u ocultar formulario de pago según estado
                self.pago_form.setVisible(not pagado)
                
                if not pagado:
                    # Configurar monto por defecto (lo que falta por pagar)
                    monto_restante = cuota.get('monto', 0) - cuota.get('monto_pagado', 0)
                    self.monto_a_pagar_spin.setMaximum(monto_restante)
                    self.monto_a_pagar_spin.setValue(monto_restante)
            else:
                self.resultado_container.setVisible(False)
                QMessageBox.warning(self, "Error", f"No se pudo obtener la información de la cuota. Status code: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al seleccionar cuota: {str(e)}")

