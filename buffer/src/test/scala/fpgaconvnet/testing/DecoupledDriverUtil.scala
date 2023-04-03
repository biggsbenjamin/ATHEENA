package fpgaconvnet.testing

import chiseltest._
import chiseltest.iotesters._
import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint
import scala.io._

object DecoupledDriverUtil {

  implicit class DecoupledFlowDriver(x: ReadyValidIO[FixedPoint]) {

	def initSource(): this.type = {
	  x.valid.poke(false.B)
	  this
	}

	def setSourceClock(clock: Clock): this.type = {
	  ClockResolutionUtils.setClock(DecoupledFlowDriver.decoupledSourceKey, x, clock)
	  this
	}

	protected def getSourceClock: Clock = {
	  ClockResolutionUtils.getClock(
		DecoupledFlowDriver.decoupledSourceKey,
		x,
		x.ready.getSourceClock
	  ) // TODO: validate against bits/valid sink clocks
	}

    def enqueueSeq(data: Seq[Double], burst_size: Int = 1, wait_time: Int = 0): Unit = timescope {

      // reshape sequence into packets
      val packets = (0 until (data.size/burst_size).toInt).map(i =>
        data.slice(i*burst_size, data.size.min((i+1)*burst_size)) )

      // iterate over packets
      for(i <- 0 until (data.size/burst_size).ceil.toInt ) {
        // get the packet
        val packet = data.slice(i*burst_size, data.size.min((i+1)*burst_size))
        // run within thread
        // x.valid.poke(true.B)
        if( wait_time > 0 ) {
          fork.withRegion(Monitor) {
            // count clock cycles
            var cntr = packet.size
            // iterate over elements in the packet
            for( elt <- packet ) {
              // send bits
              x.valid.poke(true.B)
              x.bits.poke(elt)
              getSourceClock.step(1)
              // wait until ready
              while (x.ready.peek().litToBoolean == false) {
                getSourceClock.step(1)
                cntr += 1
              }
            }
            // send invalid signal
            x.valid.poke(false.B)
            for(_ <- (cntr-packet.size) until wait_time) {
              getSourceClock.step(1)
            }
          }.joinAndStep(getSourceClock)
        } else {
          for( elt <- packet ) {
            x.bits.poke(elt)
            x.valid.poke(true.B)
    	    fork.withRegion(Monitor) {
              while (x.ready.peek().litToBoolean == false) {
                getSourceClock.step(1)
              }
            }.joinAndStep(getSourceClock)
          }
        }
      }
    }

	// Sink (dequeue) functions

	 def initSink(): this.type = {
	   x.ready.poke(false.B)
	   this
	 }

	 def setSinkClock(clock: Clock): this.type = {
	   ClockResolutionUtils.setClock(DecoupledFlowDriver.decoupledSinkKey, x, clock)
	   this
	 }

	 protected def getSinkClock: Clock = {
	   ClockResolutionUtils.getClock(
	 	DecoupledFlowDriver.decoupledSinkKey,
	 	x,
	 	x.valid.getSourceClock
	   ) // TODO: validate against bits/valid sink clocks
	 }

	 // NOTE: this doesn't happen in the Monitor phase, unlike public functions
	 def waitForValid(): Unit = {
	   while (x.valid.peek().litToBoolean == false) {
	 	getSinkClock.step(1)
	   }
	 }

    def expectDequeueSeq(data: Seq[Double], burst_size: Int = 1, wait_time: Int = 0,
		tolerance: Double = 0.001): Unit = timescope {

      // reshape sequence into packets
      val packets = (0 until (data.size/burst_size).toInt).map(i =>
        data.slice(i*burst_size, data.size.min((i+1)*burst_size)) )

      // iterate over packets
      for(i <- 0 to (data.size/burst_size).ceil.toInt ) {
        // get the packet
        val packet = data.slice(i*burst_size, data.size.min((i+1)*burst_size))
        // run within thread
        if( wait_time > 0 ) {
          fork.withRegion(Monitor) {
            // count clock cycles
            var cntr = packet.size
            // iterate over elements in the packet
            for( elt <- packet ) {
              // send bits
              x.ready.poke(true.B)
              getSinkClock.step(1)
              // wait until ready
              while (x.valid.peek().litToBoolean == false) {
                getSinkClock.step(1)
                cntr += 1
              }
              // expect valid and correct bits
              x.valid.expect(true.B)
              x.bits.expect(elt, tolerance)

            }
            // send invalid signal
            x.ready.poke(false.B)
            for(_ <- (cntr-packet.size) until wait_time) {
              getSinkClock.step(1)
            }
          }.joinAndStep(getSinkClock)
        } else {
          for( elt <- packet ) {
            x.ready.poke(true.B)
            fork.withRegion(Monitor) {
              waitForValid()
              x.valid.expect(true.B)
              x.bits.expect(elt, tolerance)
            }.joinAndStep(getSinkClock)
          }
        }
      }
    }

  }

  object DecoupledFlowDriver {
    protected val decoupledSourceKey = new Object()
    protected val decoupledSinkKey = new Object()
  }

}



