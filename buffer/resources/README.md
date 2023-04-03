# Resource modelling for modules

## Resource runner
The resource runner runs Vivado synthesis for a module on a specified range of uniformly sampled design points and produce a resource usage and timing analysis report.

To begin resource runner for the `Accum` module, run the following command in this directory:
```
python modules.Accum.AccumFixed_runner.py
```
The resource report will be stored as `./results/AccumFixed/{design_point_params}/results.json` , and the generated verilog file will be stored in `./results/AccumFixed/{design_point_params}/impl/` folder.


## Resource model
The resource model uses linear regression to fit the `LUT` resources; deterministic models were used for `FF`, `DSP`, and `BRAM`. 
From `https://app.box.com/s/wg4de1owydlx2azg8og3brfx6uyl2gqn` download `results.zip` and unzip the content in the current directory. To predict resource usage, from the current directory, import and instantiate a resource model class:
```
from modules.Accum.AccumFixed_model import AccumFixed_model
accum = AccumFixed_model()
results = accum.get_rsc({
    "data_width": 16,
    "channels": 8,
    "filters": 16
})
accum.visualize_model_performance()
```

