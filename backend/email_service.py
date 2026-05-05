import smtplib
import os
import base64
import requests
import json
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


def monto_a_letras(monto: float) -> str:
    """Convierte un monto a letras en pesos argentinos."""
    try:
        entero = int(monto)
        centavos = round((monto - entero) * 100)
        letras = num2words(entero, lang='es').upper()
        if centavos > 0:
            return f"{letras} PESOS CON {centavos:02d}/100"
        return f"{letras} PESOS CON CERO CENTAVOS"
    except Exception:
        return ""


class EmailService:
    def __init__(self, smtp_server, smtp_port, username, password, sender_email):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender = sender_email
        
        # Detectar si usar Brevo (antes Sendinblue)
        self.brevo_api_key = os.getenv('BREVO_API_KEY')
        self.use_brevo = bool(self.brevo_api_key)
        
        if self.use_brevo:
            print("✅ Usando Brevo API para envío de emails")
        else:
            print("📧 Usando SMTP tradicional para envío de emails")
    
    def _send_email_brevo(self, recipient_email, subject, body, pdf_data, filename):
        """Enviar email usando Brevo API (antes Sendinblue)"""
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            
            headers = {
                "accept": "application/json",
                "api-key": self.brevo_api_key,
                "content-type": "application/json"
            }
            
            payload = {
                "sender": {
                    "name": "UARC Río Cuarto",
                    "email": self.sender
                },
                "to": [
                    {
                        "email": recipient_email
                    }
                ],
                "subject": subject,
                "htmlContent": body.replace('\n', '<br>')
            }
            
            if pdf_data:
                pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                payload["attachment"] = [
                    {
                        "content": pdf_base64,
                        "name": filename
                    }
                ]
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201, 202]:
                print(f"✅ Email enviado exitosamente a {recipient_email}")
                return True, "Email enviado exitosamente"
            else:
                error_msg = response.text
                print(f"❌ Error al enviar email: {response.status_code} - {error_msg}")
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
            
            pdf_attachment = MIMEApplication(pdf_data, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(pdf_attachment)
            
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
            from models import Partida
            
            partida = db.query(Partida).filter(Partida.cobranza_id == cobranza.id).first()
            
            if cobranza.tipo_documento == "factura":
                numero_documento = cobranza.numero_factura or "S/N"
                tipo_doc_texto = "Factura/Recibo"
            else:
                numero_documento = partida.recibo_factura if partida else f"REC-{cobranza.id}"
                tipo_doc_texto = "Recibo"
            
            pdf_data = self.generate_receipt_pdf(db, cobranza, numero_documento, tipo_doc_texto)
            
            subject = f"{tipo_doc_texto} #{numero_documento}"
            body = f"""
Estimado/a,

Adjuntamos el {tipo_doc_texto.lower()} correspondiente a:

Número de {tipo_doc_texto}: {numero_documento}
Fecha: {cobranza.fecha.strftime('%d/%m/%Y')}
Monto: ${cobranza.monto:.2f}

Gracias por su pago.

Saludos cordiales,
Unidad de Árbitros Río Cuarto
            """
            
            filename = f"{tipo_doc_texto.replace('/', '_')}_{numero_documento.replace('/', '_')}.pdf"
            
            if self.use_brevo:
                return self._send_email_brevo(recipient_email, subject, body, pdf_data, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf_data, filename)
                
        except Exception as e:
            print(f"❌ Error al enviar recibo: {str(e)}")
            return False, f"Error al enviar recibo: {str(e)}"
    
    def send_payment_receipt_email(self, db, pago, recipient_email):
        """Enviar orden de pago por email"""
        try:
            from models import Partida
            
            partida = db.query(Partida).filter(Partida.pago_id == pago.id).first()
            
            if pago.tipo_documento == "factura":
                numero_documento = pago.numero_factura or "S/N"
                tipo_doc_texto = "Factura/Recibo"
            else:
                numero_documento = partida.recibo_factura if partida else f"O.P-{pago.id}"
                tipo_doc_texto = "Orden de Pago"
            
            pdf_data = self.generate_payment_receipt_pdf(db, pago, numero_documento, tipo_doc_texto)
            
            subject = f"{tipo_doc_texto} #{numero_documento}"
            body = f"""
Estimado/a,

Adjuntamos la {tipo_doc_texto.lower()} correspondiente a:

Número de {tipo_doc_texto}: {numero_documento}
Fecha: {pago.fecha.strftime('%d/%m/%Y')}
Monto: ${pago.monto:.2f}

Saludos cordiales,
Unidad de Árbitros Río Cuarto
            """
            
            filename = f"{tipo_doc_texto.replace('/', '_')}_{numero_documento.replace('/', '_')}.pdf"
            
            if self.use_brevo:
                return self._send_email_brevo(recipient_email, subject, body, pdf_data, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf_data, filename)
                
        except Exception as e:
            print(f"❌ Error al enviar orden de pago: {str(e)}")
            return False, f"Error al enviar orden de pago: {str(e)}"
    
    def send_cuota_receipt_email(self, db, cuota, recipient_email):
        """Enviar recibo de cuota por email"""
        try:
            numero_recibo = cuota.nro_comprobante or f"CUOTA-{cuota.id}"
            
            pdf_data = self.generate_cuota_receipt_pdf(db, cuota, numero_recibo)
            
            subject = f"Recibo de Cuota Societaria #{numero_recibo}"
            body = f"""
Estimado/a Socio/a,

Adjuntamos el recibo correspondiente al pago de su cuota societaria:

Número de Recibo: {numero_recibo}
Fecha de Pago: {cuota.fecha_pago.strftime('%d/%m/%Y') if cuota.fecha_pago else 'N/A'}
Monto Pagado: ${cuota.monto_pagado:.2f}

Gracias por mantener su cuota al día.

Saludos cordiales,
Unidad de Árbitros Río Cuarto
            """
            
            filename = f"Recibo_Cuota_{numero_recibo.replace('/', '_')}.pdf"
            
            if self.use_brevo:
                return self._send_email_brevo(recipient_email, subject, body, pdf_data, filename)
            else:
                return self._send_email_smtp(recipient_email, subject, body, pdf_data, filename)
                
        except Exception as e:
            print(f"❌ Error al enviar recibo de cuota: {str(e)}")
            return False, f"Error al enviar recibo de cuota: {str(e)}"
    
    def generate_receipt_pdf(self, db, cobranza, numero_documento, tipo_doc_texto):
        """Generar PDF del recibo de cobranza"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph(tipo_doc_texto.upper(), title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        from models import Usuario
        usuario = db.query(Usuario).filter(Usuario.id == cobranza.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "N/A"
        
        info_data = [
            ['Número:', numero_documento],
            ['Fecha:', cobranza.fecha.strftime('%d/%m/%Y')],
            ['Pagador/Cobrador:', nombre_usuario],
            ['Monto:', f"${cobranza.monto:.2f}"],
        ]
        
        if cobranza.descripcion:
            info_data.append(['Concepto:', cobranza.descripcion])
        
        if cobranza.tipo_documento == "factura" and cobranza.razon_social:
            info_data.append(['Razón Social:', cobranza.razon_social])
        
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
        
        # ✅ FIX: pesos argentinos en lugar de euros
        monto_letras = monto_a_letras(float(cobranza.monto))
        if monto_letras:
            elements.append(Paragraph(f"<b>Son:</b> {monto_letras}", styles['Normal']))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def generate_payment_receipt_pdf(self, db, pago, numero_documento, tipo_doc_texto):
        """Generar PDF de orden de pago"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph(tipo_doc_texto.upper(), title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        from models import Usuario
        usuario = db.query(Usuario).filter(Usuario.id == pago.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "N/A"
        
        info_data = [
            ['Número:', numero_documento],
            ['Fecha:', pago.fecha.strftime('%d/%m/%Y')],
            ['Pagador/Cobrador:', nombre_usuario],
            ['Monto:', f"${pago.monto:.2f}"],
        ]
        
        if pago.descripcion:
            info_data.append(['Concepto:', pago.descripcion])
        
        if pago.tipo_documento == "factura" and pago.razon_social:
            info_data.append(['Razón Social:', pago.razon_social])
        
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

        # ✅ FIX: pesos argentinos en lugar de euros
        monto_letras = monto_a_letras(float(pago.monto))
        if monto_letras:
            elements.append(Paragraph(f"<b>Son:</b> {monto_letras}", styles['Normal']))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def generate_cuota_receipt_pdf(self, db, cuota, numero_recibo):
        """Generar PDF de recibo de cuota"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph("RECIBO DE CUOTA SOCIETARIA", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        from models import Usuario
        usuario = db.query(Usuario).filter(Usuario.id == cuota.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "N/A"
        
        info_data = [
            ['Número de Recibo:', numero_recibo],
            ['Socio:', nombre_usuario],
            ['Fecha de Pago:', cuota.fecha_pago.strftime('%d/%m/%Y') if cuota.fecha_pago else 'N/A'],
            ['Monto Pagado:', f"${cuota.monto_pagado:.2f}"],
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

        # ✅ FIX: pesos argentinos en lugar de euros
        monto_letras = monto_a_letras(float(cuota.monto_pagado))
        if monto_letras:
            elements.append(Paragraph(f"<b>Son:</b> {monto_letras}", styles['Normal']))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data