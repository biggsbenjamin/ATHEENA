package fpgaconvnet.util

import chisel3._
import chisel3.util._

class AXIStreamIO[+T <: Data](gen: T) extends Bundle {

  val TREADY = Input(Bool())
  val TVALID = Output(Bool())
  val TLAST  = Output(Bool())
  val TDATA  = Output(gen)

}

object AXIStream
{
  /** Wraps some Data with a DecoupledIO interface. */
  def apply[T <: Data](gen: T): AXIStreamIO[T] = new AXIStreamIO(gen)
}
