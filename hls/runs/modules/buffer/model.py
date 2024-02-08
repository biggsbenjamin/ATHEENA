import os
import sys

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

from modules.module_model import ModuleModel
#from module_model import ModuleModel
from fpgaconvnet_optimiser.models.modules import Buffer

MAX_RSC = {
    "LUT"   : 53200,
    "FF"    : 106400,
    "BRAM"  : 280,
    "DSP"   : 220
}

# define resource model
def build_module(parameter):
    return Buffer(
        parameter['rows'],
        parameter['cols'],
        parameter['channels'],
        0, #ctrledge
        parameter['drop_mode'],
        #parameter['filters'],
        #parameter['groups'],
        #data_width=parameter['data_width']
    )

def model_buffer():
    # load buffer model
    model = ModuleModel(build_module)
    model.load_points("modules/buffer/logs")

    # fit model
    model.fit_model()

    # save coefficients
    model.save_coefficients("coefficients/buffer")

    # plot error
    model.plot_error(MAX_RSC)

    # print out error
    model.print_absolute_error()

if __name__ == "__main__":
    model_buffer()
