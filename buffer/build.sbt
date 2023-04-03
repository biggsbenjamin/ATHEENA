// See README.md for license details.

ThisBuild / scalaVersion     := "2.12.13"
ThisBuild / version          := "0.1.0"
ThisBuild / organization     := "FCCM-artifact"

val chiselVersion = "3.5.5"
val chiselTestVersion = "0.5.5"

enablePlugins(PackPlugin)

lazy val root = (project in file("."))
  .settings(
    name := "fpgaconvnet-chisel",
    resolvers +=Resolver.sonatypeRepo("snapshots"),
    resolvers +=Resolver.mavenLocal,
    libraryDependencies ++= Seq(
      "edu.berkeley.cs" %% "chisel3" % chiselVersion,
      "edu.berkeley.cs" %% "chiseltest" % chiselTestVersion % "test",
      "edu.berkeley.cs" % "ip-contributions" % "0.5.0",
      "org.json4s" %% "json4s-jackson" % "3.6.0",
    ),
    scalacOptions ++= Seq(
      "-Xsource:2.11",
      "-language:reflectiveCalls",
      "-deprecation",
      "-feature",
      "-Xcheckinit"
    ),
    addCompilerPlugin("edu.berkeley.cs" % "chisel3-plugin" % chiselVersion cross CrossVersion.full),
    addCompilerPlugin("org.scalamacros" % "paradise" % "2.1.1" cross CrossVersion.full),
    classLoaderLayeringStrategy := ClassLoaderLayeringStrategy.Flat,
    updateOptions := updateOptions.value.withCachedResolution(true)
  )

mainClass in Compile := Some("fpgaconvnet.Elaborate")

