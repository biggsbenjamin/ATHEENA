import os
import sys

sys.path.append('..')

from fpgaconvnet_optimiser.models.modules.Exponential import Exponential
from Data import Data

class ExponenTB(Data):
    def __init__(self):
        Data.__init__(self,'exponen')

    # update stimulus generation
    def gen_stimulus(self):
        # Init Module
        exponen = Exponential(
                self.param['rows'],
                self.param['cols'],
                self.param['channels']
        )
        # data in
        data_in = self.gen_data([
            self.param['rows'],
            self.param['cols'],
            self.param['channels']
        ])
        # data out
        data_out = exponen.functional_model(data_in)
        # return data
        data = {
            'input'     : data_in.reshape(-1).tolist(),
            'output'    : data_out.reshape(-1).tolist()
        }
        # resource and latency model
        model = {
            'latency'   : exponen.latency(),
            'resources' : exponen.rsc()
        }
        return data, model

if __name__ == '__main__':
    exponen_tb = ExponenTB()
    exponen_tb.main(sys.argv[1:])

