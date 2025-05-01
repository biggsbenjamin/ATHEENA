import os
import sys
import numpy as np

sys.path.append('..')

from fpgaconvnet_optimiser.models.modules.ReduceMax import ReduceMax
from Data import Data

class ReduceMaxTB(Data):
    def __init__(self):
        Data.__init__(self,'reducemax')

    # update stimulus generation
    def gen_stimulus(self):
        # Init Module
        redmx = ReduceMax(
                self.param['rows'],
                self.param['cols'],
                self.param['channels']
        )
        # data in
        print("batch size:",self.param['batch_size'])
        data_in = self.gen_data([
            self.param['batch_size'],
            self.param['rows'],
            self.param['cols'],
            self.param['channels']
        ])
        # data out
        data_out = [redmx.functional_model(b) for b in data_in]
        data_out = np.asarray(data_out)
        # return data
        data = {
            'input'     : data_in.reshape(-1).tolist(),
            'output'    : data_out.reshape(-1).tolist()
        }
        # resource and latency model
        #TODO fix latency model
        model = {
            'latency'   : redmx.latency(),
            'resources' : redmx.rsc()
        }
        return data, model

if __name__ == '__main__':
    redmx_tb = ReduceMaxTB()
    redmx_tb.main(sys.argv[1:])

