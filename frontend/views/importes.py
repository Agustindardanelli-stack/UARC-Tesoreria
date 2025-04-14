import os
import sys
from datetime import datetime
import pandas as pd
import requests
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QFrame, QTabWidget, QSpacerItem, QSizePolicy,
    QFormLayout, QLineEdit, QMessageBox, QDoubleSpinBox, QCheckBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal

from views.dashboard import SidebarWidget
from sesion import session

class ImportesView(QWidget):
    navigation_requested = Signal(str)  # Señal para solicitar navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
        self.retenciones = []
        self.categorias = []
        
        
    
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
        title_label = QLabel("Gestión de Importes")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.content_layout.addWidget(title_label)
        
        # Tabs para las diferentes secciones
        self.tabs = QTabWidget()
        
        # Tab 1: Retenciones
        self.tab_retenciones = QWidget()
        self.setup_tab_retenciones()
        self.tabs.addTab(self.tab_retenciones, "Retenciones")
        
        # Tab 2: Categorías
        self.tab_categorias = QWidget()
        self.setup_tab_categorias()
        self.tabs.addTab(self.tab_categorias, "Categorías")
        
        self.content_layout.addWidget(self.tabs)
        
        # Agregar al layout principal
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_widget)
    
    def setup_tab_retenciones(self):
        layout = QHBoxLayout(self.tab_retenciones)
        
        # Panel izquierdo (lista de retenciones)
        self.retenciones_panel = QWidget()
        retenciones_layout = QVBoxLayout(self.retenciones_panel)
        
        # Título
        retenciones_title = QLabel("Retenciones Existentes")
        title_font = QFont()
        title_font.setPointSize(16)
        retenciones_title.setFont(title_font)
        retenciones_layout.addWidget(retenciones_title)
        
        # Tabla de retenciones
        self.retenciones_table = QTableWidget()
        self.retenciones_table.setColumnCount(3)
        self.retenciones_table.setHorizontalHeaderLabels(["ID", "Nombre", "Monto"])
        self.retenciones_table.horizontalHeader().setStretchLastSection(True)
        self.retenciones_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.retenciones_table.setAlternatingRowColors(True)
        self.retenciones_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.retenciones_table.setSelectionMode(QTableWidget.SingleSelection)
        self.retenciones_table.itemSelectionChanged.connect(self.on_retencion_selected)
        
        retenciones_layout.addWidget(self.retenciones_table)
        
        # Panel derecho (formularios)
        self.forms_panel = QWidget()
        forms_layout = QVBoxLayout(self.forms_panel)
        
        # Formulario para nueva retención
        self.new_retencion_form = QWidget()
        new_retencion_layout = QVBoxLayout(self.new_retencion_form)
        
        new_title = QLabel("Agregar Retención")
        new_title.setFont(title_font)
        new_retencion_layout.addWidget(new_title)
        
        new_form = QFormLayout()
        
        self.retencion_nombre_edit = QLineEdit()
        self.retencion_nombre_edit.setPlaceholderText("Nombre de la retención")
        new_form.addRow("Nombre:", self.retencion_nombre_edit)
        
        self.retencion_monto_spin = QDoubleSpinBox()
        self.retencion_monto_spin.setRange(0, 999999.99)
        self.retencion_monto_spin.setSingleStep(100)
        self.retencion_monto_spin.setPrefix("$ ")
        self.retencion_monto_spin.setDecimals(2)
        new_form.addRow("Monto:", self.retencion_monto_spin)
        
        self.retencion_save_btn = QPushButton("Guardar")
        self.retencion_save_btn.clicked.connect(self.on_guardar_retencion)
        
        new_retencion_layout.addLayout(new_form)
        new_retencion_layout.addWidget(self.retencion_save_btn)
        
        # Formulario para editar/eliminar retención
        self.edit_retencion_form = QWidget()
        edit_retencion_layout = QVBoxLayout(self.edit_retencion_form)
        
        edit_title = QLabel("Editar/Eliminar Retención")
        edit_title.setFont(title_font)
        edit_retencion_layout.addWidget(edit_title)
        
        self.retencion_id_label = QLabel()
        edit_retencion_layout.addWidget(self.retencion_id_label)
        
        edit_form = QFormLayout()
        
        self.retencion_nombre_edit_existing = QLineEdit()
        edit_form.addRow("Nombre:", self.retencion_nombre_edit_existing)
        
        self.retencion_monto_spin_existing = QDoubleSpinBox()
        self.retencion_monto_spin_existing.setRange(0, 999999.99)
        self.retencion_monto_spin_existing.setSingleStep(100)
        self.retencion_monto_spin_existing.setPrefix("$ ")
        self.retencion_monto_spin_existing.setDecimals(2)
        edit_form.addRow("Monto:", self.retencion_monto_spin_existing)
        
        buttons_layout = QHBoxLayout()
        
        self.retencion_update_btn = QPushButton("Actualizar")
        self.retencion_update_btn.clicked.connect(self.on_actualizar_retencion)
        
        self.retencion_delete_btn = QPushButton("Eliminar")
        self.retencion_delete_btn.clicked.connect(self.on_eliminar_retencion)
        self.retencion_delete_btn.setStyleSheet("background-color: #d9534f; color: white;")
        
        buttons_layout.addWidget(self.retencion_update_btn)
        buttons_layout.addWidget(self.retencion_delete_btn)
        
        edit_retencion_layout.addLayout(edit_form)
        edit_retencion_layout.addLayout(buttons_layout)
        
        # Inicialmente ocultar el formulario de edición
        self.edit_retencion_form.setVisible(False)
        
        # Agregar formularios al panel derecho
        forms_layout.addWidget(self.new_retencion_form)
        forms_layout.addWidget(self.edit_retencion_form)
        forms_layout.addStretch()
        
        # Agregar paneles al layout principal de la pestaña
        layout.addWidget(self.retenciones_panel, 2)  # Proporción 2/3
        layout.addWidget(self.forms_panel, 1)        # Proporción 1/3
    
    def setup_tab_categorias(self):
        layout = QHBoxLayout(self.tab_categorias)
        
        # Panel izquierdo (lista de categorías)
        self.categorias_panel = QWidget()
        categorias_layout = QVBoxLayout(self.categorias_panel)
        
        # Título
        categorias_title = QLabel("Categorías Existentes")
        title_font = QFont()
        title_font.setPointSize(16)
        categorias_title.setFont(title_font)
        categorias_layout.addWidget(categorias_title)
        
        # Tabla de categorías
        self.categorias_table = QTableWidget()
        self.categorias_table.setColumnCount(2)
        self.categorias_table.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.categorias_table.horizontalHeader().setStretchLastSection(True)
        self.categorias_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.categorias_table.setAlternatingRowColors(True)
        self.categorias_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.categorias_table.setSelectionMode(QTableWidget.SingleSelection)
        self.categorias_table.itemSelectionChanged.connect(self.on_categoria_selected)
        
        categorias_layout.addWidget(self.categorias_table)
        
        # Panel derecho (formularios)
        self.cat_forms_panel = QWidget()
        cat_forms_layout = QVBoxLayout(self.cat_forms_panel)
        
        # Formulario para nueva categoría
        self.new_categoria_form = QWidget()
        new_categoria_layout = QVBoxLayout(self.new_categoria_form)
        
        new_cat_title = QLabel("Agregar Categoría")
        new_cat_title.setFont(title_font)
        new_categoria_layout.addWidget(new_cat_title)
        
        new_cat_form = QFormLayout()
        
        self.categoria_nombre_edit = QLineEdit()
        self.categoria_nombre_edit.setPlaceholderText("Nombre de la categoría")
        new_cat_form.addRow("Nombre:", self.categoria_nombre_edit)
        
        self.categoria_save_btn = QPushButton("Guardar")
        self.categoria_save_btn.clicked.connect(self.on_guardar_categoria)
        
        new_categoria_layout.addLayout(new_cat_form)
        new_categoria_layout.addWidget(self.categoria_save_btn)
        
        # Formulario para editar/eliminar categoría
        self.edit_categoria_form = QWidget()
        edit_categoria_layout = QVBoxLayout(self.edit_categoria_form)
        
        edit_cat_title = QLabel("Editar/Eliminar Categoría")
        edit_cat_title.setFont(title_font)
        edit_categoria_layout.addWidget(edit_cat_title)
        
        self.categoria_id_label = QLabel()
        edit_categoria_layout.addWidget(self.categoria_id_label)
        
        edit_cat_form = QFormLayout()
        
        self.categoria_nombre_edit_existing = QLineEdit()
        edit_cat_form.addRow("Nombre:", self.categoria_nombre_edit_existing)
        
        cat_buttons_layout = QHBoxLayout()
        
        self.categoria_update_btn = QPushButton("Actualizar")
        self.categoria_update_btn.clicked.connect(self.on_actualizar_categoria)
        
        self.categoria_delete_btn = QPushButton("Eliminar")
        self.categoria_delete_btn.clicked.connect(self.on_eliminar_categoria)
        self.categoria_delete_btn.setStyleSheet("background-color: #d9534f; color: white;")
        
        cat_buttons_layout.addWidget(self.categoria_update_btn)
        cat_buttons_layout.addWidget(self.categoria_delete_btn)
        
        edit_categoria_layout.addLayout(edit_cat_form)
        edit_categoria_layout.addLayout(cat_buttons_layout)
        
        # Inicialmente ocultar el formulario de edición
        self.edit_categoria_form.setVisible(False)
        
        # Agregar formularios al panel derecho
        cat_forms_layout.addWidget(self.new_categoria_form)
        cat_forms_layout.addWidget(self.edit_categoria_form)
        cat_forms_layout.addStretch()
        
        # Agregar paneles al layout principal de la pestaña
        layout.addWidget(self.categorias_panel, 2)  # Proporción 2/3
        layout.addWidget(self.cat_forms_panel, 1)   # Proporción 1/3
    
    def connect_signals(self):
        self.sidebar.navigation_requested.connect(self.navigation_requested)
    
    def refresh_data(self):
        """Carga los datos iniciales"""
        self.cargar_retenciones()
        self.cargar_categorias()
    
    def cargar_retenciones(self):
        """Carga la lista de retenciones desde la API"""
        try:
            # Verificar que haya token antes de hacer la petición
            if not session.token:
                print("No hay token de sesión para cargar retenciones")
                return
                
            headers = session.get_headers()
            
            # Asegúrate de que la URL coincida con la del backend
            response = requests.get(f"{session.api_url}/retenciones", headers=headers)
            
            if response.status_code == 200:
                self.retenciones = response.json()
                
                # Limpiar tabla
                self.retenciones_table.setRowCount(0)
                
                # Llenar tabla con datos
                for row, retencion in enumerate(self.retenciones):
                    self.retenciones_table.insertRow(row)
                    
                    # ID
                    self.retenciones_table.setItem(row, 0, QTableWidgetItem(str(retencion.get("id", ""))))
                    
                    # Nombre
                    self.retenciones_table.setItem(row, 1, QTableWidgetItem(retencion.get("nombre", "")))
                    
                    # Monto
                    monto = retencion.get("monto", 0)
                    monto_item = QTableWidgetItem(f"${monto:,.2f}")
                    monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.retenciones_table.setItem(row, 2, monto_item)
                
                # Ajustar columnas
                self.retenciones_table.resizeColumnsToContents()
            else:
                print(f"Error al cargar retenciones: {response.status_code} - {response.text}")
                QMessageBox.warning(self, "Error", f"No se pudieron cargar las retenciones. Status code: {response.status_code}")
        except Exception as e:
            print(f"Excepción al cargar retenciones: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al cargar retenciones: {str(e)}")
        
    def cargar_categorias(self):
        """Carga la lista de categorías desde la API"""
        try:
            # Verificar que haya token antes de hacer la petición
            if not session.token:
                print("No hay token de sesión para cargar categorías")
                return
                
            headers = session.get_headers()
            response = requests.get(f"{session.api_url}/categorias", headers=headers)
            
            if response.status_code == 200:
                self.categorias = response.json()
                
                # Limpiar tabla
                self.categorias_table.setRowCount(0)
                
                # Llenar tabla con datos
                for row, categoria in enumerate(self.categorias):
                    self.categorias_table.insertRow(row)
                    
                    # ID
                    self.categorias_table.setItem(row, 0, QTableWidgetItem(str(categoria.get("id", ""))))
                    
                    # Nombre
                    self.categorias_table.setItem(row, 1, QTableWidgetItem(categoria.get("nombre", "")))
                
                # Ajustar columnas
                self.categorias_table.resizeColumnsToContents()
            else:
                QMessageBox.warning(self, "Error", "No se pudieron cargar las categorías")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar categorías: {str(e)}")
    
    def on_retencion_selected(self):
        """Maneja la selección de una retención en la tabla"""
        selected_items = self.retenciones_table.selectedItems()
        if selected_items:
            # Obtener el ID de la fila seleccionada (primera columna)
            row = selected_items[0].row()
            retencion_id = int(self.retenciones_table.item(row, 0).text())
            
            # Encontrar la retención correspondiente
            retencion = next((r for r in self.retenciones if r["id"] == retencion_id), None)
            
            if retencion:
                # Mostrar formulario de edición
                self.edit_retencion_form.setVisible(True)
                
                # Actualizar campos
                self.retencion_id_label.setText(f"<b>ID:</b> {retencion['id']}")
                self.retencion_nombre_edit_existing.setText(retencion["nombre"])
                self.retencion_monto_spin_existing.setValue(retencion["monto"])
        else:
            # Ocultar formulario de edición si no hay selección
            self.edit_retencion_form.setVisible(False)
    
    def on_categoria_selected(self):
        """Maneja la selección de una categoría en la tabla"""
        selected_items = self.categorias_table.selectedItems()
        if selected_items:
            # Obtener el ID de la fila seleccionada (primera columna)
            row = selected_items[0].row()
            categoria_id = int(self.categorias_table.item(row, 0).text())
            
            # Encontrar la categoría correspondiente
            categoria = next((c for c in self.categorias if c["id"] == categoria_id), None)
            
            if categoria:
                # Mostrar formulario de edición
                self.edit_categoria_form.setVisible(True)
                
                # Actualizar campos
                self.categoria_id_label.setText(f"<b>ID:</b> {categoria['id']}")
                self.categoria_nombre_edit_existing.setText(categoria["nombre"])
        else:
            # Ocultar formulario de edición si no hay selección
            self.edit_categoria_form.setVisible(False)
    
    def on_guardar_retencion(self):
        """Guarda una nueva retención"""
        nombre = self.retencion_nombre_edit.text().strip()
        monto = self.retencion_monto_spin.value()
        
        if not nombre:
            QMessageBox.warning(self, "Error", "Por favor ingrese un nombre")
            return
        
        if monto <= 0:
            QMessageBox.warning(self, "Error", "El monto debe ser mayor a cero")
            return
        
        # Crear objeto de retención
        retencion_data = {
            "nombre": nombre,
            "monto": monto
        }
        
        try:
            # Enviar solicitud para crear retención
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            # Usar /retenciones/ con la barra al final para mayor compatibilidad
            response = requests.post(
                f"{session.api_url}/retenciones/",
                headers=headers,
                json=retencion_data  # Usar json en lugar de data con json.dumps
            )
            
            if response.status_code == 200 or response.status_code == 201:
                QMessageBox.information(self, "Éxito", "Retención guardada exitosamente")
                
                # Limpiar formulario
                self.retencion_nombre_edit.clear()
                self.retencion_monto_spin.setValue(0)
                
                # Actualizar lista de retenciones
                self.cargar_retenciones()
            else:
                error_msg = "Error al guardar la retención"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                print(f"Error al guardar retención: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar retención: {str(e)}")
    
    def on_actualizar_retencion(self):
        """Actualiza una retención existente"""
        selected_items = self.retenciones_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Por favor seleccione una retención")
            return
        
        # Obtener el ID de la fila seleccionada
        row = selected_items[0].row()
        retencion_id = int(self.retenciones_table.item(row, 0).text())
        
        nombre = self.retencion_nombre_edit_existing.text().strip()
        monto = self.retencion_monto_spin_existing.value()
        
        if not nombre:
            QMessageBox.warning(self, "Error", "Por favor ingrese un nombre")
            return
        
        if monto <= 0:
            QMessageBox.warning(self, "Error", "El monto debe ser mayor a cero")
            return
        
        # Crear objeto de actualización
        retencion_data = {
            "nombre": nombre,
            "monto": monto
        }
        
        try:
            # Enviar solicitud para actualizar retención
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            response = requests.put(
                f"{session.api_url}/retenciones/{retencion_id}",
                headers=headers,
                data=json.dumps(retencion_data)
            )
            
            if response.status_code == 200:
                QMessageBox.information(self, "Éxito", "Retención actualizada exitosamente")
                
                # Actualizar lista de retenciones
                self.cargar_retenciones()
                
                # Limpiar selección
                self.retenciones_table.clearSelection()
                self.edit_retencion_form.setVisible(False)
            else:
                error_msg = "Error al actualizar la retención"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar retención: {str(e)}")
    
    def on_eliminar_retencion(self):
        """Elimina una retención existente"""
        selected_items = self.retenciones_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Por favor seleccione una retención")
            return
        
        # Obtener el ID de la fila seleccionada
        row = selected_items[0].row()
        retencion_id = int(self.retenciones_table.item(row, 0).text())
        retencion_nombre = self.retenciones_table.item(row, 1).text()
        
        # Confirmar eliminación
        confirm = QMessageBox.question(
            self, 
            "Confirmar eliminación", 
            f"¿Está seguro de eliminar la retención '{retencion_nombre}'?\n\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                # Enviar solicitud para eliminar retención
                headers = session.get_headers()
                
                response = requests.delete(
                    f"{session.api_url}/retenciones/{retencion_id}",
                    headers=headers
)
                
                if response.status_code == 200:
                    QMessageBox.information(self, "Éxito", "Retención eliminada correctamente")
                    
                    # Actualizar lista de retenciones
                    self.cargar_retenciones()
                    
                    # Limpiar selección
                    self.retenciones_table.clearSelection()
                    self.edit_retencion_form.setVisible(False)
                else:
                    error_msg = "Error al eliminar la retención"
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            error_msg = error_data["detail"]
                    except:
                        pass
                    QMessageBox.critical(self, "Error", error_msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar retención: {str(e)}")
    
    def on_guardar_categoria(self):
        """Guarda una nueva categoría"""
        nombre = self.categoria_nombre_edit.text().strip()
        
        if not nombre:
            QMessageBox.warning(self, "Error", "Por favor ingrese un nombre")
            return
        
        # Crear objeto de categoría
        categoria_data = {
            "nombre": nombre
        }
        
        try:
            # Enviar solicitud para crear categoría
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            # Quitar barra al final para mantener consistencia con el backend
            response = requests.post(
                f"{session.api_url}/categorias",
                headers=headers,
                json=categoria_data  # Usar json en lugar de data con json.dumps
            )
            
            if response.status_code == 200 or response.status_code == 201:
                QMessageBox.information(self, "Éxito", "Categoría guardada exitosamente")
                
                # Limpiar formulario
                self.categoria_nombre_edit.clear()
                
                # Actualizar lista de categorías
                self.cargar_categorias()
            else:
                error_msg = "Error al guardar la categoría"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                print(f"Error al guardar categoría: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar categoría: {str(e)}")
    
    def on_actualizar_categoria(self):
        """Actualiza una categoría existente"""
        selected_items = self.categorias_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Por favor seleccione una categoría")
            return
        
        # Obtener el ID de la fila seleccionada
        row = selected_items[0].row()
        categoria_id = int(self.categorias_table.item(row, 0).text())
        
        nombre = self.categoria_nombre_edit_existing.text().strip()
        
        if not nombre:
            QMessageBox.warning(self, "Error", "Por favor ingrese un nombre")
            return
        
        # Crear objeto de actualización
        categoria_data = {
            "nombre": nombre
        }
        
        try:
            # Enviar solicitud para actualizar categoría
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            response = requests.put(
                f"{session.api_url}/categorias/{categoria_id}",
                headers=headers,
                data=json.dumps(categoria_data)
            )
            
            if response.status_code == 200:
                QMessageBox.information(self, "Éxito", "Categoría actualizada exitosamente")
                
                # Actualizar lista de categorías
                self.cargar_categorias()
                
                # Limpiar selección
                self.categorias_table.clearSelection()
                self.edit_categoria_form.setVisible(False)
            else:
                error_msg = "Error al actualizar la categoría"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar categoría: {str(e)}")
    
    def on_eliminar_categoria(self):
        """Elimina una categoría existente"""
        selected_items = self.categorias_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Por favor seleccione una categoría")
            return
        
        # Obtener el ID de la fila seleccionada
        row = selected_items[0].row()
        categoria_id = int(self.categorias_table.item(row, 0).text())
        categoria_nombre = self.categorias_table.item(row, 1).text()
        
        # Confirmar eliminación
        confirm = QMessageBox.question(
            self, 
            "Confirmar eliminación", 
            f"¿Está seguro de eliminar la categoría '{categoria_nombre}'?\n\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                # Enviar solicitud para eliminar categoría
                headers = session.get_headers()
                
                response = requests.delete(
                    f"{session.api_url}/categorias/{categoria_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    QMessageBox.information(self, "Éxito", "Categoría eliminada correctamente")
                    
                    # Actualizar lista de categorías
                    self.cargar_categorias()
                    
                    # Limpiar selección
                    self.categorias_table.clearSelection()
                    self.edit_categoria_form.setVisible(False)
                else:
                    error_msg = "Error al eliminar la categoría"
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            error_msg = error_data["detail"]
                    except:
                        pass
                    QMessageBox.critical(self, "Error", error_msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar categoría: {str(e)}")