from modules.module_model import *
import math

def lcm(a, b):
  return abs(a*b) // math.gcd(a, b)

class SqueezeFixed_model(ModuleModel):
  def __init__(self):
    super().__init__("SqueezeFixed")
    #self.queue = Queue_model()

  # def get_decoupled_data(self):
  #   width_points = np.array([point["data_width"] for point in self.parameters])
  #   idx = {w: (width_points == w).nonzero()[0] for w in width_TYPES}
  #   for rsc in RSC_TYPES:
  #     for w in width_TYPES:
  #       for i in idx[w]:
  #         point = self.parameters[i]
  #         buffer_size = lcm(point["coarse_in"], point["coarse_out"])
  #         self.actual[rsc][i] = self.actual[rsc][i] - Queue_RSC[rsc][w] * buffer_size


  def FF_model(self, parameters):
    #=====Counters=====
    #cntr_in => 32 @Squeeze.scala:39
    #cntr_out => 32 @Squeeze.scala:40
    #if (buffer_size > 1):
    ## input_cntr => buffer_size.bits @Squeeze.scala:52
    ## output_cntr => buffer_size.bits @Squeeze.scala:53
    #else:
    ## no counter regs
    #
    #=====REGs=====
    # buffer => data_width * buffer_size @Squeeze.scala:35

    buffer_size = lcm(parameters["coarse_in"], parameters["coarse_out"])
    data_width = parameters["data_width"]
    if buffer_size > 1:
      return 2 * int2bits(buffer_size) + (data_width + 1) * buffer_size + 64
      #return (data_width + 1) * buffer_size + 64
    else :
      return data_width + 1 + 64

  def LUTLogic_model(self, parameters):
    data_width = parameters["data_width"]
    coarse_in = parameters["coarse_in"]
    coarse_out = parameters["coarse_out"]
    buffer_size = lcm(coarse_in, coarse_out)
    return np.array([data_width, coarse_in*buffer_size, coarse_out*buffer_size, buffer_size])

  def LUTLogic_model_width(self, parameters):
    data_width = parameters["data_width"]
    coarse_in = parameters["coarse_in"]
    coarse_out = parameters["coarse_out"]
    buffer_size = lcm(coarse_in, coarse_out)
    return np.array([coarse_in*buffer_size, coarse_out*buffer_size, buffer_size])

if __name__ == "__main__":

    # load model
    m = SqueezeFixed_model()

    # save coefficients
    with open("coefficients/squeeze_lutlogic.npy", "wb") as f:
        np.save(f, m.coef["Logic_LUT"])

