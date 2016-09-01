from datetime import datetime
from functools import partial
import math
import random

TTL_AMP = 5           # Amplitude of the digital signal
AM_LARGE_AMP = 5      # Amplitude of an analog '1' bit
AM_SMALL_AMP = 5/3    # Amplitude of an analog '0' bit
PULSE_WIDTH = 10      # Based on IRIG spec
BIT_WIDTH = {'0': 2, '1': 5, '_': 8}  #  Based on IRIG spec
OFFSET=0
CARRIER_FREQ = 1000   # Based on IRIG spec
SAMPLE_FREQ = 32000   # Somewhat arbitrarily chosen. This produces 32 samples/wave
SAMPLES = SAMPLE_FREQ//CARRIER_FREQ

NUM_FRAME_BITS = 100  # Based on IRIG spec

f = lambda x, a, c=CARRIER_FREQ, s=SAMPLE_FREQ, o=OFFSET: a*math.sin(x*c/s*2*math.pi)+o
LARGE_WAVE = [f(x, AM_LARGE_AMP) for x in range(SAMPLES)]
SMALL_WAVE = [f(x, AM_SMALL_AMP) for x in range(SAMPLES)]

def random_bit():
    """Returns a random IRIG bit
    >>> random.seed(1)
    >>> random_bit()
    '0'
    """
    return random.choice(['0', '1', '_'])

def random_frame():
    """Generates a random, but valid, IRIG frame, in the form a bit string, 
    with marks and zeros in the correct locations. 
    >>> random.seed(1)
    >>> random_frame()
    '_00100111_100100110_011000100_000001010_010001010_011001001_000000000_000000000_011011110_101101101_'
    """

    # All bits at these indices should be marks (0, 9, 19 .. 79, 89, 99)
    mark_indices = {x for x in range(NUM_FRAME_BITS+1) if x == 0 or (x+1)%10 == 0}

    # All bits at these indices are forced zero based on IRIG protocol
    zero_indices = {5, 14, 18, 24, 27, 28, 34, 42, 43, 44, 54}
    zero_indices.update(range(60, 69))
    zero_indices.update(range(70, 79))
    zero_indices.add(99)

    bits = ''
    for i in range(NUM_FRAME_BITS):
      if i in mark_indices:
        bits += '_'
      elif i in zero_indices:
        bits += '0'
      else:
        bits += random.choice(['0','1'])

    return bits

