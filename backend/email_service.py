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
            r'C:\Users\agusd\Desktop\Abuela Coca\uarc-tesoreria\frontend\assets\UarcLogo.jpg',
            
            # Ruta para servidor de producción
            '/opt/render/project/src/frontend/assets/UarcLogo.jpg',
            
            # Rutas relativas desde el backend
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        'frontend', 'assets', 'UarcLogo.jpg')
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
        
        raise FileNotFoundError("No se encontró el logo UarcLogo.jpg")

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
        """Genera un PDF con el recibo de la cobranza"""
         
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Ruta al ícono usando rutas relativas desde el backend
        self.load_logo(p, width, height)
        # Agregar ícono
        
        
            
        # Obtener usuario/árbitro
        usuario = db.query(models.Usuario).filter(models.Usuario.id == cobranza.usuario_id).first()
        
        # Configurar el recibo
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width/2, height - 3*inch, "UNIDAD DE ARBITROS")
        p.drawCentredString(width/2, height - 3.3*inch, "DE RIO CUARTO") 
        
        # Configurar el número de recibo
        p.setFont("Helvetica", 12)
        p.drawRightString(width - inch, height - 3.8*inch, f"RECIBO N° {cobranza.id:06d}")
        p.drawRightString(width - inch, height - 4.1*inch, f"Fecha {cobranza.fecha.strftime('%d/%m/%Y')}")
        
        # Línea horizontal
        p.line(inch, height - 4.5*inch, width - inch, height - 4.5*inch)
        
        # Información del recibo
        p.setFont("Helvetica", 12)
        p.drawString(inch, height - 4.9*inch, "Recibimos de:")
        p.line(3*inch, height - 4.9*inch, width - inch, height - 4.9*inch)
        p.drawString(3.2*inch, height - 4.9*inch, usuario.nombre if usuario else "")
        
        # Monto en letras y números
        monto_texto = self.numero_a_letras(float(cobranza.monto))
        p.drawString(inch, height - 5.4*inch, "La suma de pesos:")
        p.line(3*inch, height - 5.4*inch, width - inch, height - 5.4*inch)
        p.drawString(3.2*inch, height - 5.4*inch, monto_texto)
        
        # Concepto
        p.drawString(inch, height - 5.9*inch, "En concepto de:")
        p.line(3*inch, height - 5.9*inch, width - inch, height - 5.9*inch)
        p.drawString(3.2*inch, height - 5.9*inch, "Pago de arbitraje")
        # Monto total
        p.setFont("Helvetica-Bold", 14)
        p.drawString(4*inch, height - 7.7*inch, "$ ")
        p.drawRightString(width - inch, height - 7.7*inch, f"{float(cobranza.monto):,.2f}")
        
        # Firma
        p.setFont("Helvetica", 10)
        p.drawCentredString(2*inch, height - 9*inch, "_________________")
        p.drawCentredString(2*inch, height - 9.3*inch, "Firma")
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def send_receipt_email(self, db: Session, cobranza, recipient_email):
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient_email
            msg['Subject'] = f"Recibo de Cobranza #{cobranza.id}"
            
            # Cuerpo del mensaje extremadamente simple sin ningún carácter especial
            body = """
            Estimado/a usuario,
            
            Adjunto encontrara el recibo correspondiente a su pago reciente.
            
            Gracias por su preferencia.
            
            Unidad de Arbitros de Rio Cuarto
            """
            
            # Usar utf-8 explícitamente
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Generar y adjuntar PDF
            pdf = self.generate_receipt_pdf(db, cobranza)
            attachment = MIMEApplication(pdf, _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', 
                                filename=f"Recibo_{cobranza.id}.pdf")
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
        """Genera un PDF con el recibo del pago con diseño mejorado"""
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Cargar logo
        self.load_logo(p, width, height)
        
        # Título principal
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width/2, height - 1 * inch, "UNIDAD DE ÁRBITROS")
        p.drawCentredString(width/2, height - 1.5 * inch, "DE RÍO CUARTO")
        
        # Subtítulo
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, height - 2.2 * inch, "ORDEN DE PAGO")
        
        # Número de orden
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width/2, height - 2.6 * inch, f"N° {pago.id:06d}")
        
        # Línea horizontal decorativa
        p.setStrokeColorRGB(0, 0, 0.8)  # Azul oscuro
        p.setLineWidth(1)
        p.line(margin + 0.5 * inch, height - 2.8 * inch, width - margin - 0.5 * inch, height - 2.8 * inch)
        
        # Obtener usuario/árbitro
        usuario = db.query(models.Usuario).filter(models.Usuario.id == pago.usuario_id).first()
        
        # Obtener retención
        retencion = db.query(models.Retencion).filter(models.Retencion.id == pago.retencion_id).first()
        
        # Definir márgenes y posiciones
        margin = 1 * inch
        
        # Configurar tabla
        p.setFont("Helvetica", 11)
        
        # Encabezados de columnas
        encabezados = ["N° RECIBO", "IMPORTE", "SE ABONARÁ A", "CONCEPTO A PAGAR"]
        cols_width = [1.5 * inch, 1.5 * inch, 2 * inch, 2.5 * inch]
        
        # Dibujar tabla
        y_start = height - 3.5 * inch
        
        # Dibujar cuadrícula
        p.setStrokeColorRGB(0.7, 0.7, 0.7)  # Gris claro
        p.setLineWidth(0.5)
        
        # Dibujar líneas horizontales
        for i in range(2):  # Una línea más para datos
            p.line(margin, y_start - i * 0.5 * inch, width - margin, y_start - i * 0.5 * inch)
        
        # Dibujar líneas verticales
        x_pos = margin
        for ancho in cols_width:
            p.line(x_pos, y_start, x_pos, y_start - 0.5 * inch)
            x_pos += ancho
        p.line(x_pos, y_start, x_pos, y_start - 0.5 * inch)
        
        # Escribir encabezados
        p.setFont("Helvetica-Bold", 10)
        x_pos = margin
        for encabezado in encabezados:
            p.drawCentredString(x_pos + cols_width[encabezados.index(encabezado)]/2, y_start - 0.25 * inch, encabezado)
            x_pos += cols_width[encabezados.index(encabezado)]
        
        # Escribir datos
        p.setFont("Helvetica", 10)
        y_start -= 0.5 * inch
        
        p.drawCentredString(margin + cols_width[0]/2, y_start - 0.25 * inch, f"{pago.id:06d}")
        p.drawCentredString(margin + cols_width[0] + cols_width[1]/2, y_start - 0.25 * inch, f"$ {float(pago.monto):,.2f}")
        p.drawCentredString(margin + cols_width[0] + cols_width[1] + cols_width[2]/2, y_start - 0.25 * inch, usuario.nombre if usuario else "")
        
        concepto = f"Pago de arbitraje - {retencion.nombre if retencion else 'Pago'}"
        p.drawCentredString(margin + cols_width[0] + cols_width[1] + cols_width[2] + cols_width[3]/2, y_start - 0.25 * inch, concepto)
        
        # Firma y total
        y_pos = margin + 1.5 * inch
        p.setFont("Helvetica", 10)
        p.drawString(margin, y_pos, "Firma:")
        p.line(margin + 1 * inch, y_pos - 0.1 * inch, margin + 4 * inch, y_pos - 0.1 * inch)
        
        p.drawRightString(width - margin, y_pos, f"TOTAL: $ {float(pago.monto):,.2f}")
        
        # Fecha
        p.drawRightString(width - margin, margin + 0.5 * inch, f"Fecha: {pago.fecha.strftime('%d/%m/%Y')}")
        
        # Pie de página
        p.setFont("Helvetica-Oblique", 8)
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.drawCentredString(width/2, margin * 0.5, "Unidad de Árbitros de Río Cuarto - Documento generado automáticamente")
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    def send_payment_receipt_email(self, db: Session, pago, recipient_email):
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient_email
            msg['Subject'] = f"Orden de Pago #{pago.id}"
            
            # Cuerpo del mensaje
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
            attachment.add_header('Content-Disposition', 'attachment', 
                                filename=f"OrdenPago_{pago.id}.pdf")
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