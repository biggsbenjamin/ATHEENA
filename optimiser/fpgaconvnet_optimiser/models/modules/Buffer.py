"""
Buffering Module

Stores intermediate compute information such as results from Conv or Pool layers.
During DSE the required size will be calculated to store intermediate results at
branching layers. The position of the buffer layer will then be moved along a
given branch until the buffer size is feasible and the latency of the exit
condition is mitigated/matched. For effective pipelining I think.

Secondary function of the buffer is to "drop" a partial calculation.
Clear a FIFO - takes X number of cycles?
Drop signal will be control signal from the Exit Condition.

Future goal will be to have buffer as an offchip memory link.
In this case, the drop might not be used.
"""

from fpgaconvnet_optimiser.models.modules import Module
import numpy as np
import math
import os
from dataclasses import dataclass, field
#NOTE using accum resource model for now
from fpgaconvnet_optimiser.tools.resource_model import bram_memory_resource_model

@dataclass
class Buffer(Module):
    ctrledge: int
    drop_mode: bool = True

    def __post_init__(self):
        self.rsc_coef["LUT"] = np.load(
                os.path.join(os.path.dirname(__file__),
                "../../coefficients/buffer_lut.npy"))
        self.rsc_coef["FF"] = np.load(
                os.path.join(os.path.dirname(__file__),
                "../../coefficients/buffer_ff.npy"))
        self.rsc_coef["BRAM"] = np.load(
                os.path.join(os.path.dirname(__file__),
                "../../coefficients/buffer_bram.npy"))
        self.rsc_coef["DSP"] = np.load(
                os.path.join(os.path.dirname(__file__),
                "../../coefficients/buffer_dsp.npy"))

    def utilisation_model(self):
        return {
            "LUT"   : np.array([self.rows,self.cols,self.channels,self.data_width]),
            "FF"    : np.array([self.rows,self.cols,self.channels,self.data_width]),
            "DSP"   : np.array([self.rows,self.cols,self.channels,self.data_width]),
            "BRAM"  : np.array([self.rows,self.cols,self.channels,self.data_width]),
        }

    def module_info(self):
        # get the base module fields
        info = Module.module_info(self)
        # add module-specific info fields
        info["ctrledge"] = self.ctrledge
        info["drop_mode"] = "true" if self.drop_mode == True else "false"
        # return the info
        return info

    def rsc(self,coef=None):
        # use module resource coefficients if none are given
        if coef == None:
            coef = self.rsc_coef
        # get the buffer buffer BRAM estimate
        # NOTE using MINIMUM functioning buffer size
        min_buff = 16
        buf_buffer_bram = bram_memory_resource_model(
                int((self.rows*self.cols*self.channels)*min_buff), self.data_width)
        # 7 series pow2
        buf_buffer_bram_pow2=int(math.pow(
            2,math.ceil(math.log2(buf_buffer_bram))))
        # separate BRAMs for buffer per coarse factor
        buf_buffer_bram = buf_buffer_bram_pow2
        # get the linear model estimation
        rsc = Module.rsc(self, coef)
        # add the bram estimation
        rsc["BRAM"] = buf_buffer_bram
        # return the resource usage
        return rsc

    def functional_model(self, data, ctrl_drop):
        # check input dimensionality
        assert data.shape[0] == self.rows    , "ERROR: invalid row dimension"
        assert data.shape[1] == self.cols    , "ERROR: invalid column dimension"
        assert data.shape[2] == self.channels, "ERROR: invalid channel dimension"

        out = np.zeros((
            self.rows,
            self.cols,
            self.channels),dtype=float)

        if self.drop_mode: #non-inverted
            if ctrl_drop == 1.0:
                return
            else:
                return data #pass through
        else: #inverted
            if not ctrl_drop == 1.0:
                return
            else:
                return data #pass through
