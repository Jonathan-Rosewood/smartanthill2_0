..  Copyright (c) 2015, OLogN Technologies AG. All rights reserved.
    Redistribution and use of this file in source (.rst) and compiled
    (.html, .pdf, etc.) forms, with or without modification, are permitted
    provided that the following conditions are met:
        * Redistributions in source form must retain the above copyright
          notice, this list of conditions and the following disclaimer.
        * Redistributions in compiled form must reproduce the above copyright
          notice, this list of conditions and the following disclaimer in the
          documentation and/or other materials provided with the distribution.
        * Neither the name of the OLogN Technologies AG nor the names of its
          contributors may be used to endorse or promote products derived from
          this software without specific prior written permission.
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL OLogN Technologies AG BE LIABLE FOR ANY
    DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
    OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
    DAMAGE SUCH DAMAGE

.. _saccp:

SmartAnthill Command&Control Protocol (SACCP)
=============================================

:Version:   v0.2.2a

*NB: this document relies on certain terms and concepts introduced in*
:ref:`saoverarch` *and*
:ref:`saprotostack` *documents, please make sure to read them before proceeding.*

SACCP is a part of SmartAnthill 2.0 protocol stack. It belongs to Level 7 of OSI/ISO Network Model, and is responsible for allowing SmartAnthill Client (usually implemented by SmartAnthill Central Controller) to control SmartAnthill Device.

Within SmartAnthill protocol stack, SACCP is located on top of SAGDP. On the side of SmartAnthill Device, on top of SACCP there is Zepto VM. On the side of SmartAnthill Client, on top of SACCP is Control Program.

As well as it's underlying protocol (which is usually SAGDP), SACCP is an asymmetric protocol; it means that behaviour of SACCP is somewhat different for SmartAnthill Device and SmartAnthill Client. For the purposes of SACCP underlying protocol,  SmartAnthill Client is considered “master device”, and SmartAnthill Device is considered “slave device”.

.. contents::

SACCP Assumptions
-----------------

It is assumed that authentication, encryption, integrity and reliable delivery should be implemented by protocol layers below SACCP. SACCP operates on data packets which are already defragmented, authenticated, decrypted, and are guaranteed to be reliably delivered (reliable delivery includes guarantees that every data packet is delivered only once, see also an exceptions to guaranteed delivery in cases of “dual packet chains” and “fatal error handling” below).

The underlying protocol of SACCP should support the concept of “packet chain” (see section “Packet Chains” for more details). SACCP, when sending a packet, MUST specify to the underlying protocol whether the packet is the first, intermediate, or last in the “packet chain” (and receiving this information back when receiving the packet). One protocol which can be used as SACCP underlying protocol, is SAGDP.

Packet Chains
-------------

All interactions in SACCP are considered as “packet chains” (see :ref:`saprotostack` document for more details). With "packet chains", one of the parties initiates communication by sending a packet P1, another party responds with a packet P2, then first party may respond to P2 with P3 and so on. Whenever SACCP issues a packet to an underlying protocol, it MUST specify whether a packet is a first, intermediate, or last within a “packet chain” (using 'is-first' and 'is-last' flags; note that due to “rules of engagement” described below, 'is-first' and 'is-last' flags are inherently incompatible, which MAY be relied on by implementation). This information allows underlying protocol to arrange for proper retransmission if some packets are lost during communication.


Handling of Fatal Errors
------------------------

SACCP is built under the assumption that in case of any inconsistency between SmartAnthill Client and SmartAnthill Device, it is SmartAnthill Client which is right (see :ref:`saprotostack` document for more details). Keeping this in mind, implementation of SACCP underlying protocol on the SmartAnthill Device side MUST detect any fatal inconsistencies in the protocol (one example of such inconsistency is authenticated packet which is out-of-chain-order), and MUST invoke re-initialization of the SmartAnthill Device in this case. It is done regardless of the SACCP state and layers above SACCP, and MAY be done without notifying SACCP or any layers above the SACCP.

Layering remarks
----------------

