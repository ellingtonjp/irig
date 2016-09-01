from myhdl import *
from irig import hardware
import random

PERIOD = 1000

def bench():
  rst = ResetSignal(0, active=1, async=True)
  request, ttl, enable, clk = [Signal(bool(0)) for i in range(4)]
  bit = Signal(intbv(0)[2:])
  pulse_length = Signal(intbv(0)[8:])

  dut = hardware.BitEncoder(bit, pulse_length, request, ttl, enable, clk, rst)

  pulse_counter = Signal(intbv(0)[8:])

  @always(delay(PERIOD//2))
  def clkgen():
    clk.next = not clk

  @always(clk.negedge)
  def count_pulses():
      if request: pulse_counter.next = 0
      elif ttl: pulse_counter.next = pulse_counter + 1

  @instance
  def monitor():
    while True:
      yield request.posedge  # bit was sent
      assert bit in [0, 1, 2]
      if bit == 0:
        assert pulse_counter == int(pulse_length * 0.2)
      elif bit == 1:
        assert pulse_counter == int(pulse_length * 0.5)
      elif bit == 2:
        assert pulse_counter == int(pulse_length * 0.8)

  @instance
  def stimulus():
    rst.next = bool(1)
    enable.next = bool(0)
    yield clk.negedge 
    rst.next = bool(0)
    pulse_length.next = 10
    yield clk.negedge 
    enable.next = bool(1)

    for i in range(100):
      bit.next = random.choice([0, 1, 2])
      yield request.posedge

    raise StopSimulation

  return dut, clkgen, count_pulses, monitor, stimulus

def test_bench():
  sim = traceSignals(bench)
  sim = Simulation(sim)
  sim.run()

if __name__ == '__main__':
  test_bench()
