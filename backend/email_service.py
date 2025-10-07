import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from sqlalchemy.orm import Session
import models
import base64

# Importar Resend solo si está disponible
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

class EmailService:
    def __init__(self, smtp_server, smtp_port, username, password, sender_email):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender = sender_email
        
        # Detectar si usar Resend
        self.resend_api_key = os.getenv('RESEND_API_KEY')
        self.use_resend = bool(self.resend_api_key and RESEND_AVAILABLE)
        
        if self.use_resend:
            print("✅ Usando Resend API para envío de emails")
        else:
            print("📧 Usando SMTP tradicional para envío de emails")
    
    def _send_email_resend(self, recipient_email, subject, body, pdf_data, filename):
        """Enviar email usando Resend API"""
        try:
            resend.api_key = self.resend_api_key
            
            # Codificar PDF en base64
            pdf_base64 = base64.b64encode(pdf_data).decode()
            
            params = {
                "from": f"Unidad de Árbitros <{self.sender}>",
                "reply_to": self.sender,  # Las respuestas van al email de UARC
                "to": [recipient_email],
                "subject": subject,
                "html": body.replace('\n', '<br>'),
                "attachments": [{
                    "filename": filename,
                    "content": pdf_base64
                }]
            }
            
            email = resend.Emails.send(params)
            print(f"✅ Resend response: {email}")
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            print(f"❌ Error con Resend: {e}")
            return False, f"Error al enviar email: {str(e)}"
    
    def _send_email_smtp(self, recipient_email, subject, body, pdf_data, filename):
        """Enviar email usando SMTP tradicional"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            attachment = MIMEApplication(pdf_data, _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"✅ Email enviado via SMTP")
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            print(f"❌ Error con SMTP: {e}")
            return False, f"Error al enviar email: {str(e)}"

    def get_logo_path(self):
        """Encontrar la ruta correcta del logo"""
        possible_paths = [
            r'C:\Users\agusd\Desktop\Abuela Coca\uarc-tesoreria\frontend\assets\UarcLogo.png',
            '/opt/render/project/src/frontend/assets/UarcLogo.png',
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        'frontend', 'assets', 'UarcLogo.png')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError("No se encontró el logo UarcLogo.png")

    def load_logo(self, pdf_canvas, width, height):
        """Cargar y dibujar el logo en el PDF"""
        try:
            ruta_icono = self.get_logo_path()
            icono = ImageReader(ruta_icono)
            icono_ancho = 1.5 * inch
            icono_alto = 1.5 * inch
            
            pdf_canvas.drawImage(
                icono, 
                0.5 * inch,
                height - 1.5 * inch,
                width=icono_ancho, 
                height=icono_alto
            )
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

    def generate_receipt_pdf(self, db: Session, cobranza):
        """Genera un PDF con el recibo de la cobranza con diseño moderno y detallado"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        margin = 0.75 * inch
        accent_color = (0.1, 0.5, 0.7)
        
        p.setFillColorRGB(0.95, 0.95, 1)
        p.rect(margin/2, margin/2, width - margin, height - margin, fill=1, stroke=0)
        
        p.setStrokeColorRGB(*accent_color)
        p.setLineWidth(2)
        p.rect(margin/2, margin/2, width - margin, height - margin)
        
        self.load_logo(p, margin + 1*inch, height - margin - inch)
        
        p.setFillColorRGB(*accent_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, height - 1.5*inch, "UNIDAD DE ÁRBITROS DE RÍO CUARTO")
        
        if hasattr(cobranza, 'tipo_documento') and cobranza.tipo_documento == "factura":
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, height - 2*inch, "FACTURA/RECIBO")
        else:
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, height - 2*inch, "RECIBO DE COBRANZA")
        
        usuario = db.query(models.Usuario).filter(models.Usuario.id == cobranza.usuario_id).first()
        
        retencion = None
        retencion_info = "Sin retención"
        if cobranza.retencion_id:
            retencion = db.query(models.Retencion).filter(models.Retencion.id == cobranza.retencion_id).first()
            if retencion:
                retencion_info = f"{retencion.nombre} - ${float(retencion.monto):,.2f}"
        
        p.setFont("Helvetica", 12)
        p.setFillColorRGB(0, 0, 0)
        
        partida = db.query(models.Partida).filter(
            models.Partida.cobranza_id == cobranza.id
        ).first()
        
        if hasattr(cobranza, 'tipo_documento') and cobranza.tipo_documento == "factura":
            num_doc = cobranza.numero_factura if hasattr(cobranza, 'numero_factura') and cobranza.numero_factura else cobranza.id
            p.drawRightString(width - margin, height - 2.5*inch, f"N° Factura: {num_doc}")
        else:
            if partida and partida.recibo_factura and partida.recibo_factura.startswith("REC-"):
                numero_recibo = partida.recibo_factura
            else:
                numero_recibo = f"REC-{cobranza.id:05d}"
            
            p.drawRightString(width - margin, height - 2.5*inch, f"N° Recibo: {numero_recibo}")
        
        info_y = height - 3.5*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, info_y, "Datos de la Cobranza")
        
        p.setFont("Helvetica", 11)
        linea_altura = 0.3*inch
        
        campos = [
            ("Fecha:", cobranza.fecha.strftime('%d/%m/%Y')),
        ]
        
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
        
        descripcion = cobranza.descripcion if cobranza.descripcion else "Sin descripción"
        p.setFont("Helvetica-Bold", 10)
        p.drawString(margin, info_y - (len(campos)+1)*linea_altura, "Descripción:")
        p.setFont("Helvetica", 10)
        
        palabras = descripcion.split()
        lineas = []
        linea_actual = []
        ancho_maximo = 60
        
        for palabra in palabras:
            linea_actual.append(palabra)
            if len(' '.join(linea_actual)) > ancho_maximo:
                linea_actual.pop()
                lineas.append(' '.join(linea_actual))
                linea_actual = [palabra]
        if linea_actual:
            lineas.append(' '.join(linea_actual))
        
        for i, linea in enumerate(lineas):
            p.drawString(margin + 2*inch, info_y - (len(campos)+1+i)*linea_altura, linea)
        
        p.setFont("Helvetica-Bold", 10)
        y_pos = info_y - (len(campos)+1+len(lineas))*linea_altura
        p.drawString(margin, y_pos, "Monto en letras:")
        p.setFont("Helvetica", 10)
        monto_texto = self.numero_a_letras(float(cobranza.monto))
        p.drawString(margin + 2*inch, y_pos, monto_texto)
        
        firma_y = margin + 2*inch
        p.setFont("Helvetica", 10)
        p.drawString(margin, firma_y + linea_altura, "Firma:")
        p.line(margin + inch, firma_y, margin + 4*inch, firma_y)
        
        p.setFont("Helvetica", 8)
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.drawString(margin, margin, "Unidad de Árbitros de Río Cuarto")
        p.drawRightString(width - margin, margin, datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()

    def send_receipt_email(self, db: Session, cobranza, recipient_email):
        if hasattr(cobranza, 'tipo_documento') and cobranza.tipo_documento == "factura":
            print(f"No se envía correo para facturas: ID {cobranza.id}")
            return False, "No se envía correo para facturas"
        
        try:
            partida = db.query(models.Partida).filter(
                models.Partida.cobranza_id == cobranza.id
            ).first()
            
            if partida and partida.recibo_factura and partida.recibo_factura.startswith("REC-"):
                numero_recibo = partida.recibo_factura
                subject = f"Recibo de Cobranza {numero_recibo}"
                filename = f"{numero_recibo}.pdf"
            else:
                subject = f"Recibo de Cobranza #{cobranza.id}"
                filename = f"Recibo_{cobranza.id}.pdf"
            
            body = """
            Estimado/a usuario,
            
            Adjunto encontrará el recibo correspondiente a su pago reciente.
            
            Gracias por su preferencia.
            
            Unidad de Árbitros de Río Cuarto
            """
            
            pdf = self.generate_receipt_pdf(db, cobranza)
            
            # Decidir qué método usar
            if self.use_resend:
                return self._send_email_resend(recipient_email, subject, body, pdf, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf, filename)
            
        except Exception as e:
            print(f"Error detallado: {e}")
            return False, f"Error al enviar email: {str(e)}"

    def numero_a_letras(self, numero):
        """Convierte un número a su representación en letras"""
        try:
            from num2words import num2words
            return num2words(numero, lang='es') + " pesos"
        except:
            return f"{numero:,.2f} pesos"

    def generate_payment_receipt_pdf(self, db: Session, pago):
        """Genera un PDF con el recibo del pago"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        margin = 0.75 * inch
        accent_color = (0.1, 0.5, 0.7)
        
        p.setFillColorRGB(0.95, 0.95, 1)
        p.rect(margin/2, margin/2, width - margin, height - margin, fill=1, stroke=0)
        
        p.setStrokeColorRGB(*accent_color)
        p.setLineWidth(2)
        p.rect(margin/2, margin/2, width - margin, height - margin)
        
        self.load_logo(p, margin + 1*inch, height - margin - inch)
        
        p.setFillColorRGB(*accent_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, height - 1.5*inch, "UNIDAD DE ÁRBITROS DE RÍO CUARTO")
        
        if hasattr(pago, 'tipo_documento') and pago.tipo_documento == "factura":
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, height - 2*inch, "FACTURA/RECIBO DE PAGO")
        else:
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, height - 2*inch, "ORDEN DE PAGO")
        
        usuario = db.query(models.Usuario).filter(models.Usuario.id == pago.usuario_id).first()
        
        p.setFont("Helvetica", 12)
        p.setFillColorRGB(0, 0, 0)
        
        partida = db.query(models.Partida).filter(
            models.Partida.pago_id == pago.id
        ).first()
        
        if hasattr(pago, 'tipo_documento') and pago.tipo_documento == "factura":
            num_doc = pago.numero_factura if hasattr(pago, 'numero_factura') and pago.numero_factura else pago.id
            p.drawRightString(width - margin, height - 2.5*inch, f"N° Factura: {num_doc}")
        else:
            if partida and partida.recibo_factura and partida.recibo_factura.startswith("O.P-"):
                numero_orden = partida.recibo_factura
            else:
                numero_orden = f"O.P-{pago.id:05d}"
            
            p.drawRightString(width - margin, height - 2.5*inch, f"N° Orden: {numero_orden}")
        
        info_y = height - 3.5*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, info_y, "Datos del Pago")
        
        p.setFont("Helvetica", 11)
        linea_altura = 0.3*inch
        
        campos = [
            ("Fecha:", pago.fecha.strftime('%d/%m/%Y')),
        ]
        
        if hasattr(pago, 'tipo_documento') and pago.tipo_documento == "factura" and hasattr(pago, 'razon_social') and pago.razon_social:
            campos.append(("Razón Social:", pago.razon_social))
        else:
            campos.append(("Beneficiario:", usuario.nombre if usuario else "No especificado"))
            
        campos.append(("Monto:", f"$ {float(pago.monto):,.2f}"))
        
        descripcion = pago.descripcion if hasattr(pago, 'descripcion') and pago.descripcion else "Sin descripción"
        campos.append(("Descripción:", descripcion))
        
        for i, (etiqueta, valor) in enumerate(campos):
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margin, info_y - (i+1)*linea_altura, etiqueta)
            p.setFont("Helvetica", 10)
            p.drawString(margin + 2*inch, info_y - (i+1)*linea_altura, str(valor))
        
        firma_y = margin + 2*inch
        p.setFont("Helvetica", 10)
        p.drawString(margin, firma_y + linea_altura, "Firma:")
        p.line(margin + inch, firma_y, margin + 4*inch, firma_y)
        
        p.setFont("Helvetica", 8)
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.drawString(margin, margin, "Unidad de Árbitros de Río Cuarto")
        p.drawRightString(width - margin, margin, datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    def send_payment_receipt_email(self, db: Session, pago, recipient_email):
        if hasattr(pago, 'tipo_documento') and pago.tipo_documento == "factura":
            print(f"No se envía correo para facturas de pago: ID {pago.id}")
            return False, "No se envía correo para facturas de pago"
        
        try:
            partida = db.query(models.Partida).filter(
                models.Partida.pago_id == pago.id
            ).first()
            
            if partida and partida.recibo_factura and partida.recibo_factura.startswith("O.P-"):
                numero_orden = partida.recibo_factura
                subject = f"Orden de Pago {numero_orden}"
                filename = f"{numero_orden}.pdf"
            else:
                subject = f"Orden de Pago #{pago.id}"
                filename = f"OrdenPago_{pago.id}.pdf"
            
            body = """
            Estimado/a usuario,
            
            Adjunto encontrará la orden de pago correspondiente.
            
            Gracias.
            
            Unidad de Árbitros de Río Cuarto
            """
            
            pdf = self.generate_payment_receipt_pdf(db, pago)
            
            # Decidir qué método usar
            if self.use_resend:
                return self._send_email_resend(recipient_email, subject, body, pdf, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf, filename)
            
        except Exception as e:
            print(f"Error detallado: {e}")
            return False, f"Error al enviar email: {str(e)}"
        
    def generate_cuota_receipt_pdf(self, db: Session, cuota):
        """Genera un PDF con el recibo de pago de cuota"""
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        self.load_logo(p, width, height)
        
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width/2, height - 1 * inch, "UNIDAD DE ÁRBITROS DE RÍO CUARTO")
        p.drawCentredString(width/2, height - 1.5 * inch, "CUOTA SOCIETARIA")
        
        p.setFont("Helvetica-Bold", 12)
        p.drawRightString(width - 1 * inch, height - 1.5 * inch, f"RECIBO Nº {cuota.id:06d}")
        
        usuario = db.query(models.Usuario).filter(models.Usuario.id == cuota.usuario_id).first()
        
        p.setFont("Helvetica", 12)
        
        p.drawString(1 * inch, height - 3 * inch, "Recibimos de:")
        p.line(3 * inch, height - 3 * inch, width - 2 * inch, height - 3 * inch)
        p.drawString(3.2 * inch, height - 3 * inch, usuario.nombre if usuario else "")
        
        p.drawString(1 * inch, height - 4 * inch, "La suma de pesos:")
        p.line(3 * inch, height - 4 * inch, width - 2 * inch, height - 4 * inch)
        
        monto_valor = float(cuota.monto_pagado) if cuota.pagado else float(cuota.monto)
        monto_texto = self.numero_a_letras(monto_valor)
        p.drawString(3.2 * inch, height - 4 * inch, monto_texto)
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1 * inch, height - 5 * inch, "$ ")
        p.drawString(2 * inch, height - 5 * inch, f"{monto_valor:,.2f}")
        
        p.setFont("Helvetica", 10)
        p.line(1 * inch, 2 * inch, 5 * inch, 2 * inch)
        p.drawCentredString(3 * inch, 1.7 * inch, "Firma")
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        p.drawRightString(width - 1 * inch, 1.7 * inch, f"Fecha: {fecha_actual}")
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    def send_cuota_receipt_email(self, db: Session, cuota, recipient_email):
        try:
            subject = f"Recibo de Cuota Societaria - {cuota.fecha.strftime('%B %Y')}"
            filename = f"Cuota_Societaria_{cuota.id}.pdf"
            
            body = """
            Estimado/a socio/a,
            
            Adjunto encontrará el recibo correspondiente a su cuota societaria.
            
            Gracias por formar parte de nuestra unidad.
            
            Unidad de Árbitros de Río Cuarto
            """
            
            pdf = self.generate_cuota_receipt_pdf(db, cuota)
            
            # Decidir qué método usar
            if self.use_resend:
                return self._send_email_resend(recipient_email, subject, body, pdf, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf, filename)
            
        except Exception as e:
            print(f"Error detallado: {e}")
            return False, f"Error al enviar email: {str(e)}"