SACCP (and it's underlying protocol, which is normally SAGDP) are somewhat unusual for an application-level protocol in a sense that SACCP needs to care about details which are implicitly related to retransmission correctness. This is a design choice of SACCP (and SAGDP) which has been made in face of extremely constrained (and unusual for conventional communication) environments. It should also be noted that while some such details are indeed exposed to SACCP, they are formalized as a clear set of “rules of engagement” to be obeyed. As long as these “rules of engagement” are obeyed, SACCP does not need to care about retransmission correctness (though the rationale for “rules of engagement” is provided by retransmission correctness). Any references to retransmission correctness in current document are non-normative and are presented for the purposes of better understanding only.

SACCP Rules of Engagement
-------------------------

To ensure correct operation of an underlying protocol, there are certain rules (referred to “rules of engagement”) which MUST be obeyed (note that these “rules of engagement” are not specific to SAGDP, but will be a general requirement for any underlying protocol of similar nature):

1. Each packet belongs to a “chain”, and has associated flags which specify whether the packet 'is-first' or 'is-last'

2. All “chains” MUST be at least two packets long (this is required by an underlying protocol to ensure retransmission correctness)

   a) From (2) it follows that 'is-first' and 'is-last' flags are inherently incompatible (which MAY be relied on by implementation)

3. Multiple replies to a single command are not allowed. Scenarios when 'double-reply' to the same command is needed (for example, for longer- or uncertain-time-taking commands need to be implemented, SHOULD be handled in the same way as scenarios with disabling the receiver ('last' packet on the SmartAnthill Device side, then long command, then SmartAnthill Device initiates a new chain). A short “ACK” to confirm that the command is received, may be sent first, then the command can be executed, and then a real reply may be sent), MUST be implemented as follows:

   a) first reply MUST be the last packet in the “packet chain” (that is, it MUST have 'is-last' flag)
   b) second reply MUST start a new “packet chain” (that is, it MUST have 'is-first' flag)

      * TODO: this approach implies that there should be a reply-to-second-reply, need to see if it is restrictive enough in practice to consider adding special handling for double-replies

4. If a device is going to turn off it's receiver as a result of receiving a packet, such a packet MUST be the last packet in the “chain” (again, this is required to ensure retransmission correctness)

   a) From (2) and (3) it follows that if SmartAnthill Client needs to initiate a “packet chain” which requests SmartAnthill Device to turn off it's receiver, such a chain MUST be at least 3 packets long. (NB: if such a chain is initiated by SmartAnthill Device, it MAY be 2 packets long).

5. If the underlying protocol issues a packet with a 'previous-send-aborted' flag (which can happen only for SmartAnthill Device, and not for SmartAnthill Client), it means that underlying protocol has canceled a send of previously issued packet. In such cases, SACCP (and all the layers above) MUST NOT assume that previously issued packet was received by counterpart (TODO: maybe we can guarantee that the packet was NOT sent?)

6. Due to the “Fatal Error Handling” mechanism described above, SACCP (as well as any layers above SACCP) on the SmartAnthill Device MUST assume that re-initialization can occur at any moment of their operation (at least whenever control is passed to the protocol which is an underlying protocol for SACCP). The effect of such re-initialization is that all volatile memory (such as RAM) is re-initialized, but all non-volatile memory (such as EEPROM) is preserved.

   As long as the “rules of engagement” above are obeyed, and SACCP properly informs an underlying protocol whether each packet it sends, is first, intermediary, or last in the chain, retransmission correctness can be provided by an underlying protocol, and SACCP doesn't need to care about it.

SACCP Checksum
--------------

To re-use the same code which is used for SASP anyway, SACCP uses the following checksum algorithm:

* prepend input with input-size (encoded as Encoded-Size<max=2>). This ensures that CBC-MAC is secure (because prepending length as Encoded-Size guarantees that there are no two distinct messages which are prefixes of each other; not that we really need it).
* split input (with prepended input-size) into 12-byte blocks; if there is an incomplete block, pad it with zeros
* calculate CBC-MAC on sequence of these blocks, using Speck-96 (with a 96-bit block), with a pre-defined Speck-96 key, where each byte of the pre-defined key is 0xA5.
* calculated CBC-MAC represents 96 bits (12 bytes) of checksum
* starting from the beginning of the 96-bit (12-byte) checksum, take as many bytes as necessary (up to 12)

SACCP Packets
-------------

SACCP packets are divided into SACCP command packets (from SmartAnthill Client to SmartAnthill Device) and SACCP reply packets (from SmartAnthill Device to SmartAnthill Client).


