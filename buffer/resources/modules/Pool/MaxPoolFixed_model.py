from modules.module_model import *

class MaxPoolFixed_model(ModuleModel):
  def __init__(self):
    super().__init__("MaxPoolFixed")

  def LUTLogic_model(self, parameters):
    data_width = parameters["data_width"]
    kernel_size = parameters["kernel_size"]
    return np.array([kernel_size * kernel_size, data_width])

  def LUTLogic_model_width(self, parameters):
    #data_width = parameters["data_width"]
    kernel_size = parameters["kernel_size"]
    return np.array([kernel_size * kernel_size])

if __name__ == "__main__":

    # load model
    m = MaxPoolFixed_model()

    # save coefficients
    with open("coefficients/pool_lutlogic.npy", "wb") as f:
        np.save(f, m.coef["Logic_LUT"])

