class MidiMessage:
    def __init__(self, message, pedal_channel=176) -> None:
        self.m = message
        self.type = hex(message[0][0])
        self.parameters = message[0][1:]
        self.pedal_channel = pedal_channel

    def get_type(self):
        """
        Get the type of the midi message
        :return: type as string
        """
        if self.is_note_on():
            return "note_on"
        elif self.is_note_off():
            return "note_off"
        elif self.is_pedal_on():
            return "pedal_on"
        elif self.is_pedal_off():
            return "pedal_off"
        else:
            return "unknown"

    def is_note_on(self):
        """
        Check if the message is a note on message
        :return:
        """
        if '0x9' in self.type:
            return True
        return False

    def is_note_off(self):
        """
        Check if the message is a note off message
        :return:
        """
        if '0x8' in self.type:
            return True
        return False

    def is_pedal_on(self):
        """
        Check if the message is a pedal on message
        :return:
        """
        if '0xb' in self.type and self.parameters[1] != 0:
            return True
        return False

    def is_pedal_off(self):
        """
        Check if the message is a pedal off message
        :return:
        """
        if '0xb' in self.type and self.parameters[1] == 0:
            return True
        return False

    def get_midi_note_octave(self):
        """
        Get the octave of the midi note as integer
        :return: int
        """
        return int(self.get_midi_note_number() / 12) - 1

    def get_midi_note_names(self):
        """
        Get the name of the midi note as string
        :return: string
        """
        note = "C C#D D#E F F#G G#A A#B "
        substring_start = (self.get_midi_note_number() % 12) * 2
        note = note[substring_start:substring_start + 2]
        return note

    def get_midi_note_number(self):
        """
        Get the midi note number as integer
        :return: int
        """
        return self.parameters[0]

    def get_midi_velocity(self):
        """
        Get the midi velocity as integer
        :return: int 0-127
        """
        return self.parameters[1]

    def get_pedal_state(self):
        """
        Get the state of the pedal as integer
        :return: int
        """
        return self.parameters[1]

    def get_timestamp(self):
        """
        Get the time relative to the last midi event
        :return: float time relative to the last event
        """
        return self.m[1]
