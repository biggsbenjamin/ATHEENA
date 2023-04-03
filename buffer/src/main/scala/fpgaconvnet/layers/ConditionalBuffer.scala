package fpgaconvnet.layers

import scala.reflect.ClassTag

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

import fpgaconvnet.util._
import fpgaconvnet.modules._

import chisel.lib.dclib._

case class ConditionalBufferConfig(
  coarse: Int, 
  channels_in: Int,
  rows_in: Int,
  cols_in: Int, 
  batch_size: Int,
  min_delay: Int, //value from optimiser
  drop_mode: Boolean, // true = drop on 1, false = drop on 0

  // data types
  data_t: FixedPointConfig,
  //ctrl_t: Bool, // not necessary really
  sample_id_width: Int = 16,

  // For testing
  stall_delay: Int = 0
) extends BaseLayerConfig {

  // input and output types
  val input_t: FixedPointConfig = data_t
  val output_t: FixedPointConfig = data_t

  // create module from the ration
  def toModule(): ConditionalBufferFixed = {
    // return module instance
    Module(new ConditionalBufferFixed(
          data_t.to_fixed(),
          UInt(8.W),
          UInt(sample_id_width.W),
          coarse,
          channels_in, 
          rows_in, 
          cols_in,
          batch_size,
          min_delay,
          drop_mode
        )
    )
  }
}


class ConditionalBufferIO(
  data_gen: FixedPoint, 
  ctrl_gen: UInt,   // 8bit
  id_gen: UInt,     // 16bit
  coarse: Int
) extends LayerIO(data_gen, data_gen, coarse, coarse) {
  // ID streams
  val in_id = Vec(1, Vec(coarse, Flipped(Decoupled(id_gen))))
  val out_id = Vec(1, Vec(coarse, Decoupled(id_gen)))

  val ctrl_id = Flipped(Decoupled(id_gen))
  // FIXME type will have to be different for intf w hls version
  val ctrl_drop   = Flipped(Decoupled(ctrl_gen))
}

class ConditionalBufferFixed(
  data_gen: FixedPoint,
  ctrl_gen: UInt,   // 8bit but only bool
  id_gen: UInt,     // 16bit
  coarse: Int,
  channels: Int, rows: Int, cols: Int,
  batch_size: Int,
  min_delay: Int, // value from the optimiser
  // vvv using the scala boolean as its not hw
  drop_mode: Boolean, // true = drop on 1, false = drop on 0 
  input_buffer_depth: Int = 2, output_buffer_depth: Int = 2
) extends Module {

  // create IO
  val io = IO(new ConditionalBufferIO(data_gen, ctrl_gen, id_gen, coarse))

  // input and output of layer
  val input = io.in(0) // zero here selects port number (only one)
  val output = io.out(0)
  val input_id = io.in_id(0)
  val output_id = io.out_id(0)
  // ctrl
  val ctrl_input = io.ctrl_drop
  val ctrl_input_id = io.ctrl_id

  val mod_chans = channels / coarse

  //////////////////////// create the modules ///////////////////////////
  // input buffers (data, id)
  val in_buffer = Array.fill(coarse)(
    Module(new Queue(data_gen, input_buffer_depth)).io)
  val in_id_buffer = Array.fill(coarse)(
    Module(new Queue(id_gen, input_buffer_depth)).io)
  val ctrl_buffer = Module(new Queue(ctrl_gen, input_buffer_depth)).io
  val ctrl_id_buffer = Module(new Queue(id_gen, input_buffer_depth)).io

  // fork module for control signals
  val no_fine = 1 //fine not needed in this case
  val ctrl_fork = Module(new ForkFixed_uint(ctrl_gen, no_fine, coarse))
  val ctrl_id_fork = Module(new ForkFixed_uint(id_gen, no_fine, coarse))

  // Cond Buffer module 
  val cond_buff = Array.fill(coarse)(
    Module(new CondBufferFixed(
      data_gen, Bool(), id_gen,
      mod_chans, rows, cols,
      batch_size, min_delay,
      drop_mode)
    ) )

  // output buffers (data, id)
  val out_buffer = Array.fill(coarse)(
    Module(new Queue(data_gen, output_buffer_depth)).io)
  val out_id_buffer = Array.fill(coarse)(
    Module(new Queue(id_gen, output_buffer_depth)).io)

  ///// connect modules /////
  // connect ctrl to fork input
  ctrl_buffer.enq <> ctrl_input
  ctrl_id_buffer.enq <> ctrl_input_id
  ctrl_fork.io.in(0) <> ctrl_buffer.deq
  ctrl_id_fork.io.in(0) <> ctrl_id_buffer.deq

  for( i <- 0 until coarse ) {
    // input to q connections
    in_buffer(i).enq <> input(i)
    in_id_buffer(i).enq <> input_id(i)
    //cond buff connections
    cond_buff(i).io.in <> in_buffer(i).deq    
    cond_buff(i).io.in_id <> in_id_buffer(i).deq    
    // connecting single bit of fork output
    cond_buff(i).io.ctrl_drop.valid := ctrl_fork.io.out(i)(0).valid
    cond_buff(i).io.ctrl_drop.bits := ctrl_fork.io.out(i)(0).bits(0)
    ctrl_fork.io.out(i)(0).ready := cond_buff(i).io.ctrl_drop.ready

    cond_buff(i).io.ctrl_id <> ctrl_id_fork.io.out(i)(0)
    out_buffer(i).enq <> cond_buff(i).io.out
    out_id_buffer(i).enq <> cond_buff(i).io.out_id
    // q to output connections
    output(i) <> out_buffer(i).deq
    output_id(i) <> out_id_buffer(i).deq
  }
}

