from modules.module_model import *

class WeightsFromStreamFixed_model(ModuleModel):
  def __init__(self):
    super().__init__("WeightsFromStreamFixed")

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
    return 0


