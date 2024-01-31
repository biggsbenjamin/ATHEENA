import sys
import parser
import argparse

import json
from fpgaconvnet_optimiser.tools.layer_enum import LAYER_TYPE
import fpgaconvnet_optimiser.proto.fpgaconvnet_pb2
from fpgaconvnet_optimiser.tools.layer_enum \
        import from_proto_layer_type, to_proto_layer_type
from fpgaconvnet_optimiser.models.layers import SqueezeLayer

import copy
import os
from google.protobuf import json_format
#from google.protobuf.text_format import MessageToString
from google.protobuf.json_format import MessageToJson

import math
import re

import pandas as pd

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

def exit_fusion(args,ee1,eef,output_name):
    #FIXME currently only works for two stage networks
    #load first exit stage - deep copy as this will form the basis of the output
    merge_out = copy.deepcopy(ee1)
    ee1_prt = ee1.partition[0]
    eef_prt = eef.partition[0]
    #for easier access - should pass by ref
    out0 = merge_out.partition[0]

    out0.output_node = "brn_exit"

    #find the exit buffer, keep a note
    ebuff=None
    #find the if layer, keep a note
    emerge=None
    for lyr in out0.layers:
        lyr_type = from_proto_layer_type(lyr.type)

        if lyr.streams_out[0].name == "out":
            if lyr_type == LAYER_TYPE.Buffer:
                print("found buffer to late stage")
                ebuff = lyr
            if lyr_type == LAYER_TYPE.If:
                print("found exit merge")
                emerge = lyr
                emerge.name = "brn_exit"
                emerge.node_out.pop()
                emerge.node_out.append("brn_exit")

        if lyr_type == LAYER_TYPE.Greater:
            print("Found exit decision layer")
            lyr.parameters.ctrl_out_size = 2

        if len(lyr.streams_out) == 1:
            if "exit" in lyr.node_out:
                print("Found layer before exit merge")
                lyr.node_out.pop()
                lyr.node_out.append("brn_exit")

    def _update_stream_info(stream,name,ctrl=False,split=False):
        stream.name = name
        stream.ctrl = ctrl
        stream.split = split
        return

    # Little helper function to edit io for changing layers
    def _connect_layers(partition,input_layer,output_layer, out_stream_index=0):
            stream_name = str(input_layer.name)+"_"+str(output_layer.name)
            # construct new input stream (from input_layer)
            assert len(output_layer.streams_in) == 1,\
                    "multiple input streams for output layer (2nd stage)"

            #stream names are the same UNLESS adding squeeze
            stream_name_in = stream_name
            stream_name_out = stream_name
            # same process for updating node in/out
            name_in = str(input_layer.name)
            name_out = str(output_layer.name)
            # check if there is a coarse layer mismatch
            if output_layer.parameters.coarse_in != \
                    input_layer.parameters.coarse_out:
                # create new partition layer
                sq_layer = partition.layers.add()
                # update squeeze layer with connection to ip and op layer
                sq_layer.name = "_".join([input_layer.name,
                                          "squeeze",
                                          output_layer.name])
                sq_layer.type = to_proto_layer_type(LAYER_TYPE.Squeeze)
                # create default squeeze model with params
                sq_model = SqueezeLayer(
                    input_layer.parameters.rows_out,
                    input_layer.parameters.cols_out,
                    input_layer.parameters.channels_out,
                    input_layer.parameters.coarse_out,
                    output_layer.parameters.coarse_in
                )
                # streams
                sq_stream_in = sq_layer.streams_in.add()
                stream_name_out = str(input_layer.name)+"_"+str(sq_layer.name)
                _update_stream_info(sq_stream_in,stream_name_out,False,False)
                sq_stream_out = sq_layer.streams_out.add()
                stream_name_in = str(sq_layer.name)+"_"+str(output_layer.name)
                _update_stream_info(sq_stream_out,stream_name_in,False,False)
                # node in list
                sq_layer.node_in.append(name_in)
                # node out list
                sq_layer.node_out.append(name_out)
                # squeeze is now inbetween the layers
                name_in = str(sq_layer.name)
                name_out = str(sq_layer.name)
                # layer parameters
                sq_model.layer_info(sq_layer.parameters,
                                    batch_size=partition.batch_size)

            ### Update output layer information
            if out_stream_index > 0: # expecting multiple inputs to layer
                # generate another place for a new stream
                new_stream_in = copy.deepcopy(output_layer.streams_in[0])
                # add stream to multi-input layer (when provided)
                output_layer.streams_in.append(new_stream_in)
            # update the stream information at the selected input port
            _update_stream_info(output_layer.streams_in[out_stream_index],
                                stream_name_in,False,False)
            # can't assign with list because of protobuf FIXME
            if output_layer.node_in[0] == str(output_layer.name):
                # if the layer loops back to itself (terminal)
                # then remove, ready to be updated
                output_layer.node_in.pop()
            # update the node in info with the name of the preceding layer
            output_layer.node_in.append(name_in)

            ### Update input layer information
            # change input_layer output stream, change node_out etc.
            assert len(input_layer.streams_out) == 1, \
                    "multiple output streams for 1st stage buffer"
            _update_stream_info(input_layer.streams_out[0],
                                stream_name_out,False,False)
            # can't assign with list because of protobuf FIXME
            if input_layer.node_out[0] == str(input_layer.name):
                input_layer.node_out.pop()
            input_layer.node_out.append(name_out)

    for eef_lyr in eef_prt.layers:
        #if its the input node then change the input to the buffer of ee1
        if eef_lyr.streams_in[0].name == "in":
            print("found input node for eef")
            new_ip_lyr = copy.deepcopy(eef_lyr)
            _connect_layers(out0, ebuff, new_ip_lyr, 0)
            # add connected version of 2nd stage input layer
            out0.layers.append(new_ip_lyr)
            continue
        #if its the output node then connect to IF (eMerge)
        if eef_lyr.streams_out[0].name == "out":
            print("found output node for eef")
            new_op_lyr = copy.deepcopy(eef_lyr)
            _connect_layers(out0, new_op_lyr, emerge, 1)
            # add connected version of 2nd stage input layer
            out0.layers.append(new_op_lyr)
            continue
        # add layer into merge_out
        out0.layers.append(eef_lyr)

    # saving to specified output name @ output path
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
        print("Output Path does not exist. Generating...")

    with open(os.path.join(args.output_path,f"{output_name}"),"w") as f:
        f.write(MessageToJson(merge_out,preserving_proto_field_name=True))
    print(f"JSON merge completed. Saved to {output_name}")
    return

