from reportlab.platypus import PageBreak
import os.path
from laboratory.settings import BASE_DIR
import simplejson as json
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import FONTS_FOLDER
import os.path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from results.sql_func import get_paraclinic_result_by_iss


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, **kwargs):
    """
    Форма печати протокола из шаблона
    """

    pdfmetrics.registerFont(TTFont("PTAstraSerifBold", os.path.join(FONTS_FOLDER, "PTAstraSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("PTAstraSerifReg", os.path.join(FONTS_FOLDER, "PTAstraSerif-Regular.ttf")))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 11
    style.leading = 12
    style.spaceAfter = 1.2 * mm
    style.alignment = TA_JUSTIFY
    style.firstLineIndent = 15

    styleFL = deepcopy(style)
    styleFL.firstLineIndent = 0

    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleBold.firstLineIndent = 0

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.spaceAfter = 0 * mm

    styleRight = deepcopy(style)
    styleRight.aligment = TA_RIGHT

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.firstLineIndent = 0
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 13
    styleCenterBold.face = "PTAstraSerifBold"

    styleTableCentre = deepcopy(style)
    styleTableCentre.alignment = TA_CENTER
    styleTableCentre.spaceAfter = 4.5 * mm
    styleTableCentre.fontSize = 8
    styleTableCentre.leading = 4.5 * mm

    styleT = deepcopy(style)
    styleT.firstLineIndent = 0
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styles_obj = {
        "style": style,
        "styleCenter": styleCenter,
        "styleBold": styleBold,
        "styleCenterBold": styleCenterBold,
        "styleJustified": styleJustified,
        "styleRight": styleRight,
    }

    current_template_file = iss.research.schema_pdf.path

    fields_values = get_paraclinic_result_by_iss(iss.pk)
    result_data = {i.field_title: i.field_value for i in fields_values}

    if current_template_file:
        with open(current_template_file) as json_file:
            data = json.load(json_file)
            body_paragraphs = data["body_paragraphs"]
            header_paragraphs = data["header"]

    objs = []
    if current_template_file:
        for section in header_paragraphs:
            objs = check_section_param(objs, styles_obj, section, result_data)
        fwb.extend(objs)
        objs = []
        for section in body_paragraphs:
            objs = check_section_param(objs, styles_obj, section, result_data)

    fwb.extend(objs)

    return fwb


def check_section_param(objs, styles_obj, section, field_titles_value):
    if section.get("Spacer"):
        height_spacer = section.get("spacer_data")
        objs.append(Spacer(1, height_spacer * mm))
    elif section.get("page_break"):
        objs.append(PageBreak())
    elif section.get("text"):
        field_titles_sec = section.get("fieldTitles")
        data_fields = [field_titles_value.get(i) for i in field_titles_sec if field_titles_value.get(i)]
        difference = len(field_titles_sec) - len(data_fields)
        if len(data_fields) < len(field_titles_sec):
            data_fields = [*data_fields, *["" for count in range(difference)]]
        objs.append(Paragraph(section.get("text").format(*data_fields), styles_obj[section.get("style")]))
    return objs
