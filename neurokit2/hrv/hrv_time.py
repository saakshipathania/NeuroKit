# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..stats import mad, summary_plot
from .hrv_utils import _hrv_get_rri, _hrv_sanitize_input


def hrv_time(peaks, sampling_rate=1000, show=False):
    """ Computes time-domain indices of Heart Rate Variability (HRV).

     See references for details.

    Parameters
    ----------
    peaks : dict
        Samples at which cardiac extrema (i.e., R-peaks, systolic peaks) occur.
        Dictionary returned by ecg_findpeaks, ecg_peaks, ppg_findpeaks, or
        ppg_peaks.
    sampling_rate : int, optional
        Sampling rate (Hz) of the continuous cardiac signal in which the peaks
        occur. Should be at least twice as high as the highest frequency in vhf.
        By default 1000.
    show : bool
        If True, will plot the distribution of R-R intervals.

    Returns
    -------
    DataFrame
        Contains time domain HRV metrics:
        - "*RMSSD*": the square root of the mean of the sum of successive differences between adjacent RR intervals.
        - "*MeanNN*": the mean of the RR intervals.
        - "*SDNN*": the standard deviation of the RR intervals.
        - "*SDSD*": the standard deviation of the successive differences between RR intervals.
        - "*CVNN*": the standard deviation of the RR intervals (SDNN) divided by the mean of the RR intervals (MeanNN).
        - "*CVSD*": the root mean square of the sum of successive differences (RMSSD) divided by the mean of the RR intervals (MeanNN).
        - "*MedianNN*": the median of the absolute values of the successive differences between RR intervals.
        - "*MadNN*": the median absolute deviation of the RR intervals.
        - "*HCVNN*": the median absolute deviation of the RR intervals (MadNN) divided by the median of the absolute differences of their successive differences (MedianNN).
        - "*pNN50*": the proportion of RR intervals greater than 50ms, out of the total number of RR intervals.
        - "*pNN20*": the proportion of RR intervals greater than 20ms, out of the total number of RR intervals.
        - "*TINN*": a geometrical parameter of the HRV, or more specifically, the baseline width of the RR intervals distribution obtained by triangular interpolation, where the error of least squares determines the triangle. It is an approximation of the RR interval distribution.
        - "*HTI*": the HRV triangular index, measuring the total number of RR intervals divded by the height of the RR intervals histogram.

    See Also
    --------
    ecg_peaks, ppg_peaks, hrv_frequency, hrv_summary, hrv_nonlinear

    Examples
    --------
    >>> import neurokit2 as nk
    >>>
    >>> # Download data
    >>> data = nk.data("bio_resting_5min_100hz")
    >>>
    >>> # Find peaks
    >>> peaks, info = nk.ecg_peaks(data["ECG"], sampling_rate=100)
    >>>
    >>> # Compute HRV indices
    >>> hrv = nk.hrv_time(peaks, sampling_rate=100, show=True)

    References
    ----------
    - Stein, P. K. (2002). Assessing heart rate variability from real-world
      Holter reports. Cardiac electrophysiology review, 6(3), 239-244.
    - Shaffer, F., & Ginsberg, J. P. (2017). An overview of heart rate
    variability metrics and norms. Frontiers in public health, 5, 258.
    """
    # Sanitize input
    peaks = _hrv_sanitize_input(peaks)

    # Compute R-R intervals (also referred to as NN) in milliseconds
    rri = _hrv_get_rri(peaks, sampling_rate=sampling_rate, interpolate=False)
    diff_rri = np.diff(rri)

    out = {}  # Initialize empty container for results

    # Mean based
    out["RMSSD"] = np.sqrt(np.mean(diff_rri ** 2))
    out["MeanNN"] = np.mean(rri)
    out["SDNN"] = np.std(rri, ddof=1)
    out["SDSD"] = np.std(diff_rri, ddof=1)
    out["CVNN"] = out["SDNN"] / out["MeanNN"]
    out["CVSD"] = out["RMSSD"] / out["MeanNN"]

    # Robust
    out["MedianNN"] = np.median(np.abs(rri))
    out["MadNN"] = mad(rri)
    out["MCVNN"] = out["MadNN"] / out["MedianNN"]

    # Extreme-based
    nn50 = np.sum(np.abs(diff_rri) > 50)
    nn20 = np.sum(np.abs(diff_rri) > 20)
    out["pNN50"] = nn50 / len(rri) * 100
    out["pNN20"] = nn20 / len(rri) * 100

    # Geometrical domain
    bar_y, bar_x = np.histogram(rri, bins="auto")
    out["TINN"] = np.max(bar_x) - np.min(bar_x)  # Triangular Interpolation of the NN Interval Histogram
    out["HTI"] = len(rri) / np.max(bar_y)  # HRV Triangular Index

    if show:
        _hrv_time_show(rri)

    out = pd.DataFrame.from_dict(out, orient="index").T.add_prefix("HRV_")
    return out


def _hrv_time_show(rri, **kwargs):

    fig = summary_plot(rri, **kwargs)
    plt.xlabel("R-R intervals (ms)")
    fig.suptitle("Distribution of R-R intervals")

    return fig
