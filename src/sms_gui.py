#!/usr/bin/env python3.7

from tkinter import *
from tkinter import font, ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
from logging import getLogger

from .sms_event import *


RESOURCES_PATH = Path(__file__).parent.absolute().joinpath('resources/')
LOGOTYPE_PATH = str(RESOURCES_PATH.joinpath('sms_logotype_gui.png'))
MAX_DESCRIPTION_LENGTH = 256

logger = getLogger('memberbooth')

class GuiEvent(Event):

    GUI_EVENT_PREFIX = 'gui_event'

    PRINT_TEMPORARY_STORAGE_LABEL = f'{GUI_EVENT_PREFIX}_print_storage_label'
    PRINT_BOX_LABEL = f'{GUI_EVENT_PREFIX}_print_box_label'
    LOG_OUT = f'{GUI_EVENT_PREFIX}_log_out'
    DRAW_STORAGE_LABEL_GUI = f'{GUI_EVENT_PREFIX}_draw_storage_label_gui'
    CANCEL = f'{GUI_EVENT_PREFIX}_cancel_gui'

class GuiTemplate:

    def add_print_button(self, master, label, callback=''):
        button = Button(master, text=label, font=self.label_font, command=callback)
        button.pack(fill=X, pady=5)
        return button

    def show_error_message(self,error_message, error_title='Error'):
        return messagebox.showwarning(error_title, error_message)

    def create_label(self, master, text):
        return Label(master,text=text, anchor='w', bg='white', font=self.label_font)

    def create_entry(self, master, text):

        entry = Entry(master, bg='white', font=self.text_font, disabledbackground='white', disabledforeground='black', cursor='arrow')
        entry.insert(END, text)
        entry.config(state=DISABLED)
        return entry

    def add_basic_information(self, master, member_id, name, tag_expiration_date):

        member_id_label = self.create_label(master, 'Member number:')
        member_id_label.pack(fill=X, pady=5)

        member_id_text = self.create_entry(master, member_id)
        member_id_text.pack(fill=X)

        name_label = self.create_label(master, 'Name:')
        name_label.pack(fill=X, pady=5)

        name_id_text = self.create_entry(master, name)
        name_id_text.pack(fill=X)

        tag_expiration_label = self.create_label(master, 'Lab membership expires:')
        tag_expiration_label.pack(fill=X, pady=5)

        tag_expiration_text = self.create_entry(master, tag_expiration_date)
        tag_expiration_text.pack(fill=X)

    def __init__(self, master):

        self.master = master

        for widget in self.master.winfo_children():
            widget.destroy()

        self.label_font = font.Font(family='Arial', size=25, weight='bold')
        self.text_font = font.Font(family='Arial', size=25)

        self.logotype_img = Image.open(LOGOTYPE_PATH)
        self.logotype = ImageTk.PhotoImage(self.logotype_img)
        self.window_width, self.window_height = self.master.winfo_screenwidth(), self.master.winfo_screenheight()

        self.logotype_label = Label(self.master, image=self.logotype, bd=0)
        self.logotype_label.pack(pady=25)

        self.frame = Frame(self.master, bg='', bd=0, width=self.logotype_img.size[0], height=self.window_height)
        self.frame.pack_propagate(0)

class StartGui(GuiTemplate):

    def __init__(self, master):
        super().__init__(master)

        self.scan_tag_label = self.create_label(self.frame, 'Scan tag on reader...')
        self.scan_tag_label.pack(fill=X, pady=5)

        self.progress_bar = ttk.Progressbar(self.frame, mode='indeterminate')
        self.frame.pack(pady=25)

    def start_progress_bar(self):
        self.progress_bar.start()
        self.progress_bar.pack(fill=X, pady=5)


    def stop_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()


class MemberInformation(GuiTemplate):

    def __init__(self, master, event_callback, member):
        super().__init__(master)

        self.add_basic_information(self.frame, member.member_number, member.get_name(), str(member.lab_end_date))


        storage_label_button = self.add_print_button(self.frame,
                                                     'Print temporary storage label',
                                                     lambda: event_callback(GuiEvent(GuiEvent.DRAW_STORAGE_LABEL_GUI)))
        box_label_button = self.add_print_button(self.frame,
                                                 'Print storage box label',
                                                 lambda: event_callback(GuiEvent(GuiEvent.PRINT_BOX_LABEL)))

        exit_button = self.add_print_button(self.frame,
                                            'Log out',
                                            lambda: event_callback(GuiEvent(GuiEvent.LOG_OUT)))

        self.frame.pack(pady=25)


class TemporaryStorage(GuiTemplate):

    def text_box_callback_key(self, event):
        text_box_length = len(self.text_box.get('1.0', END)) - 1
        self.character_label_string.set(f'{text_box_length} / {MAX_DESCRIPTION_LENGTH}')

        if text_box_length > MAX_DESCRIPTION_LENGTH:
            self.character_label.config(fg='red')
        else:
            self.character_label.config(fg='grey')

    def text_box_callback_focusin(self, event):
        self.text_box.config(fg='black')
        self.text_box.delete('1.0', END)
        self.text_box.bind('<FocusIn>', '')
        self.text_box.bind('<KeyRelease>', self.text_box_callback_key)

    def __init__(self, master, gui_callback):
        super().__init__(master)

        self.text_box = Text(self.frame, height=5, bg='white', fg='grey', font=self.text_font)
        self.text_box.insert(END, 'Describe what you want to store here...')
        self.text_box.pack()

        self.character_label_string = StringVar()
        self.character_label_string.set(f'0 / {MAX_DESCRIPTION_LENGTH}')

        self.character_label = Label(self.frame, textvariable=self.character_label_string, anchor='e', bg='white', fg='grey', font=self.text_font)
        self.character_label.pack(fill=X, pady=5)

        self.text_box.bind('<FocusIn>', self.text_box_callback_focusin)
        self.text_box.pack()

        self.print_button = self.add_print_button(self.frame,
                                                  'Print',
                                                  lambda: gui_callback(GuiEvent(GuiEvent.PRINT_TEMPORARY_STORAGE_LABEL,
                                                                                self.text_box.get('1.0', 'end-1c')
                                                                                )))

        self.cancel_button = self.add_print_button(self.frame,
                                                  'Cancel',
                                                  lambda: gui_callback(GuiEvent(GuiEvent.CANCEL)))
        self.frame.pack(pady=25)
