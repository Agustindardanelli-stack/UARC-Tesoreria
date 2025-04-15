from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox, QFormLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
                             QDialogButtonBox, QCheckBox, QTabWidget)
from PySide6.QtCore import Qt, Signal, Slot
import requests
import json

class EditUserDialog(QDialog):
    """Diálogo para editar un usuario existente"""
    
    def __init__(self, user_data, roles, base_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Usuario")
        self.user_data = user_data
        self.roles = roles
        self.base_url = base_url
        
        # Inicializar la interfaz
        self.init_ui()
        self.load_user_data()
        
        # Validar inputs inicialmente
        self.validate_inputs()
    
    def init_ui(self):
        """Inicializa la interfaz del diálogo"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Campo Nombre
        self.nombre_input = QLineEdit()
        self.nombre_input.textChanged.connect(self.validate_inputs)
        form_layout.addRow("Nombre:", self.nombre_input)
        
        # Campo Email
        self.email_input = QLineEdit()
        self.email_input.textChanged.connect(self.validate_inputs)
        form_layout.addRow("Email:", self.email_input)
        
        # Checkbox para cambiar contraseña
        self.change_password_checkbox = QCheckBox("Cambiar contraseña")
        self.change_password_checkbox.stateChanged.connect(self.toggle_password_fields)
        form_layout.addRow("", self.change_password_checkbox)
        
        # Campo Contraseña
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese la nueva contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.validate_inputs)
        self.password_input.setEnabled(False)
        form_layout.addRow("Nueva Contraseña:", self.password_input)
        
        # Campo Confirmar Contraseña
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirme la nueva contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.textChanged.connect(self.validate_inputs)
        self.confirm_password_input.setEnabled(False)
        form_layout.addRow("Confirmar Contraseña:", self.confirm_password_input)
        
        # Campo Rol
        self.rol_combobox = QComboBox()
        for rol in self.roles:
            self.rol_combobox.addItem(rol['nombre'], rol['id'])
        self.rol_combobox.currentIndexChanged.connect(self.validate_inputs)
        form_layout.addRow("Rol:", self.rol_combobox)
        
        # Checkbox para estado activo
        self.is_active_checkbox = QCheckBox("Usuario activo")
        form_layout.addRow("Estado:", self.is_active_checkbox)
        
        main_layout.addLayout(form_layout)
        
        # Mensaje de validación
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red;")
        main_layout.addWidget(self.validation_label)
        
        # Botones estándar
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        
        main_layout.addWidget(self.button_box)
    
    def toggle_password_fields(self, state):
        """Habilita o deshabilita los campos de contraseña según el estado del checkbox"""
        enabled = state == Qt.Checked
        self.password_input.setEnabled(enabled)
        self.confirm_password_input.setEnabled(enabled)
        self.validate_inputs()
    
    def load_user_data(self):
        """Carga los datos del usuario en los campos"""
        self.nombre_input.setText(self.user_data.get('nombre', ''))
        self.email_input.setText(self.user_data.get('email', ''))
        
        # Seleccionar el rol
        rol_id = self.user_data.get('rol_id')
        if rol_id is not None:
            index = self.rol_combobox.findData(rol_id)
            if index >= 0:
                self.rol_combobox.setCurrentIndex(index)
        
        # Estado activo
        self.is_active_checkbox.setChecked(self.user_data.get('is_active', True))
    
    def validate_inputs(self):
        """Valida los inputs y actualiza el estado del botón OK"""
        nombre = self.nombre_input.text().strip()
        email = self.email_input.text().strip()
        
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
        
        # Validar contraseñas solo si el checkbox está marcado
        if self.change_password_checkbox.isChecked():
            password = self.password_input.text()
            confirm_password = self.confirm_password_input.text()
            
            if not password:
                valid = False
                message = "La nueva contraseña es obligatoria"
            elif password != confirm_password:
                valid = False
                message = "Las contraseñas no coinciden"
        
        self.validation_label.setText(message)
        if self.button_box:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(valid)
        
        return valid
    
    def get_updated_data(self):
        """Retorna los datos actualizados del usuario"""
        data = {
            "nombre": self.nombre_input.text().strip(),
            "email": self.email_input.text().strip(),
            "rol_id": self.rol_combobox.currentData(),
            "is_active": self.is_active_checkbox.isChecked()
        }
        
        # Añadir contraseña solo si se va a cambiar
        if self.change_password_checkbox.isChecked() and self.password_input.text():
            data["password"] = self.password_input.text()
        
        return data

class AddUserWindow(QWidget):
    # Señal que se emite cuando se agrega un usuario exitosamente
    userAdded = Signal()
    # Señal para navegación, requerida por tu MainWindow
    navigation_requested = Signal(str)
    
    def __init__(self, parent=None, base_url="https://uarc-tesoreria.onrender.com"):
        super().__init__(parent)
        
        # Configuración de la ventana
        self.setWindowTitle("Gestión de Usuarios")
        self.setMinimumSize(800, 500)
        
        # URL base para las peticiones a la API
        self.base_url = base_url
        
        # Lista de usuarios
        self.users = []
        
        # Lista de roles
        self.roles = []
        
        # Crear la interfaz de usuario con pestañas
        self.init_ui()
        
        # Obtener roles disponibles
        self.load_roles()
        
        # Cargar lista de usuarios
        self.load_users()
        
        # Validar inputs inicialmente en el formulario de agregar
        self.validate_inputs()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario con pestañas"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Título principal
        title_label = QLabel("Gestión de Usuarios")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Crear pestañas
        self.tabs = QTabWidget()
        
        # Pestaña 1: Agregar Usuario
        self.add_tab = QWidget()
        self.setup_add_tab()
        self.tabs.addTab(self.add_tab, "Agregar Usuario")
        
        # Pestaña 2: Lista de Usuarios
        self.list_tab = QWidget()
        self.setup_list_tab()
        self.tabs.addTab(self.list_tab, "Lista de Usuarios")
        
        # Añadir pestañas al layout principal
        main_layout.addWidget(self.tabs)
        
        # Botón para volver al Dashboard (fuera de las pestañas)
        dashboard_button = QPushButton("Volver al Dashboard")
        dashboard_button.clicked.connect(self.go_to_dashboard)
        main_layout.addWidget(dashboard_button)
        
        # Cambiar a la pestaña de lista cuando se haya agregado un usuario
        self.userAdded.connect(lambda: self.tabs.setCurrentIndex(1))
    
    def setup_add_tab(self):
        """Configura la pestaña de agregar usuario"""
        # Layout de la pestaña
        add_layout = QVBoxLayout(self.add_tab)
        
        # Título
        add_title = QLabel("Agregar Nuevo Usuario")
        add_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        add_layout.addWidget(add_title)
        
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
        
        add_layout.addLayout(form_layout)
        
        # Mensaje de validación
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red;")
        add_layout.addWidget(self.validation_label)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_user)
        self.save_button.setEnabled(False)
        
        clear_button = QPushButton("Limpiar Formulario")
        clear_button.clicked.connect(self.clear_form)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(clear_button)
        
        add_layout.addLayout(buttons_layout)
    
    def setup_list_tab(self):
        """Configura la pestaña de lista de usuarios"""
        # Layout de la pestaña
        list_layout = QVBoxLayout(self.list_tab)
        
        # Título
        list_title = QLabel("Lista de Usuarios")
        list_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        list_layout.addWidget(list_title)
        
        # Botón para actualizar la lista
        refresh_button = QPushButton("Actualizar lista")
        refresh_button.clicked.connect(self.load_users)
        list_layout.addWidget(refresh_button)
        
        # Tabla de usuarios
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)  # id, nombre, email, rol, estado, acciones
        self.users_table.setHorizontalHeaderLabels(["ID", "Nombre", "Email", "Rol", "Estado", "Acciones"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre se expande
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Email se expande
        list_layout.addWidget(self.users_table)
    
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
    
    def load_users(self):
        """Carga la lista de usuarios desde la API"""
        try:
            # Importar la sesión para obtener el token
            from sesion import session
            
            # Obtener el token directamente del atributo
            token = session.token
            
            # Preparar headers con el token de autenticación
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            
            # Obtener usuarios
            response = requests.get(
                f"{self.base_url}/api/usuarios", 
                headers=headers
            )
            
            if response.status_code == 200:
                self.users = response.json()
                self.populate_users_table()
            else:
                error_message = f"Error al obtener usuarios: {response.status_code}"
                try:
                    error_detail = response.json().get('detail', '')
                    error_message = f"{error_message} - {error_detail}"
                except:
                    error_message = f"{error_message} - {response.text}"
                
                print(error_message)
                QMessageBox.critical(self, "Error", error_message)
        except Exception as e:
            error_message = f"Error de conexión: {str(e)}"
            print(error_message)
            QMessageBox.critical(self, "Error de conexión", error_message)
    
    def populate_users_table(self):
        """Llena la tabla con los usuarios obtenidos"""
        # Limpiar tabla
        self.users_table.setRowCount(0)
        
        # Crear diccionario para mapear roles
        roles_map = {role['id']: role['nombre'] for role in self.roles}
        
        # Llenar tabla con usuarios
        for row, user in enumerate(self.users):
            self.users_table.insertRow(row)
            
            # Insertar datos
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.get('nombre', '')))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
            
            # Rol
            rol_nombre = roles_map.get(user.get('rol_id'), "Desconocido")
            self.users_table.setItem(row, 3, QTableWidgetItem(rol_nombre))
            
            # Estado
            estado = "Activo" if user.get('is_active', True) else "Inactivo"
            self.users_table.setItem(row, 4, QTableWidgetItem(estado))
            
            # Botones de acción
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_button = QPushButton("Editar")
            edit_button.setProperty("user_id", user.get('id'))
            edit_button.clicked.connect(self.edit_user)
            
            delete_button = QPushButton("Eliminar")
            delete_button.setProperty("user_id", user.get('id'))
            delete_button.setStyleSheet("background-color: #d9534f; color: white;")
            delete_button.clicked.connect(self.delete_user)
            
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            
            self.users_table.setCellWidget(row, 5, action_widget)
    
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
                
                # Actualizar lista de usuarios
                self.load_users()
                
                # Cambiar a la pestaña de lista (se hace automáticamente por la conexión de señal)
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

    @Slot()
    def edit_user(self):
        """Abre el diálogo para editar un usuario"""
        # Obtener el ID del usuario desde el botón que disparó la señal
        sender = self.sender()
        user_id = sender.property("user_id")
        
        # Encontrar el usuario en la lista
        user = next((u for u in self.users if u.get('id') == user_id), None)
        if not user:
            QMessageBox.warning(self, "Error", "Usuario no encontrado")
            return
        
        # Crear y mostrar el diálogo de edición
        dialog = EditUserDialog(user, self.roles, self.base_url, self)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            updated_data = dialog.get_updated_data()
            self.update_user(user_id, updated_data)
    
    def update_user(self, user_id, data):
        """Actualiza los datos de un usuario en la API"""
        try:
            # Importar la sesión para obtener el token
            from sesion import session
            
            # Obtener el token directamente del atributo
            token = session.token
            
            # Preparar headers con el token de autenticación
            headers = {
                "Authorization": f"Bearer {token}" if token else {},
                "Content-Type": "application/json"
            }
            
            # Enviar petición al API
            response = requests.put(
                f"{self.base_url}/api/usuarios/{user_id}",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Usuario actualizado con éxito."
                )
                # Recargar la lista de usuarios
                self.load_users()
            else:
                error_msg = "Error al actualizar el usuario"
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
    
    @Slot()
    def delete_user(self):
        """Elimina un usuario previa confirmación"""
        # Obtener el ID del usuario desde el botón que disparó la señal
        sender = self.sender()
        user_id = sender.property("user_id")
        
        # Encontrar el usuario en la lista
        user = next((u for u in self.users if u.get('id') == user_id), None)
        if not user:
            QMessageBox.warning(self, "Error", "Usuario no encontrado")
            return
        
        # Solicitar confirmación
        confirmation = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar al usuario {user.get('nombre')}?\n\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirmation == QMessageBox.Yes:
            self.perform_delete_user(user_id)
    
    def perform_delete_user(self, user_id):
        """Realiza la eliminación del usuario en la API"""
        try:
            # Importar la sesión para obtener el token
            from sesion import session
            
            # Obtener el token directamente del atributo
            token = session.token
            
            # Preparar headers con el token de autenticación
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            
            # Enviar petición al API
            response = requests.delete(
                f"{self.base_url}/api/usuarios/{user_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                QMessageBox.information(
                    self,
                    "Éxito",
                    "Usuario eliminado con éxito."
                )
                # Recargar la lista de usuarios
                self.load_users()
            else:
                error_msg = "Error al eliminar el usuario"
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