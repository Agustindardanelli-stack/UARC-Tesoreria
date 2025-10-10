import smtplib
import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from num2words import num2words
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition


class EmailService:
    def __init__(self, smtp_server, smtp_port, username, password, sender_email):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender = sender_email
        
        # Detectar si usar SendGrid
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.use_sendgrid = bool(self.sendgrid_api_key)
        
        if self.use_sendgrid:
            print("✅ Usando SendGrid API para envío de emails")
        else:
            print("📧 Usando SMTP tradicional para envío de emails")
    
    def _send_email_sendgrid(self, recipient_email, subject, body, pdf_data, filename):
        """Enviar email usando SendGrid API"""
        try:
            # Crear el mensaje
            message = Mail(
                from_email=self.sender,
                to_emails=recipient_email,
                subject=subject,
                html_content=body.replace('\n', '<br>')
            )
            
            # Adjuntar PDF
            pdf_base64 = base64.b64encode(pdf_data).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(pdf_base64)
            attachment.file_type = FileType('application/pdf')
            attachment.file_name = FileName(filename)
            attachment.disposition = Disposition('attachment')
            message.attachment = attachment
            
            # Enviar
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                print(f"✅ Email enviado exitosamente a {recipient_email}")
                return True, "Email enviado exitosamente"
            else:
                print(f"❌ Error al enviar email: {response.status_code}")
                return False, f"Error al enviar email: {response.status_code}"
                
        except Exception as e:
            print(f"❌ Excepción al enviar email: {str(e)}")
            return False, f"Error al enviar email: {str(e)}"
    
    def _send_email_smtp(self, recipient_email, subject, body, pdf_data, filename):
        """Enviar email usando SMTP tradicional (para entorno local)"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Adjuntar PDF
            pdf_attachment = MIMEApplication(pdf_data, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(pdf_attachment)
            
            # Enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"✅ Email SMTP enviado exitosamente a {recipient_email}")
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            print(f"❌ Error SMTP: {str(e)}")
            return False, f"Error al enviar email: {str(e)}"
    
    def send_receipt_email(self, db, cobranza, recipient_email):
        """Enviar recibo de cobranza por email"""
        try:
            # Generar PDF
            pdf_data = self.generate_receipt_pdf(db, cobranza)
            
            # Preparar email
            subject = f"Recibo de Cobranza #{cobranza.numero_recibo}"
            body = f"""
Estimado/a,

Adjuntamos el recibo de cobranza correspondiente a:

Número de Recibo: {cobranza.numero_recibo}
Fecha: {cobranza.fecha.strftime('%d/%m/%Y')}
Monto: ${cobranza.monto:.2f}

Gracias por su pago.

Saludos cordiales,
Unidad de Árbitros Río Cuarto
            """
            
            filename = f"Recibo_{cobranza.numero_recibo}.pdf"
            
            # Decidir método de envío
            if self.use_sendgrid:
                return self._send_email_sendgrid(recipient_email, subject, body, pdf_data, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf_data, filename)
                
        except Exception as e:
            print(f"❌ Error al enviar recibo: {str(e)}")
            return False, f"Error al enviar recibo: {str(e)}"
    
    def send_payment_receipt_email(self, db, orden_pago, recipient_email):
        """Enviar orden de pago por email"""
        try:
            # Generar PDF
            pdf_data = self.generate_payment_receipt_pdf(db, orden_pago)
            
            # Preparar email
            subject = f"Orden de Pago #{orden_pago.numero_orden}"
            body = f"""
Estimado/a,

Adjuntamos la orden de pago correspondiente a:

Número de Orden: {orden_pago.numero_orden}
Fecha: {orden_pago.fecha.strftime('%d/%m/%Y')}
Monto: ${orden_pago.monto:.2f}

Saludos cordiales,
Unidad de Árbitros Río Cuarto
            """
            
            filename = f"Orden_Pago_{orden_pago.numero_orden}.pdf"
            
            # Decidir método de envío
            if self.use_sendgrid:
                return self._send_email_sendgrid(recipient_email, subject, body, pdf_data, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf_data, filename)
                
        except Exception as e:
            print(f"❌ Error al enviar orden de pago: {str(e)}")
            return False, f"Error al enviar orden de pago: {str(e)}"
    
    def send_cuota_receipt_email(self, db, pago_cuota, recipient_email):
        """Enviar recibo de cuota por email"""
        try:
            # Generar PDF
            pdf_data = self.generate_cuota_receipt_pdf(db, pago_cuota)
            
            # Preparar email
            subject = f"Recibo de Cuota #{pago_cuota.numero_recibo}"
            body = f"""
Estimado/a,

Adjuntamos el recibo de pago de cuota correspondiente a:

Número de Recibo: {pago_cuota.numero_recibo}
Fecha: {pago_cuota.fecha_pago.strftime('%d/%m/%Y')}
Monto: ${pago_cuota.monto_pagado:.2f}

Gracias por su pago.

Saludos cordiales,
Unidad de Árbitros Río Cuarto
            """
            
            filename = f"Recibo_Cuota_{pago_cuota.numero_recibo}.pdf"
            
            # Decidir método de envío
            if self.use_sendgrid:
                return self._send_email_sendgrid(recipient_email, subject, body, pdf_data, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf_data, filename)
                
        except Exception as e:
            print(f"❌ Error al enviar recibo de cuota: {str(e)}")
            return False, f"Error al enviar recibo de cuota: {str(e)}"
    
    def generate_receipt_pdf(self, db, cobranza):
        """Generar PDF del recibo de cobranza"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph("RECIBO DE COBRANZA", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Información del recibo
        info_data = [
            ['Número de Recibo:', str(cobranza.numero_recibo)],
            ['Fecha:', cobranza.fecha.strftime('%d/%m/%Y')],
            ['Concepto:', cobranza.concepto],
            ['Monto:', f"${cobranza.monto:.2f}"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Monto en letras
        try:
            monto_letras = num2words(cobranza.monto, lang='es', to='currency')
            elements.append(Paragraph(f"<b>Son:</b> {monto_letras.upper()}", styles['Normal']))
        except:
            pass
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def generate_payment_receipt_pdf(self, db, orden_pago):
        """Generar PDF de orden de pago"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph("ORDEN DE PAGO", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Información de la orden
        info_data = [
            ['Número de Orden:', str(orden_pago.numero_orden)],
            ['Fecha:', orden_pago.fecha.strftime('%d/%m/%Y')],
            ['Concepto:', orden_pago.concepto],
            ['Monto:', f"${orden_pago.monto:.2f}"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Monto en letras
        try:
            monto_letras = num2words(orden_pago.monto, lang='es', to='currency')
            elements.append(Paragraph(f"<b>Son:</b> {monto_letras.upper()}", styles['Normal']))
        except:
            pass
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def generate_cuota_receipt_pdf(self, db, pago_cuota):
        """Generar PDF de recibo de cuota"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph("RECIBO DE PAGO DE CUOTA", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Información del pago
        info_data = [
            ['Número de Recibo:', str(pago_cuota.numero_recibo)],
            ['Fecha de Pago:', pago_cuota.fecha_pago.strftime('%d/%m/%Y')],
            ['Monto Pagado:', f"${pago_cuota.monto_pagado:.2f}"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Monto en letras
        try:
            monto_letras = num2words(pago_cuota.monto_pagado, lang='es', to='currency')
            elements.append(Paragraph(f"<b>Son:</b> {monto_letras.upper()}", styles['Normal']))
        except:
            pass
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data