from myhdl import *
from irig import BitEncoder

PERIOD = 1000

def bench():
  request, ttl, enable, clk, rst = [Signal(bool(0)) for i in range(5)]
  bit = Signal(intbv(0)[2:]
  pulse_length = Signal(intbv(0)[8:])

  dut = BitEncoder(bit, pulse_length, request, ttl, enable, clk, rst)

  bit_sent = Signal(intbv(0)[2:])  # shadow input so we can change whenever we like
  pulse_counter = Signal(intbv(0)[8:])

  @always(delay(PERIOD//2))
  def clkgen():
    clock.next = not clock

  @always(latched.posedge)
  def latched_bit():
    bit_sent.next = bit

  @always(clk.negedge)
  def count_pulses():
      if request: pulse_counter.next = 0
      elif ttl: pulse_counter.next = pulse_counter + 1

  @instance
  def monitor():
    while True:
      yield request.posedge  # bit was sent
      assert bit_sent in [0, 1, 2]
      if bit_sent == 0:
        assert pulse_counter == int(pulse_length * 0.2)
      elif bit_sent == 1:
        assert pulse_counter == int(pulse_length * 0.5)
      elif bit_sent == 2:
        assert pulse_counter == int(pulse_length * 0.8)

  @instance
  def stimulus():
    rst.next = bool(1)
    enable.next = bool(0)
    yield clk.negedge 
    rst.next = bool(0)
    yield clk.negedge 
    enable.next = bool(1)

    for i in range(100):
      bit = randchoice([0, 1, 2])
      yield request.posedge

    raise StopSimulation

  return dut, clkgen, latched_bit, count_pulses, monitor, stimulus

def test_bench():
  sim = Simulation(bench())
  sim.run()

if __name__ == '__main__':
  test_bench()
