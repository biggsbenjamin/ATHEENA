import random
import os
import json
import sys

from runner    import Runner
from functools import reduce

class ModuleRunner(Runner):

    def __init__(self,name):

        Runner.__init__(self)

        self.name = name
        self.fpga = "xc7z045ffg900-2"

        # parameters
        self.parameters = {}

        # flags
        self.resource_flag  = True
        self.power_flag     = False

        self.max_runners = 1

    def get_factors(self, n):
        return list(set(reduce(list.__add__,
            ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0))))

    def gen_parameters(self):
        # dimensions
        self.parameters['batch_size'] = random.randint(1,100)
        self.parameters['rows']       = random.randint(1,128)
        self.parameters['cols']       = random.randint(1,128)
        self.parameters['channels']   = random.randint(1,96)
        # basic
        self.parameters['freq']       = random.randint(50,150)

    def get_param_string(self):
        return "_".join([ param+"_"+str(self.parameters[param]) for param in self.parameters ])

    def get_header_file(self):
        header = """#ifndef {NAME}_PARAM_HPP_
#define {NAME}_PARAM_HPP_

{parameters}

#endif
        """.format(
            NAME=self.name.upper(),
            resource_flag=int(self.resource_flag==True),
            power_flag=int(self.power_flag==True),
            parameters="\n".join(["#define {NAME}_{PARAM_NAME}\t{param}".format(
                NAME=self.name.upper(),
                PARAM_NAME=param.upper(),
                param=self.parameters[param]) for param in self.parameters])
        )

        with open("modules/{name}/tb/{name}_param.hpp".format(name=self.name), 'w') as f:
            f.write(header)

    # run script
    def run(self):

        # setup results
        results = {
            "name"          : self.name,
            "fpga"          : self.fpga,
            "parameters"    : self.parameters,
            "resources" : {
                "LUT"   : 0,
                "FF"    : 0,
                "DSP"   : 0,
                "BRAM"  : 0
            }
        }

        # create header file
        self.get_header_file()

        # remove acc from glue
        if "acc" in self.parameters:
            del self.parameters['acc']

        # get clock period
        period = float(1000/self.parameters['freq'])

        # run synthesis
        print("RUNNING SYNTHESIS ... \n\n\n")
        os.system("vivado_hls -f scripts/run_module.tcl {name} synth {period} {fpga}".format(
            name=self.name,period=period,fpga=self.fpga))

        #if not self.check_timing():
        #    print("WARNING: timing failed")
        #    return
        #if not self.check_resources():
        #    print("WARNING: resources exceeded")
        #    return

        # run implementation
        print("RUNNING IMPLEMENTATION  ... \n\n\n")
        os.system("vivado_hls -f scripts/run_module.tcl {name} impl {period} {fpga}".format(
            name=self.name,period=period,fpga=self.fpga))

        # collect resources
        print("COLLECTING RESOURCES ... \n\n\n")
        try:
            results['resources'] = self.get_resources()
            results['clk_impl'] = self.get_clk_impl()

            os.system(f"mkdir -p modules/{self.name}/logs")
            with open("modules/{name}/logs/{param}.json".format(name=self.name,param=self.get_param_string()),"w") as f:
                json.dump(results,f)
        except:
            print("Unable to collect resources")

        return results

