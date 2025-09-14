from typing import Any, Sequence
import qrcode
from datetime import datetime, timedelta
from time import time

from src.backend import label_data
from src.util.logger import get_logger
import math
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import config

logger = get_logger()

QR_CODE_BOX_SIZE = 15  # Pixel size per box.
QR_CODE_VERSION = None  # Auto-resize QR code
QR_CODE_BORDER = 0
QR_CODE_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_M
QR_CODE_DESCRIPTION_MAX_LENGTH = 100

# For Brother QL-810W with 62 mm wide labels
PRINTER_HEIGHT_MARGIN_MM = 3
PRINTER_PIXELS_PER_MM = 300 / 25.4
PRINTER_LABEL_PRINTABLE_WIDTH = 58

IMG_WIDTH = math.floor(PRINTER_PIXELS_PER_MM * PRINTER_LABEL_PRINTABLE_WIDTH)
IMG_HEIGHT = math.floor((58 + 20) / 25.4 * 300)
IMG_MARGIN = 48

# Versions of different types of QR codes
QR_VERSION_BOX_LABEL = 2
QR_VERSION_WARNING_LABEL = 1
QR_VERSION_TEMP_STORAGE_LABEL = 1

# The possible QR code data fields
JSON_MEMBER_NUMBER_KEY = 'member_number'
JSON_UNIX_TIMESTAMP_KEY = 'unix_timestamp'  # Unix timestamp for when the label was printed
JSON_EXPIRY_DATE_KEY = 'expiry_date'  # ISO date for expiry of temporary storage
JSON_DESCRIPTION_KEY = "description"
JSON_VERSION_KEY = 'v'  # The version of the label
JSON_TYPE_KEY = "type"  # The type of label
JSON_TYPE_VALUE_BOX = "box"
JSON_TYPE_VALUE_TEMP_STORAGE = "temp"

WIKI_LINK_MEMBER_STORAGE = "https://wiki.makerspace.se/Medlemsförvaring"

TEMP_STORAGE_LENGTH = os.environ.get("MEMBERBOOTH_TEMP_STORAGE_LENGTH", default=60)
TEMP_WARNING_STORAGE_LENGTH = os.environ.get("MEMBERBOOTH_TEMP_WARNING_STORAGE_LENGTH", default=90)
FIRE_BOX_STORAGE_LENGTH = os.environ.get("MEMBERBOOTH_FIRE_BOX_STORAGE_LENGTH", default=90)
CANVAS_WIDTH = 569
MULTILINE_STRING_LIMIT = 40


class LabelObject(object):
    def __init__(self) -> None:
        self.width: float = 0
        self.height: float = 0

    def __str__(self) -> str:
        return f'width = {self.width}, height = {self.height}'

