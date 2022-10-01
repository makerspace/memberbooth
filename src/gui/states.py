import tkinter
from re import compile, search
from time import time

import serial.serialutil

import config
from src.backend.makeradmin import MakerAdminTokenExpiredError, NetworkError
from src.backend.member import Member, NoMatchingTagId
from src.label import creator as label_creator
from src.label import printer as label_printer
from src.util.key_reader import EM4100, NoReaderFound, KeyReaderNeedsRebootError
from src.util.logger import get_logger
from .design import GuiEvent, StartGui, MemberInformation, TemporaryStorage, WaitForTokenGui, WaitForKeyReaderReadyGui
from .event import Event

logger = get_logger()

TAG_FORMAT_REGULAR_EXPRESSION = compile('^[0-9]{9}$')
SERIAL_POLL_TIME_MS = 100


class State(object):
    def __init__(self, application, master, member=None):
        logger.info(f'Processing current state: {self}')
        self.application = application
        self.master = master
        self.master.title('memberbooth')
        self.member = member

    def change_state(self):
        self.gui.timeout_timer_cancel()
        self.gui = None

    def gui_callback(self, gui_event):

        # Fix to not let the timer expired event fill the logs in production when it is not relevant..
        if (not config.development and type(self) in [WaitingForTokenState, WaitForKeyReaderReadyState, WaitingState] and gui_event.event == GuiEvent.TIMEOUT_TIMER_EXPIRED):
            return

        logger.info(gui_event)

    def on_event(self, event):
        logger.info(event)

    def gui_print(self, label):

        event = Event(Event.PRINTING_FAILED)

        if config.no_printer:
            file_name = f'{self.member.member_number}_{str(int(time()))}.png'
            logger.info(f'Program run with --no-printer, storing image to {file_name} instead of printing it.')
            label.save(file_name)
            label.show()
            event = Event(Event.PRINTING_SUCCEEDED)
            self.application.on_event(event)
            return

        try:

            print_status = label_printer.print_label(label.label)

            logger.info(f'Printer status: {print_status}')

            if print_status['did_print']:
                logger.info('Printed label successfully')
                self.application.slack_client.post_message_info(
                    f"*#{self.member.member_number} - {self.member.get_name()}* successfully printed a label.")
                event = Event(Event.PRINTING_SUCCEEDED)
            else:
                errors = print_status['printer_state']['errors']
                error_string = ', '.join(errors)
                self.application.slack_client.post_message_error(f"Printer reported error: {error_string}.")
                self.gui.show_error_message(f'Printer reported error: {error_string}', error_title='Printer error!')

        except ValueError:
            self.gui.show_error_message(
                'Printer not found, ensure that printer is connected and turned on. Also ensure that the \"Editor Lite\" function is disabled.',
                error_title='Printer error!')

        except Exception:
            logger.exception('This error should not occur')
            self.gui.show_error_message('Unknow printer error occured!', error_title='Printer error!')

        finally:
            self.application.on_event(event)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


