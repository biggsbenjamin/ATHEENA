from modules.module_model import *
from modules.util.Queue_model import Queue_model

class WeightsToStreamFixed_model(ModuleModel):
  def __init__(self):
    self.Queue = Queue_model()
    super().__init__("WeightsToStreamFixed")
    

  def LUTLogic_model(self, parameters):
    data_width = parameters["data_width"]
    size = parameters["size"]
    fine = parameters["fine"]

    return np.array([data_width, fine, int2bits(size)])

  def LUTLogic_model_width(self, parameters):
    data_width = parameters["data_width"]
    size = parameters["size"]
    fine = parameters["fine"]

    return np.array([fine, int2bits(size)])

  def LUTRAM_model(self, parameters):
    data_width = parameters["data_width"]
    size = parameters["size"]
    fine = parameters["fine"]

    return np.array([data_width, fine, data_width*fine])

  def LUTRAM_model_width(self, parameters):
    data_width = parameters["data_width"]
    size = parameters["size"]
    fine = parameters["fine"]

    return np.array([fine])

  def FF_model(self, parameters):
    #=====Counters=====
    #if (size > 1):
    ## weights_cntr => size.bits @Weights.scala:74
    #else:
    ## no counter regs
    #
    #=====REGs=====
    # fine * Queue @Weights.scala:71
    # RegNext(stream_ready) => 1 @Weights.scala:91
    data_width = parameters["data_width"]
    size = parameters["size"]
    fine = parameters["fine"]
    queue_param = {
        "data_width": data_width,
        "entries": 2
    }
    queue = fine * self.Queue.FF_model(queue_param)
    
    if size > 1:
      return int2bits(size) + queue + 1
    else:
      return queue + 1


