package fpgaconvnet.modules.condbuffer_test

// from chiseltest github
import chisel3._
import chiseltest._
import org.scalatest.flatspec.AnyFlatSpec

// from other fcn tests

import chisel3.util._
import chisel3.experimental.FixedPoint
import fpgaconvnet.testing._
import fpgaconvnet.testing.DecoupledDriverUtil._
// import the DUT
import fpgaconvnet.modules.CondBufferFixed

// test configuration case class - from other fcn tests
case class CondBufferConfig(
  // parameters
  channels: Int, rows: Int, cols: Int,
  batch_size: Int,
  min_delay: Int, //value from optimiser
  drop_mode: Boolean, // true = drop on 1, false = drop on 0

  // data types
  data_width: Option[Int], binary_point: Option[Int],
  sample_id_width: Int,
  stall_delay: Int = 0
)


// actual test thing - FIXME what are traits???

trait CondBufferBehaviour extends TestBehaviour[CondBufferConfig] {
  // vvv chisel test boilerplate
  this: AnyFlatSpec with ChiselScalatestTester =>

  def run_test (config: CondBufferConfig, test_config: TestConfig,
    seq_in_data: Seq[Double],
    //seq_in_id: Seq[Double],
    seq_in_id: Seq[UInt],
    //seq_ctrl: Seq[Double],
    seq_ctrl: Seq[Bool],
    //seq_ctrl_id: Seq[Double],
    seq_ctrl_id: Seq[UInt],
    seq_out_data: Seq[Double],
    //seq_out_id: Seq[Double]
    seq_out_id: Seq[UInt]
    ){ // double prec+tolerance

    // create the data type
    val fxp_data_type = get_fixed_point_type(
      config.data_width, config.binary_point)
    val samp_id_type = UInt(config.sample_id_width.W) 
    val ctrl_type = Bool()

    val min_ctrl_delay = config.min_delay

    val flush_val = 6.9
    val flush_id = 65535.U
    val flush_count = (20*config.channels*config.rows*config.cols)
    val fval_seq = List.fill(flush_count)(flush_val)
    val fid_seq = List.fill(flush_count)(flush_id)

    val stall_delay = config.stall_delay

    it should s"be correct for ${test_config.description}" in {

      // create DUT instance
      test(new CondBufferFixed(
        fxp_data_type,
        ctrl_type,
        samp_id_type,
        config.channels, config.rows, config.cols,
        config.batch_size,
        config.min_delay,
        config.drop_mode
      ) ) .withAnnotations(annotations) { c =>

        // module setup
        c.io.in.initSource().setSourceClock(c.clock)
        c.io.in_id.initSource().setSourceClock(c.clock)
        c.io.ctrl_drop.initSource().setSourceClock(c.clock)
        c.io.ctrl_id.initSource().setSourceClock(c.clock)
        c.io.out.initSink().setSinkClock(c.clock)
        c.io.out_id.initSink().setSinkClock(c.clock)

        // run test streams
        // FIXME be nice to change this to forks and joins for my brain
        // NOTE: pull from test config but if None(equiv) then use default from getOrElse()
        fork { // data streams in
          c.io.in.enqueueSeq(seq_in_data,
              burst_size=test_config.valid_burst.getOrElse(1),
              wait_time=test_config.valid_wait.getOrElse(0)
              ) 
        }.fork {
          c.io.in_id.enqueueSeq(seq_in_id,
              //burst_size=test_config.valid_burst.getOrElse(1),
              //wait_time=test_config.valid_wait.getOrElse(0)
              ) 
        }.fork { // ctrl streams in
          c.clock.step(min_ctrl_delay)
          c.io.ctrl_drop.enqueueSeq(seq_ctrl,
              //burst_size=test_config.valid_burst.getOrElse(1),
              //wait_time=test_config.valid_wait.getOrElse(0)
              ) 
        }.fork {
          c.clock.step(min_ctrl_delay)
          c.io.ctrl_id.enqueueSeq(seq_ctrl_id,
              //burst_size=test_config.valid_burst.getOrElse(1),
              //wait_time=test_config.valid_wait.getOrElse(0)
              )
        }.fork { // data streams out
          // split the sequence
          val (s0, s1) = seq_out_data.splitAt(seq_out_data.length / 7)
          c.clock.step(stall_delay)
          c.io.out.expectDequeueSeq(s0,
              burst_size=test_config.ready_burst.getOrElse(1),
              wait_time=test_config.ready_wait.getOrElse(0),
              tolerance=test_config.tolerance.getOrElse(0.01)
              )
          c.io.out.expectDequeueSeq(s1,
              burst_size=test_config.ready_burst.getOrElse(1),
              wait_time=test_config.ready_wait.getOrElse(0),
              tolerance=test_config.tolerance.getOrElse(0.01)
              )
        }.fork {
          c.clock.step(stall_delay)
          val (s0_id, s1_id) = seq_out_id.splitAt(seq_out_id.length / 7)
          c.io.out_id.expectDequeueSeq(s0_id) 
          c.io.out_id.expectDequeueSeq(s1_id) 
        }.join()

        // flush mode
        fork {
          c.clock.step(22)
          c.io.out.expectDequeueSeq(fval_seq,
              burst_size=test_config.ready_burst.getOrElse(1),
              wait_time=test_config.ready_wait.getOrElse(0),
              tolerance=100.0
              ) 
        }.fork {
          c.clock.step(22)
          c.io.out_id.expectDequeueSeq(fid_seq,
              //burst_size=test_config.ready_burst.getOrElse(1),
              //wait_time=test_config.ready_wait.getOrElse(0),
              //tolerance=test_config.tolerance.getOrElse(0.0)
              ) 
        }.join()

        c.clock.step(10) // for easy viewing of resulting signals

      }
    }
  }
}

