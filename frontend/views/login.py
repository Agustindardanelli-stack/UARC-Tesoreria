import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QSpacerItem, QSizePolicy, QMessageBox
)
from PySide6.QtGui import QPixmap, QFont, QIcon
from PySide6.QtCore import Qt
from .logo_loader import load_logo

from sesion import session

class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        
        # Configurar el layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        
        # Crear contenedor central para el formulario
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignCenter)
        
        # Logotipo
        self.logo_label = QLabel()
        load_logo(self.logo_label, "UarcLogo.png", 150, 150)
        self.content_layout.addWidget(self.logo_label)
        
        # Título
        self.title_label = QLabel("Gestion Integral UARC")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.title_label)
        
        # Subtítulo
        self.subtitle_label = QLabel("Iniciar Sesión")
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.subtitle_label)
        
        # Espaciador
        self.content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Formulario de login
        self.form_layout = QFormLayout()
        
        # Campo de email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Ingrese su email")
        self.form_layout.addRow("Email:", self.email_edit)
        
        # Campo de contraseña
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Ingrese su contraseña")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.form_layout.addRow("Contraseña:", self.password_edit)
        
        # Agregar formulario al layout
        self.content_layout.addLayout(self.form_layout)
        
        # Espaciador
        self.content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Botón de login
        self.login_button = QPushButton("Iniciar Sesión")
        self.login_button.clicked.connect(self.on_login_clicked)
        self.content_layout.addWidget(self.login_button)
        
        # Información de ayuda
        self.help_label = QLabel("Si no tiene una cuenta o ha olvidado su contraseña, contacte al administrador.")
        self.help_label.setAlignment(Qt.AlignCenter)
        self.help_label.setWordWrap(True)
        self.content_layout.addWidget(self.help_label)
        
        # Pie de página
        self.footer_label = QLabel("© 2025 Unión de Árbitros Río Cuarto. Todos los derechos reservados.")
        self.footer_label.setAlignment(Qt.AlignCenter)
        
        # Espaciadores para centrar el contenido
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(self.content_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.footer_label)
        
        # Conectar señales
        session.login_failed.connect(self.on_login_failed)
        
        # Enter key para login
        self.email_edit.returnPressed.connect(self.on_login_clicked)
        self.password_edit.returnPressed.connect(self.on_login_clicked)
    
    def on_login_clicked(self):
        """Maneja el evento de clic en el botón de login"""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Por favor complete todos los campos")
            return
        
        # Cambiar el cursor y deshabilitar el botón durante el login
        self.setCursor(Qt.WaitCursor)
        self.login_button.setEnabled(False)
        self.login_button.setText("Iniciando sesión...")
        
        # Usar QTimer para permitir que la interfaz se actualice antes de llamar a login
        # que podría bloquear el hilo principal
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.perform_login(email, password))
    
    def perform_login(self, email, password):
        """Realiza el login real"""
        session.login(email, password)
        
        # Restaurar el cursor y habilitar el botón
        self.setCursor(Qt.ArrowCursor)
        self.login_button.setEnabled(True)
        self.login_button.setText("Iniciar Sesión")
    
    def on_login_failed(self, error_message):
        """Maneja el evento de error en el login"""
        QMessageBox.critical(self, "Error de inicio de sesión", error_message)