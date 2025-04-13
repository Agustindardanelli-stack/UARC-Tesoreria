import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import Qt

# Importación de las vistas
from views.login import LoginView
from views.dashboard import DashboardView
from views.pagos import PagosView
from views.cobranzas import CobranzasView
from views.socio_couta import SocioCuotaView
from views.importes import ImportesView
from views.reportes import ReportesView
from views.email_config_view import EmailConfigView
# No importamos AddUserWindow aquí para evitar problemas de inicialización temprana
# Importar la sesión para manejar el estado de autenticación
from sesion import session

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana principal
        self.setWindowTitle("Gestion Integral UARC")
        self.setMinimumSize(1200, 700)
        
        # Widget central que contendrá todo
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Widget apilado para alternar entre login y sistema
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Inicializar vistas
        self.init_views()
        
        # Conectar señales
        session.login_success.connect(lambda user_info: self.show_system())
        
        # Mostrar la vista de login por defecto
        self.stacked_widget.setCurrentWidget(self.login_view)
        
    def init_views(self):
        """Inicializa todas las vistas y las añade al widget apilado"""
        # Vista de login
        self.login_view = LoginView()
        self.stacked_widget.addWidget(self.login_view)
        
        # Crear instancias de las vistas del sistema
        self.dashboard_view = DashboardView()
        self.pagos_view = PagosView()
        self.cobranzas_view = CobranzasView()
        self.socio_cuota_view = SocioCuotaView()
        self.importes_view = ImportesView()
        self.reportes_view = ReportesView()
        self.email_config_view = EmailConfigView()
        
        # No creamos AddUserWindow aquí, lo haremos bajo demanda
        # Añadimos un flag para controlar si ya se creó o no
        self.add_user_view_created = False
        
        # Añadir las vistas al widget apilado
        self.stacked_widget.addWidget(self.dashboard_view)
        self.stacked_widget.addWidget(self.pagos_view)
        self.stacked_widget.addWidget(self.cobranzas_view)
        self.stacked_widget.addWidget(self.socio_cuota_view)
        self.stacked_widget.addWidget(self.importes_view)
        self.stacked_widget.addWidget(self.reportes_view)
        self.stacked_widget.addWidget(self.email_config_view)
        
        # Conectar señales de navegación de todas las vistas
        self.dashboard_view.navigation_requested.connect(self.navigate_to)
        self.pagos_view.navigation_requested.connect(self.navigate_to)
        self.cobranzas_view.navigation_requested.connect(self.navigate_to)
        self.socio_cuota_view.navigation_requested.connect(self.navigate_to)
        self.importes_view.navigation_requested.connect(self.navigate_to)
        self.reportes_view.navigation_requested.connect(self.navigate_to)
        self.email_config_view.navigation_requested.connect(self.navigate_to)
                
    def show_system(self):
        """Muestra la interfaz principal del sistema después de la autenticación"""
        self.stacked_widget.setCurrentWidget(self.dashboard_view)
        # Actualizar los datos del dashboard
        if hasattr(self.dashboard_view, 'refresh_data'):
            self.dashboard_view.refresh_data()
            
        # Actualizar visibilidad de botones según los permisos
        self.update_navigation_permissions()
    
    def update_navigation_permissions(self):
        """Actualiza la visibilidad de elementos de navegación según los permisos del usuario"""
        # Obtener el rol del usuario actual
        user_rol = ''
        if session.user_info and 'rol' in session.user_info:
            user_rol = session.user_info['rol'].lower()
        
        # Lista de roles con permiso para agregar usuarios
        roles_permitidos = ['admin', 'administrador', 'tesorero']
        
        # Verificar si cada vista tiene el método para actualizar permisos
        views_with_permissions = [
            self.dashboard_view,
            self.pagos_view,
            self.cobranzas_view,
            self.socio_cuota_view,
            self.importes_view,
            self.reportes_view,
            self.email_config_view
        ]
        
        for view in views_with_permissions:
            if hasattr(view, 'update_permissions'):
                # Pasar los permisos a cada vista
                can_add_user = user_rol in roles_permitidos
                view.update_permissions(user_rol=user_rol, can_add_user=can_add_user)
        
    def has_permission_for_view(self, view_name):
        """Verifica si el usuario actual tiene permiso para acceder a una vista específica"""
        # Obtener el rol del usuario actual
        user_rol = ''
        if session.user_info and 'rol' in session.user_info:
            user_rol = session.user_info['rol'].lower()
        
        # Definir permisos por vista
        if view_name == "add_user":
            # Solo admin y tesorero pueden agregar usuarios
            return user_rol in ['admin', 'administrador', 'tesorero']
        elif view_name == "email_config":
            # Solo admin puede configurar email (ejemplo)
            return user_rol in ['admin', 'tesorero']
        
        # Para otras vistas, por defecto permitir acceso
        return True
        
    def navigate_to(self, view_name):
        """Cambia a la vista especificada dentro del sistema"""
        # Verificar permisos antes de navegar
        if not self.has_permission_for_view(view_name):
            QMessageBox.warning(
                self, 
                "Acceso Denegado", 
                "No tienes permisos para acceder a esta funcionalidad."
            )
            return
            
        if view_name == "dashboard":
            self.stacked_widget.setCurrentWidget(self.dashboard_view)
            # Actualizar los datos cuando se regresa al dashboard
            self.dashboard_view.refresh_data()
        elif view_name == "pagos":
            self.stacked_widget.setCurrentWidget(self.pagos_view)
        elif view_name == "cobranzas":
            self.stacked_widget.setCurrentWidget(self.cobranzas_view)
        elif view_name == "socio_cuota":
            self.stacked_widget.setCurrentWidget(self.socio_cuota_view)
        elif view_name == "importes":
            self.stacked_widget.setCurrentWidget(self.importes_view)
            # Añade esta línea para cargar los datos cuando se navega a importes
            self.importes_view.refresh_data()
        elif view_name == "reportes":
            self.stacked_widget.setCurrentWidget(self.reportes_view)
        elif view_name == "email_config": 
            self.stacked_widget.setCurrentWidget(self.email_config_view)
        elif view_name == "add_user":
            # Crear la vista de AddUserWindow solo cuando se necesite
            if not hasattr(self, 'add_user_view') or not self.add_user_view_created:
                # Importamos aquí para evitar problemas de inicialización temprana
                from views.add_user import AddUserWindow
                self.add_user_view = AddUserWindow(self)
                self.add_user_view.navigation_requested.connect(self.navigate_to)
                self.stacked_widget.addWidget(self.add_user_view)
                self.add_user_view_created = True
            self.stacked_widget.setCurrentWidget(self.add_user_view)
        elif view_name == "logout":
            # Cerrar sesión y volver a login
            session.logout()
            self.stacked_widget.setCurrentWidget(self.login_view)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configuración global de la aplicación
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())