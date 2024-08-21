# read in file
import re

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import wave
d = pd.read_csv("../mood_data.csv", sep=";")
# print(d.head())

# arou = []
# x_a = []
# # print(d["arousal"])
# for i,line in enumerate(d["arousal"]):
#     array = []
#
#     arr = line.strip('][').split(",")
#     for a in arr:
#         try:
#             array.append(float(a))
#         except:
#             array.append(float(a.split("(")[1].strip(")")))
#             # print(float(a.split("(")[1].strip(")")))
#     arou.append(array)
#     # for a in arr:
#     #     array.append(float(a.split("(")[1].strip(")")))
#     # arou.append(array)
#     x_a.append(np.linspace(0,60, len(array)))
#     plt.scatter(x_a[i], arou[i], marker="x")
# plt.show()

# plt.plot(x_a[0], arou[0])

### Mood
arou = []
x_a = []
for i,line in enumerate(d["arousal"]):
    data_points = []
    if i == 24:
        print("test")
        print(line)
        line = re.sub('[^0-9,.-]', '', line)
        print(line)
        arr = line.split(",")
        for x,a in enumerate(arr):
            data_points.append(float(a))
        arou.append(data_points)
        x_a.append(np.linspace(0,60, len(arr)))

# draw red vertikal line at the timestamps
valence = []
x_v = []
for i,line in enumerate(d["valence"]):
    data_points = []
    if i == 24:
        print("test")
        print(line)
        line = re.sub('[^0-9,.-]', '', line)
        print(line)
        arr = line.split(",")
        for x,a in enumerate(arr):
            data_points.append(float(a))
        valence.append(data_points)
        x_v.append(np.linspace(0,60, len(arr)))



sound = wave.open("../../data/highlights/song7.wav", "rb")
sample_frequency = sound.getframerate()
n_samples = sound.getnframes()
signal_wave = sound.readframes(n_samples)
duration = n_samples / sample_frequency
signal_array = np.frombuffer(signal_wave, dtype=np.int16)
time = np.linspace(0, duration, num=n_samples)

fig, ax1 = plt.subplots()

fig.set_figwidth(12)
ax1.set_ylabel('Mood')
ax1.set_xlabel('time (s)')
ax1.plot(x_a[0], arou[0])
ax1.plot(x_v[0], valence[0])
# ax1.set_title('Mood over time')
ax1.legend(["Arousal","Valence"])
ax1.set_ylim(-1,1)
ax1.set_xlim(0,60)

ax2 = ax1.twinx()
ax2.plot(time, signal_array,linewidth=0.5, color="black", alpha=0.2)
ax2.set_ylabel(' signal wave')
# plt.xlabel('time (s)')
# plt.xlim(0, time) #limiting the x axis to the audio time
plt.show()

### MOOD

### Highlight

for i,line in enumerate(d["highlight"]):
    timestamps = []
    types = []
    if i == 22:
        print("test")
        print(line)
        line = re.sub('[^0-9,.]', '', line)
        print(line)
        arr = line.split(",")
        for x,a in enumerate(arr):
            if x%2 == 0:
                timestamps.append(float(a))
            else:
                types.append(int(a))
        print(timestamps)
        #reduce times so lowest is 0
        timestamps = [x - timestamps[0] for x in timestamps]
        print(timestamps)
        #remove all timestamps over 60
        timestamps = [x for x in timestamps if x <= 60]
        # timestamps = [x for x in timestamps if x >= 10]
        # timestamps = [x - timestamps[0] for x in timestamps]
        print(types)
        print(timestamps)

        #     print(a.split("(")[1].strip(")"))
# draw red vertikal line at the timestamps


sound = wave.open("../../data/highlights/song5.wav", "rb")
sample_frequency = sound.getframerate()
n_samples = sound.getnframes()
signal_wave = sound.readframes(n_samples)
duration = n_samples / sample_frequency
signal_array = np.frombuffer(signal_wave, dtype=np.int16)
time = np.linspace(0, duration, num=n_samples)

plt.figure().set_figwidth(12)
for t in timestamps:
    t = t+5.4
    plt.axvline(t, color="red", ls="--")

plt.plot(time, signal_array,linewidth=0.5, color="black")
plt.title('Highlight moments')
plt.xlim(0, 60)
plt.ylabel(' signal wave')
plt.xlabel('time (s)')
# plt.xlim(0, time) #limiting the x axis to the audio time
plt.show()
### Highlight

# val = []
# x_v = []
# for i,line in enumerate(d["valence"]):
#     array = []
#     arr = line.strip('][').split(",")
#     for a in arr:
#         array.append(float(a.split("(")[1].strip(")")))
#     val.append(array)
#     x_v.append(np.linspace(0,60, len(array)))
#     # x[i] = np.linspace(0,60, len(data[i]))
#     #
#     # plt.plot(x[i],data[i] )


# ## Tempos
# temp = []
# x_t = []
# for t,tempos in enumerate(d["tempo"]):
#     array = []
#     arr = tempos.strip('][').split(",")
#     for a in arr[3:]:
#         array.append(int(a))
#
#     x_t.append(np.linspace(0,60, len(array)))
#     if t == 16 or t == 17:
#         # half values in array if its over 100
#         for x in range(len(array)):
#             if array[x] < 100:
#                 array[x] = array[x] * 2
#     if t == 15 or t == 14:
#         for x in range(len(array)):
#             if array[x] > 100:
#                 array[x] = array[x] / 2
#     temp.append(array)
#     # plt.scatter(x_t[t],temp[t],marker="x")
# # multiply tempo by 2 if it is below 100
# plt.scatter(x_t[14],temp[14],marker="x", color="blue")
#
# plt.scatter(x_t[15],temp[15],marker="x", color="orange")
# plt.scatter(x_t[16],temp[16],marker="x", color="green")
#
# plt.scatter(x_t[17],temp[17],marker="x", color="red")
#
# # plt.plot(x_t[0],temp[0])
# # plt.plot(x_t[1],temp[1])
# # plt.plot((d["valence"][0]))
# # plt.ylim(-1,1)
# # plt.xlim(0,len(d["valence"][0]))
# plt.yticks(np.arange(60, 150, step=10, ))
# plt.yticks(np.arange(65, 145, step=10), minor=True)
# plt.ylabel("Tempo in bpm")
# plt.xlabel("Time in seconds")
# # plt.title("Tempo estimations on perfect bpm")
# plt.title("Corrected Tempo estimations on played notes")
# #
# # plt.legend(["60 bpm","85 bpm","107 bpm","120 bpm","150 bpm"])
# plt.legend(["60 bpm","85 bpm","120 bpm","130 bpm"])
# # plt.legend(["120 bpm","130 bpm"])
# # plt.legend(["130 bpm"])

plt.show()