class WaitingState(State):
    def __init__(self, *args):
        super().__init__(*args)

        self.gui = StartGui(self.master, self.gui_callback, self.is_tag_valid, self.application.key_reader)

        self.tag_reader_timer = None
        if isinstance(self.application.key_reader, EM4100):
            self.tag_reader_timer_start()

    def is_tag_valid(self, tag):
        return search(TAG_FORMAT_REGULAR_EXPRESSION, tag) is not None

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data

        if event == GuiEvent.TAG_READ:
            tag_id = data
            self.application.on_event(Event(Event.TAG_READ, tag_id))

    def tag_reader_timer_expired(self):
        try:
            if self.application.key_reader.tag_was_read():
                self.tag_reader_timer_cancel()
                tag_id = self.application.key_reader.get_aptus_tag_id()
                self.application.on_event(Event(Event.TAG_READ, tag_id))
                if self.application.state != self:
                    return
        except serial.serialutil.SerialException:
            logger.exception("Key reader disconnected")
            self.key_reader.close()
            self.tag_reader_timer_cancel()
            self.application.key_reader.com.close()
            self.application.on_event(Event(Event.SERIAL_PORT_DISCONNECTED))
            return
        except KeyReaderNeedsRebootError:
            self.application.on_event(Event(Event.SERIAL_PORT_DISCONNECTED))
        except Exception:
            logger.exception("Exception while polling key reader")

        self.tag_reader_timer_start()

    def tag_reader_timer_start(self):
        self.tag_reader_timer = self.master.after(SERIAL_POLL_TIME_MS, self.tag_reader_timer_expired)

    def tag_reader_timer_cancel(self):
        self.master.after_cancel(self.tag_reader_timer)

    def on_event(self, event):
        super().on_event(event)

        event_type = event.event

        if event_type == Event.TAG_READ:
            self.gui.start_progress_bar()
            self.gui.set_tag_status("Tag read...")
            self.master.update()

            try:
                tagid = event.data
                self.member = Member.from_tagid(self.application.makeradmin_client, tagid)
                return MemberIdentified(self.application, self.master, self.member)
            except NoMatchingTagId:
                self.gui.reset_gui()
                self.gui.show_error_message("Could not find a member that matches the specific tag")
            except MakerAdminTokenExpiredError:
                return WaitingForTokenState(self, self.member)
            except NetworkError:
                self.gui.reset_gui()
                self.gui.show_error_message("Network error, please try again")
            except Exception as e:
                logger.exception("Unexpected exception")
                self.gui.show_error_message(f"Error... \n{e}")
                self.gui.reset_gui()

        elif event_type == Event.SERIAL_PORT_DISCONNECTED:
            return WaitForKeyReaderReadyState(self.application, self.master)


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

        elif event == GuiEvent.TIMEOUT_TIMER_EXPIRED:
            self.application.on_event(Event(Event.LOG_OUT))

        elif event == GuiEvent.PRINT_TEMPORARY_STORAGE_LABEL:
            textbox_string = str(data)
            if len(textbox_string.replace(r' ', '')) < 5 or textbox_string == self.gui.instruction:
                self.gui.show_error_message("You have to add a description of at least 5 letters",
                                            error_title='User error!')
                return

            self.gui.deactivate_buttons()
            self.application.busy()

            self.application.busy()
            label_image = label_creator.create_temporary_storage_label(self.member.member_number,
                                                                       self.member.get_name(),
                                                                       data)

            self.application.slack_client.post_message_info(
                f"*#{self.member.member_number} - {self.member.get_name()}* tried to print a temporary storage label with message: {data}")

            self.gui_print(label_image)
            self.application.notbusy()

    def on_event(self, event):
        super().on_event(event)

        event = event.event
        if event == Event.CANCEL or event == Event.PRINTING_SUCCEEDED:
            return MemberIdentified(self.application, self.master, self.member)

        elif event == Event.LOG_OUT:
            return WaitingState(self.application, self.master, None)


class MemberIdentified(State):
    def __init__(self, *args):
        super().__init__(*args)

        self.gui = MemberInformation(self.master, self.gui_callback, self.member)

        # TODO Implement this
        # self.member_information = member_information

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        # data = gui_event.data

        if event == GuiEvent.DRAW_STORAGE_LABEL_GUI:
            self.application.on_event(Event(Event.PRINT_TEMPORARY_STORAGE_LABEL))

        elif event == GuiEvent.LOG_OUT or event == GuiEvent.TIMEOUT_TIMER_EXPIRED:
            self.application.on_event(Event(Event.LOG_OUT))

        elif event == GuiEvent.PRINT_BOX_LABEL:

            self.gui.deactivate_buttons()
            self.application.busy()

            label_image = label_creator.create_box_label(self.member.member_number, self.member.get_name())

            self.application.slack_client.post_message_info(
                f"*#{self.member.member_number} - {self.member.get_name()}* tried to print a box label.")

            self.gui_print(label_image)

            self.application.notbusy()
            self.master.after(100, self.gui.activate_buttons)

        elif event == GuiEvent.PRINT_3D_PRINTER_LABEL:

            self.gui.deactivate_buttons()
            self.application.busy()

            label_image = label_creator.create_3d_printer_label(self.member.member_number, self.member.get_name())

            self.application.slack_client.post_message_info(
                f"*#{self.member.member_number} - {self.member.get_name()}* tried to print a 3D printer label.")

            self.gui_print(label_image)

            self.application.notbusy()
            self.master.after(100, self.gui.activate_buttons)

        elif event == GuiEvent.PRINT_NAME_TAG:

            self.gui.deactivate_buttons()
            self.application.busy()

            label_image = label_creator.create_name_tag(self.member.member_number, self.member.get_name(), self.member.membership.end_date)

            self.application.slack_client.post_message_info(
                f"*#{self.member.member_number} - {self.member.get_name()}* tried to print a name tag.")

            self.gui_print(label_image)

            self.application.notbusy()
            self.master.after(100, self.gui.activate_buttons)

        elif event == GuiEvent.PRINT_MEETUP_NAME_TAG:

            self.gui.deactivate_buttons()
            self.application.busy()

            label_image = label_creator.create_meetup_name_tag(self.member.get_name())

            self.application.slack_client.post_message_info(
                f"*#{self.member.member_number} - {self.member.get_name()}* tried to print a meetup name tag.")

            self.gui_print(label_image)

            self.application.notbusy()
            self.master.after(100, self.gui.activate_buttons)

        elif event == GuiEvent.PRINT_FIRE_BOX_LABEL:

            self.gui.deactivate_buttons()
            self.application.busy()

            label_image = label_creator.create_fire_box_storage_label(self.member.member_number, self.member.get_name())

            self.application.slack_client.post_message_info(
                f"*#{self.member.member_number} - {self.member.get_name()}* tried to print a fire box storage label.")

            self.gui_print(label_image)

            self.application.notbusy()
            self.master.after(100, self.gui.activate_buttons)

    def on_event(self, event):
        super().on_event(event)

        event = event.event
        if event == Event.LOG_OUT:
            return WaitingState(self.application, self.master)

        elif event == Event.PRINT_TEMPORARY_STORAGE_LABEL:
            return EditTemporaryStorageLabel(self.application, self.master, self.member)


