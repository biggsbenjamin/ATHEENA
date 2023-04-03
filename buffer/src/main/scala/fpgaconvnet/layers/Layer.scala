package fpgaconvnet.layers

import scala.io._

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

import fpgaconvnet.util._

abstract class BaseLayerConfig() {

  val input_t: FixedPointConfig
  val output_t: FixedPointConfig

}

case class BaseLayerParameter(
  buffer_depth: Int, batch_size: Int,
  // dimensions in
  rows_in: List[Int], cols_in: List[Int], channels_in: List[Int],
  // dimensions out
  rows_out: List[Int], cols_out: List[Int], channels_out: List[Int],
  // coarse factors
  coarse_in: Int, coarse_out: Int,
  // data types
  input_width: Option[Int], output_width: Option[Int],
  // optional types (convolution, inner product)
  data_width: Option[Int], weight_width: Option[Int],
  acc_width: Option[Int], biases_width: Option[Int],
  // optional coarse parameters
  coarse: Option[Int], coarse_group: Option[Int],
  // optional convolution and pooling parameters
  kernel_size: Option[List[Int]],
  stride: Option[List[Int]], fine: Option[Int],
  // optional padding parameters
  pad_top: Option[Int], pad_right: Option[Int],
  pad_bottom: Option[Int], pad_left: Option[Int],
  // multi-port parameters
  ports_in: Option[Int], ports_out: Option[Int],
)

// class LayerIO(input_t: FixedPoint, output_t: FixedPoint,
//     coarse_in: Int, coarse_out: Int, ports_in: Option[Int] = None,
//     ports_out: Option[Int] = None) extends Bundle {

//   // generate for ports in
//   val in = if(ports_in.isDefined) Vec(ports_in.getOrElse(1),
//       Vec(coarse_in, Flipped(Decoupled(input_t)))) else
//       Vec(coarse_in, Flipped(Decoupled(input_t)))

//   // val in = ports_in.isDefined match {
//   //   case true => Vec(ports_in.get, Vec(coarse_in, Flipped(Decoupled(input_t))))
//   //   case false => Vec(coarse_in, Flipped(Decoupled(input_t)))
//   // }

//   // generate for ports out
//   val out = if(ports_out.isDefined) Vec(ports_out.getOrElse(1),
//     Vec(coarse_out, Decoupled(output_t))) else
//     Vec(coarse_out, Decoupled(output_t))

//   // val out = ports_out.isDefined match {
//   //   case true => Vec(ports_out.get, Vec(coarse_out, Decoupled(output_t)))
//   //   case false => Vec(coarse_out, Decoupled(output_t))
//   // }

// }

class LayerIO(input_t: FixedPoint, output_t: FixedPoint,
    coarse_in: Int, coarse_out: Int, ports_in: Int = 1,
    ports_out: Int = 1) extends Bundle {

  // interface definition
  val in = Vec(ports_in, Vec(coarse_in, Flipped(Decoupled(input_t))))
  val out = Vec(ports_out, Vec(coarse_out, Decoupled(output_t)))

}
