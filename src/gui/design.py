from tkinter import LEFT, X, NORMAL, DISABLED, Frame, Button, Label, Entry, Text, StringVar, END
import tkinter
from tkinter import font, ttk, messagebox
from PIL import Image, ImageTk
from src.util.logger import get_logger
from src.util.key_reader import EM4100, Aptus, Keyboard
from re import compile, sub
import config
from datetime import datetime
from .event import GuiEvent

MAX_DESCRIPTION_LENGTH = 256
TIMEOUT_TIMER_PERIOD_MS = 60 * 1000
TEMPORARY_STORAGE_LABEL_DEFAULT_TEXT = 'Describe what you want to store here...'

logger = get_logger()


class GuiTemplate:

    def add_print_button(self, master, label, callback='', takefocus=True):
        button = Button(master, text=label, font=self.label_font, command=callback, takefocus=takefocus)
        button.pack(fill=X, pady=5)
        return button

    def show_error_message(self, error_message, error_title='Error'):
        logger.error(f"GUI error: {error_message}")
        return messagebox.showwarning(error_title, error_message)

    def create_label(self, master, text):
        return Label(master, text=text, anchor='w', bg='white', font=self.label_font)

    def create_entry(self, master, text='', border=True):

        entry = Entry(master, bg='white', font=self.text_font, disabledbackground='white', disabledforeground='black',
                      cursor='arrow', borderwidth=1 if border else 0, highlightthickness=1 if border else 0)
        entry.insert(END, text)
        entry.config(state=DISABLED)
        return entry

    def create_label_with_status_indicator(self, master, label_text, text, is_expired):

        holder = Frame(master, background='')

        label = self.create_label(master, label_text)
        label.pack(fill=X, pady=5)

        status_label = self.create_label(holder, 'X' if is_expired else "✓")
        status_label.configure(fg="red" if is_expired else "green")
        status_label.pack(side=LEFT, padx=5)

        tag_expiration_text = self.create_entry(holder, text, border=False)
        tag_expiration_text.pack(fill=X)

        return holder

    def add_basic_information(self, master, member_id, name, tag_expiration_date, membership_expiration_date):

        member_id_label = self.create_label(master, 'Member number:')
        member_id_label.pack(fill=X, pady=5)

        member_id_text = self.create_entry(master, member_id, border=False)
        member_id_text.pack(fill=X)

        name_label = self.create_label(master, 'Name:')
        name_label.pack(fill=X, pady=5)

        name_id_text = self.create_entry(master, name, border=False)
        name_id_text.pack(fill=X)

        now = datetime.now()
        membership_status = self.create_label_with_status_indicator(master, "Organization membership expires:",
                                                                    membership_expiration_date,
                                                                    now > membership_expiration_date)
        membership_status.pack(fill=X, pady=5)
        lab_membership_status = self.create_label_with_status_indicator(master, 'Lab membership expires:',
                                                                        tag_expiration_date, now > tag_expiration_date)
        lab_membership_status.pack(fill=X, pady=5)

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
        self.window_width, self.window_height = self.master.winfo_screenwidth(), self.master.winfo_screenheight()

        if config.development:
            dev_title = Label(self.master, text="Development mode", font=self.label_font)
            dev_title.pack(pady=25)
        else:
            self.logotype = ImageTk.PhotoImage(self.logotype_img)
            self.logotype_label = Label(self.master, image=self.logotype, bd=0)
            self.logotype_label.pack(pady=25)

        self.frame = Frame(self.master, bg='', bd=0, width=self.logotype_img.size[0], height=self.window_height)
        self.frame.pack_propagate(0)
        self.frame.pack()

    def timeout_timer_reset(self):

        if config.development:
            logger.info('Timeout timer was reset')

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
    debounce_time = 100  # ms

    def __init__(self, master, gui_callback, tag_verifier, key_reader, debounce_time=None):
        super().__init__(master, gui_callback)

        self.tag_status_label = self.create_label(self.frame, 'Scan tag on reader...')
        self.tag_status_label.pack(fill=X, pady=5)

        self.verify_tag = tag_verifier
        self.key_reader = key_reader

        if isinstance(key_reader, EM4100):
            self.key_reader.flush()
        elif isinstance(key_reader, Aptus) or isinstance(key_reader, Keyboard):
            self.tag_entry = self.create_entry(self.frame, '')
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

    def set_tag_status(self, status):
        self.tag_status_label.config(text=status)

    def show_error_message(self, error_message, error_title='Error'):
        logger.error(f"GUI error: {error_message}")
        if self.error_message_debouncer is not None:
            self.frame.after_cancel(self.error_message_debouncer)
        self.error_message_label.config(text=error_message)
        self.error_message_debouncer = self.frame.after(5000, lambda: self.error_message_label.config(text=''))
        return

    def reset_gui(self):
        self.stop_progress_bar()
        self.show_message('Scan tag on reader...')
        self.gui.tag_entry.config(state=NORMAL)
        if isinstance(self.key_reader, Aptus) or isinstance(self.key_reader, Keyboard):
            self.tag_entry.delete(0, 'end')
            self.tag_entry.focus_force()

    def tag_read(self):
        tag = self.tag_entry.get()
        logger.info('Tag read...')
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

        self.tag_entry.delete(0, 'end')
        tag = sub(no_number_pattern, "", tag)
        self.tag_entry.insert(0, tag)
        return tag

    def clear_tag_entry(self):
        _ = self.tag_entry.get()
        logger.debug("Auto-clearing tag-entry")
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