def size_from_bbox(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def offset_from_bbox(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    return bbox[0], bbox[1]

class LabelString(LabelObject):
    def __init__(self, text, font_path=config.FONT_PATH, multiline=False, label_width=CANVAS_WIDTH,
                 replace_whitespace: bool = True, max_font_size=None):
        super().__init__()

        self.text = text
        self.multiline = multiline
        self.label_width = label_width
        self.max_font_size = max_font_size

        # Decide starting point for label fitting
        if max_font_size is not None:
            self.font_size = self.max_font_size
        elif self.multiline is False:
            self.font_size = get_font_size_estimation(self.text)
        elif self.multiline is True:
            self.font_size = get_font_size_estimation_from_lookup_table(MULTILINE_STRING_LIMIT) \
                if (len(text) > MULTILINE_STRING_LIMIT) else get_font_size_estimation(self.text)

        self.font = ImageFont.truetype(font_path, self.font_size)

        if not self.multiline:

            while self.font.getlength(self.text) > label_width:
                self.font_size -= 1
                self.font = ImageFont.truetype(font_path, self.font_size)

            size = size_from_bbox(self.font.getbbox(self.text))

        else:
            self.text = textwrap.fill(text, MULTILINE_STRING_LIMIT, break_on_hyphens=True, break_long_words=True,
                                      replace_whitespace=replace_whitespace)
            tmp_img = Image.new('RGB', (1, 1))
            tmp_canvas = ImageDraw.Draw(tmp_img)

            while size_from_bbox(tmp_canvas.textbbox((0,0), self.text, font=self.font))[0] < label_width:
                self.font_size += 1
                self.font = ImageFont.truetype(font_path, self.font_size)
            while size_from_bbox(tmp_canvas.textbbox((0,0), self.text, font=self.font))[0] >= label_width:
                self.font_size -= 1
                self.font = ImageFont.truetype(font_path, self.font_size)

            size = size_from_bbox(tmp_canvas.textbbox((0,0), self.text, font=self.font))

        self.height = size[1]
        self.width = size[0]

    def __str__(self):
        return f'text = {self.text}, size = {self.width}x{self.height}'


class LabelImage(LabelObject):
    def __init__(self, image: Image.Image | str, label_width: int = CANVAS_WIDTH) -> None:
        super().__init__()

        if isinstance(image, str):
            img: Image.Image = Image.open(image)
        else:
            img = image
        width, height = img.size
        new_height = int(label_width / width * height)
        self.image = img.resize((label_width, new_height), Image.Resampling.LANCZOS)

        self.height = self.image.size[1]
        self.width = self.image.size[0]


class Label(object):

    def __init__(self, label_objects: Sequence[LabelObject], label_height_mm: float | None = None) -> None:

        self.label_width = CANVAS_WIDTH
        self.label_objects = label_objects

        if label_height_mm is None:
            self.label_margin = ITEM_MARGIN
            self.label_height = int(self.get_canvas_height() + ((len(self.label_objects) + 1) * self.label_margin))
        else:
            self.label_height = int(math.floor((label_height_mm - 2 * PRINTER_HEIGHT_MARGIN_MM) * PRINTER_PIXELS_PER_MM))
            self.label_margin = int(math.floor((self.label_height - self.get_canvas_height()) / ((len(self.label_objects) + 1))))

        self.label_width = IMG_WIDTH
        self.label = self.generate_label()

    def save(self, path: str) -> None:
        return self.label.save(path)

    def show(self) -> None:
        self.label.show()

    def get_canvas_height(self) -> float:

        content_height = 0.0
        for label_object in self.label_objects:

            if type(label_object) is LabelString:
                (offset_w, offset_h) = offset_from_bbox(label_object.font.getbbox(label_object.text))
                content_height += label_object.height
            else:
                content_height += label_object.height

        return content_height

    def generate_label(self) -> Image.Image:

        image = Image.new('RGB', (self.label_width, self.label_height), color='white')
        canvas = ImageDraw.Draw(image)

        draw_point_y: float = self.label_margin

        for label_object in self.label_objects:

            if type(label_object) is LabelString:
                (_, offset_h) = offset_from_bbox(label_object.font.getbbox(label_object.text))
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
            draw_point_y += label_object.height + self.label_margin

        return image

    def __str__(self):
        return f'label_height = {self.label_height}'


def get_unix_timestamp() -> int:
    return int(time())


def get_date_string() -> str:
    return datetime.now().strftime('%Y-%m-%d')


def get_end_date_string(storage_length: int) -> str:
    return (datetime.now() + timedelta(days=storage_length)).strftime('%Y-%m-%d')


def get_end_drying_string(drying_length: int) -> str:
    return (datetime.now() + timedelta(hours=drying_length)).strftime('%Y-%m-%d %H:00')


def create_qr_code(data: str) -> qrcode.QRCode[Any]:
    qr_code = qrcode.QRCode(box_size=QR_CODE_BOX_SIZE,
                            version=QR_CODE_VERSION,
                            error_correction=QR_CODE_ERROR_CORRECTION,
                            border=QR_CODE_BORDER)
    qr_code.add_data(data)
    qr_code.make()

    return qr_code.make_image()


def get_font_size(estimated_size: int, text: str) -> int:
    font = ImageFont.truetype(config.FONT_PATH, estimated_size)

    while font.getlength(text) > CANVAS_WIDTH:
        estimated_size -= 1
        font = ImageFont.truetype(config.FONT_PATH, estimated_size)

    return estimated_size


def get_font_size_estimation_from_lookup_table(string_length: int, percent_offset: float = 0.2) -> int:
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


def get_font_size_estimation(text: str) -> int:
    return get_font_size_estimation_from_lookup_table(len(text))


def get_label_height_in_px(label_height_mm: float) -> int:
    return math.floor((label_height_mm - 2 * PRINTER_HEIGHT_MARGIN_MM) * PRINTER_PIXELS_PER_MM)


def create_temporary_storage_label(member_id: int, name: str, description: str):
    end_date_str = get_end_date_string(TEMP_STORAGE_LENGTH)
    data_json = json.dumps({
        JSON_MEMBER_NUMBER_KEY: member_id,
        JSON_VERSION_KEY: QR_VERSION_TEMP_STORAGE_LABEL,
        JSON_TYPE_KEY: JSON_TYPE_VALUE_TEMP_STORAGE,
        JSON_EXPIRY_DATE_KEY: end_date_str,
        JSON_UNIX_TIMESTAMP_KEY: get_unix_timestamp(),
        JSON_DESCRIPTION_KEY: textwrap.shorten(description, width=QR_CODE_DESCRIPTION_MAX_LENGTH)
    },
        indent=None, separators=(',', ':')
    )
    logger.info(f"Creating a QR code for temporary storage with data: {data_json}")
    qr_code_img = create_qr_code(data_json)

    labels = [LabelString('Temporary storage'),
              LabelImage(qr_code_img),
              LabelString(f'#{member_id}\n{name}', multiline=True, replace_whitespace=False),
              LabelString(f'The board can throw this away after\n{end_date_str}', multiline=True,
                          replace_whitespace=False),
              LabelString(description, multiline=True)]
    return Label(labels)


def create_box_label(member_id, name):
    data_json = json.dumps({JSON_MEMBER_NUMBER_KEY: int(member_id),
                            JSON_VERSION_KEY: QR_VERSION_BOX_LABEL,
                            JSON_TYPE_KEY: JSON_TYPE_VALUE_BOX,
                            JSON_UNIX_TIMESTAMP_KEY: get_unix_timestamp()}, indent=None, separators=(',', ':'))

    logger.info(f'Added data:{data_json} with size {len(data_json)}')

    qr_code_img = create_qr_code(data_json)

    labels = [LabelImage(config.SMS_LOGOTYPE_PATH),
              LabelImage(qr_code_img),
              LabelString(f'#{member_id}'),
              LabelString(f'{name}')]

    return Label(labels)


def create_warning_label():
    qr_code_wiki_link = create_qr_code(WIKI_LINK_MEMBER_STORAGE)
    labels = [LabelImage(config.SMS_LOGOTYPE_PATH),
              LabelString(
                  f'This project is, as of {datetime.today().date()}, violating our project marking rules. Unless corrected, the board may throw this away by',
                  multiline=True),
              LabelString(get_end_date_string(TEMP_WARNING_STORAGE_LENGTH)),
              LabelString("More info on the following web page:"),
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


def create_3d_printer_label(member_id, name):
    label_height_mm = 25
    label_height = get_label_height_in_px(label_height_mm)
    number_of_labels = 2

    max_font_size_px = math.floor((label_height - (number_of_labels + 1)) / number_of_labels)
    max_font_size = math.floor(max_font_size_px * 1.33)

    labels = [LabelString(f'#{member_id}', max_font_size=max_font_size),
              LabelString(f'{name}', max_font_size=max_font_size)]
    return Label(labels, label_height_mm=label_height_mm)


def create_name_tag(member_id, name, membership_end_date):

    membership_string = ''
    if (membership_end_date is None or membership_end_date < datetime.now()):
        membership_string = 'No actve membership'
    else:
        membership_string = 'Member until ' + membership_end_date.strftime('%Y-%m-%d')

    labels = [LabelString(f'{member_id}'),
              LabelString(f'{name}'),
              LabelString(membership_string)]
    return Label(labels)


def create_meetup_name_tag(name):

    labels = [LabelString(f'{name}'),
              LabelString('Ask me about:'),
              LabelString('\n')]
    return Label(labels)


def create_drying_label(member_id: int, name: str, estimated_drying_time: int):
    end_time_str = get_end_drying_string(estimated_drying_time)

    labels = [LabelString('\nDone drying by\n', multiline=True, replace_whitespace=False),
              LabelString(f'{end_time_str}', replace_whitespace=False),
              LabelString(f'#{member_id}', replace_whitespace=False),
              LabelString(f'{name}\n', multiline=True, replace_whitespace=False)]

    return Label(labels)
