import sys
import parser
import argparse

import json
from fpgaconvnet_optimiser.tools.layer_enum import LAYER_TYPE
import fpgaconvnet_optimiser.proto.fpgaconvnet_pb2
from fpgaconvnet_optimiser.tools.layer_enum \
        import from_proto_layer_type

import copy
import os
from google.protobuf import json_format
#from google.protobuf.text_format import MessageToString
from google.protobuf.json_format import MessageToJson

import math
import re

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

    # Little helper function to edit io for changing layers
    def _connect_layers(input_layer,output_layer, out_stream_index=0):
            stream_name = str(input_layer.name)+"_"+str(output_layer.name)
            # construct new input stream (from input_layer)
            assert len(output_layer.streams_in) == 1,\
                    "multiple input streams for output layer (2nd stage)"
            # coarse should be the same, FIXME add squeeze if not
            assert output_layer.parameters.coarse_in == \
                    input_layer.parameters.coarse_out,\
                    "COARSE DIFFERS BETWEEN BUFFER AND 2nd stage"
            if out_stream_index > 0: # expecting multiple inputs to layer
                new_stream_in = copy.deepcopy(output_layer.streams_in[0])
                output_layer.streams_in.append(new_stream_in)
            output_layer.streams_in[out_stream_index].name   = stream_name
            output_layer.streams_in[out_stream_index].ctrl   = False
            output_layer.streams_in[out_stream_index].split  = False
            # can't assign with list because of protobuf FIXME
            if output_layer.node_in[0] == str(output_layer.name):
                output_layer.node_in.pop()
            output_layer.node_in.append(str(input_layer.name))
            # change input_layer output stream, change node_out etc.
            assert len(input_layer.streams_out) == 1, \
                    "multiple output streams for 1st stage buffer"
            input_layer.streams_out[0].name   = stream_name
            input_layer.streams_out[0].ctrl   = False
            input_layer.streams_out[0].split  = False
            # can't assign with list because of protobuf FIXME
            if input_layer.node_out[0] == str(input_layer.name):
                input_layer.node_out.pop()
            input_layer.node_out.append(str(output_layer.name))

    for eef_lyr in eef_prt.layers:
        #if its the input node then change the input to the buffer of ee1
        if eef_lyr.streams_in[0].name == "in":
            print("found input node for eef")
            new_ip_lyr = copy.deepcopy(eef_lyr)
            _connect_layers(ebuff, new_ip_lyr, 0)
            # add connected version of 2nd stage input layer
            out0.layers.append(new_ip_lyr)
            continue
        #if its the output node then connect to IF (eMerge)
        if eef_lyr.streams_out[0].name == "out":
            print("found output node for eef")
            new_op_lyr = copy.deepcopy(eef_lyr)
            _connect_layers(new_op_lyr, emerge, 1)
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

    parser.add_argument('-c', '--combined_path', metavar='PATH', required=False,
            help='Path to the optimal combined network stages')
    parser.add_argument('-j', '--json_path', metavar='PATH', required=False,
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
        with open(args.combined_path, 'r') as f:
            lines = f.readlines()
            entries = (len(lines)-1)//3
            print(entries)
            entr = [lines[entry*3 : entry*3 +3] for entry in range(1,entries)]

        for e in entr:
            # fixup entry 0 - coords on graph
            e[0] = _strip_outer(e[0], '[',']')
            coords = e[0].split()
            thru = math.floor(float(coords[1]))
            rsc = math.floor(float(coords[0])*100)
            e[0] = [rsc,thru]

            print("Throughput:{} Resources:{}".format(thru, rsc))

            # fixup entry 1 - ee1 report
            e[1] = _strip_outer(e[1], "'", "'")
            # remove 'report_'
            e[1] = e[1][7:]
            # finds the resource lim specified in the file name
            rsc_lim = re.search(r"(?<=rsc)([0-9])+(?=p)", e[1]).group()
            e[1] = os.path.join(args.json_path,"post_optim-rsc{}p/{}".format(rsc_lim,e[1]))

            # fixup entry 2 - eef report
            e[2] = _strip_outer(e[2], "'", "'")
            e[2] = e[2][7:]
            rsc_lim = re.search(r"(?<=rsc)([0-9])+(?=p)", e[2]).group()
            e[2] = os.path.join(args.json_path,"post_optim-rsc{}p/{}".format(rsc_lim,e[2]))
            print(e)

        # generate the combined file
        for jlist in entr:
            j1,jf = jlist[1],jlist[2]
            rsc = jlist[0][0]
            thru = jlist[0][1]
            ee1 = fpgaconvnet_optimiser.proto.fpgaconvnet_pb2.partitions()
            with open(j1,'r') as f:
                json_format.Parse(f.read(), ee1)

            eef = fpgaconvnet_optimiser.proto.fpgaconvnet_pb2.partitions()
            with open(jf,'r') as f:
                json_format.Parse(f.read(), eef)

            output_name = "{}_rsc{}_thru{}.json".format(args.output_name, rsc, thru)

            exit_fusion(args, ee1, eef, output_name)
