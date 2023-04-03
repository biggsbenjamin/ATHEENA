from modules.module_model import *

class WindowFilterFixed_model(ModuleModel):

  def __init__(self):
    super().__init__("WindowFilterFixed")

  def LUTLogic_model(self, parameters):
    data_width = parameters["data_width"]
    rows = parameters["rows"]
    cols = parameters["cols"]
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]
    stride = parameters["stride"]
    return np.array([data_width, data_width*kernel_size*kernel_size, int2bits(rows), int2bits(cols), int2bits(channels), int2bits(stride), kernel_size*kernel_size])

  def LUTLogic_model_width(self, parameters):
    data_width = parameters["data_width"]
    rows = parameters["rows"]
    cols = parameters["cols"]
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]
    stride = parameters["stride"]
    return np.array([int2bits(rows), int2bits(cols), int2bits(channels), int2bits(stride), kernel_size*kernel_size])

  def LUTRAM_model(self, parameters):
    data_width = parameters["data_width"]
    kernel_size = parameters["kernel_size"]
    return np.array([data_width, kernel_size*kernel_size])

  def LUTRAM_model_width(self, parameters):
    data_width = parameters["data_width"]
    kernel_size = parameters["kernel_size"]
    return np.array([kernel_size*kernel_size])

  def FF_model(self, parameters):
    #=====Counters=====
    #if (rows > 1):
    ## row_cntr => rows.bits @SlidingWindow.scala:32
    #if (cols > 1):
    ## col_cntr => cols.bits @SlidingWindow.scala:33
    #if (channels > 1):
    ## channel_cntr => channels.bits @SlidingWindow.scala:34
    #else:
    ## no counter regs
    #
    #=====REGs=====
    # RegNext(output_ready) => 1 @SlidingWindow.scala:49 & 68
    #=====Queue===
    # depth: 2 => 2 * int2bits(2) + 1
    rows = parameters["rows"]
    cols = parameters["cols"]
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]
    rows_reg = 0
    cols_reg = 0
    channels_reg = 0
    queue_reg = 3

    if rows > 1:
      rows_reg = int2bits(rows)
    if cols > 1:
      cols_reg = int2bits(cols)
    if channels > 1:
      channels_reg = int2bits(channels)

    return kernel_size*kernel_size * queue_reg + rows_reg + cols_reg + channels_reg + 1