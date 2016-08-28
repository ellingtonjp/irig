from myhdl import *

def BitEncoder(bit, pulse_length, request, ttl, enable, clk, rst):
  """ Takes in a bit and drives it according to an IRIG specification
  There are three encoded symbols:

    Marker:  0.8 of a bit time
    Logic 1: 0.5 of a bit time
    Logic 0: 0.2 of a bit time

  bit        [1:0]   <input>  : 0, 1, or 2 (2 representing marker)
  enable             <input>  : enable bit
  pulse_length [7:0] <input>  : bit pulse length, in number of clock cycles
  request            <output> : goes high at the end of a bit time, indicating its time
                                for the next bit
  latched            <output> : goes high when the input bit is latched, indicating which
                                data value is used for encoding
          ___________________________________________________________
  bit     X______0____X_____1_____X_____1_____X____2______X__________X
                     _           _           _           _          _
  request |_________| |_________| |_________| |_________| |________| |
            _           _           _           _           _
  latched _| |_________| |_________| |_________| |_________| |_______
           __          _____       _____       ________    __
  ttl   ..|  |________|     |_____|     |_____|        |__|  |________
  """

  @instance
  def logic():

    while True:
      yield clk.posedge, rst.posedge

      if reset or not enable:  # TODO: see how this gets converted to verilog
        ttl.next = bool(0)
        latched.next = bool(0)
        request.next = bool(0)
      else:


