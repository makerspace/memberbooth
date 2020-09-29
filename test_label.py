#!/usr/bin/env python3.7

from src.util.logger import init_logger, get_logger
import argparse
import config
import sys
import traceback
import os


from src.label.creator import Label, LabelString

def main():

    print(f"test")

    test_labels = [LabelString(f'Andreas'), LabelString(f'David'), LabelString('Joel')]    


    label = Label(test_labels)




if __name__=="__main__":
    main()
