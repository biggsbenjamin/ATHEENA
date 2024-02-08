import os
import sys

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

from modules.module_model import ModuleModel
from fpgaconvnet_optimiser.models.modules import ReduceMax

MAX_RSC = {
    "LUT"   : 53200,
    "FF"    : 106400,
    "BRAM"  : 280,
    "DSP"   : 220
}

# define resource model
def build_module(parameter):
    return ReduceMax(
        parameter['rows'],
        parameter['cols'],
        parameter['channels'],
        #data_width=parameter['data_width']
    )

def model_reducemax():
    # load reducemax model
    model = ModuleModel(build_module)
    model.load_points("modules/reducemax/logs")

    # fit model
    model.fit_model()

    # save coefficients
    model.save_coefficients("coefficients/reducemax")

    # plot error
    model.plot_error(MAX_RSC)

    # print out error
    model.print_absolute_error()

if __name__ == "__main__":
    model_reducemax()
