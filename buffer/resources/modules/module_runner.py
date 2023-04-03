import random
import os
import csv
import json
import re
import subprocess
from datetime import date

class ModuleRunner:

    def __init__(self, name, max_runners=1000):
        self.name = name
        self.fpga = "xc7z020clg484-1"
        self.parameters = {}
        self.max_runners = max_runners
        self.date = str(date.today())
        self.commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("ascii")

    def gen_parameters(self):
        # Generate constarint randomized test params
        raise NotImplementedError("Constraint ramdomized test not implemented for module \"{0}\"".format(self.name))

    def get_param_names(self):
        params = []
        for key, val in self.parameters.items():
            if isinstance(val, list):
                params.append(key + "_" + "_".join([ str(v) for v in val]))
            else:
                params.append(key + "_" + str(val))
        return "_".join(params)
        #return "_".join([key + "_" + str(val) for key, val in self.parameters.items()])

    def get_results(self, run_path):
        with open(f"{run_path}/resource_report.csv","r") as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]

        with open(f"{run_path}/timing_report.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            rows_timing = [row for row in reader]

        if(len(rows) <= 1 or len(rows_timing) < 3):
            return

        #resource_usage
        Total_LUTs = int(rows[1][2])
        Logic_LUTs = int(rows[1][3])
        LUT_RAMs = int(rows[1][4])
        LUT_SRs = int(rows[1][5])
        FFs = int(rows[1][6])
        BRAM36 = int(rows[1][7])
        BRAM18 = int(rows[1][8])
        DSPs = int(rows[1][-1])

        #timing_summary
        pat_0 = r".+(\d+)"
        pat_1 = r".+(\d+\.\d+.*)"

        return {
            "name": self.name,
            "fpga": self.fpga,
            "parameters": self.parameters,
            "time_stamp": {
                "date": self.date,
                "commit_hash": self.commit_hash
            },
            "resources": {
                "LUT": Total_LUTs,
                "Logic_LUT": Logic_LUTs,
                "LUT_RAM": LUT_RAMs,
                "LUT_SR": LUT_SRs,
                "FF": FFs,
                "DSP": DSPs,
                "BRAM36": BRAM36,
                "BRAM18": BRAM18
            },
            "timing": {
                "Setup": {
                    "failing_endpoints": int(re.match(pat_0, rows_timing[0][0]).group(1)),
                    "worst_slack": re.match(pat_1, rows_timing[0][1]).group(1),
                    "total_violation": re.match(pat_1, rows_timing[0][2]).group(1)
                },
                "Hold": {
                    "failing_endpoints": int(re.match(pat_0, rows_timing[1][0]).group(1)),
                    "worst_slack": re.match(pat_1, rows_timing[1][1]).group(1),
                    "total_violation": re.match(pat_1, rows_timing[1][2]).group(1)
                },
                "PW": {
                    "failing_endpoints": int(re.match(pat_0, rows_timing[2][0]).group(1)),
                    "worst_slack": re.match(pat_1, rows_timing[2][1]).group(1),
                    "total_violation": re.match(pat_1, rows_timing[2][2]).group(1)
                }
            }
        }



    def run(self):

        # create the folder path for results and so on
        run_path = f"results/{self.name}/{self.get_param_names()}"
        try:
            os.mkdir(run_path)
        except:
            print(f"WARNING: {run_path} exists!")

        # save the configuration
        with open(f"{run_path}/config.json", "w") as f:
            json.dump(self.parameters, f, indent=4)

        # build module verilog
        module_identifier = re.sub(r'(?<!^)(?=[A-Z])', '_', self.name.replace("Fixed","")).lower()
        # os.system(f"scala ../target/scala-2.12/fpgaconvnet-chisel-assembly-0.1.0.jar module \
        #         {module_identifier} {run_path}/config.json --target-dir {run_path}")
        os.system(f"scala ../target/pack/bin/elaborate module \
                {module_identifier} {run_path}/config.json --target-dir {run_path}")

        # create the vivado project folder
        prj_path = f"{self.name}_rsc_prj"
        try:
            os.mkdir(prj_path)
        except:
            print(f"WARNING: {prj_path} exists!")

        # run synthesis
        os.system(f"vivado -mode batch -notrace -source ../scripts/tcl/get_rsc_usage.tcl -tclargs \
                \" -prj-path {prj_path} -hw-path {run_path}/{self.name}.v -top {self.name} \
                -output-path {run_path} -fpga {self.fpga} \" ")


        #collect results
        with open(f"{run_path}/results.json", "w") as f:
            json.dump(self.get_results(run_path), f,
                    ensure_ascii=False, sort_keys=False, indent=4)







