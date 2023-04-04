import yaml
import sys, os, getopt
import numpy as np
from PIL import Image, ImageOps
import copy
from types import FunctionType
import csv
import re
import random
from fpbinary import FpBinary
import math

import onnx
import onnxruntime
import onnx.numpy_helper

import torch
import torchvision.transforms.functional as TF

import fpgaconvnet_optimiser.tools.graphs as graphs
import fpgaconvnet_optimiser.tools.layer_enum as layer_enum
from fpgaconvnet_optimiser.tools.layer_enum import LAYER_TYPE
import fpgaconvnet_optimiser.tools.onnx_helper as onnx_helper
import fpgaconvnet_optimiser.proto.fpgaconvnet_pb2 as fpgaconvnet_pb2
from fpgaconvnet_optimiser.tools.layer_enum \
        import from_proto_layer_type

try:
    from tools.array_init import array_init
except ModuleNotFoundError:
    from array_init import array_init

SCALE=256

def fixed_point(val,total_width=16,int_width=8):
    val = min(val,  2**(int_width-1))
    val = max(val, -2**(int_width-1))
    return FpBinary(int_bits=int_width,frac_bits=(total_width-int_width),signed=True,value=val)

def get_layer_from_partition(partition, layer_name): # Non ONNXData class version
    for layer in partition.layers:
        if layer.name == layer_name:
            return layer
    raise NameError("layer name not in partition")

def gen_layer_name(layer): # layer in protobuf form
    #macro issue is that layers that have numerical names cause compiler to error
    layer_type_str = str(fpgaconvnet_pb2.layer.layer_type.Name(layer.type))
    if layer.name.isnumeric(): # preprend with type to avoid macro issue
        return f'{layer_type_str}{layer.name}'
    else:
        return layer.name

#FIXME not actually fixed point
def bin_to_fixed_point(filename, data_width=16, int_width=8, ee_flag=False):

    def _get_np_type(data_width):
        if   0  < data_width <= 8:
            data_type = np.uint8
        elif 8  < data_width <= 16:
            data_type = np.uint16
        elif 16 < data_width <= 32:
            data_type = np.uint32
        elif 32 < data_width <= 64:
            data_type = np.uint64
        else:
            raise typeerror
        return data_type

    #get numpy data type from width
    data_type = _get_np_type(data_width)
    if ee_flag:
        print("EE flag triggered")
        data_type = _get_np_type(data_width*2)

    #import the file
    bin_in = np.fromfile(filename, dtype=data_type)

    if ee_flag:
        samp_id_bin = np.right_shift(bin_in,data_width)
        samp_id_bin.astype( _get_np_type(data_width) )

        samp_dat_bin = np.bitwise_and(bin_in, 0xffff)
        samp_dat_bin.astype( _get_np_type(data_width) )

        #TODO pull number of classes from user info
        class_num = 10
        samp_id_bin = samp_id_bin.reshape((-1,class_num))
        #checking samples all have same batch id thru output
        for samp in samp_id_bin:
            if not np.all(samp == samp[0]):
                raise ValueError(f"Sample ID mismatch in check bin. ID:{samp}")

        samp_dat_bin = samp_dat_bin.reshape((-1,class_num))

        # {ID: {"early_exit":T/F, "result": [0 .. class_num]}, ... }
        result_dict = {}
        le_tracker = [] #NOTE put all the out of order ones in this bin? works for small batches
        prev_id = -1
        for id_num_arr, samp_res in zip(samp_id_bin,samp_dat_bin):
            id_num = id_num_arr[0] #NOTE verified that they are the same

            # FIXME method for telling if EE or LE
            #print("CURRENT ID NUM:",id_num, "PREV ID:", prev_id)
            #ee_res_flag=True
            #if id_num in le_tracker:
            #    ee_res_flag=False
            #else:
            #    if prev_id+1 < id_num:
            #        # out of order
            #        ooo_ids = [i for i in range(prev_id+1,id_num)]
            #        le_tracker = le_tracker + ooo_ids
            #        print("RANGE:", ooo_ids)
            #    prev_id = id_num
            #print("New le tracker:", le_tracker)
            ## {"early_exit":T/F, "result": [0 .. class_num]}
            #samp_dict = {"early_exit":ee_res_flag, "output": samp_res}
            #result_dict[id_num] = samp_dict

            result_dict[id_num] = samp_res

        return result_dict

        #return samp_dat_bin

    #TODO convert to fixed point with integer component of width int_width
    #TODO maybe convert to floating point?
    #for b in bin_in:
    #    print(b)

    # FIXME baseline stripped back version (no sample ID, deprecating)
    return bin_in

