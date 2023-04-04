import sys
import parser
import argparse
import json
import numpy as np
import os
from google.protobuf import json_format
import fpgaconvnet_optimiser.proto.fpgaconvnet_pb2
from onnx_data import gen_layer_name, get_layer_from_partition
from host_code_template import *
from fpgaconvnet_optimiser.tools.layer_enum import LAYER_TYPE
from fpgaconvnet_optimiser.tools.layer_enum \
        import from_proto_layer_type

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

########################################################
################ Split HW Gen Functions ################
########################################################

def gen_host_code(args, prt):
    # Returns some sort of automated generation of host code
    # (required manual integration with sdk)
    print("PLEASE NOTE: HOST CODE REQUIRES MANUAL INTEGRATION WITH VIVADO SDK")
    net = args.network_name

    layer_names = get_layers(args, prt)
    # add the top layer
    layer_names.insert(0, net)
    hc_layers = []
    lyr_inc=""
    lyr_cfg=""
    lyr_inits=""
    lyr_strts=""
    top = LayerHostCode(net, 0, net)
    for idx,l in enumerate(layer_names):
        num=idx
        Lyr = LayerHostCode(l,num,net)
        lyr_inc     +=  Lyr.get_include()
        lyr_cfg     +=  Lyr.get_code_handlers()
        lyr_inits   +=  Lyr.get_layer_inits()
        lyr_strts   +=  Lyr.get_layer_starts()

    # TODO get these sizes from partition info
    input_size=784
    output_size=10
    data_type='uint32_t'
    batch_size = prt.batch_size

    hc = hc_template.format(includes        =lyr_inc,
                            config_pntrs    =lyr_cfg,
                            input_size      =input_size,
                            output_size     =output_size,
                            batch_size      =batch_size,
                            layer_inits     =lyr_inits,
                            layer_starts    =lyr_strts,
                            data_type       =data_type)

    # TODO save the host code to partition
    pth = args.json_path # might as well put it here
    pth = os.path.abspath(pth)
    pth = os.path.dirname(pth)
    op_pth = os.path.join(pth, f"{net}_host_code.c")
    #write...
    with open(op_pth,'w') as f:
        f.write(hc)

# Returns the layer names as a list (to tcl)
def get_layers(args, prt):
    lyrs=[]
    for lyr in prt.layers:
        lyr_name = gen_layer_name(lyr)
        if lyr.name != lyr_name:
            raise NameError("ERROR: layer name difference")
        print(lyr.name) #for Tcl
        lyrs.append(lyr.name)
    return lyrs #for non-Tcl use

# Returns the output node(s as a list) followed by coarse factor
def get_conn(args, prt):
    ctrl_f = args.control_flag
    # search through the partition
    lyr = args.layer_name
    lyr_obj = get_layer_from_partition(prt, lyr)

    # check if the layer has conditional output (exit decision)
    lyr_type = from_proto_layer_type(lyr_obj.type)
    if ctrl_f and lyr_type == LAYER_TYPE.Greater:
        lyr_out = lyr_obj.parameters.ctrledges
        crs_out = lyr_obj.parameters.ctrl_out_size
    else:

        # might be a list...
        lyr_out = lyr_obj.node_out
        # should be consistent btwn lyrs
        # (TODO add assertion, or tolerate if not consistent)
        crs_out = lyr_obj.parameters.coarse_out

    result=""
    for l in lyr_out:
        result+=str(l)+" "
    result += str(crs_out)
    # result form: lyr0 lyr1 ... lyrN crs_out
    print(result)

# Returns the input layer of the partition
def get_input(args,prt):
    for l in prt.layers:
        if l.streams_in[0].name == "in":
            print(l.name)
            return
    raise NameError("ERROR: no inputs or something?")

# Returns the output layer of the partition
def get_output(args,prt):
    #FIXME might break for weirdly connected layers
    for l in prt.layers:
        if l.streams_out[0].name == "out":
            print(l.name)
            return
    raise NameError("ERROR: no outputs or something?")

if __name__ == "__main__":
    #NOTE arguments returned are delineated by spaces, newline
    parser = argparse.ArgumentParser(
            description="Script for getting layer names (and connections),\
                    input and output nodes, bonus is it generates host code...\
                    TODO move to separate file")
    # regular top level arguments
    parser.add_argument('-p', '--json_path', metavar='PATH', required=True,
            help='Path to network json file (.json)')
    parser.add_argument('-pi', '--partition_index', type=int, required=False,
            default=0, help='Index of the target partition in the json')

    # first go at sub parser - separate one for each command
    subparsers = parser.add_subparsers(dest='helper_func', required=True)

    #get_layers
    get_layers_p = subparsers.add_parser("get_layers",
            help="Get the layer name for each layer in the partition")
    #get_conn
    get_conn_p = subparsers.add_parser("get_conn",
            help="Get the connections for a layer")
    get_conn_p.add_argument("-n","--layer_name", type=str, required=True)
    get_conn_p.add_argument("-c","--control_flag",
            action='store_true', help='Looking for ctrl edges.')
    #get_input
    get_input_p = subparsers.add_parser("get_input",
            help="Get the input layer name")
    #get_output
    get_output_p = subparsers.add_parser("get_output",
            help="Get the output layer name")

    gen_hc_p = subparsers.add_parser("gen_host_code",
            help="Generate the host code for the network")
    gen_hc_p.add_argument("-n","--network_name",type=str,required=True)

    # parse arguments
    args = parser.parse_args()

    # load partition information
    partitions = fpgaconvnet_optimiser.proto.fpgaconvnet_pb2.partitions()
    with open(args.json_path,'r') as f:
        json_format.Parse(f.read(), partitions)

    # select helper function
    if args.helper_func == 'get_layers':
        get_layers(args, partitions.partition[args.partition_index])
    elif args.helper_func == 'get_conn':
        get_conn(args, partitions.partition[args.partition_index])
    elif args.helper_func == 'get_input':
        get_input(args, partitions.partition[args.partition_index])
    elif args.helper_func == 'get_output':
        get_output(args, partitions.partition[args.partition_index])
    elif args.helper_func == 'gen_host_code':
        gen_host_code(args, partitions.partition[args.partition_index])
    else:
        raise NotImplementedError(
                f"ERROR: {args.helper_func} does not exist")
