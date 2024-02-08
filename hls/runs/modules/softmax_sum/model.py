import os
import sys

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

from modules.module_model import ModuleModel
from fpgaconvnet_optimiser.models.modules import SoftMaxSum

MAX_RSC = {
    "LUT"   : 53200,
    "FF"    : 106400,
    "BRAM"  : 280,
    "DSP"   : 220
}

# define resource model
def build_module(parameter):
    return SoftMaxSum(
        parameter['rows'],
        parameter['cols'],
        parameter['channels'],
        #data_width=parameter['data_width']
    )

def model_softmax_sum():
    # load softmax_sum model
    model = ModuleModel(build_module)
    model.load_points("modules/softmax_sum/logs")

    # fit model
    model.fit_model()

    # save coefficients
    model.save_coefficients("coefficients/softmax_sum")

    # plot error
    model.plot_error(MAX_RSC)

    # print out error
    model.print_absolute_error()

if __name__ == "__main__":
    model_softmax_sum()
