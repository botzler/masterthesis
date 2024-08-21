import threading
import time
from tkinter import colorchooser

import rtmidi
from midi.message import MidiMessage
from lightning.dmx_controller import DMXUniverse, hsv_to_rgb
from midi.tracker import MidiNoteTracker
from midi.input import MidiInput
from tkinter import *


def main():
    main_loop = MainLoop()
    gui(main_loop)


def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb


def hsv_to_hex(hsv):
    return rgb_to_hex(hsv_to_rgb(hsv))


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def gui(main_loop):
    """
    GUI for the Ambient Light Project
    :param main_loop:
    :return:
    """
    colorschemes = {
        "pop1": ["#7e288c", "#ffb51d", "#0ef51a"],
        "pop2": ["#9c7508", "#12f315", "#e4360a"],
        "R&B": ["#6e2695", "#e9004b", "#ca9915"],
        "rock": ["#9b2d68", "#3ee609", "#ca9915"],
        "funk": ["#7c7e2b", "#24dc2b", "#c80066"],
    }

    # Root Frame
    root = Tk()
    root.title("Ambient Light")
    root.minsize(800, 650)

    left_frame = Frame(root, width=400)
    left_frame.pack(side="left", fill="both", expand=True)

    right_frame = Frame(root, width=400)
    right_frame.pack(side="right", fill="both", expand=True)

    dmx_add_frame = Frame(right_frame, bg="lightgrey", height=100)
    dmx_add_frame.pack(side="top", fill="both", expand=True)

    device_frame = Frame(right_frame, height=100)
    device_frame.pack(side="bottom", fill="both", expand=True)

    command_frame = Frame(left_frame, height=100)
    command_frame.pack(side="top", fill="both", expand=True)

    dmx_list_frame = Frame(left_frame, bg="lightgrey", height=100)
    dmx_list_frame.pack(side="bottom", fill="both", expand=True)

    # Command Frame

    def start():
        drop_midi_port.config(state=DISABLED)
        try:
            port = int(number_midi.get("1.0", END))
        except ValueError:
            print("else")
            port_subs = midi_port.get().split(" ")
            port = port_subs[len(port_subs) - 1]
        print(port)

        main_loop.start_main(int(port))
        add_device.config(state=NORMAL)
        start_button.config(state=DISABLED)
        reset_tracker_button.config(state=NORMAL)
        pass

    def stop():
        main_loop.stop_main()
        time.sleep(0.5)
        root.quit()

    Label(command_frame, text="Control Panel", font=("Arial", 15)).pack(pady=5)

    # Midi Frame

    start_info = Label(command_frame, text="On Windows select a Midi input to Start")
    start_info.pack(pady=5)

    def port_selected(value):
        start_button.config(state=NORMAL)
        pass

    midi_ports = []
    midiin_ports = rtmidi.MidiIn()
    ports = range(midiin_ports.get_port_count())
    print(ports)
    if ports:
        for i in ports:
            print(midiin_ports.get_port_name(i))
            midi_ports.append(midiin_ports.get_port_name(i))
    midi_port = StringVar()
    drop_midi_port = OptionMenu(command_frame, midi_port, *midi_ports, command=port_selected)
    drop_midi_port.pack(pady=5)

    Label(command_frame, text="Or on Linux enter the port number").pack(pady=5, padx=20)
    number_midi = Text(command_frame, height=1, width=5)
    number_midi.pack(pady=5, padx=5)
    number_midi.bind("<Key>", port_selected)

    start_button = Button(command_frame, text="Start", width=20, height=2, command=start, state=DISABLED)
    start_button.pack(pady=5)

    stop_button = Button(command_frame, text="Stop", width=20, height=2, command=stop)
    stop_button.pack(pady=5)

    reset_tracker_button = Button(command_frame, text="Reset Tracker", width=20, height=2,
                                  command=main_loop.reset_tracker, state=DISABLED)
    # reset_tracker_button.pack(pady=5)

    # device Frame

    def dmx_disconnect():
        device_disc = devices_list.get(devices_list.curselection())
        devices_list.delete(devices_list.curselection())
        main_loop.remove_dmx_device(device_disc)
        for widget in device_frame.winfo_children():
            widget.destroy()
        # todo /n nicht mitsenden
        pass

    def device_options(event):
        if devices_list.curselection():
            for widget in device_frame.winfo_children():
                widget.destroy()
            # open new window
            device_id = devices_list.get(devices_list.curselection())
            Label(device_frame, text=f"Device {device_id} Settings", font=("Arial", 15)).grid(row=0, column=1, padx=10,
                                                                                              pady=10)
            mode = main_loop.get_device_mode(device_id)
            print(mode)
            Label(device_frame, text=f"mode = {mode}").grid(row=0, column=2, padx=10, pady=10)
            # Color Picker

            def color_picker():
                color = colorchooser.askcolor()
                color_picker_color.config(bg=color[1])

            def color_picker_1():
                color = colorchooser.askcolor()
                color_picker_color_1.config(bg=color[1])

            def color_picker_2():
                color = colorchooser.askcolor()
                color_picker_color_2.config(bg=color[1])

            color_picker = Button(device_frame, text="Highlight Color", width=15, height=2, command=color_picker)
            color_picker.grid(row=3, column=0, padx=10, pady=10)

            device_highlight = main_loop.get_highlight_color(device_id)
            device_hex = hsv_to_hex(device_highlight)
            color_picker_color = Canvas(device_frame, width=30, height=30, bg=device_hex)
            color_picker_color.grid(row=3, column=1, padx=10, pady=10)

            mood_1 = Button(device_frame, text="Low Mood Color", width=15, height=2, command=color_picker_1)
            mood_1.grid(row=4, column=0, padx=10, pady=10)

            device_highlight_1, device_highlight_2 = main_loop.get_mood_colors(device_id)
            device_hex_1 = hsv_to_hex(device_highlight_1)
            color_picker_color_1 = Canvas(device_frame, width=30, height=30, bg=device_hex_1)
            color_picker_color_1.grid(row=4, column=1, padx=10, pady=10)

            mood_2 = Button(device_frame, text="High Mood Color", width=15, height=2, command=color_picker_2)
            mood_2.grid(row=4, column=2, padx=10, pady=10)

            device_hex_2 = hsv_to_hex(device_highlight_2)
            color_picker_color_2 = Canvas(device_frame, width=30, height=30, bg=device_hex_2)
            color_picker_color_2.grid(row=4, column=3, padx=10, pady=10)

            disconnect_button = Button(device_frame, text="Disconnect Device", width=15, height=2,
                                       command=dmx_disconnect)
            disconnect_button.grid(row=7, column=1, padx=10, pady=10)

            update_button = Button(device_frame, text="Update Colors", width=15, height=2,
                                   command=lambda: main_loop.update_device_colors(color_picker_color.cget("bg"),
                                                                                  color_picker_color_1.cget("bg"),
                                                                                  color_picker_color_2.cget("bg"),
                                                                                  device_id))
            update_button.grid(row=6, column=1, padx=10, pady=10)


            def update_colorscheme(value):
                print(value)
                print(colorschemes[value])
                color_picker_color.config(bg=colorschemes[value][0])
                color_picker_color_1.config(bg=colorschemes[value][1])
                color_picker_color_2.config(bg=colorschemes[value][2])
                pass
            scheme = StringVar()
            scheme_menu = OptionMenu(device_frame, scheme,*colorschemes.keys(), command=update_colorscheme)
            scheme_menu.grid(row=6, column=0, padx=10, pady=10)
        else:
            for widget in device_frame.winfo_children():
                widget.destroy()
            # pass

    Label(dmx_list_frame, text="Devices", font=("Arial", 15)).pack(pady=5, side="top")
    devices_list = Listbox(dmx_list_frame, width=25)
    devices_list.pack(pady=5, side="top", expand=True)
    devices_list.bind('<<ListboxSelect>>', device_options)

    # DMX Add Frame

    Label(dmx_add_frame, text="Add new Device", font=("Arial", 15)).grid(row=9, column=1, padx=10, pady=10)

    def add_device():
        device_name = device_id.get("1.0", END)
        device_chan = device_channel.get("1.0", END)
        device_mo = device_mode.get()
        if main_loop.add_dmx_device(device_name, int(device_chan), device_mo):
            devices_list.insert(END, device_name)
        else:
            print("Device_id or channel already exists")
        pass

    Label(dmx_add_frame, text="Device ID").grid(row=10, column=0, padx=10, pady=10)
    device_id = Text(dmx_add_frame, height=1, width=5)
    device_id.grid(row=11, column=0, padx=10, pady=10)

    Label(dmx_add_frame, text="Device Channel").grid(row=10, column=1, padx=10, pady=10)
    device_channel = Text(dmx_add_frame, height=1, width=5)
    device_channel.grid(row=11, column=1, padx=10, pady=10)

    Label(dmx_add_frame, text="Device Mode").grid(row=10, column=2, padx=10, pady=10)
    device_mode = StringVar()
    drop_device_mode = OptionMenu(dmx_add_frame, device_mode, "normal", "highlight")
    drop_device_mode.grid(row=11, column=2, padx=10, pady=10, sticky="ew")

    add_device = Button(dmx_add_frame, text="Add Device", width=10, height=2, command=add_device, state=DISABLED)
    add_device.grid(row=15, column=1, padx=10, pady=10)

    mainloop()


