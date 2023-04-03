import math
import numpy as np
from ..module_model import ModuleModel, int2bits

class AccumFixed_model(ModuleModel):
    def __init__(self):
        super().__init__("AccumFixed")

    def LUTLogic_model(self, parameters):
        #Counters = channels*c + filters*c
        #Compare = math.ceil(log(2, channels)) * c1
        #Adder = data_width * c2
        return np.array([parameters["channels"], parameters["filters"],
            parameters["data_width"], math.ceil(math.log(parameters["channels"], 2))])

    def LUTRAM_model(self, parameters):
        #SyncReadMem = filters, data_width
        return np.array([parameters["filters"], parameters["data_width"],
            parameters["filters"] * parameters["data_width"]])

    def LUTSR_model(self, parameters):
        return np.array([0])

    def LUTLogic_model_width(self, parameters):
    #Counters = channels*c + filters*c
    #Compare = math.ceil(log(2, channels)) * c1
    #Adder = data_width * c2
        return np.array([parameters["channels"], parameters["filters"],
            math.ceil(math.log(parameters["channels"], 2))])

    def LUTRAM_model_width(self, parameters):
        #SyncReadMem = filters, data_width
        return np.array([parameters["filters"]])

    def FF_model(self, parameters):
        #input_val=RegNext(io.in.bits)@Accum.scala:52 data_width * Reg
        #acc_cache=SyncReadMem(filters, gen)@Accum.scala:45 => {
        ## if filters==1, Mem synthesized as FF
        #acc_cache_acc_cache_val_addr_pipe_0 ##address pipeline register synthesized from RegNext(filter_cntr_val)@Accum.scala:131
        #[ceil(log(filters, 2)) - 1: 0] ##if MemDepth==1, no addr_reg
        #}
        #RegNext(channel_cntr_val)@Accum.scala:58, 71 => REG, REG_1 -> single reg channels_bits
        #Counter(Int){
        #if Int==1, no counter reg
        #channel_cntr  = Counter(channels) => value: channels_bits
        #filter_cntr   = Counter(filters) => value_1: filters_bits
        #}
        filters = parameters["filters"]
        channels = parameters["channels"]
        data_width = parameters["data_width"]
        if(filters==1):
            return data_width*2 + int2bits(channels)*2
        else:
            return data_width + int2bits(filters) + 2*int2bits(channels) + int2bits(filters)

if __name__ == "__main__":

    # load model
    accum = AccumFixed_model()

    # save coefficients
    with open("coefficients/accum_lutlogic.npy", "wb") as f:
        np.save(f, accum.coef["Logic_LUT"])
    with open("coefficients/accum_lutram.npy", "wb") as f:
        np.save(f, accum.coef["LUT_RAM"])

