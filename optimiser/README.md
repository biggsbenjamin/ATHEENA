# ATHEENA Optimiser

This repo contains code for optimising the mapping a Early-Exit Convolutional Neural Network (CNN) model to an FPGA. Hardware-specific transforms are applied to the model, producing a hardware description that can be used by the hls backend. The generated architecture is streaming-based, and optimised for a specified hardware platform.

## Setup

The following programs are required for the optimiser:

- `python=3.7`

To install this package, run from this directory the following:

```
sudo apt install protobuf-compiler libprotoc-dev
conda env create  -f atheena_opt_hls_p37.yml
conda activate ahteena_opt_hls_p37
python -m pip install atheena_setup.py
```

## Optimiser Framework

The main tool is the optimisation script which generates an optimised hardware topology for a given model and platform. There are several components needed for this: a model of the hardware, transforms that map the model to the hardware and an optimisation scheme that chooses the best mapping. These will be outlined later.
To use the optimiser, an example of running it using the `run_optimiser.py` script for VGG16 is as follows:

```Shell
python -m fpgaconvnet_optimiser --name vgg16 \
    --model_path examples/models/vgg16.onnx \
    --platform_path examples/platforms/zc706.json \
    --output_path outputs/vgg16 \
    --batch_size 256 \
    --objective throughput \
    --optimiser simulated_annealing \
    --optimiser_config_path examples/optimiser_example.yml
```

This will generate the following files:

- `(output_path)/(name).prototxt`: Hardware topology description for backend
- `(output_path)/report.json`: A report file containing estimations of usage and performance

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