class irigtime(datetime):
    """An irigtime is a datetime with functions for producing digital (TTL) and analog (AM) IRIG frames.

    >>> frame = irigtime(2013, 5, 25, 12, 45, 55)
    >>> frame
    irigtime(2013, 5, 25, 12, 45, 55)
    >>> frame.second
    55

    """
    @property
    def bits(self):
        """Return the bits of this IRIG frame
        >>> irigtime(2016, 7, 20, 1, 49).bits
        '_00000000_100101000_000100000_001000000_100000000_011000001_000000000_000000000_000000000_000000000_'
        """
        return self.generate_bit_str(self.second, self.minute, self.hour, self.timetuple().tm_yday, self.year)

    @property
    def digital_signal(self):
        """Returns a generator for the IRIG digital signal"""
        for bit in self.bits:
            for i in range(PULSE_WIDTH):
                yield TTL_AMP if i < BIT_WIDTH[bit] else 0

    @property
    def analog_signal(self):
        """Returns a generator for an IRIG analog signal"""
        for bit in self.digital_signal:
            wave = LARGE_WAVE if bit else SMALL_WAVE
            for x in wave:
                yield x

    @staticmethod
    def from_digital_signal(signal):
        """Creates an irigtime from an irig digital signal"""
        if (len(signal) != PULSE_WIDTH * NUM_FRAME_BITS):
            raise ValueError('signal must be a complete irig frame')

        bits = irigtime.demodulate_digital_signal(signal)

        return irigtime.from_bits(bits)

    @staticmethod
    def from_analog_signal(signal):
      pass  #TODO

    @staticmethod
    def from_bits(bits):
        """Create an irigtime from a bit string. Adds '20' to the year (years start counting from 2000)
        >>> bits = '_00010001_000100010_001000000_100100011_100000000_011000001_000000000_000000000_000000000_000000000_'
        >>> irigtime.from_bits(bits)
        irigtime(2016, 8, 26, 2, 11, 11)
        """
        second = str(int(bits[6:9], 2)) + str(int(bits[1:5], 2))
        minute = str(int(bits[15:18], 2)) + str(int(bits[10:14], 2))
        hour = str(int(bits[25:27], 2)) + str(int(bits[20:24], 2))
        day_of_year = str(int(bits[40:42], 2)) + str(int(bits[35:39], 2)) + str(int(bits[30:34], 2))
        year = '20' + str(int(bits[55:59], 2)) + str(int(bits[50:54], 2))

        # return irigtime(second, minute, hour, day_of_year, year)
        return irigtime.strptime(' '.join([year, day_of_year, hour, minute, second]), '%Y %j %H %M %S')

    @staticmethod
    def demodulate_digital_signal(signal):
        bstr = ''
        pulse_count = 0
        for x in signal:
            if x:
                pulse_count += 1
            elif pulse_count >= irigtime.BIT_WIDTH['_']:
                pulse_count = 0
                bstr += '_'
            elif pulse_count >= irigtime.BIT_WIDTH['1']:
                pulse_count = 0
                bstr += '1'
            elif pulse_count >= irigtime.BIT_WIDTH['0']:
                pulse_count = 0
                bstr += '0'
            else:
                pulse_count = 0

        return bstr
                

    @staticmethod
    def generate_bit_str(second, minute, hour, day_of_year, year):
        """Generate bit string from IRIG fields
        Years field is only two digits, eg 00-99, so we define it as
        years since 2000.
        """
        if year < 2000:
          raise ValueError('year must be >= 2000')

        # P0
        bitstring = '_'

        # Seconds
        digits = str(second).zfill(2)
        bitstring += bin(int(digits[1]))[2:].zfill(4)  # least significant digit
        bitstring += '0'
        bitstring += bin(int(digits[0]))[2:].zfill(3)  # most significant digit

        # P1
        bitstring += '_'

        # Minutes
        digits = str(minute).zfill(2)
        bitstring += bin(int(digits[1]))[2:].zfill(4)  # least significant digit
        bitstring += '0'
        bitstring += bin(int(digits[0]))[2:].zfill(3)  # most significant digit
        bitstring += '0'

        # P2
        bitstring += '_'

        # Hours
        digits = str(hour).zfill(2)
        bitstring += bin(int(digits[1]))[2:].zfill(4)  # least significant digit
        bitstring += '0'
        bitstring += bin(int(digits[0]))[2:].zfill(2)  # most significant digit
        bitstring += '0'
        bitstring += '0'

        # P3
        bitstring += '_'

        # Days
        digits = str(day_of_year).zfill(3)
        bitstring += bin(int(digits[2]))[2:].zfill(4)  # least significant digit
        bitstring += '0'
        bitstring += bin(int(digits[1]))[2:].zfill(4)  # mid significant digit

        # P4
        bitstring += '_'

        # Days (continued)
        bitstring += bin(int(digits[0]))[2:].zfill(2)  # most significant digit
        bitstring += '0'*7

        # P5
        bitstring += '_'

        # Years since 2000
        digits = str(year)[-2:]
        bitstring += bin(int(digits[1]))[2:].zfill(4)  # least significant digit
        bitstring += '0'
        bitstring += bin(int(digits[0]))[2:].zfill(4)  # most significant digit

        # P6
        bitstring += '_'

        # Control functions
        bitstring += '0'*9  # (TODO)

        # P7
        bitstring += '_'

        # Control functions (continued)
        bitstring += '0'*9  # (TODO)

        # P8
        bitstring += '_'

        # Straight Binary Seconds
        bitstring += '0'*9  # (TODO)

        # P8
        bitstring += '_'

        # Straight Binary Seconds (continued)
        bitstring += '0'*8   # (TODO)
        bitstring += '0'

        # P9
        bitstring += '_'

        return bitstring


if __name__ == '__main__':
  import doctest
  doctest.testmod()

