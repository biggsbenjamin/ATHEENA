import untangle
import re
import csv
import numpy as np
import random

class Runner():

    def __init__(self):
        pass

    # check timing
    def check_timing(self):
        obj  = untangle.parse('modules/{name}/{name}_prj/solution/syn/report/test_{name}_csynth.xml'.format(name=self.name))
        predicted = float(obj.profile.UserAssignments.TargetClockPeriod.cdata)
        expected  = float(obj.profile.PerformanceEstimates.SummaryOfTimingAnalysis.EstimatedClockPeriod.cdata)
        if (predicted-expected) < 0:
            return False
        return True

    # check resources
    def check_resources(self):
        obj  = untangle.parse('modules/{name}/{name}_prj/solution/syn/report/test_{name}_csynth.xml'.format(name=self.name))
        ff   = float(obj.profile.AreaEstimates.Resources.FF.cdata)
        lut  = float(obj.profile.AreaEstimates.Resources.LUT.cdata)
        bram = float(obj.profile.AreaEstimates.Resources.BRAM_18K.cdata)
        dsp  = float(obj.profile.AreaEstimates.Resources.DSP48E.cdata)

        ff_available   = float(obj.profile.AreaEstimates.AvailableResources.FF.cdata)
        lut_available  = float(obj.profile.AreaEstimates.AvailableResources.LUT.cdata)
        bram_available = float(obj.profile.AreaEstimates.AvailableResources.BRAM_18K.cdata)
        dsp_available  = float(obj.profile.AreaEstimates.AvailableResources.DSP48E.cdata)

        if ff/ff_available > 1:
            return False
        if lut/lut_available > 1:
            return False
        if bram/bram_available > 1:
            return False
        if dsp/dsp_available > 1:
            return False
        return True

    # get resources
    """
    def get_resources(self):
        rsc = {
            "LUT"  : 0,
            "FF"   : 0,
            "BRAM" : 0,
            "DSP"  : 0,
            "Total_LUTs": 0,
            "Logic_LUTs": 0,
            "LUTRAMs"   : 0,
            "SRLs"      : 0,
            "FFs"       : 0,
            "RAMB36"    : 0,
            "RAMB18"    : 0,
            "DSP48"     : 0
        }

        rsc_info = re.compile("\| test_{name}_U0 +\| bd_0_hls_inst_0_test_{name} +\| +([0-9]+) \| +([0-9]+) \| +([0-9]+) \| +([0-9]+) \| +([0-9]+) \| +([0-9]+) \| +([0-9]+) \| +([0-9]+) \|".format(
            name=self.name))

        with open("modules/{name}/logs/{param}.rpt".format(name=self.name,param=self.get_param_string()),'r') as f:
            for line in f:
                rsc_row =  rsc_info.match(line)
                if rsc_row:
                    rsc["Total_LUTs"]   += int(rsc_row.group(1))
                    rsc["Logic_LUTs"]   += int(rsc_row.group(2))
                    rsc["LUTRAMs"]      += int(rsc_row.group(3))
                    rsc["SRLs"]         += int(rsc_row.group(4))
                    rsc["FFs"]          += int(rsc_row.group(5))
                    rsc["RAMB36"]       += int(rsc_row.group(6))
                    rsc["RAMB18"]       += int(rsc_row.group(7))
                    rsc["DSP48"]        += int(rsc_row.group(8))
                    break

        rsc["LUT"]  = rsc["Total_LUTs"]
        rsc["FF"]   = rsc["FFs"] + rsc["SRLs"]
        rsc["BRAM"] = 2*rsc["RAMB36"] + rsc["RAMB18"]
        rsc["DSP"]  = rsc["DSP48"]

        return rsc
    """

    def get_resources(self):
        obj = untangle.parse(f"modules/{self.name}/{self.name}_prj/solution/impl/report/verilog/{self.name}_top_export.xml")
        return {
            'LUT'   : int(obj.profile.AreaReport.Resources.LUT.cdata),
            'FF'    : int(obj.profile.AreaReport.Resources.FF.cdata),    
            'DSP'   : int(obj.profile.AreaReport.Resources.DSP.cdata),    
            'BRAM'  : int(obj.profile.AreaReport.Resources.BRAM.cdata)    
        }

    def get_clk_impl(self):
        obj = untangle.parse(f"modules/{self.name}/{self.name}_prj/solution/impl/report/verilog/{self.name}_top_export.xml")
        return float(obj.profile.TimingReport.AchievedClockPeriod.cdata)    
 
    """
    # find implemented clock period
    def get_clk_impl(self):
        with open("modules/{name}/{name}_prj/solution/impl/verilog/{name}_top.xdc".format(name=self.name),'r') as f:
            for line in f:
                clk = re.match("(create_clock -name ap_clk -period )([0-9]+(\.[0-9]+)?)",line)
                if clk:
                    return float(clk.group(2))
    """

    # generate data 
    def gen_data(self,dim,output_path,data_range=[0,1],data_type=float):
        # Initialise random data array
        data = np.ndarray(dim,dtype=data_type)
        # assign values
        for index,_ in np.ndenumerate(data):
            data[index] = random.uniform(data_range[0],data_range[1])
        # save to csv
        with open(output_path,"w") as f:
            writer = csv.writer(f)
            writer.writerows([data.reshape(-1).tolist()])

       
