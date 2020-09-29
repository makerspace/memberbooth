#!/usr/bin/env python3.7

from src.util.logger import init_logger, get_logger
import argparse
import config
import sys
import traceback
import os


from src.label.creator import Label, LabelString, create_fire_box_storage_label, create_temporary_storage_label, create_box_label

def main():

    print(f"test")

    #test_labels = [LabelString(f'Andreas'), LabelString(f'David'), LabelString('Joel')]    
    #label = Label(test_labels)

    create_fire_box_storage_label(f'1140', f'Andreas Lundquist')
    create_box_label(f'1140', f'Andreas Lundquist')
    create_temporary_storage_label(f'1140', f'Andreas Lundquist', f'BBla bla bla blaBla bla bla blaBla bla bla blaBla bla bla blaBla bla bla blala bla bla blav')


if __name__=="__main__":
    main()
