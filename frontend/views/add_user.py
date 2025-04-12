from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt, Signal, Slot
import requests
import json

class AddUserWindow(QWidget):
    # Señal que se emite cuando se agrega un usuario exitosamente
    userAdded = Signal()
    # Señal para navegación, requerida por tu MainWindow
    navigation_requested = Signal(str)
    
    def __init__(self, parent=None, base_url="https://uarc-tesoreria.onrender.com"):
        super().__init__(parent)
        
        # Configuración de la ventana
        self.setWindowTitle("Agregar Nuevo Usuario")
        self.setMinimumSize(450, 400)
        
        # URL base para las peticiones a la API
        self.base_url = base_url
        
        # Crear la interfaz de usuario
        self.init_ui()
        
        # Obtener roles disponibles (después de crear la UI para poder mostrar mensajes si hay error)
        self.roles = []
        self.load_roles()
        
        # Validar inputs inicialmente
        self.validate_inputs()
    
    def load_roles(self):
        """Carga los roles disponibles"""
        try:
            # Importar la sesión para obtener el token
            from sesion import session
            
            # Obtener el token directamente del atributo
            token = session.token
            
            # Preparar headers con el token de autenticación
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            
            # Usar el endpoint existente para obtener roles, ahora con autenticación
            response = requests.get(
                f"{self.base_url}/api/roles", 
                headers=headers
            )
            
            if response.status_code == 200:
                self.roles = response.json()
                # Verificar que hayamos recibido una lista y no esté vacía
                if self.roles and isinstance(self.roles, list):
                    print(f"Roles obtenidos correctamente: {self.roles}")
                    # Actualizar el combo box con los roles obtenidos
                    self.update_roles_combobox()
                else:
                    print(f"Respuesta inválida o sin roles: {self.roles}")
                    self.roles = []
            else:
                error_message = f"Error al obtener roles: {response.status_code}"
                try:
                    error_detail = response.json().get('detail', '')
                    error_message = f"{error_message} - {error_detail}"
                except:
                    error_message = f"{error_message} - {response.text}"
                
                print(error_message)
                QMessageBox.critical(self, "Error", error_message)
                self.roles = []
        except Exception as e:
            error_message = f"Error de conexión: {str(e)}"
            print(error_message)
            QMessageBox.critical(self, "Error de conexión", error_message)
            self.roles = []
    
    def update_roles_combobox(self):
        """Actualiza el combobox con los roles obtenidos"""
        if hasattr(self, 'rol_combobox'):
            self.rol_combobox.clear()
            if self.roles:
                for rol in self.roles:
                    self.rol_combobox.addItem(rol['nombre'], rol['id'])
    
    def check_email_exists(self, email):
        """Verifica si el email ya está registrado"""
        try:
            # Importar la sesión para obtener el token
            from sesion import session
            
            # Obtener el token directamente del atributo
            token = session.token
            
            # Preparar headers con el token de autenticación
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            
            # Verificar si el email existe
            response = requests.get(f"{self.base_url}/api/usuarios", headers=headers)
            if response.status_code == 200:
                usuarios = response.json()
                for usuario in usuarios:
                    if usuario.get('email') == email:
                        return True
            return False
        except Exception:
            return False
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Agregar Nuevo Usuario")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Campo Nombre
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ingrese el nombre completo")
        self.nombre_input.textChanged.connect(self.validate_inputs)
        form_layout.addRow("Nombre:", self.nombre_input)
        
        # Campo Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ejemplo@correo.com")
        self.email_input.textChanged.connect(self.validate_inputs)
        self.email_input.editingFinished.connect(self.check_email)
        form_layout.addRow("Email:", self.email_input)
        
        # Campo Contraseña
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese la contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.validate_inputs)
        form_layout.addRow("Contraseña:", self.password_input)
        
        # Campo Confirmar Contraseña
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirme la contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.textChanged.connect(self.validate_inputs)
        form_layout.addRow("Confirmar Contraseña:", self.confirm_password_input)
        
        # Campo Rol
        self.rol_combobox = QComboBox()
        self.rol_combobox.currentIndexChanged.connect(self.validate_inputs)
        form_layout.addRow("Rol:", self.rol_combobox)
        
        main_layout.addLayout(form_layout)
        
        # Mensaje de validación
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red;")
        main_layout.addWidget(self.validation_label)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_user)
        self.save_button.setEnabled(False)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.go_back)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(cancel_button)
        
        # Botón para volver al Dashboard
        dashboard_button = QPushButton("Volver al Dashboard")
        dashboard_button.clicked.connect(self.go_to_dashboard)
        
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(dashboard_button)
    
    @Slot()
    def go_back(self):
        """Vuelve a la vista anterior"""
        self.navigation_requested.emit("dashboard")
    
    @Slot()
    def go_to_dashboard(self):
        """Va directamente al dashboard"""
        self.navigation_requested.emit("dashboard")
    
    @Slot()
    def check_email(self):
        """Verifica si el email ya existe cuando el campo pierde el foco"""
        email = self.email_input.text().strip()
        if email and '@' in email and '.' in email:
            if self.check_email_exists(email):
                self.validation_label.setText("Este email ya está registrado")
                self.save_button.setEnabled(False)
                return False
        return True
    
    @Slot()
    def validate_inputs(self):
        """Valida los inputs y actualiza el estado del botón guardar"""
        nombre = self.nombre_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        valid = True
        message = ""
        
        if not nombre:
            valid = False
            message = "El nombre es obligatorio"
        elif not email:
            valid = False
            message = "El email es obligatorio"
        elif '@' not in email or '.' not in email:
            valid = False
            message = "Ingresa un email válido"
        elif not password:
            valid = False
            message = "La contraseña es obligatoria"
        elif password != confirm_password:
            valid = False
            message = "Las contraseñas no coinciden"
        elif self.rol_combobox.count() == 0:
            valid = False
            message = "No hay roles disponibles"
        
        self.validation_label.setText(message)
        self.save_button.setEnabled(valid)
        
        return valid
    
    @Slot()
    def save_user(self):
        """Guarda el nuevo usuario en la base de datos"""
        if not self.validate_inputs() or not self.check_email():
            return
        
        nombre = self.nombre_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        rol_id = self.rol_combobox.currentData()
        
        # Datos a enviar al API
        data = {
            "nombre": nombre,
            "email": email,
            "password": password,
            "rol_id": rol_id
        }
        
        try:
            # Importar la sesión para obtener el token
            from sesion import session
            
            # Obtener el token directamente del atributo
            token = session.token
            
            # Preparar headers con el token de autenticación
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            
            # Enviar petición al API
            response = requests.post(
                f"{self.base_url}/api/usuarios",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200 or response.status_code == 201:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Usuario {nombre} agregado con éxito."
                )
                # Emitir señal de usuario agregado
                self.userAdded.emit()
                
                # Limpiar formulario
                self.clear_form()
                
                # Opcional: regresar al dashboard
                self.navigation_requested.emit("dashboard")
            else:
                error_msg = "Error al crear el usuario"
                try:
                    resp_json = response.json()
                    if 'detail' in resp_json:
                        error_msg = resp_json['detail']
                except:
                    error_msg = f"Error {response.status_code}: {response.text}"
                    
                QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de conexión",
                f"Error al comunicarse con el servidor: {str(e)}"
            ) 
    
    def clear_form(self):
        """Limpia todos los campos del formulario"""
        self.nombre_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        if self.rol_combobox.count() > 0:
            self.rol_combobox.setCurrentIndex(0)
        self.validation_label.setText("")
        self.save_button.setEnabled(False)