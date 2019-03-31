#!/usr/bin/env python3.7

from src.sms_event import *
from src.sms_gui import *
from src import sms_label_creator
from src import sms_label_printer
from logging import basicConfig, INFO, getLogger
from traceback import print_exc


root = Tk()
root.attributes('-fullscreen', True)
root.bind('<Escape>', lambda e: e.widget.quit())
root.configure(background='white')

logger = getLogger('memberbooth')
basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s', stream=sys.stderr, level=INFO)

# TODO
# - Change gui model - do not redraw logotype, just a frame.
# - Naming of methods and variable
# - Clean up code

class State(object):

    def __init__(self, application, master):
        logger.info(f'Processing current state: {self}')
        self.application = application
        self.master = master

    def gui_callback(self, gui_event):
        logger.info(gui_event)

    def on_event(self, event):
        pass

    def gui_print(self, label):

        event = SMSEvent(SMSEvent.PRINTING_FAILED)

        try:

            print_status = sms_label_printer.print_label(label)

            logger.info(f'Printer status: {print_status}')

            if print_status['did_print']:
                logger.info('Printed label successfully')
                event = SMSEvent(SMSEvent.PRINTING_SUCCEEDED)
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

    def __init__(self, application, master):

        super().__init__(application, master)

        self.gui = StartGui(self.master)

    def on_event(self, sms_event):

        event = sms_event.event

        if event == SMSEvent.TAG_READ:
            self.gui.start_progress_bar()
            # TODO FETCH DATA FROM SERVER
            return self

        elif event == SMSEvent.MEMBER_INFORMATION_RECEIVED:
            self.gui.start_progress_bar()
            return MemberIdentified(self.application, self.master)

        return self


class EditTemporaryStorageLabel(State):

    def __init__(self, application, master):
        super().__init__(application, master)

        self.gui = TemporaryStorage(self.master, self.gui_callback)

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data

        if event == GuiEvent.CANCEL:
            self.application.on_event(SMSEvent(SMSEvent.CANCEL))

        elif event == GuiEvent.PRINT_TEMPORARY_STORAGE_LABEL:

            self.application.busy()


            label = sms_label_creator.create_temporary_storage_label('1234',
                                                                     'Stockholm Makerspace',
                                                                     data)

            self.gui_print(label)
            self.application.notbusy()

    def on_event(self, sms_event):

        logger.info(sms_event)

        event = sms_event.event
        data = sms_event.data

        if event == SMSEvent.CANCEL or SMSEvent.PRINTING_SUCCEEDED:
            return MemberIdentified(self.application, self.master)

        return self

class MemberIdentified(State):

    def __init__(self, application, master):
        super().__init__(application, master)

        self.gui = MemberInformation(self.master, self.gui_callback)

        # TODO Implement this
        #self.member_information = member_information

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data


        if event == GuiEvent.DRAW_STORAGE_LABEL_GUI:
            self.application.on_event(SMSEvent(SMSEvent.PRINT_TEMPORARY_STORAGE_LABEL))

        elif event == GuiEvent.LOG_OUT:
            self.application.on_event(SMSEvent(SMSEvent.LOG_OUT))

        elif event == GuiEvent.PRINT_BOX_LABEL:

            self.application.busy()

            label = sms_label_creator.create_box_label('1234',
                                                       'Stockholm Makerspace')

            self.gui_print(label)

            self.application.notbusy()

    def on_event(self, sms_event):

        logger.info(sms_event)

        event = sms_event.event
        data = sms_event.data

        if event == SMSEvent.LOG_OUT:
            return WaitingState(self.application, self.master)

        elif event == SMSEvent.PRINT_TEMPORARY_STORAGE_LABEL:
            return EditTemporaryStorageLabel(self.application, self.master)

        return self

class Application(object):

    def busy(self):
        self.master.config(cursor='watch')

    def notbusy(self):
        self.master.config(cursor='')

    def __init__(self, master):

        self.master = master
        self.state = WaitingState(self, self.master)

        # Developing purposes
        self.master.bind('<A>', lambda e:self.on_event(SMSEvent(SMSEvent.TAG_READ)))
        self.master.bind('<B>', lambda e:self.on_event(SMSEvent(SMSEvent.MEMBER_INFORMATION_RECEIVED)))
        self.master.bind('<C>', lambda e:self.on_event(SMSEvent(SMSEvent.PRINT_TEMPORARY_STORAGE_LABEL)))

    def on_event(self, event):
        self.state = self.state.on_event(event)


app = Application(root)

root.mainloop()
root.destroy()

