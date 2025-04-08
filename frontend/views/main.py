from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QComboBox, QHBoxLayout

class TesoreriaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Tesorería")
        self.setGeometry(100, 100, 800, 600)
        
        self.initUI()
    
    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Menú de navegación
        self.btn_cobranzas = QPushButton("Cobranzas")
        self.btn_pagos = QPushButton("Pagos")
        self.btn_reportes = QPushButton("Reportes")
        
        menu_layout = QHBoxLayout()
        menu_layout.addWidget(self.btn_cobranzas)
        menu_layout.addWidget(self.btn_pagos)
        menu_layout.addWidget(self.btn_reportes)
        
        layout.addLayout(menu_layout)
        
        # Formulario
        self.lbl_monto = QLabel("Monto:")
        self.txt_monto = QLineEdit()
        
        self.lbl_categoria = QLabel("Categoría:")
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItems(["Retenciones", "Infanto-Juveniles", "Primera División", "Futsal", "Seguro", "Entrenamiento", "Otras Cobranzas"])
        
        self.btn_registrar = QPushButton("Registrar Movimiento")
        
        form_layout = QHBoxLayout()
        form_layout.addWidget(self.lbl_monto)
        form_layout.addWidget(self.txt_monto)
        form_layout.addWidget(self.lbl_categoria)
        form_layout.addWidget(self.cmb_categoria)
        form_layout.addWidget(self.btn_registrar)
        
        layout.addLayout(form_layout)
        
        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Monto", "Categoría"])
        layout.addWidget(self.table)
        
        self.btn_registrar.clicked.connect(self.agregar_movimiento)
    
    def agregar_movimiento(self):
        monto = self.txt_monto.text()
        categoria = self.cmb_categoria.currentText()
        
        if monto:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(monto))
            self.table.setItem(row_position, 1, QTableWidgetItem(categoria))
            
            self.txt_monto.clear()


