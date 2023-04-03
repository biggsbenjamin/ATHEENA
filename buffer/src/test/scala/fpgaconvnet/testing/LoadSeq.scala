package fpgaconvnet.testing

import chisel3._
import scala.io._
import chisel3.experimental.FixedPoint
import scala.math._

object LoadSeq {

  /**
   *  Loads a single stream of values. Used in:
   *  - Accum
   */

  def load_single_stream(filepath: String): Seq[String] = {
    Source.fromFile(filepath).getLines.toSeq
  }

  def load_single_stream_fixed_point[T <: FixedPoint](gen: T, filepath: String): Seq[FixedPoint] = {
    val seq = load_single_stream(filepath)
    seq.map(_.toDouble).map(_.F(gen.binaryPoint))
  }

  def load_single_stream_int[T <: UInt](gen: T, filepath: String): Seq[UInt] = {
    val seq = load_single_stream(filepath)
    seq.map(_.toInt.U)
  }

  def load_single_stream_double(filepath: String): Seq[Double] = {
    val seq = load_single_stream(filepath)
    seq.map(_.toDouble)
  }

  /**
   *  Loads stream of values for kernel_size*kernel_size. Used in:
   *  - SlidingWindow
   *  - Pool
   */

  def load_kernel_kernel_stream(filepath: String,
        kernel_size_x: Int, kernel_size_y: Int): Array[Array[Seq[String]]] = {
    val stream  = Source.fromFile(filepath).getLines
    val seq = Array.ofDim[Seq[String]](kernel_size_x, kernel_size_y)
    for( i <- 0 to kernel_size_x - 1 ) {
      for( j <- 0 to kernel_size_y - 1 ) {
        seq(i)(j) = Seq[String]()
      }
    }
    while ( stream.hasNext ) {
      for( i <- 0 to kernel_size_x - 1 ) {
        for( j <- 0 to kernel_size_y - 1 ) {
          seq(i)(j) = seq(i)(j) :+ stream.next()
        }
      }
    }
    seq
  }

  def load_kernel_kernel_stream_fixed_point[T <: FixedPoint](gen: T,
        filepath: String, kernel_size: Int): Array[Array[Seq[FixedPoint]]] = {
    val seq = load_kernel_kernel_stream(filepath, kernel_size, kernel_size)
    seq.map(a => a.map(b => b.map(s => s.toDouble.F(gen.binaryPoint))))
  }

  def load_kernel_kernel_stream_double(filepath: String,
        kernel_size: Int): Array[Array[Seq[Double]]] = {
    val seq = load_kernel_kernel_stream(filepath, kernel_size, kernel_size)
    seq.map(a => a.map(b => b.map(s => s.toDouble)))
  }

  def load_kernel_kernel_stream_double(filepath: String,
        kernel_size_x: Int, kernel_size_y: Int): Array[Array[Seq[Double]]] = {
    val seq = load_kernel_kernel_stream(filepath, kernel_size_x, kernel_size_y)
    seq.map(a => a.map(b => b.map(s => s.toDouble)))
  }

  def load_kernel_kernel_stream_int[T <: UInt](gen: T,
        filepath: String, kernel_size: Int): Array[Array[Seq[UInt]]] = {
    val seq = load_kernel_kernel_stream(filepath, kernel_size, kernel_size)
    seq.map(a => a.map(b => b.map(s => s.toInt.U)))
  }

  /**
   *  Loads stream of values for kernel_size*kernel_size*kernel_size. Used in:
   *  - SlidingTensor
   */

