package fpgaconvnet.modules

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint
import chisel3.experimental.ChiselEnum

import chisel.lib.dclib._

class SinglePortRAM(size: Int = 1, width: Int = 32) extends Module {
  val addrWidth = chiselTypeOf((size).U)
  val io = IO(new Bundle {
    val addrIn = Input(addrWidth)
    val addrOut = Input(addrWidth)
    val dataIn1 = Input(FixedPoint(16.W, 8.BP))
    val en1 = Input(Bool())
    val we1 = Input(Bool())
    val dataOut1 = Output(FixedPoint(16.W, 8.BP))
  })

  val mem = SyncReadMem(size, FixedPoint(16.W, 8.BP))
  when (io.we1) {
    mem.write(io.addrIn, io.dataIn1)
  }
  io.dataOut1 := mem.read(io.addrOut, io.en1)
}

class CondBufferIO(
  data_gen: FixedPoint,
  ctrl_gen: Bool,   // 8bit
  id_gen: UInt      // 16bit
) extends Bundle {
  // data streams
  val in  = Flipped(Decoupled(data_gen))
  val out = Decoupled(data_gen)

  // ID streams
  val in_id   = Flipped(Decoupled(id_gen))
  val ctrl_id = Flipped(Decoupled(id_gen))
  val out_id  = Decoupled(id_gen)

  // FIXME type will have to be different for intf w hls version
  val ctrl_drop   = Flipped(Decoupled(ctrl_gen))
}