def validate_output(args):
    print(args.gold_path)
    #get fixed point tolerance
    errtol = fixed_point(args.error_tolerance, args.data_width) #TODO add int_width
    print(f"Error tolerance as fxpbin: {errtol}, as uint: {errtol.bits_to_signed()}")
    #load golden data, convert to float
    g_dat_list = []
    for gp in args.gold_path:
        g_dat = bin_to_fixed_point(gp, args.data_width, ee_flag=args.early_exit)
        g_dat_list.append(g_dat)
    #load actual data, convert to float
    a_dat = bin_to_fixed_point(args.actual_path, args.data_width, ee_flag=args.early_exit)
    #compare values, check length, compute average error
    if len(g_dat) != len(a_dat):
        raise ValueError(f"Data length differs! Expected: {len(g_dat)} Actual: {len(a_dat)}")

    def make_signed(value, datawidth):
        if value > 2**(datawidth-1)-1:
            return value-(2**datawidth)
        return value

    def make_signed_16(value):
        if value > 2**(16-1)-1:
            return value-(2**16)
        return value


    #TODO make this a user defined input or something
    class_num = 10

    max_err=0.0
    err_tot=0

    # TODO warnings based on binary difference, errors based on classif difference
    EE_cnt=0
    LE_cnt=0
    for samp_id in g_dat_list[0].keys():
        # compare the values for now

        for idx,(g0,g1,a) in enumerate(zip( g_dat_list[0][samp_id],
                                            g_dat_list[1][samp_id],
                                            a_dat[samp_id])):

            sg0=make_signed(g0,args.data_width)
            sg1=make_signed(g1,args.data_width)

            sa=make_signed(a,args.data_width)

            cmpr0 = (sg0-sa) if (sg0 > sa) else (sa-sg0)
            cmpr1 = (sg1-sa) if (sg1 > sa) else (sa-sg1)

            #max_err = max(max_err,cmpr)

        #make the values signed for easier reading
        s16_f = np.vectorize(make_signed_16)
        eegdat = s16_f(g_dat_list[0][samp_id])
        legdat = s16_f(g_dat_list[1][samp_id])
        adat = s16_f(a_dat[samp_id])

        if cmpr0 > errtol.bits_to_signed() and cmpr1 > errtol.bits_to_signed():
            print(f"ERROR: Difference greater than tolerance.\n \
                            Values g0:{sg0} g1:{sg1} a:{sa} @ sample:{samp_id}, index:{idx}")
            err_tot+=1
        elif cmpr0 > errtol.bits_to_signed():
            #if np.exp(max(eegdat)) >= (sum(np.exp(eegdat))*0.996):
            #    print("Should be early exit!")
            #print(f"EE error so assuming LE Sample ID:{samp_id}\n \
            #        EEgdat:\t{eegdat}\n \
            #        adat:\t{adat},\n \
            #        LEgdat:\t{legdat}")
            LE_cnt+=1
            max_err = max(max_err,cmpr1)
        elif cmpr1 > errtol.bits_to_signed():
            max_err = max(max_err,cmpr0)
            EE_cnt+=1
        else:
            print("ERROR TOO LOW BETWEEN EXITS")
            ee_diff = np.linalg.norm((eegdat - adat))
            le_diff = np.linalg.norm((legdat - adat))
            if ee_diff < le_diff:
                EE_cnt += 1
            else:
                LE_cnt += 1


        #NOTE printing stuff for debug etc.
        if args.verbose:
            print(f"Signed gold0:{sg0}, gold1:{sg1}, signed actual:{sa}")
            print(f"\tcompare var: {cmpr}, error total:{err_tot}")

    print("Num EE:{} LE:{}".format(EE_cnt, LE_cnt))

    # NOTE old version compares everything - any value difference
    #for idx,(g,a) in enumerate(zip(g_dat, a_dat)):
    #    #print("bin repr g: ",np.binary_repr(g,width=32), "bin repr a: ",np.binary_repr(a,width=32))

    #    sg=make_signed(g,args.data_width)
    #    sa=make_signed(a,args.data_width)
    #    cmpr = (sg-sa) if (sg > sa) else (sa-sg)
    #    max_err = max(max_err,cmpr)
    #    if cmpr > errtol.bits_to_signed():
    #        #print(f"ERROR: Difference greater than tolerance.\n \
    #        #        Values g:{sg} a:{sa} @ index:{idx}")
    #        err_tot+=1
    #    #NOTE printing stuff for debug etc.
    #    if args.verbose:
    #        print(f"Signed gold:{sg}, signed actual:{sa}")
    #        print(f"\tcompare var: {cmpr}, error total:{err_tot}")

    err_p = (max_err)/errtol.bits_to_signed()
    raw_err_mx = err_p*args.error_tolerance
    if err_tot == 0:
        print("Made it to end with no errors exceeding tolerance! YAY")
    else:
        print("Error count total:",err_tot)

    print("(Maximum error was ~{:.2f}% of tolerance, ~{:.5f})".format(100*err_p, raw_err_mx))
    print("ee flag:", args.early_exit)

