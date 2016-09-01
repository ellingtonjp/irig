from scipy import signal
import irig
from irig import irigtime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Envelope detection using a small 3-tap IIR filter, easily implementable on an MCU

nyquist_frequency = irig.SAMPLE_FREQ/2

b, a = signal.iirfilter(3, rs=30, Wn=2000/nyquist_frequency, btype='lowpass', ftype='cheby2')

am_signal = pd.Series(irigtime.now().analog_signal)
noisy_signal = am_signal + np.random.normal(0, .5, len(am_signal))

rectified = [x**2 for x in noisy_signal]
filtered = signal.lfilter(b, a, rectified)

plt.plot(am_signal)
plt.plot(filtered)
plt.show()
