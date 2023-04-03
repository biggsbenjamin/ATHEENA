from fpgaconvnet_optimiser.tools.resource_model import bram_stream_resource_model
from modules.module_model import *
from .WindowFilterFixed_model import WindowFilterFixed_model
from modules.util.QueueBRAM_model import QueueBRAM_model

class SlidingWindowFixed_model(ModuleModel):
  def __init__(self):
    self.WindowFilterFixed = WindowFilterFixed_model()
    self.QueueBRAM = QueueBRAM_model()
    super().__init__("SlidingWindowFixed")


  def BRAM_model(self, parameters):
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]
    data_width = parameters["data_width"]
    cols = parameters["cols"]

    window_buffer = kernel_size * (kernel_size - 1) * bram_stream_resource_model(channels+1, data_width)
    line_buffer = (kernel_size - 1) * bram_stream_resource_model(cols*channels+1, data_width)

    return line_buffer + window_buffer

  def LUTLogic_model(self, parameters):

    data_width = parameters["data_width"]
    rows = parameters["rows"]
    cols = parameters["cols"]
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]
    stride = parameters["stride"]

    return np.array([
        data_width, (kernel_size-1), kernel_size*(kernel_size-1),
        (kernel_size-1)*(cols*channels+1), kernel_size*(kernel_size-1)*(channels+1),
        data_width*kernel_size*kernel_size, int2bits(rows), int2bits(cols), int2bits(channels),
        int2bits(stride), kernel_size*kernel_size, (kernel_size-1)*int2bits(rows*cols*channels),
        (kernel_size*(kernel_size-2))*int2bits(rows*cols*channels),
        kernel_size*int2bits(rows*cols*channels)])

  def LUTLogic_model_width(self, parameters):

    data_width = parameters["data_width"]
    rows = parameters["rows"]
    cols = parameters["cols"]
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]
    stride = parameters["stride"]

    return np.array([
        (kernel_size-1), kernel_size*(kernel_size-1),
        (kernel_size-1)*(cols*channels+1), kernel_size*(kernel_size-1)*(channels+1),
        kernel_size*kernel_size, int2bits(rows), int2bits(cols), int2bits(channels),
        int2bits(stride), kernel_size*kernel_size, (kernel_size-1)*int2bits(rows*cols*channels),
        (kernel_size*(kernel_size-2))*int2bits(rows*cols*channels),
        kernel_size*int2bits(rows*cols*channels)])

  def LUTRAM_model(self, parameters):
    data_width = parameters["data_width"]
    kernel_size = parameters["kernel_size"]

    return np.array([data_width, kernel_size*kernel_size])

  def LUTRAM_model_width(self, parameters):
    data_width = parameters["data_width"]
    kernel_size = parameters["kernel_size"]

    return np.array([data_width, kernel_size*kernel_size])

  # def LUTRAM_model_width(self, parameters):
  #   #return self.WindowFilterFixed.LUTRAM_model_width(parameters)
  #   kernel_size = parameters["kernel_size"]
  #   rows = parameters["rows"]
  #   cols = parameters["cols"]
  #   channels = parameters["channels"]
  #   line_buffer = kernel_size - 1
  #   window_buffer = kernel_size * (kernel_size-1)
  #   line_buffer_depth = cols*channels+1
  #   window_buffer_depth = channels+1

  #   return np.array([kernel_size*kernel_size,  line_buffer, line_buffer_depth, window_buffer, window_buffer_depth])

  def LUTSR_model(self, parameters):
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]
    return np.array([kernel_size*kernel_size, channels, kernel_size*kernel_size*channels])

  def LUTSR_model_width(self, parameters):
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]
    return np.array([kernel_size*kernel_size, channels, kernel_size*kernel_size*channels])

  def FF_model(self, parameters):
    #=====Counters=====
    #if (rows*cols*channels > 1):
    ## pixel_cntr => pixel.bits @SlidingWindow.scala:137
    #else:
    ## no counter regs
    #
    #=====REGs=====
    #frame_cache_valid => (kernel_size-1) @SlidingWindow.scala:212
    #if (channels > 1):
    ## no regs
    #else:
    ## frame_cache => (kernel_size*(kernel_size-1)) * data_width @SlidingWindow.scala:222
    #frame_cache_valid => (kernel_size*(kernel_size-1)) @SlidingWindow.scala:224
    #RegNext(window_filter_ready) => 1 @SlidingWindow.scala:238 //Synthesis merged into 1
    #RegNext(window_filter_ready) @SlidingWindow.scala:251 => merged into above
    #RegNext(frame_cache(0)(0)) => 1 @SlidingWindow.scala:259 & 263
    #RegNext(frame_cache_valid(0)(0)) => 1 @SlidingWindow.scala:260 & 264 & 278
    #ShiftRegister

    data_width = parameters["data_width"]
    rows = parameters["rows"]
    cols = parameters["cols"]
    channels = parameters["channels"]
    kernel_size = parameters["kernel_size"]

    window_filter = kernel_size*kernel_size*3 + int2bits(rows) + int2bits(cols) + int2bits(channels) + 1
    line_buffer = (kernel_size-1) * (3*int2bits(cols*channels+1) + 1)
    window_buffer = (kernel_size*(kernel_size-1)) * (3*int2bits(channels+1) + 1)

    return window_filter + line_buffer + window_buffer + \
            kernel_size-1 + (kernel_size*(kernel_size-1)) + 3 + (kernel_size*(kernel_size-1)) * data_width

if __name__ == "__main__":

    # load model
    m = SlidingWindowFixed_model()

    # save coefficients
    with open("coefficients/sliding_window_lutlogic.npy", "wb") as f:
        np.save(f, m.coef["Logic_LUT"])
    with open("coefficients/sliding_window_lutram.npy", "wb") as f:
        np.save(f, m.coef["LUT_RAM"])
    with open("coefficients/sliding_window_lutsr.npy", "wb") as f:
        np.save(f, m.coef["LUT_SR"])

