package fpgaconvnet.testing

import scala.io._
import scala.collection.mutable.{Map,HashMap}

import org.json4s._
import org.json4s.jackson.JsonMethods._

object LoadParameters {

  def get_config_description(config_path: String): String = {
    // get config
    val config = parse(Source.fromFile(config_path).getLines.mkString)
    // get description
    val JString(description) = (config \ "description")
    description
  }

  def get_config_parameters(config_path: String): Map[String,Int] = {
    // get config
    implicit val formats = DefaultFormats
    val config = parse(Source.fromFile(config_path).getLines.mkString)
    // get all parameters
    val parameters_raw = config.extract[Map[String,Any]]
    // remove description
    parameters_raw -= "description"
    // map to integers
    val parameters = new HashMap[String,Int]
    parameters_raw.foreach {
      case (k,v) => {
        parameters += (k -> v.toString.toInt)
      }
    }
    parameters
  }

  def get_config_parameters_list(config_path: String): Map[String,List[Int]] = {
    // get config
    implicit val formats = DefaultFormats
    val config = parse(Source.fromFile(config_path).getLines.mkString)
    // get all parameters
    val parameters_raw = config.extract[Map[String,Any]]
    // remove description
    parameters_raw -= "description"
    // map to integers
    val parameters = new HashMap[String,List[Int]]
    parameters_raw.foreach {
      case (k,v) => {
        parameters += (k -> v.asInstanceOf[List[Any]].map(_.toString.toInt))
      }
    }
    parameters
  }
}
