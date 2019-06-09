from tkinter import Tk
from .event import Event
from .design import GuiEvent, StartGui, MemberInformation, TemporaryStorage
from src.label import creator as label_creator
from src.label import printer as label_printer
from src.util.logger import get_logger
from traceback import print_exc
from src.backend.member import Member, NoMatchingTagId, NoMatchingMemberNumber
from re import compile, search, sub
from time import time
import sys
import config

import traceback

logger = get_logger()

TAG_FORMAT_REGULAR_EXPRESSION = compile('^[0-9]{9}$')

class State(object):

    def __init__(self, application, master, member=None):
        logger.info(f'Processing current state: {self}')
        self.application = application
        self.master = master
        self.member = member

    def change_state(self):
        self.gui.timeout_timer_cancel()
        self.gui = None

    def gui_callback(self, gui_event):
        logger.info(gui_event)

    def on_event(self, event):
        logger.info(event)

    def gui_print(self, label):

        event = Event(Event.PRINTING_FAILED)

        if config.no_printer:
            file_name = f'{self.member.member_number}_{str(int(time()))}.png'
            logger.info(f'Program run with --no-printer, storing image to {file_name} instead of printing it.')
            label.save(file_name)
            event = Event(Event.PRINTING_SUCCEEDED)
            self.application.on_event(event)
            return

        try:

            print_status = label_printer.print_label(label)

            logger.info(f'Printer status: {print_status}')

            if print_status['did_print']:
                logger.info('Printed label successfully')
                event = Event(Event.PRINTING_SUCCEEDED)
            else:
                errors = print_status['printer_state']['errors']
                error_string = ', '.join(errors)
                self.gui.show_error_message(f'Printer reported error: {error_string}', error_title='Printer error!')

        except ValueError:
            self.gui.show_error_message( f'Printer not found, ensure that printer is connected and turned on. Also ensure that the \"Editor Line\" function is disabled.', error_title=f'Printer error!')

        except:
            logger.error('This error should not occur')
            print_exc()
            self.gui.show_error_message('Unknow printer error occured!', error_title='Printer error!')

        finally:
            self.application.on_event(event)


    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__

class WaitingState(State):

    def tag_verifier(self, tag):
        return search(TAG_FORMAT_REGULAR_EXPRESSION, tag) is not None

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data

        if event == GuiEvent.TAG_READ:
            tag_id = data
            self.application.on_event(Event(Event.TAG_READ, tag_id))

    def __init__(self, *args):

        super().__init__(*args)

        self.gui = StartGui(self.master, self.gui_callback, self.tag_verifier)

    def on_event(self, event):
        super().on_event(event)

        state = self
        event_type = event.event

        if event_type == Event.TAG_READ:
            self.gui.start_progress_bar()

            try:
                tagid = event.data
                self.member = Member.from_tagid(_makeradmin_client, tagid)
                state = MemberIdentified(self.application, self.master, self.member)
            except NoMatchingTagId as e:
                self.gui.reset_gui()
                self.gui.show_error_message("Could not find a member that matches the specific tag")
                logger.info(f"No member matched tag id {tagid}")
                state = self
            except Exception as e:
                logger.error(f"Exception raised {e}")
                traceback.print_exception(*sys.exc_info())
                self.gui.show_error_message(f"Error... \n{e}")
                self.gui.reset_gui()
                state = self

        if state is not self:
            self.change_state()
        return state

class EditTemporaryStorageLabel(State):

    def __init__(self, *args):
        super().__init__(*args)

        self.gui = TemporaryStorage(self.master, self.gui_callback)

        print(self.member)

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data

        if event == GuiEvent.CANCEL:
            self.application.on_event(Event(Event.CANCEL))

        elif event == GuiEvent.TIMEOUT_TIMER_EXPIRED:
            self.application.on_event(Event(Event.LOG_OUT))

        elif event == GuiEvent.PRINT_TEMPORARY_STORAGE_LABEL:

            self.application.busy()

            label = label_creator.create_temporary_storage_label(self.member.member_number,
                                                                     self.member.get_name(),
                                                                     data)

            self.gui_print(label)
            self.application.notbusy()

    def on_event(self, event):
        super().on_event(event)

        state = self
        event = event.event

        if event == Event.CANCEL or event == Event.PRINTING_SUCCEEDED:
            state = MemberIdentified(self.application, self.master, self.member)

        elif event == Event.LOG_OUT:
            state = WaitingState(self.application, self.master, None)

        if state is not self:
            self.change_state()
        return state

class MemberIdentified(State):

    def __init__(self, *args):
        super().__init__(*args)

        self.gui = MemberInformation(self.master, self.gui_callback, self.member)

        # TODO Implement this
        #self.member_information = member_information

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data


        if event == GuiEvent.DRAW_STORAGE_LABEL_GUI:
            self.application.on_event(Event(Event.PRINT_TEMPORARY_STORAGE_LABEL))

        elif event == GuiEvent.LOG_OUT or event == GuiEvent.TIMEOUT_TIMER_EXPIRED:
            self.application.on_event(Event(Event.LOG_OUT))

        elif event == GuiEvent.PRINT_BOX_LABEL:

            self.application.busy()

            label = label_creator.create_box_label(self.member.member_number, self.member.get_name())

            self.gui_print(label)

            self.application.notbusy()

    def on_event(self, event):
        super().on_event(event)

        state = self
        event = event.event

        if event == Event.LOG_OUT:
            state = WaitingState(self.application, self.master)

        elif event == Event.PRINT_TEMPORARY_STORAGE_LABEL:
            state = EditTemporaryStorageLabel(self.application, self.master, self.member)

        if state is not self:
            self.change_state()
        return state

class Application(object):

    def busy(self):
        self.master.config(cursor='watch')

    def notbusy(self):
        self.master.config(cursor='')

    def __init__(self, makeradmin_client):
        global _makeradmin_client
        _makeradmin_client = makeradmin_client

        tk = Tk()
        tk.attributes('-fullscreen', True)
        tk.configure(background='white')

        self.master = tk
        self.state = WaitingState(self, self.master)

        # Developing purposes
        if config.development:
            self.master.bind('<Escape>', lambda e: e.widget.quit())
            self.master.bind('<A>', lambda e:self.on_event(Event(Event.TAG_READ)))

    def on_event(self, event):
        self.state = self.state.on_event(event)

    def run(self):
        self.master.mainloop()
        self.master.destroy()
