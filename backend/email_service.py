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