// Top level module - for connecting layer via AXI-Stream
class ConditionalBufferTopIO(
  data_gen: FixedPoint, 
  ctrl_gen: UInt,   // 8bit
  id_gen: UInt,     // 16bit
  coarse: Int
) extends Bundle {
  // NO TLAST - tie off
  val in      = Vec(coarse, Flipped(AXIStream(data_gen).suggestName("NAME_GOES_HERE")))
  val in_id   = Vec(coarse, Flipped(AXIStream(id_gen)))
  val out     = Vec(coarse, AXIStream(data_gen))
  val out_id  = Vec(coarse, AXIStream(id_gen))
  // EE ctrl  
  val ctrl_drop = Flipped(AXIStream(ctrl_gen))
  val ctrl_id   = Flipped(AXIStream(id_gen))
  // NOT USED -FIXME might be needed in testing?
  //val ctrl    = AXILiteSlave()
}

class ConditionalBufferTop(
  data_gen: FixedPoint,
  ctrl_gen: UInt, // param? = UInt(8.W)// 8bit but only bool
  id_gen: UInt,   // 16bit
  coarse: Int,
  channels: Int, rows: Int, cols: Int,
  batch_size: Int,
  min_delay: Int, // value from the optimiser
  // vvv using the scala boolean as its not hw
  drop_mode: Boolean, // true = drop on 1, false = drop on 0 
  input_buffer_depth: Int = 2, output_buffer_depth: Int = 2
) extends Module {

  // create IO
  val io = IO(new ConditionalBufferTopIO(data_gen, ctrl_gen, id_gen, coarse))

  // create instance of Convolution Fixed
  val hw = Module( new ConditionalBufferFixed(
    data_gen, Bool(), id_gen,
    coarse,
    channels, rows, cols,
    batch_size,
    min_delay, drop_mode
  ) )

  // input and output for hw
  val hw_input = hw.io.in(0)
  val hw_input_id = hw.io.in_id(0)
  val hw_output = hw.io.out(0)
  val hw_output_id = hw.io.out_id(0)


  // connect IO
  for ( coarse_index <- 0 until coarse ) {
    hw_input(coarse_index).valid := io.in(coarse_index).TVALID
    hw_input(coarse_index).bits := io.in(coarse_index).TDATA
    io.in(coarse_index).TREADY := hw_input(coarse_index).ready
    // id conns
    hw_input_id(coarse_index).valid := io.in_id(coarse_index).TVALID
    hw_input_id(coarse_index).bits := io.in_id(coarse_index).TDATA
    io.in_id(coarse_index).TREADY := hw_input_id(coarse_index).ready
  }
  for ( coarse_index <- 0 until coarse ) {
    io.out(coarse_index).TVALID := hw_output(coarse_index).valid
    io.out(coarse_index).TDATA := hw_output(coarse_index).bits
    hw_output(coarse_index).ready := io.out(coarse_index).TREADY
    // id conns
    io.out_id(coarse_index).TVALID := hw_output_id(coarse_index).valid
    io.out_id(coarse_index).TDATA := hw_output_id(coarse_index).bits
    hw_output_id(coarse_index).ready := io.out_id(coarse_index).TREADY
  }
  // connect EE ctrl
  hw.io.ctrl_drop.valid := io.ctrl_drop.TVALID
  hw.io.ctrl_drop.bits := io.ctrl_drop.TDATA
  io.ctrl_drop.TREADY := hw.io.ctrl_drop.ready
  // ctrl id
  hw.io.ctrl_id.valid := io.ctrl_id.TVALID
  hw.io.ctrl_id.bits := io.ctrl_id.TDATA
  io.ctrl_id.TREADY := hw.io.ctrl_id.ready

  // Tie off TLAST signals as not required by HLS
  for (i <- 0 until coarse) {
    io.out(i).TLAST := false.B
    io.out_id(i).TLAST := false.B
  }
}
