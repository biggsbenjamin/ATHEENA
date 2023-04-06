# Conditional Buffer (written in Chisel)

A chisel project used to generate the hardware conditional buffer layers for ATHEENA.

## Setup

This module has been verified working for Ubuntu 20.04.6 LTS, Java version 11.0.18, sbt version 1.4.9, [Scala 2.12.13](https://www.scala-lang.org/download/2.12.13.html)

The following instructions are taken from [Chisel's](https://github.com/chipsalliance/chisel3) instructions on environment setup:

1. Install [Coursier](https://docs.scala-lang.org/getting-started/index.html#using-the-scala-installer-recommended-way) and follow the instructions.

```
curl -fL https://github.com/coursier/coursier/releases/latest/download/cs-x86_64-pc-linux.gz | gzip -d > cs && chmod +x cs 

./cs setup
```

> **Note**: This will install the most recent version of scala. To check it has worked, run `scala -version` (a restart of the terminal maybe required).

2. Install Scala version 2.12.13 and sbt version 1.4.9

```
cs install scala:2.12.13 && cs install scalac:2.12.13

cs install sbt:1.4.9 && cs install sbtn:1.4.9
```
> **Note**: To check the scala and sbt versions, run `scala -version` and `sbt --script-version`.

Other than that, you will need to install and setup Vivado 2019.1 (as instructed in the HLS folder).

## Hardware Generation

First, the project needs to be regenerated. This can be done with the two
following commands:

```
sbt pack
```

Then the command-line interface for generating hardware can be used.

```
./target/pack/bin/elaborate <layer,module> <hardware type> <configuration file path> --target-dir <output path> \
--emission-options=disableMemRandomization,disableRegisterRandomization
```

For example:
```
./target/pack/bin/elaborate layer conditional_buffer ./data/layers/conditional_buffer/test_0/config.json --target-dir ./impl \
--emission-options=disableMemRandomization,disableRegisterRandomization
```

## Buffer Generation

The current buffer generation is simplified by the `./gen_buff.sh` script. 

Activate the ATHEENA optimiser environment and run the script to generate a buffer using the example configurations based on the resource point. 

Be sure to run this *before* HLS backend is run.

Further example buffer generation configurations files can be found in `data/layers/conditional_buffer/test_*`. Please look at this folder for examples of creating new configurations.

> **Note**: Testing of the buffer module is not included as an artifact for this paper. However tests 0, 1, 2, and 3 come with input and output data for verification.
> To test these configurations you can run: `sbt "testOnly fpgaconvnet.layers.conditional_buffer_test.BasicConfigTest"` and view the results in `test_run_dir`.

## Verilog Generation

Once the design is verified using chisel's testbench setup, you can the start generating the verilog. This can be done using the `build_verilog.sh` script in the `scripts` folder. This script takes as an input the module to generate as well as the configuration for that module. The generated verilog appears in the `impl` folder.

Further to generating the hardware, you can also checkout the resource usage of the module using the `scripts/get_rsc_usage.tcl` vivado script. An example for the generated `Accum` module is as follows:

```
vivado -mode batch -notrace -source scripts/get_rsc_usage.tcl -tclargs ConditionalBufferFixed
```
