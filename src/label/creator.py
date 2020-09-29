import qrcode
from datetime import datetime, timedelta
from time import time
from src.util.logger import get_logger
import json
import math
from PIL import Image, ImageDraw, ImageFont
import textwrap
from pathlib import Path
import config

logger = get_logger()

QR_CODE_BOX_SIZE = 15 # Pixel size per box.
QR_CODE_VERSION = 5 # Support for 64  alphanumeric with high error correction
QR_CODE_BORDER = 4
QR_CODE_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_L
QR_VERSION = 1

IMG_WIDTH = 696 # From brother_ql for 62 mm labels
IMG_HEIGHT = math.floor((58+20)/25.4*300)
IMG_MARGIN = 48

JSON_MEMBER_NUMBER_KEY = 'member_number'
JSON_UNIX_TIMESTAMP_KEY ='unix_timestamp'
JSON_VERSION_KEY = 'v'

TEMP_STORAGE_LENGTH = 45
FIRE_BOX_STORAGE_LENGTH = 90
CANVAS_WIDTH = 569

class LabelObject(object):
    def __init__(self):
        self.width = 0
        self.height = 0

    def __str__(self):
        return f'width = {self.width}, height = {self.height}'

class LabelString(LabelObject): 
    
    def __init__(self, text, font_path=config.FONT_PATH, font_size_estimation=500, multiline=False, label_width=CANVAS_WIDTH):
        super().__init__()

        self.text = text
        #self.font_path = font_path
        #self.font_size_estimation = font_size_estimation
        self.multiline = multiline
        self.label_width = label_width

        self.font = ImageFont.truetype(font_path, font_size_estimation)

        #TODO This is stupid, binary implementation? 
        
        if not multiline:

            while self.font.getsize(self.text)[0] > label_width:
                font_size_estimation -= 1
                self.font = ImageFont.truetype(font_path, font_size_estimation)
        
            size = self.font.getsize(self.text)
        
        elif multiline:
            #TODO This is not implemented correct. Needs su 
            self.text = textwrap.fill(text, 40, break_long_words=True)
            tmp_img = Image.new('RGB', (1, 1))
            tmp_canvas = ImageDraw.Draw(tmp_img)

            while tmp_canvas.multiline_textsize(self.text, font=self.font)[0] > label_width:
                font_size_estimation -= 1
                self.font = ImageFont.truetype(font_path, font_size_estimation)

            size = tmp_canvas.multiline_textsize(self.text, font=self.font)
    
        #print(f'{font.getsize(text)}')
        
        self.height = size[1]
        self.width = size[0]

    def __str__(self):
        return f'text = {self.text}, size = {self.size}'

class LabelImage(LabelObject):
    def __init__(self, image, label_width=CANVAS_WIDTH):
        super().__init__()

        if type(image) is str:
            self.image = Image.open(config.SMS_LOGOTYPE_PATH)
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
        self.label.show()

    def get_canvas_height(self):

        content_height = 0
        for label_object in self.label_objects:
            #import pdb; pdb.set_trace()
            #print(f'{label_object.height}')i
            #TODO This is troublesome
            if type(label_object) is LabelString:
                (offset_w, offset_h) = label_object.font.getoffset(label_object.text)
                content_height += label_object.height - offset_h
            else:
                content_height += label_object.height
        return content_height 
        

    def generate_label(self):   
        
        image = Image.new('RGB', (self.label_width, self.label_height), color='white')
        canvas = ImageDraw.Draw(image)
        
        draw_point_x = IMG_MARGIN
        draw_point_y = IMG_MARGIN

        for label_object in self.label_objects:
            print(f'x = {draw_point_x}, y = {draw_point_y}, ({label_object.height})')
           
            #TODO Might be able to move this
            if type(label_object) is LabelString:
                (offset_w, offset_h) = label_object.font.getoffset(label_object.text)
                print(f'offset_w = {offset_w}, offset_h = {offset_h}') 
            else:
                (offset_w, offset_h) = (0,0)

            # Center drawing
            draw_point_x = 0.5*(IMG_WIDTH - label_object.width)

            # Draw
            if type(label_object) is LabelString:
                
                if label_object.multiline is True:
                    canvas.multiline_text((draw_point_x, draw_point_y),
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
            draw_point_x = IMG_MARGIN

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

    return font.getsize(text), font

def create_temporary_storage_label(member_id, name, description):
   
    labels = [LabelString(f'Temporary storage'), 
              LabelString(f'#{member_id}'),
              LabelString(f'{name}'),
              LabelString(f'The board can throw this away after'),
              LabelString(get_end_date_string(TEMP_STORAGE_LENGTH)),
              LabelString(f'{description}', multiline=True)]
    return Label(labels)

def create_box_label(member_id, name):

    data_json = json.dumps({JSON_MEMBER_NUMBER_KEY: int(member_id),
                            JSON_VERSION_KEY: QR_VERSION,
                            JSON_UNIX_TIMESTAMP_KEY: get_unix_timestamp()}, indent=None, separators=(',', ':'))

    logger.info(f'Added data:{data_json} with size {len(data_json)}')

    qr_code_img = create_qr_code(data_json)
        
    labels = [LabelImage(config.SMS_LOGOTYPE_PATH),
              LabelImage(qr_code_img),
              LabelString(f'#{member_id}'),
              LabelString(f'{name}')]
    
    return Label(labels)

def create_fire_box_storage_label(member_id, name):

    labels = [LabelString(f'Fire safety cabinet'), 
              LabelString(f'This product belongs to'), 
              LabelString(f'#{member_id}'),
              LabelString(f'{name}'),
              LabelString('Any member can use this product from'),
              LabelString(get_end_date_string(FIRE_BOX_STORAGE_LENGTH))]
    return Label(labels)
