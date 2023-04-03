from modules.module_model import *

class Delay_model(ModuleModel):
#ToDo: separate coef modelling for overflown DSP
    def __init__(self):
        super().__init__("Delay")

    def LUTLogic_model(self, parameters):
        # return np.array([int2bits(parameters["depth"]),1])
        return np.array([parameters["depth"], 1])

    def LUTRAM_model(self, parameters):
        buffer_depth = 2**int2bits(parameters["depth"])
        return np.array([buffer_depth, parameters["data_width"],1])
        # return np.array([parameters["depth"], parameters["data_width"]])

    def DSP_model(self, parameters):
        #ToDo: general DSP_multiplier model regarding data_width
        return 0

    def FF_model(self, parameters):
        return 2*int2bits(parameters["depth"])+1+2*32

if __name__ == "__main__":

    # load model
    m = Delay_model()

    # # save coefficients
    # with open("coefficients/queue_lutlogic.npy", "wb") as f:
    #     print(m.coef)
    #     np.save(f, m.coef["Logic_LUT"])

    m.get_model_performance()
