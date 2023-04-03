from modules.module_model import *


class Queue_model(ModuleModel):
  def __init__(self):
    super().__init__("Queue")
    

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
    #if (entries == 1):
    ## ram => data_width @Decoupled.scala:218
    #else:
    ## no ram regs
    if parameters["entries"] == 1:
      return parameters["data_width"] + 1
    else:
      return 2 * int2bits(parameters["entries"]) + 1

  def LUTLogic_model(self, parameters):
    entries = parameters["entries"]
    data_width = parameters["data_width"]
    return np.array([int2bits(entries), data_width])

  def LUTLogic_model_width(self, parameters):
    entries = parameters["entries"]
    return np.array([int2bits(entries), 1])

  def LUTRAM_model(self, parameters):
    data_width = parameters["data_width"]
    entries = parameters["entries"]
    return np.array([data_width, entries])

  def LUTRAM_model_width(self, parameters):
    data_width = parameters["data_width"]
    entries = parameters["entries"]
    return np.array([entries, 1])