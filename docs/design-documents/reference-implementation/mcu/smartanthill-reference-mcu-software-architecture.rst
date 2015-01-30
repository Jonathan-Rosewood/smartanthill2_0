v0.2

Copyright (c) 2015, OLogN Technologies AG. All rights reserved.

Redistribution and use of this file in source (.rst) and compiled (.html, .pdf, etc.) forms, with or without modification, are permitted provided that the following conditions are met:

  * Redistributions in source form must retain the above copyright notice, this list of conditions and the following disclaimer.

  * Redistributions in compiled form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 
  * Neither the name of the OLogN Technologies AG nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL OLogN Technologies AG BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

SmartAnthill Reference Implementation - MCU Software Architecture
=================================================================

*NB: this document relies on certain terms and concepts introduced in “SmartAnthill Overall Architecture” document, please make sure to read it before proceeding.*

SmartAnthill project is intended to operate on MCUs which are extremely resource-constrained. In particular, currently we're aiming to run SmartAnthill on MCUs with as little as 512 bytes of RAM. This makes the task of implementing SmartAnthill on such MCUs rather non-trivial. Present document aims to describe our approach to implementing SmartAnthill on MCU side. It should be noted that what is described here is merely our approach to a reference SmartAnthill implementation; it is not the only possible approach, and any other implementation which is compliant with SmartAnthill protocol specification, is welcome (as long as it can run on target MCUs and meet energy consumption and other requirements).


Assumptions (=mother of all screw-ups)
--------------------------------------

1. RAM is the most valuable resource we need to deal with. Limits on RAM are on the order of 512-8192 bytes, while limits on code size are on the order of 8192-32768 bytes.
2. EEPROM (or equivalent) is present on all the supported chips
3. There is a limit on number of EEPROM operations (such as 10000 to 100000 during MCU lifetime, depending on MCU)
4. This limit is usually per-writing-location and EEPROM writings are done with some granularity which is less than whole EEPROM size. One expected granularity size is 32 bits-per-write; if EEPROM on MCU has such a granularity, it means that even we're writing one byte, we're actually writing 4 bytes (and reducing the number of available writes for all 4 bytes).
5. There are MCUs out there which allow to switch to “sleep” mode
6. During such “MCU sleep”, RAM may or may not be preserved (NB: if RAM is preserved, it usually means higher energy consumption)
7. During such “MCU sleep”, receiver may or may not be turned off (NB: this issue is addressed in detail in "SmartAnthill Protocol Stack" and "SAGDP" documents).

Layers and Libraries
--------------------

Reference implementation of SmartAnthill on MCU is divided into two parts:

* SmartAnthill reference implementation as such (the same for all MCUs)
* MCU- and device-dependent libraries

Memory Architecture
-------------------

As RAM is considered the most valuable resource, it is suggested to pay special attention to RAM usage. 

SmartAnthill memory architecture is designed as follows:

