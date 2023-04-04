# import modules
import os
import shutil

import generate.layers.convolution

def gen_inner_product_layer(name,param,src_path,header_path,topless=True,wr_factor=1):
    # Edit existing params to match conv layer functionality
    flat_chans = param['rows_in']*param['cols_in']*param['channels_in']
    param['rows_in']               = 1
    param['cols_in']               = 1
    param['channels_in']           = flat_chans
    # Double checking expected output dims
    assert(param['rows_out']==1)
    assert(param['cols_out']==1)
    assert(param['channels_out']==param['filters']) # NOTE probably?
    # Add params missing from inner_product layer configuration
    param['kernel_size']    = [1,1]
    param['fine']           = 1
    param['stride']         = [1,1]
    param['pad_left']       = 0
    param['pad_right']      = 0
    param['pad_top']        = 0
    param['pad_bottom']     = 0
    param['groups']         = 1
    param['coarse_group']   = 1

    # Run generation of convolution layer
    generate.layers.convolution.gen_convolution_layer(
            name,
            param,
            src_path,
            header_path,
            topless,
            wr_factor)

    # NOTE Hope the weights/biases don't go to all hell
    return
