import math
from fpgaconvnet_optimiser.tools.resource_model import bram_stream_resource_model
from modules.module_model import *

# def isPower2(n):
#   return (n & (n-1)) == 0 and (n != 0)

class QueueBRAM_model(ModuleModel):
  def __init__(self):
    super().__init__("QueueBRAM")
    

  def FF_model(self, parameters):
    
    #=====Counters=====
    #if (entries > 1):
    ## enq_ptr => entries.bits @Decoupled.scala:219
    ## deq_ptr => entries.bits @Decoupled.scala:220
    #else:
    ## no counter regs
    #
    #=====REGs=====
    # maybe_full => 1 @Decoupled.scala:221
    # ram_io_deq_bits_MPORT_en_pipe_0 => 1
    # ram_io_deq_bits_MPORT_addr_pipe_0 => entries.bits

    return 3 * int2bits(parameters["entries"]) + 1

  def LUTLogic_model(self, parameters):
    entries = parameters["entries"]
    data_width = parameters["data_width"]
    return np.array([int2bits(entries), data_width])

  def LUTLogic_model_width(self, parameters):
    entries = parameters["entries"]
    return np.array([int2bits(entries)])

  def BRAM_model(self, parameters):
    return bram_stream_resource_model(parameters["entries"], parameters["data_width"])

  def get_BRAM(self):
    self.actual["BRAM"] = self.actual["BRAM18"] + 2*self.actual["BRAM36"]
    self.results["BRAM"] = np.array([self.BRAM_model(point) for point in self.parameters])