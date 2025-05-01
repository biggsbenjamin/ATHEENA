"""
Exit Merge Module

For combining early exit streams with later exit streams.
The result is passed to the memory write module.
Future work will be adding more inputs OR stacking these modules for more exits.

"""

from fpgaconvnet_optimiser.models.modules import Module
import numpy as np
import math
import os
import sys
from typing import Union, List
from dataclasses import dataclass, field
from fpgaconvnet_optimiser.tools.resource_model import bram_memory_resource_model, bram_stream_resource_model,queue_lutram_resource_model,bram_array_resource_model

@dataclass
class ExitMerge(Module):
    #early_exit_edge, #edges record where batch ID comes from
    #late_exit_edge,
    #batch ID input edge?
    #ID pipeline connection
    exits: int

    def __post_init__(self):
        # load the resource model coefficients
        #NOTE using fork coeifficients until module profiled
        self.rsc_coef["LUT"] = np.load(
                os.path.join(os.path.dirname(__file__),
                "../../coefficients/fork_lut.npy"))
        self.rsc_coef["FF"] = np.load(
                os.path.join(os.path.dirname(__file__),
                "../../coefficients/fork_ff.npy"))
        self.rsc_coef["BRAM"] = np.load(
                os.path.join(os.path.dirname(__file__),
                "../../coefficients/fork_bram.npy"))
        self.rsc_coef["DSP"] = np.load(
                os.path.join(os.path.dirname(__file__),
                "../../coefficients/fork_dsp.npy"))
    def utilisation_model(self):
        #NOTE using fork utilisation until module profiled
        #FIXME make utilisation aware of potential different sizes
        return {
            "LUT"  : np.array([math.ceil(math.log(self.channels*self.rows*self.cols,2))]),
            "FF"   : np.array([math.ceil(math.log(self.channels*self.rows*self.cols,2))]),
            "DSP"  : np.array([1]),
            "BRAM" : np.array([1]),
        }

    def rsc(self,coef=None):
        # use module resource coefficients if none are given
        if coef == None:
            coef = self.rsc_coef
        # get the em  buffer BRAM estimate
        #FIXME hardcoding batch size
        em_buffer_depth = 1024*self.channels*self.rows*self.cols +8 #self.channels*self.rows*self.cols +8
        em_buffer_bram = bram_array_resource_model(em_buffer_depth, self.data_width, 'fifo')
        if em_buffer_bram == 0:
            # below vivado bram threshold, using lutram
            em_buffer_lutram = queue_lutram_resource_model(em_buffer_depth, self.data_width)
        else:
            em_buffer_lutram = 0

        # get the linear model estimation
        rsc = Module.rsc(self, coef)
        # add the bram estimation
        rsc["BRAM"] = em_buffer_bram*self.exits*2
        # return the resource usage
        rsc["LUT"] += em_buffer_lutram*self.exits*2

        # NOTE hardcoding LUT offset
        rsc["LUT"] += 2000 # for dma and exit
        rsc["LUT"] += 4000 # for interconnects
        rsc["BRAM"] += 13 # for DMA and io fifos
        return rsc

    def functional_model(self, data):
        print("trying merge fn model")
        #Exit merge is not an ONNX or pytorch op
        # check input dimensionality
        assert EEdata.shape[0] == self.rows    , "ERROR: invalid row dimension"
        assert EEdata.shape[1] == self.cols    , "ERROR: invalid column dimension"
        assert EEdata.shape[2] == self.channels, "ERROR: invalid channel dimension"

        assert LEdata.shape[0] == self.rows    , "ERROR: invalid row dimension"
        assert LEdata.shape[1] == self.cols    , "ERROR: invalid column dimension"
        assert LEdata.shape[2] == self.channels, "ERROR: invalid channel dimension"

        #temporary, testing more on the other hw side
        return data
