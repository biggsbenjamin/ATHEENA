![build](https://github.com/AlexMontgomerie/fpgaconvnet-chisel/actions/workflows/integration-testing.yml/badge.svg)

# fpgaConvNet Chisel

This repo contains an implementation of a backend for fpgaConvNet using [Chisel](https://github.com/chipsalliance/chisel3).

## Setup

Follow [Chisel's](https://github.com/chipsalliance/chisel3) instructions on setting up the chisel environment.

[Scala 2.12.13](https://www.scala-lang.org/download/2.12.13.html) is required. You may want to install using the [Coursier](https://docs.scala-lang.org/getting-started/index.html#using-the-scala-installer-recommended-way) tool.

You will also need to setup fpgaConvNet for testing purposes. Instructions can be found [here](https://github.com/AlexMontgomerie/fpgaconvnet-optimiser).

Other than that, you will need to install and setup Vivado.

## Hardware Generation

First, the project needs to be regenerated. This can be done with the two
following commands:

```
sbt pack
```

Then the command-line interface for generating hardware can be used.

```
./target/pack/bin/elaborate <partition,layer,module> <hardware type> <configuration file path> --target-dir <output path>
```

## Testing

Test cases are generated from configuration files found in `data`. Please look at this folder for examples of creating new configurations.
To generate test data, you can run:

```
python scripts/generate_module_data.py -m (module name) -n (test case)
```

You can run all tests using:

```
sbt test
```

To test individual modules, you can run:

```
sbt "testOnly fpgaconvnet.modules.(module_name)_test.*"
```

## Debugging

Alongside testing, debugging can be a useful step in resolving problems with the hardware. My prefered method is to use a waveform viewer such as [gtkwave](http://gtkwave.sourceforge.net/). The waveforms can be found in the `test_run_dir` directory.

## Verilog Generation

Once the design is verified using chisel's testbench setup, you can the start generating the verilog. This can be done using the `build_verilog.sh` script in the `scripts` folder. This script takes as an input the module to generate as well as the configuration for that module. An example for generating the `Accum` module is as follows:

```
./scripts/build_verilog.sh accum data/accum/test_0/config.json
```

The generated verilog appears in the `impl` folder.

Further to generating the hardware, you can also checkout the resource usage of the module using the `scripts/get_rsc_usage.tcl` vivado script. An example for the generated `Accum` module is as follows:

```
vivado -mode batch -notrace -source scripts/get_rsc_usage.tcl -tclargs AccumFixed
```
## Simulation Latency

It is important that the hardware generated meets the performance requirements specified by the hardware models in the optimiser. To check that the latency in clock cycles for the simulation results, you can use the following script:

```
python scripts/get_clock_cycle.py
```

This script produces a table of all the test runs, and how many clock cycles they took. You can compare this to the latency of the models, found in the `reports` folder.