class ONNXData:
    def __init__(self, partition, model_path=None):
        # partitions
        self.partition = partition
        self.model = None
        if model_path:
            # model
            self.model = onnx_helper.load(model_path)
            self.model = onnx_helper.update_batch_size(self.model,self.partition.batch_size)
            # merge subgraphs into main graph
            self.merge_subgraphs()
            # add intermediate layers to outputs
            new_outputs=[]
            for node in self.model.graph.node:
                og_VIP = onnx_helper.get_ValueInfoProto_from_node(self.model.graph,node)
                VIP = onnx.ValueInfoProto()
                VIP.CopyFrom(og_VIP)
                # FIXME temporarily ignoring 'ReduceMax' op because onnx_helper broken
                if node.op_type in ['ReduceMax', 'Greater', 'Cast']:
                    print("found control operation, ignore output")
                else:
                    new_outputs.append(VIP)
            # add input aswell to output
            input_VIP = onnx.ValueInfoProto()
            input_VIP.CopyFrom(self.model.graph.input[0])
            new_outputs.append(input_VIP)
            # extending model with intermediate outputs
            self.model.graph.output.extend(new_outputs)
            # remove bias FIXME what is this doing again???
            self.remove_initializer_from_input()
            self.remove_bias()
            # need to do EE VERSION to get all the other outputs
            self.model = onnx_helper.update_batch_size(self.model,
                    self.partition.batch_size, ee_flag=True)
            # verify model is onnx compliant after changes
            onnx.checker.check_model(self.model)
            # inference session
            self.sess = onnxruntime.InferenceSession(self.model.SerializeToString())
            # get input data
            self.input_name  = self.sess.get_inputs()[0].name
            self.input_shape = self.sess.get_inputs()[0].shape
            # get output data
            self.output_name  = self.sess.get_outputs()[0].name
            self.output_shape = self.sess.get_outputs()[0].shape
            # create random data input
            self.data = np.random.uniform(0,1,self.input_shape).astype(np.float32)
            onnx.save(self.model, "./TMP_ONNX_MODEL_bs4.onnx")

    def load_input(self,filepath):
        self.data = np.array(Image.open(filepath),dtype=np.float32)
        #"normalising", more like scaling, input to prevent saturation of quant data types
        data_max = np.amax(self.data)
        self.data = self.data / data_max
        if len(self.data.shape) == 2:
            self.data = np.expand_dims(self.data,axis=0)
        self.data = np.stack([self.data for _ in range(self.partition.batch_size)], axis=0 )

    #TODO version of load input that takes in folder full of images, maybe randomised
    def load_inputs(self,filepath):
        img_ls = os.listdir(filepath)
        img_ls.sort()

        np_ls=[]
        for s in range(self.partition.batch_size):
            current_path = os.path.join(filepath,img_ls[s])
            # load in the numpy array
            #img = np.array(Image.open(current_path),dtype=np.float32)
            img = np.load(current_path)
            # scale images
            data_max = np.amax(img)
            img = img / data_max
            if len(img.shape) == 2:
                img = np.expand_dims(img,axis=0)
            np_ls.append(img)
        self.data = np.concatenate(np_ls, axis=0 )
        print("Input data shape:",self.data.shape)

    def get_layer(self,layer_name):
        for layer in self.partition.layers:
            if layer.name == layer_name:
                return layer

    def get_type(self,layer):
        return self.net.layers[list(self.net._layer_names).index(layer)].type

    def gen_data(self,dim,data_range=[0,1],data_type=float):
        # Initialise random data array
        data = np.ndarray(dim,dtype=data_type)
        # assign values
        for index,_ in np.ndenumerate(data):
            data[index] = data_type(random.uniform(data_range[0],data_range[1]))
        return data

    def normalise(self,data,scale=SCALE):
        return np.true_divide(data,scale)
        #return np.multiply(np.subtract(np.true_divide(data,scale),0.5),2)

    def remove_initializer_from_input(self):
        inputs = self.model.graph.input
        name_to_input = {}
        for input in inputs:
            name_to_input[input.name] = input
        for initializer in self.model.graph.initializer:
            if initializer.name in name_to_input:
                inputs.remove(name_to_input[initializer.name])

    def remove_bias(self):
        for layer in self.partition.layers:
            if layer.bias_path and layer.parameters.has_bias==0:
                initializer = onnx_helper.get_model_initializer(self.model, layer.bias_path, to_tensor=False)
                # TODO: seems like theres no bias initializer for inner product layer
                if not initializer:
                    continue
                zeroes = np.zeros(onnx.numpy_helper.to_array(initializer).shape).astype(np.float32)
                initializer_new = onnx.numpy_helper.from_array(zeroes,name=initializer.name)
                self.model.graph.initializer.remove(initializer)
                self.model.graph.initializer.extend([initializer_new])

    def merge_subgraphs(self):
        #try and merge the subgraph nodes into the main graph nodes
        subnodes=[]
        valinfs=[]
        ifnode_idxs=[]
        #outputs=[]
        for idx,node in enumerate(self.model.graph.node):
            #expand subgraphs
            name = onnx_helper._name(node)
            if layer_enum.from_onnx_op_type(node.op_type) == LAYER_TYPE.If:
                for subgraph in node.attribute:
                    for og_node in subgraph.g.node:
                        # copy VIP information to new class
                        og_VIP = onnx_helper.get_ValueInfoProto_from_node(subgraph.g,og_node)
                        #print(og_VIP)
                        #raise NameError
                        VIP = onnx.ValueInfoProto()
                        VIP.CopyFrom(og_VIP)
                        # copy node information
                        new_node = onnx.NodeProto()
                        new_node.CopyFrom(og_node)
                        # build lists of fields from sub-graphs
                        subnodes.append(new_node)
                        valinfs.append(VIP)
                # append ifnode index for removal
                ifnode_idxs.append(idx)
                #remove exit associated with the ifnode
                for op in self.model.graph.output:
                    if op.name == node.output[0]:
                        self.model.graph.output.remove(op)

        #extend main graph
        self.model.graph.node.extend(subnodes)
        self.model.graph.value_info.extend(valinfs)
        #remove ifnodes
        for idx in reversed(ifnode_idxs):
            self.model.graph.node.pop(idx)

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

    def _fixed_point_stream_format(self, stream, streams=1, port_width=16, ports=1,
            batch_flag=False,batch_num_width=8, sample_size=1):
        print(f"batch flag:{batch_flag}")
        # check it's only a 1D array
        assert len(stream.shape) == 1
        # check the stream is fixed-point
        # TODO
        # get width of fixed point data
        data_width = sum(stream[0].format)
        # check theres enough ports for the streams
        if streams > ports*(port_width/data_width):
            print(f"streams:{streams} ports:{ports} pw:{port_width} dw:{data_width}")
            raise ValueError

        ##### batch id things #####
        tot_data_width = data_width + batch_num_width
        # get stream data type
        if   0  < tot_data_width <= 8:
            tot_data_type = np.uint8
        elif 8  < tot_data_width <= 16:
            tot_data_type = np.uint16
        elif 16 < tot_data_width <= 32:
            tot_data_type = np.uint32
        elif 32 < tot_data_width <= 64:
            tot_data_type = np.uint64
        else:
            raise TypeError
        ##### batch id things #####

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
        # get the size of the binary streams out
        size = int(stream.shape[0]/streams)
        # binary stream out
        bin_out = np.zeros([ports,size], dtype=port_type)
        if not batch_flag:
            # copy stream to binary stream out
            for i in range(size):
                for j in range(streams):
                    port_index = math.floor((j*data_width)/port_width)
                    # print(stream[i*streams+j].bits_to_signed() & ((2**data_width)-1), data_type(stream[i*streams+j].bits_to_signed()))
                    stream_val = tot_data_type( stream[i*streams+j].bits_to_signed() & ((2**data_width)-1) )
                    bin_out[port_index][i] |= port_type( stream_val  << (data_width*j)%port_width )
            # return the formatted stream
            return bin_out
        else:
            batch_id=0
            # copy stream to binary stream out
            for i in range(size):
                for j in range(streams): # streams = 1 in my case
                    #format is portwidth[31:0];
                    #portwidth[31:16] = batchid[15:0];
                    #portwidth[15:0] = data[15:0];

                    port_index = math.floor((j*tot_data_width)/port_width) # the port you're assigning the data to (always 0 in my case)
                    #print(stream[i*streams+j].bits_to_signed() & ((2**data_width)-1), data_type(stream[i*streams+j].bits_to_signed()))
                    batchid_val = data_type( batch_id )
                    stream_val = data_type( stream[i*streams+j].bits_to_signed() & ((2**data_width)-1) )
                    bin_out[port_index][i] |= port_type( batchid_val  << 16 )
                    bin_out[port_index][i] |= port_type( stream_val  << 0 ) #<< (data_width*j)%port_width )
                if (i+1) % sample_size == 0:
                    batch_id+=1
            # return the formatted stream
            return bin_out

    def _fixed_point_stream_to_bin(self, stream, output_path, streams=1, port_width=64, ports=1,
            batch_flag=False, batch_num_width=8, sample_size=1):
        # get the formatted_stream
        bin_out = self._fixed_point_stream_format(stream, streams=streams, port_width=port_width, ports=ports,
                batch_flag=batch_flag, batch_num_width=batch_num_width, sample_size=sample_size)
        # get the port type
        port_type = bin_out.dtype
        # save to binary file
        for i in range(ports):
            bin_out[i].astype(port_type).tofile(f"{output_path}_{i}.bin".format(i=i))

    def _fixed_point_stream_to_dat(self, stream, output_path, streams=1, port_width=64, ports=1,
            batch_flag=False, batch_num_width=8, sample_size=1):
        # get the formatted_stream
        bin_out = self._fixed_point_stream_format(stream, streams=streams, port_width=port_width, ports=ports,
                batch_flag=batch_flag, batch_num_width=batch_num_width, sample_size=sample_size)
        # save to binary file
        for i in range(ports):
            with open(f"{output_path}_{i}.dat", 'w') as f:
                f.write("\n".join([str(j) for j in bin_out[i]]))

    def transform_featuremap(self, featuremap):
        # normalise
        #featuremap = self.normalise(featuremap) # TODO: remove
        # transform featuremap
        if featuremap.ndim == 1:
            return featuremap
        return np.moveaxis(featuremap, 1, -1)
        # TODO: handle 1D and 2D featuremaps

    def save_featuremap(self, featuremap, output_path, sample_size=1, parallel_streams=1, to_yaml=False, to_bin=False, to_csv=False, to_dat=False):
        # yaml format
        if to_yaml:
            # save to yaml file
            with open(output_path+'.yaml', 'w') as f:
                print("fm shape:",featuremap.shape)
                yaml.dump({
                    "batch_size": featuremap.shape[0],
                    "rows"      : featuremap.shape[1],
                    "cols"      : featuremap.shape[2],
                    "channels"  : featuremap.shape[3],
                    "data"      : featuremap.reshape(-1).tolist() }, f)
        # get feature map stream
        # NOTE THIS MAKES IT 16 bit fixed point
        stream = self._convert_fixed_port_stream(featuremap.reshape(-1))
        # binary format
        if to_bin:
            print("WARNING: port width set to 32 bits for bin, adding batchnum")
            self._fixed_point_stream_to_bin(stream, output_path, streams=parallel_streams, port_width=32,
                    batch_flag=True, batch_num_width=16, sample_size=sample_size)
        # dat format
        if to_dat:
            print("WARNING: port width set to 32 bits for dat, adding batchnum")
            self._fixed_point_stream_to_dat(stream, output_path, streams=parallel_streams, port_width=32,
                    batch_flag=True, batch_num_width=16, sample_size=sample_size)
        # csv format
        if to_csv:
            pass

    def save_featuremap_in_out(self, output_path, to_bin=False, to_csv=False, to_dat=False):
        # save input layer
        input_node = self.partition.input_node
        input_data = np.array( self.sess.run([input_node], { self.input_name : self.data } )[0] )
        input_data = self.transform_featuremap(input_data)
        input_streams = int(self.partition.layers[0].parameters.coarse_in)
        #FIXME allow input to be have more parallelism
        assert input_streams == 1,\
                "ERROR: Input stream is not coarse=1!\
                (in save_featuremap_in_out)"
        self.save_featuremap(input_data,
                os.path.join(output_path,
                    onnx_helper._format_name(input_node) ),
            sample_size=784,
            parallel_streams=input_streams,
            to_yaml=False,to_bin=to_bin,
            to_csv=to_csv, to_dat=to_dat)
        # save output layer
        output_node = self.partition.output_node

        def _get_available_onnx_op(check_node, output_node_list):
            avoid_types = [ LAYER_TYPE.If,
                            LAYER_TYPE.Buffer,
                            LAYER_TYPE.Split,
                            LAYER_TYPE.Greater,
                            LAYER_TYPE.Squeeze]
            #find the layer to get the type, if its NOT in avoid_layers then RETURN that layer name
            for idx,lyr in enumerate(self.partition.layers):
                if lyr.name == check_node:
                    ltype = from_proto_layer_type(self.partition.layers[idx].type)
                    if ltype in avoid_types:
                        # WE HAVE TO GO DEEPER
                        #tmp_name=[]
                        for ip_node in lyr.node_in:
                            _get_available_onnx_op(ip_node, output_node_list)
                    else:
                        # WE DUG TOO GREEDILY AND TOO DEEP
                        output_node_list.append(lyr.name)
                        return
        exit_list=[]
        _get_available_onnx_op(output_node, exit_list)
        print("exit list:", exit_list)
        #print("attempting to run sesh")
        output_data_list = []
        for ex in exit_list:
            #output_data = np.array( self.sess.run([output_node], { self.input_name : self.data } )[0], dtype=np.float64) #making sure data type works
            ex_int = ''.join(c for c in ex if c.isdigit())
            try:
                op_data_tmp = np.array( self.sess.run([ex_int],
                    { self.input_name : self.data } )[0],
                    dtype=np.float64)
            except onnxruntime.capi.onnxruntime_pybind11_state.InvalidArgument:
                # onnx is stupid and removes TRAILING zeroes... sometimes
                ex_int = str( int(ex_int)*10 )
                #print("new ex_int:",ex_int)
                op_data_tmp = np.array( self.sess.run([ex_int],
                    { self.input_name : self.data } )[0],
                    dtype=np.float64)
            # store exits in list for post proc
            output_data_list.append(op_data_tmp)
        #print("sesh is run, now trying transform fm")

        #output_data = self.transform_featuremap(output_data)
        od_list=[]
        for od in output_data_list:
            od_tmp = self.transform_featuremap(od)
            od_list.append(od_tmp)
        #print("Output tensor:\n",output_data)

        output_streams = int(
                self.partition.layers[-1].parameters.coarse_out)
        #FIXME allow output to be have more parallelism
        assert output_streams == 1,\
                "ERROR: Output stream is not coarse=1!\
                (in save_featuremap_in_out)"

        for idx,(node,data) in enumerate(zip(exit_list, od_list)):
            self.save_featuremap(
                    data,
                    os.path.join(output_path,
                        f"OUTPUT{idx}_"+str(onnx_helper._format_name(node)) ),
                    sample_size=10,
                    parallel_streams=output_streams,
                    to_yaml=False, to_bin=to_bin,
                    to_csv=to_csv, to_dat=to_dat)

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    WEIGHTS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    @staticmethod
    def _transform_weights(weights_raw,wr_factor,coarse_in,coarse_out,coarse_group,groups):
        # parameters
        num_filters  = int(weights_raw.shape[0]/(groups*coarse_out*wr_factor))
        num_channels = int(weights_raw.shape[1]/coarse_in)
        k_size_x       = weights_raw.shape[2]
        k_size_y       = weights_raw.shape[3]
        # correct output shape for weights
        weights = np.ndarray(
            shape=(
                wr_factor,
                coarse_group,
                coarse_in,
                coarse_out,
                int(groups/coarse_group),
                num_channels,
                num_filters,
                k_size_x,k_size_y),dtype=float,order='C')

        # transform weights raw shape
        for index,_ in np.ndenumerate(weights):
            weights[index] = weights_raw[
                      index[4]*coarse_group*num_filters*wr_factor*coarse_out+index[1]*num_filters*wr_factor*coarse_out+index[6]*wr_factor*coarse_out+index[0]*coarse_out+index[3],
                      index[5]*coarse_in+index[2],
                      index[7],
                      index[8]]
        # merge channel and filter dimensions
        weights = np.reshape(weights,[wr_factor,coarse_in*coarse_group,coarse_out,int(groups/coarse_group)*num_channels*num_filters,k_size_x,k_size_y])
        # return transformed weights
        return weights

    def get_weights_convolution(self, layer, wr_factor=1):
        # get weights
        if self.model:
            weights_raw = onnx_helper.get_model_initializer(self.model, layer.weights_path)
        else:
            print(f"WARNING: no initializer found for {layer.name}, creating a random initializer")
            dim = [layer.parameters.filters*wr_factor,
                int(layer.parameters.channels_in / layer.parameters.groups),
                layer.parameters.kernel_size[0],
                layer.parameters.kernel_size[1]]

            # Initialise random data array
            weights_raw = np.ndarray(dim,dtype=float)
            # assign values
            for index,_ in np.ndenumerate(weights_raw):
                weights_raw[index] = random.uniform(-8, 8) #todo: consistent with weight_t

        # transform parameters
        coarse_in   = layer.parameters.coarse_in
        coarse_out  = layer.parameters.coarse_out
        coarse_group  = layer.parameters.coarse_group
        groups = layer.parameters.groups
        # return transformed weights
        return self._transform_weights(weights_raw,wr_factor,coarse_in,coarse_out,coarse_group,groups)

    def get_weights_inner_product(self, layer, wr_factor=1):
        # get weights
        weights_raw = onnx_helper.get_model_initializer(self.model, layer.weights_path)
        #print("weights reshape: ",weights_raw.shape)
        #print("HAS BIAS",layer.parameters.has_bias)
        if not (layer.parameters.has_bias == 1):
        #if layer.parameters.matmul_flag:
            print("MatMul ONNX Operation used, transposing")
            weights_raw = np.matrix.transpose(weights_raw)
            print("weights transpose: ",weights_raw.shape)
        # transform parameters
        coarse_in   = layer.parameters.coarse_in
        coarse_out  = layer.parameters.coarse_out
        filters     = layer.parameters.filters
        channels    = layer.parameters.channels_in
        rows        = layer.parameters.rows_in
        cols        = layer.parameters.cols_in
        #reshape for transforming
        weights_raw = np.reshape(weights_raw,(filters*wr_factor,channels,rows,cols))
        #print("weights reshape: ",weights_raw.shape)
        weights_raw = np.rollaxis(weights_raw,1,4) #input filters need to be FINAL axis
        #print("weights rollaxis: ",weights_raw.shape)
        weights_raw = np.reshape(weights_raw,(filters*wr_factor,rows*cols*channels,1,1))
        #print("weights reshape2: ",weights_raw.shape)
        # return transformed weights
        return self._transform_weights(weights_raw,wr_factor,coarse_in,coarse_out,1,1)

    def save_weights_layer(self,layer,wr_factor=1,output_path=None,to_yaml=False,to_bin=False,to_csv=False,to_dat=False):
        # get transformed weights
        if layer_enum.from_proto_layer_type(layer.type) == layer_enum.LAYER_TYPE.Convolution:
            transformed_weights = self.get_weights_convolution(layer, wr_factor=wr_factor)
        elif layer_enum.from_proto_layer_type(layer.type) == layer_enum.LAYER_TYPE.InnerProduct:
            transformed_weights = self.get_weights_inner_product(layer, wr_factor=wr_factor)
        else:
            raise TypeError
        # save weights
        if output_path:
            # csv format
            if to_csv:
                # iterate over weights reloading factor
                for weights_reloading_index in range(wr_factor):
                    # get filepath name
                    filepath = f'{output_path}_{weights_reloading_index}.csv'
                    # save to csv file
                    with open(filepath, 'w') as f:
                        f.write(array_init(transformed_weights[weights_reloading_index]))
            # get the bitwidth for the weights
            bitwidth = layer.parameters.weight_width
            # flatten the weights for binary and data formats
            weights_stream =  self._convert_fixed_port_stream(transformed_weights.reshape(-1), total_width=bitwidth, int_width=bitwidth//2)
            # bin format
            if to_bin:
                self._fixed_point_stream_to_bin(weights_stream, output_path=output_path, streams=1, port_width=64, ports=1)
            # dat format
            if to_dat:
                self._fixed_point_stream_to_dat(weights_stream, output_path=output_path, streams=1, port_width=64, ports=1)
        # return transformed weights
        return transformed_weights

    def save_weights_partition(self,output_path,to_yaml=False,to_bin=False,to_csv=False,to_dat=False):

        def _fix_identifier(name):
            if name[0].isdigit():
                return "n" + name
            else:
                return name
        weights = {}
        # iterate over layers in network
        for layer in self.partition.layers:
            layer_type_str = str(fpgaconvnet_pb2.layer.layer_type.Name(layer.type)) # REQUIRED EDIT
            layer_name = gen_layer_name(layer) # REQUIRED EDIT
            # skip weights outside of partition
            if layer_enum.from_proto_layer_type(layer.type) in [ layer_enum.LAYER_TYPE.Convolution, layer_enum.LAYER_TYPE.InnerProduct ]:
                # get weights reloading factor
                if layer.name == self.partition.weights_reloading_layer:
                    wr_factor = self.partition.weights_reloading_factor
                else:
                    wr_factor = 1
                # get output path
                output_path_layer = None
                if output_path:
                    layer_identifier = _fix_identifier(layer.name)
                    output_path_layer = os.path.join(output_path,f"{layer_identifier}_weights")
                # get layer info
                weights[layer.name] = self.save_weights_layer(layer,wr_factor=wr_factor,
                        output_path=output_path_layer,to_bin=to_bin,to_csv=to_csv,to_dat=to_dat)
        return weights

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    BIASES
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    @staticmethod
    def _transform_biases(biases_raw, filters, coarse_out,wr_factor=1):
        # parameters
        if wr_factor == -1:
            num_filters  = biases_raw.shape[0]//(coarse_out)
            biases = np.ndarray(
                shape=(
                    coarse_out,
                    num_filters
                    ), dtype=float, order='C')#order is row major

            # transform biases raw shape
            for index,_ in np.ndenumerate(biases):
                biases[index] = biases_raw[coarse_out*index[1]+index[0]]
        else:
            num_filters  = biases_raw.shape[0]//(coarse_out*wr_factor)
            biases = np.ndarray(
                shape=(
                    wr_factor,
                    coarse_out,
                    num_filters
                    ), dtype=float, order='C')#order is row major

            # transform biases raw shape
            for index,_ in np.ndenumerate(biases):
                biases[index] = biases_raw[coarse_out*wr_factor*index[2]+index[1]+index[0]]

        # return transformed biases
        return biases

    def get_biases_convolution(self, layer, wr_factor=-1):
        # get biases
        if self.model:
            biases_raw = onnx_helper.get_model_initializer(self.model, layer.bias_path)
        else:
            print(f"WARNING: no initializer found for {layer.name}")
            #, creating a random initializer") # FIXME - see get weights conv

        # transform parameters
        coarse_out  = layer.parameters.coarse_out
        filters = layer.parameters.filters
        # return transformed biases
        return self._transform_biases(biases_raw,filters,coarse_out,wr_factor)

    def get_biases_inner_product(self, layer,wr_factor=-1):
        # get biases
        biases_raw = onnx_helper.get_model_initializer(self.model, layer.bias_path)
        # transform parameters
        coarse_out  = layer.parameters.coarse_out
        filters     = layer.parameters.filters
        channels    = layer.parameters.channels_in
        rows        = layer.parameters.rows_in
        cols        = layer.parameters.cols_in
        return self._transform_biases(biases_raw,filters,coarse_out,wr_factor)

    def save_biases_layer(self,layer,wr_factor=-1,output_path=None,to_yaml=False,to_bin=False,to_csv=False,
                            to_dat=False):
        # get transformed biases
        if layer_enum.from_proto_layer_type(layer.type) == layer_enum.LAYER_TYPE.Convolution:
            transformed_biases = self.get_biases_convolution(layer,wr_factor)
        elif layer_enum.from_proto_layer_type(layer.type) == layer_enum.LAYER_TYPE.InnerProduct:
            transformed_biases = self.get_biases_inner_product(layer,wr_factor)
        else:
            raise TypeError
        # save biases
        if output_path:
            # csv format
            if to_csv:
                # get filepath name
                filepath = f'{output_path}.csv'
                # save to csv file
                with open(filepath, 'w') as f:
                    f.write(array_init(transformed_biases))

            # get the bitwidth for the biases
            bitwidth = layer.parameters.biases_width
            # flatten the biases for binary and data formats
            biases_stream =  self._convert_fixed_port_stream(transformed_biases.reshape(-1), total_width=bitwidth, int_width=bitwidth//2)
            # bin format
            if to_bin:
                self._fixed_point_stream_to_bin(biases_stream, output_path=output_path, streams=1, port_width=64, ports=1)
            # dat format
            if to_dat:
                self._fixed_point_stream_to_dat(biases_stream, output_path=output_path, streams=1, port_width=64, ports=1)
        # return transformed biases
        return transformed_biases
    def save_biases_partition(self,output_path,to_yaml=False,to_bin=False,to_csv=False,
                                to_dat=False):

        def _fix_identifier(name):
            if name[0].isdigit():
                return "n" + name
            else:
                return name
        biases = {}
        # iterate over layers in network
        for layer in self.partition.layers: # skip biases outside of partition
            layer_type_str = str(fpgaconvnet_pb2.layer.layer_type.Name(layer.type)) # REQUIRED EDIT
            layer_name = gen_layer_name(layer) # REQUIRED EDIT
            if layer_enum.from_proto_layer_type(layer.type) in \
                    [ layer_enum.LAYER_TYPE.Convolution, layer_enum.LAYER_TYPE.InnerProduct ]:
                # get weights reloading factor
                if layer.name == self.partition.weights_reloading_layer:
                    wr_factor = self.partition.weights_reloading_factor
                else:
                    wr_factor = -1
                # get output path
                output_path_layer = None
                if output_path:
                    layer_identifier = _fix_identifier(layer.name)
                    output_path_layer = os.path.join(output_path,f"{layer_identifier}_biases")
                if layer.parameters.has_bias: # skip layers with no bias
                    # get layer info
                    biases[layer.name] = self.save_biases_layer(layer,wr_factor,
                                                                output_path=output_path_layer,
                                                                to_bin=to_bin,to_csv=to_csv,
                                                                to_dat=to_dat)
        return biases

if __name__ == "__main__":
    bin_to_fixed_point()