class WaitingForTokenState(State):
    def __init__(self, *args):
        super().__init__(*args)
        self.gui = WaitForTokenGui(self.master, self.gui_callback)
        self.token_reader_timer = None
        self.token_reader_timer_start()

    def gui_callback(self, gui_event):
        super().gui_callback(gui_event)

        event = gui_event.event
        data = gui_event.data

        # TODO This can be removed?
        if event == GuiEvent.TAG_READ:
            tag_id = data
            self.application.on_event(Event(Event.TAG_READ, tag_id))

    # TODO Do cleanup if not logged_in and restart timer.
    def token_reader_timer_expired(self):
        try:
            if self.application.makeradmin_client.configured:
                self.application.on_event(Event(Event.MAKERADMIN_CLIENT_CONFIGURED))
            else:
                self.token_reader_timer_start()
        except NetworkError:
            logger.error("Network error. Cannot connect to login server.")
            self.gui.show_error_message("Network error. Cannot connect to login server.")
            self.token_reader_timer_start()
        except Exception:
            logger.exception("Exception while waiting for makeradmin token")
            self.token_reader_timer_start()

    def token_reader_timer_start(self):
        self.token_reader_timer = self.master.after(1000, self.token_reader_timer_expired)

    def token_reader_timer_cancel(self):
        self.master.after_cancel(self.token_reader_timer)

    def on_event(self, event):
        super().on_event(event)

        event_type = event.event
        if event_type == Event.MAKERADMIN_CLIENT_CONFIGURED:
            return WaitForKeyReaderReadyState(self.application, self.master)


class WaitForKeyReaderReadyState(State):
    def __init__(self, *args):
        super().__init__(*args)
        self.gui = WaitForKeyReaderReadyGui(self.master)

        self.check_reader_connected_timeout = self.master.after(500, self.check_key_reader_ready)

    def check_key_reader_ready(self):
        try:
            self.application.key_reader = self.application.key_reader_class.get_reader()
            self.application.on_event(Event(Event.KEY_READER_CONNECTED))
        except KeyReaderNeedsRebootError:
            self.gui.show_error_message("The key reader has hanged. Unplug it and plug it in again.")
            self.check_reader_connected_timeout = self.master.after(500, self.check_key_reader_ready)
        except NoReaderFound:
            self.check_reader_connected_timeout = self.master.after(500, self.check_key_reader_ready)
        except Exception:
            logger.exception("Exception while waiting for key reader to get ready")

    def on_event(self, event):
        event_type = event.event
        if event_type == Event.KEY_READER_CONNECTED:
            self.master.after_cancel(self.check_reader_connected_timeout)
            return WaitingState(self.application, self.master)


class Application(object):
    def __init__(self, key_reader_class, makeradmin_client, slack_client):
        self.key_reader = None
        self.key_reader_class = key_reader_class
        self.makeradmin_client = makeradmin_client
        self.slack_client = slack_client

        tk = tkinter.Tk()
        tk.attributes('-fullscreen', not config.development)
        tk.configure(background='white')

        self.master = tk
        self.state = WaitingForTokenState(self, self.master)

        # Developing purposes
        if config.development:
            self.master.bind('<Escape>', lambda e: e.widget.quit())
            self.master.bind('<A>', lambda e: self.on_event(Event(Event.TAG_READ)))
        self.master.bind('<Alt-q>', lambda e: self.force_stop_application())

    def force_stop_application(self):
        logger.warning("User is force-stopping application")
        self.slack_client.post_message_alert("User is force-stopping the application")
        self.master.quit()

    def busy(self):
        self.master.config(cursor='watch')

    def notbusy(self):
        self.master.config(cursor='')

    def on_event(self, event):
        next_state = self.state.on_event(event)
        if next_state is not None and next_state is not self.state:
            self.state.change_state()
            self.state = next_state

    def run(self):
        self.slack_client.post_message_alert("Application was started!")
        self.master.mainloop()
