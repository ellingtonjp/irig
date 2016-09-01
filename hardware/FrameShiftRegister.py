from myhdl import *

NUM_BITS = 100

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

def convert(BitEncoder):
  rst = ResetSignal(0, active=1, async=True)
  request, frame_latched, enable, clk = [Signal(bool(0)) for i in range(4)]
  irig_frame = Signal(intbv(0)[100:])
  irig_bit = Signal(intbv(0)[2:])
  toVerilog(FrameShiftRegister, irig_frame, frame_latched, irig_bit, request, enable, clk, rst)