  def load_kernel_kernel_kernel_stream(filepath: String,
        kernel_size_x: Int, kernel_size_y: Int,
        kernel_size_z: Int): Array[Array[Array[Seq[String]]]] = {
    val stream  = Source.fromFile(filepath).getLines
    val seq = Array.ofDim[Seq[String]](kernel_size_x, kernel_size_y, kernel_size_z)
    for( i <- 0 until kernel_size_x ) {
      for( j <- 0 until kernel_size_y ) {
        for( k <- 0 until kernel_size_z ) {
          seq(i)(j)(k) = Seq[String]()
        }
      }
    }
    while ( stream.hasNext ) {
      for( i <- 0 until kernel_size_x ) {
        for( j <- 0 until kernel_size_y ) {
          for( k <- 0 until kernel_size_z ) {
            seq(i)(j)(k) = seq(i)(j)(k) :+ stream.next()
          }
        }
      }
    }
    seq
  }

  def load_kernel_kernel_kernel_stream_double(filepath: String,
        kernel_size_x: Int, kernel_size_y: Int,
        kernel_size_z: Int): Array[Array[Array[Seq[Double]]]] = {
    val seq = load_kernel_kernel_kernel_stream(filepath,
      kernel_size_x, kernel_size_y, kernel_size_z)
    seq.map(_.map(_.map(_.map(_.toDouble))))
  }

  /**
   *  Loads stream of values for a parallel stream. Used in:
   *  - StreamAcc
   */

  def load_parallel_stream(filepath: String, streams: Int): Array[Seq[String]] = {
    val stream  = Source.fromFile(filepath).getLines
    val seq = Array.ofDim[Seq[String]](streams)
    for( i <- 0 to streams - 1 ) {
      seq(i) = Seq[String]()
    }
    while ( stream.hasNext ) {
      for( i <- 0 to streams - 1 ) {
        seq(i) = seq(i) :+ stream.next()
      }
    }
    seq
  }

  def load_parallel_stream_fixed_point[T <: FixedPoint](gen: T, filepath: String, streams: Int): Array[Seq[FixedPoint]] = {
    val seq = load_parallel_stream(filepath, streams)
    seq.map(a => a.map(s => s.toDouble.F(gen.binaryPoint)))
  }

  def load_parallel_stream_int[T <: UInt](gen: T, filepath: String, streams: Int): Array[Seq[UInt]] = {
    val seq = load_parallel_stream(filepath, streams)
    seq.map(a => a.map(s => s.toInt.U))
  }

  def load_parallel_stream_double(filepath: String, streams: Int): Array[Seq[Double]] = {
    val seq = load_parallel_stream(filepath, streams)
    seq.map(a => a.map(s => s.toDouble))
  }

   /**
   *  Loads stream of values for a*b. Used in:
   *  - Fork
   */
  def load_a_b_stream(filepath: String, a: Int, b: Int): Array[Array[Seq[String]]] = {
    val stream  = Source.fromFile(filepath).getLines
    val seq = Array.ofDim[Seq[String]](a,b)
    for( i <- 0 to a - 1 ) {
      for( j <- 0 to b - 1 ) {
        seq(i)(j) = Seq[String]()
      }
    }
    while ( stream.hasNext ) {
      for( i <- 0 to a - 1 ) {
        for( j <- 0 to b - 1 ) {
          seq(i)(j) = seq(i)(j) :+ stream.next()
        }
      }
    }
    seq
  }

  def load_a_b_stream_fixed_point[T <: FixedPoint](gen: T, filepath: String, a: Int, b: Int): Array[Array[Seq[FixedPoint]]] = {
    val seq = load_a_b_stream(filepath, a, b)
    seq.map(a => a.map(b => b.map(s => s.toDouble.F(gen.binaryPoint))))
  }

  def load_a_b_stream_double(filepath: String, a: Int, b: Int): Array[Array[Seq[Double]]] = {
    val seq = load_a_b_stream(filepath, a, b)
    seq.map(a => a.map(b => b.map(s => s.toDouble)))
  }

  def load_a_b_stream_int[T <: UInt](gen: T, filepath: String, a: Int, b: Int): Array[Array[Seq[UInt]]] = {
    val seq = load_a_b_stream(filepath, a, b)
    seq.map(a => a.map(b => b.map(s => s.toInt.U)))
  }

}
