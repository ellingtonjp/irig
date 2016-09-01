from myhdl import *
from BitEncoder import BitEncoder
from FrameShiftRegister import FrameShiftRegister

def IrigTTLOutput(next_frame, frame_latched, ttl_out, enable, clk, rst):
  pulse_length = Signal(intbv(10)[8:])
  irig_bit = Signal(intbv(0)[2:])
  request = Signal(bool(0))
  inst1 = BitEncoder(irig_bit, pulse_length, request, ttl_out, enable, clk, rst)
  inst2 = FrameShiftRegister(next_frame, frame_latched, irig_bit, request, enable, clk, rst)

  return inst1, inst2
