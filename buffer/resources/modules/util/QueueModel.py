from modules.module_model import *
from fpgaconvnet_optimiser.tools.resource_model import bram_stream_resource_model

class QueueModel:
    def __init__(self, entries, data_width):


        self.FF =


    if parameters["entries"] == 1:
      return parameters["data_width"] + 1
    else:
      return 2 * int2bits(parameters["entries"]) + 1