SACCP Command Packets
^^^^^^^^^^^^^^^^^^^^^

SACCP command packets can be one of the following:

**\| SACCP_NEW_PROGRAM, Reserved \| Execution-Layer-Program \|**

where SACCP_NEW_PROGRAM is a 4-bit constant, Reserved is a 4-bit field which MUST consist of zeros (otherwise SACCP returns SACCP_ERROR_INVALID_FORMAT), and Execution-Layer-Program is variable-length program.

NEW_PROGRAM command packet indicates that Execution-Layer-Program (normally - Zepto VM program) is requested to be executed on the SmartAnthill Device.

**\| SACCP_REPEAT_OLD_PROGRAM, Checksum-Length \| Checksum \|**

where SACCP_REPEAT_OLD_PROGRAM is a 4-bit constant, Checksum-Length is a 4-bit length of Checksum field (Checksum-Length MUST be >= 4 and MUST be <= 12, if it is not - SACCP returns SACCP_ERROR_INVALID_FORMAT error), Checksum has length of Checksum-Length, and is calculated as SACCP Checksum which is described above.

OLD_PROGRAM command packet indicates that the Execution-Layer program which is already in memory of SmartAnthill Device, needs to be repeated. Checksum field is used to ensure that perceptions of the "program which is already in memory" are the same for SmartAnthill Client and SmartAnthill Device (inconsistencies are possible is several scenarios, such as two SmartAnthill Clients working with the same SmartAnthill Device, accidental reboot of the SmartAnthill Device, and so on). If Checksum does not match the program within SmartAnthill Device, SACCP returns SACCP_ERROR_OLD_PROGRAM_CHECKSUM_DOESNT_MATCH error.

**\| SACCP_REUSE_OLD_PROGRAM, Checksum-Length \| Checksum \| Fragments \|** TODO: New-Checksum just in case?

where SACCP_REUSE_OLD_PROGRAM is a 4-bit constant, Checksum-Length and Checksum are similar to those in SACCP_REPEAT_OLD_PROGRAM, and Fragments is a sequence of fragments.

SACCP_REUSE_OLD_PROGRAM is used when existing program is mostly the same, but there are some differences. When processing it, SACCP goes through the fragments, and appends data within (or referred to by) the fragment, to the new program, in a sense "assembling" new program from verbatim fragments, and from reference-to-old-program fragments.

