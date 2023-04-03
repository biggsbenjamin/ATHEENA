package fpgaconvnet

import scala.io._

import org.json4s._
import org.json4s.JsonDSL._
import org.json4s.jackson.JsonMethods._

import chisel3._
import chisel3.experimental.FixedPoint

import fpgaconvnet.modules._
import fpgaconvnet.layers._

object Elaborate extends App {

  implicit val formats = DefaultFormats

  // chisel stage object
  val chisel_stage = new chisel3.stage.ChiselStage

  // match case for type of hardware
  args(0) match {

    // module
    case "module" => {

      // load the configuration
      val conf = parse(Source.fromFile(args(2))
        .getLines.mkString).extract[JObject]

      // generate hardware based on module
      args(1) match {

        case "fork" => {

          // get parameters
          val data_width = ( conf \ "data_width" ).extract[Int]
          val binary_point = ( conf \ "binary_point" ).extract[Int]
          val fine = ( conf \ "fine" ).extract[Int]
          val coarse = ( conf \ "coarse" ).extract[Int]

          // generate the hardware
          println("generating fork module ...")
          chisel_stage.emitVerilog(new ForkFixed(
            FixedPoint(data_width.W, binary_point.BP),
            fine, coarse), args)

        }
      }

    }

    case "layer" => {

      // load the configuration
      val conf = parse(Source.fromFile(args(2))
        .getLines.mkString).extract[JObject]

      // generate hardware based on layer
      args(1) match {


        case "conditional_buffer" => {

          // initialise conditional buffer parameters
          val hardware = conf.extract[ConditionalBufferConfig]

          // generate the hardware
          println("generating conditional buffer layer module ...")
          chisel_stage.emitVerilog(new ConditionalBufferTop(
            hardware.data_t.to_fixed(),
            UInt(8.W),
            UInt(hardware.sample_id_width.W),
            hardware.coarse,
            hardware.channels_in, 
            hardware.rows_in, 
            hardware.cols_in,
            hardware.batch_size,
            hardware.min_delay,
            hardware.drop_mode
          ), args)

        }


      }

    }

    case h => throw new Exception(s"${h} invalid hardware type")

  }

  // (new chisel3.stage.ChiselStage).emitVerilog(new $inst, args)
}