def _strip_outer(str_in, strt_ch, end_ch):
    start = str_in.index(strt_ch)
    stripped = str_in[start+1:]
    end = stripped.index(end_ch)
    return stripped[:end]

if __name__ == "__main__":
    #NOTE arguments returned are delineated by spaces, newline
    parser = argparse.ArgumentParser(
            description="Script for merging ee json files.")

    # TODO make this compatitble with multiple exit stages
    parser.add_argument('-p1', '--json_path1', metavar='PATH', required=False,
            help='Path to network ee1 json file (.json)')
    parser.add_argument('-pf', '--json_pathf', metavar='PATH', required=False,
            help='Path to network eef json file (.json)')

    parser.add_argument('-cp', '--combined_path', metavar='PATH', required=False,
            help='Path to the optimal combined network stages')
    parser.add_argument('-jp', '--json_path', metavar='PATH', required=False,
            help='Path to the separate json files')

    parser.add_argument('-op','--output_path', metavar='PATH', required=True,
            help='Path to output directory')
    parser.add_argument("-on","--output_name", type=str, required=True,
            help="intended output name (minus .json)")

    # parse arguments
    args = parser.parse_args()

    if args.json_path1 is not None and args.json_pathf is not None:
        # load partition information
        ee1 = fpgaconvnet_optimiser.proto.fpgaconvnet_pb2.partitions()
        with open(args.json_path1,'r') as f:
            json_format.Parse(f.read(), ee1)

        eef = fpgaconvnet_optimiser.proto.fpgaconvnet_pb2.partitions()
        with open(args.json_pathf,'r') as f:
            json_format.Parse(f.read(), eef)

        output_name = "{}.json".format(args.output_name)

        #NOTE defaulting to partition 0
        exit_fusion(args, ee1, eef, output_name)
    else:
        # parser the combined file and generate all jsons
        # Updated to parsing the csv file
        df = pd.read_csv(args.combined_path)
        rp_names = df['report_name'].tolist()
        thru_ls = df['throughput'].tolist()
        rsc_ls = df['resource_max'].tolist()
        print(rp_names, rsc_ls, thru_ls)

        for nm, r, t in zip(rp_names, rsc_ls, thru_ls):
            # pull rsc and thruput nums for name
            thru = math.floor(float(t))
            rsc = math.floor(float(r)*100)
            #e[0] = [rsc,thru]

            print("Throughput:{} Resources:{}".format(thru, rsc))

            # split report name lines
            e = nm.split('\n')

            # fixup entry 1 - ee1 report
            e[0] = _strip_outer(e[0], "'", "'")
            # remove 'report_'
            e[0] = e[0][7:]
            # finds the resource lim specified in the file name
            rsc_lim = re.search(r"(?<=rsc)([0-9])+(?=p)", e[0]).group()
            j1 = os.path.join(args.json_path,"post_optim-rsc{}p/{}".format(rsc_lim,e[0]))

            # fixup entry 2 - eef report
            e[1] = _strip_outer(e[1], "'", "'")
            e[1] = e[1][7:]
            rsc_lim = re.search(r"(?<=rsc)([0-9])+(?=p)", e[1]).group()
            jf = os.path.join(args.json_path,"post_optim-rsc{}p/{}".format(rsc_lim,e[1]))

            # open the different files
            ee1 = fpgaconvnet_optimiser.proto.fpgaconvnet_pb2.partitions()
            with open(j1,'r') as f:
                json_format.Parse(f.read(), ee1)

            eef = fpgaconvnet_optimiser.proto.fpgaconvnet_pb2.partitions()
            with open(jf,'r') as f:
                json_format.Parse(f.read(), eef)

            output_name = "{}_rsc{}_thru{}.json".format(args.output_name, rsc, thru)

            exit_fusion(args, ee1, eef, output_name)
