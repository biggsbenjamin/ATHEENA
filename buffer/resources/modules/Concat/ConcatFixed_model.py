
import re
from modules.module_model import *
import numpy as np

def get_scala_list(s):
    pat = r'.*?\((.*)\).*'
    string = re.search(pat, s).group(1)
    l = string.split(",")
    return [int(i) for i in l]
  
  
class ConcatFixed_model(ModuleModel):
  def __init__(self):
    super().__init__("ConcatFixed")

  
  def FF_model(self, parameters):
    #=====Counters=====
    #if (ports_in = 1):
    ## no counter regs
    #else:
    ## port_cntr => ports_in.bits @Concat.scala:28
    ## channel_cntr => channels.max.bits @Concat.scala:29
    #
    #=====REGs=====
    #io.out.bits => data_width @Concat.scala:58
    #io.out.valid => 1 @Concat.scala:59
    ports_in = parameters["ports_in"]
    if isinstance(parameters["channels"], str):
      try: 
        channels_max = max(get_scala_list(parameters["channels"]))
      except:
        print("\"channels\" parameter must be of the format \"List(1,2,...,n)\"")
    else:
      try:
        channels_max = max(parameters["channels"])
      except TypeError:
        print("\"channels\" parameter must be list of int")
        
    data_width = parameters["data_width"]
    if ports_in > 1:
      return int2bits(ports_in) + int2bits(channels_max) + data_width + 1
    else:
      return data_width + 1

  def LUTLogic_model(self, parameters):
    if isinstance(parameters["channels"], str):
      try: 
        channels_max = max(get_scala_list(parameters["channels"]))
      except:
        print("\"channels\" parameter must be of the format \"List(1,2,...,n)\"")
    else:
      try:
        channels_max = max(parameters["channels"])
      except TypeError:
        print("\"channels\" parameter must be list of int")
    ports_in = parameters["ports_in"]
    data_width = parameters["data_width"]
    return np.array([ports_in, channels_max, int2bits(ports_in), int2bits(channels_max), data_width])

  def LUTLogic_model_width(self, parameters):
    if isinstance(parameters["channels"], str):
      try: 
        channels_max = max(get_scala_list(parameters["channels"]))
      except:
        print("\"channels\" parameter must be of the format \"List(1,2,...,n)\"")
    else:
      try:
        channels_max = max(parameters["channels"])
      except TypeError:
        print("\"channels\" parameter must be list of int")
    ports_in = parameters["ports_in"]
    # data_width = parameters["data_width"]
    return np.array([ports_in, channels_max, int2bits(ports_in), int2bits(channels_max)])