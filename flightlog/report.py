from flask import Blueprint, flash, g, request, url_for, send_file
from werkzeug.exceptions import abort
from datetime import datetime
from io import BytesIO
from os import path

from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle


from flightlog.db import get_db

report = Blueprint("report", __name__)


@report.route("/generate_pdf")
def generate_pdf():
    db = get_db()

    summary_data = db.execute(
        """
            SELECT
                COUNT(DISTINCT id) as num_flights,
                (SUM(duration_minutes) / 60) || "h " || (SUM(duration_minutes) % 60) || "m" as total_time
            FROM flight
        UNION
            SELECT
                COUNT(DISTINCT id) as num_flights_3m,
                (SUM(duration_minutes) / 60) || "h " || (SUM(duration_minutes) % 60) || "m" as total_time_3m
            FROM flight
            WHERE date > DATE('now', '-3 month')
        UNION
            SELECT
                COUNT(DISTINCT id) as num_flights_12m,
                (SUM(duration_minutes) / 60) || "h " || (SUM(duration_minutes) % 60) || "m" as total_time_12m
            FROM flight
            WHERE date > DATE('now', '-12 month')
        """
    ).fetchall()
    summary_data = {
        "columns": ["Number of flights", "Flight time"],
        "rows": ["Total", "Last 12 months", "Last 3 months"],
        "data": [[c for c in r] for r in summary_data][::-1],
    }

    flightlog_data = db.execute(
        """
        SELECT
            f.flight_no as flight_no,
            f.date as date,
            wm.name || " " || wt.name || " " || w.size_designator as wing,
            IIF(laus.is_inofficial, "Zirbenkopf, AUT", laus.name || ", " || lauc.shorty) as launch_site,
            IIF(lans.is_inofficial, "Rosenhang Alm, AUT", lans.name || ", " || lanc.shorty) as landing_site,
            (f.duration_minutes / 60) || "h " || (f.duration_minutes % 60) || "m" as duration
        FROM flight f
            JOIN site laus ON f.launch_site_id = laus.id
            JOIN site lans ON f.landing_site_id = lans.id
            JOIN country lauc ON laus.country_id = lauc.id
            JOIN country lanc ON lans.country_id = lanc.id
            JOIN wing w ON f.wing_id = w.id
            JOIN wing_type wt ON w.wing_type_id = wt.id
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
        ORDER BY
            f.flight_no ASC
        """
    ).fetchall()
    flightlog_data = {
        "columns": ["No.", "Date", "Wing", "Launch site", "Landing site", "Time"],
        "data": [[c for c in r] for r in flightlog_data],
    }

    pilot_config_path = path.join("instance", "report.cfg")
    if path.isfile(pilot_config_path):
        with open(pilot_config_path, "r") as f:
            lines = f.readlines()
            if len(lines) == 2:
                pilot_info = {
                    "Pilot": lines[0].strip(),
                    "License No.": lines[1].strip(),
                }

    pdf_report = generate_pdf_file(pilot_info, summary_data, flightlog_data)
    report_filename = f"flightlog-{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(pdf_report, as_attachment=True, download_name=report_filename)


def generate_pdf_file(pilot_info: dict, summary: dict, flightlog: dict):
    pdf_report = BytesIO()

    elements = []
    doc = SimpleDocTemplate(pdf_report, rightMargin=1 * cm, leftMargin=1 * cm, topMargin=1 * cm, bottomMargin=1.5 * cm)

    # title
    elements.append(Paragraph("Flightlog", ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=24)))
    elements.append(Spacer(1, 1 * cm))

    # pilot and report info
    t = []
    for k, v in pilot_info.items():
        t.append(f"<b>{k}</b>: {v}")
    t = "<br/>".join(t)
    elements.append(Paragraph(t, ParagraphStyle("sub-title", fontName="Helvetica", fontSize=12)))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(
        Paragraph(
            f"<i>Generated on {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>",
            ParagraphStyle("timestampe", fontName="Helvetica", fontSize=10),
        )
    )
    elements.append(Spacer(1, 1 * cm))

    # summary table
    data = summary["data"]
    data.insert(0, summary["columns"])
    summary["rows"].insert(0, "")
    for i in range(len(data)):
        data[i].insert(0, summary["rows"][i])
    for i in range(1, len(data)):
        data[i][0] = Paragraph(str(data[i][0]), ParagraphStyle("table-header", fontName="Helvetica-Bold", fontSize=10))
    for i in range(1, len(data[0])):
        data[0][i] = Paragraph(
            str(data[0][i]), ParagraphStyle("table-header", fontName="Helvetica-Bold", fontSize=10, alignment=1)
        )
    table = Table(data, colWidths=[4 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 1 * cm))

    # flightlog table
    data = flightlog["data"]
    data.insert(0, flightlog["columns"])
    for i in range(len(data[0])):
        data[0][i] = Paragraph(str(data[0][i]), ParagraphStyle("table-header", fontName="Helvetica-Bold", fontSize=6))
    table = Table(
        data, colWidths=[0.8 * cm, 1.5 * cm, 2.5 * cm, 5 * cm, 5 * cm, 1.3 * cm], rowHeights=0.5 * cm, repeatRows=1
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("FONTSIZE", (0, 0), (-1, -1), 6, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    elements.append(table)

    # build
    doc.build(elements, canvasmaker=PageNumberCanvas)

    pdf_report.seek(0)
    return pdf_report


class PageNumberCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def draw_page_number(self, page_count):
        # Modify the content and styles according to the requirement
        page = "{curr_page} of {total_pages}".format(curr_page=self._pageNumber, total_pages=page_count)
        self.setFont("Helvetica", 8)
        self.drawCentredString(105 * mm, 10 * mm, page)

    def save(self):
        # Modify the save() function to add page-number before saving every page
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)
