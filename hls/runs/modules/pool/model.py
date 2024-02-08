from modules.module_model import ModuleModel
from fpgaconvnet_optimiser.models.modules import Pool

MAX_RSC = {
    "LUT"   : 53200,
    "FF"    : 106400,
    "BRAM"  : 280,
    "DSP"   : 220
}

# define resource model
def build_module(parameter):
    return Pool(
        parameter['rows'],
        parameter['cols'],
        parameter['channels'],
        parameter['kernel_size']
    )

# load accum model
model = ModuleModel(build_module)
model.load_points("modules/pool/logs")

# fit model
model.fit_model()

# save coefficients
model.save_coefficients("coefficients/pool")

# # plot error
model.plot_error(MAX_RSC)

# print out error
model.print_absolute_error()
