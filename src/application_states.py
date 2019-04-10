from tkinter import Tk
from .event import Event
from .gui import GuiEvent, StartGui, MemberInformation, TemporaryStorage
from src import label_creator
from src import label_printer
from logging import basicConfig, INFO, getLogger
from traceback import print_exc
from src.member import Member
import sys

import traceback

logger = getLogger('memberbooth')
basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s', stream=sys.stderr, level=INFO)

# TODO
# - Change gui model - do not redraw logotype, just a frame.
# - Naming of methods and variable
# - Clean up code

class State(object):

    def __init__(self, application, master, member=None):
        logger.info(f'Processing current state: {self}')
        self.application = application
        self.master = master
        self.member = member

    def gui_callback(self, gui_event):
        logger.info(gui_event)

    def on_event(self, event):
        pass

    def gui_print(self, label):

        event = Event(Event.PRINTING_FAILED)

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

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data
        if event == GuiEvent.LOG_IN:
            tag_id = data
             
            self.application.on_event(Event(Event.TAG_READ, tag_id))

            #FETCH DATA AND GET USER
            pass

    def __init__(self, *args):

        super().__init__(*args)

        self.gui = StartGui(self.master, self.gui_callback)

    def on_event(self, event):

        event_type = event.event

        if event_type == Event.TAG_READ:
            self.gui.start_progress_bar()
            
            try:
                tagid = event.data
                self.member = Member.from_tagid(_makeradmin_client, tagid)
                return MemberIdentified(self.application, self.master, self.member)
            except Exception as e:
                logger.error(f"Exception raised {e}")
                traceback.print_exception(*sys.exc_info())
                self.gui.show_error_message("Could not find a member that matches the specific tag")
                return WaitingState(self.application, self.master)
            return self

        return self


class EditTemporaryStorageLabel(State):

    def __init__(self, *args):
        super().__init__(*args)

        self.gui = TemporaryStorage(self.master, self.gui_callback)

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data

        if event == GuiEvent.CANCEL:
            self.application.on_event(Event(Event.CANCEL))

        elif event == GuiEvent.PRINT_TEMPORARY_STORAGE_LABEL:

            self.application.busy()


            label = label_creator.create_temporary_storage_label('1234',
                                                                     'Stockholm Makerspace',
                                                                     data)

            self.gui_print(label)
            self.application.notbusy()

    def on_event(self, event):

        logger.info(event)

        event = event.event
        data = event.data

        if event == Event.CANCEL or Event.PRINTING_SUCCEEDED:
            return MemberIdentified(self.application, self.master)

        return self

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

        elif event == GuiEvent.LOG_OUT:
            self.application.on_event(Event(Event.LOG_OUT))

        elif event == GuiEvent.PRINT_BOX_LABEL:

            self.application.busy()

            member = self.gui.member
            label = label_creator.create_box_label(member.member_number, member.get_name())

            self.gui_print(label)

            self.application.notbusy()

    def on_event(self, event):

        logger.info(event)

        event = event.event
        data = event.data

        if event == Event.LOG_OUT:
            return WaitingState(self.application, self.master)

        elif event == Event.PRINT_TEMPORARY_STORAGE_LABEL:
            return EditTemporaryStorageLabel(self.application, self.master)

        return self

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
        tk.bind('<Escape>', lambda e: e.widget.quit())
        tk.configure(background='white')
        
        self.master = tk
        self.state = WaitingState(self, self.master)

        # Developing purposes
        self.master.bind('<A>', lambda e:self.on_event(Event(Event.TAG_READ)))
        self.master.bind('<B>', lambda e:self.on_event(Event(Event.MEMBER_INFORMATION_RECEIVED)))
        self.master.bind('<C>', lambda e:self.on_event(Event(Event.PRINT_TEMPORARY_STORAGE_LABEL)))
        self.master.bind('<D>', lambda e:self.on_event(Event(Event.TAG_READ)))

    def on_event(self, event):
        self.state = self.state.on_event(event)

    def run(self):
        self.master.mainloop()
        self.master.destroy()
