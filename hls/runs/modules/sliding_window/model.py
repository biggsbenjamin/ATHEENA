import os
import sys

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

from modules.module_model import ModuleModel
from fpgaconvnet_optimiser.models.modules import SlidingWindow

MAX_RSC = {
    "LUT"   : 53200,
    "FF"    : 106400,
    "BRAM"  : 280,
    "DSP"   : 220
}

def model_sw():
# define resource model
    def build_module(parameter):
        return SlidingWindow(
            parameter['rows'],
            parameter['cols'],
            parameter['channels'],
            [parameter['kernel_size_x'],parameter['kernel_size_y']],
            [parameter['stride_x'],parameter['stride_y']],
            parameter['pad_top'],
            parameter['pad_right'],
            parameter['pad_bottom'],
            parameter['pad_left'],
        )

# load accum model
    model = ModuleModel(build_module)
    model.load_points("modules/sliding_window/logs")

# fit model
    model.fit_model()


# save coefficients
    model.save_coefficients("coefficients/sliding_window")

# plot error
    model.plot_error(MAX_RSC)

# print out error
    model.print_absolute_error()

if __name__ == "__main__":
    model_sw()
