from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

bpm = 150
track_length = 60

track.append(MetaMessage('key_signature', key='C'))
track.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm)))
track.append(MetaMessage('time_signature', numerator=4, denominator=4))

i = 0
step = 60 / bpm
note_amount = track_length / step
while i < note_amount:
    track.append(Message('note_on', channel=0, note=60, velocity=100, time=0))
    track.append(Message('note_on', channel=0, note=61, velocity=100, time=0))
    track.append(Message('note_on', channel=0, note=62, velocity=100, time=0))

    track.append(Message('note_off', channel=0, note=60, velocity=100, time=480))
    track.append(Message('note_off', channel=0, note=61, velocity=100, time=0))
    track.append(Message('note_off', channel=0, note=62, velocity=100, time=0))

    i += 1
    # 480 = eine viertelnote
track.append(Message('note_on', channel=0, note=21, velocity=100, time=0))

track.append(MetaMessage('end_of_track'))

mid.save(f'comp/{bpm}bpm{track_length}sec.mid')
