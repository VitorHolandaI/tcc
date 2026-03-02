from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

class ReportGenerator:
    def __init__(self, report_data, output_file="analysis_report.pdf"):
        self.report_data = report_data
        self.output_file = output_file
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        
    def _setup_styles(self):
        """Configura estilos personalizados para o relatório"""
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER
            ))
        
        if 'CustomHeading2' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomHeading2',
                parent=self.styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue
            ))
        
        if 'CustomBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomBodyText',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=8
            ))
        
        if 'Alert' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Alert',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=colors.red,
                spaceAfter=8
            ))
        
        if 'Conclusion' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Conclusion',
                parent=self.styles['Normal'],
                fontSize=14,
                textColor=colors.darkgreen,
                spaceAfter=12
            ))
    
    def _create_title_page(self, story):
        """Cria a página de título do relatório"""
        story.append(Paragraph("RELATÓRIO DE ANÁLISE DE COMPORTAMENTO", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph("Identificação da Atividade", self.styles['CustomHeading2']))
        story.append(Paragraph(f"Arquivo analisado: {os.path.basename(self.report_data['file_analyzed'])}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"Data da análise: {self.report_data['analysis_date']}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"Total de eventos registrados: {self.report_data['typing_metrics']['total_events']}", self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 0.3*inch))
        story.append(PageBreak())
    
    def _create_typing_metrics_section(self, story):
        """Cria a seção de métricas de digitação"""
        story.append(Paragraph("Métricas de Digitação", self.styles['CustomHeading2']))
        
        data = [
            ["Métrica", "Valor"],
            ["Tempo médio de pressionamento", f"{self.report_data['typing_metrics']['hold_time_avg']} segundos"],
            ["Desvio padrão do tempo de pressionamento", f"{self.report_data['typing_metrics']['hold_time_std']} segundos"],
            ["Tempo médio entre teclas", f"{self.report_data['typing_metrics']['flight_time_avg']} segundos"],
            ["Desvio padrão do tempo entre teclas", f"{self.report_data['typing_metrics']['flight_time_std']} segundos"]
        ]
        
        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        if 'graph_data' in self.report_data:
            story.append(Paragraph("Distribuição de Tempos de Digitação", self.styles['CustomHeading2']))
            img = Image(self.report_data['graph_data'], width=6*inch, height=4*inch)
            story.append(img)
        
        story.append(PageBreak())
    
    def _create_suspicious_commands_section(self, story):
        """Cria a seção de análise de comandos suspeitos"""
        story.append(Paragraph("Análise de Comandos Suspeitos", self.styles['CustomHeading2']))
        
        data = [
            ["Total de Comandos Suspeitos", f"{self.report_data['suspicious_commands']['total_commands']}/{self.report_data['typing_metrics']['total_events']}"],
            ["Porcentagem", f"{self.report_data['suspicious_commands']['suspicious_percentage']}%"]
        ]
        
        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("Sobre a Distância de Manhattan:", self.styles['CustomBodyText']))
        story.append(Paragraph("• A Distância de Manhattan é uma métrica que mede a diferença absoluta entre dois pontos em um espaço n-dimensional", self.styles['CustomBodyText']))
        story.append(Paragraph("• No contexto da análise de digitação, ela é calculada como a soma das diferenças absolutas entre:", self.styles['CustomBodyText']))
        story.append(Paragraph("  - Tempo médio de pressionamento (hold time) do segmento vs. tempo base", self.styles['CustomBodyText']))
        story.append(Paragraph("  - Tempo médio entre teclas (flight time) do segmento vs. tempo base", self.styles['CustomBodyText']))
        story.append(Paragraph("• Um segmento é considerado suspeito quando sua distância de Manhattan excede um limiar determinado", self.styles['CustomBodyText']))
        story.append(Paragraph("• Isso ajuda a identificar padrões de digitação que se desviam significativamente do comportamento normal", self.styles['CustomBodyText']))
        
        story.append(PageBreak())
    
    def _create_outlier_analysis_section(self, story):
        """Cria a seção de análise de outliers"""
        story.append(Paragraph("Análise de Outliers (Z-score)", self.styles['CustomHeading2']))
        story.append(Paragraph("Esta seção mostra a análise de outliers baseada no Z-score para tempos de digitação.", self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.2*inch))
        
        data = [
            ["Métrica", "Número de Outliers"],
            ["Tempo de Pressionamento (Hold Time)", str(self.report_data['outlier_counts']['hold_time_outliers'])],
            ["Tempo Entre Teclas (Flight Time)", str(self.report_data['outlier_counts']['flight_time_outliers'])]
        ]
        
        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("Sobre o Z-score e a Detecção de Outliers:", self.styles['CustomBodyText']))
        story.append(Paragraph("• O Z-score é uma medida estatística que indica quantos desvios padrão um valor está da média da distribuição", self.styles['CustomBodyText']))
        story.append(Paragraph("• É calculado como: Z = (X - μ) / σ, onde:", self.styles['CustomBodyText']))
        story.append(Paragraph("  - X é o valor observado", self.styles['CustomBodyText']))
        story.append(Paragraph("  - μ é a média da distribuição", self.styles['CustomBodyText']))
        story.append(Paragraph("  - σ é o desvio padrão da distribuição", self.styles['CustomBodyText']))
        story.append(Paragraph("• Valores com |Z-score| > 3 são considerados outliers, pois estão a mais de 3 desvios padrão da média", self.styles['CustomBodyText']))
        story.append(Paragraph("• Na análise de digitação, outliers podem indicar:", self.styles['CustomBodyText']))
        story.append(Paragraph("  - Pausas anormais entre teclas", self.styles['CustomBodyText']))
        story.append(Paragraph("  - Tempos de pressionamento inconsistentes", self.styles['CustomBodyText']))
        story.append(Paragraph("  - Possível uso de automação ou comportamento não humano", self.styles['CustomBodyText']))
        
        if self.report_data['outlier_counts']['hold_time_outliers'] > 5 or self.report_data['outlier_counts']['flight_time_outliers'] > 5:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("SINAIS DE ALERTA:", self.styles['Alert']))
            story.append(Paragraph(f"• Número elevado de outliers detectados: {self.report_data['outlier_counts']['hold_time_outliers']} em hold time e {self.report_data['outlier_counts']['flight_time_outliers']} em flight time", self.styles['Alert']))
        
        story.append(PageBreak())
    
    def _create_application_metrics_section(self, story):
        """Cria a seção de métricas por aplicação"""
        story.append(Paragraph("Métricas por Aplicação", self.styles['CustomHeading2']))
        
        data = [["Aplicação", "Duração (s)", "Taxa de Digitação", "Razão Suspeita", "Eventos"]]
        
        for app, metrics in self.report_data['application_metrics'].items():
            data.append([
                app,
                str(metrics['duration']),
                f"{metrics['typing_rate']:.2f}",
                f"{metrics['suspicious_ratio']:.2f}",
                str(metrics['event_count'])
            ])
        
        table = Table(data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        if len(self.report_data['application_metrics']) > 5:
            story.append(Paragraph("SINAIS DE ALERTA:", self.styles['Alert']))
            story.append(Paragraph(f"• Muitas aplicações diferentes utilizadas: {len(self.report_data['application_metrics'])}", self.styles['Alert']))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(PageBreak())
    
    def _create_text_analysis_section(self, story):
        """Cria a seção de análise de trechos de texto"""
        story.append(Paragraph("Análise de Trechos de Texto", self.styles['CustomHeading2']))
        story.append(Paragraph("Esta seção mostra os trechos de texto digitados e os comandos utilizados.", self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.2*inch))
        
        self.styles.add(ParagraphStyle(
            'NormalText',
            parent=self.styles['CustomBodyText'],
            textColor=colors.black
        ))
        self.styles.add(ParagraphStyle(
            'RedText',
            parent=self.styles['CustomBodyText'],
            textColor=colors.red
        ))
        
        data = [["Tipo", "Conteúdo", "Tempo"]]
        
        for segment in self.report_data['text_segments']:
            if segment['type'] == 'typing':
                text = segment['text']
                
                if not text.strip():
                    text = '[espaço]'
                
                style = 'RedText' if segment['is_suspicious'] else 'NormalText'
                content = Paragraph(text, self.styles[style])
                
                time_str = f"{segment['start_time'].strftime('%H:%M:%S')} - {segment['end_time'].strftime('%H:%M:%S')}"
                data.append(["Digitação", content, time_str])
            else:
                command_map = {
                    'copy': '[Ctrl+C] (Copiar)',
                    'paste': '[Ctrl+V] (Colar)',
                    'cut': '[Ctrl+X] (Recortar)'
                }
                command_text = command_map.get(segment['command'], segment['command'].upper())
                content = Paragraph(command_text, self.styles['RedText'])
                data.append(["Comando", content, segment['time']])
        
        col_widths = [1.5*inch, 4*inch, 1.5*inch]
        table = Table(data, colWidths=col_widths, rowHeights=[20] * len(data))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("Legenda:", self.styles['CustomBodyText']))
        story.append(Paragraph("• Texto em preto: Digitação normal", self.styles['CustomBodyText']))
        story.append(Paragraph("• Texto em vermelho: Trechos suspeitos e comandos especiais", self.styles['CustomBodyText']))
        story.append(Paragraph("• Símbolos especiais:", self.styles['CustomBodyText']))
        story.append(Paragraph("  ↵ = Enter", self.styles['CustomBodyText']))
        story.append(Paragraph(" |← = Backspace", self.styles['CustomBodyText']))
        story.append(Paragraph("  →| = Tab (tabulação)", self.styles['CustomBodyText']))
        story.append(Paragraph("  →  ←  ↓  ↑  = Movimento do cursor", self.styles['CustomBodyText']))
        story.append(Paragraph("Sequências de uso da tecla tab podem indicar uso do auto-complete das IDEs", self.styles['CustomBodyText']))
        story.append(PageBreak())
    
    def generate_pdf(self):
        """Gera o relatório em PDF"""
        doc = SimpleDocTemplate(
            self.output_file,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        self._create_title_page(story)
        self._create_typing_metrics_section(story)
        self._create_suspicious_commands_section(story)
        self._create_outlier_analysis_section(story)
        self._create_application_metrics_section(story)
        self._create_text_analysis_section(story)
        
        doc.build(story)
        return self.output_file