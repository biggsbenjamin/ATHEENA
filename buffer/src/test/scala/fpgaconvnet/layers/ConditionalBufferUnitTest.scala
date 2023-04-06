package fpgaconvnet.layers.conditional_buffer_test

import org.scalatest.flatspec._

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

import chiseltest._

import fpgaconvnet.testing._
import fpgaconvnet.testing.DecoupledDriverUtil._

import fpgaconvnet.layers.{ConditionalBufferConfig, ConditionalBufferFixed}

trait ConditionalBufferBehaviour extends TestBehaviour[ConditionalBufferConfig] {

  this: AnyFlatSpec with ChiselScalatestTester =>

  def run_test (config: ConditionalBufferConfig, test_config: TestConfig,
    seq_in_data: Array[Seq[Double]],
    seq_in_id: Array[Seq[UInt]],
    seq_ctrl: Seq[Bool],
    seq_ctrl_id: Seq[UInt],
    seq_out_data: Array[Seq[Double]],
    seq_out_id: Array[Seq[UInt]]
  ){

    // useful constants
    val min_ctrl_delay = config.min_delay
    val flush_val = 6.9
    val flush_id = 65535.U
    val fm_size = (config.channels_in*config.rows_in*config.cols_in)/config.coarse
    val flush_count = (20*fm_size)
    val fval_seq = List.fill(flush_count)(flush_val)
    val fid_seq = List.fill(flush_count)(flush_id)

    val stall_delay = config.stall_delay

    it should s"be correct for ${test_config.description}" in {
      // create DUT instance
      test(new ConditionalBufferFixed(
        config.data_t.to_fixed(),
        UInt(8.W),
        UInt(config.sample_id_width.toInt.W),
        config.coarse,
        config.channels_in, config.rows_in, config.cols_in,
        config.batch_size,
        config.min_delay,
        config.drop_mode
      ) ) .withAnnotations(annotations) { c =>
        // fork over coarseness

        // module setup
        c.io.in(0).map(_.initSource().setSourceClock(c.clock))
        c.io.out(0).map(_.initSink().setSinkClock(c.clock))
        c.io.in_id(0).map(_.initSource().setSourceClock(c.clock))
        c.io.out_id(0).map(_.initSink().setSinkClock(c.clock))
        c.io.ctrl_drop.initSource().setSourceClock(c.clock) 
        c.io.ctrl_id.initSource().setSourceClock(c.clock) 

        // run test streams
        fork { // enqueue input
          val thread_in = fork( c.io.in(0)(0).enqueueSeq(seq_in_data(0)) )
          thread_in.fork(c.io.in_id(0)(0).enqueueSeq(seq_in_id(0)) )
          for( i <- 1 until config.coarse ) {
            thread_in.fork( c.io.in(0)(i).enqueueSeq(seq_in_data(i)) )
            thread_in.fork( c.io.in_id(0)(i).enqueueSeq(seq_in_id(i)) )
          }
          // ee ctrl intputs
          thread_in.fork{
            c.clock.step(min_ctrl_delay)
            c.io.ctrl_drop.enqueueSeq(seq_ctrl)
          }
          thread_in.fork{
            c.clock.step(min_ctrl_delay)
            c.io.ctrl_id.enqueueSeq(seq_ctrl_id)
          }
          thread_in.join()
        }.fork { // enqueue output
          val thread_out = fork{
            c.clock.step(stall_delay)
            c.io.out(0)(0).expectDequeueSeq(seq_out_data(0),
            tolerance=test_config.tolerance.getOrElse(0.01)) 
          }
          thread_out.fork{
            c.clock.step(stall_delay)
            c.io.out_id(0)(0).expectDequeueSeq(seq_out_id(0)) 
          }
          for( i <- 1 until config.coarse ) {
            thread_out.fork{
              c.clock.step(stall_delay)
              c.io.out(0)(i).expectDequeueSeq(seq_out_data(i),
              tolerance=test_config.tolerance.getOrElse(0.01))
            }
            thread_out.fork{
              c.clock.step(stall_delay)
              c.io.out_id(0)(i).expectDequeueSeq(seq_out_id(i))
            }
          }
          thread_out.join()
        }.join()

        // test flush output
        val flush_delay = 22 //arbitrary...
        fork {
          val flush_thread = fork{
            c.clock.step(flush_delay)
            c.io.out(0)(0).expectDequeueSeq(fval_seq,
                tolerance=100.0 ) 
          }
          flush_thread.fork{
            c.clock.step(flush_delay)
            c.io.out_id(0)(0).expectDequeueSeq(fid_seq) 
          }
          for( i <- 1 until config.coarse ) {
            flush_thread.fork{
              c.clock.step(flush_delay)
              c.io.out(0)(i).expectDequeueSeq(fval_seq,
              tolerance=100.0)
            }
            flush_thread.fork{
              c.clock.step(flush_delay)
              c.io.out_id(0)(i).expectDequeueSeq(fid_seq)
            }
          }
          flush_thread.join()
        }.join()

        c.clock.step(10) // for easy viewing of resulting signals
      }
    }
  }
}


