from typing import Any, Sequence
import qrcode
from datetime import datetime, timedelta
from time import time

from src.backend import label_data
from src.backend.makeradmin import UploadedLabel
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
ITEM_MARGIN = 48

WIKI_LINK_MEMBER_STORAGE = "https://wiki.makerspace.se/Medlemsförvaring"

TEMP_STORAGE_LENGTH = int(os.environ.get("MEMBERBOOTH_TEMP_STORAGE_LENGTH", default=60))
TEMP_WARNING_STORAGE_LENGTH = int(os.environ.get("MEMBERBOOTH_TEMP_WARNING_STORAGE_LENGTH", default=90))
FIRE_BOX_STORAGE_LENGTH = int(os.environ.get("MEMBERBOOTH_FIRE_BOX_STORAGE_LENGTH", default=90))
CANVAS_WIDTH = 569
MULTILINE_STRING_LIMIT = 40

class LabelObject(object):
    def __init__(self) -> None:
        self.width: float = 0
        self.height: float = 0
        self.margin_top: float | None = None
        self.margin_bottom: float | None = None

    def __str__(self) -> str:
        return f'width = {self.width}, height = {self.height}'

def size_from_bbox(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def offset_from_bbox(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    return bbox[0], bbox[1]

class LabelString(LabelObject):
    def __init__(self, text, font_path=config.FONT_PATH, multiline=False, label_width=CANVAS_WIDTH,
                 replace_whitespace: bool = True, max_font_size=None, align: str = 'center', margin_top: float | None = None, margin_bottom: float | None = None) -> None:
        super().__init__()

        self.text = text
        self.multiline = multiline
        self.label_width = label_width
        self.max_font_size = max_font_size
        self.align = align
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom

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
    def __init__(self, image: Image.Image | str, label_width: int = CANVAS_WIDTH, margin_top: float | None = None, margin_bottom: float | None = None) -> None:
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
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom


class Label(object):

    def __init__(self, label_objects: Sequence[LabelObject], label_height_mm: float | None = None) -> None:

        self.label_width = CANVAS_WIDTH
        self.label_objects = label_objects

        if label_height_mm is None:
            self.label_margin = ITEM_MARGIN
            h = float(self.label_margin)
            for label_object in self.label_objects:
                h += label_object.height
                h += label_object.margin_top if label_object.margin_top is not None else 0
                h += label_object.margin_bottom if label_object.margin_bottom is not None else self.label_margin

            self.label_height = int(h)
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
                align = label_object.align
            else:
                (_, offset_h) = (0, 0)
                align = "center"

            draw_point_y += label_object.margin_top if label_object.margin_top is not None else 0

            if align == "center":
                # Center drawing
                draw_point_x = 0.5 * (IMG_WIDTH - label_object.width)
            elif align == "left":
                draw_point_x = (IMG_WIDTH - CANVAS_WIDTH)/2
            elif align == "right":
                draw_point_x = IMG_WIDTH - (IMG_WIDTH - CANVAS_WIDTH)/2 - label_object.width

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
            draw_point_y += label_object.height
            draw_point_y += label_object.margin_bottom if label_object.margin_bottom is not None else self.label_margin

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

    # Set optimization parameter to at most the length of the numeric id,
    # to allow for more efficient encoding of the id.
    qr_code.add_data(data, optimize=12)
    qr_code.make()

    return qr_code

# This is the format for QR codes that we use.
# We use uppercase to enable smaller QR codes (there's a specific encoding for alphanumeric uppercase only)
# We also pick an id of length 13 to ensure we get in under the size limit for a size=2 QR code.
qr_size = create_qr_code("HTTP://API.MAKERSPACE.SE/L/1234567890123").best_fit()
assert qr_size == 2, f"QR code size is {qr_size}, expected 2"


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

def create_label(uploaded_label: UploadedLabel) -> Label:
    match uploaded_label.label:
        case label_data.BoxLabel():
            label_image = create_box_label(uploaded_label.public_observation_url, uploaded_label.label)
        case label_data.Printer3DLabel():
            label_image = create_3d_printer_label(uploaded_label.label)
        case label_data.NameTag():
            label_image = create_name_tag(uploaded_label.label)
        case label_data.MeetupNameTag():
            label_image = create_meetup_name_tag(uploaded_label.label)
        case label_data.FireSafetyLabel():
            label_image = create_fire_box_storage_label(uploaded_label.label)
        case label_data.TemporaryStorageLabel():
            label_image = create_temporary_storage_label(uploaded_label.public_observation_url, uploaded_label.label)
        case label_data.DryingLabel():
            label_image = create_drying_label(uploaded_label.label)
        case label_data.WarningLabel():
            label_image = create_warning_label(uploaded_label.label)
        case label_data.RotatingStorageLabel():
            label_image = create_rotating_storage_label(uploaded_label.public_observation_url, uploaded_label.label)
        case _:
            raise ValueError(f"Unknown label type: {uploaded_label.label}")

    return label_image

def create_temporary_storage_label(public_url: str, label: label_data.TemporaryStorageLabel) -> Label:
    qr_code_img = create_qr_code(public_url).make_image()
    id_str = '{:_}'.format(label.base.id).replace('_', ' ')
    labels = [LabelString('Temporary storage'),
              LabelImage(qr_code_img, margin_bottom=0),
              LabelString(id_str, label_width=CANVAS_WIDTH / 5, align="right", margin_top=10, margin_bottom=ITEM_MARGIN - 10),
              LabelString(f'#{label.base.member_number}\n{label.base.member_name}', multiline=True, replace_whitespace=False),
              LabelString(f'The board can throw this away after\n{label.expires_at}', multiline=True,
                          replace_whitespace=False),
              LabelString(label.description, multiline=True)]
    return Label(labels)


def create_rotating_storage_label(public_url: str, label: label_data.RotatingStorageLabel) -> Label:
    qr_code_img: Image.Image = create_qr_code(public_url).make_image()

    qr_size = 200
    qr_code_img = qr_code_img.resize((qr_size, qr_size))
    im = Image.open(config.ROTATING_ICON_PATH)
    offset = ((im.width - qr_size)//2, (im.height - qr_size)//2)
    im.paste(qr_code_img, offset)
    
    # Format ID with spaces as thousands separator
    id_str = '{:_}'.format(label.base.id).replace('_', ' ')

    labels = [LabelString('Rotating storage'),
              LabelImage(im, margin_bottom=0),
              LabelString(id_str, label_width=CANVAS_WIDTH / 5, align="center", margin_top=-5 - offset[0], margin_bottom=ITEM_MARGIN - (-5) + offset[0]),
              LabelString(f'#{label.base.member_number}\n{label.base.member_name}', multiline=True, replace_whitespace=False),
              LabelString(f'Printed {label.base.created_at.date()}\n\nAny member can use this when in the Free For All section', multiline=True,
                          replace_whitespace=False),
              LabelString(label.description, multiline=True)]
    return Label(labels)

def create_box_label(public_url: str, label: label_data.BoxLabel) -> Label:
    qr_code_img = create_qr_code(public_url).make_image()

    labels = [LabelImage(config.SMS_LOGOTYPE_PATH),
              LabelImage(qr_code_img),
              LabelString(f'#{label.base.member_number}'),
              LabelString(f'{label.base.member_name}')]

    return Label(labels)


def create_warning_label(label: label_data.WarningLabel) -> Label:
    qr_code_wiki_link = create_qr_code(WIKI_LINK_MEMBER_STORAGE).make_image()
    labels: list[LabelObject] = [LabelImage(config.SMS_LOGOTYPE_PATH),
              LabelString(
                  f'This project is, as of {label.base.created_at.date()}, violating our storage rules. Unless corrected, the board may throw this away by {label.expires_at.strftime('%Y-%m-%d')}.',
                  multiline=True),
              *([LabelString(label.description, multiline=True)] if label.description else []),
              LabelString("More info on the following web page:"),
              LabelImage(qr_code_wiki_link),
              LabelString(WIKI_LINK_MEMBER_STORAGE)]


    return Label(labels)


def create_fire_box_storage_label(label: label_data.FireSafetyLabel):
    labels = [LabelImage(config.FLAMMABLE_ICON_PATH),
              LabelString('Store in Fire safety cabinet'),
              LabelString('This product belongs to'),
              LabelString(f'#{label.base.member_number}'),
              LabelString(f'{label.base.member_name}'),
              LabelString('Any member can use this product from'),
              LabelString(label.expires_at.strftime('%Y-%m-%d')),
    ]
    return Label(labels)


def create_3d_printer_label(label: label_data.Printer3DLabel):
    label_height_mm = 25
    label_height = get_label_height_in_px(label_height_mm)
    number_of_labels = 2

    max_font_size_px = math.floor((label_height - (number_of_labels + 1)) / number_of_labels)
    max_font_size = math.floor(max_font_size_px * 1.33)

    labels = [LabelString(f'#{label.base.member_number}', max_font_size=max_font_size),
              LabelString(f'{label.base.member_name}', max_font_size=max_font_size)]
    return Label(labels, label_height_mm=label_height_mm)


def create_name_tag(label: label_data.NameTag):
    membership_string = ''
    if (label.membership_expires_at is None or label.membership_expires_at < datetime.now().date()):
        membership_string = 'No active membership'
    else:
        membership_string = 'Member until ' + label.membership_expires_at.strftime('%Y-%m-%d')

    labels = [LabelString(f'{label.base.member_name}'),
              LabelString(membership_string)]
    return Label(labels)


def create_meetup_name_tag(label: label_data.MeetupNameTag) -> Label:

    labels = [LabelString(f'{label.base.member_name}'),
              LabelString('Ask me about:'),
              LabelString('\n')]
    return Label(labels)


def create_drying_label(label: label_data.DryingLabel):
    labels = [LabelString('\nDone drying by\n', multiline=True, replace_whitespace=False),
              LabelString(f'{label.expires_at.strftime('%Y-%m-%d %H:%M')}', replace_whitespace=False),
              LabelString(f'#{label.base.member_number}', replace_whitespace=False),
              LabelString(f'{label.base.member_name}\n', multiline=True, replace_whitespace=False)]

    return Label(labels)