* Two large blocks of RAM are pre-allocated: a) stack (TODO: size), b) “command buffer”
* “command buffer” is intended to handle variable-size request/response data (such as incoming packets, packets as they're processed by protocol handlers, replies etc.); it's use is described in detail in "Main Loop" section below.
* In addition, there are fixed-size states of various state machines which implement certain portions of SmartAnthill protocol stack (see details below). These fixed-size state may either reside globally, or on stack of "main loop" (see below)

"Main Loop" a.k.a. "Main Pump"
------------------------------

SmartAnthill on MCU is implemented as a "main loop", which calls different functions and performs other tasks as follows:

* first, "main loop" calls a function [TODO](void\* data, uint16 datasz), which waits for an incoming packet and fills *data* with an incoming packet. This function is a part of device-specific library. If incoming packets can arrive while the "main loop" is running, i.e. asynchronously, they need to be handled in a separate buffer and handled separately, but otherwise "main loop" can pass a pointer to the beginning of the “command buffer” to this function call.
* then, "main loop" calls one “receiving” protocol handler (such as “receiving” portion of SADLP-CAN), with the following prototype: **protocol_handler(void\* src,uint16 src_size,void\* dst, uint16\* dst_size);** In fact, for this call "main loop" uses both *src* and *dst* which reside within “command buffer”, *src* coming from the “command buffer” start, and *dst=src+src_size*.
* NB: all calls of protocol handlers (both “receiving” and “sending”) are made right from the program “main loop” (and not one protocol handler calling another one), to reduce stack usage.
* after protocol handler has processed the data, it returns to “main loop”. Now previous src is not needed anymore, so "main loop" can and should **memmove()** dst to the beginning of “command buffer”, discarding src and freeing space in "command buffer" for future processing.
* after such **memmove()** is done, we have current packet (as processed by previous protocol handler) at the beginning of “command buffer”, so we can repeat the process of calling the “receiving” “protocol handler” (such as SAGDP, and then Yocto VM).
* when Yocto VM is called (it has prototype **yocto_vm(void\* src,uint16 src_size,void\* dst, uint16\* dst_size,WaitingFor\* waiting_for);**; *WaitingFor* structure is described in detail in 'Asynchronous Returns' subsection below), it starts parsing the command buffer and execute commands. Whenever Yocto VM encounters an EXEC command (see "Yocto VM" document for details), Yocto VM calls an appropriate plugin handler, with the following prototype: **plugin_handler(void* plugin_state,void\* src,uint16 src_size,void\* reply, uint16\* reply_size, WaitingFor\* waiting_for)**, passing pointer to plugin data as a src and it's own *dst* as *reply*. After plugin_handler returns, Yocto VM increments it's own *dst* by a size of the reply passed back from the plugin. It ensures proper and easy forming of "reply buffer" as required by Yocto VM specification.
* after the Yocto VM has processed the data, “main loop” doesn't need the command anymore, so it can again **memmove()** "reply buffer" (returned at *dst* location by Yocto VM) to the beginning of “command buffer” and call SAGDP “sending” protocol handler.
* after “sending” protocol handler returns, “main loop” may and should **memmove()** reply of the “sending” protocol handler to the beginning of the “command buffer” and continue calling the “sending” protocol handlers (and memmove()-ing data to the beginning of the “command buffer”) until the last protocol handler is called; at this point, data is prepared for feeding to the physical channel.
* at this point, "main loop" may and should call [TODO] function (which belongs to device-specific library) to pass data back to the physical layer.

In a sense, "main loop" is always "pumping" the data from one "protocol handler" to another one, always keeping "data to be processed" in the beginning of the "command buffer" and discarding it as soon as it becomes unnecessary. This "pumping" **memmove()**-based approach allows to avoid storing multiple copies of data (only two copies are stored at any given moment), and therefore to save on the amount of RAM required for SmartAnthill stack operation.

Return Codes
^^^^^^^^^^^^

Each protocol handler returns error code. Error codes are protocol-handler specific and may include such things as IGNORE_PACKET (causing "main loop" to stop processing of current packet and start waiting for another one), FATAL_ERROR_REINIT (causing "main loop" to perform complete re-initialization of the whole protocol stack), WAITING_FOR (described below in 'Asynchronous Returns' subsection) and so on.

Asynchronous Returns from Yocto VM 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to paramaters which are usual for protocol handlers, Yocto VM also receives a pointer to a struct WaitingFor { uint16 sec; uint16 msec; byte pins_to_wait[(NPINS+7)/8]; byte pin_values_to_wait[(NPINS+7)/8] };
When Yocto VM execution is paused to wait for some event, it SHOULD return to "main loop" with an error code = WAITING_FOR, filling in this parameter with time which it wants to wait, and filling in any pins (with associated pin values) for which it wants to wait. These instructions to wait for are always treated as waiting for *any* of conditions to happen, i.e. to "wait for time OR for pin#2==1 OR for pin#4==0".

It is responsibility of the "main loop" to perform waiting as requested by Yocto VM and call it back when the condition is met (passing NULL for src). 

During such a wait, "main loop" is supposed to wait for incoming packets too; if an incoming packet comes in during such a wait, "main loop" should handle incoming packet first (before reporting to 'Yocto VM' that it's requested wait is over). 

Yocto VM may issue WAITING_FOR either as a result of SLEEP instruction, or as a result of plugin handler returning WAITING_FOR (see example below).

TODO: MCUSLEEP?

State Machines
--------------

Model which is described above in "Main Loop" section, implies that all SmartAnthill protocol handlers (including Yocto VM) are implemented as "state machines"; state of these "state machines" should be fixed-size and belongs to "fixed-size states" memory area mentioned in "Memory Architecture" section above.

Plugins
^^^^^^^

Ideally, plugins SHOULD also be implemented as state machines, for example:

::

  struct MyPluginData {
    byte state; //'0' means 'initial state', '1' means 'requested sensor to perform read'
  };

  byte my_plugin_handler_init(void* plugin_data) {
    //perform sensor initialization if necessary
    MyPluginData* pd = (MyPluginData*)plugin_data;
    pd->state = 0;
  }

  byte my_plugin_handler(void* plugin_data,
      byte pins_to_wait[(NPINS+7)/8], byte pin_values_to_wait[(NPINS+7)/8]) {
    MyPluginData* pd = (MyPluginData*)plugin_data;
    if(pd->state == 0) {
      //request sensor to perform read
      pd->state = 1;
      //let's assume that sensor will set signal on pin#3 to 1 when the data is ready

      //filling in pins_to_wait to indicate we're waiting for pin #3, and value =1 for it:
      pins_to_wait[0] |= (1<<3);
      pins_values_to_wait[0] |= (1<<3);

      return WAITING_FOR;
    }
    else {
      //read pin#3 just in case
      if(pin3 != 1) {
        pins_to_wait[0] |= (1<<3);
        pins_values_to_wait[0] |= (1<<3);
        return WAITING_FOR;
      }
      //read data from sensor and fill in "reply buffer" with data
      return 0;
    }
  }

Such an approach allows Yocto VM to perform proper pausing (with ability for Central Controller to interrupt processing by sending a new command while it didn't receive an answer to the previous one) when long waits are needed. It also enables parallel processing of the plugins (TODO: PARALLEL instruction for Yocto VM).

However, for some plugins (simple ones without waiting at all, or if we're too lazy to write proper state machine), we can use 'dummy state machine', with *MyPluginData* being zero-size and unused, and **plugin_handler()** not taking into account any states at all.


Programming Guidelines
----------------------

The following guidelines are considered important to ensure that only absolutely minimum amount of RAM is used:

* Dynamic allocation is not used, at all. (yes, it means no **malloc()**)
* No third-party libraries (except for those specially designed for MCUs) are allowed
* All on-stack arrays MUST be analyzed for being necessary and rationale presented in comments.

EEPROM Handling
---------------

TODO

