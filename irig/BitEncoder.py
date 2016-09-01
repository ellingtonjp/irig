from myhdl import *

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

def convert(BitEncoder):
  rst = ResetSignal(0, active=1, async=True)
  request, ttl_out, enable, clk = [Signal(bool(0)) for i in range(4)]
  pulse_length = Signal(intbv(0)[7:])
  irig_bit = Signal(intbv(0)[2:])
  toVerilog(BitEncoder, irig_bit, pulse_length, request, ttl_out, enable, clk, rst)