SACCP Reuse Fragments
'''''''''''''''''''''

Each of the fragments in SACCP_REUSE_OLD_PROGRAM command packet is one of the following:

**\| SACCP_REUSE_FRAME_VERBATIM \| Fragment-Length \| Fragment \|**

where SACCP_REUSE_FRAME_VERBATIM is a 1-byte constant, Fragment-Length is Encoded-Size<max=2> field, and Fragment has size of Fragment-Length. TODO: Truncated-Encoded-Size (also for FRAME_REFERENCE)?

**\| SACCP_REUSE_FRAME_REFERENCE \| Fragment-Length \| Fragment-Offset \|**

where SACCP_REUSE_FRAME_REFERENCE is a 1-byte constant, Fragment-Length is Encoded-Size<max=2> field, and Fragment-Offset is Encoded-Size<max=2> field, indicating offset of the fragment within existing program.


SACCP Reply Packets
^^^^^^^^^^^^^^^^^^^

SACCP reply packets can be one of the following:

**\| SACCP_OK \| Execution-Layer-Reply \|**

where SACCP_OK is 1-byte constant, and Execution-Layer-Reply is variable-length field.

**\| SACCP_ERROR_VM_EXCEPTION \| Exception-Data \|**

where SACCP_ERROR_VM_EXCEPTION is a 1-byte constant (different from all valid values of Saccp-Error-Code), and Exception-Data is exception data as passed by Execution Layer.

**\| Saccp-Error-Code \|**

where Saccp-Error-Code is a 1-byte field, which takes one of the following values: SACCP_ERROR_INVALID_FORMAT, SACCP_ERROR_OLD_PROGRAM_CHECKSUM_DOESNT_MATCH, or SACCP_NO_MEMORY (the last one may occur if SACCP runs out of memory while re-packing the packet coming from Execution Layer). 

Device Pins SHOULD NOT be Addressed Directly within Execution-Layer-Program
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Execution-Layer-Program may contain EXEC instructions (see :ref:`sazeptovm` document for details). These EXEC instructions address a certain 'ant body part', and pass opaque data to the corresponding plugin. While the data passed to the plugin is opaque, it SHOULD NOT contain any device pins in it; which device pins are used by the plugin on this specific device, is considered a part of 'body part configuration' and is stored within MCU.

Therefore, data within EXEC instruction normally does *not* contain pins, but contains only a BODYPART-ID and an action. For example, a command to plugin which turns on connected LED, SHOULD
look as **\|EXEC\|BODYPART-ID\|ON\|**, where ON is a 1-byte taking values '0' and '1', indicating "what to do with LED". All mappings of BODYPART-ID to pins SHOULD be described as plugin_config parameter of plugin_handler(), as described in :ref:`sazeptoos` document.

TODO: ?describe same thing in 'Zepto VM'?

Execution Layer and Control Program
-----------------------------------

Whenever SmartAnthill Device receives a SACCP command packet, SACCP invokes Execution Layer  and passes received (or calculated as described above) Execution-Layer-Program to it. After Execution Layer has finished it's execution, SACCP passes the reply back to the SmartAnthill Client. One example of a valid Execution Layer is Zepto VM which is described in a separate document, :ref:`sazeptovm` .

Within SmartAnthill system, Execution Layer exists only on the side of SmartAnthill Device (and not on the side of SmartAnthill Client). It's counterpart on the side of SmartAnthill Client is Control Program.

Execution Layer Restrictions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To comply with SACCP's “rules of engagement”, SACCP on the side of SmartAnthill Device (a.k.a Execution Layer) MUST comply and enforce the following restrictions:

1. Each reply provided by Execution Layer MUST be accompanied with a flag which signifies if the reply is 'is-first' or 'is-last' (or neither) in a “packet chain”. This flag is specified by Execution-Layer-Program.

2. If a reply is sent before the Execution-Layer-Program exit, it MUST have a 'is-last' flag is set. If it is not the case, Execution Layer MUST generate a “Program Error” exception.

3. If Execution Layer disables device receiver (such a disabling is always temporary) while processing a program, it MUST check that a reply was not sent before disabling device receiver (if it was –Execution Layer generates a “Program Error” exception, and does not disable receiver). However, after device receiver is re-enabled and Execution Layer execution continues and completes, Execution layer MUST check that a reply is sent before the Execution-Layer-Program is completed; this reply MUST have 'is-first' flag. If any of these conditions is not met, Execution Layer MUST generate a “Program Error” exception.

4. If Execution Layer does not disable device receiver while processing an Execution-Layer-Program and the program terminates, Execution Layer MUST check that reply was sent before or on program exit; this reply MUST NOT have 'is-first' flag. If any of these conditions is not met, Execution Layer MUST generate a “Program Error” exception.

5.  Multiple replies to the same command are NOT allowed

6. Whenever “Program Error” exception is generated, Execution Layer MUST abort program execution, and MUST send a special packet which indicates that an error has occurred, to the other side of the channel (i.e. to SmartAnt Client).

7. If the underlying protocol issues a packet with a 'previous-send-aborted' flag, it means that underlying protocol has canceled a send of previously issued packet. In such cases, Execution Layer (and all the layers above) MUST NOT assume that previously issued packet was received by counterpart (TODO: maybe we can guarantee that the packet was NOT sent?)

8. Due to the “Fatal Error Handling” mechanism described above, Execution Layer MUST assume that re-initialization can occur at any moment of their operation (at least whenever control is passed to the protocol which is an underlying protocol for SACCP). The effect of such re-initialization is that all volatile memory (such as RAM) is re-initialized, but all non-volatile memory (such as EEPROM) is preserved.

9. TODO: check if these rules are enough.

TODO: timeouts

Control Program Restrictions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To comply with SACCP's rules of engagement, SACCP on the side of SmartAnthill Client (a.k.a Control Program) MUST comply and enforce the following restrictions:

1. Control Program SHOULD NOT send a program which would cause Execution Layer on the server side to violate Execution Layer rules of engagement

2. TODO: is this enough?

