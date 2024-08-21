import platform
import time
import threading
import colorsys
from DMXEnttecPro import Controller


def rgb_to_hsv(rgb):
    # RGB-Werte skalieren
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    # Konvertierung von RGB zu HSV
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    # HSV-Werte skalieren und auf den richtigen Bereich setzen
    h = int(h * 360)
    s = int(s * 100)
    v = int(v * 100)
    return (h, s, v)


def hsv_to_rgb(hsv):
    # HSV-Werte skalieren und auf den richtigen Bereich setzen
    h, s, v = hsv[0] / 360.0, hsv[1] / 100.0, hsv[2] / 100.0
    # Konvertierung von HSV zu RGB
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    # RGB-Werte skalieren und auf den richtigen Bereich setzen
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    return (r, g, b)


class DMXUniverse:
    # TODO automatisch nach controller suchen
    def __init__(self, midiTracker, port='/dev/ttyUSB0'):
        if platform.system() == "Windows":
            port = 'COM4'
        try:
            self.dmx = Controller(port)
        except:
            print("No DMX device found")
            return
        self.devices = {}
        self.midiTracker = midiTracker
        self.active = True

        self.highlight_thread = threading.Thread(target=self.set_highlight_color, name="Highlight Thread")
        self.highlight_thread.start()

        self.mood_thread = threading.Thread(target=self.set_mood_colors, name="Mood Thread")
        self.mood_thread.start()

    def add_device(self, device_id, start_channel, mode="normal"):
        """
        Add a device to the universe
        :param device_id:
        :param start_channel:
        :param mode:
        :return: True if device was added, False if device already exists
        """
        for device in self.devices.values():
            if device.start_channel == start_channel:
                return False
            if device_id == device.id:
                return False
        device = DMXDevice(device_id, start_channel, mode, self.dmx)
        # device.set_dmx(self.dmx)
        self.devices[device_id] = device
        return True

    def remove_device(self, device_id):
        """
        Remove a device from the universe and set it to black
        :param device_id:
        :return:
        """
        self.devices[device_id].set_rgb(0, 0, 0)
        self.devices[device_id].shutdown()
        del self.devices[device_id]

    def get_device_mode(self, device_id):
        """
        Get the mode of a device
        :param device_id:
        :return: mode
        """
        return self.devices[device_id].mode

    def close_universe(self):
        """
        Close the universe and set all devices to black
        :return:
        """
        self.active = False
        self.midiTracker.highlight_set.set()
        self.midiTracker.mood_set.set()
        for device in self.devices.values():
            device.set_rgb(0, 0, 0)
            device.shutdown()
        time.sleep(0.5)
        self.midiTracker.shutdown()
        self.dmx.close()

    def update_device_colors(self, device_id, highlight_rgb, low_rgb, high_rgb):
        """
        Update the color scheme of a device
        :param device_id:
        :param highlight_rgb:
        :param low_rgb:
        :param high_rgb:
        :return:
        """
        print(highlight_rgb, low_rgb, high_rgb)
        self.devices[device_id].set_highlight_color(*rgb_to_hsv(highlight_rgb))
        self.devices[device_id].set_color_scheme(rgb_to_hsv(low_rgb), rgb_to_hsv(high_rgb))

    def set_mood_colors(self):
        """
        Thread to Set the mood event of all devices in "mood", if set by tracker
        :return:
        """
        while self.active:
            self.midiTracker.mood_set.clear()
            self.midiTracker.mood_set.wait()
            if self.active:
                # listen to tracker and set color based on mood value changes
                for device in self.devices.values():
                    if device.mode == "normal":
                        mood = self.midiTracker.get_mood_value()
                        # calculate color based on mood value
                        hsv1, hsv2 = device.get_mood_colors()
                        h = (hsv2[0] - hsv1[0]) / 2 * mood[1] + (hsv2[0] + hsv1[0]) / 2
                        s = (hsv2[1] - hsv1[1]) / 2 * mood[1] + (hsv2[1] + hsv1[1]) / 2
                        v = 45 * mood[0] + 55
                        # h = (hsv2[0]-hsv1[0]) / 2 * mood[0] + (hsv2[0]+hsv1[0]) / 2
                        # s = (hsv2[1]-hsv1[1]) / 2 * mood[0] + (hsv2[1]+hsv1[1]) / 2
                        # v = 45 * mood[1] + 50
                        device.set_rgb_time(*hsv_to_rgb((h, s, v)), 0.4)

    def set_highlight_color(self):
        """
        Thread to Set the highlight event of the device, if set by tracker
        :return:
        """
        while self.active:
            # listen to tracker and set color based on highlight value changes
            self.midiTracker.highlight_set.clear()
            self.midiTracker.highlight_set.wait()
            if self.active:
                for device in self.devices.values():
                    if device.mode == "highlight":
                        # if not device.highlight_thread.is_alive():
                        #     device.highlight_thread.start()
                        if self.midiTracker.get_bpm() is None:
                            break
                        device.current_bpm = self.midiTracker.get_bpm()
                        device.new_highlight_event.set()