abstract class ConditionalBufferBaseTest extends BaseTest[ConditionalBufferConfig] with ConditionalBufferBehaviour {

  // module identifier
  val module = "ConditionalBufferFixed"
  val test_path = "data/layers/conditional_buffer"

  // test parameters
  val basic_test_indices = List(0,1,2,3)
  val back_pressure_burst = 8
  val back_pressure_wait = 16
  val slow_burst = 8
  val slow_wait = 16

  // method to run test for a given configuration index
  def run_config_test(config: ConditionalBufferConfig,
  test_config: TestConfig, index: Int) = {

    // test constants for ease of use
    val fm_size = (config.rows_in).toInt * (config.cols_in).toInt * (config.channels_in.toInt)
    val bs = (config.batch_size).toInt
    val coarse = (config.coarse).toInt

    // generate sequences
    val seq_in_data = LoadSeq.load_parallel_stream_double(
      s"$test_path/test_$index/input.dat", coarse)
    // create the sample ID sequence
    val seq_in_id_list = List.tabulate(bs)(n => List.fill(fm_size)(n.U) ).flatten.toSeq
    val seq_in_id = Array.ofDim[Seq[UInt]](coarse)
    for( i <- 0 until coarse ) {
      seq_in_id(i) = Seq[UInt]()
    }
    var j=0
    while (j < seq_in_id_list.length) {
      for( i <- 0 until coarse ) {
        seq_in_id(i) = seq_in_id(i) :+ seq_in_id_list(j)
        j = j+1
      }
    }
    
    // load ctrl sequence FIXME: new func added, who knows if it works
    val seq_ctrl_string = LoadSeq.load_single_stream(
      s"$test_path/test_$index/ctrl_in.dat")
    val ctrl_mask = seq_ctrl_string.map(_.toInt)
    val seq_ctrl = ctrl_mask.map(_.B)
    val seq_ctrl_id = (0 until bs).map(_.U).toSeq

    // load test sequence out
    val seq_out_data = LoadSeq.load_parallel_stream_double(
      s"$test_path/test_$index/output.dat", coarse)
    // create sample id sequence - gate the output batches with drop_mode AND seq_ctrl
    val seq_out_id_tmp = if (config.drop_mode) {
      (0 until bs).toList.zip(ctrl_mask).collect { case (v, 0) => List.fill(fm_size)(v.U)}
    } else if (!config.drop_mode) {
      (0 until bs).toList.zip(ctrl_mask).collect { case (v, 1) => List.fill(fm_size)(v.U)}
    } else {
      ??? // something broke...
    }

    val seq_out_id_list = seq_out_id_tmp.flatten.toSeq
    //transform to coarse
    val seq_out_id = Array.ofDim[Seq[UInt]](coarse)
    for( i <- 0 until coarse ) {
      seq_out_id(i) = Seq[UInt]()
    }
    j=0
    while (j < seq_out_id_list.length) {
      for( i <- 0 until coarse ) {
        seq_out_id(i) = seq_out_id(i) :+ seq_out_id_list(j)
        j = j+1
      }
    }

    // run the actual test
    run_test(config, test_config,
      seq_in_data, seq_in_id,
      seq_ctrl, seq_ctrl_id,
      seq_out_data, seq_out_id
    )
  }
}

class AllConfigTest extends ConditionalBufferBaseTest { run_all_config_tests }
class BasicConfigTest extends ConditionalBufferBaseTest { run_basic_config_tests }
class BasicBackPressureConfigTest extends ConditionalBufferBaseTest { run_basic_config_back_pressure_tests }
class ConfigTest extends ConditionalBufferBaseTest { run_specific_config_test }