abstract class CondBufferBaseTest extends BaseTest[CondBufferConfig] with CondBufferBehaviour {

  // module identifier
  val module = "CondBufferFixed"
  val test_path = "data/modules/cond_buffer"

  // test parameters
  val basic_test_indices = List(0,1,2,3)
  val back_pressure_burst = 8
  val back_pressure_wait = 16
  val slow_burst = 8
  val slow_wait = 16

  // method to run test for a given configuration index
  def run_config_test(config: CondBufferConfig,
      test_config: TestConfig, index: Int) = {

    // test constants for ease of use
    val fm_size = (config.rows).toInt * (config.cols).toInt * (config.channels.toInt)
    val bs = (config.batch_size).toInt

    // load test sequence in
    val seq_in_data = LoadSeq.load_single_stream_double(
      s"$test_path/test_$index/input.dat")
    // create the sample ID sequence
    val seq_in_id_tmp = List.tabulate(bs)(n => List.fill(fm_size)(n.U) )
    // flattening the list, changing to sequence (list/vec wrapper anyway)
    val seq_in_id = seq_in_id_tmp.flatten.toSeq 

    // load ctrl sequence FIXME: new func added, who knows if it works
    val seq_ctrl_string = LoadSeq.load_single_stream(
      s"$test_path/test_$index/ctrl_in.dat")
    val ctrl_mask = seq_ctrl_string.map(_.toInt)
    val seq_ctrl = ctrl_mask.map(_.B)
    //val seq_ctrl = LoadSeq.load_single_stream_double(
    //  s"$test_path/test_$index/ctrl_in.dat")
    // create ctrl id test sequence
    val seq_ctrl_id = (0 until bs).map(_.U).toSeq

    // load test sequence out
    val seq_out_data = LoadSeq.load_single_stream_double(
      s"$test_path/test_$index/output.dat")
    // create sample id sequence - gate the output batches with drop_mode AND seq_ctrl
    val seq_out_id_tmp = if (config.drop_mode) {
      (0 until bs).toList.zip(ctrl_mask).collect { case (v, 0) => List.fill(fm_size)(v.U)}
    } else if (!config.drop_mode) {
      (0 until bs).toList.zip(ctrl_mask).collect { case (v, 1) => List.fill(fm_size)(v.U)}
    } else {
      ??? // something broke...
    }
    val seq_out_id = seq_out_id_tmp.flatten.toSeq

    // execute the test
    run_test(config, test_config,
      seq_in_data, seq_in_id,
      seq_ctrl, seq_ctrl_id,
      seq_out_data, seq_out_id)

  }
}

// FIXME check which of these is run by default...
class AllConfigTest extends CondBufferBaseTest { run_all_config_tests }
class BasicConfigTest extends CondBufferBaseTest { run_basic_config_tests }
class BasicBackPressureConfigTest extends CondBufferBaseTest { run_basic_config_back_pressure_tests }
class ConfigTest extends CondBufferBaseTest { run_specific_config_test }
