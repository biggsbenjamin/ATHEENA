from typing import List
import pydot
import collections
from google.protobuf.json_format import MessageToDict
import numpy as np
from dataclasses import dataclass, field

from fpgaconvnet_optimiser.models.layers.utils import get_factors
from fpgaconvnet_optimiser.models.layers.utils import balance_module_rates

import fpgaconvnet_optimiser.proto.fpgaconvnet_pb2 as fpgaconvnet_pb2

@dataclass
class MultiPortLayer:
    """
    Base class for all layer models.

    Attributes
    ----------
    buffer_depth: int, default: 0
        depth of incoming fifo buffers for each stream in.
    rows: list int
        row dimension of input featuremap
    cols: list int
        column dimension of input featuremap
    channels: list int
        channel dimension of input featuremap
    ports_in: int
        number of ports into the layer
    ports_out: int
        number of ports out of the layer
    coarse_in: list int
        number of parallel streams per port into the layer.
    coarse_out: list int
        number of parallel streams per port out of the layer.
    data_width: int
        bitwidth of featuremap pixels
    modules: dict
        dictionary of `module` instances that make
        up the layer. These modules are used for the
        resource and performance models of the layer.
    """

    _rows: List[int]
    _cols: List[int]
    _channels: List[int]
    _coarse_in: List[int]
    _coarse_out: List[int]
    ports_in: int = field(default=1, init=True)
    _rows_op: List[int] = field(default=None, init=True)
    _cols_op: List[int] = field(default=None, init=True)
    _channels_op: List[int] = field(default=None, init=True)
    ports_out: int = field(default=1, init=True)
    data_width: int = field(default=16, init=True)
    buffer_depth: int = field(default=0, init=False)
    modules: dict = field(default_factory=collections.OrderedDict, init=False)

    """
    properties
    """
    #legacy (input ports)
    @property
    def rows(self) -> List[int]:
        assert(isinstance(self._rows,list))
        return self._rows

    @property
    def cols(self) -> List[int]:
        assert(isinstance(self._cols,list))
        return self._cols

    @property
    def channels(self) -> List[int]:
        assert(isinstance(self._channels,list))
        return self._channels

    #output ports
    @property
    def rows_op(self) -> List[int]:
        if self._rows_op is None: #treating None as 1 op port
            return [self._rows[0]]*self.ports_out
        assert(len(self._rows_op) == self.ports_out)
        return self._rows_op

    @property
    def cols_op(self) -> List[int]:
        if self._cols_op is None: #treating None as 1 op port
            return [self._cols[0]]*self.ports_out
        assert(len(self._cols_op) == self.ports_out)
        return self._cols_op

    @property
    def channels_op(self) -> List[int]:
        if self._channels_op is None: #treating None as 1 op port
            return [self._channels[0]]*self.ports_out
        assert(len(self._channels_op) == self.ports_out)
        return self._channels_op

    @property
    def coarse_in(self) -> List[int]:
        return self._coarse_in

    @property
    def coarse_out(self) -> List[int]:
        return self._coarse_out

    """
    property setters
    """

    @rows.setter
    def rows(self, val: List[int]) -> None:
        assert(isinstance(val,list))
        assert(len(val) == self.ports_in)
        self._rows = val
        self.update()

    @cols.setter
    def cols(self, val: List[int]) -> None:
        assert(isinstance(val,list))
        assert(len(val) == self.ports_in)
        self._cols = val
        self.update()

    @channels.setter
    def channels(self, val: List[int]) -> None:
        assert(isinstance(val,list))
        assert(len(val) == self.ports_in)
        self._channels = val
        self.update()

    #output ports

    @rows_op.setter
    def rows_op(self, val: List[int]) -> None:
        assert(isinstance(val,list))
        assert(len(val) == self.ports_out)
        self._rows_op = val
        self.update()

    @cols_op.setter
    def cols_op(self, val: List[int]) -> None:
        assert(isinstance(val,list))
        assert(len(val) == self.ports_out)
        self._cols_op = val
        self.update()

    @channels_op.setter
    def channels_op(self, val: List[int]) -> None:
        assert(isinstance(val,list))
        assert(len(val) == self.ports_out)
        self._channels_op = val
        self.update()

    @coarse_in.setter
    def coarse_in(self, val: List[int]) -> None:
        assert(isinstance(val,list))
        assert(len(val) == self.ports_in)
        for i in range(val):
            assert(val[i] in self.coarse_in_feasible(port_index=i))
        self._coarse_in = val
        self.coarse_out = val
        self.update()

    @coarse_out.setter
    def coarse_out(self, val: List[int]) -> None:
        assert(isinstance(val,list))
        assert(len(val) == self.ports_out)
        for i in range(val):
            assert(val[i] in self.coarse_out_feasible(port_index=i))
        self._coarse_out = val
        self._coarse_in = val
        self.update()

    def rows_in(self, port_index=0):
        """
        Parameters
        ----------
        port_index: int
            index of port into the layer

        Returns
        -------
        int
            row dimension of the input featuremap
        """
        assert(port_index < self.ports_in)
        return self.rows[port_index]

    def cols_in(self, port_index=0):
        """
        Parameters
        ----------
        port_index: int
            index of port into the layer

        Returns
        -------
        int
            column dimension of the input featuremap
        """
        assert(port_index < self.ports_in)
        return self.cols[port_index]

    def channels_in(self, port_index=0):
        """
        Parameters
        ----------
        port_index: int
            index of port into the layer

        Returns
        -------
        int
            channel dimension of the input featuremap
        """
        assert(port_index < self.ports_in)
        return self.channels[port_index]

    def rows_out(self, port_index=0):
        """
        Parameters
        ----------
        port_index: int
            index of port out of the layer

        Returns
        -------
        int
            row dimension of the output featuremap
        """
        assert(port_index < self.ports_out,
                "ERROR: multiport layer rows_out: rows-{} port-{}".format(self.rows,port_index))
        return self.rows_op[port_index]

    def cols_out(self, port_index=0):
        """
        Parameters
        ----------
        port_index: int
            index of port out of the layer

        Returns
        -------
        int
            column dimension of the output featuremap
        """
        assert(port_index < self.ports_out,
                "ERROR: multiport layer cols_out: cols-{} port-{}".format(self.cols,port_index))
        return self.cols_op[port_index]

    def channels_out(self, port_index=0):
        """
        Parameters
        ----------
        port_index: int
            index of port out of the layer

        Returns
        -------
        int
            channel dimension of the output featuremap
        """
        assert(port_index < self.ports_out,
                "ERROR: multiport layer channels_out: chans-{} port-{}".format(
                    self.channels,port_index))
        return self.channels_op[port_index]

    def rates_graph(self):

        # create the rates graph
        rates_graph = np.zeros(shape=(len(self.modules.keys()),
                                      len(self.modules.keys())+1) , dtype=float )

        # iterate over modules
        for i, module in enumerate(self.modules.keys()):
            # update rates_graph
            rates_graph[i,i] = self.modules[module].rate_in()
            rates_graph[i,i+1] = self.modules[module].rate_out()

        # return rates_graph
        return rates_graph

    def rate_in(self, port_index=0):
        """
        Parameters
        ----------
        index: int
            index of port into layer

        Returns
        -------
        float
            rate of words into layer. As a fraction of a
            clock cycle.

            default is 1.0
        """
        assert(port_index < self.ports_in)
        return abs(balance_module_rates(self.rates_graph())[0,0])

    def rate_out(self, port_index=0):
        """
        Parameters
        ----------
        index: int
            index of port into layer

        Returns
        -------
        float
            rate of words out of the layer. As a fraction
            of a clock cycle.

            default is 1.0
        """
        assert(port_index < self.ports_out)
        return abs(balance_module_rates(
            self.rates_graph())[len(self.modules.keys())-1,len(self.modules.keys())])

    def streams_in(self, port_index=0):
        """
        Returns
        -------
        int
            number of parallel streams into the layer.
        """
        assert(port_index < self.ports_in)
        return self.coarse_in[port_index]

    def streams_out(self, port_index=0):
        """
        Returns
        -------
        int
            number of parallel streams out of the layer.
        """
        assert(port_index < self.ports_out)
        return self.coarse_out[port_index]

    def workload_in(self, port_index=0):
        """
        Parameters
        ----------
        index: int
            index of port into layer

        Returns
        -------
        int
            workload into layer from port `index` for a single
            featuremap. This is calculated by
            `rows_in()*cols_in()*channels_in()`.
        """
        assert(port_index < self.ports_in)
        return self.rows_in(port_index) * self.cols_in(port_index) * self.channels_in(port_index)

    def workload_out(self, port_index=0):
        """
        Parameters
        ----------
        index: int
            index of port out of layer

        Returns
        -------
        int
            workload out of layer from port `index` for a
            single featuremap. This is calculated by
            `rows_out()*cols_out()*channels_out()`.
        """
        assert(port_index < self.ports_out)
        return self.rows_out(port_index) * self.cols_out(port_index) * self.channels_out(port_index)

    def size_in(self, port_index=0):
        """
        Returns
        -------
        int
            workload in per stream.
        """
        assert(port_index < self.ports_in)
        return self.rows_in(port_index) * self.cols_in(port_index) * int( self.channels_in(port_index) / self.streams_in(port_index) )

    def size_out(self, port_index=0):
        """
        Returns
        -------
        int
            workload out per stream.
        """
        assert(port_index < self.ports_out)
        return self.rows_out(port_index) * self.cols_out(port_index) * int( self.channels_out(port_index) / self.streams_out(port_index) )

    def width_in(self):
        """
        Returns
        -------
        int
            data width in
        """
        return self.data_width

    def width_out(self):
        """
        Returns
        -------
        int
            data width out
        """
        return self.data_width

    def latency_in(self):
        return max([
            abs(self.workload_in(i)/(self.rate_in(i)*self.streams_in(i) )) for
            i in range(self.ports_in) ])

    def latency_out(self):
        return max([
            abs(self.workload_out(i)/(self.rate_out(i)*self.streams_out(i)))
            for i in range(self.ports_out) ])

    def latency(self):
        return max(self.latency_in(), self.latency_out())

    def pipeline_depth(self):
        return sum([ self.modules[module].pipeline_depth() for module in self.modules ])

    def wait_depth(self):
        return sum([ self.modules[module].wait_depth() for module in self.modules ])

    def resource(self):
        return {
            "LUT"   : 0,
            "FF"    : 0,
            "BRAM"  : bram_stream_resource_model(self.buffer_depth,self.data_width)*self.streams_in(),
            "DSP"   : 0
        }

    def get_coarse_in_feasible(self, port_index=0, wr_factor=1):
        assert(port_index < self.ports_in)
        return get_factors(int(self.channels_in(port_index)/wr_factor))

    def get_coarse_out_feasible(self, port_index=0, wr_factor=1):
        assert(port_index < self.ports_out)
        return get_factors(int(self.channels_out(port_index)/wr_factor))

    def update(self):
        pass

    def layer_info(self, parameters, batch_size=1):
        parameters.batch_size   = batch_size
        parameters.buffer_depth = self.buffer_depth
        parameters.rows_in      = self.rows_in()
        parameters.cols_in      = self.cols_in()
        parameters.channels_in  = self.channels_in()
        parameters.rows_out     = self.rows_out()
        parameters.cols_out     = self.cols_out()
        parameters.channels_out = self.channels_out()
        parameters.coarse_in    = self.streams_in()
        parameters.coarse_out   = self.streams_out()

    def get_operations(self):
        return 0

    def layer_info_dict(self):
        # get parameters
        parameter = fpgaconvnet_pb2.parameter()
        self.layer_info(parameter)
        # convert to dictionary
        return MessageToDict(parameter, preserving_proto_field_name=True)

    def visualise(self,name):
        cluster = pydot.Cluster(name,label=name)

        for i in range(self.coarse_in[0]):
            cluster.add_node(pydot.Node( "_".join([name,"edge",str(i)]), label=self.__class__.__name__ ))

        return cluster, "_".join([name,"edge"]), "_".join([name,"edge"])

    def functional_model(self,data,batch_size=1):
        return
