import os
import sys

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

from modules.module_model import ModuleModel
from fpgaconvnet_optimiser.models.modules import FIFO

MAX_RSC = {
    "LUT"   : 53200,
    "FF"    : 106400,
    "BRAM"  : 280,
    "DSP"   : 220
}

# define resource model
def build_module(parameter):
    return FIFO([
        1,
        1,
        1],
        parameter['coarse'],
        parameter['depth'],
        parameter['data_width']
    )

# load fifo model
model = ModuleModel(build_module)
model.load_points("modules/fifo/logs")

# filter parameters
#filters = {
#    "data_width" : [15,17]
#}
#model.filter_parameters(filters)

# fit model
model.fit_model()

# save coefficients
model.save_coefficients("coefficients/fifo")

# plot error
model.plot_error(MAX_RSC)

# print out error
model.print_absolute_error()
