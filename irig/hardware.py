from myhdl import *

def IrigTTLOutput(next_frame, frame_latched, ttl_out, enable, clk, rst):
  pulse_length = Signal(intbv(10)[8:])
  irig_bit = Signal(intbv(0)[2:])
  request = Signal(bool(0))
  inst1 = BitEncoder(irig_bit, pulse_length, request, ttl_out, enable, clk, rst)
  inst2 = FrameShiftRegister(next_frame, frame_latched, irig_bit, request, enable, clk, rst)

  return inst1, inst2


def FrameShiftRegister(irig_frame, frame_latched, irig_bit, request, enable, clk, rst):
  """ Takes an IRIG frame and shifts it out to be encoded

  The data at marker positions (0,9,19..99) is ignored, and
  a marker symbol is sent on irig_bit output.

  irig_frame     [99:0]   <input>  : 100 bit irig frame, marker indices ignored
  request                 <input>  : request next bit
  enable                  <input>  : enable bit
  frame_latched           <output> : indicates when input frame is latched
  irig_bit       [1:0]    <output> : irig symbol output, logic one or zero, or marker
  """
  NUM_BITS=100  # Number of bits per frame

  frame = Signal(intbv(0)[NUM_BITS:])
  index = Signal(intbv(0)[7:]) 

  # These two signals are used to ensure two markers
  # are sent on the very first frame
  latched_first_frame = Signal(False) 
  sent_first_marker = Signal(False)

  @always_seq(clk.posedge, reset=rst)
  def seq_logic():
    if enable:
      frame_latched.next = 0
      
      if not sent_first_marker:  # send the first marker frame
        index.next = 0  # don't advance index while we send the first marker
        if request:
          sent_first_marker.next = True

      elif not latched_first_frame:
        frame_latched.next = 1
        frame.next = irig_frame
        index.next = 0  # don't advance the index while latching the first frame
        latched_first_frame.next = True
      elif request:
        index.next = (index+1) % NUM_BITS

        if index == NUM_BITS-1:
          frame.next = irig_frame
          frame_latched.next = 1
        else:
          frame.next[NUM_BITS-2:0] = frame[NUM_BITS-1:1]
          frame.next[NUM_BITS-1] = 0

  @always_comb
  def comb_logic():
    if index == 0 or index % 10 == 9:  # marker condition
      irig_bit.next = 2
    else:
      irig_bit.next = frame[0]

  return seq_logic, comb_logic


def BitEncoder(irig_bit, pulse_length, request, ttl_out, enable, clk, rst):
  """ Takes in a bit and drives it according to an IRIG specification
  There are three encoded symbols:

    Marker:  0.8 of pulse_length
    Logic 1: 0.5 of pulse_length
    Logic 0: 0.2 of pulse_length

  irig_bit     [1:0] <input>  : 0, 1, or 2 (2 representing marker)
  enable             <input>  : enable bit
  pulse_length [7:0] <input>  : bit pulse length, in number of clock cycles
  request            <output> : goes high at the end of a bit time, indicating its time
                                for the next bit
               ___________________________________________________________
  irig_bit     X______0____X_____1_____X_____1_____X____2______X__________X
                          _           _           _           _          _
  request      |_________| |_________| |_________| |_________| |________| |
                __          _____       _____       ________    __
  ttl_out      |  |________|     |_____|     |_____|        |__|  |________
  """

  index = Signal(intbv(0)[4:])
  ttl_high = Signal(False)

  @always_comb
  def comb_logic():
    a = (irig_bit == 0 and index < pulse_length * 0.2)
    b = (irig_bit == 1 and index < pulse_length * 0.5)
    c = (irig_bit == 2 and index < pulse_length * 0.8)
    ttl_high.next = a or b or c

  @always_seq(clk.posedge, reset=rst)
  def seq_logic():
    if enable:
      index.next = (index + 1) % pulse_length

      if ttl_high:
        ttl_out.next = 1
      else:
        ttl_out.next = 0

      # Send request at end of bit
      if index == pulse_length - 1:
        request.next = 1
      else:
        request.next = 0

  return seq_logic, comb_logic


# Conversion to Verilog Functions
def convertFrameShiftRegister():
  rst = ResetSignal(0, active=1, async=True)
  request, frame_latched, enable, clk = [Signal(bool(0)) for i in range(4)]
  irig_frame = Signal(intbv(0)[NUM_BITS:])
  irig_bit = Signal(intbv(0)[2:])
  toVerilog(FrameShiftRegister, irig_frame, frame_latched, irig_bit, request, enable, clk, rst)

def convertBitEncoder():
  rst = ResetSignal(0, active=1, async=True)
  request, ttl_out, enable, clk = [Signal(bool(0)) for i in range(4)]
  pulse_length = Signal(intbv(0)[7:])
  irig_bit = Signal(intbv(0)[2:])
  toVerilog(BitEncoder, irig_bit, pulse_length, request, ttl_out, enable, clk, rst)
