# Resource Modelling

For the fpgaConvNet project, it is necessary to improve on the current resource modelling. At the moment, only deterministic models exist for **BRAM** and **DSP** resources, however the **FF** and **LUT** resources are also significant for fpgaConvNet. 

In order to carry out resource modelling, firstly some empirical data must be gathered to fit what ever the model is to. An example for the `accum` module  would be running the following from the `runs` directory in the fpgaconvnet-hls repo:

```
python -m modules.accum.run_accum
```

This script continuously generates random configurations for the module and gets the resource utilisation after synthesis and implementation.

After collecting many reading, they can then be used to fit models for the module. The resource models are defined in the fpgaconvnet-optimiser repo within each module class, and is the `utilisation_model()` method in the class. This utilisation model requires coefficients to describe the weighting that each model parameter has on the total resources. This model is fitted using Non-Negative Least Squares regression (NNLS). To generate the model for the `accum` module, you can run the following

```
python -m modules.accum.model_accum
```
