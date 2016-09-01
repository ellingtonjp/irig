from myhdl import *
from irig import hardware, utilities
import random

PERIOD = 1000

def bench():
  rst = ResetSignal(0, active=1, async=True)
  request = Signal(bool(0))
  frame_latched, enable, clk = [Signal(bool(0)) for i in range(3)]
  irig_bit = Signal(intbv(0)[2:])
  irig_frame = Signal(intbv(0)[100:])

  dut = hardware.FrameShiftRegister(irig_frame, frame_latched, irig_bit, request, enable, clk, rst)
  frame = Signal(intbv(0)[100:])

  @always(delay(PERIOD//2))
  def clkgen():
    clk.next = not clk

  @always(clk.negedge)
  def get_frame():
    if frame_latched:
      frame.next = irig_frame

  @always(clk.negedge)
  def reqgen():
    request.next = not request

  @instance
  def monitor():
    index = 0 
    counting = False

    while True:
      yield clk.negedge

      if enable and not rst:
        if frame_latched:
          counting = True # only start counting once first frame is latched
          index = 0
        elif request and counting:
          index += 1

        if index == 0 or index % 10 == 9:
          assert irig_bit == 2
        else:

          print(irig_bit, frame, index, frame[index])
          assert irig_bit == frame[index]

  @instance
  def stimulus():
    rst.next = bool(1)
    enable.next = bool(0)
    yield clk.negedge 
    rst.next = bool(0)

    frame = utilities.random_frame().replace('_','0')
    irig_frame.next = int(frame, 2)

    yield clk.negedge 
    enable.next = bool(1)

    num_frames = 10
    for i in range(num_frames): 
      yield frame_latched.negedge  # wait til frame is latched before changing it
      frame = utilities.random_frame().replace('_','0')
      irig_frame.next = int(frame, 2)

    raise StopSimulation

  return dut, clkgen, reqgen, get_frame, monitor, stimulus

def test_bench():
  sim = traceSignals(bench)
  sim = Simulation(sim)
  sim.run()

if __name__ == '__main__':
  test_bench()