class MainLoop:
    """
    Main Loop for the Ambient Light Project
    """
    def __init__(self):
        self.main_active = False
        self.midi_input = None
        self.tracker = None
        self.dmx_universe = None

    def start_main(self, port=None):
        """
        Start the main loop
        :param port:
        :return:
        """
        self.main_active = True

        # initialize midi input and tracker
        self.midi_input = MidiInput(port)
        self.tracker = MidiNoteTracker()
        self.dmx_universe = DMXUniverse(self.tracker)

        main_thread = threading.Thread(target=self.main_loop, name="Main Thread")
        main_thread.start()

    def add_dmx_device(self, device_name, start_channel, mode="normal"):
        """
        Add a new DMX device to the universe
        :param device_name:
        :param start_channel:
        :param mode:
        :return:
        """
        return self.dmx_universe.add_device(device_name, start_channel, mode)

    def remove_dmx_device(self, device_name):
        """
        Remove a DMX device from the universe
        :param device_name:
        :return:
        """
        self.dmx_universe.remove_device(device_name)

    def update_device_colors(self, hex_highlight, hex_low, hex_high, device_id):
        """
        Update the colors of a DMX device
        :param hex_highlight:
        :param hex_low:
        :param hex_high:
        :param device_id:
        :return:
        """
        print(hex_highlight, hex_low, hex_high)
        self.dmx_universe.update_device_colors(device_id, hex_to_rgb(hex_highlight), hex_to_rgb(hex_low),
                                               hex_to_rgb(hex_high))

    def get_devices(self):
        if self.dmx_universe is None:
            return []
        return self.dmx_universe.devices

    def get_device_mode(self, device_id):
        return self.dmx_universe.get_device_mode(device_id)

    def get_highlight_color(self, device_name):
        return self.dmx_universe.devices[device_name].highlight_hsv

    def get_mood_colors(self, device_name):
        return self.dmx_universe.devices[device_name].color_low_hsv, self.dmx_universe.devices[
            device_name].color_high_hsv

    def stop_main(self):
        self.main_active = False

    def reset_tracker(self):
        self.tracker.reset()

    def main_loop(self):
        """
        Main loop for the midi input port
        :return:
        """
        while self.main_active:
            m = self.midi_input.midiin.get_message()
            if m:
                midi_message = MidiMessage(m)
                self.tracker.evaluate_midi_input(m)
                if midi_message.get_midi_note_number() == 21:
                    # save current data to file and then delete it
                    print("end seen")
                    if len(self.tracker.calculated_tempos) > 0:
                        with open("mood_data.csv", "a") as file:
                            print("Writing to file")
                            print(self.tracker.all_arousal)
                            file.write(f"{self.tracker.all_arousal};")
                            file.write(f"{self.tracker.all_valence};")
                            file.write(f"{self.tracker.calculated_tempos};")
                            print(self.tracker.highlight_timings)
                            file.write(f"{self.tracker.highlight_timings}\n")
                        self.reset_tracker()

        self.dmx_universe.close_universe()


if __name__ == "__main__":
    main()
