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
        """Genera un PDF con el recibo del pago con diseño mejorado"""
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Ruta al ícono usando rutas relativas desde el backend
        ruta_icono = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'frontend', 'assets',  'Uarclogo.jpg')
        
        # Agregar color de fondo para encabezado
        p.setFillColorRGB(0.95, 0.95, 0.95)  # Gris muy claro
        p.rect(0, height - 2.2*inch, width, 2.2*inch, fill=1, stroke=0)
        p.setFillColorRGB(0, 0, 0)  # Volver a negro para texto
        
        # Intentar agregar ícono
        try:
            icono = ImageReader(ruta_icono)
            icono_ancho = 1.2 * inch
            icono_alto = 1.2 * inch
            p.drawImage(
                icono, 
                width - 1.7 * inch,  # Posición a la derecha
                height - 1.7 * inch, # Posición arriba
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
        p.setFont("Helvetica-Bold", 16)
        p.drawString(width/2 - 2.5*inch, height - 0.9*inch, "UNIDAD DE ÁRBITROS")
        p.drawString(width/2 - 1.8*inch, height - 1.3*inch, "DE RÍO CUARTO")
        
        # Línea separadora decorativa
        p.setStrokeColorRGB(0.3, 0.3, 0.7)  # Azul oscuro
        p.setLineWidth(2)
        p.line(inch, height - 1.8*inch, width - inch, height - 1.8*inch)
        p.setLineWidth(1)
        p.setStrokeColorRGB(0, 0, 0)  # Volver a negro
        
        # Orden de pago
        p.setFont("Helvetica-Bold", 14)
        p.drawString(width/2 - 1.2*inch, height - 2.3*inch, "ORDEN DE PAGO")
        p.setFont("Helvetica-Bold", 12)
        p.drawString(width/2 - 0.6*inch, height - 2.7*inch, f"N° {pago.id:06d}")
        
        # Sombreado para sección principal
        p.setFillColorRGB(0.98, 0.98, 1.0)  # Azul muy claro
        p.rect(inch, height - 6*inch, width - 2*inch, 3*inch, fill=1, stroke=0)
        p.setFillColorRGB(0, 0, 0)  # Volver a negro para texto
        
        # Dibujar el rectángulo principal con borde más estético
        p.setStrokeColorRGB(0.3, 0.3, 0.7)  # Azul oscuro
        p.setLineWidth(1.5)
        p.rect(inch, height - 6*inch, width - 2*inch, 3*inch)
        p.setLineWidth(0.8)
        
        # Líneas horizontales para las filas
        y_start = height - 3*inch
        p.line(inch, y_start - 0.75*inch, width - inch, y_start - 0.75*inch)
        p.line(inch, y_start - 1.5*inch, width - inch, y_start - 1.5*inch)
        p.line(inch, y_start - 2.25*inch, width - inch, y_start - 2.25*inch)
        
        # Líneas verticales para las columnas
        p.line(inch + 1.5*inch, y_start, inch + 1.5*inch, y_start - 3*inch)  # N° recibo
        p.line(inch + 3*inch, y_start, inch + 3*inch, y_start - 3*inch)      # Importe
        p.line(inch + 4.5*inch, y_start, inch + 4.5*inch, y_start - 3*inch)  # Se abonará a
        
        # Títulos de columnas con fondo
        p.setFillColorRGB(0.3, 0.3, 0.7)  # Azul oscuro
        p.setFont("Helvetica-Bold", 10)
        p.setFillColorRGB(1, 1, 1)  # Texto blanco
        
        # Rectángulos para títulos
        for i, (pos, width_col) in enumerate([
            (inch, 1.5*inch),  # N° recibo
            (inch + 1.5*inch, 1.5*inch),  # Importe
            (inch + 3*inch, 1.5*inch),  # Se abonará a
            (inch + 4.5*inch, width - inch - (inch + 4.5*inch))  # Concepto
        ]):
            p.rect(pos, y_start - 0.6*inch, width_col, 0.6*inch, fill=1, stroke=0)
        
        # Textos de títulos
        p.drawString(inch + 0.3*inch, y_start - 0.4*inch, "N° RECIBO")
        p.drawString(inch + 2*inch, y_start - 0.4*inch, "IMPORTE")
        p.drawString(inch + 3.5*inch, y_start - 0.4*inch, "SE ABONARÁ A")
        p.drawString(inch + 5*inch, y_start - 0.4*inch, "CONCEPTO A PAGAR")
        
        # Volver a negro para el contenido
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 10)
        
        # Información del pago
        p.drawString(inch + 0.5*inch, y_start - 1.2*inch, f"{pago.id:06d}")
        p.drawString(inch + 2*inch, y_start - 1.2*inch, f"$ {float(pago.monto):,.2f}")
        p.drawString(inch + 3.5*inch, y_start - 1.2*inch, usuario.nombre if usuario else "")
        
        # Concepto
        concepto = f"Pago de arbitraje - {retencion.nombre if retencion else 'Pago'}"
        p.drawString(inch + 5*inch, y_start - 1.2*inch, concepto)
        
        # Sección inferior con sombreado
        p.setFillColorRGB(0.96, 0.96, 0.98)  # Gris azulado muy claro
        p.rect(inch, height - 6.7*inch, width - 2*inch, 0.7*inch, fill=1, stroke=0)
        p.setFillColorRGB(0, 0, 0)  # Volver a negro
        p.setStrokeColorRGB(0, 0, 0)  # Volver a negro
        p.setLineWidth(1)
        
        # Campo para firma con estilo
        p.setFont("Helvetica-Bold", 10)
        p.drawString(1.5*inch, height - 6.3*inch, "Firma:")
        p.setLineWidth(0.5)
        p.line(2.3*inch, height - 6.3*inch, 4*inch, height - 6.3*inch)
        
        # Campo para monto con estilo
        p.drawString(4.5*inch, height - 6.3*inch, "TOTAL: $")
        p.setFillColorRGB(1, 1, 1)  # Blanco
        p.setStrokeColorRGB(0.3, 0.3, 0.7)  # Azul oscuro
        p.rect(5.3*inch, height - 6.5*inch, 1.2*inch, 0.4*inch, fill=1)
        p.setFillColorRGB(0, 0, 0)  # Negro
        p.setFont("Helvetica-Bold", 10)
        p.drawString(5.4*inch, height - 6.3*inch, f"{float(pago.monto):,.2f}")
        
        # Fecha con estilo
        p.setFont("Helvetica-Bold", 10)
        p.setFillColorRGB(0, 0, 0)  # Negro
        p.drawString(width - 2.5*inch, height - 6.3*inch, "Fecha:")
        p.setFillColorRGB(1, 1, 1)  # Blanco
        p.rect(width - 1.8*inch, height - 6.5*inch, 0.8*inch, 0.4*inch, fill=1)
        p.setFillColorRGB(0, 0, 0)  # Negro
        p.drawString(width - 1.7*inch, height - 6.3*inch, pago.fecha.strftime('%d/%m/%Y'))
        
        # Añadir pie de página
        p.setFont("Helvetica-Oblique", 8)
        p.setFillColorRGB(0.5, 0.5, 0.5)  # Gris medio
        p.drawCentredString(width/2, 0.5*inch, "Unidad de Árbitros de Río Cuarto - Documento generado automáticamente")
        
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
        """Genera un PDF con el recibo de pago de cuota con formato mejorado"""
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Configurar orientación horizontal
        p.rotate(90)
        p.translate(0, -width)
        
        # Ruta al ícono
        ruta_icono = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'frontend', 'assets', 'Uarclogo.jpg')
        
        # Variables para posicionamiento
        margin = 1 * inch
        content_width = height - (2 * margin)
        
        # Dibujar un rectángulo para el área del recibo
        p.setStrokeColorRGB(0, 0, 0)
        p.setLineWidth(2)
        p.rect(margin, margin, content_width, width - (2 * margin))
        
        # Intentar agregar ícono
        try:
            icono = ImageReader(ruta_icono)
            icono_ancho = 0.8 * inch
            icono_alto = 0.8 * inch
            p.drawImage(
                icono, 
                margin + 0.5 * inch,
                width - margin - 1.3 * inch,
                width=icono_ancho, 
                height=icono_alto
            )
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")
        
        # Obtener usuario/árbitro
        usuario = db.query(models.Usuario).filter(models.Usuario.id == cuota.usuario_id).first()
        
        # Título principal (centrado)
        p.setFont("Helvetica-Bold", 14)
        # Unidad de Árbitros de Río Cuarto - texto vertical a la izquierda
        p.drawString(margin + 0.6 * inch, width - margin - 0.7 * inch, "UNIDAD")
        p.drawString(margin + 0.6 * inch, width - margin - 1.0 * inch, "DE ÁRBITROS")
        p.drawString(margin + 0.6 * inch, width - margin - 1.3 * inch, "DE RÍO CUARTO")
        
        # CUOTA SOCIETARIA (título grande centrado)
        title_width = p.stringWidth("CUOTA SOCIETARIA", "Helvetica-Bold", 16)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(margin + (content_width - title_width)/2, width - margin - 0.8 * inch, "CUOTA SOCIETARIA")
        
        # Número de recibo (alineado a la derecha)
        p.setFont("Helvetica-Bold", 12)
        recibo_num = f"RECIBO Nº {cuota.id:06d}"
        recibo_width = p.stringWidth(recibo_num, "Helvetica-Bold", 12)
        p.drawString(margin + content_width - recibo_width - 0.5 * inch, width - margin - 1.2 * inch, recibo_num)
        
        # Línea horizontal decorativa
        p.line(margin + 0.5 * inch, width - margin - 1.5 * inch, margin + content_width - 0.5 * inch, width - margin - 1.5 * inch)
        
        # Contenido del recibo (formulario)
        p.setFont("Helvetica", 11)
        
        # Recibimos de:
        y_pos = width - margin - 2.2 * inch
        p.drawString(margin + 0.7 * inch, y_pos, "Recibimos de:")
        p.line(margin + 2.5 * inch, y_pos - 0.1 * inch, margin + content_width - 0.7 * inch, y_pos - 0.1 * inch)
        p.setFont("Helvetica", 10)
        p.drawString(margin + 2.6 * inch, y_pos, usuario.nombre if usuario else "")
        
        # La suma de pesos:
        y_pos = width - margin - 2.9 * inch
        p.setFont("Helvetica", 11)
        p.drawString(margin + 0.7 * inch, y_pos, "La suma de pesos:")
        p.line(margin + 2.5 * inch, y_pos - 0.1 * inch, margin + content_width - 2.2 * inch, y_pos - 0.1 * inch)
        p.setFont("Helvetica", 10)
        monto_texto = self.numero_a_letras(float(cuota.monto_pagado) if cuota.pagado else float(cuota.monto))
        p.drawString(margin + 2.6 * inch, y_pos, monto_texto)
        
        # Rectángulo para el monto
        p.setFillColorRGB(0.9, 0.9, 0.9)  # Gris claro
        p.rect(margin + content_width - 2 * inch, y_pos - 0.3 * inch, 1.3 * inch, 0.4 * inch, fill=1)
        p.setFillColorRGB(0, 0, 0)  # Volver a negro
        
        # Símbolo de pesos y monto
        p.setFont("Helvetica-Bold", 11)
        p.drawString(margin + content_width - 1.95 * inch, y_pos, "$")
        monto_valor = float(cuota.monto_pagado) if cuota.pagado else float(cuota.monto)
        p.drawString(margin + content_width - 1.8 * inch, y_pos, f"{monto_valor:,.2f}")
        
        # Línea para firma en la parte inferior
        y_pos = margin + 1 * inch
        p.line(margin + 1 * inch, y_pos, margin + 3 * inch, y_pos)
        p.setFont("Helvetica", 10)
        p.drawCentredString(margin + 2 * inch, y_pos - 0.3 * inch, "Firma")
        
        # Línea decorativa inferior
        p.line(margin + 0.5 * inch, margin + 0.5 * inch, margin + content_width - 0.5 * inch, margin + 0.5 * inch)
        
        # Fecha
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        p.drawRightString(margin + content_width - 0.7 * inch, margin + 0.7 * inch, f"Fecha: {fecha_actual}")
        
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