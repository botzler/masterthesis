import threading

import rtmidi
import time
import mido
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def main(file_paths):
    midiout = rtmidi.MidiOut()

    ports = range(midiout.get_port_count())
    if ports:
        for i in ports:
            print(midiout.get_port_name(i))

    port_number = input("Enter port number: ")

    port = mido.open_output(port_number)
    for file in file_paths:
        f = mido.MidiFile(file, clip=True)
        for message in f.play():
            port.send(message)

        msg = mido.Message('note_on', note=21, velocity=100)
        port.send(msg)
        time.sleep(12)


if __name__ == "__main__":

    # main(["comp/120bpm60sec.mid", "comp/60bpm60sec.mid", "comp/85bpm60sec.mid", "comp/107bpm60sec.mid", "comp/150bpm60sec.mid"])
    # main(["oceans.mid"])
    # main(["piano/60bpm_chords_melody.mid", "piano/85bpm_chords_melody.mid", "piano/120bpm_chords_melody.mid", "piano/130bpm_chords_melody.mid"])
    main(["piano/60bpm_tones.mid", "piano/85bpm_tones.mid", "piano/120bpm_tones.mid", "piano/130bpm_tones.mid", "piano/130bpm_tones_eights.mid"])