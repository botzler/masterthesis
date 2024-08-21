import numpy as np
import time
from scipy import signal
from scipy.interpolate import interp1d


def create_pulse_train(peak, corr, v, weight):
    """
    Create a pulse train with a peak at the given position
    :param peak:
    :param corr:
    :param v:
    :param weight:
    :return:
    """
    pulse_train = np.zeros(len(corr))
    pulse_train[int(peak * 0 * v)] = weight
    pulse_train[int(peak * 1 * v)] = weight
    try:
        pulse_train[int(peak * 2 * v)] = weight
    except:
        pass
    try:
        pulse_train[int(peak * 3 * v)] = weight
    except:
        pass
    return pulse_train


def evaluate_pulse_trains(corr, peaks, sampling_rate):
    """
    Evaluate pulse trains for given peaks
    :param corr:
    :param peaks:
    :param sampling_rate:
    :return:
    """
    # Evaluate pulse trains
    # For each peak, evaluate the pulse train
    highest_score = 0
    estimated_tempo = 0
    for peak in peaks:
        pulse_train = np.zeros(len(corr))
        # v = 1, weight 1
        pulse_train_1 = create_pulse_train(peak, corr, 1, 1)
        # v = 1.5, weight 0.5
        pulse_train_15 = create_pulse_train(peak, corr, 1.5, 0.5)
        # v = 2, weight 0.5
        pulse_train_2 = create_pulse_train(peak, corr, 2, 0.5)

        # combined pulse train
        combined_pulse_train = pulse_train_1 + pulse_train_15 + pulse_train_2

        # cross correlate with original signal
        cross_corr = signal.correlate(corr, combined_pulse_train, mode='full')

        # find max of cross correlation
        max_corr = np.max(cross_corr)
        # find variance of cross correlation
        var_corr = np.var(cross_corr)

        score = max_corr + var_corr
        if score > highest_score:
            highest_score = score
            estimated_tempo = int(60 * sampling_rate / peak)
    return estimated_tempo, highest_score


def find_top_peaks(corr, sampling_rate, num_peaks=5, min_distance=10):
    """
    Find the top peaks in the autocorrelation function
    :param sampling_rate:
    :param corr: signal to find peaks in
    :param num_peaks:
    :param min_distance:
    :return: sorted peaks and their value
    """
    max_lag = 60 * sampling_rate / 55
    min_lag = 60 * sampling_rate / 210

    peaks, _ = signal.find_peaks(corr, distance=min_distance)

    # reduce to only peaks between minimum and maximum autocorrelation lag
    peaks = peaks[(peaks > min_lag) & (peaks < max_lag)]
    peak_values = corr[peaks]
    top_peaks_indices = np.argsort(peak_values)[-num_peaks:]
    top_peaks = peaks[top_peaks_indices]
    top_peaks = top_peaks[np.argsort(corr[top_peaks])[::-1]]
    return top_peaks, corr[top_peaks]


def enhance_corr(corr):
    """
    Enhance the autocorrelation function by adding time-stretched versions of the original signal
    :param corr:
    :return:
    """
    # Length of the original array
    length = len(corr)

    # Create time-stretched versions of the array by factors of 2 and 4
    x = np.arange(length)
    interp_func_2 = interp1d(x, corr, kind='linear', fill_value="extrapolate")
    interp_func_4 = interp1d(x, corr, kind='linear', fill_value="extrapolate")

    x2 = np.linspace(0, length - 1, 2 * length)
    x4 = np.linspace(0, length - 1, 4 * length)

    corr_2t = interp_func_2(x2)[:length]  # Downsample to original length
    corr_4t = interp_func_4(x4)[:length]  # Downsample to original length

    # Enhanced autocorrelation: EAC_m(t) = A_m(t) + A_m(2*t) + A_m(4*t)
    enhanced_corr = corr + corr_2t + corr_4t

    return enhanced_corr


def estimate_tempo(played_notes):
    """
    Estimate tempo using scipy autocorrelation and based on paper
    :return: estimated tempo in bpm
    """
    sampling_rate = 344
    # window of 2048 samples
    duration = 2048 / sampling_rate  # seconds
    # get notes from last X seconds
    start_time = time.time() - duration
    note_timings = [(note[1], note[2]) for note in played_notes if note[1] > start_time]

    if len(note_timings) < 4:
        return None
    zero_time = note_timings[0][0]
    note_timings = [(note[0] - zero_time, note[1]) for note in note_timings]

    signal_data = np.zeros(int(duration * sampling_rate))
    for timing in note_timings:
        sample_index = int(np.floor(timing[0] * sampling_rate))
        # use velocity as y value to emphasize strong onsets
        signal_data[sample_index] = timing[1]
        # signal_data[sample_index] = 1
    corr = signal.correlate(signal_data, signal_data, mode='full')
    corr = corr / np.max(corr)
    # cut negative half off, since its mirrored
    corr = corr[len(corr) // 2:]

    # cut peak at 0-5
    corr[0:5] = 0

    # enhance harmonics nach paper
    corr = enhance_corr(corr)

    # pick top 5 peaks, some sorted
    peaks, values = find_top_peaks(corr, sampling_rate, num_peaks=5, min_distance=20)
    # Evaluate Pulse trains
    estimated_tempo, highest_score = evaluate_pulse_trains(corr, peaks, sampling_rate)
    if estimated_tempo < 58:
        estimated_tempo = estimated_tempo * 2
    return estimated_tempo
