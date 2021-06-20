import qrcode
from datetime import datetime, timedelta
from time import time
from src.util.logger import get_logger
import json
import math
from PIL import Image, ImageDraw, ImageFont
import textwrap
import config

logger = get_logger()

QR_CODE_BOX_SIZE = 15  # Pixel size per box.
QR_CODE_VERSION = 5  # Support for 64  alphanumeric with high error correction
QR_CODE_BORDER = 0
QR_CODE_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_L

# Versions of different types of QR codes
QR_VERSION_BOX_LABEL = 1
QR_VERSION_WARNING_LABEL = 1
QR_VERSION_TEMP_STORAGE_LABEL = 1

IMG_WIDTH = 696  # From brother_ql for 62 mm labels
IMG_HEIGHT = math.floor((58 + 20) / 25.4 * 300)
IMG_MARGIN = 48

JSON_MEMBER_NUMBER_KEY = 'member_number'
JSON_UNIX_TIMESTAMP_KEY = 'unix_timestamp'
JSON_VERSION_KEY = 'v'
WIKI_LINK_MEMBER_STORAGE = "https://wiki.makerspace.se/Medlems_Förvaring"

TEMP_STORAGE_LENGTH = 90
TEMP_WARNING_STORAGE_LENGTH = 90
FIRE_BOX_STORAGE_LENGTH = 90
CANVAS_WIDTH = 569
MULTILINE_STRING_LIMIT = 40


class LabelObject(object):
    def __init__(self):
        self.width = 0
        self.height = 0

    def __str__(self):
        return f'width = {self.width}, height = {self.height}'


class LabelString(LabelObject):

    def __init__(self, text, font_path=config.FONT_PATH, multiline=False, label_width=CANVAS_WIDTH):
        super().__init__()

        self.text = text
        self.multiline = multiline
        self.label_width = label_width

        if self.multiline is False:
            self.font_size = get_font_size_estimation(self.text)
        elif self.multiline is True:
            self.font_size = get_font_size_estimation_from_lookup_table(MULTILINE_STRING_LIMIT)\
                if (len(text) > MULTILINE_STRING_LIMIT) else get_font_size_estimation(self.text)

        self.font = ImageFont.truetype(font_path, self.font_size)

        if self.multiline is False:

            while self.font.getsize(self.text)[0] > label_width:
                self.font_size -= 1
                self.font = ImageFont.truetype(font_path, self.font_size)

            size = self.font.getsize(self.text)

        elif self.multiline is True:
            self.text = textwrap.fill(text, MULTILINE_STRING_LIMIT, break_long_words=True)
            tmp_img = Image.new('RGB', (1, 1))
            tmp_canvas = ImageDraw.Draw(tmp_img)

            while tmp_canvas.multiline_textsize(self.text, font=self.font)[0] > label_width:
                self.font_size -= 1
                self.font = ImageFont.truetype(font_path, self.font_size)

            size = tmp_canvas.multiline_textsize(self.text, font=self.font)

        self.height = size[1]
        self.width = size[0]

    def __str__(self):
        return f'text = {self.text}, size = {self.size}'


class LabelImage(LabelObject):
    def __init__(self, image, label_width=CANVAS_WIDTH):
        super().__init__()

        if type(image) is str:
            self.image = Image.open(image)
        else:
            self.image = image

        self.height = self.image.size[1]
        self.width = self.image.size[0]


class Label(object):

    def __init__(self, label_objects):

        self.label_width = CANVAS_WIDTH
        self.label_objects = label_objects

        self.label_height = self.get_canvas_height() + ((len(self.label_objects) + 1) * IMG_MARGIN)
        self.label_width = IMG_WIDTH
        self.label = self.generate_label()

    def save(self, path):
        return self.label.save(path)

    def show(self):
        self.label.show()

    def get_canvas_height(self):

        content_height = 0
        for label_object in self.label_objects:

            if type(label_object) is LabelString:
                (offset_w, offset_h) = label_object.font.getoffset(label_object.text)
                content_height += label_object.height - offset_h
            else:
                content_height += label_object.height

        return content_height

    def generate_label(self):

        image = Image.new('RGB', (self.label_width, self.label_height), color='white')
        canvas = ImageDraw.Draw(image)

        draw_point_y = IMG_MARGIN

        for label_object in self.label_objects:

            if type(label_object) is LabelString:
                (_, offset_h) = label_object.font.getoffset(label_object.text)
            else:
                (_, offset_h) = (0, 0)

            # Center drawing
            draw_point_x = 0.5 * (IMG_WIDTH - label_object.width)

            # Draw
            if type(label_object) is LabelString:

                if label_object.multiline is True:
                    canvas.multiline_text((draw_point_x, draw_point_y - offset_h),
                                          label_object.text,
                                          font=label_object.font,
                                          fill='black')

                else:
                    canvas.text((draw_point_x, draw_point_y - offset_h),
                                label_object.text,
                                font=label_object.font,
                                fill='black')

            elif type(label_object) is LabelImage:
                image.paste(label_object.image, (round(draw_point_x), round(draw_point_y)))

            # Update draw coordinates
            draw_point_y += label_object.height - offset_h + IMG_MARGIN

        return image

    def __str__(self):
        return f'label_height = {self.label_height}'


