import os
import json
import pydot
import copy
import math
import numpy as np
import networkx as nx

from google.protobuf import json_format
import fpgaconvnet_optimiser.proto.fpgaconvnet_pb2

import fpgaconvnet_optimiser.tools.parser as parser
import fpgaconvnet_optimiser.tools.graphs as graphs
import fpgaconvnet_optimiser.tools.matrix as matrix

import fpgaconvnet_optimiser.transforms.helper as helper

from fpgaconvnet_optimiser.models.partition.Partition import Partition

import fpgaconvnet_optimiser.tools.layer_enum
from fpgaconvnet_optimiser.tools.layer_enum import LAYER_TYPE

from fpgaconvnet_optimiser.models.layers import ConvolutionLayer
from fpgaconvnet_optimiser.models.layers import InnerProductLayer
from fpgaconvnet_optimiser.models.layers import PoolingLayer
from fpgaconvnet_optimiser.models.layers import ReLULayer
from fpgaconvnet_optimiser.models.layers import SqueezeLayer

class Network():

    def __init__(   self,
                    name,
                    network_path,
                    batch_size=1,
                    freq=125,
                    reconf_time=0.0,
                    data_width=16,
                    weight_width=8,
                    acc_width=30,
                    fuse_bn=True): #, rsc_allocation=1.0):
        print("Network __init__")

        # empty transforms configuration
        #FIXME why is this here??
        #self.transforms_config = {}

        ## percentage resource allocation
        #self.rsc_allocation = rsc_allocation

        ## bitwidths
        self.data_width     = data_width
        self.weight_width   = weight_width
        self.acc_width      = acc_width

        # network name
        self.name = name

        # initialise variables
        self.batch_size = batch_size
        self.fuse_bn = fuse_bn

        # load network
        self.model,self.submodels,self.graph,self.ctrledges=\
                parser.parse_net(network_path, view=False,
                data_width=self.data_width,
                weight_width=self.weight_width,
                acc_width=self.acc_width, fuse_bn=self.fuse_bn)

        # node and edge lists
        self.node_list = list(self.graph.nodes())
        self.edge_list = list(self.graph.edges())

        # matrices
        self.connections_matrix =\
                matrix.get_connections_matrix(self.graph)
        self.workload_matrix    =\
                matrix.get_workload_matrix(self.graph)

        # partitions
        self.partitions = [ Partition(copy.deepcopy(
            self.graph), self.ctrledges,
            data_width=self.data_width,
            weight_width=self.weight_width,
            acc_width=self.acc_width) ]

        # platform
        self.platform = {
            'name'          : 'platform',
            'freq'          : freq,
            'reconf_time'   : 0.0,
            'wr_time'       : 0.0,
            'ports'         : 4,
            'port_width'    : 64,
            'mem_bandwidth' : 0,
            'mem_capacity'  : 0,
            'constraints'   : {
                'FF'    : 0,
                'LUT'   : 0,
                'DSP'   : 0,
                'BRAM'  : 0
            }
        }

        # all types of layers
        self.conv_layers = helper.get_all_layers(
                self.graph, LAYER_TYPE.Convolution)
        self.pool_layers = helper.get_all_layers(
                self.graph, LAYER_TYPE.Pooling)

        # update partitions
        self.update_partitions()

    from fpgaconvnet_optimiser.transforms.partition import check_parallel_block
    from fpgaconvnet_optimiser.transforms.partition import get_all_horizontal_splits
    from fpgaconvnet_optimiser.transforms.partition import get_all_vertical_splits
    from fpgaconvnet_optimiser.transforms.partition import get_all_horizontal_merges
    from fpgaconvnet_optimiser.transforms.partition import get_all_vertical_merges
    from fpgaconvnet_optimiser.transforms.partition import split_horizontal
    from fpgaconvnet_optimiser.transforms.partition import split_vertical
    from fpgaconvnet_optimiser.transforms.partition import merge_horizontal
    from fpgaconvnet_optimiser.transforms.partition import merge_vertical
    from fpgaconvnet_optimiser.transforms.partition import split_horizontal_complete
    from fpgaconvnet_optimiser.transforms.partition import split_vertical_complete
    from fpgaconvnet_optimiser.transforms.partition import split_complete
    from fpgaconvnet_optimiser.transforms.partition import merge_horizontal_complete
    from fpgaconvnet_optimiser.transforms.partition import merge_vertical_complete
    from fpgaconvnet_optimiser.transforms.partition import merge_complete
    from fpgaconvnet_optimiser.transforms.partition import apply_random_partition

    from fpgaconvnet_optimiser.models.network.report import create_report

    from fpgaconvnet_optimiser.models.network.scheduler import get_partition_order
    from fpgaconvnet_optimiser.models.network.scheduler import get_input_base_addr
    from fpgaconvnet_optimiser.models.network.scheduler import get_output_base_addr
    from fpgaconvnet_optimiser.models.network.scheduler import get_partition_input_dependence
    from fpgaconvnet_optimiser.models.network.scheduler import get_partition_output_dependence
    from fpgaconvnet_optimiser.models.network.scheduler import get_scheduler
    from fpgaconvnet_optimiser.models.network.scheduler import get_schedule_csv
    from fpgaconvnet_optimiser.models.network.scheduler import check_scheduler

    from fpgaconvnet_optimiser.models.network.update import update_partitions
    from fpgaconvnet_optimiser.models.network.update import update_platform
    from fpgaconvnet_optimiser.models.network.update import update_coarse_in_out_partition

    from fpgaconvnet_optimiser.models.network.represent import get_model_input_node
    from fpgaconvnet_optimiser.models.network.represent import get_model_output_node
    from fpgaconvnet_optimiser.models.network.represent import save_all_partitions
    from fpgaconvnet_optimiser.models.network.represent import gen_layer_name
    from fpgaconvnet_optimiser.models.network.represent import add_stream_in
    from fpgaconvnet_optimiser.models.network.represent import add_stream_out
    # EE partitioning
    from fpgaconvnet_optimiser.models.network.represent import save_partition_subgraphs
    from fpgaconvnet_optimiser.models.network.represent import exit_split
    from fpgaconvnet_optimiser.models.network.represent import buffer_shift


    from fpgaconvnet_optimiser.models.network.validate import check_ports
    from fpgaconvnet_optimiser.models.network.validate import check_resources
    from fpgaconvnet_optimiser.models.network.validate import get_resources_bad_partitions
    from fpgaconvnet_optimiser.models.network.validate import check_workload
    from fpgaconvnet_optimiser.models.network.validate import check_streams
    from fpgaconvnet_optimiser.models.network.validate import check_partitions
    from fpgaconvnet_optimiser.models.network.validate import check_memory_bandwidth

    def get_memory_usage_estimate(self):

        # for sequential networks, our worst-case memory usage is
        # going to be both the largest input and output featuremap pair

        # get the largest input featuremap size
        max_input_size = 0
        max_output_size = 0
        for partition in self.partitions:
            input_node  = partition.input_nodes[0]
            output_node = partition.output_nodes[0]
            partition_input_size  = partition.graph.nodes[input_node]['hw'].workload_in()*partition.batch_size
            partition_output_size = partition.graph.nodes[output_node]['hw'].workload_out()*partition.batch_size*partition.wr_factor
            if partition_input_size > max_input_size:
                max_input_size = partition_input_size
            if partition_output_size > max_output_size:
                max_output_size = partition_output_size

        return math.ceil(((max_input_size + max_output_size)*self.data_width)/8)

    def get_latency(self, partition_list=None, ignore_reconf=False, print_lim_layer=False):
        if partition_list == None:
            partition_list = list(range(len(self.partitions)))
        latency = 0
        # iterate over partitions:
        for partition_index, partition in enumerate(self.partitions):
            if partition_index not in partition_list:
                continue
            # accumulate latency for each partition
            latency += partition.get_latency(self.platform["freq"],
                    print_lim_layer=print_lim_layer)
        # return the total latency as well as reconfiguration time
        if ignore_reconf:
            return latency
        return latency + (len(partition_list)-1)*self.platform["reconf_time"]

    def get_throughput(self, partition_list=None, print_lim_layer=False):
        if partition_list == None:
            partition_list = list(range(len(self.partitions)))
        # return the frames per second
        return float(self.batch_size)/self.get_latency(partition_list,
                print_lim_layer=print_lim_layer)

    def visualise(self, output_path):
        g = pydot.Dot(graph_type='digraph')
        for partition in self.partitions:
            partition_cluster = partition.visualise(self.partitions.index(partition))
            g.add_subgraph(partition_cluster)
        # save graph
        g.write_png(output_path)

    def get_layer_hardware(self, layer_proto):
        # get layer type
        layer_type = fpgaconvnet_optimiser.tools.layer_enum.from_proto_layer_type(layer_proto.type)
        # Convolution layer
        if layer_type == LAYER_TYPE.Convolution:
            return ConvolutionLayer(
                layer_proto.parameters.channels_out,
                layer_proto.parameters.rows_in,
                layer_proto.parameters.cols_in,
                layer_proto.parameters.channels_in,
                kernel_size =list(layer_proto.parameters.kernel_size),
                stride      =list(layer_proto.parameters.stride),
                pad         = [
                    layer_proto.parameters.pad_top,
                    layer_proto.parameters.pad_right,
                    layer_proto.parameters.pad_bottom,
                    layer_proto.parameters.pad_left],
                groups      =layer_proto.parameters.groups,
                fine        =layer_proto.parameters.fine,
                coarse_in   =layer_proto.parameters.coarse_in,
                coarse_out  =layer_proto.parameters.coarse_out
            )

        # Inner Product Layer
        if layer_type == LAYER_TYPE.InnerProduct:
            return InnerProductLayer(
                layer_proto.parameters.channels_out,
                layer_proto.parameters.rows_in,
                layer_proto.parameters.cols_in,
                layer_proto.parameters.channels_in,
                coarse_in   =layer_proto.parameters.coarse_in,
                coarse_out  =layer_proto.parameters.coarse_out
            )

        # Pooling layer
        if layer_type == LAYER_TYPE.Pooling:
            return PoolingLayer(
                layer_proto.parameters.rows_in,
                layer_proto.parameters.cols_in,
                layer_proto.parameters.channels_in,
                pool_type   = 'max',
                kernel_size =list(layer_proto.parameters.kernel_size),
                stride      =list(layer_proto.parameters.stride),
                pad         = [
                    layer_proto.parameters.pad_top,
                    layer_proto.parameters.pad_right,
                    layer_proto.parameters.pad_bottom,
                    layer_proto.parameters.pad_left],
                coarse      =layer_proto.parameters.coarse
            )

        # ReLU Layer
        if layer_type == LAYER_TYPE.ReLU:
            # create relu layer hardware
            return ReLULayer(
                layer_proto.parameters.rows_in,
                layer_proto.parameters.cols_in,
                layer_proto.parameters.channels_in,
                coarse      =layer_proto.parameters.coarse
            )

        # Squeeze Layer
        if layer_type == LAYER_TYPE.Squeeze:
            # create relu layer hardware
            return SqueezeLayer(
                layer_proto.parameters.rows_in,
                layer_proto.parameters.cols_in,
                layer_proto.parameters.channels_in,
                coarse_in   =layer_proto.parameters.coarse_in,
                coarse_out  =layer_proto.parameters.coarse_out
            )

    def load_network(self, network_path):
        # load the prototxt file
        partitions = fpgaconvnet_optimiser.proto.fpgaconvnet_pb2.partitions()
        with open(network_path, "r") as f:
            json_format.Parse(f.read(), partitions)
        # delete current partitions
        self.partitions = []
        # iterate over partitions
        for i, partition in enumerate(partitions.partition):
            # add all layers to partition
            graph = nx.DiGraph()
            for layer in partition.layers:
                # get layer type and hardware
                layer_type = fpgaconvnet_optimiser.tools.layer_enum.from_proto_layer_type(layer.type)
                layer_hw = self.get_layer_hardware(layer)
                # add layer
                graph.add_node( layer.name, type=layer_type, hw=layer_hw, inputs={} )
            # add all connections to graph
            for layer in partition.layers:
                if layer.node_in != layer.name:
                    graph.add_edge(layer.node_in, layer.name)
                if layer.node_out != layer.name:
                    graph.add_edge(layer.name, layer.node_out)
            # add partition
            new_partition = Partition(graph)
            # update partition attributes
            new_partition.wr_factor = int(partition.weights_reloading_factor)
            new_partition.wr_layer  = partition.weights_reloading_layer
            self.partitions.append(new_partition)

