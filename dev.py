#!/usr/bin/env python3.7
from src.label import creator as label_creator
from src.label import printer as label_printer

import config
from datetime import datetime, timedelta
from time import time
#import pdb; pdp.set_trace()


label = label_creator.create_fire_box_storage_label("1140", "Andreas Lundquist")

file_name = f'1140_{str(int(time()))}.png'
label.save(file_name)


