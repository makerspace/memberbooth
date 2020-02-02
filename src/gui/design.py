from tkinter import *
from tkinter import font, ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
from src.util.logger import get_logger
from src.util.key_reader import EM4100, Aptus, Keyboard
from re import compile, search, sub
import config
from .event import GuiEvent

MAX_DESCRIPTION_LENGTH = 256
TIMEOUT_TIMER_PERIOD_MS = 60*1000

logger = get_logger()

class GuiTemplate:

    def add_print_button(self, master, label, callback='', takefocus=True):
        button = Button(master, text=label, font=self.label_font, command=callback, takefocus=takefocus)
        button.pack(fill=X, pady=5)
        return button

    def show_error_message(self,error_message, error_title='Error'):
        return messagebox.showwarning(error_title, error_message)

    def create_label(self, master, text):
        return Label(master,text=text, anchor='w', bg='white', font=self.label_font)

    def create_entry(self, master, text=''):

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

    def __init__(self, master, gui_callback):

        self.master = master
        self.gui_callback = gui_callback
        self.timer = None
        self.timeout_timer_start()

        for widget in self.master.winfo_children():
            widget.destroy()

        self.label_font = font.Font(family='Arial', size=25, weight='bold')
        self.text_font = font.Font(family='Arial', size=25)

        self.logotype_img = Image.open(config.LOGOTYPE_PATH)
        self.logotype = ImageTk.PhotoImage(self.logotype_img)
        self.window_width, self.window_height = self.master.winfo_screenwidth(), self.master.winfo_screenheight()

        self.logotype_label = Label(self.master, image=self.logotype, bd=0)
        self.logotype_label.pack(pady=25)

        self.frame = Frame(self.master, bg='', bd=0, width=self.logotype_img.size[0], height=self.window_height)
        self.frame.pack_propagate(0)

    def timeout_timer_reset(self):
        logger.info(f'Timeout timer was reset')
        self.master.after_cancel(self.timer)
        self.timeout_timer_start()

    def timeout_timer_cancel(self):
        self.master.after_cancel(self.timer)

    def timeout_timer_start(self):
        self.timer = self.master.after(TIMEOUT_TIMER_PERIOD_MS, self.timeout_timer_expired)

    def timeout_timer_expired(self):
        self.master.after_idle(lambda: self.gui_callback(GuiEvent(GuiEvent.TIMEOUT_TIMER_EXPIRED)))
        self.timeout_timer_start()

class StartGui(GuiTemplate):
    debounce_time = 100 #ms

    def __init__(self, master, gui_callback, tag_verifier, key_reader, debounce_time=None):
        super().__init__(master, gui_callback)

        self.scan_tag_label = self.create_label(self.frame, 'Scan tag on reader...')
        self.scan_tag_label.pack(fill=X, pady=5)

        self.verify_tag = tag_verifier
        self.key_reader = key_reader

        if isinstance(key_reader, EM4100):
            self.key_reader.flush()
        elif isinstance(key_reader, Aptus) or isinstance(key_reader, Keyboard):
            self.tag_entry = self.create_entry(self.frame ,'')
            self.tag_entry.config(state=NORMAL, show='*')
            self.tag_entry.pack(fill=X, pady=5)
            self.tag_entry.focus_force()

            self.tag_entry.bind("<KeyRelease>", self.keyup)
            self.debouncer = None
            if debounce_time is not None:
                self.debounce_time = debounce_time

        self.progress_bar = ttk.Progressbar(self.frame, mode='indeterminate')

        self.error_message_debouncer = None
        self.error_message_label = self.create_label(self.frame, '')
        self.error_message_label.config(fg='red')
        self.error_message_label.pack(fill=X, pady=5)

        self.frame.pack(pady=25)

    def show_error_message(self, error_message, error_title='Error'):
        if self.error_message_debouncer is not None:
            self.frame.after_cancel(self.error_message_debouncer)
        self.error_message_label.config(text=error_message)
        self.error_message_debouncer = self.error_message_label.after(5000, lambda: self.error_message_label.config(text=''))
        return

    def reset_gui(self):
        self.tag_entry.delete(0, 'end')
        self.stop_progress_bar()
        self.tag_entry.focus_force()

    def tag_read(self):
        tag = self.tag_entry.get()
        logger.info(f'Tag read: {tag}')
        self.gui_callback(GuiEvent(GuiEvent.TAG_READ, tag))

    def start_progress_bar(self):
        self.progress_bar.start()
        self.progress_bar.pack(fill=X, pady=5)

    def stop_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    def filter_tag_input(self):
        tag = self.tag_entry.get()

        # For debug, print the characters that are removed (if any)
        no_number_pattern = compile(r"[^\d]")
        filtered_chars = no_number_pattern.findall(tag)
        if len(filtered_chars) == 0:
            return tag

        logger.debug(f"Filtered from tag input: {filtered_chars}")
        self.tag_entry.delete(0, 'end')
        tag = sub(no_number_pattern, "", tag)
        self.tag_entry.insert(0, tag)
        return tag

    def clear_tag_entry(self):
        tag_input = self.tag_entry.get()
        logger.debug(f"Auto-clearing tag-entry \"{tag_input}\"")
        self.tag_entry.delete(0, 'end')

    def touch_cleanup_timeout(self):
        if self.debouncer is not None:
            self.frame.after_cancel(self.debouncer)
        self.debouncer = self.frame.after(self.debounce_time, self.clear_tag_entry)

    def keyup(self, key_event):
        tag = self.filter_tag_input()
        self.touch_cleanup_timeout()

        if self.verify_tag(tag):
            self.tag_read()

class MemberInformation(GuiTemplate):

    def __init__(self, master, gui_callback, member):
        super().__init__(master, gui_callback)

        self.add_basic_information(self.frame, member.member_number, member.get_name(), str(member.lab_end_date))


        storage_label_button = self.add_print_button(self.frame,
                                                     'Print temporary storage label',
                                                     lambda: gui_callback(GuiEvent(GuiEvent.DRAW_STORAGE_LABEL_GUI)))
        box_label_button = self.add_print_button(self.frame,
                                                 'Print storage box label',
                                                 lambda: gui_callback(GuiEvent(GuiEvent.PRINT_BOX_LABEL)))

        exit_button = self.add_print_button(self.frame,
                                            'Log out',
                                            lambda: gui_callback(GuiEvent(GuiEvent.LOG_OUT)))

        self.frame.pack(pady=25)


class TemporaryStorage(GuiTemplate):

    def text_box_callback_key(self, event):
        text_box_content = self.text_box.get('1.0', END)
        text_box_length = len(text_box_content) - 1
        self.timeout_timer_reset()

        if text_box_length >= MAX_DESCRIPTION_LENGTH:
            self.text_box.delete('1.0', END)
            self.text_box.insert('1.0', text_box_content[:MAX_DESCRIPTION_LENGTH])
        else:
            self.character_label.config(fg='grey')

        self.character_label_update()

    def character_label_update(self):
        text_box_content = self.text_box.get('1.0', END)
        text_box_length = len(text_box_content) - 1
        self.character_label_string.set(f'{text_box_length} / {MAX_DESCRIPTION_LENGTH}')

    def text_box_callback_focusin(self, event):
        self.text_box.config(fg='black')
        self.text_box.delete('1.0', END)
        self.text_box.bind('<FocusIn>', '')
        self.text_box.bind('<KeyRelease>', self.text_box_callback_key)

    def __init__(self, master, gui_callback):
        super().__init__(master, gui_callback)

        self.text_box = Text(self.frame, height=5, bg='white', fg='grey', font=self.text_font, takefocus=True)
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
