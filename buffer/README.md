# Conditional Buffer (written in Chisel)

This repo contains an implementation of a backend for fpgaConvNet using [Chisel](https://github.com/chipsalliance/chisel3).

## Setup

Follow [Chisel's](https://github.com/chipsalliance/chisel3) instructions on setting up the chisel environment.

[Scala 2.12.13](https://www.scala-lang.org/download/2.12.13.html) is required. You may want to install using the [Coursier](https://docs.scala-lang.org/getting-started/index.html#using-the-scala-installer-recommended-way) tool.

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

## Buffer Generation

The current buffer generation is controlled by the `gen_buff.sh` script. Activate the buffer env and run the script to generate a large buffer using the example configurations.
Further example buffer generation configurations files can be found in `data`. Please look at this folder for examples of creating new configurations.
To generate test data, you can run:

To test individual configurations, you can run:

```
sbt "testOnly fpgaconvnet.layers.Conditional_Buffer_test.*"
```

## Verilog Generation

Once the design is verified using chisel's testbench setup, you can the start generating the verilog. This can be done using the `build_verilog.sh` script in the `scripts` folder. This script takes as an input the module to generate as well as the configuration for that module. The generated verilog appears in the `impl` folder.

Further to generating the hardware, you can also checkout the resource usage of the module using the `scripts/get_rsc_usage.tcl` vivado script. An example for the generated `Accum` module is as follows:

```
vivado -mode batch -notrace -source scripts/get_rsc_usage.tcl -tclargs ConditionalBufferFixed
```