// FIXME get rid of batch size as a param, possible with no flush
class CondBufferFixed(
  data_gen: FixedPoint,
  ctrl_gen: Bool,   // 8bit but only bool
  id_gen: UInt,     // 16bit
  channels: Int, rows: Int, cols: Int,
  batch_size: Int,
  min_delay: Int, // value from the optimiser
  // vvv using the scala boolean as its not hw
  drop_mode: Boolean // true = drop on 1, false = drop on 0 
) extends Module {

  // IO def
  val io = IO(new CondBufferIO(data_gen,ctrl_gen,id_gen))

  // Helpful constant sizes
  val fm_size = rows*cols*channels
  // minimum delay from model - cycle latency for cond signal
  val min_fm = (min_delay.toFloat / fm_size).ceil.toInt
  // total number of values to be stored at min fm size
  val min_depth = min_fm*fm_size
  // only store up to the batch if smaller
  val ram_depth = (min_depth+(16*fm_size)).min(batch_size*fm_size)

  // input and output data buffers - default size 2
  val ip_buf = Module(new Queue(data_gen, 2, useSyncReadMem=true))
  val ip_id_buf = Module(new Queue(id_gen, 2, useSyncReadMem=true))
  val op_buf = Module(new Queue(data_gen, 2, useSyncReadMem=true))
  val op_id_buf = Module(new Queue(id_gen, 2, useSyncReadMem=true))
  // control data buffer - default size is batch 
  val ctrl_buf = Module(new Queue(ctrl_gen, batch_size, useSyncReadMem=true))
  val ctrl_id_buf = Module(new Queue(id_gen, batch_size, useSyncReadMem=true))

  // connect input to Qs in
  ip_buf.io.enq <> io.in
  ctrl_buf.io.enq <> io.ctrl_drop
  ip_id_buf.io.enq <> io.in_id
  ctrl_id_buf.io.enq <> io.ctrl_id

  // instantiate data ram (one big ram)
  // NOTE using same writefirst option as q - unsure of operation
  //val one_big_ram = SyncReadMem(ram_depth, data_gen, SyncReadMem.WriteFirst)
  val tmp_ram = Module(new SinglePortRAM(ram_depth, 16))
  // ctrl variables for ram
  val wr_ptr      = RegInit(0.U((log2Ceil(ram_depth+1)).W))
  val rd_ptr      = RegInit(0.U((log2Ceil(ram_depth+1)).W))
  // fm_in, fm_out - counts up to fm size
  val fm_in       = Counter(fm_size)
  val fm_out      = Counter(fm_size)
  // batch counters (in vs out) - before flush
  val b_count_in  = Counter(batch_size+1)
  val b_count_out = Counter(batch_size+1)

  // Using queue backpressure implementation
  val maybe_full = RegInit(false.B)
  val ptr_match = wr_ptr === rd_ptr
  val ram_empty = ptr_match && !maybe_full
  val ram_full = ptr_match && maybe_full
  // indicates both ready and valid for the ports are high
  val str_in      = WireDefault(ip_buf.io.deq.fire)
  val str_in_id   = WireDefault(ip_id_buf.io.deq.fire)
  val str_ctrl    = WireDefault(ctrl_buf.io.deq.fire)
  val str_ctrl_id = WireDefault(ctrl_id_buf.io.deq.fire)
  val rd_out      = WireDefault(op_buf.io.enq.fire) // should really be && with ID
  
  // more control signals
  val data_id_sink  = Reg(id_gen)
  val curr_ctrl     = RegInit(true.B)
  val curr_ctrl_id  = Reg(id_gen)
  val ctrl_avail = ctrl_buf.io.deq.valid && ctrl_id_buf.io.deq.valid

  // TERMINATION flags
  val b_in_done = WireDefault(b_count_in.value === batch_size.U)
  val b_out_done = WireDefault(b_count_out.value === batch_size.U)

  val flush_flag = RegInit(false.B)
  // flushing the stages post buffer
  when(ram_empty && !ctrl_avail && b_in_done && b_out_done) { flush_flag := true.B}

  /////////////////////// getting control info ////////////////////////
  val ctrl_lock = RegInit(false.B)
  // ctrl input registering - do only on fm_out == 0
  when(str_ctrl){ //when ready,valid fire...
    when(fm_out.value === 0.U) {
      if (drop_mode) {
        // FIXME check this is the right way round compared to the HLS buffer
        // also switch the operation of ctrl to true = drop rather than false = drop as is currently
        curr_ctrl := !ctrl_buf.io.deq.bits
      } else {
        curr_ctrl := (ctrl_buf.io.deq.bits)
      }
      curr_ctrl_id := ctrl_id_buf.io.deq.bits 
      ctrl_lock := true.B
    }
  }

  /////////////////////// writing to data RAM ////////////////////////
  when(str_in){
    // not necessary every time but less logic 
    //one_big_ram(wr_ptr) := ip_buf.io.deq.bits
    // increment write pointer
    when(wr_ptr +& 1.U === ram_depth.U) {
      // wrap, last value reached
      wr_ptr := 0.U
    } .otherwise {
      wr_ptr := wr_ptr + 1.U
    }
    // increment fm in counter
    when(fm_in.inc() ) {
      b_count_in.inc()
    }
  }
  // Get the input ID for the data, just a sink
  when(str_in_id){
    data_id_sink := ip_id_buf.io.deq.bits
  }
  
  // FIXME: a little too strict
  // Might need to depend on drop/pass thru
  // Drop logic sets low to allow flush op
  when(str_in =/= rd_out) {
    maybe_full := str_in
  }

  ////////////////// conditional read out data RAM ///////////////////
  // pass through operation
  //when(rd_out && read_out_states ){ //FIXME check not needed 
  when(!flush_flag){
    when(rd_out){
      // increment write pointer
      when(rd_ptr + 1.U === ram_depth.U) {
        // wrap, last value reached
        rd_ptr := 0.U
      } .otherwise {
        rd_ptr := rd_ptr + 1.U
      }
      // increment fm out counter
      when(fm_out.inc()) {
        b_count_out.inc()
        // reset ctrl lock to get new ctrl info
        ctrl_lock := false.B
      }
    }
    // rd_out dependent on curr ctrl so cannont happen at the same time
    // needs to be dependent on lock or it will miss IDs
    when(!curr_ctrl && ctrl_lock &&
        // vvv  read in one extra batch than read out
      (b_count_in.value > b_count_out.value || 
        ( (b_count_in.value === b_count_out.value) 
          && (fm_in.value + 1.U > fm_size.U) ) 
        // ^^^  b read out has caught up to b read in,
        // fm read in is just about to wrap/finish reading in batch 
      ) ) {
      // initiate read out skip, wrap, last value reached
      //when(rd_ptr+fm_size.U >= ram_depth.U) { //FIXME check not needed
      //  rd_ptr := (rd_ptr +& fm_size.U) - ram_depth.U
      when(rd_ptr + fm_size.U === ram_depth.U) {
        rd_ptr := 0.U // max ptr is multiple of fm size, no remainder
      } .otherwise {
        rd_ptr := rd_ptr + fm_size.U
      }
      // reset fm_out counter
      fm_out.reset()
      // move on to next batch
      b_count_out.inc()
      // reset ctrl lock to get new ctrl info
      ctrl_lock := false.B
      // maybe full can't be true here...
      maybe_full := false.B
    }
  }
  // ONLY read new when reading new data
  ip_buf.io.deq.ready := !ram_full
  ip_id_buf.io.deq.ready := !ram_full 

  // ready signal for deq-ing of ctrl and id
  // LOGIC: fm_in==? fm_out=0 <- means 
  // finished with outputting current id,
  // loading ctrl is latched for fm_size read outs or drop 
  val get_ctrl = (fm_out.value === 0.U) && !ctrl_lock
  ctrl_buf.io.deq.ready := get_ctrl
  ctrl_id_buf.io.deq.ready := get_ctrl

  // str_out.enq.ready controlled by op queue
  val write_out_valid = !ram_empty && curr_ctrl && ctrl_lock
  op_buf.io.enq.valid := write_out_valid
  op_id_buf.io.enq.valid := write_out_valid

  // reading from the ram, from Queue
  val deq_ptr_next = Mux((rd_ptr === (ram_depth.U-1.U)), 0.U, rd_ptr + 1.U)
  val r_addr = WireDefault(Mux(rd_out, deq_ptr_next, rd_ptr))
  //op_buf.io.enq.bits := one_big_ram.read(r_addr)
  // Tying out id to current control value, only valid important
  op_id_buf.io.enq.bits := curr_ctrl_id 

  tmp_ram.io.we1 := str_in
  tmp_ram.io.en1 := true.B
  tmp_ram.io.addrIn := wr_ptr
  tmp_ram.io.addrOut := r_addr
  tmp_ram.io.dataIn1 := ip_buf.io.deq.bits
  op_buf.io.enq.bits := tmp_ram.io.dataOut1

  /////////////////////////////////////////////////////////////////////
  // flushing operation - puts random stuff on the output for n*fm_size
  /////////////////////////////////////////////////////////////////////

  val fb_count = Counter(500) //TODO make param
  when(flush_flag) {
    val fxp_flush = (6.9).F(data_gen.binaryPoint)
    // FIXME: make these flush vars large and garbage
    op_buf.io.enq.valid := true.B
    //op_buf.io.enq.bits := fxp_flush
    op_id_buf.io.enq.valid := true.B
    op_id_buf.io.enq.bits := 65535.U

    // update fm counter
    when(rd_out) { // back pressure during flush
      when(fm_out.inc()) { 
        // when fm wraps, increment flush batch counter
        when(fb_count.inc()) {
          // Reset everything!
          flush_flag := false.B
          // not really necessary but makes sure pntrs aligned
          wr_ptr := 0.U 
          rd_ptr := 0.U
          maybe_full := false.B //needed
          // fm_in already reset, fm out resetting now
          ctrl_lock := false.B // doesn't hurt but not needed
          b_count_in.reset()
          b_count_out.reset()
        }
      }
    }
  }

  // connect Qs out to output
  io.out <> op_buf.io.deq
  io.out_id <> op_id_buf.io.deq
}
