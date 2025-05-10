import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import os # For checking if image files exist


def generate_report(json_data_string,name,idx):
    first,last = json_data_string.find('{'),json_data_string.rfind('}')
    json_data_string = json_data_string[first:last+1].replace('₂','2')
    data = json.loads(json_data_string)

    # PDF Document Setup
    output_filename = f"{idx}_{name}_physiological_assessment_report.pdf"
    doc = SimpleDocTemplate(output_filename, pagesize=letter,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle', parent=styles['h1'], fontSize=22, alignment=TA_CENTER, spaceAfter=0.3*inch, textColor=colors.HexColor("#333366")))
    styles.add(ParagraphStyle(name='PatientDetails', parent=styles['Normal'], fontSize=11, spaceAfter=0.1*inch, leading=14))
    styles.add(ParagraphStyle(name='SectionHeading', parent=styles['h2'], fontSize=16, alignment=TA_LEFT, spaceBefore=0.3*inch, spaceAfter=0.15*inch, textColor=colors.HexColor("#4A4A4A"), keepWithNext=1))
    styles.add(ParagraphStyle(name='SubSectionHeading', parent=styles['h3'], fontSize=13, alignment=TA_LEFT, spaceBefore=0.2*inch, spaceAfter=0.1*inch, textColor=colors.HexColor("#5A5A5A"), keepWithNext=1))
    styles.add(ParagraphStyle(name='NormalText', parent=styles['Normal'], fontSize=10, alignment=TA_JUSTIFY, spaceAfter=0.1*inch, leading=14))
    styles.add(ParagraphStyle(name='InterpretationText', parent=styles['Normal'], fontSize=9, alignment=TA_JUSTIFY, spaceAfter=0.05*inch, leading=12, leftIndent=0.2*inch))
    styles.add(ParagraphStyle(name='BulletPoint', parent=styles['NormalText'], bulletIndent=0.25*inch, leftIndent=0.5*inch, spaceAfter=0.05*inch))
    styles.add(ParagraphStyle(name='ImageCaption', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, spaceBefore=0.1*inch, spaceAfter=0.2*inch))


    # Helper function for metrics table
    def create_metrics_table(metrics_data, section_title_style, normal_style, interpretation_style):
        table_data = [[Paragraph("<b>Metric</b>", normal_style), Paragraph("<b>Value</b>", normal_style), Paragraph("<b>Interpretation</b>", normal_style)]]
        for key, metric in metrics_data.items():
            if isinstance(metric, dict) and "metricName" in metric: # Ensure it's a metric entry
                table_data.append([
                    Paragraph(metric.get("metricName", ""), normal_style),
                    Paragraph(str(metric.get("value", "")), normal_style), # Ensure value is string
                    Paragraph(metric.get("interpretation", ""), interpretation_style)
                ])

        if len(table_data) > 1: # Only create table if there are metrics
            table = Table(table_data, colWidths=[2*inch, 1.2*inch, 3.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#DDDDDD")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
            ]))
            return [table, Spacer(1, 0.2*inch)]
        return []


    # --- Build Document ---

    # Report Title
    story.append(Paragraph(data.get("reportTitle", "Physiological Assessment Report"), styles['ReportTitle']))

    # Patient and Assessment Details
    pat_details = data.get("patientAndAssessmentDetails", {})
    story.append(Paragraph(f"<b>Patient Name:</b> {pat_details.get('patientName', 'N/A')}", styles['PatientDetails']))
    story.append(Paragraph(f"<b>Date of Data Collection:</b> {pat_details.get('dateOfDataCollection', 'N/A')}", styles['PatientDetails']))
    story.append(Paragraph(f"<b>Reason for Assessment:</b> {pat_details.get('reasonForAssessment', 'N/A')}", styles['PatientDetails']))
    story.append(Spacer(1, 0.2*inch))

    # Introduction
    intro = data.get("introduction", {})
    if "paragraph" in intro:
        story.append(Paragraph(intro["paragraph"], styles['NormalText']))
        story.append(Spacer(1, 0.2*inch))

    # Heart Rate Variability Analysis
    hrv_analysis = data.get("heartRateVariabilityAnalysis", {})
    if hrv_analysis:
        story.append(Paragraph("HEART RATE VARIABILITY (HRV) ANALYSIS", styles['SectionHeading']))
        if "introductionParagraph" in hrv_analysis:
            story.append(Paragraph(hrv_analysis["introductionParagraph"], styles['NormalText']))
            story.append(Spacer(1, 0.1*inch))

        # Time-Domain Metrics
        time_domain = hrv_analysis.get("timeDomainMetrics", {})
        if time_domain:
            story.append(Paragraph(time_domain.get("sectionTitle", "Time-Domain Metrics"), styles['SubSectionHeading']))
            if "sectionDescription" in time_domain:
                story.append(Paragraph(time_domain["sectionDescription"], styles['NormalText']))
            story.extend(create_metrics_table(time_domain, styles['SubSectionHeading'], styles['NormalText'], styles['InterpretationText']))

        # Frequency-Domain Metrics
        freq_domain = hrv_analysis.get("frequencyDomainMetrics", {})
        if freq_domain:
            story.append(Paragraph(freq_domain.get("sectionTitle", "Frequency-Domain Metrics"), styles['SubSectionHeading']))
            if "sectionDescription" in freq_domain:
                story.append(Paragraph(freq_domain["sectionDescription"], styles['NormalText']))
            story.extend(create_metrics_table(freq_domain, styles['SubSectionHeading'], styles['NormalText'], styles['InterpretationText']))

        # Nonlinear Metrics
        nonlinear = hrv_analysis.get("nonlinearMetrics", {})
        if nonlinear:
            story.append(Paragraph(nonlinear.get("sectionTitle", "Nonlinear Metrics"), styles['SubSectionHeading']))
            if "sectionDescription" in nonlinear:
                story.append(Paragraph(nonlinear["sectionDescription"], styles['NormalText']))
            story.extend(create_metrics_table(nonlinear, styles['SubSectionHeading'], styles['NormalText'], styles['InterpretationText']))
        
        # Per-Window HRV Metrics
        per_window = hrv_analysis.get("perWindowHrvMetrics", {})
        if per_window:
            story.append(Paragraph(per_window.get("sectionTitle", "Per-Window HRV Metrics"), styles['SubSectionHeading']))
            if "sectionDescription" in per_window:
                story.append(Paragraph(per_window["sectionDescription"], styles['NormalText']))
            
            windows_data = per_window.get("windows", [])
            if windows_data:
                headers = [Paragraph(f"<b>{key}</b>", styles['NormalText']) for key in windows_data[0].keys()]
                table_data_pw = [headers]
                for item in windows_data:
                    row = []
                    for key in headers: # Use original keys from header to maintain order
                        # Extract the plain text from the Paragraph object representing the header
                        header_text = key.text.replace('<b>','').replace('</b>','') 
                        value = item.get(header_text, "")
                        if isinstance(value, float):
                            value_str = f"{value:.2f}" # Format floats nicely
                        else:
                            value_str = str(value)
                        row.append(Paragraph(value_str, styles['NormalText']))
                    table_data_pw.append(row)
                
                col_count = len(headers)
                # Attempt to make columns somewhat equal, with first column slightly wider
                if col_count > 0:
                    first_col_width = 1.5 * inch
                    remaining_width = (doc.width - first_col_width)
                    other_col_width = remaining_width / (col_count -1) if col_count > 1 else remaining_width
                    col_widths = [first_col_width] + [other_col_width] * (col_count -1)

                    window_table = Table(table_data_pw, colWidths=col_widths)
                    window_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#DDDDDD")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                        ('TOPPADDING', (0,0), (-1,-1), 6),
                    ]))
                    story.append(window_table)
                    story.append(Spacer(1, 0.1*inch))

            if "overallAnalysis" in per_window:
                story.append(Paragraph(per_window["overallAnalysis"], styles['NormalText']))
            story.append(Spacer(1, 0.2*inch))


    # Peripheral Oxygen Saturation Summary
    spo2_summary = data.get("peripheralOxygenSaturationSummary", {})
    if spo2_summary:
        story.append(Paragraph(spo2_summary.get("sectionTitle", "PERIPHERAL OXYGEN SATURATION (SpO2) SUMMARY"), styles['SectionHeading']))
        if "sectionDescription" in spo2_summary:
            story.append(Paragraph(spo2_summary["sectionDescription"], styles['NormalText']))
        story.extend(create_metrics_table(spo2_summary, styles['SubSectionHeading'], styles['NormalText'], styles['InterpretationText']))
        if "overallInterpretation" in spo2_summary:
            story.append(Paragraph(spo2_summary["overallInterpretation"], styles['NormalText']))
        story.append(Spacer(1, 0.2*inch))


    # Integrated Impression & Summary
    impression = data.get("integratedImpressionAndSummary", {})
    if impression:
        story.append(Paragraph(impression.get("sectionTitle", "INTEGRATED IMPRESSION & SUMMARY"), styles['SectionHeading']))
        content_list = impression.get("content", [])
        for item in content_list:
            story.append(Paragraph(item, styles['NormalText']))
        story.append(Spacer(1, 0.2*inch))

    # Recommendations & Considerations
    recommendations = data.get("recommendationsAndConsiderations", {})
    if recommendations:
        story.append(Paragraph(recommendations.get("sectionTitle", "RECOMMENDATIONS & CONSIDERATIONS"), styles['SectionHeading']))
        points_list = recommendations.get("points", [])
        for point in points_list:
            story.append(Paragraph(f"• {point}", styles['BulletPoint'])) # Using a simple bullet
        story.append(Spacer(1, 0.2*inch))


    # Add Images at the end
    story.append(PageBreak())
    story.append(Paragraph("APPENDIX: VISUALIZATIONS", styles['SectionHeading']))

    image_paths = ['./rr_intervals.png', './poincare.png', './series.png', './psd.png']
    image_captions = [
        "Figure 1: RR Intervals Over Time",
        "Figure 2: Poincaré Plot of RR Intervals",
        "Figure 3: Time Series Data (Example)", # Adjust caption as needed
        "Figure 4: Power Spectral Density (PSD) of HRV"
    ]

    # Available width for images on the page
    available_width = doc.width - doc.leftMargin - doc.rightMargin # This is actually already doc.width for SimpleDocTemplate
    img_max_width = available_width * 0.9 # Use 90% of available width
    img_max_height = 4 * inch # Max height for an image to avoid being too large

    for i, img_path in enumerate(image_paths):
        if os.path.exists(img_path):
            try:
                img = Image(img_path, width=img_max_width, height=img_max_height, kind='bound') # 'bound' maintains aspect ratio
                
                # For better flow, wrap image and caption in KeepInFrame if possible, or just add them
                # If images are large, they might break across pages. Consider two images per page or adjust sizes.
                # For simplicity here, just adding them sequentially.
                
                story.append(img)
                if i < len(image_captions):
                    story.append(Paragraph(image_captions[i], styles['ImageCaption']))
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                print(f"Could not add image {img_path}: {e}")
                story.append(Paragraph(f"<i>Error loading image: {os.path.basename(img_path)}</i>", styles['NormalText']))
        else:
            print(f"Image not found: {img_path}")
            story.append(Paragraph(f"<i>Image not found: {os.path.basename(img_path)}</i>", styles['NormalText']))


    # Build the PDF
    try:
        doc.build(story)
        print(f"PDF '{output_filename}' generated successfully.")
        return output_filename
    except Exception as e:
        print(f"Error generating PDF: {e}")

