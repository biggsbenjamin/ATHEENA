# ATHEENA Optimiser

This repo contains code for optimising the mapping a Early-Exit Convolutional Neural Network (CNN) model to an FPGA. Hardware-specific transforms are applied to the model, producing a hardware description that can be used by the hls backend. The generated architecture is streaming-based, and optimised for a specified hardware platform.

## Setup

The optimiser (and HLS generation) has been verified using the following software:

- `python=3.7`
- `miniconda=4.10.1`

To install this package, run from this directory the following:

```
sudo apt install protobuf-compiler libprotoc-dev
cd ./optimiser/
conda env create -f atheena_opt_hls_p37.yml
conda activate atheena_opt_hls_p37
python atheena_setup.py install 
```

## Optimiser Framework

The main tool is the optimisation script which generates an optimised hardware topology for a given model and platform. There are several components needed for this: a model of the hardware, transforms that map the model to the hardware and an optimisation scheme that chooses the best mapping.

```Shell
python -m fpgaconvnet_optimiser.tools.dev_script \
    --expr opt_brn \
    --save_name branchy_lenet \
    -o outputs/branchy_lenet \
    --model_path examples/models/atheena/branchy_lenet_20220902.onnx \
    --platform_path examples/platforms/zc706.json \
    --optimiser_path examples/optimiser_example.yml \
    -bs 1024
```

This will generate the following a series of json files describing the stages of the early-exit network under different resource utilisation contraints.

- `(output_path)/post_optim-rsc(P)p/report_(save_name)-ee(stage)-rsc(P)p-iter(I).json`: A report file containing estimations of usage and performance at `(P)` percent of the boards available resources, for `(stage)` of the network, for the `(I)th` iteration of the optimiser..
- `(output_path)/post_optim-rsc[P]p/(save_name)-ee(stage)-rsc(P)p-iter(I).json`: A hardware specification file containing estimations of usage and performance at `[P]` percent of the boards available resources, for `(stage)` of the network, for the `(I)th` iteration of the optimiser.

```Shell
python -m fpgaconvnet_optimiser.tools.dev_script \
    --expr gen_graph \
    --save_name branchy_lenet_graph \
    -o outputs/branchy_lenet/results/ \
    -i outputs/branchy_lenet/ \
    --profiled_probability 0.75 
```

Running the `gen_graph` experiment will generate a pareto front for the optimised combination of the networks as well as a list of the reports for each of the network stages so that the user can choose pairs of network stages on the pareto front.

- `(output_path)/combined_rpt_eefrac(PR).txt`: lists the pareto front combinations of network stages and their expected throughput and resource usage.

> **Note**: for a graph containing baseline results, specify the path using `-bi`.

### Merging optimised stages

Run the following command to perform a stage merge for all the results in the combined report.

```Shell
python -m fpgaconvnet_optimiser.tools.ee_stage_merger \
    -c outputs/branchy_lenet/results/combined_rpt_eefrac75.txt \
    -j outputs/branchy_lenet/ \
    -on branchy_lenet_merged \
    --output_path outputs/branchy_lenet/merged/
```

- `(output_path)/branchy_lenet_merged(resources and throughput).json`: the final hardware specification ready to be implemented using the HLS backend.

Copy this `.json` file into a folder in `hls/test/partitions/(example)/`.

For example: 
```
mkdir -p ../hls/test/partitions/branchy_lenet_eg

cp outputs/branchy_lenet/merged/branchy_lenet_merged_rsc80_thru95000.json ../hls/test/partitions/branchy_lenet_eg/
```

## Additional Information

### Modelling

In order to do the CNN to hardware mapping, a model of the hardware is needed. There are four levels of abstraction for the final hardware: modules, layers, partitions and network. At each level of abstraction, there is an associated performance and resource estimate so that the constraints for the optimiser can be obtained.

- __Module:__ These are the basic building blocks of the accelerator. The modules are the following:
  - Accum
  - Conv
  - Glue
  - SlidingWindow
  - Fork
  - Pool
  - Squeeze
- __EE Modules:__
  - Exponential
  - Buffer
  - Compare
  - ExitMerge
  - ReduceMax
  - SoftMaxSum
- __Layer:__ Layers are comprised of modules. They have the same functionality of the equivalent layers of the CNN model. The following layers are supported:
  - Convolution
  - Inner Product
  - Pooling
  - ReLU
- __EE Layers:__
  - Buffer
  - SoftMaxCmp
  - Split
  - ExitMerge

- __Partition:__ Partitions make up a sub-graph of the CNN model network. They are comprised of layers. A single partition fits on an FPGA at a time, and partitions are changed by reconfiguring the FPGA.
- __Network:__ This is the entire CNN model described through hardware. A network contains partitions and information on how to execute them.

### Transforms

In order to find the optimal mapping, transforms are used to manipulate the performance/resource trade-off of the hardware. The main transforms implemented currently are:

| Transform | Level | Description |
|-----------|:-----:|------------|
| Fine | Module | Defines the parallelism for the kernel x kernel dot product of the `conv` module. |
| Coarse | Layer | Input and output channel dimension parallelism of Layers. For a convolution layer, this is how filters are run in parallel. |

### Optimisation Schemes

Finally, optimisations schemes are used to explore the transform design space and find an optimal mapping for a given hardware platform. The optimisation schemes implemented are the following:

- __Simulated Annealing:__ Randomly chooses a transform and hardware component to change. The change is accepted based on a probability-based decision function.

---

