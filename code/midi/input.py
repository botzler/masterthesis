import rtmidi
import threading


class MidiInput:
    def __init__(self, port=1):
        self.midiin = rtmidi.MidiIn()
        self.port = port
        self.stop_event = threading.Event()
        self._open_port()

    def _open_port(self):
        """
        Open the midi port
        :return:
        """
        ports = range(self.midiin.get_port_count())
        if ports:
            for i in ports:
                print(self.midiin.get_port_name(i))
            if self.port is None:
                self.port = int(input("Enter port number: "))
            try:
                self.midiin.open_port(self.port)
                print("Midi port opened")
                return True
            except:
                print("Midi port not found")
                return False
        print("Midi port not found")
        return False

    def get_message(self):
        """
        Get a midi message from the input
        :return:
        """
        return self.midiin.get_message()

    def stop(self):
        """
        Stop the midi input and close the port
        :return:
        """
        self.stop_event.set()
        self.midiin.close_port()
