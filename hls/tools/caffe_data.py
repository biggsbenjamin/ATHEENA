import yaml
import caffe
import sys, os, getopt
import numpy as np
from PIL import Image
import copy
from types import FunctionType
import csv
import re
import random
from fpbinary import FpBinary
import math

import tools.graphs as graphs

from tools.layer_enum import LAYER_TYPE
from tools.array_init import array_init

SCALE=256

def fixed_point(val,total_width=16,int_width=8):
    val = min(val,  2**(int_width-1))
    val = max(val, -2**(int_width-1))
    return FpBinary(int_bits=int_width,frac_bits=(total_width-int_width),signed=True,value=val)


class CaffeData:
    def __init__(self):
        # input data
        self.data_in = None
        # network
        self.net = None

    # Load net from file
    def load_net(self,model_path,weights_path):
        self.net = caffe.Classifier(model_path,weights_path)

    # Load input from file
    def load_input(self,filepath):
        self.data_in = np.array(Image.open(filepath),dtype=np.float32)

    # get type
    def get_type(self,layer):
        return self.net.layers[list(self.net._layer_names).index(layer)].type

    def gen_data(self,dim,data_range=[0,1],data_type=float):
        # Initialise random data array
        data = np.ndarray(dim,dtype=data_type)
        # assign values
        for index,_ in np.ndenumerate(data):
            data[index] = data_type(random.uniform(data_range[0],data_range[1]))
        return data

    # Run network
    def run_net(self,remove_bias=True):
        # load net input
        if len(self.data_in.shape) == 2:
            self.net.blobs['data'].data[...][0] = copy.deepcopy(np.array(self.data_in,dtype=np.float32))
        else:
            for channel in range(self.data_in.shape[2]):
                self.net.blobs['data'].data[...][0][channel] = copy.deepcopy(np.array(self.data_in[:,:,channel],dtype=np.float32))
        # remove bias term
        #print(self.net.params)
        if remove_bias:
            for layer in self.net.params:
                #print(layer, self.net.__dict__.keys())
                #print(layer, list(self.net.params.keys()).index(layer),self.get_type(layer))
                #if self.get_type(layer) == 'BatchNorm':
                #    print(self.net.params[layer][2].data)
                if len(self.net.params[layer]) != 2:
                    continue
                shape = self.net.params[layer][1].data.shape
                self.net.params[layer][1].data[...] = np.zeros(shape)
        # run network
        self.net.forward()

    def normalise(self,data,scale=SCALE):
        return np.true_divide(data,scale)
        #return np.multiply(np.subtract(np.true_divide(data,scale),0.5),2)

    def find_layer_in_net(self,layer):
        for layer_name in self.net._layer_names:
            print(layer_name,layer)
            if layer_name.replace("/","_") == layer:
                return layer_name
    
    def get_layer_bottom(self,layer):
        return self.net.bottom_names[layer][0]

    def get_layer_top(self,layer):
        return self.net.top_names[layer][0]

    def get_featuremap(self,layer):
        return self.net.blobs[layer].data[...][0]

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    DATA
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    def _convert_fixed_port_stream(self, stream_in, total_width=16, int_width=8):
        stream_out = np.ndarray(shape=stream_in.shape, dtype=FpBinary)
        for index,val in np.ndenumerate(stream_in):
            stream_out[index] = fixed_point(val,total_width=total_width,int_width=int_width)
        return stream_out

    def _fixed_point_stream_to_bin(self, stream, output_path=None, streams=1, port_width=64, ports=1):
        # check it's only a 1D array
        assert len(stream.shape) == 1
        # check the stream is fixed-point
        # TODO
        # get width of fixed point data
        data_width = sum(stream[0].format)
        # check theres enough ports for the streams
        if streams > ports*(port_width/data_width):
            raise ValueError
        # get port data type
        if   port_width == 8:
            port_type = np.uint8
        elif port_width == 16:
            port_type = np.uint16
        elif port_width == 32:
            port_type = np.uint32
        elif port_width == 64:
            port_type = np.uint64
        else:
            raise TypeError
        # get stream data type
        if   0  < data_width <= 8:
            data_type = np.uint8
        elif 8  < data_width <= 16:
            data_type = np.uint16
        elif 16 < data_width <= 32:
            data_type = np.uint32
        elif 32 < data_width <= 64:
            data_type = np.uint64
        else:
            raise TypeError
        # check streams are a factor of the stream shape
        if not stream.shape[0]%streams == 0:
            raise ValueError
        # get the size of the binary streas out
        size = int(stream.shape[0]/streams)
        # binary stream out
        bin_out = np.zeros([ports,size], dtype=port_type)
        # copy stream to binary stream out
        for i in range(size):
            for j in range(streams):
                port_index = math.floor((j*data_width)/port_width)
                stream_val = data_type( int(hex(stream[i*streams+j]),data_width) & ((2**data_width)-1) )
                bin_out[port_index][i] |= port_type( stream_val  << (data_width*j)%port_width )
        # save to binary file
        for i in range(ports):
            bin_out[i].astype(port_type).tofile(output_path+"_{i}.bin".format(i=i))
        # return binary stream
        return bin_out

    def save_featuremap(self, featuremap):
        # normalise
        featuremap = self.normalise(featuremap) # TODO: remove
        # transform featuremap
        featuremap = np.moveaxis(featuremap, 0, -1)
        # save featuremap information
        data = {
            "rows"      : featuremap.shape[0],
            "cols"      : featuremap.shape[1],
            "channels"  : featuremap.shape[2],
            "data"      : featuremap.reshape(-1).tolist()
        }
        # return feature map data
        return data

    def save_featuremap_layer(self, partition_info, layer, output_path=None, to_yaml=False, to_bin=False, to_csv=False):
        # check layer is in network
        #print(layer)
        #for layer in self.net.blobs:
        #    print(layer)
        assert layer in self.net.blobs
        # check the layer has the correct dimensions
        if len(self.net.blobs[layer].data[...][0].shape) != 3:
           raise ValueError("Wrong feature map dimensions")
        # get feature map
        featuremap = self.get_featuremap(layer)
        # get featuremap information
        data = self.save_featuremap(featuremap)
        # save feature map if there's an output path
        if output_path:
            # yaml format
            if to_yaml:
                # save to yaml file
                with open(output_path+'.yaml', 'w') as f:
                    yaml.dump(data, f)
            # binary format
            if to_bin:
                # get feature map stream
                stream = self._convert_fixed_port_stream(np.array(data['data']))
                # save to binary file
                self._fixed_point_stream_to_bin(stream, output_path=output_path) # TODO: add port info
            # csv format
            if to_csv:
                pass
        return data

    def save_featuremaps_partition(self, partition_info, output_path=None, to_bin=False, to_csv=False):
        # store data for each layer
        data = {}
        # iterate over layers in partition
        for layer in partition_info['layer_info']:
            # update output path for layer
            output_path_layer = None
            if output_path:
                output_path_layer = os.path.join(output_path,layer.replace("/","_"))
            # save feature map of that layer
            data[layer] = self.save_featuremap_layer(partition_info,layer,
                output_path=output_path_layer,to_yaml=False,to_bin=to_bin,to_csv=to_csv)
        # yaml format
        if output_path and to_yaml:
            # save to yaml file
            with open(os.path.join(output_path,'data.yaml'), 'w') as f:
                yaml.dump(data, f)

    def save_featuremap_in_out(self, partition_info, output_path=None, to_bin=False, to_csv=False):
        # input layer
        input_node = partition_info['partition_info']['input_node']
        if partition_info['layer_info'][input_node]['type'] == 'SQUEEZE':
            input_node = partition_info['graph'][input_node][0]
        input_layer = self.get_layer_bottom(input_node)
        output_path_layer = None
        if output_path:
            output_path_layer = os.path.join(output_path,input_layer.replace("/","_"))
        input_data = self.save_featuremap_layer(partition_info, input_layer, output_path=output_path_layer, 
                to_yaml=False, to_bin=to_bin, to_csv=to_csv)
        # output layer
        output_node = partition_info['partition_info']['output_node']
        if partition_info['layer_info'][output_node]['type'] == 'SQUEEZE':
            output_node = graphs.get_graph_inv(partition_info['graph'])[output_node][0]
        output_layer = self.get_layer_top(output_node)
        output_path_layer = None
        if output_path:
            output_path_layer = os.path.join(output_path,output_layer.replace("/","_"))
        output_data = self.save_featuremap_layer(partition_info, output_layer, output_path=output_path_layer, 
                to_yaml=False, to_bin=to_bin, to_csv=to_csv)
        # save data
        data = {
            partition_info['partition_info']['input_node'].replace("/","_")  : input_data,
            partition_info['partition_info']['output_node'].replace("/","_") : output_data
        }
        # yaml format
        if output_path:
            # save to yaml file
            with open(os.path.join(output_path,'data.yaml'), 'w') as f:
                yaml.dump(data, f)

    def save_all_featuremaps(self, partition_info, output_path=None, to_yaml=False, to_bin=False, to_csv=False):
        # data
        data = {}
        # iterate over each layer
        for layer in self.net.blobs:
            if len(self.net.blobs[layer].data[...][0].shape) != 3:
               continue
            # update output path for layer
            output_path_layer = None
            if output_path:
                output_path_layer = os.path.join(output_path,layer.replace("/","_"))
            # save feature map of that layer
            data[layer] = self.save_featuremap_layer(partition_info,layer,
                output_path=output_path_layer,to_yaml=False,to_bin=to_bin,to_csv=to_csv)
        # yaml format
        if output_path and to_yaml:
            # save to yaml file
            with open(os.path.join(output_path,'data.yaml'), 'w') as f:
                yaml.dump(data, f)

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    WEIGHTS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    def _transform_weights(self,weights_raw,wr_factor=1,coarse_in=1,coarse_out=1):
        # parameters
        num_filters  = int(weights_raw.shape[0]/(coarse_out*wr_factor))
        num_channels = int(weights_raw.shape[1]/coarse_in)
        k_size       = weights_raw.shape[2]
        # correct output shape for weights
        weights = np.ndarray(
            shape=(
                wr_factor,
                coarse_in,
                coarse_out,
                num_channels,
                num_filters,
                k_size,k_size),dtype=float,order='C')
        # transform weights raw shape
        for index,_ in np.ndenumerate(weights):
            weights[index] = weights_raw[
                      index[4]*wr_factor*coarse_out+index[0]*coarse_out+index[2],
                      index[3]*coarse_in+index[1],
                      index[5],
                      index[6]]
        # merge channel and filter dimensions
        weights = np.reshape(weights,[wr_factor,coarse_in,coarse_out,num_channels*num_filters,k_size,k_size])
        # remove last two dimensions if kernel size is 1
        if k_size == 1:
            weights = weights[:,:,:,:,0,0]
        # return transformed weights
        return weights

    def get_weights_convolution(self, layer_info, layer, wr_factor=1):
        # get weights
        weights_raw = self.net.params[layer][0].data
        # transform parameters
        coarse_in   = layer_info['coarse_in']
        coarse_out  = layer_info['coarse_out']
        # return transformed weights
        return self._transform_weights(weights_raw,wr_factor,coarse_in,coarse_out)

    def get_weights_inner_product(self, layer_info, layer, wr_factor=1):
        # get weights
        weights_raw = self.net.params[layer][0].data
        # transform parameters
        coarse_in   = layer_info['coarse_in']
        coarse_out  = layer_info['coarse_out']
        filters     = layer_info['filters']
        channels    = layer_info['channels']
        rows        = layer_info['rows']
        cols        = layer_info['cols']
        #reshape for transforming
        weights_raw = np.reshape(weights_raw,(filters,channels,rows,cols))
        weights_raw = np.rollaxis(weights_raw,1,3)
        weights_raw = np.reshape(weights_raw,(filters,rows*cols*channels,1,1))
        # return transformed weights
        return self._transform_weights(weights_raw,wr_factor,coarse_in,coarse_out)

    def save_weights_layer(self,layer_info,layer,wr_factor=1,output_path=None,to_yaml=False,to_bin=False,to_csv=False):
        # get layer type
        layer_type = layer_info['type']
        # get transformed weights
        if   layer_type == "CONVOLUTION":
            transformed_weights = self.get_weights_convolution(layer_info, layer, wr_factor=wr_factor)
        elif layer_type == "INNER_PRODUCT":
            transformed_weights = self.get_weights_inner_product(layer_info, layer, wr_factor=wr_factor)
        else:
            raise TypeError
        # save weights
        if output_path:
            # csv format
            if to_csv:
                # iterate over weights reloading factor
                for weights_reloading_index in range(wr_factor):
                    # get filepath name
                    filepath = '{path}_{index}.csv'.format(path=output_path,index=weights_reloading_index)
                    # save to csv file
                    with open(filepath, 'w') as f:
                        f.write(array_init(transformed_weights[weights_reloading_index]))
            # bin format
            if to_bin:
                # iterate over weights reloading factor
                for weights_reloading_index in range(wr_factor):
                    weights_stream =  self._convert_fixed_port_stream(transformed_weights[weights_reloading_index].reshape(-1), total_width=16, int_width=8)
                    self._fixed_point_stream_to_bin(weights_stream, output_path=output_path+"_"+str(weights_reloading_index), streams=1, port_width=64, ports=1)
        # return transformed weights
        return transformed_weights

    def save_weights_partition(self,partition_info,output_path=None,to_yaml=False,to_bin=False,to_csv=False):
        weights = {}
        # iterate over layers in network
        for layer in self.net.params:
            # skip weights outside of partition
            if not layer.replace("/","_") in partition_info['layer_info']:
                continue
            # check if layer has weights
            if partition_info['layer_info'][layer.replace("/","_")]['type'] in ["CONVOLUTION","INNER_PRODUCT"]:
                # get weights reloading factor
                if layer.replace("/","_") == partition_info['partition_info']['weights_reloading_layer']:
                    wr_factor = partition_info['partition_info']['weights_reloading_factor']
                else:
                    wr_factor = 1
                # get output path
                output_path_layer = None
                if output_path:
                    output_path_layer = os.path.join(output_path,"{layer}_weights".format(layer=layer.replace("/","_")))
                # get layer info
                layer_info = partition_info['layer_info'][layer.replace("/","_")]
                weights[layer.replace("/","_")] =  self.save_weights_layer(layer_info,layer,wr_factor=wr_factor,
                        output_path=output_path_layer,to_bin=to_bin,to_csv=to_csv)
        # yaml format
        if to_yaml:
            tmp = {}
            for layer in weights:
                tmp[layer] = weights[layer].reshape(-1).tolist()
            # save to yaml file
            with open(os.path.join(output_path,'weights.yaml'), 'w') as f:
                yaml.dump(tmp, f)
        # return weights
        return weights

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    WEIGHTS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    def save_batch_norm(self,node_info,output_path):
        # weights
        scale = {}
        shift = {}
        # iterate over each layer
        for node in node_info:
            if node_info[node]['type'] != LAYER_TYPE.BatchNorm:
               continue
            # scale layer
            scale_layer = node_info['hw'].scale_layer
            # get parameters
            mean  = self.net.params[layer][0].data
            var   = self.net.params[layer][1].data
            gamma = self.net.params[scale_layer][0].data
            beta  = self.net.params[scale_layer][1].data
            eps   = np.float_power(10,-5)
            # transform to 2 operations
            scale[node] = gamma / np.sqrt( var + eps )
            shift[node] = ( beta / scale[node] - mean )

        if output_path:
            # save scale coeffients
            with open(output_path + '/scale.yaml', 'w') as f:
                yaml.dump(scale, f)
            # save shift coeffients
            with open(output_path + '/shift.yaml', 'w') as f:
                yaml.dump(shift, f)

        return scale, shift

    def transform_batch_norm_coef(self,coef_raw,coarse=1):
        # parameters
        num_channels = int(coef_raw.shape[0]/coarse)

        # correct output shape for weights
        coef = np.ndarray(
            shape=(
                coarse,
                num_channels),dtype=float,order='C')

        # transform weights raw shape
        for index,_ in np.ndenumerate(coef):
            coef[index] = coef_raw[index[1]*coarse+index[0]]
            #coef[index] = coef_raw[index[0]*num_channels+index[1]]

        return coef

    def save_batch_norm_csv(self,output_path,net_info):
        # find layers with weights
        for layer in self.net.params:
            if self.get_type(layer) == 'BatchNorm':
                layer_index = list(self.net.params.keys()).index(layer)
                next_layer  = list(self.net.params.keys())[layer_index+1]
                mean  = self.net.params[layer][0].data
                var   = self.net.params[layer][1].data
                gamma = self.net.params[next_layer][0].data
                beta  = self.net.params[next_layer][1].data

                print(layer)

                eps = np.float_power(10,-5)
                # get coarse factor
                try:
                    coarse_in  = net_info[layer]['coarse_in']
                except KeyError:
                    coarse_in  = 1

                # channels
                num_channels = int(self.net.params[layer][0].shape[0]/coarse_in)

                # scale
                scale = np.ndarray([
                    num_channels,
                    coarse_in
                ],dtype=float)
                for index,_ in np.ndenumerate(scale):
                    i = index[0]*coarse_in+index[1]
                    scale[index] = gamma[i]/np.sqrt(var[i]+eps)
                # scale
                offset = np.ndarray([
                    num_channels,
                    coarse_in
                ],dtype=float)
                for index,_ in np.ndenumerate(offset):
                    i = index[0]*coarse_in+index[1]
                    offset[index] = beta[i] - mean[i]*gamma[i]/np.sqrt(var[i]+eps)
                # save csv
                filepath = '{path}/{layer}_scale.csv'.format( path=output_path,layer=layer.replace("/","_") )
                with open(filepath, 'w') as writeFile:
                    writer = csv.writer(writeFile)
                    writer.writerows([scale.reshape(-1).tolist()])
                filepath = '{path}/{layer}_offset.csv'.format( path=output_path,layer=layer.replace("/","_") )
                with open(filepath, 'w') as writeFile:
                    writer = csv.writer(writeFile)
                    writer.writerows([offset.reshape(-1).tolist()])

if __name__ == "__main__":
    caffe_data = CaffeData()
    caffe_data.load_net(
        'data/models/lenet.prototxt',
        'data/weights/lenet.caffemodel'
    )
    caffe_data.load_input(
        #'data/imagenet_0_vgg.jpg'
        'data/inputs/lenet_0.png'
    )
    print('run ...')
    caffe_data.run_net()
    print('save data ...')
    #caffe_data.save_data('.')
    print('save weight ...')
    #caffe_data.save_weight('.')
    print('save weight csv ...')
    #caffe_data.save_weight_csv('.',{})