def get_unix_timestamp():
    return int(time())


def get_date_string():
    return datetime.now().strftime('%Y-%m-%d')


def get_end_date_string(storage_length):
    return (datetime.now() + timedelta(days=storage_length)).strftime('%Y-%m-%d')


def create_qr_code(data):
    qr_code = qrcode.QRCode(box_size=QR_CODE_BOX_SIZE,
                            version=QR_CODE_VERSION,
                            error_correction=QR_CODE_ERROR_CORRECTION,
                            border=QR_CODE_BORDER)
    qr_code.add_data(data)
    qr_code.make()

    return qr_code.make_image()


def get_font_size(estimated_size, text):
    font = ImageFont.truetype(config.FONT_PATH, estimated_size)

    while font.getsize(text)[0] > CANVAS_WIDTH:
        estimated_size -= 1
        font = ImageFont.truetype(config.FONT_PATH, estimated_size)

    return estimated_size


def get_font_size_estimation_from_lookup_table(string_length, percent_offset=0.2):
    lookup_table = {2: 728,
                    3: 511,
                    4: 372,
                    5: 300,
                    6: 249,
                    7: 213,
                    8: 184,
                    9: 165,
                    10: 148,
                    11: 135,
                    12: 124,
                    13: 115,
                    14: 106,
                    15: 98,
                    16: 92,
                    17: 87,
                    18: 83,
                    19: 77,
                    20: 73,
                    21: 70,
                    22: 67,
                    23: 64,
                    24: 61,
                    25: 59,
                    26: 56,
                    27: 54,
                    28: 52,
                    29: 50,
                    30: 48,
                    31: 47,
                    32: 45,
                    33: 44,
                    34: 43,
                    35: 42,
                    36: 40,
                    37: 39,
                    38: 38,
                    39: 37,
                    40: 36,
                    41: 35,
                    42: 34,
                    43: 33,
                    44: 32,
                    45: 31,
                    46: 30,
                    47: 29,
                    48: 28,
                    49: 28,
                    50: 28}

    try:
        size_estimation = lookup_table[string_length]
    except KeyError:
        size_estimation = 25 if string_length > len(lookup_table) else 728

    return size_estimation + math.floor(percent_offset * size_estimation)


def get_font_size_estimation(text):
    return get_font_size_estimation_from_lookup_table(len(text))


def create_temporary_storage_label(member_id, name, description):
    labels = [LabelString('Temporary storage'),
              LabelString(f'#{member_id}'),
              LabelString(name),
              LabelString('The board can throw this away after'),
              LabelString(get_end_date_string(TEMP_STORAGE_LENGTH)),
              LabelString(description, multiline=True)]
    return Label(labels)


def create_box_label(member_id, name):
    data_json = json.dumps({JSON_MEMBER_NUMBER_KEY: int(member_id),
                            JSON_VERSION_KEY: QR_VERSION_BOX_LABEL,
                            JSON_UNIX_TIMESTAMP_KEY: get_unix_timestamp()}, indent=None, separators=(',', ':'))

    logger.info(f'Added data:{data_json} with size {len(data_json)}')

    qr_code_img = create_qr_code(data_json)

    labels = [LabelImage(config.SMS_LOGOTYPE_PATH),
              LabelImage(qr_code_img),
              LabelString(f'#{member_id}'),
              LabelString(f'{name}')]

    return Label(labels)


def create_warning_label():
    data_json = json.dumps({JSON_VERSION_KEY: QR_VERSION_WARNING_LABEL,
                            JSON_UNIX_TIMESTAMP_KEY: get_unix_timestamp()}, indent=None, separators=(',', ':'))

    logger.info(f'Added data:{data_json} with size {len(data_json)}')

    qr_code_wiki_link = create_qr_code(WIKI_LINK_MEMBER_STORAGE)

    labels = [LabelImage(config.SMS_LOGOTYPE_PATH),
              LabelString(
                  'This project has violated our project marking rules. The board may throw this away by', multiline=True),
              LabelString(get_end_date_string(FIRE_BOX_STORAGE_LENGTH)),
              LabelString("More info on the following webpage:"),
              LabelImage(qr_code_wiki_link),
              LabelString(WIKI_LINK_MEMBER_STORAGE)]

    return Label(labels)


def create_fire_box_storage_label(member_id, name):
    labels = [LabelImage(config.FLAMMABLE_ICON_PATH),
              LabelString('Store in Fire safety cabinet'),
              LabelString('This product belongs to'),
              LabelString(f'#{member_id}'),
              LabelString(f'{name}'),
              LabelString('Any member can use this product from'),
              LabelString(get_end_date_string(FIRE_BOX_STORAGE_LENGTH))]
    return Label(labels)
