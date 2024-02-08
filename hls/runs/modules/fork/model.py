import os
import sys

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

from modules.module_model import ModuleModel
from fpgaconvnet_optimiser.models.modules import Fork

MAX_RSC = {
    "LUT"   : 53200,
    "FF"    : 106400,
    "BRAM"  : 280,
    "DSP"   : 220
}

# define resource model
def build_module(parameter):
    return Fork(
        parameter['rows'],
        parameter['cols'],
        parameter['channels'],
        parameter['kernel_size'],
        parameter['coarse']
    )

# load accum model
model = ModuleModel(build_module)
model.load_points("modules/fork/logs")

# fit model
model.fit_model()

# save coefficients
model.save_coefficients("coefficients/fork")

# # plot error
# model.plot_error(MAX_RSC)

# print out error
model.print_absolute_error()
