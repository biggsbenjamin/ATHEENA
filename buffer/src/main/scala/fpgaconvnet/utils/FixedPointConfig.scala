package fpgaconvnet.util

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

case class FixedPointConfig(width: Int, binary_point: Int) {

  def to_fixed(): FixedPoint = {
    FixedPoint(width.W, binary_point.BP)
  }
}