class ButtonsGuiMixin:
    '''
    The class shall add the Tkinter buttons to the self.buttons array
    '''
    buttons = []

    def deactivate_buttons(self):
        for b in self.buttons:
            b['state'] = tkinter.DISABLED

    def activate_buttons(self):
        for b in self.buttons:
            b['state'] = tkinter.NORMAL


class MemberInformation(GuiTemplate, ButtonsGuiMixin):

    def __init__(self, master, gui_callback, member):
        super().__init__(master, gui_callback)

        self.add_basic_information(
            self.frame, member.member_number, member.get_name(),
            member.effective_labaccess.end_date, member.membership.end_date)

        self.print_header = self.create_label(self.frame, "Print label for:")
        self.print_header.pack(fill=X, pady=(40, 0))

        self.storage_label_button = self.add_print_button(
            self.frame,
            'Temporary storage',
            lambda: gui_callback(GuiEvent(GuiEvent.DRAW_STORAGE_LABEL_GUI))
        )

        self.fire_box_label_button = self.add_print_button(
            self.frame,
            'Fire safety cabinet storage',
            lambda: gui_callback(GuiEvent(GuiEvent.PRINT_FIRE_BOX_LABEL))
        )

        self.box_label_button = self.add_print_button(
            self.frame,
            'Storage box',
            lambda: gui_callback(GuiEvent(GuiEvent.PRINT_BOX_LABEL))
        )

        self.exit_button = self.add_print_button(
            self.frame,
            'Log out',
            lambda: gui_callback(GuiEvent(GuiEvent.LOG_OUT))
        )
        self.exit_button.pack(pady=(40, 0))

        self.buttons = [self.storage_label_button, self.fire_box_label_button, self.box_label_button, self.exit_button]


class TemporaryStorage(GuiTemplate, ButtonsGuiMixin):

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

        self.instruction = 'Describe what you want to temporary store here...'
        self.description_label = self.create_label(self.frame, 'Temporary storage label')
        self.description_label.pack(fill=X, pady=5)

        self.text_box = Text(self.frame, height=5, bg='white', fg='grey', font=self.text_font, takefocus=True)

        self.text_box.insert(END, self.instruction)

        self.text_box.pack()

        self.character_label_string = StringVar()
        self.character_label_string.set(f'0 / {MAX_DESCRIPTION_LENGTH}')

        self.character_label = Label(self.frame, textvariable=self.character_label_string, anchor='e', bg='white',
                                     fg='grey', font=self.text_font)
        self.character_label.pack(fill=X, pady=5)

        self.text_box.bind('<FocusIn>', self.text_box_callback_focusin)
        self.text_box.pack()

        self.print_button = self.add_print_button(
            self.frame,
            'Print',
            lambda: gui_callback(GuiEvent(GuiEvent.PRINT_TEMPORARY_STORAGE_LABEL, self.text_box.get('1.0', 'end-1c')))
        )

        self.cancel_button = self.add_print_button(
            self.frame,
            'Cancel',
            lambda: gui_callback(GuiEvent(GuiEvent.CANCEL))
        )

        self.buttons = [self.print_button, self.cancel_button]

        self.frame.pack(pady=25)


class WaitForTokenGui(GuiTemplate):

    def __init__(self, master, gui_callback):
        super().__init__(master, gui_callback)

        self.scan_tag_label = self.create_label(self.frame, 'Waiting for token...')
        self.scan_tag_label.pack(fill=X, pady=5)

        self.progress_bar = ttk.Progressbar(self.frame, mode='indeterminate')

        self.error_message_debouncer = None
        self.error_message_label = self.create_label(self.frame, '')
        self.error_message_label.config(fg='red')
        self.error_message_label.pack(fill=X, pady=5)

        self.frame.pack(pady=25)

    def show_error_message(self, error_message, error_title='Error'):
        logger.error(f"GUI error: {error_message}")
        if self.error_message_debouncer is not None:
            self.frame.after_cancel(self.error_message_debouncer)
        self.error_message_label.config(text=error_message)
        self.error_message_debouncer = self.error_message_label.after(
            5000,
            lambda: self.error_message_label.config(text='')
        )

    def reset_gui(self):
        self.tag_entry.delete(0, 'end')
        self.stop_progress_bar()
        self.tag_entry.focus_force()

    def start_progress_bar(self):
        self.progress_bar.start()
        self.progress_bar.pack(fill=X, pady=5)

    def stop_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()


class WaitForKeyReaderReadyGui(GuiTemplate):
    def __init__(self, master):
        super().__init__(master, None)
        self.scan_tag_label = self.create_label(self.frame, 'Connect key reader...')
        self.scan_tag_label.pack(fill=X, pady=5)
        self.frame.pack(pady=25)
