import time
import numpy as np
import threading
from midi.message import MidiMessage
from signal_evaluation.tempo import estimate_tempo


class MidiNoteTracker:
    def __init__(self) -> None:
        self.played_notes = []
        self.notes_on_pedal = {}
        self.active_notes = {}
        self.last_note_durations = []
        self.pedal_active = False
        self.new_note_event = threading.Event()

        self.tempo_manager = threading.Thread(target=self.manage_tempo, name="Tempo Manager")
        self.tempo_manager_active = False

        self.calculated_tempos = []
        self.estimated_chords = []  # (timestamp, root_note, chord_type)
        self.bpm = None
        self.mood_manager_active = False
        self.mood_manager = threading.Thread(target=self.manage_mood, name="Mood Manager")

        self.current_mood = None  # (arousal, valence)
        self.all_arousal = []
        self.all_valence = []
        self.mood_set = threading.Event()

        self.lock = threading.Lock()

        self.highlight_factor = None
        self.highlight_set = threading.Event()
        self.highlight_timings = []

        self.tempo_manager.start()

    def reset(self):
        """
        Reset all values of the tracker
        :return:
        """
        self.played_notes = []
        self.notes_on_pedal = {}
        self.active_notes = {}
        self.last_note_durations = []
        self.pedal_active = False
        self.calculated_tempos = []
        self.estimated_chords = []
        self.bpm = None
        self.current_mood = None
        self.all_arousal = []
        self.all_valence = []
        self.highlight_factor = None

    def shutdown(self):
        """
        Shutdown all running threads and the tracker
        :return:
        """
        self.tempo_manager_active = False
        self.mood_manager_active = False
        self.new_note_event.set()
        self.mood_set.set()
        self.tempo_manager.join()

    def get_mood_value(self):
        """
        Get the current mood value
        :return: tuple (arousal, valence)
        """
        return self.current_mood

    def get_bpm(self):
        """
        Get the current estimated tempo in BPM
        :return: either the estimated tempo in BPM or None
        """
        return self.bpm

    def get_highlight_value(self):
        """
        Get the current highlight factor
        :return: float
        """
        return self.highlight_factor

    def evaluate_midi_input(self, midi_message):
        """
        Evaluate the midi message and call the corresponding function
        :param midi_message:
        :return:
        """
        m = MidiMessage(midi_message)
        # note on
        if m.is_note_on():
            self.note_on(m.get_midi_note_number(), m.get_midi_velocity())
            return "note_on"
        # note off
        elif m.is_note_off():
            self.note_off(m.get_midi_note_number())
            return "note_off"
        # pedal on
        elif m.is_pedal_on():
            self.pedal_on()
            return "pedal_on"
        # pedal off
        elif m.is_pedal_off():
            self.pedal_off()
            return "pedal_off"
        else:
            return "unknown"

    def note_on(self, note, velocity):
        """
        function to manage note_on events
        :param note:
        :param velocity:
        :return:
        """
        note_time = time.time()
        self.new_note_event.set()
        self.played_notes.append((note, time.time(), velocity))
        # with self.lock:
        if note not in self.active_notes:
            self.active_notes[note] = {'start_time': time.time(), 'velocity': velocity, 'pedal': self.pedal_active,
                                       'pressed': True}
            if self.estimate_highlight(note_time):
                self.highlight_set.set()
            self.get_played_chord()
        else:
            # Handle case where note is already active (e.g., note-on event while note is still playing)
            pass
        self.new_note_event.clear()

    def note_off(self, note) -> None:
        """
        function to manage note_off events
        :param note:
        :return:
        """
        if note in self.active_notes:
            start_time = self.active_notes[note]['start_time']
            end_time = time.time()
            duration = end_time - start_time

            self.active_notes[note]['pressed'] = False
            # Remove the note from the active_notes dictionary
            if not self.active_notes[note]['pedal']:
                self.last_note_durations.append(duration)
                del self.active_notes[note]
        else:
            # Handle case where note-off event is received without a corresponding note-on
            pass

    def pedal_on(self) -> None:
        """
        function to manage active notes with the pedal
        :return:
        """
        self.pedal_active = True
        for note in self.active_notes:
            self.active_notes[note]['pedal'] = True

    def pedal_off(self) -> None:
        """
        function to manage active notes with the pedal
        :return:
        """
        self.pedal_active = False
        notes_to_delete = [note for note in self.active_notes if not self.active_notes[note]['pressed']]
        for note in self.active_notes:
            self.active_notes[note]['pedal'] = False
        for note in notes_to_delete:
            del self.active_notes[note]

    def get_played_chord(self):
        """
        Estimate the chord that is currently played
        :return:
        """

        minor_major = {
            "Major": [4, 11],
            "Minor": [3, 10]

        }

        # Function to calculate the interval between two MIDI note numbers
        def calculate_interval(note1, note2) -> int:
            return (note2 - note1) % 12

        def get_midi_note_name(note_id):
            note = "C C#D D#E F F#G G#A A#B "
            substring_start = (note_id % 12) * 2
            note = note[substring_start:substring_start + 2]
            return substring_start

        sorted_active_notes = sorted(self.active_notes.keys())
        if len(sorted_active_notes) == 0:
            return []
        # Find the root note (lowest pitch)
        root_note = sorted_active_notes[0]
        root_number = get_midi_note_name(root_note)

        # Calculate intervals between the root note and other notes
        intervals = list(dict.fromkeys(sorted([calculate_interval(root_note, note) for note in sorted_active_notes])))

        # Check each known chord pattern
        for interval in intervals:
            if interval in minor_major["Major"]:
                self.estimated_chords.append((time.time(), root_number, "Major"))
                return
            elif interval in minor_major["Minor"]:
                self.estimated_chords.append((time.time(), root_number, "Minor"))
                return
        return

    def manage_tempo(self):
        """
        Thread to estimate the tempo of the recent played notes
        :return:
        """
        self.tempo_manager_active = True
        while self.tempo_manager_active:
            estimated_tempo = self.estimate_tempo()
            if estimated_tempo is not None:
                self.calculated_tempos.append(estimated_tempo)

            # 0.37 seconds is used in https://ieeexplore.ieee.org/abstract/document/6879451
            time.sleep(0.37)

    def estimate_tempo(self):
        """
        :return: estimated tempo in BPM
        """
        self.bpm = estimate_tempo(self.played_notes)
        if not self.mood_manager_active and self.bpm is not None:
            self.mood_manager.start()
        return self.bpm

    def manage_mood(self):
        """
        Thread to manage the mood estimation
        :return:
        """
        print("Mood manager started")
        self.mood_manager_active = True
        while self.mood_manager_active:
            estimated_mood = self.estimate_mood()
            if estimated_mood is not None:
                self.current_mood = estimated_mood
                self.all_arousal.append(estimated_mood[0])
                self.all_valence.append(estimated_mood[1])
                self.mood_set.set()
                time.sleep(0.5)
            else:
                # wait until new note is played
                self.new_note_event.wait()

    def estimate_mood(self):
        """
        Estimate the mood of the recent played notes
        based on some mathematical features of the notes
        :return: tuple (arousal, valence) from -1 to 1
        """
        if self.bpm is None or self.bpm == 0:
            return None

        # sigmoid function where 0 = -1 and 127 = 1
        # linear scale max_velocity to -10 and 10
        # then scale sigmoid value to -1 and 1
        # https://www.digitalocean.com/community/tutorials/sigmoid-activation-function-python
        def sigmoid(x):
            return 1 / (1 + np.exp(-x))

        # get notes from last 10 seconds
        duration = 6
        start_time = time.time() - duration
        played_notes = [note for note in self.played_notes if note[1] > start_time]
        if len(played_notes) < 2:
            return None

        # get velocities from last 10 seconds
        velocities = [note[2] for note in played_notes]
        timings = [note[1] for note in played_notes]
        notes = [note[0] for note in played_notes]

        # get highest velocity
        max_velocity = max(velocities)
        # get timestemp of highest velocity
        # to remove divide by 0
        max_velocity_time = abs(
            [note[1] for note in played_notes if note[2] == max_velocity][0] - time.time()) + 0.00001

        # get frequency range
        # lowest note
        lowest_note = min(notes)
        # highest note
        highest_note = max(notes)
        # frequency range
        t_range = highest_note - lowest_note

        # get number of notes but only count one note if multiple notes are played at the same time
        # caluclate expected time between notes
        tempo = self.bpm
        # divide by 2 for eights
        beat_interval = (60 / tempo)
        beat_eights = beat_interval / 2
        # possible offset
        offset = 0.9
        beat_eights_off = beat_eights * offset
        # get notes that are not played at the same time

        # sort notes by time
        timings.sort()
        # calculate time differences between notes
        time_diff = [timings[i] - timings[i - 1] for i in range(1, len(timings))]
        # only take time differences that are bigger than the beat interval
        time_diff = [diff for diff in time_diff if diff > beat_eights_off]
        # calculate number of notes
        number_of_notes = len(time_diff) + 1

        # length of played notes
        # get up to last 30 note durations
        last_note_durations = self.last_note_durations[-30:]
        # calculate average note duration
        avg_duration = np.mean(last_note_durations)
        # calculate average note duration in relation to beat interval
        avg_duration_rel = avg_duration / beat_interval
        # rate it into -1 and 1 on sigmoid function
        avg_duration_rel = sigmoid(avg_duration_rel)

        # analyze chords from last 2 seconds
        chord_duration = 2
        chord_time = time.time() - chord_duration
        chords = [chord for chord in self.estimated_chords if chord[0] > chord_time]
        if len(chords) == 0:
            val_tonality = 0
        else:
            # get the most common chord
            chord = max(set(chords), key=chords.count)
            # get the type of the chord
            chord_type = chord[2]
            # get the tonality of the chord
            if chord_type == "Major":
                val_tonality = 1
            elif chord_type == "Minor":
                val_tonality = -1
            else:
                val_tonality = 0

        # calculate some arousal and valence score from -1 to 1
        # arousal setzt sich zusammen aus lautstärke und anzahl der anschläge und der länge der noten
        # anzahl der schläge im verhältnis zu viertelnoten
        # jede viertel ist 0, jede achtel und mehr 1
        # jede halbe und weniger -1
        quarts = duration / beat_interval

        # valence setzt sich zusammen aus dur moll und tonumfang
        # tonumfang von 88 Tönen heruntergebrochen mit sigmoid
        val_range = sigmoid((t_range - 44) / 4.4) * 2 - 1
        val_high = sigmoid((highest_note - 44) / 4.4) * 2 - 1
        val_low = sigmoid((lowest_note - 44) / 4.4) * 2 - 1

        # standard deviation of notes
        # valence
        # zwischen 5 und 15 linear auf -1 und 1
        std_notes = np.std(notes)
        val_std_notes = np.clip((std_notes - 10) / 5, -1, 1)

        # spectral centroid
        # valence
        # 60 ist mittleres C, 50 ist niedrig, 70 ist hoch
        centroid = np.average(notes, weights=velocities)
        val_centroid = np.clip((centroid - 60) / 10, -1, 1)

        # arousal

        # intensity - summe aller velocities
        # Arousal - irgendwas von mehreren tausend, sinnvoller im vergleich zum letzten zu schauen
        intensity = sum(velocities)
        # aro_intensity =

        # Anzahl der Anschläge
        # normalize between -1 and 1
        aro_hits = min(max(2 / quarts * number_of_notes - 2, -1), 1)

        # maximale lautstärke

        # max velocity
        aro_max_velocity = sigmoid((max_velocity - 63.5) / 6.35) * 2 - 1

        # average velocity
        aro_avg_velocity = sigmoid((np.mean(velocities) - 63.5) / 6.35) * 2 - 1

        # maximale velocity gewichten, mit der Zeit abnehmend
        weight = min(max(-((np.log(max_velocity_time)) / 2) + 1, 0), 1)
        weighted_max = max_velocity * weight
        weighted_velocity = (np.mean(velocities) + weighted_max) / (1 + weight)
        aro_weighted_velocity = sigmoid((weighted_velocity - 63.5) / 6.35) * 2 - 1

        # weight arousal and valence factors and return a tuple
        arousal = (aro_hits + aro_max_velocity + aro_avg_velocity + aro_weighted_velocity) / 4
        valence = (val_range + val_high + val_low + val_centroid + val_std_notes) / 5
        return arousal, valence

    def estimate_highlight(self, note_time):
        """
        Estimate if the played note should be highlighted
        Based on std deviation of recently played notes
        :return: boolean if note should be highlighted
        """

        if len(self.played_notes) < 5:
            return False
        played_note = self.played_notes[-1]
        played_note_velocity = played_note[2]

        # average velocity last 3 seconds:
        start_time = time.time() - 2
        last_notes = [note for note in self.played_notes if note[1] > start_time]
        if len(last_notes[1:]) == 0:
            return False
        avg_velocity = np.mean([note[2] for note in last_notes[1:]])
        # standard deviation of velocities
        std_velocity = np.std([note[2] for note in last_notes[1:]])

        # if played note is 1.2 standard deviations higher than average velocity
        if played_note_velocity > avg_velocity + 1.2 * std_velocity:
            self.highlight_factor = played_note_velocity / avg_velocity
            self.highlight_timings.append((time.time(),0))
            return True
        # intensity über lautstärke der noten
        intensity_time = time.time() - 0.1
        intensity_notes = [note for note in last_notes if note[1] > intensity_time]
        intensity = sum([note[2] for note in intensity_notes])
        if intensity > 400:
            self.highlight_factor = intensity / 400
            self.highlight_timings.append((time.time(),1))
            return True
        return False