class DMXDevice:
    def __init__(self, id, start_channel, mode, dmx, r=0, g=0, b=0):
        self.dmx = dmx
        self.id = id
        self.start_channel = start_channel  # Start DMX channel of the device
        self.r = r  # current color
        self.g = g  # current color
        self.b = b  # current color

        # ColorManager
        self.mode = mode
        self.hsv = (0, 0, 0)  # current color
        self.hsv_target = (0, 0, 0)  # target color
        self.target_time = 0
        self.active = True
        self.mood_value = (0, 0)

        self.device_active = threading.Thread(target=self.color_thread, name=f"Device {id}")
        self.new_color_event = threading.Event()  # Event to signal a new color was set - for fading
        self.step_time = 0.005

        self.highlight_thread = threading.Thread(target=self.highlight_thread, name=f"Highlight {id}")
        self.new_highlight_event = threading.Event()
        self.current_bpm = None

        self.highlight_hsv = (0, 0, 100)  # HSV
        self.color_low_hsv = (0, 100, 50)  # HSV
        self.color_high_hsv = (60, 100, 100)  # HSV

        self.start()

    def start(self):
        """
        Start the device
        :return:
        """
        self.device_active.start()
        if self.mode == "normal":
            h = (self.color_high_hsv[0] + self.color_low_hsv[0]) / 2
            s = (self.color_high_hsv[1] + self.color_low_hsv[1]) / 2
            v = (self.color_high_hsv[2] + self.color_low_hsv[2]) / 2
            self.hsv = (h, 0, 0)
            self.set_rgb_time(*hsv_to_rgb((h, s, v)), 1)
        elif self.mode == "highlight":
            self.set_rgb_time(*hsv_to_rgb(self.color_low_hsv), 0.5)
            time.sleep(0.5)
            self.set_rgb_time(0, 0, 0, 0.5)
            self.highlight_thread.start()

    def shutdown(self):
        """
        Shutdown the device
        :return:
        """
        self.active = False
        self.new_color_event.set()
        self.new_highlight_event.set()
        if self.device_active:
            self.device_active.join()

    def highlight_thread(self):
        """
        Thread that highlights the device if the event is set by the Universe
        :return:
        """
        print("Highlight Thread started")
        while self.active:
            self.new_highlight_event.wait()
            if not self.active:
                break
            if self.current_bpm is None or self.current_bpm == 0:
                self.new_highlight_event.clear()
                continue
            sleeptime = (60 / self.current_bpm) / 2  # achtelnote zeit
            self.set_rgb_time(*hsv_to_rgb(self.highlight_hsv),0)
            time.sleep(sleeptime)
            self.set_rgb_time(0, 0, 0, 0)
            time.sleep(sleeptime)
            second_hsv = (self.highlight_hsv[0], self.highlight_hsv[1], self.highlight_hsv[2] * 0.66)
            self.set_rgb_time(*hsv_to_rgb(second_hsv), 0)
            time.sleep(sleeptime)
            self.set_rgb_time(0, 0, 0, 0)
            time.sleep(sleeptime)
            self.new_highlight_event.clear()

    def set_highlight_color(self, h, s, v):
        """
        Set the highlight color of the device
        """
        self.highlight_hsv = (h, s, v)

    def set_color_scheme(self, low, high):
        """
        Set the color scheme of the device
        :param low: low_hsv
        :param high: high_hsv
        """
        self.color_low_hsv = low
        self.color_high_hsv = high

    def set_color(self):
        """
        Sets the color of the device to the current hsv value
        :return: void
        """
        self.dmx.set_channel(self.start_channel, self.r)
        self.dmx.set_channel(self.start_channel + 1, self.g)
        self.dmx.set_channel(self.start_channel + 2, self.b)
        self.dmx.submit()  # Sends the update to the controller

    def set_rgb(self, r, g, b):
        """
        Set the RGB color of the device.
        """
        self.r = r
        self.g = g
        self.b = b
        threading.Thread(target=self.set_color, name="Setting Color").start()

    def get_mood_colors(self):
        """
        Get the current mood colors
        :return: low_hsv, high_hsv
        """
        return self.color_low_hsv, self.color_high_hsv

    def get_highlight_color(self):
        """
        Get the current highlight color
        :return: highlight_hsv
        """
        return self.highlight_hsv

    def color_thread(self):
        """
        Thread to fade the color of the device
        :return:
        """
        while self.active:
            self.new_color_event.clear()
            self.new_color_event.wait()
            # solange die farbe nicht stimmt, wird sie angepasst
            while self.active and not self.hsv == self.hsv_target:
                # calculate color step based on target time and color difference
                h_diff = self.hsv_target[0] - self.hsv[0]
                s_diff = self.hsv_target[1] - self.hsv[1]
                v_diff = self.hsv_target[2] - self.hsv[2]
                t_diff = max(self.target_time - time.time(), 0)
                if t_diff <= 0.005:
                    self.hsv = self.hsv_target
                    self.set_rgb(*hsv_to_rgb(self.hsv))
                    break
                steps = t_diff / self.step_time
                h_step = h_diff / steps
                s_step = s_diff / steps
                v_step = v_diff / steps
                self.hsv = (self.hsv[0] + h_step, self.hsv[1] + s_step, self.hsv[2] + v_step)
                self.set_rgb(*hsv_to_rgb(self.hsv))
                time.sleep(self.step_time)

    def set_rgb_time(self, r, g, b, t_time=0.0):
        """
        Set the RGB color of the device with a fade time
        """
        self.hsv_target = rgb_to_hsv((r, g, b))
        self.target_time = time.time() + t_time
        self.new_color_event.set()
