#!/usr/bin/env python3.7


from src.sms_event import * 
from src.sms_gui import * 
from src import sms_label_creator
from src import sms_label_printer

root = Tk()
root.attributes('-fullscreen', True)
root.bind('<Escape>', lambda e: e.widget.quit())
root.configure(background='white')


# TODO 
# - Change gui model - do not redraw logotype, just a frame. 
# - Fix possibility to handle error
# - Investigate event emit from printing start/finish 
# - Naming of methods and variable
# - Clean up code

class State(object):
    
    def __init__(self, application, master): 
        print(f'Processing current state: {self}')
        self.application = application
        self.master = master 

    def gui_callback(self, gui_event):
        print(gui_event) 

    def on_event(self, event):
        pass

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
        
        elif event == GuiEvent.PRINT_BOX_LABEL or GuiEvent.PRINT_TEMPORARY_STORAGE_LABEL:
            
            self.application.busy()
            status = {}
            
            try: 

                if event == GuiEvent.PRINT_BOX_LABEL:

                    label = sms_label_creator.create_box_label('1234', 
                                                               'Stockholm Makerspace')
                elif event == GuiEvent.PRINT_TEMPORARY_STIRAGE_LABEL:

                    label = sms_label_creator.create_temporary_storage_label('1234', 
                                                                            'Stockholm Makerspace', 
                                                                            data)
             
                status = sms_label_printer.print_label(label)

            except:
                print('TODO - Handle this error!')

            finally:
                print(f'Printer status: {status}')
                
                # TODO Status must be inspected to detect if printing succeeded. 

                self.application.notbusy()


    def on_event(self, sms_event):

        print(sms_event)

        event = sms_event.event
        data = sms_event.data

        if event == SMSEvent.LOG_OUT:
            return  WaitingState(self.application, self.master)

        elif event == SMSEvent.PRINT_TEMPORARY_STORAGE_LABEL:
            self.gui = TemporaryStorage(self.master, self.gui_callback) 
        
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


    def on_event(self,event):
        self.state = self.state.on_event(event)

app = Application(root) 

root.mainloop()
root.destroy()

