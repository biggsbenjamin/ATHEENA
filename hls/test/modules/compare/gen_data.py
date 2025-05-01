import os
import sys
import numpy as np

sys.path.append('..')

from fpgaconvnet_optimiser.models.modules.Compare import Compare
from Data import Data

class CompareTB(Data):
    def __init__(self):
        Data.__init__(self,'compare')

    # update stimulus generation
    def gen_stimulus(self):
        # Init Module
        cmp_fn = Compare(
                self.param['rows'], #not used in HLS but used in optimiser
                self.param['cols'],
                self.param['channels'],
                self.param['thr_val']
        )
        # data in
        data_max_in = self.gen_data([
            self.param['batch_size'],
        ])
        data_thr_in = self.gen_data([
            self.param['batch_size'],
        ])

        # data out
        data_out = cmp_fn.functional_model(data_max_in,data_thr_in)# for mx,thr in zip(data_max_in,data_thr_in)]
        #data_out = np.asarray(data_out)
        # return data
        data = {
            'input_max' : data_max_in.reshape(-1).tolist(),
            'input_thr_mul' : data_thr_in.reshape(-1).tolist(),
            'thr_val'   : [cmp_fn.threshold],
            'output'    : data_out.reshape(-1).tolist()
        }
        # resource and latency model
        #TODO needs to be fixed on optimiser side
        model = {
            'latency'   : cmp_fn.latency(),
            'resources' : cmp_fn.rsc()
        }
        return data, model

if __name__ == '__main__':
    cmp_tb = CompareTB()
    cmp_tb.main(sys.argv[1:])

