from myhdl import *

def IrigTTLEncoder(next_frame, frame_latched, ttl_out, enable, clk, rst, num_bits=100):
  """ Takes an IRIG frame and encodes it based on IRIG TTL encoding.

  The data at marker positions (0,9,19..99) is ignored, and
  a marker symbol is sent on irig_bit output. In all other cases, the 
  corresponding bit value (0 or 1) is encoded and sent out ttl_out output.

  For timecodes D and H, next_frame should only be 60 bits wide, all other
  timecodes are 100 bits.

  Properties for various time codes:

    Timecode    num_bits     clk
      A           100       10  kHz
      B           100       1   kHz
      D           60        1/6 Hz
      E           100       100 Hz
      G           100       100 kHz
      H           60        10  Hz

  Ports
    irig_frame  [num_bits:0] <input>  : 100 or 60 bit irig frame to be encoded
    frame_latched            <output> : indicates when input frame is latched, and ready for next frame
    ttl_out                  <output> : encoded irig ttl output
    enable                   <input>  : enable bit

  Parameters
    num_bits  : number of bits in the IRIG frame

  Waves:
                  _____________________________________________________________
    irig_frame    _X___________X___________X___________X___________X__________X
                   _           _           _           _           _          _
    frame_latched | |_________| |_________| |_________| |_________| |________| |_
                  
  Notice the input IRIG frame data changes shortly after posedge of the latched bit.
  Follow this example to ensure the correct data is latched (we don't want input
  data changing while the module is latching the input).
  """
  # pulse_length = Signal(intbv(10)[8:])  # Each IRIG bit will take 10 clock cycles
  irig_bit = Signal(intbv(0)[2:])
  request = Signal(bool(0))
  inst1 = BitEncoder(irig_bit, request, ttl_out, enable, clk, rst)
  inst2 = FrameShiftRegister(next_frame, frame_latched, irig_bit, request, enable, clk, rst, num_bits)

  return inst1, inst2


def FrameShiftRegister(irig_frame, frame_latched, irig_bit, request, enable, clk, rst, num_bits=100):
  """ Takes an IRIG frame and shifts it out to be encoded

  The data at marker positions (0,9,19..99) is ignored, and
  a marker symbol is sent on irig_bit output.

  Ports
    irig_frame [num_bits:0] <input>  : irig frame, marker indices ignored
    request                 <input>  : request next bit
    enable                  <input>  : enable bit
    frame_latched           <output> : indicates when input frame is latched
    irig_bit   [1:0]        <output> : irig symbol output, logic one or zero, or marker

  Parameters
    num_bits  : number of bits per frame
  """

  frame = Signal(intbv(0)[num_bits:])
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
        index.next = (index+1) % num_bits

        if index == num_bits-1:
          frame.next = irig_frame
          frame_latched.next = 1
        else:
          frame.next[num_bits-2:0] = frame[num_bits-1:1]
          frame.next[num_bits-1] = 0

  @always_comb
  def comb_logic():
    if index == 0 or index % 10 == 9:  # marker condition
      irig_bit.next = 2
    else:
      irig_bit.next = frame[0]

  return seq_logic, comb_logic


def BitEncoder(irig_bit, request, ttl_out, enable, clk, rst, pulse_length=10):
  """ Takes in a bit and drives it according to an IRIG specification
  There are three encoded symbols:

    Marker:  0.8 of pulse_length
    Logic 1: 0.5 of pulse_length
    Logic 0: 0.2 of pulse_length

  Ports:
    irig_bit     [1:0] <input>  : 0, 1, or 2 (2 representing marker)
    enable             <input>  : enable bit
    request            <output> : goes high at the end of a bit time, indicating its time
                                  for the next bit
  Parameters
    pulse_length       <input>  : bit pulse length, in number of clock cycles
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
  num_bits=100
  rst = ResetSignal(0, active=1, async=True)
  request, frame_latched, enable, clk = [Signal(bool(0)) for i in range(4)]
  irig_frame = Signal(intbv(0)[num_bits:])  # assume 100 bits
  irig_bit = Signal(intbv(0)[2:])
  toVerilog(FrameShiftRegister, irig_frame, frame_latched, irig_bit, request, enable, clk, rst, num_bits=num_bits)

def convertBitEncoder():
  rst = ResetSignal(0, active=1, async=True)
  request, ttl_out, enable, clk = [Signal(bool(0)) for i in range(4)]
  pulse_length = Signal(intbv(0)[7:])
  irig_bit = Signal(intbv(0)[2:])
  toVerilog(BitEncoder, irig_bit, request, ttl_out, enable, clk, rst)
