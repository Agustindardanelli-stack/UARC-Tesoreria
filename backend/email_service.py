import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter,landscape
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from sqlalchemy.orm import Session
import models

class EmailService:
    def __init__(self, smtp_server, smtp_port, username, password, sender_email):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender = sender_email
    

    def get_logo_path(self):
        """Encontrar la ruta correcta del logo"""
        possible_paths = [
            # Ruta para desarrollo local (Windows)
            r'C:\Users\agusd\Desktop\Abuela Coca\uarc-tesoreria\frontend\assets\UarcLogo.png',
            
            # Ruta para servidor de producción
            '/opt/render/project/src/frontend/assets/UarcLogo.png',
            
            # Rutas relativas desde el backend
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        'frontend', 'assets', 'UarcLogo.png')
        ]
        
        # Depuración
        print("Buscando logo en las siguientes rutas:")
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            print(f"Ruta: {abs_path}")
            print(f"Existe: {os.path.exists(abs_path)}")
        
        # Encontrar la primera ruta que exista
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError("No se encontró el logo UarcLogo.png")

    def load_logo(self, pdf_canvas, width, height):
        """Cargar y dibujar el logo en el PDF"""
        try:
            # Obtener la ruta del logo
            ruta_icono = self.get_logo_path()
            
            # Leer el logo
            icono = ImageReader(ruta_icono)
            
            # Dimensiones y posición del logo
            icono_ancho = 1.5 * inch
            icono_alto = 1.5 * inch
            
            # Dibujar el logo
            pdf_canvas.drawImage(
                icono, 
                0.5 * inch,  # Mover más a la izquierda
                height - 1.5 * inch,  # Posición vertical
                width=icono_ancho, 
                height=icono_alto
            )
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")
            
    def generate_receipt_pdf(self, db: Session, cobranza):
        """Genera un PDF con el recibo de la cobranza con diseño moderno y detallado"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))  # Orientación horizontal
        width, height = landscape(letter)
        
        # Definir márgenes y colores
        margin = 0.75 * inch
        accent_color = (0.1, 0.5, 0.7)  # Color azul corporativo
        
        # Fondo con sombreado suave
        p.setFillColorRGB(0.95, 0.95, 1)  # Fondo muy claro
        p.rect(margin/2, margin/2, width - margin, height - margin, fill=1, stroke=0)
        
        # Borde con color de acento
        p.setStrokeColorRGB(*accent_color)
        p.setLineWidth(2)
        p.rect(margin/2, margin/2, width - margin, height - margin)
        
        # Cargar logo en la esquina superior izquierda
        self.load_logo(p, margin + 1*inch, height - margin - inch)
        
        # Encabezado
        p.setFillColorRGB(*accent_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, height - 1.5*inch, "UNIDAD DE ÁRBITROS DE RÍO CUARTO")
        
        # Modificado: Título según tipo de documento
        if hasattr(cobranza, 'tipo_documento') and cobranza.tipo_documento == "factura":
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, height - 2*inch, "FACTURA/RECIBO")
        else:
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, height - 2*inch, "RECIBO DE COBRANZA")
        
        # Obtener usuario/árbitro
        usuario = db.query(models.Usuario).filter(models.Usuario.id == cobranza.usuario_id).first()
        
        # Obtener retención y sus detalles si existe
        retencion = None
        retencion_info = "Sin retención"
        if cobranza.retencion_id:
            retencion = db.query(models.Retencion).filter(models.Retencion.id == cobranza.retencion_id).first()
            if retencion:
                retencion_info = f"{retencion.nombre} - ${float(retencion.monto):,.2f}"
        
        # Detalles de la cobranza
        p.setFont("Helvetica", 12)
        p.setFillColorRGB(0, 0, 0)
        
        # Número de recibo o factura
        if hasattr(cobranza, 'tipo_documento') and cobranza.tipo_documento == "factura":
            num_doc = cobranza.numero_factura if hasattr(cobranza, 'numero_factura') and cobranza.numero_factura else cobranza.id
            p.drawRightString(width - margin, height - 2.5*inch, f"N° Factura: {num_doc}")
        else:
            p.drawRightString(width - margin, height - 2.5*inch, f"N° Recibo: {cobranza.id:05d}")
        
        # Información detallada
        info_y = height - 3.5*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, info_y, "Datos de la Cobranza")
        
        p.setFont("Helvetica", 11)
        linea_altura = 0.3*inch
        
        # Campos de información principales
        campos = [
            ("Fecha:", cobranza.fecha.strftime('%d/%m/%Y')),
        ]
        
        # Modificado: Agregar razón social si es factura
        if hasattr(cobranza, 'tipo_documento') and cobranza.tipo_documento == "factura" and hasattr(cobranza, 'razon_social') and cobranza.razon_social:
            campos.append(("Razón Social:", cobranza.razon_social))
        else:
            campos.append(("Pagador:", usuario.nombre if usuario else "No especificado"))
        
        campos.extend([
            ("Monto:", f"$ {float(cobranza.monto):,.2f}"),
            ("Retención:", retencion_info)
        ])
        
        for i, (etiqueta, valor) in enumerate(campos):
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margin, info_y - (i+1)*linea_altura, etiqueta)
            p.setFont("Helvetica", 10)
            p.drawString(margin + 2*inch, info_y - (i+1)*linea_altura, str(valor))
        
        # Descripción con manejo especial para texto largo
        descripcion = cobranza.descripcion if cobranza.descripcion else "Sin descripción"
        p.setFont("Helvetica-Bold", 10)
        p.drawString(margin, info_y - (len(campos)+1)*linea_altura, "Descripción:")
        p.setFont("Helvetica", 10)
        
        # Dividir descripción larga en múltiples líneas si es necesario
        palabras = descripcion.split()
        lineas = []
        linea_actual = []
        ancho_maximo = 60  # caracteres aproximados por línea
        
        for palabra in palabras:
            linea_actual.append(palabra)
            if len(' '.join(linea_actual)) > ancho_maximo:
                linea_actual.pop()
                lineas.append(' '.join(linea_actual))
                linea_actual = [palabra]
        if linea_actual:
            lineas.append(' '.join(linea_actual))
        
        # Dibujar cada línea de la descripción
        for i, linea in enumerate(lineas):
            p.drawString(margin + 2*inch, info_y - (len(campos)+1+i)*linea_altura, linea)
        
        # Monto en letras
        p.setFont("Helvetica-Bold", 10)
        y_pos = info_y - (len(campos)+1+len(lineas))*linea_altura
        p.drawString(margin, y_pos, "Monto en letras:")
        p.setFont("Helvetica", 10)
        monto_texto = self.numero_a_letras(float(cobranza.monto))
        p.drawString(margin + 2*inch, y_pos, monto_texto)
        
        # Área de firma
        firma_y = margin + 2*inch
        p.setFont("Helvetica", 10)
        p.drawString(margin, firma_y + linea_altura, "Firma:")
        p.line(margin + inch, firma_y, margin + 4*inch, firma_y)
        
        # Información adicional en pie de página
        p.setFont("Helvetica", 8)
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.drawString(margin, margin, "Unidad de Árbitros de Río Cuarto")
        p.drawRightString(width - margin, margin, datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()

    def send_receipt_email(self, db: Session, cobranza, recipient_email):
        # Primero verificar si es una factura y NO enviar correo en ese caso
        if hasattr(cobranza, 'tipo_documento') and cobranza.tipo_documento == "factura":
            # Si es una factura, retornar sin enviar correo
            print(f"No se envía correo para facturas: ID {cobranza.id}")
            return False, "No se envía correo para facturas"
        
        try:
            # El resto del código existente...
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient_email
            msg['Subject'] = f"Recibo de Cobranza #{cobranza.id}"
            
            body = """
            Estimado/a usuario,
            
            Adjunto encontrará el recibo correspondiente a su pago reciente.
            
            Gracias por su preferencia.
            
            Unidad de Árbitros de Río Cuarto
            """
            
            # Usar utf-8 explícitamente
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Generar y adjuntar PDF
            pdf = self.generate_receipt_pdf(db, cobranza)
            attachment = MIMEApplication(pdf, _subtype="pdf")
            filename = f"Recibo_{cobranza.id}.pdf"
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.sender, recipient_email, text)
            
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            print(f"Error detallado: {e}")
            return False, f"Error al enviar email: {str(e)}"    
    def numero_a_letras(self, numero):
        """Convierte un número a su representación en letras (versión simplificada)"""
        # Versión básica
        try:
            from num2words import num2words
            return num2words(numero, lang='es') + " pesos"
        except:
            # Fallback simplificado si no tienes la biblioteca num2words
            return f"{numero:,.2f} pesos"
        
    def generate_payment_receipt_pdf(self, db: Session, pago):
        """Genera un PDF con el recibo del pago con diseño moderno y profesional"""
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))  # Orientación horizontal
        width, height = landscape(letter)
        
        # Definir márgenes y colores
        margin = 0.75 * inch
        accent_color = (0.1, 0.5, 0.7)  # Color azul corporativo
        
        # Fondo con sombreado suave
        p.setFillColorRGB(0.95, 0.95, 1)  # Fondo muy claro
        p.rect(margin/2, margin/2, width - margin, height - margin, fill=1, stroke=0)
        
        # Borde con color de acento
        p.setStrokeColorRGB(*accent_color)
        p.setLineWidth(2)
        p.rect(margin/2, margin/2, width - margin, height - margin)
        
        # Cargar logo en la esquina superior izquierda
        self.load_logo(p, margin + 1*inch, height - margin - inch)
        
        # Encabezado
        p.setFillColorRGB(*accent_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, height - 1.5*inch, "UNIDAD DE ÁRBITROS DE RÍO CUARTO")
        
        # Modificado: Título según tipo de documento
        if hasattr(pago, 'tipo_documento') and pago.tipo_documento == "factura":
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, height - 2*inch, "FACTURA/RECIBO DE PAGO")
        else:
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, height - 2*inch, "ORDEN DE PAGO")
        
        # Obtener usuario/árbitro
        usuario = db.query(models.Usuario).filter(models.Usuario.id == pago.usuario_id).first()        
        
        # Detalles del pago
        p.setFont("Helvetica", 12)
        p.setFillColorRGB(0, 0, 0)
        
        # Número de orden de pago o factura
        if hasattr(pago, 'tipo_documento') and pago.tipo_documento == "factura":
            num_doc = pago.numero_factura if hasattr(pago, 'numero_factura') and pago.numero_factura else pago.id
            p.drawRightString(width - margin, height - 2.5*inch, f"N° Factura: {num_doc}")
        else:
            p.drawRightString(width - margin, height - 2.5*inch, f"N° Orden: {pago.id:05d}")
        
        # Información detallada
        info_y = height - 3.5*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, info_y, "Datos del Pago")
        
        p.setFont("Helvetica", 11)
        linea_altura = 0.3*inch
        
        # Campos de información
        campos = [
            ("Fecha:", pago.fecha.strftime('%d/%m/%Y')),
        ]
        
        # Modificado: Agregar razón social si es factura
        if hasattr(pago, 'tipo_documento') and pago.tipo_documento == "factura" and hasattr(pago, 'razon_social') and pago.razon_social:
            campos.append(("Razón Social:", pago.razon_social))
        else:
            campos.append(("Beneficiario:", usuario.nombre if usuario else "No especificado"))
            
        campos.append(("Monto:", f"$ {float(pago.monto):,.2f}"))
        
        # Descripción
        descripcion = pago.descripcion if hasattr(pago, 'descripcion') and pago.descripcion else "Sin descripción"
        campos.append(("Descripción:", descripcion))
        
        for i, (etiqueta, valor) in enumerate(campos):
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margin, info_y - (i+1)*linea_altura, etiqueta)
            p.setFont("Helvetica", 10)
            p.drawString(margin + 2*inch, info_y - (i+1)*linea_altura, str(valor))
        
        # Área de firma
        firma_y = margin + 2*inch
        p.setFont("Helvetica", 10)
        p.drawString(margin, firma_y + linea_altura, "Firma:")
        p.line(margin + inch, firma_y, margin + 4*inch, firma_y)
        
        # Información adicional en pie de página
        p.setFont("Helvetica", 8)
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.drawString(margin, margin, "Unidad de Árbitros de Río Cuarto")
        p.drawRightString(width - margin, margin, datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def send_payment_receipt_email(self, db: Session, pago, recipient_email):
        # Primero verificar si es una factura y NO enviar correo en ese caso
        if hasattr(pago, 'tipo_documento') and pago.tipo_documento == "factura":
            # Si es una factura, retornar sin enviar correo
            print(f"No se envía correo para facturas de pago: ID {pago.id}")
            return False, "No se envía correo para facturas de pago"
        
        try:
            # El resto del código existente...
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient_email
            msg['Subject'] = f"Orden de Pago #{pago.id}"
            
            body = """
            Estimado/a usuario,
            
            Adjunto encontrará la orden de pago correspondiente.
            
            Gracias.
            
            Unidad de Árbitros de Río Cuarto
            """
            
            # Usar utf-8 explícitamente
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Generar y adjuntar PDF
            pdf = self.generate_payment_receipt_pdf(db, pago)
            attachment = MIMEApplication(pdf, _subtype="pdf")
            filename = f"OrdenPago_{pago.id}.pdf"
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.sender, recipient_email, text)
            
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            print(f"Error detallado: {e}")
            return False, f"Error al enviar email: {str(e)}"    
        
    def generate_cuota_receipt_pdf(self, db: Session, cuota):
        """Genera un PDF con el recibo de pago de cuota"""
        
        buffer = BytesIO()
        # Usar landscape (horizontal)
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        self.load_logo(p, width, height)
        
        # Título principal
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width/2, height - 1 * inch, "UNIDAD DE ÁRBITROS DE RÍO CUARTO")
        p.drawCentredString(width/2, height - 1.5 * inch, "CUOTA SOCIETARIA")
        
        # Número de recibo
        p.setFont("Helvetica-Bold", 12)
        p.drawRightString(width - 1 * inch, height - 1.5 * inch, f"RECIBO Nº {cuota.id:06d}")
        
        # Obtener usuario/árbitro
        usuario = db.query(models.Usuario).filter(models.Usuario.id == cuota.usuario_id).first()
        
        # Campos del recibo
        p.setFont("Helvetica", 12)
        
        # Recibimos de:
        p.drawString(1 * inch, height - 3 * inch, "Recibimos de:")
        p.line(3 * inch, height - 3 * inch, width - 2 * inch, height - 3 * inch)
        p.drawString(3.2 * inch, height - 3 * inch, usuario.nombre if usuario else "")
        
        # La suma de pesos:
        p.drawString(1 * inch, height - 4 * inch, "La suma de pesos:")
        p.line(3 * inch, height - 4 * inch, width - 2 * inch, height - 4 * inch)
        
        # Convertir monto a letras
        monto_valor = float(cuota.monto_pagado) if cuota.pagado else float(cuota.monto)
        monto_texto = self.numero_a_letras(monto_valor)
        p.drawString(3.2 * inch, height - 4 * inch, monto_texto)
        
        # Monto en números
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1 * inch, height - 5 * inch, "$ ")
        p.drawString(2 * inch, height - 5 * inch, f"{monto_valor:,.2f}")
        
        # Línea de firma
        p.setFont("Helvetica", 10)
        p.line(1 * inch, 2 * inch, 5 * inch, 2 * inch)
        p.drawCentredString(3 * inch, 1.7 * inch, "Firma")
        
        # Fecha
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        p.drawRightString(width - 1 * inch, 1.7 * inch, f"Fecha: {fecha_actual}")
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    def send_cuota_receipt_email(self, db: Session, cuota, recipient_email):
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient_email
            msg['Subject'] = f"Recibo de Cuota Societaria - {cuota.fecha.strftime('%B %Y')}"
            
            # Cuerpo del mensaje
            body = """
            Estimado/a socio/a,
            
            Adjunto encontrará el recibo correspondiente a su cuota societaria.
            
            Gracias por formar parte de nuestra unidad.
            
            Unidad de Árbitros de Río Cuarto
            """
            
            # Usar utf-8 explícitamente
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Generar y adjuntar PDF
            pdf = self.generate_cuota_receipt_pdf(db, cuota)
            attachment = MIMEApplication(pdf, _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', 
                                filename=f"Cuota_Societaria_{cuota.id}.pdf")
            msg.attach(attachment)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.sender, recipient_email, text)
            
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            print(f"Error detallado: {e}")
            return False, f"Error al enviar email: {str(e)}"