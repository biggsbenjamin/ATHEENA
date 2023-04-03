from modules.module_model import *

class EltWiseFixed_model(ModuleModel):

  def __init__(self):
    super().__init__("EltWiseFixed")

  def LUTLogic_model(self, parameters):
    data_width = parameters["data_width"]
    ports_in = parameters["ports_in"]
    return np.array([ports_in, data_width, ports_in * data_width])

  def LUTLogic_model_width(self, parameters):
    # data_width = parameters["data_width"]
    ports_in = parameters["ports_in"]
    return np.array([ports_in])

  # def plot_results(self, plot=nnls_RSC_TYPES):
  #   path = "results/{0}/".format(self.name)
  #   for rsc in plot:
  #       fig, ax = plt.subplots(figsize=(10, 6))
  #       x = self.actual[rsc]
  #       y = self.results[rsc]
  #       ax.plot(x, x, label="actual")
  #       ax.scatter(x, y, label="predict", marker="x", color="r")
  #       ax.set_title(rsc)
  #       ax.set_xlabel("actual")
  #       ax.set_ylabel("predicted")
  #       ax.legend()
  #       ax.set_xlim((0, 100))
  #       ax.set_ylim((0, 100))
  #       #fig.savefig(path + rsc + ".jpg")

  # def plot_results_width(self, plot=nnls_RSC_TYPES): 
  #   path = "results/{0}/".format(self.name)
  #   for rsc in plot:
  #         fig, ax = plt.subplots(figsize=(10, 6))
  #         x = self.actual[rsc]
  #         ax.plot(x, x, label="actual")
  #         ax.set_title(rsc)
  #         ax.set_xlabel("actual")
  #         ax.set_ylabel("predicted")
  #         for w in width_TYPES:
  #           x = self.actual_width[rsc][w]
  #           y = self.results_width[rsc][w]
  #           ax.scatter(x, y, label="predict: data_width={0}".format(w), marker="x")
  #         ax.legend()
  #         ax.set_xlim((0, 100))
  #         ax.set_ylim((0, 100))
  #         #fig.savefig(path + rsc + "_width.jpg")
