import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
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
    
    def generate_receipt_pdf(self, db: Session, cobranza):
        """Genera un PDF con el recibo de la cobranza"""
         
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Ruta al ícono usando rutas relativas desde el backend
        ruta_icono = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'frontend', 'assets',  'Uarclogo.jpg')
        
        # Agregar ícono
        try:
            # Abrir el ícono
            icono = ImageReader(ruta_icono)
            
            # Obtener dimensiones del ícono (ajustar según sea necesario)
            icono_ancho = 1.5 * inch  # Ancho del ícono
            icono_alto = 1.5 * inch   # Alto del ícono
            
            # Posicionar el ícono (centrado, un poco arriba del título)
            p.drawImage(
                icono, 
                width/2 - icono_ancho/2,  # Centrar horizontalmente
                height - 1.5 * inch,      # Posición vertical
                width=icono_ancho, 
                height=icono_alto
            )
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")
            print(f"Ruta intentada: {ruta_icono}")  # Añadido para depuración
            print(f"Ruta absoluta: {os.path.abspath(ruta_icono)}")  # Añadido para depuración
            print(f"Existe el archivo: {os.path.exists(ruta_icono)}")
            
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
        
        # Items
        p.drawString(inch, height - 6.7*inch, "Item: $")
        p.line(2*inch, height - 6.7*inch, 3.5*inch, height - 6.7*inch)
        
        p.drawString(inch, height - 7.2*inch, "Item: $")
        p.line(2*inch, height - 7.2*inch, 3.5*inch, height - 7.2*inch)
        
        p.drawString(inch, height - 7.7*inch, "Item: $")
        p.line(2*inch, height - 7.7*inch, 3.5*inch, height - 7.7*inch)
        
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
        """Genera un PDF con el recibo del pago"""
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Ruta al ícono usando rutas relativas desde el backend
        ruta_icono = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'frontend', 'assets',  'Uarclogo.jpg')
        
        # Intentar agregar ícono
        try:
            icono = ImageReader(ruta_icono)
            icono_ancho = 1 * inch
            icono_alto = 1 * inch
            p.drawImage(
                icono, 
                width - 1.5 * inch,  # Posición a la derecha
                height - 1.5 * inch, # Posición arriba
                width=icono_ancho, 
                height=icono_alto
            )
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")
        
        # Obtener usuario/árbitro
        usuario = db.query(models.Usuario).filter(models.Usuario.id == pago.usuario_id).first()
        
        # Obtener retención
        retencion = db.query(models.Retencion).filter(models.Retencion.id == pago.retencion_id).first()
        
        # Título
        p.setFont("Helvetica-Bold", 14)
        p.drawString(width/2 - 2.5*inch, height - 1.2*inch, "UNIDAD DE ARBITROS")
        p.drawString(width/2 - 2*inch, height - 1.6*inch, "DE RIO CUARTO")
        
        # Orden de pago
        p.setFont("Helvetica-Bold", 12)
        p.drawString(width/2 - 1.5*inch, height - 2.1*inch, "ORDENES DE PAGO")
        p.drawString(width/2 - 0.6*inch, height - 2.5*inch, f"N° {pago.id:06d}")
        
        # Diseñar el formulario similar al de la imagen
        p.setFont("Helvetica", 10)
        
        # Dibujar el rectángulo principal
        p.rect(inch, height - 6*inch, width - 2*inch, 3*inch)
        
        # Líneas horizontales para las filas
        y_start = height - 3*inch
        p.line(inch, y_start - 0.75*inch, width - inch, y_start - 0.75*inch)
        p.line(inch, y_start - 1.5*inch, width - inch, y_start - 1.5*inch)
        p.line(inch, y_start - 2.25*inch, width - inch, y_start - 2.25*inch)
        
        # Líneas verticales para las columnas
        p.line(inch + 1.5*inch, y_start, inch + 1.5*inch, y_start - 3*inch)  # N° recibo
        p.line(inch + 3*inch, y_start, inch + 3*inch, y_start - 3*inch)      # Importe
        p.line(inch + 4.5*inch, y_start, inch + 4.5*inch, y_start - 3*inch)  # Se abonará a
        
        # Títulos de columnas
        p.drawString(inch + 0.5*inch, y_start - 0.5*inch, "N° recibo")
        p.drawString(inch + 2*inch, y_start - 0.5*inch, "Importe")
        p.drawString(inch + 3.5*inch, y_start - 0.5*inch, "Se abonará a")
        p.drawString(width - 2*inch, y_start - 0.5*inch, "Concepto a pagar")
        
        # Información del pago
        p.drawString(inch + 0.5*inch, y_start - 1.2*inch, f"{pago.id:06d}")
        p.drawString(inch + 2*inch, y_start - 1.2*inch, f"$ {float(pago.monto):,.2f}")
        p.drawString(inch + 3.5*inch, y_start - 1.2*inch, usuario.nombre if usuario else "")
        
        # Concepto
        concepto = f"Pago de arbitraje - {retencion.nombre if retencion else 'Pago'}"
        p.drawString(width - 2.5*inch, y_start - 1.2*inch, concepto)
        
        # Campo para firma
        p.drawString(1.5*inch, height - 6.3*inch, "Firma:")
        p.line(2.5*inch, height - 6.3*inch, 4*inch, height - 6.3*inch)
        
        # Campo para monto
        p.drawString(4.5*inch, height - 6.3*inch, "$")
        p.rect(4.8*inch, height - 6.5*inch, 1.5*inch, 0.4*inch)
        p.drawString(5*inch, height - 6.3*inch, f"{float(pago.monto):,.2f}")
        
        # Fecha
        p.drawString(width - 2.5*inch, height - 6.3*inch, "Fecha:")
        p.rect(width - 1.8*inch, height - 6.5*inch, 0.8*inch, 0.4*inch)
        p.drawString(width - 1.7*inch, height - 6.3*inch, pago.fecha.strftime('%d/%m/%Y'))
        
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
        """Genera un PDF con el recibo de pago de cuota con formato similar a la imagen"""
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Ruta al ícono
        ruta_icono = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'frontend', 'assets', 'Uarclogo.jpg')
        
        # Configurar el recibo - orientación apaisada como en la imagen
        p.rotate(90)  # Girar para formato horizontal
        p.translate(0, -width)  # Ajustar coordenadas tras rotación
        
        # Intentar agregar ícono
        try:
            icono = ImageReader(ruta_icono)
            icono_ancho = 0.7 * inch
            icono_alto = 0.7 * inch
            p.drawImage(
                icono, 
                inch,  # Posición izquierda
                height - 1.5 * inch,  # Posición arriba
                width=icono_ancho, 
                height=icono_alto
            )
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")
        
        # Obtener usuario/árbitro
        usuario = db.query(models.Usuario).filter(models.Usuario.id == cuota.usuario_id).first()
        
        # Título (UNIDAD DE ÁRBITROS DE RÍO CUARTO - vertical)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(inch, height - 1.1 * inch, "UNIDAD")
        p.drawString(inch, height - 1.4 * inch, "DE ÁRBITROS")
        p.drawString(inch, height - 1.7 * inch, "DE RÍO CUARTO")
        
        # CUOTA SOCIETARIA
        p.setFont("Helvetica-Bold", 14)
        p.drawString(height - 3 * inch, width - 1.5 * inch, "CUOTA SOCIETARIA")
        
        # Número de recibo
        p.setFont("Helvetica-Bold", 12)
        p.drawString(height - 3 * inch, width - 1.8 * inch, f"RECIBO Nº {cuota.id:06d}")
        
        # Dibujar los tres cuadrados para marcar
        for i in range(3):
            p.rect(height - 3 * inch, width - (2.2 + i * 0.5) * inch, 0.3 * inch, 0.3 * inch)
        
        # Líneas para información
        p.setFont("Helvetica", 10)
        
        # Recibimos de:
        p.drawString(inch, width - 2.5 * inch, "Recibimos de:")
        p.line(2.2 * inch, width - 2.5 * inch, 5 * inch, width - 2.5 * inch)
        p.drawString(2.3 * inch, width - 2.5 * inch, usuario.nombre if usuario else "")
        
        # La suma de pesos:
        p.drawString(inch, width - 3 * inch, "La suma de pesos:")
        p.line(2.2 * inch, width - 3 * inch, 5 * inch, width - 3 * inch)
        monto_texto = self.numero_a_letras(float(cuota.monto_pagado) if cuota.pagado else float(cuota.monto))
        p.drawString(2.3 * inch, width - 3 * inch, monto_texto)
        
        # Campo para monto - rectángulo gris
        p.setFillGray(0.85)
        p.rect(5.5 * inch, width - 3 * inch, 1 * inch, 0.3 * inch, fill=1)
        p.setFillGray(0)  # Volver a negro para texto
        
        # Símbolo de pesos y monto
        p.drawString(5.4 * inch, width - 2.95 * inch, "$")
        p.setFont("Helvetica-Bold", 10)
        monto_valor = float(cuota.monto_pagado) if cuota.pagado else float(cuota.monto)
        p.drawString(5.6 * inch, width - 2.95 * inch, f"{monto_valor:,.2f}")
        
        # Firma
        p.setFont("Helvetica", 8)
        p.drawString(height - 1.5 * inch, width - 3 * inch, "Firma")
        p.line(height - 3 * inch, width - 3 * inch, height - 1.8 * inch, width - 3 * inch)
        
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