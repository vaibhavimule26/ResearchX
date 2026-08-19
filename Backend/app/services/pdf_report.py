import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor

def generate_ieee_pdf(title: str, summary_text: str, gaps_text: str, exp_text: str) -> str:
    os.makedirs("uploads/generated_reports", exist_ok=True)
    clean_name = "".join(c for c in title[:20] if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
    file_path = f"uploads/generated_reports/{clean_name or 'paper'}_IEEE.pdf"
    
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    t_style = ParagraphStyle(name='TStyle', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=HexColor("#0E2B5C"), alignment=1)
    h_style = ParagraphStyle(name='HStyle', fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=HexColor("#0E2B5C"), spaceBefore=12)
    b_style = ParagraphStyle(name='BStyle', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8)

    story = [
        Paragraph(title, t_style),
        Spacer(1, 10),
        Paragraph("<b>1. Abstract & Executive Summary</b>", h_style),
        Paragraph(summary_text.replace("\n", "<br/>"), b_style),
        Spacer(1, 10),
        Paragraph("<b>2. Research Gaps & Bottlenecks</b>", h_style),
        Paragraph(gaps_text.replace("\n", "<br/>"), b_style),
        Spacer(1, 10),
        Paragraph("<b>3. Experimental Protocol</b>", h_style),
        Paragraph(exp_text.replace("\n", "<br/>"), b_style),
    ]

    doc.build(story)
    return file_path