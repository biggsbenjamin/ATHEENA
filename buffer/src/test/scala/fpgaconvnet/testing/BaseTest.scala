package fpgaconvnet.testing

import java.io.File
import sys.process._
import scala.io._
import scala.util.matching.Regex

import org.json4s._
import org.json4s.JsonDSL._
import org.json4s.jackson.JsonMethods._

import org.scalatest._
import org.scalatest.flatspec._
import matchers.should._

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

import chiseltest.simulator.SimulatorDebugAnnotation

import chiseltest._
import chiseltest.simulator.{VerilatorCFlags, VerilatorFlags}

// test configuration case class
case class TestConfig(
  // test bench parameters
  description: String,
  valid_burst: Option[Int], valid_wait: Option[Int],
  ready_burst: Option[Int], ready_wait: Option[Int],
  tolerance: Option[Double],
)

trait TestBehaviour[T] {

  this: AnyFlatSpec with ChiselScalatestTester =>

  // module identifier
  val module: String
  val test_path: String

  // test parameters
  val basic_test_indices: List[Int]
  val back_pressure_burst: Int
  val back_pressure_wait: Int
  val slow_burst: Int
  val slow_wait: Int

  // testing annotations
  // val annotations = Seq(VerilatorBackendAnnotation, VerilatorCFlags(Seq("-std=c++0x")))
  //val annotations = Seq(VerilatorBackendAnnotation,
  //  WriteVcdAnnotation,VerilatorCFlags(Seq("-std=c++0x")))//,
  //  //VerilatorFlags(Seq("--trace-depth 2")))
  var annotations = Seq(VerilatorBackendAnnotation,
    WriteVcdAnnotation, VerilatorCFlags(Seq("-std=c++0x")))
  annotations :+ VerilatorFlags(Seq("--trace-depth", "1"))

  // method to generate fixed point type
  def get_fixed_point_type(w: Option[Int], bp: Option[Int],
      default_w: Int = 16, default_bp: Int = 8): FixedPoint = {

    // get the data width and binary point
    val data_width = w match {
      case Some(i) => i
      case _ => default_w
    }
    val binary_point = bp match {
      case Some(i) => i
      case _ => default_bp
    }

    // create the data type
	FixedPoint(data_width.W, binary_point.BP)

  }

  // method to run test for a given configuration index
  def run_config_test(config: T, test_config: TestConfig, index: Int)

}

// with ParallelTestExecution
abstract class BaseTest[T] extends AnyFlatSpec with TestBehaviour[T]
    with ChiselScalatestTester with Matchers  {

  implicit val formats = DefaultFormats

  // method to extract configuration from json
  def extract_config(config_path: String)(implicit m: Manifest[T]): T = {
    parse(Source.fromFile(config_path)
        .getLines.mkString)
        .extract[T]
  }

  // method to extract configuration from json
  def extract_test_config(config_path: String): TestConfig = {
    parse(Source.fromFile(config_path)
        .getLines.mkString)
        .extract[TestConfig]
  }

  // method to discover tests
  def discover_tests(dir: String): List[Int] = {

    // turn path to file
    val dir_file = new File(dir)

    // get all directories
    val dirs = dir_file.listFiles.toList
      .map(_.toString)
      .map(_.replace(s"${dir}/", ""))

    // extract test indices
    val test_index_pattern: Regex = """test\_(\d+)""".r
    dirs.map( x => { x match {
      case test_index_pattern(d) => d.toInt
      case _ => 0
    }})

  }

  // method to load config from test path
  def load_config(index: Int)(implicit m: Manifest[T]): T =
    extract_config(s"$test_path/test_$index/config.json")

  // method to load test config from test path
  def load_test_config(index: Int): TestConfig =
    extract_test_config(s"$test_path/test_$index/config.json")

  // all test indices
  def all_test_indices = discover_tests(test_path)

  // run all tests method
  def run_all_config_tests(implicit m: Manifest[T]) = {
    for( i <- all_test_indices ) {
      s"$module (Config: $i)" should behave like run_config_test(
        load_config(i), load_test_config(i), i)
    }
  }

  // run basic tests method
  def run_basic_config_tests(implicit m: Manifest[T]) = {
    for( i <- basic_test_indices ) {
      s"$module (Config: $i)" should behave like run_config_test(
        load_config(i), load_test_config(i), i)
    }
  }

  // run basic tests method with back pressure
  def run_basic_config_back_pressure_tests(implicit m: Manifest[T]) = {

    // run all tests
    for( i <- basic_test_indices ) {

      // load test config
      val test_config = load_test_config(i)

      // create backpressure in config
      val back_pressure_test_config = TestConfig(
        test_config.description,
        test_config.valid_burst, test_config.valid_wait,
        Some(back_pressure_burst), Some(back_pressure_wait),
        test_config.tolerance)

      // run the test
      s"$module (Config: $i)" should behave like run_config_test(
        load_config(i), back_pressure_test_config, i)
    }

  }

  // run basic tests method with slow input
  def run_basic_config_slow_tests(implicit m: Manifest[T]) = {

    // run all tests
    for( i <- basic_test_indices ) {

      // load test config
      val test_config = load_test_config(i)

      // create backpressure in config
      val back_pressure_test_config = TestConfig(
        test_config.description,
        Some(slow_burst), Some(slow_wait),
        test_config.ready_burst, test_config.ready_wait,
        test_config.tolerance)

      // run the test
      s"$module (Config: $i)" should behave like run_config_test(
        load_config(i), back_pressure_test_config, i)
    }

  }

  // run specific configuration
  def run_specific_config_test(implicit m: Manifest[T]) = {

    // get config from file (dirty workaround)
    val index = Source.fromFile("CONFIG_INDEX").getLines.mkString.toInt

    // run the test
    s"$module (Config: $index)" should behave like run_config_test(
      load_config(index), load_test_config(index), index)

  }

}

