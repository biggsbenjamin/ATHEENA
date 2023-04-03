package fpgaconvnet.modules

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

import chisel.lib.dclib._
import fpgaconvnet.util._

class ForkIO(gen: FixedPoint, fine: Int, coarse: Int) extends Bundle {
  val in  = Vec(fine,Flipped(Decoupled(gen)))
  val out = Vec(coarse,Vec(fine,Decoupled(gen)))
}
class ForkIO_bool(gen: Bool, fine: Int, coarse: Int) extends Bundle {
  val in  = Vec(fine,Flipped(Decoupled(gen)))
  val out = Vec(coarse,Vec(fine,Decoupled(gen)))
}
class ForkIO_uint(gen: UInt, fine: Int, coarse: Int) extends Bundle {
  val in  = Vec(fine,Flipped(Decoupled(gen)))
  val out = Vec(coarse,Vec(fine,Decoupled(gen)))
}

class ForkFixed(gen: FixedPoint, fine: Int, coarse: Int,
      buffer_depth: Int = 2) extends Module {

  // assertitions
  require(fine >= 1, "fine needs to be larger than or equal to 1")
  require(coarse >= 1, "coarse needs to be larger than or equal to 1")

  // IO definition
  val io = IO(new ForkIO(gen,fine,coarse))

  if( coarse == 1 ) {

    for( j <- 0 until fine ) {
      io.out(0)(j) <> io.in(j)
    }

  } else {

    // create buffers
    val input_buffer = Array.fill(fine)(
      Module(new DCInput(gen)).suggestName("input_buffer").io)
    val output_buffer = Array.fill(coarse, fine)(
      Module(new DCOutput(gen)).suggestName("output_buffer").io)

    // syncronise all output streams
    val input_buffer_valid = input_buffer.map(_.deq.valid).reduce(_&_)
    val output_buffer_ready = output_buffer.flatten.map(_.enq.ready).reduce(_&_)

    for( j <- 0 until fine ) {
      // connect input buffer
      input_buffer(j).enq <> io.in(j)
      for( i <- 0 until coarse ) {
        // connect output buffer to output (with synchronisation)
        io.out(i)(j) <> output_buffer(i)(j).deq
        // connect output buffer to input
        output_buffer(i)(j).enq.bits := input_buffer(j).deq.bits
        output_buffer(i)(j).enq.valid := input_buffer_valid && output_buffer_ready
      }
      // connect ready signal
      input_buffer(j).deq.ready := output_buffer_ready &&
          (0 until fine)
            .map { x => if (x != j) input_buffer(x).deq.valid else true.B }
            .reduce(_&_)
    }

  }
}

// Alternative input type Fork modules (Bool, UInt)
class ForkFixed_bool(gen: Bool, fine: Int, coarse: Int,
      buffer_depth: Int = 2) extends Module {

  // assertitions
  require(fine >= 1, "fine needs to be larger than or equal to 1")
  require(coarse >= 1, "coarse needs to be larger than or equal to 1")

  // IO definition
  val io = IO(new ForkIO_bool(gen,fine,coarse))

  // create buffers
  val input_buffer = Array.fill(fine)(Module(new Queue(gen, 2))
    .suggestName("input_buffer").io)
  val output_buffer = Array.fill(coarse, fine)(Module(new Queue(gen, 2))
    .suggestName("output_buffer").io)

  // syncronise all output streams
  val input_buffer_valid = input_buffer.map(_.deq.valid).reduce(_&_)
  val output_buffer_ready = output_buffer.flatten.map(_.enq.ready).reduce(_&_)

  for( j <- 0 until fine ) {
    // connect input buffer
    input_buffer(j).enq <> io.in(j)
    for( i <- 0 until coarse ) {
      // connect output buffer to output (with synchronisation)
      io.out(i)(j) <> output_buffer(i)(j).deq
      // connect output buffer to input
      output_buffer(i)(j).enq.bits := input_buffer(j).deq.bits
      output_buffer(i)(j).enq.valid := input_buffer_valid && output_buffer_ready
    }
    // // connect ready signal
    // input_buffer(j).deq.ready := output_buffer_ready
    // connect ready signal
    input_buffer(j).deq.ready := output_buffer_ready &&
        (0 until fine)
          .map { x => if (x != j) input_buffer(x).deq.valid else true.B }
          .reduce(_&_)
  }
}

class ForkFixed_uint(gen: UInt, fine: Int, coarse: Int,
      buffer_depth: Int = 2) extends Module {

  // assertitions
  require(fine >= 1, "fine needs to be larger than or equal to 1")
  require(coarse >= 1, "coarse needs to be larger than or equal to 1")

  // IO definition
  val io = IO(new ForkIO_uint(gen,fine,coarse))

  // create buffers
  val input_buffer = Array.fill(fine)(Module(new Queue(gen, 2))
    .suggestName("input_buffer").io)
  val output_buffer = Array.fill(coarse, fine)(Module(new Queue(gen, 2))
    .suggestName("output_buffer").io)

  // syncronise all output streams
  val input_buffer_valid = input_buffer.map(_.deq.valid).reduce(_&_)
  val output_buffer_ready = output_buffer.flatten.map(_.enq.ready).reduce(_&_)

  for( j <- 0 until fine ) {
    // connect input buffer
    input_buffer(j).enq <> io.in(j)
    for( i <- 0 until coarse ) {
      // connect output buffer to output (with synchronisation)
      io.out(i)(j) <> output_buffer(i)(j).deq
      // connect output buffer to input
      output_buffer(i)(j).enq.bits := input_buffer(j).deq.bits
      output_buffer(i)(j).enq.valid := input_buffer_valid && output_buffer_ready
    }
    // // connect ready signal
    // input_buffer(j).deq.ready := output_buffer_ready
    // connect ready signal
    input_buffer(j).deq.ready := output_buffer_ready &&
        (0 until fine)
          .map { x => if (x != j) input_buffer(x).deq.valid else true.B }
          .reduce(_&_)
  }
}
