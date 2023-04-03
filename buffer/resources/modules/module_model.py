import os
import json
import numpy as np
import sklearn.linear_model
import matplotlib.pyplot as plt
import math



RSC_TYPES=["Logic_LUT", "LUT_RAM", "LUT_SR", "FF", "DSP", "BRAM18"]
nnls_RSC_TYPES = ["Logic_LUT", "LUT_RAM", "LUT_SR"]
width_TYPES = [8, 16, 32] #Discrete width types for width-based nnls model
MAX_RSC = {
    "LUT"   : 53200,
    "FF"    : 106400,
    "BRAM"  : 280,
    "DSP"   : 220
}

def int2bits(n):
  return math.ceil(math.log(n, 2))

def get_nnls_coef(model, rsc):
  nnls = sklearn.linear_model.LinearRegression(positive=True, fit_intercept=False)
  return nnls.fit(model,rsc).coef_

class ModuleModel:

  def __init__(self, name):
    self.name = name
    #self.PARAMETER_TYPES = [] #list of parameters string
    #self.Data = []
    self.loadData()
    self.coef = dict.fromkeys(nnls_RSC_TYPES)
    self.results = dict.fromkeys(RSC_TYPES)

    #width-based nnls data
    self.coef_width = {rsc: dict.fromkeys(width_TYPES)
                for rsc in nnls_RSC_TYPES}
    self.results_width = {rsc: dict.fromkeys(width_TYPES) for rsc in nnls_RSC_TYPES}

    #fit model on init
    self.load_width_based_Data()
    self.fit_LUT_model()
    self.fit_LUT_model_width()

    ## get flip-flop and BRAM usage
    self.get_FF_results()
    self.get_BRAM_results()
    self.get_DSP_results()

  def loadData(self):
    self.parameters = [] #List of dict
    self.actual = {k: [] for k in RSC_TYPES} #Dict of list
    self.points = 0
    #exclude = [".jpg"]
    folders = [f for f in os.listdir("results/{0}".format(self.name)) if not f.endswith(".jpg")]
    for folder in folders:
        # self.points += 1
        filename = "results/{0}/".format(self.name) + str(folder) + "/results.json"
        try:
          with open(filename,"r") as jsonfile:
              oneDict = json.load(jsonfile)
              self.parameters.append(oneDict["parameters"])
              for rsc in RSC_TYPES:
                  self.actual[rsc].append(oneDict["resources"][rsc])
          self.points += 1
        except:
          pass

    for rsc in RSC_TYPES:
      self.actual[rsc] = np.array(self.actual[rsc])


  def load_width_based_Data(self):
    #width-based data
    self.parameters_width = dict.fromkeys(width_TYPES)
    self.actual_width = {rsc: dict.fromkeys(width_TYPES) for rsc in RSC_TYPES}
    #creating masks
    width_points = [ point["data_width"] for point in self.parameters ]
    mask = {w: (np.array(width_points) == w) for w in width_TYPES}
    #loading width-based data
    for w in width_TYPES:
      self.parameters_width[w] = np.array(self.parameters, dtype=object)[mask[w]]
    for rsc in RSC_TYPES:
      for w in width_TYPES:
        self.actual_width[rsc][w] = np.array(self.actual[rsc])[mask[w]]


  def LUTLogic_model(self, para):
    return np.array([0])

  def LUTRAM_model(self, para):
    return np.array([0])

  def LUTSR_model(self, para):
    return np.array([0])

  def get_nnls_model(self):
    return {
        "Logic_LUT": self.LUTLogic_model,
        "LUT_RAM": self.LUTRAM_model,
        "LUT_SR": self.LUTSR_model
    }

  def LUTLogic_model_width(self, para):
    return np.array([0])

  def LUTRAM_model_width(self, para):
    return np.array([0])

  def LUTSR_model_width(self, para):
    return np.array([0])

  def get_nnls_model_width(self):
    return {
        "Logic_LUT": self.LUTLogic_model_width,
        "LUT_RAM": self.LUTRAM_model_width,
        "LUT_SR": self.LUTSR_model_width
    }

  def FF_model(self, parameters):
    return 0

  def BRAM_model(self, parameters):
    return 0

  def DSP_model(self, parameters):
    return 0


  def fit_LUT_model(self):
    model = {k: [] for k in nnls_RSC_TYPES}
    for rsc in nnls_RSC_TYPES:
        func = self.get_nnls_model()[rsc]
        for point in self.parameters:
            model[rsc].append(func(point))

    for rsc in nnls_RSC_TYPES:
        self.coef[rsc] = get_nnls_coef(np.array(model[rsc]), np.array(self.actual[rsc]))
        self.results[rsc] = np.array(np.dot(np.array(model[rsc]), self.coef[rsc]), dtype="int")

  def fit_LUT_model_width(self):
    #get modeled parameter points
    #model = {rsc: {w: [] for w in width_TYPES} for rsc in nnls_RSC_TYPES}
    for rsc in nnls_RSC_TYPES:
      func = self.get_nnls_model_width()[rsc]
      for w in width_TYPES:
        model = []
        for point in self.parameters_width[w]:
          model.append(func(point))
        #fit coef for each rsc and width
        self.coef_width[rsc][w] = get_nnls_coef(np.array(model), np.array(self.actual_width[rsc][w]))
        self.results_width[rsc][w] = np.array(np.dot(np.array(model), self.coef_width[rsc][w]), dtype="int")

  # def fit_LUT_model_width(self):
  #   def get_nnls_coef(model, rsc):
  #     nnls = sklearn.linear_model.LinearRegression(positive=True, fit_intercept=False)
  #     return nnls.fit(model,rsc).coef_
  #   #get modeled parameter points
  #   self.model_width = {rsc: {w: [] for w in width_TYPES} for rsc in nnls_RSC_TYPES}
  #   for rsc in nnls_RSC_TYPES:
  #     func = self.get_nnls_model_width()[rsc]
  #     for w in width_TYPES:
  #       for point in self.parameters_width[w]:
  #         self.model_width[rsc][w].append(func(point))
  #       #fit coef for each rsc and width
  #       # self.coef_width[rsc][w] = get_nnls_coef(np.array(model), np.array(self.actual_width[rsc][w]))
  #       # self.results_width[rsc][w] = np.array(np.dot(np.array(model), self.coef_width[rsc][w]), dtype="int")

  def get_FF_results(self):
    self.results["FF"] = [self.FF_model(point) for point in self.parameters]

  def get_BRAM_results(self):
    self.results["BRAM18"] = [self.BRAM_model(point) for point in self.parameters]

  def get_DSP_results(self):
    self.results["DSP"] = [self.DSP_model(point) for point in self.parameters]

  def plot_results(self, plot=nnls_RSC_TYPES):
    path = "results/{0}/".format(self.name)
    for rsc in plot:
        fig, ax = plt.subplots(figsize=(10, 6))
        x = self.actual[rsc]
        y = self.results[rsc]
        ax.plot(x, x, label="actual")
        ax.scatter(x, y, label="predict", marker="x", color="r")
        ax.set_title(rsc)
        ax.set_xlabel("actual")
        ax.set_ylabel("predicted")
        ax.legend()
        fig.savefig(path + rsc + ".jpg")

  def plot_results_width(self, plot=nnls_RSC_TYPES):
    path = "results/{0}/".format(self.name)
    for rsc in plot:
          fig, ax = plt.subplots(figsize=(10, 6))
          x = self.actual[rsc]
          ax.plot(x, x, label="actual")
          ax.set_title(rsc)
          ax.set_xlabel("actual")
          ax.set_ylabel("predicted")
          for w in width_TYPES:
            x = self.actual_width[rsc][w]
            y = self.results_width[rsc][w]
            ax.scatter(x, y, label="predict: data_width={0}".format(w), marker="x")
          # ax.legend()
          # fig.savefig(path + rsc + "_width.jpg")

  def get_model_performance(self, resources=RSC_TYPES):
    #return mean and variance of model in models(list)
    #performance = {rsc: dict.fromkeys(["mean", "var"]) for rsc in models}
    for rsc in resources:
      if rsc in nnls_RSC_TYPES:
        diff = self.results[rsc] - self.actual[rsc]
        mean_err = diff.mean()
        mse = (diff*diff).mean()
        std = diff.std()

        # diff_width = np.array([])
        # for w in width_TYPES:
        #   diff_width = np.append(diff_width, (self.results_width[rsc][w] - self.actual_width[rsc][w]))
        # mean_err_width = diff_width.mean()
        # mse_width = (diff_width*diff_width).mean()
        # std_width = diff_width.std()
        print("="*5 + "{}_model".format(rsc) + "="*5)
        print("Base: mean_err={0}, mse={1}, std={2}".format(mean_err, mse, std))
        # print("Width_based: mean_err={0}, mse={1}, std={2}".format(mean_err_width, mse_width, std_width))
        print("\n")

      else:
        diff = self.results[rsc] - self.actual[rsc]
        mean_err = diff.mean()
        mse = (diff*diff).mean()
        std = diff.std()
        print("="*5 + "{}_model".format(rsc) + "="*5)
        print("Base: mean_err={0}, mse={1}, std={2}".format(mean_err, mse, std))
        print("\n")

  # def filter_above(self, param_type, val):
  #   param_points = np.array([p[param_type] for p in self.parameters])
  #   mask = param_points <= val
  #   self.parameters = np.array(self.parameters)[mask]
  #   for rsc in RSC_TYPES:
  #     self.actual[rsc] = self.actual[rsc][mask]

  def get_rsc(self, parameters):
    logic_lut_coef = self.coef_width["Logic_LUT"][parameters["data_width"]]
    lut_ram_coef = self.coef_width["LUT_RAM"][parameters["data_width"]]
    lut_sr_coef = self.coef_width["LUT_SR"][parameters["data_width"]]
    logic_lut_model = self.LUTLogic_model_width(parameters)
    lut_ram_model = self.LUTRAM_model_width(parameters)
    lut_sr_model = self.LUTSR_model_width(parameters)
    lut_rsc = int(np.dot(logic_lut_coef, logic_lut_model)) + \
      int(np.dot(lut_ram_coef, lut_ram_model)) + \
      int(np.dot(lut_sr_coef, lut_sr_model))
    return {
      "LUT": lut_rsc,
      "FF": self.FF_model(parameters),
      "DSP": self.DSP_model(parameters),
      "BRAM": self.BRAM_model(parameters)
    }

  def visualize_model_performance(self, plot=["LUT"]):
    for rsc in plot:
      if rsc == "LUT":
        fig, ax = plt.subplots(figsize=(10, 6))
        x = self.actual["Logic_LUT"] + self.actual["LUT_RAM"] + self.actual["LUT_SR"]
        ax.plot(x, x, label="actual")
        ax.set_title(rsc)
        ax.set_xlabel("actual")
        ax.set_ylabel("predicted")
        for w in width_TYPES:
          x = np.zeros(len(self.actual_width["Logic_LUT"][w]))
          y = np.zeros(len(self.actual_width["Logic_LUT"][w]))
          for lut_rsc in nnls_RSC_TYPES:
            x += self.actual_width[lut_rsc][w]
            y += self.results_width[lut_rsc][w]
          ax.scatter(x, y, label="predict: data_width={0}".format(w), marker="x")
          ax.legend()



