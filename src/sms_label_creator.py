#!/usr/bin/env python3.7

import qrcode
from datetime import datetime, timedelta
import json
import math
from PIL import Image, ImageDraw, ImageFont
import textwrap
from pathlib import Path
from logging import getLogger


logger = getLogger('memberbooth')

RESOURCES_PATH = Path(__file__).parent.absolute().joinpath('resources/')

QR_CODE_BOX_SIZE = 10 #Pixel size per box.
QR_CODE_VERSION = 10 #Support for 174 alphanumeric with high error correction
QR_CODE_BORDER = 4
QR_CODE_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_L
QR_VERSION = '1'

IMG_WIDTH = 696 # From brother_ql for 62 mm labels
IMG_HEIGHT = math.floor((58+20)/25.4*300)
IMG_MARGIN = 58

JSON_DATE_KEY = 'date'
JSON_MEMBER_ID_KEY = 'id'
JSON_NAME_KEY = 'name'
JSON_VERSION_KEY = 'version'

TMP_STORAGE_LENGTH = 30 #In days
FONT_PATH = str(RESOURCES_PATH.joinpath('BebasNeue-Regular.ttf'))
SMS_LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_label.png'))
CANVAS_WIDTH = 569

def get_date_string():
    return datetime.now().strftime('%Y-%m-%d')

def get_end_date():
    return (datetime.now() + timedelta(days=TMP_STORAGE_LENGTH)).strftime('%Y-%-m-%-d-%H')

def get_end_date_string():
    return (datetime.now() + timedelta(days=TMP_STORAGE_LENGTH)).strftime('%Y-%m-%d')

def create_qr_code(data):

    qr_code = qrcode.QRCode(box_size=QR_CODE_BOX_SIZE,
                            version=QR_CODE_VERSION,
                            error_correction=QR_CODE_ERROR_CORRECTION,
                            border=QR_CODE_BORDER)
    qr_code.add_data(data)
    qr_code.make()

    return qr_code.make_image()

def get_font_size(estimated_size, text):

    font = ImageFont.truetype(FONT_PATH, estimated_size)

    while font.getsize(text)[0] > CANVAS_WIDTH:
        estimated_size -= 1
        font = ImageFont.truetype(FONT_PATH, estimated_size)

    return font.getsize(text), font

def create_temporary_storage_label(member_id, name, description):

    storage_text = 'Temporary storage'
    storage_text_size, storage_font = get_font_size(200, storage_text)

    id_text = f'#{member_id}'
    id_text_size, id_font = get_font_size(300, id_text)

    name_text = name
    name_text_size, name_font = get_font_size(200, name_text)

    date_text = get_end_date_string()
    date_text_size, date_font = get_font_size(300, date_text)

    # Special solution due to multiline text.
    description_text = textwrap.fill(description, 40, break_long_words=False)
    description_font_point_size = 140
    description_font = ImageFont.truetype(FONT_PATH, description_font_point_size)

    tmp_img = Image.new('RGB', (1, 1))
    tmp_canvas = ImageDraw.Draw(tmp_img)

    while tmp_canvas.multiline_textsize(description_text, font=description_font)[0] > CANVAS_WIDTH:
        description_font_point_size -= 1
        description_font = ImageFont.truetype(FONT_PATH, description_font_point_size)

    description_text_size = tmp_canvas.multiline_textsize(description_text, font=description_font)

    label = Image.new('RGB',
                    (IMG_WIDTH,
                     5 * IMG_MARGIN +
                     storage_text_size[1] +
                     id_text_size[1] +
                     name_text_size[1] +
                     date_text_size[1] +
                     description_text_size[1]),
                    color='white')

    canvas = ImageDraw.Draw(label)

    # Temp storage
    draw_point_x = math.floor((label.size[0] - storage_text_size[0])/2)
    draw_point_y = IMG_MARGIN

    canvas.text((draw_point_x, draw_point_y),
                storage_text,
                font=storage_font,
                fill='black')

    # MEMBER ID
    draw_point_x = math.floor((IMG_WIDTH-id_text_size[0])/2)
    draw_point_y = math.floor(draw_point_y + storage_text_size[1])

    canvas.text((draw_point_x, draw_point_y),
                id_text,
                fill='black',
                font=id_font)

    # NAME
    draw_point_x = math.floor((IMG_WIDTH - name_text_size[0]) / 2 )
    draw_point_y = math.floor(draw_point_y + id_text_size[1] + IMG_MARGIN)

    canvas.text((draw_point_x, draw_point_y),
                name_text,
                fill='black',
                font=name_font)

    # DATE
    draw_point_x = math.floor((IMG_WIDTH - date_text_size[0]) / 2 )
    draw_point_y = math.floor(draw_point_y + name_text_size[1] + IMG_MARGIN)

    canvas.text((draw_point_x, draw_point_y),
                date_text,
                fill='black',
                font=date_font)

    # DESCRIPTION
    draw_point_x = math.floor((IMG_WIDTH - date_text_size[0]) / 2 )
    draw_point_y = math.floor(draw_point_y + date_text_size[1] + IMG_MARGIN)

    canvas.multiline_text((draw_point_x, draw_point_y),
                          description_text,
                          fill='black',
                          font=description_font)

    return label

def create_box_label(member_id, name):

    date_string = get_date_string()
    data_json = json.dumps({JSON_DATE_KEY: date_string,
                            JSON_MEMBER_ID_KEY: member_id,
                            JSON_NAME_KEY: name,
                            JSON_VERSION_KEY: QR_VERSION})

    qr_code_img = create_qr_code(data_json)

    sms_logo_img = Image.open(SMS_LOGOTYPE_PATH)



    id_text = f'#{member_id}'
    id_text_size, id_font = get_font_size(300, id_text)

    name_text = name
    name_text_size, name_font = get_font_size(200, name_text)

    label = Image.new('RGB',
                    (IMG_WIDTH,
                     IMG_MARGIN + sms_logo_img.size[1] + qr_code_img.size[1] +
                     id_text_size[1] + name_text_size[1]),
                    color='white')
    # SMS LOGO
    draw_point_x = IMG_MARGIN
    draw_point_y = IMG_MARGIN
    label.paste(sms_logo_img, (draw_point_x, draw_point_y))

    # QR CODE
    draw_point_x = math.floor((label.size[0] - qr_code_img.size[0]) / 2)
    draw_point_y = math.floor((draw_point_y + sms_logo_img.size[1]))
    label.paste(qr_code_img, (draw_point_x, draw_point_y))


    # MEMBER ID
    canvas = ImageDraw.Draw(label)
    draw_point_x = math.floor((IMG_WIDTH - id_text_size[0]) / 2 )
    draw_point_y = math.floor(draw_point_y + qr_code_img.size[1] - IMG_MARGIN)

    canvas.text((draw_point_x, draw_point_y),
                id_text,
                fill='black',
                font=id_font)

    # Name
    draw_point_x = math.floor((IMG_WIDTH - name_text_size[0]) / 2 )
    temp_draw_point_y = math.floor(draw_point_y + id_text_size[1])
    draw_point_y = math.floor(temp_draw_point_y + (label.size[1] - temp_draw_point_y)/2 - name_text_size[1]/2)

    canvas.text((draw_point_x, draw_point_y),
                name_text,
                fill='black',
                font=name_font)

    return label
