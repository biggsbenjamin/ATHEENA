from fpgaconvnet_optimiser.tools.resource_model import dsp_multiplier_resource_model
from modules.module_model import *


class VectorDotFixed_model(ModuleModel):
#ToDo: separate coef modelling for overflown DSP
  def __init__(self):
    super().__init__("VectorDotFixed")

  def DSP_model(self, parameters):
    #ToDo: general DSP_multiplier model regarding data_width
    data_width = parameters["data_width"]
    fine = parameters["fine"]
    if data_width == 8:
      return 0
    elif data_width == 16:
      return min(fine, MAX_RSC["DSP"])
    elif data_width == 32:
      return min(fine * 4, MAX_RSC["DSP"])
    else:
      return fine * dsp_multiplier_resource_model(data_width, data_width)

  def FF_model(self, parameters):
    #=====Counters=====
    #if (ports_in > 1):
    ## filter_cntr => filters.bits @VectorDot.scala:30
    #else:
    ## no counter regs
    #
    if parameters["filters"] > 1:
      return int2bits(parameters["filters"])
    else: return 0

  def LUTLogic_model(self, parameters):
    data_width = parameters["data_width"]
    filters = parameters["filters"]
    fine = parameters["fine"]
    return np.array([fine, data_width])

  def LUTLogic_model_width(self, parameters):
    filters = parameters["filters"]
    fine = parameters["fine"]
    return np.array([fine, filters])

if __name__ == "__main__":

    # load model
    m = VectorDotFixed_model()

    # save coefficients
    with open("coefficients/vector_dot_lutlogic.npy", "wb") as f:
        print(m.coef)
        np.save(f, m.coef["Logic_LUT"])

    # m.get_model_performance()
