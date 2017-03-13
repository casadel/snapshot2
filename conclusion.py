import math
import sys

import pdfminer2

from pdfminer2.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer2.converter import TextConverter
from pdfminer2.layout import LAParams
from pdfminer2.pdfpage import PDFPage
from cStringIO import StringIO

from pdfminer2.pdfparser import PDFParser
from pdfminer2.pdfdocument import PDFDocument
from pdfminer2.pdfpage import PDFTextExtractionNotAllowed
from pdfminer2.converter import PDFPageAggregator


def extract_layout_by_page(pdf_path, parse, parse_args):
    """
    Extracts LTPage objects from a pdf file.

    slightly modified from
    https://euske.github.io/pdfminer/programming.html
    """
    laparams = LAParams()

    fp = open(pdf_path, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser)

    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed

    rsrcmgr = PDFResourceManager()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)
        conclusion = parse(device.get_result(), parse_args)
        if conclusion:
            return conclusion
    raise Exception('Could not find conclusion')


TEXT_ELEMENTS = [
    pdfminer2.layout.LTTextBox,
    pdfminer2.layout.LTTextBoxHorizontal,
    pdfminer2.layout.LTTextLine,
    pdfminer2.layout.LTTextLineHorizontal
]

def flatten(lst):
    """Flattens a list of lists"""
    return [subelem for elem in lst for subelem in elem]


def extract_characters(element):
    """
    Recursively extracts individual characters from
    text elements.
    """
    if isinstance(element, pdfminer2.layout.LTChar):
        return [element]

    if any(isinstance(element, i) for i in TEXT_ELEMENTS):
        return flatten([extract_characters(e) for e in element])

    if isinstance(element, list):
        return flatten([extract_characters(l) for l in element])

    return []

def does_it_intersect(x, (xmin, xmax)):
    return (x <= xmax and x >= xmin)

def convert_to_rows(characters):
    x_limit = 100000
    y_limit = 5
    paragraph_limit = 15

    rows = []
    row = []
    cell = ""
    prior_x = None
    prior_y = None

    y_s = [];
    x_s = [];
    for c in characters:
        c_x, c_y = math.floor((c.bbox[0] + c.bbox[2]) / 2), math.floor((c.bbox[1] + c.bbox[3]) / 2)
        if prior_x is not None and not (c_x - prior_x <= x_limit and abs(c_y - prior_y) <= y_limit):
            if abs(c_y - prior_y) > y_limit:
                row.append(cell)

                # find the right row
                for i in xrange(len(rows)):
                    if abs(y_s[i] - prior_y) <= y_limit:
                        for j in xrange(len(x_s[i])):
                            if prior_x < x_s[i][j]:
                                rows[i] = rows[i][:j] + row + rows[i][j:]
                                x_s[i] = x_s[i][:j] + [prior_x] + x_s[i][j:]
                                break
                        else:
                            rows[i] += row
                            x_s[i].append(prior_x)
                            break
                        break
                else:
                    rows.append(row)
                    y_s.append(prior_y)
                    x_s.append([prior_x])

                cell = ""
                row = []
            elif c_x - prior_x > x_limit:
                row.append(cell)
                cell = ""

        cell += c.get_text()
        prior_x = c_x
        prior_y = c_y

    # handle the last row
    row.append(cell)
    for i in xrange(len(rows)):
        if abs(y_s[i] - prior_y) <= y_limit:
            for j in xrange(len(x_s[i])):
                if prior_x < x_s[i][j]:
                    rows[i] = rows[i][:j] + row + rows[i][j:]
                    x_s[i] = x_s[i][:j] + [prior_x] + x_s[i][j:]
                    break
            else:
                rows[i] += row
                x_s[i].append(prior_x)
                break
            break
    else:
        rows.append(row)
        y_s.append(prior_y)
        x_s.append([prior_x])

    # insert blank rows between particularly separated lines
    #for i in xrange(len(y_s) - 2, -1, -1):
    #    if abs(y_s[i] - y_s[i+1]) > paragraph_limit:
    #        rows = rows[:i+1] + [[]] + rows[i+1:]

    return rows


def parse_page(current_page, pages):
    texts = []

    # seperate text and rectangle elements
    for e in current_page:
        if isinstance(e, pdfminer2.layout.LTTextBoxHorizontal):
            texts.append(e)

    characters = extract_characters(texts)
    page = convert_to_rows(characters)

    pages.append(page)
    pgno = len(pages) - 1

    for i in range(len(page)):
        line = page[i][0]
        if '. CONCLUSION' in line:
            s = ""
            while True:
                line = page[i][0]
                if '. ORDER' in line:
                    break
                s += line
                i += 1
                if i == len(page) - 1:
                    if pgno == 0:
                        raise Exception("Couldn't find end of conclusion")
                    i = 0
                    pgno -= 1
                    page = pages[pgno]
            return s
    return False

def find_conclusion(path):
    return extract_layout_by_page(path, parse_page, [])
