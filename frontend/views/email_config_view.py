
import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFormLayout, 
    QLineEdit, QSpinBox, QMessageBox, QCheckBox, QInputDialog
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal

import requests
import json
from sesion import session

class EmailConfigView(QWidget):
    navigation_requested = Signal(str)  # Señal para solicitar navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.config_id = None
    
    def initialize_view(self):
        """
        Método para inicializar la vista después del login.
        Debe ser llamado explícitamente después de establecer la sesión.
        """
        # Verificar permisos
        if not self.check_user_permissions():
            # Si no tiene permisos, emitir señal para volver al dashboard
            self.navigation_requested.emit("dashboard")
        else:
            # Si tiene permisos, cargar la configuración
            self.load_config()
    
    def check_user_permissions(self):
        """Verificar si el usuario tiene permisos de admin o tesorero"""
        try:
            # Obtener el rol del usuario desde la sesión
            user_info = session.user_info
            
            # Verificar si el rol es admin o tesorero
            if user_info.get('rol', '').lower() not in ['admin', 'tesorero']:
                QMessageBox.warning(
                    self, 
                    "Acceso Denegado", 
                    "No tienes permisos para acceder a la configuración de email. Solo administradores y tesoreros pueden hacerlo."
                )
                return False
            return True
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error al verificar permisos: {str(e)}"
            )
            return False

    def go_to_dashboard(self):
        """Va directamente al dashboard"""
        self.navigation_requested.emit("dashboard")

    def showEvent(self, event):
        """Se ejecuta cuando el widget se hace visible"""
        super().showEvent(event)
        # Verificar permisos al mostrar
        if self.check_user_permissions():
            self.load_config()
    
    def setup_ui(self):
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Layout para botones de navegación
        buttons_layout = QHBoxLayout()
        
        # Botón para volver al Dashboard
        self.dashboard_button = QPushButton("Volver al Dashboard")
        self.dashboard_button.clicked.connect(self.go_to_dashboard)
        
        # Título
        title_label = QLabel("Configuración de Email para Recibos")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Descripción
        desc_label = QLabel("Configure los parámetros SMTP para el envío automático de recibos por email.")
        desc_label.setWordWrap(True)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Servidor SMTP
        self.smtp_server_edit = QLineEdit()
        self.smtp_server_edit.setPlaceholderText("smtp.gmail.com")
        form_layout.addRow("Servidor SMTP:", self.smtp_server_edit)
        
        # Puerto SMTP
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)  # Puerto por defecto para TLS
        form_layout.addRow("Puerto SMTP:", self.smtp_port_spin)
        
        # Usuario SMTP
        self.smtp_username_edit = QLineEdit()
        self.smtp_username_edit.setPlaceholderText("tu.email@gmail.com")
        form_layout.addRow("Usuario SMTP:", self.smtp_username_edit)
        
        # Contraseña SMTP
        self.smtp_password_edit = QLineEdit()
        self.smtp_password_edit.setEchoMode(QLineEdit.Password)
        self.smtp_password_edit.setPlaceholderText("Contraseña o clave de aplicación")
        form_layout.addRow("Contraseña SMTP:", self.smtp_password_edit)
        
        # Email Remitente
        self.email_from_edit = QLineEdit()
        self.email_from_edit.setPlaceholderText("Unidad de Árbitros <tu.email@gmail.com>")
        form_layout.addRow("Email Remitente:", self.email_from_edit)
        
        # Activo
        self.is_active_check = QCheckBox("Configuración Activa")
        self.is_active_check.setChecked(True)
        form_layout.addRow("", self.is_active_check)
        
        # Ayuda para Gmail
        help_label = QLabel("Nota: Si usas Gmail, deberás usar una 'Contraseña de aplicación'. Ve a tu cuenta de Google → Seguridad → Verificación en dos pasos → Contraseñas de aplicación.")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-style: italic;")
        
        # Botones de acción
        action_buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Guardar Configuración")
        self.save_btn.clicked.connect(self.on_save_config)
        
        self.test_btn = QPushButton("Probar Configuración")
        self.test_btn.clicked.connect(self.on_test_config)
        
        action_buttons_layout.addWidget(self.save_btn)
        action_buttons_layout.addWidget(self.test_btn)
        
        # Añadir al layout principal
        self.main_layout.addWidget(self.dashboard_button)
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(desc_label)
        self.main_layout.addLayout(form_layout)
        self.main_layout.addWidget(help_label)
        self.main_layout.addLayout(action_buttons_layout)
        
        # Espaciado adicional
        self.main_layout.addStretch()
    
    def load_config(self):
        """Carga la configuración de email activa desde la API"""
        try:
            headers = session.get_headers()
            url = f"{session.api_url}/email-config/active"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                config = response.json()
                self.config_id = config.get("id")
                
                # Llenar formulario
                self.smtp_server_edit.setText(config.get("smtp_server", ""))
                self.smtp_port_spin.setValue(config.get("smtp_port", 587))
                self.smtp_username_edit.setText(config.get("smtp_username", ""))
                # No llenamos la contraseña por seguridad
                self.email_from_edit.setText(config.get("email_from", ""))
                self.is_active_check.setChecked(config.get("is_active", True))
                
                print(f"Configuración de email cargada (ID: {self.config_id})")
            elif response.status_code == 404:
                print("No hay configuración de email activa")
                # No mostramos mensaje, simplemente dejamos el formulario vacío
            elif response.status_code == 401:
                QMessageBox.warning(self, "Error de autenticación", "Su sesión ha expirado o no tiene permisos suficientes")
            else:
                print(f"Error al cargar configuración de email: {response.text}")
        except Exception as e:
            print(f"Excepción al cargar configuración de email: {str(e)}")
    
    def on_save_config(self):
        """Guarda la configuración de email"""
        # Validar campos
        if not self.smtp_server_edit.text().strip():
            QMessageBox.warning(self, "Error", "Por favor ingrese el servidor SMTP")
            return
        
        if not self.smtp_username_edit.text().strip():
            QMessageBox.warning(self, "Error", "Por favor ingrese el usuario SMTP")
            return
        
        if not self.email_from_edit.text().strip():
            QMessageBox.warning(self, "Error", "Por favor ingrese el email remitente")
            return
        
        # Crear objeto de configuración
        config_data = {
            "smtp_server": self.smtp_server_edit.text().strip(),
            "smtp_port": self.smtp_port_spin.value(),
            "smtp_username": self.smtp_username_edit.text().strip(),
            "email_from": self.email_from_edit.text().strip(),
            "is_active": self.is_active_check.isChecked()
        }
        
        # Agregar contraseña solo si se ha proporcionado una nueva
        if self.smtp_password_edit.text():
            config_data["smtp_password"] = self.smtp_password_edit.text()
        
        try:
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            # Determinar si es una actualización o creación
            if self.config_id:
                url = f"{session.api_url}/email-config/{self.config_id}"
                response = requests.put(url, headers=headers, json=config_data)
            else:
                # Si no hay contraseña y es una creación, mostrar error
                if not self.smtp_password_edit.text():
                    QMessageBox.warning(self, "Error", "Por favor ingrese una contraseña")
                    return
                    
                url = f"{session.api_url}/email-config/"
                response = requests.post(url, headers=headers, json=config_data)
            
            if response.status_code in [200, 201]:
                QMessageBox.information(self, "Éxito", "Configuración de email guardada exitosamente")
                
                # Actualizar config_id si es una creación
                if not self.config_id:
                    result = response.json()
                    self.config_id = result.get("id")
                
                # Limpiar campo de contraseña
                self.smtp_password_edit.clear()
            else:
                error_msg = "Error al guardar la configuración"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
                print(f"Error al guardar configuración: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar configuración: {str(e)}")
    
    def on_test_config(self):
        """Prueba la configuración de email enviando un correo de prueba"""
        # Validar que haya una configuración guardada
        if not self.config_id:
            QMessageBox.warning(self, "Advertencia", "Debe guardar la configuración antes de probarla")
            return
        
        try:
            # Pedir email para la prueba
            email_test, ok = QInputDialog.getText(
                self, 
                "Probar Email", 
                "Ingrese email para la prueba:"
            )
            
            if not ok or not email_test:
                return
            
            # Enviar solicitud de prueba
            url = f"{session.api_url}/email-test"
            headers = session.get_headers()
            
            response = requests.post(
                url, 
                headers=headers,
                params={"email": email_test}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success", False):
                    QMessageBox.information(self, "Éxito", "Email de prueba enviado exitosamente")
                else:
                    QMessageBox.warning(self, "Advertencia", f"No se pudo enviar el email de prueba: {result.get('message', '')}")
            else:
                error_msg = "Error al enviar email de prueba"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(self, "Error", f"{error_msg}. Status code: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al probar configuración: {str(e)}")