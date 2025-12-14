import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


from flask import Flask, request, render_template_string, make_response
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import os

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Parte Diario</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&family=Roboto:wght@300;400&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Roboto', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-family: 'Poppins', sans-serif;
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #3498db, #2c3e50);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header p {
            color: #7f8c8d;
            font-size: 1.1em;
        }

        .form-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #2c3e50;
            font-family: 'Poppins', sans-serif;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s ease;
            font-family: 'Roboto', sans-serif;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            border-color: #3498db;
            outline: none;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }

        .form-group textarea {
            min-height: 120px;
            resize: vertical;
        }

        .checkbox-group {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 10px;
        }

        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .checkbox-item input[type="checkbox"] {
            width: auto;
        }

        .btn-submit {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 16px 40px;
            font-size: 18px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Poppins', sans-serif;
            font-weight: 500;
            display: block;
            margin: 0 auto;
            min-width: 200px;
        }

        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(52, 152, 219, 0.3);
        }

        .parte-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            margin-top: 30px;
            border-left: 5px solid #3498db;
        }

        .parte-header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }

        .parte-title {
            font-family: 'Poppins', sans-serif;
            color: #2c3e50;
            font-size: 2.2em;
            margin-bottom: 10px;
        }

        .parte-subtitle {
            color: #7f8c8d;
            font-size: 1.2em;
        }

        .parte-section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }

        .section-title {
            font-family: 'Poppins', sans-serif;
            color: #3498db;
            font-size: 1.3em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }

        .section-content {
            color: #2c3e50;
            line-height: 1.6;
            white-space: pre-line;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }

        .info-item {
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        }

        .info-label {
            font-weight: 600;
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .info-value {
            color: #2c3e50;
            font-size: 1.1em;
        }

        .signature-section {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px dashed #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .action-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
            flex-wrap: wrap;
        }

        .btn-pdf {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
            border: none;
            padding: 15px 35px;
            border-radius: 8px;
            cursor: pointer;
            font-family: 'Poppins', sans-serif;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            font-size: 16px;
        }

        .btn-print {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 15px 35px;
            border-radius: 8px;
            cursor: pointer;
            font-family: 'Poppins', sans-serif;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 16px;
        }

        .btn-back {
            background: linear-gradient(45deg, #95a5a6, #7f8c8d);
            color: white;
            border: none;
            padding: 15px 35px;
            border-radius: 8px;
            cursor: pointer;
            font-family: 'Poppins', sans-serif;
            font-weight: 500;
            text-decoration: none;
            display: inline-block;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 16px;
        }

        @media print {
            body {
                background: white;
            }
            .parte-container {
                box-shadow: none;
                border: none;
            }
            .action-buttons {
                display: none;
            }
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-good { background-color: #2ecc71; }
        .status-regular { background-color: #f39c12; }
        .status-bad { background-color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Sistema de Parte Diario</h1>
            <p>Registro completo de atención al paciente</p>
        </div>

        <div class="form-container">
            <form action="/generar" method="post">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="paciente">👤 Nombre del Paciente *</label>
                        <input type="text" id="paciente" name="paciente" required placeholder="Ingrese nombre completo">
                    </div>

                    <div class="form-group">
                        <label for="cuidadora">👩‍⚕️ Nombre de la Cuidadora *</label>
                        <input type="text" id="cuidadora" name="cuidadora" required placeholder="Nombre completo de la cuidadora">
                    </div>

                    <div class="form-group">
                        <label for="fecha">📅 Fecha *</label>
                        <input type="date" id="fecha" name="fecha" value="{{ fecha_hoy }}" required>
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label>😊 Estado General del Paciente</label>
                        <div class="checkbox-group">
                            <label class="checkbox-item">
                                <input type="radio" name="estado_general" value="Bueno" checked> 
                                <span class="status-indicator status-good"></span> Bueno
                            </label>
                            <label class="checkbox-item">
                                <input type="radio" name="estado_general" value="Regular">
                                <span class="status-indicator status-regular"></span> Regular
                            </label>
                            <label class="checkbox-item">
                                <input type="radio" name="estado_general" value="Malo">
                                <span class="status-indicator status-bad"></span> Malo
                            </label>
                        </div>
                        <textarea name="estado_detalle" placeholder="Describa el estado general del paciente, humor, energía, etc."></textarea>
                    </div>

                    <div class="form-group">
                        <label>💊 Medicación Administrada</label>
                        <textarea name="medicacion" placeholder="Lista de medicamentos, dosis y horarios"></textarea>
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label>🍽️ Alimentación</label>
                        <textarea name="alimentacion" placeholder="Describa comidas, cantidades, horarios y aceptación"></textarea>
                    </div>

                    <div class="form-group">
                        <label>💧 Hidratación</label>
                        <textarea name="hidratacion" placeholder="Registro de líquidos consumidos"></textarea>
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label>🚽 Eliminación</label>
                        <textarea name="eliminacion" placeholder="Registro de deposiciones y micciones"></textarea>
                    </div>

                    <div class="form-group">
                        <label>🛌 Descanso y Sueño</label>
                        <textarea name="descanso" placeholder="Horas de sueño, calidad del descanso"></textarea>
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label>🚶‍♂️ Movilidad y Ejercicio</label>
                        <textarea name="movilidad" placeholder="Actividad física, paseos, ejercicios realizados"></textarea>
                    </div>

                    <div class="form-group">
                        <label>🧼 Higiene y Cuidados</label>
                        <textarea name="higiene" placeholder="Baño, aseo, cambios de ropa, cuidados especiales"></textarea>
                    </div>
                </div>

                <div class="form-group">
                    <label>📝 Observaciones y Notas Importantes</label>
                    <textarea name="observaciones" placeholder="Incidentes, cambios notorios, llamadas al médico, etc."></textarea>
                </div>

                <div class="form-group">
                    <label>⚠️ Signos de Alerta</label>
                    <textarea name="signos_alerta" placeholder="Síntomas preocupantes, cambios que requieren atención"></textarea>
                </div>

                <button type="submit" class="btn-submit">📄 Generar Parte Diario</button>
            </form>
        </div>
    </div>
</body>
</html>
'''


def generar_pdf(datos):
    """Genera un PDF profesional del parte diario"""
    buffer = BytesIO()

    # Configurar el documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Estilos
    styles = getSampleStyleSheet()

    # Crear estilos personalizados
    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=30
    )

    subtitulo_style = ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=40
    )

    seccion_style = ParagraphStyle(
        'Seccion',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#3498db'),
        spaceAfter=12,
        spaceBefore=20
    )

    contenido_style = ParagraphStyle(
        'Contenido',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        leading=14,
        spaceAfter=10
    )

    firma_style = ParagraphStyle(
        'Firma',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceBefore=20
    )

    # Convertir fecha
    fecha_str = datos.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        fecha_formateada = fecha.strftime('%d/%m/%Y')
    except:
        fecha_formateada = datetime.now().strftime('%d/%m/%Y')

    # Crear contenido
    elementos = []

    # Título
    elementos.append(Paragraph("PARTE DIARIO DE ATENCIÓN", titulo_style))
    elementos.append(Paragraph("Registro completo de cuidados y observaciones", subtitulo_style))

    # Información básica
    info_data = [
        ['Paciente:', datos.get('paciente', 'No especificado')],
        ['Cuidadora:', datos.get('cuidadora', 'No especificada')],
        ['Fecha:', fecha_formateada],
        ['Estado General:', datos.get('estado_general', 'No evaluado')]
    ]

    info_table = Table(info_data, colWidths=[100, 400])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elementos.append(info_table)
    elementos.append(Spacer(1, 30))

    # Función para agregar secciones
    def agregar_seccion(titulo, contenido):
        if contenido and contenido.strip():
            elementos.append(Paragraph(titulo, seccion_style))
            elementos.append(Paragraph(contenido, contenido_style))
            elementos.append(Spacer(1, 15))

    # Secciones dinámicas
    agregar_seccion("ESTADO GENERAL", datos.get('estado_detalle', ''))
    agregar_seccion("MEDICACIÓN ADMINISTRADA", datos.get('medicacion', ''))
    agregar_seccion("ALIMENTACIÓN", datos.get('alimentacion', ''))
    agregar_seccion("HIDRATACIÓN", datos.get('hidratacion', ''))
    agregar_seccion("ELIMINACIÓN", datos.get('eliminacion', ''))
    agregar_seccion("DESCANSO Y SUEÑO", datos.get('descanso', ''))
    agregar_seccion("MOVILIDAD Y EJERCICIO", datos.get('movilidad', ''))
    agregar_seccion("HIGIENE Y CUIDADOS", datos.get('higiene', ''))

    # Signos de alerta (si existen)
    if datos.get('signos_alerta'):
        alerta_style = ParagraphStyle(
            'Alerta',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#721c24'),
            backColor=colors.HexColor('#f8d7da'),
            borderPadding=10,
            leading=14
        )
        elementos.append(Paragraph("SIGNOS DE ALERTA:", seccion_style))
        elementos.append(Paragraph(datos.get('signos_alerta'), alerta_style))
        elementos.append(Spacer(1, 15))

    agregar_seccion("OBSERVACIONES ADICIONALES", datos.get('observaciones', ''))

    # Firma
    elementos.append(Spacer(1, 40))
    elementos.append(Paragraph("___________________________________", firma_style))
    elementos.append(Paragraph(datos.get('cuidadora', 'Cuidadora Responsable'), firma_style))
    elementos.append(Paragraph("Cuidadora Responsable", firma_style))

    # Fecha de generación
    elementos.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.gray,
        alignment=TA_CENTER
    )
    elementos.append(Paragraph(
        f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
        footer_style
    ))

    # Construir PDF
    doc.build(elementos)

    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()

    return pdf

def subir_a_drive(pdf_bytes, nombre_archivo):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    creds_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    credentials = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=SCOPES
    )

    service = build('drive', 'v3', credentials=credentials)

    file_metadata = {
        'name': nombre_archivo,
        'parents': ['1AFEeTIMiGwCr2cgEzBe-lJ9XE9YeeZ86']
    }

    media = MediaIoBaseUpload(
        BytesIO(pdf_bytes),
        mimetype='application/pdf'
    )

    service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()



@app.route('/')
def index():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    return render_template_string(HTML_TEMPLATE, fecha_hoy=fecha_hoy)



@app.route('/generar', methods=['POST'])
def generar():
    datos = request.form

    # Generar PDF
    pdf_content = generar_pdf(datos)

    paciente = datos.get('paciente', 'paciente').replace(' ', '_')
    fecha = datos.get('fecha', datetime.now().strftime('%Y-%m-%d'))

    nombre_pdf = f"parte_diario_{paciente}_{fecha}.pdf"

    # 🔥 Subir automáticamente a Google Drive
    subir_a_drive(pdf_content, nombre_pdf)

    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Parte enviado</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .box {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                text-align: center;
            }
            h1 {
                color: #2ecc71;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>✅ Parte diario enviado</h1>
            <p>El registro fue guardado correctamente.</p>
        </div>
    </body>
    </html>
    '''





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
