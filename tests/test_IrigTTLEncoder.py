from myhdl import *
from irig import hardware, utilities
import random

PERIOD = 1000

def bench(num_bits):
  rst = ResetSignal(0, active=1, async=True)
  frame_latched, ttl_out, enable, clk = [Signal(bool(0)) for i in range(4)]
  next_frame = Signal(intbv(0)[num_bits:])

  dut = hardware.IrigTTLEncoder(next_frame, frame_latched, ttl_out, enable, clk, rst, num_bits=num_bits)
  frame = Signal(intbv(0)[num_bits:])

  @always(delay(PERIOD//2))
  def clkgen():
    clk.next = not clk

  @always(clk.negedge)
  def get_frame():
    if frame_latched:
      frame.next = next_frame

  @instance
  def pulse_counter():
    while True:
      yield ttl_out.posedge
      pulse_count = 0 

      yield clk.negedge
      while ttl_out:
        pulse_count += 1
        yield clk.negedge

  @instance
  def monitor():
    while True:
      yield clk.negedge

      if enable and not rst:
        if frame_latched:
          index = 0
        elif request:
          index += 1

        if index == 0 or index % 10 == 9:
          assert irig_bit == 2
        else:
          assert irig_bit == frame[index]

  @instance
  def stimulus():
    rst.next = bool(1)
    enable.next = bool(0)
    yield clk.negedge 
    rst.next = bool(0)

    frame = utilities.random_frame(num_bits).replace('_','0')
    next_frame.next = int(frame, 2)

    yield clk.negedge 
    enable.next = bool(1)

    num_frames = 10
    for i in range(num_frames): 
      yield frame_latched.negedge  # wait til frame is latched before changing it
      frame = utilities.random_frame(num_bits).replace('_','0')
      next_frame.next = int(frame, 2)

    raise StopSimulation

  return dut, clkgen, get_frame, pulse_counter, stimulus

def test_bench_100bits():
  # sim = traceSignals(bench, num_bits=100)
  # sim = Simulation(sim)
  sim = Simulation(bench, num_bits=100)
  sim.run()

def test_bench_60bits():
  # sim = traceSignals(bench, num_bits=60)
  # sim = Simulation(sim)
  sim = Simulation(bench, num_bits=60)
  sim.run()

if __name__ == '__main__':
  # Visual test for IRIG-H
  PERIOD=100000000
  sim = traceSignals(bench, num_bits=60)
  sim = Simulation(sim)
  sim.run()

