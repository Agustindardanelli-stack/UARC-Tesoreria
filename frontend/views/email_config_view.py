import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFormLayout, 
    QLineEdit, QSpinBox, QMessageBox, QCheckBox, QInputDialog, QGroupBox
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
        desc_label = QLabel("El sistema utiliza Brevo para el envío automático de recibos por email.")
        desc_label.setWordWrap(True)
        
        # Grupo de información del sistema
        info_group = QGroupBox("Estado del Sistema")
        info_layout = QVBoxLayout()
        
        # Estado Brevo
        self.status_label = QLabel("✅ Brevo API configurada en el servidor")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        info_layout.addWidget(self.status_label)
        
        # Información adicional
        info_text = QLabel(
            "La configuración de Brevo se gestiona mediante variables de entorno en el servidor.\n"
            "No es necesario configurar SMTP manualmente."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #666;")
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        
        # Formulario simplificado
        form_group = QGroupBox("Configuración de Email")
        form_layout = QFormLayout()
        
        # Email Remitente (editable para corregir formato)
        self.email_from_edit = QLineEdit()
        self.email_from_edit.setPlaceholderText("unidadarbitrosriocuarto@gmail.com")
        self.email_from_edit.setReadOnly(False)  # Permitir edición
        form_layout.addRow("Email Remitente (verificado en Brevo):", self.email_from_edit)
        
        # Activo
        self.is_active_check = QCheckBox("Sistema de Email Activo")
        self.is_active_check.setChecked(True)
        form_layout.addRow("", self.is_active_check)
        
        form_group.setLayout(form_layout)
        
        # Nota informativa
        help_label = QLabel(
            "ℹ️ <b>Nota importante:</b> El email remitente debe estar verificado en Brevo. "
            "Los cambios en la API Key de Brevo se realizan directamente en las variables de entorno del servidor (Render)."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px;")
        
        # Botones de acción
        action_buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Guardar Configuración")
        self.save_btn.clicked.connect(self.on_save_config)
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        
        self.test_btn = QPushButton("Probar Envío de Email")
        self.test_btn.clicked.connect(self.on_test_config)
        self.test_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-weight: bold;")
        
        action_buttons_layout.addWidget(self.save_btn)
        action_buttons_layout.addWidget(self.test_btn)
        
        # Añadir al layout principal
        self.main_layout.addWidget(self.dashboard_button)
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(desc_label)
        self.main_layout.addWidget(info_group)
        self.main_layout.addWidget(form_group)
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
                
                # Llenar formulario (solo email remitente)
                self.email_from_edit.setText(config.get("email_from", "unidadarbitrosriocuarto@gmail.com"))
                self.is_active_check.setChecked(config.get("is_active", True))
                
                print(f"Configuración de email cargada (ID: {self.config_id})")
            elif response.status_code == 404:
                print("No hay configuración de email activa")
                # Establecer valores por defecto
                self.email_from_edit.setText("unidadarbitrosriocuarto@gmail.com")
            elif response.status_code == 401:
                QMessageBox.warning(self, "Error de autenticación", "Su sesión ha expirado o no tiene permisos suficientes")
            else:
                print(f"Error al cargar configuración de email: {response.text}")
        except Exception as e:
            print(f"Excepción al cargar configuración de email: {str(e)}")
    
    def on_save_config(self):
        """Guarda la configuración de email"""
        # Validar campos
        if not self.email_from_edit.text().strip():
            QMessageBox.warning(self, "Error", "Por favor ingrese el email remitente")
            return
        
        # Limpiar email: extraer solo el email si tiene formato "Nombre <email@domain.com>"
        email_text = self.email_from_edit.text().strip()
        if '<' in email_text and '>' in email_text:
            # Extraer solo el email entre < >
            import re
            match = re.search(r'<(.+?)>', email_text)
            if match:
                email_text = match.group(1).strip()
        
        # Validar formato de email básico
        if '@' not in email_text or '.' not in email_text:
            QMessageBox.warning(self, "Error", "Por favor ingrese un email válido")
            return
        
        # Crear objeto de configuración simplificado para Brevo
        config_data = {
            "smtp_server": "brevo",  # Identificador
            "smtp_port": 587,  # Valor dummy para compatibilidad
            "smtp_username": "apikey",  # Brevo usa esto
            "smtp_password": "configured_in_env",  # La password real está en variables de entorno
            "email_from": email_text,  # Email limpio, sin formato con nombre
            "is_active": self.is_active_check.isChecked()
        }
        
        try:
            headers = session.get_headers()
            headers["Content-Type"] = "application/json"
            
            # Determinar si es una actualización o creación
            if self.config_id:
                url = f"{session.api_url}/email-config/{self.config_id}"
                response = requests.put(url, headers=headers, json=config_data)
            else:
                url = f"{session.api_url}/email-config/"
                response = requests.post(url, headers=headers, json=config_data)
            
            if response.status_code in [200, 201]:
                QMessageBox.information(
                    self, 
                    "Éxito", 
                    "Configuración de email guardada exitosamente.\n\n"
                    "El sistema utilizará Brevo para enviar los emails."
                )
                
                # Actualizar config_id si es una creación
                if not self.config_id:
                    result = response.json()
                    self.config_id = result.get("id")
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
        try:
            # Pedir email para la prueba
            email_test, ok = QInputDialog.getText(
                self, 
                "Probar Email", 
                "Ingrese el email donde desea recibir el correo de prueba:"
            )
            
            if not ok or not email_test:
                return
            
            # Validar formato de email básico
            if '@' not in email_test or '.' not in email_test:
                QMessageBox.warning(self, "Error", "Por favor ingrese un email válido")
                return
            
            # Mostrar mensaje de espera
            QMessageBox.information(
                self,
                "Enviando...",
                "Enviando email de prueba. Por favor espere..."
            )
            
            # Enviar solicitud de prueba
            url = f"{session.api_url}/email-test"
            headers = session.get_headers()
            
            response = requests.post(
                url, 
                headers=headers,
                params={"email": email_test},
                timeout=30  # Timeout de 30 segundos
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success", False):
                    QMessageBox.information(
                        self, 
                        "✅ Éxito", 
                        f"Email de prueba enviado exitosamente a:\n{email_test}\n\n"
                        "Revisa tu bandeja de entrada (y spam si no lo encuentras)."
                    )
                else:
                    QMessageBox.warning(
                        self, 
                        "Advertencia", 
                        f"No se pudo enviar el email de prueba:\n{result.get('message', 'Error desconocido')}"
                    )
            else:
                error_msg = "Error al enviar email de prueba"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"{error_msg}\n\nStatus code: {response.status_code}\n\n"
                    "Verifica que:\n"
                    "1. La API Key de Brevo esté configurada en Render\n"
                    "2. El email remitente esté verificado en Brevo"
                )
        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self,
                "Error",
                "La petición tardó demasiado tiempo. Verifica tu conexión a internet."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al probar configuración: {str(e)}")