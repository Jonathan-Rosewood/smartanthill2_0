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

.. _samp:

SmartAnthill Mesh Protocol (SAMP)
=================================

**EXPERIMENTAL**

:Version:   v0.0.7

*NB: this document relies on certain terms and concepts introduced in* :ref:`saoverarch` *and* :ref:`saprotostack` *documents, please make sure to read them before proceeding.*

SAMP is a part of SmartAnthill 2.0 protocol stack (TODO: insert). It belongs to Level 3 of OSI/ISO Network Model, and is responsible for routing packets within SmartAnthill mesh network.

SmartAnthill mesh network is a heterogeneous network. In particular, on the way from SmartAnthill Central Controller to SmartAnthill Device a packet may traverse different bus types (including all supported types of wired and wireless buses); the same stands for the packet going in the opposite direction.

SAMP is optimized based on the following assumptions:

* SAMP relies on all communications being between Central Controller and Device (no Device-to-Device communications)
* SAMP aims to optimize "last mile" traffic (between last Retransmitting Device and target Device) while paying less attention to Central-Controller-to-Retransmitting-Device and Retransmitting-Device-to-Retransmitting-Device traffic. This is based on the assumption that the Retransmitting Devices usually have significantly less power restrictions (for example, are mains-powered rather than battery-powered).
* SAMP combines data with route requests
* SAMP allows to send "urgent" data packets, which sacrifice traffic and energy consumption for the best possible delivery speed
* SAMP relies on upper-layer protocol (SAGDP) to send retransmits in case if packet has not been delivered, and to provide SAMP with an information about retransmit number (i.e., original packet having retransmit-number=0, first retransmit having retransmit-number=1, and so on).

SAMP has the following types of actors: Root (normally implemented by Central Controller), Retransmitting Device, and non-Retransmitting Device. All these actors are collectively named Nodes.

Underlying Protocol Requirements
--------------------------------

SAMP underlying protocol (normally SADLP-\*), MUST support the following operations:

* bus broadcast (addressed to all the Devices on the bus)
* bus multi-cast (addressed to a list of the Devices on the bus)
* bus uni-cast
* bus uni-cast with ACK

NB: in many cases, these operations may be simulated using very few operations as primitives; for example, PHY-level broadcast can be used to create SADLP-\*-level multi-cast by adding, for example, NEXT-HOP-NODE-ID.

SmartAnthill Retransmitting Devices
-----------------------------------

Some SmartAnthill Devices are intended to be "SmartAnthill Retransmitting Devices". "SmartAnthill Retransmitting Device" has one or more transmitters. Transmitters on SmartAnthill Retransmitting Devices MUST be always-on; turning off transmitter is NOT allowed for SmartAnthill Retransmitting Devices. That is, if MCUSLEEP instruction is executed on a SmartAnthill Retransmitting Device, it simply pauses executing a program, without turning transmitter off (TODO: add to Zepto VM). Normally, SmartAnthill Retransmitting Devices are mains-powered, or are using large batteries. SmartAnthill Protocol Stack (specifically SAMP) on SmartAnthill Retransmitting Devices requires more resources (specifically RAM) than non-Retransmitting Devices.

Highly mobile Devices SHOULD NOT be Retransmitting Devices. Building a reliable network out of highly mobile is problematic from the outset (and right impossible if these movements are not synchronized). Therefore, SAMP assumes that Retransmitting Devices are moved rarely, and is optimized for rarely-moving Retransmitting Devices. While SAMP does recover from moving one or even all Retransmitting Devices, this scenario is not optimized and recovery from it may take significant time.

Routing Tables
--------------

Each Retransmitting Device, after pairing, MUST keep a Routing Table: list of (TARGET-ID,BUS-ID,INTRA-BUS-ID,NEXT-HOP-ACK) tuples. Routing Table has semantics of "next hop to route packet addressed to TARGET-ID". TODO: omitting BUS-ID if there is only one bus, size reporting to Root (as # of entries). NEXT-HOP-ACK is a flag which set if the nearest hop (over (BUS-ID,INTRA-BUS-ID)) is known to be able not only to receive packets, but to send ACKs back via "bus uni-cast with ACK" SADLP-\* operation; in general, NEXT-HOP-ACK cannot be calculated based only on bus type, and may change for the same link during system operation. SAMP is built to try using links with NEXT-HOP-ACK as much as possible, but MAY use links without NEXT-HOP-ACK if there are no alternatives.

Routing Tables SHOULD be stored in a 'canonical' way (ordered from lower TARGET-IDs to higher ones; duplicate entries for the same TARGET-ID are currently prohibited); this is necessary to simplify calculations of the Routing Table checksums. TODO: specify Routing-Table-Checksum field

On non-Retransmitting Devices, Routing Table is rudimentary: it contains only one row with TARGET-ID=0: (0,BUS-ID,INTRA-BUS-ID). Moreover, on non-Retransmitting Devices Routing Table is OPTIONAL; if non-Retransmitting Device does not keep Routing Table - it MUST be reflected in a TODO CAPABILITIES flag during "pairing"; in this case Root MUST send requests specifying target 

All Routing Tables on both Retransmitting and non-Retransmitting Devices are essentially copies of "Master Routing Tables" which are kept on Root. It is a responsibility of Root to maintain Routing Tables for all the Devices (both Retransmitting and non-Retransmitting); it is up to Root which entries to store in each Routing Table. In some cases, Routing Table might need to be truncated; in this case, it is responsibility of Root to use VIA field in Target-Address (see below) to ensure that the packet can be routed given the Routing Tables present. In any case, Routing Table MUST be able to contain at least one entry, with TARGET-ID=0 (Root). This guarantees that path to Root can always be found without VIA field.

TODO: no mobile non-Retransmitting (TODO reporting 'mobile' in pairing CAPABILITIES, plus heuristics), priorities (low->high): non-Retransmitting, Retransmitting.

TODO: RT self-healing, re-sync, etc.

Addressing
----------

SAMP supports two ways of addressing devices: non-paired and paired. 

Non-paired addressing is used for temporary addressing Devices which are not "paired" with SmartAnthill Central Controller (yet). Non-paired addressing is used ONLY during "Pairing" process, as described in :ref:`sapairing` document. As soon as "pairing" is completed, Device obtains it's own SAMP-NODE-ID (TODO: add to pairing document), and all further communications with Device is performed using  "paired" addressing. Non-paired addressing is a triplet (NODE-ID,BUS-ID,INTRA-BUS-ID).

Paired addressing is used for addressing Devices which has already been "paired". It is always one single item SAMP-NODE-ID. Root always has SAMP-NODE-ID=0. 

Recovery Philosophy
-------------------

Recovery from route changes/failures is vital for any mesh protocol. SAMP does it as follows:

* by default, most of the transfers are not acknowledged at SAMP level (go as Samp-Unicast-Data-Packet without GUARANTEED-DELIVERY flag)
* however, upper-layer protocol (normally SAGDP) issues it's own retransmits and passed retransmit number to SAMP
* on retransmit #N, SAMP switches GUARANTEED-DELIVERY flag on
* when GUARANTEED-DELIVERY flag is set, SAMP uses "bus unicast with ACK" underlying-protocol mode
* if "bus unicast with ACK" fails for M times (with exponentially increasing timeouts), link failure is assumed
* link failure is reported to the Root, so it can initiate route discovery to the node on the other side of the failed link (using Samp-From-Santa-Data-Packet)

  + if link failure is detected from the side of the link which is close to Root, link failure reporting is done by sending Routing-Error (which always come in GUARANTEED-DELIVERY mode) back to Root
  + if link failure is detected from the side of the link which is far from Root, link failure reporting is done by broadcasting Samp-To-Santa-Data-Or-Error-Packet, which is then converted into Samp-Forward-To-Santa-Data-Or-Error-Packet (which is always sent in GUARANTEED-DELIVERY mode) by all Retransmitting Devices which have received it.


Target-Address, Multiple-Target-Addresses, and Multiple-Target-Addresses-With-Extra-Data
----------------------------------------------------------------------------------------

Target-Address allows to store either paired-address, or non-paired address. Target-Address is encoded as 

**\| FLAG-AND-NODE-ID \| OPTIONAL-VIA-OR-INTRA-BUS-SIZE-AND-BUS-ID \| ... \| OPTIONAL-VIA-INTRA-BUS-SIZE-AND-BUS-ID \| OPTIONAL-CUSTOM-INTRA-BUS-SIZE \| OPTIONAL-INTRA-BUS-ID \|**

where FLAG-AND-NODE-ID-OR-BUS-ID is an Encoded-Unsigned-Int<max=2> bitfield substrate, where bit[0] is EXTRA_DATA_FOLLOWS flag, and bits[1..] are NODE-ID.

OPTIONAL-VIA-OR-INTRA-BUS-SIZE-AND-BUS-ID is present only if EXTRA_DATA_FOLLOWS is set, and is an Encoded-Unsigned-Int<max=2> bitfield substrate, where bit[0] represents IS_NONPAIRED_ADDRESS flag, and the rest of the bits depend on bit[0]. If IS_NONPAIRED_ADDRESS flag is not set, then bits[1..] represent VIA field (encoded as `NODE-ID+1`); if VIA field is -1 (because bits[1..] are zero), then no further extra data fields are present. If IS_NONPAIRED_ADDRESS flag is set, then bits[1..3] represent INTRA-BUS-SIZE (with value 0x7 interpreted in a special way, specifying that INTRA-BUS-SIZE is 'custom'), and bits [4..] represent BUS-ID. If IS_NONPAIRED_ADDRESS flag is not set, and VIA field in it is >=0, it means that another OPTIONAL-VIA-INTRA-BUS-SIZE-AND-BUS-ID field is present, which is interpreted as above. OPTIONAL-VIA-INTRA-BUS-SIZE-AND-BUS-ID with either IS_NONPAIRED_ADDRESS set, or with VIA field equal to -1, denote the end of the list.

OPTIONAL-CUSTOM-INTRA-BUS-SIZE is present only if OPTIONAL-VIA-OR-INTRA-BUS-SIZE-AND-BUS-ID is present, and flag IS_NONPAIRED_ADDRESS is set, and INTRA-BUS-SIZE field has value 'custom'; OPTIONAL-INTRA-BUS-ID is present only if OPTIONAL-VIA-OR-INTRA-BUS-SIZE-AND-BUS-ID is present, and has INTRA-BUS-SIZE (calculated from OPTIONAL-INTRA-BUS-SIZE-AND-BUS-ID and OPTIONAL-CUSTOM-INTRA-BUS-SIZE) size.

Multiple-Target-Addresses is essentially a multi-cast address. It is encoded as a list of items, where each item is similar to an Target-Address field, with the following changes: 

* for list entries, within FLAG-AND-NODE-ID field it is `NODE-ID + 1` which is stored (instead of simple NODE-ID for single Target-Address). This change does not affect VIA fields.
* to denote the end of Multiple-Target-Addresses list, FLAG-AND-NODE-ID field with NONPAIRED_ADDRESS=0 and NODE-ID=0, is used
* value of FLAG-AND-NODE-ID field with NONPAIRED_ADDRESS=1 and NODE-ID=0, is prohibited (reserved)

Multiple-Target-Addresses-With-Extra-Data is the same as Multiple-Target-Addresses, but each item (except for the last one, where NODE-ID=0), additionally contains some extra data (which is specified whenever Multiple-Target-Addresses-With-Extra-Data is mentioned). For example, if we're speaking about "Multiple-Target-Addresses-With-Extra-Data, where Extra-Data is 1-byte field", it means that each item of the list (except for the last one) will have both Target-Address field (with changes described in Multiple-Target-Addresses), and 1-byte field of extra data.

Time-To-Live
------------

Time-To-Live (TTL) is a field which is intended to address misconfigured/inconsistent Routing Tables. TTL is set to certain value (default 4) whenever the packet is sent, and is decremented by each Node which retransmits the packet. TTL=0 is valid, but TTL < 0 is not; whenever the packet needs to be retransmitted and it would cause TTL to become < 0 - the packet is dropped (with a Routing-Error, see below).

During normal operation, it SHOULD NOT occur. Whenever the packet is dropped because TTL is down to zero (except for Routing-Error SAMP packets), it MUST cause a TODO Routing-Error to be sent to Root.

Uni-Cast Processing
-------------------

Whenever a Uni-Cast packet (the one with a Target-Address field) is received by Retransmitting Device, the procedure is the following:

* check if the Target-Address is intended for the Retransmitting Device

  + if it is - process the packet locally and don't process further

* if packet TTL is already equal to 0 - drop the packet and send Routing-Error to the Root (see Time-To-Live section above for details)
* decrement packet TTL
* using Routing Table, find next hop for the Target-Address

  + if next hop cannot be found for the Target-Address itself, but Target-Address contains VIA field(s) - try to find next hop based on each of VIA fields
  + if next hop cannot be found using Target-Address and all VIA field(s) - drop the packet and send TODO Routing-Error to the Root

* if any of VIA fields in the Target-Address is the same as the next hop - remove all such VIA fields from the Target-Address
* find bus for the next hop and send modified packet (see on TTL and VIA modifications above) over this bus

Guaranteed Uni-Cast
^^^^^^^^^^^^^^^^^^^

As described in detail below, all SAMP uni-cast packet types, except for Samp-Unicast-Data-Packet without GUARANTEED-DELIVERY flag and Samp-Loop-Ack-Packet, are sent in 'Guaranteed Uni-Cast' mode. 

Processing by Retransmitting Devices
''''''''''''''''''''''''''''''''''''

If packet is to be delivered to the next hop in 'Guaranteed' mode by Retransmitting Device, it is processed in the following manner:

If the packet already has LOOP-ACK extra header (see below), and next hop has NEXT-HOP-ACK flag set in the Routing Table, then Retransmitting Device:

* sends Samp-Loop-Ack-Packet (see below) back to the requestor specified in LOOP-ACK extra header 
* removes LOOP-ACK extra header
* continues processing as specified below

If the next hop has NEXT-HOP-ACK flag set in the Routing Table, the packet is sent using underlying protocol's "bus uni-cast with ACK". If this operation returns 'failure' (i.e. ACK wasn't received), SAMP retries it 5 (TODO) times (with exponentially increasing timeouts - TODO) - it is treated as 'Routing-Error'. In particular:

* if the packet has Root as Target-Address: 

  + packet Samp-To-Santa-Data-Or-Error-Packet containing TBD Routing-Error as PAYLOAD (and with IS_ERROR flag set) is broadcasted
  + if possible, the packet which wasn't delivered, SHOULD be preserved (**TODO: what to do if it cannot be?**), and retransmitted as soon as route to the Root is restored

* if the packet has anything except for Root as Target-Address (and therefore is coming from Root):

  + packet Samp-Routing-Error containing TBD Routing-Error is sent (towards Root)
  + the packet which wasn't delivered, doesn't need to be preserved (TODO: identify packet which has been lost within Routing-Error)

If the packet doesn't have LOOP-ACK extra header, next hop doesn't have NEXT-HOP-ACK flag set in the Routing Table, then Retransmitting Device:

* adds LOOP-ACK extra header (which is described below) to the packet (if it is not already present)
* sends modified packet using "bus unicast" operation
* and sets timer to TODO

  + if the sender doesn't receive Samp-Loop-Ack-Packet until timer expires - it retransmits the packet at SAMP level. 
  
    - if such attempts don't succeed for 5 (TODO) times (with exponentially increasing timeouts - TODO) - it is treated as 'Routing-Error' (the same way as described above, depending on packet having Root as a Target-Address).

If the packet already has LOOP-ACK extra header, and next hop doesn't have NEXT-HOP-ACK flag set in the Routing Table, then Retransmitting Device:

* keeps LOOP-ACK extra header
* sends packet using "bus unicast" operation
* doesn't set any timers

LOOP-ACK on Destination
'''''''''''''''''''''''

If packet with LOOP-ACK extra header is received by destination Device, destination Device MUST send Samp-Loop-Ack-Packet back to the node specified in LOOP-ACK extra header. If destination Device is a non-Retransmitting Device, it will send Samp-Loop-Ack-Packet with Target-Address specified in LOOP-ACK, but to the next hop specified in Root's Routing Table entry. TODO: is it possible that Device doesn't have a route to Root yet? 

LOOP-ACK and Routing
''''''''''''''''''''

As LOOP-ACK currently doesn't support VIA routing, it means that Root MUST ensure that all the nodes on the "loop" route already know the routes without VIA fields; it applies both to the route from the loop beginning to the loop end, and back from the loop end to the loop beginning (as for request-response cycle, LOOP-ACKs go both directions). When speaking about 'back from the loop end to the loop beginning', it MUST be taken into account that, as specified above, non-Retransmitting Device will send a Samp-Loop-Ack-Packet in the direction of the Root (but with Target-Address equal to the address from LOOP-ACK extra header), so there MUST be an already-defined route from this next-hop-in-direction-of-Root to the loop beginning.

Multi-Cast Processing
---------------------

Whenever a Multi-Cast packet (the one with Multiple-Target-Addresses field) is processed by a Retransmitting Device, the procedure is the following:

* check if one of addresses within Target-Address is intended for the Retransmitting Device (TODO: if multiple addresses match the Retransmitting Device - it is a TODO Routing-Error, which should never happen)

  + if it is - process the packet locally (NB: Retransmitting Devices SHOULD schedule processing instead)
  + remove the address of the Retransmitting Device from Multiple-Target-Addresses
  
    - if Multiple-Target-Addresses became empty - don't process any further

* if packet TTL is already equal to 0 - drop the packet and send Routing-Error to the Root (see Time-To-Live section above for details)
* decrement packet TTL
* using Routing Table, find next hops for all the Devices on the list of Multiple-Target-Addresses (this search MUST include using VIA field(s) if present, see Uni-Cast Processing above)
* if at least one of the next hops is not found - send a TODO Routing-Error packet (one packet containing all Routing-Errors for incoming packet) to Root, and continue processing
* if any of VIA fields in any of the Multiple-Target-Addresses is the same as the next hop - remove all such VIA fields from the Multiple-Target-Addresses
* find buses for all next hops, forming next-hop-bus-list
* for each bus on next-hop-bus-list

  + if there is only a single next hop for this bus - send the modified packet to this bus using uni-cast bus addressing

  + if there is multiple next hops for this bus:

    - if the bus supports multi-casting - send the modified packet using multi-cast bus addressing over the bus. NB: bus broadcasts (without INTRA-BUS-ID) MUST NOT be used for this purpose to avoid unnecessary multiplying number of packets.
    - otherwise, send the modified packet using uni-cast bus addressing to each of the hops

SAMP Packets
------------

Samp-Unicast-Data-Packet: **\| SAMP-UNICAST-DATA-PACKET-FLAGS-AND-TTL \| OPTIONAL-EXTRA-HEADERS \| Target-Address \| PAYLOAD \|**

where SAMP-UNICAST-DATA-PACKET-FLAGS-AND-TTL is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0] equal to 0, bit[1] being GUARANTEED-DELIVERY flag, bit [2] being BACKWARD-GUARANTEED-DELIVERY, bit [3] being EXTRA-HEADERS-PRESENT, bit[4] being reserved (MUST be zero), and bits [5..] being TTL; OPTIONAL-EXTRA-HEADERS is present only if EXTRA-HEADERS-PRESENT is set and is described below; Target-Address is described above, and PAYLOAD is a payload to be passed to the upper-layer protocol.

OPTIONAL-EXTRA-HEADERS is a sequence of the following items:

* **\| UNICAST-EXTRA-HEADER-LOOP-ACK \| LOOP-ACK-ID \|**

  where UNICAST-EXTRA-HEADER-LOOP-ACK is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0] indicating the end of OPTIONAL-EXTRA-DATA list, bits[1..3] equal to 3-bit constant UNICAST_EXTRA_HEADER_LOOP_ACK, and bits[4..] representing NODE-ID of the address where to send the LOOP-ACK, and LOOP-ACK-ID is an Encoded-Unsigned-Int<max=2> field representing ID of the LOOP-ACK to be returned.

* **\| GENERIC-EXTRA-HEADER-FLAGS \|**

  where GENETIC-EXTRA-HEADER-FLAGS is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0] indicating the end of OPTIONAL-EXTRA-HEADER list, bits[1..3] equal to 3-bit constant GENERIC_EXTRA_HEADER_FLAGS, bit[4] being IS-PROBE flag, and bits [5..] reserved (MUST be zeros).

* **\| TOSANTA-EXTRA-HEADER-LAST-INCOMING-HOP \|**

  where TOSANTA-EXTRA-HEADER-FLAGS is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0] indicating the end of OPTIONAL-EXTRA-HEADER list, bits[1..3] equal to 3-bit constant TOSANTA_EXTRA_HEADER_LAST_INCOMING_HOP, and bits [5..] being node id. This extra header MUST NOT be present for Samp-Unicast-Data-Packets.

If Target-Address is Root (i.e. =0), it MUST NOT contain VIA fields within; in addition, if Target-Address is Root (i.e. =0), the packet MUST NOT have BACKWARD-GUARANTEED-DELIVERY flag set.

If IS-PROBE flag is set, then PAYLOAD is treated differently. When destination receives Samp-Unicast-Data-Packet with IS-PROBE flag set, destination doesn't pass PAYLOAD to upper-layer protocol. Instead, destination parses PAYLOAD as follows: **\| PROBE-TYPE \| PROBE-EXTRA-HEADERS \| PROBE-PAYLOAD \|** where PROBE-TYPE is 1-byte bitfield substrate, with bits [0..2] being either PROBE_UNICAST or PROBE_TO_SANTA, bit[3] being PROBE-EXTRA-HEADERS-PRESENT; OPTIONAL-PROBE-EXTRA-HEADERS are similar to OPTIONAL-EXTRA-HEADERS, and PROBE-PAYLOAD takes the rest of the PAYLOAD; if PROBE-TYPE==PROBE_UNICAST, then destination Device sends Samp-Unicast-Data-Packet back to Root, with PAYLOAD copied from PROBE-PAYLOAD, and extra headers formed from PROBE-EXTRA-HEADERS, "as if" this packet is sent in reply to IS-PROBE packet by upper layer, but adding IS-PROBE flag (as a part of GENERIC-EXTRA-FLAGS extra header). If PROBE-TYPE==PROBE_TO_SANTA, destination Device sends a Samp-To-Santa-Data-Or-Error-Packet, with PAYLOAD copied from PROBE-PAYLOAD, "as if" the packet is sent in reply to IS-PROBE packet by upper layer, but adding IS-PROBE flag (as a part of GENERIC-EXTRA-FLAGS extra header).

Samp-Unicast-Data-Packet is processed as specified in Uni-Cast Processing section above; if GUARANTEED-DELIVERY flag is set, packet is sent in 'Guaranteed Uni-Cast' mode. Processing at the target node (regardless of node type) consists of passing PAYLOAD to the upper-layer protocol.

When target Device receives the packet, and sends reply back, it MUST set GUARANTEED-DELIVERY flag in reply to BACKWARD-GUARANTEED-DELIVERY flag in original packet; this logic applies to all the packets, including 'first' packets in SAGDP "packet chain" (as they're still sent in reply to some SAMP packet coming from the Root).

Samp-From-Santa-Data-Packet: **\| SAMP-FROM-SANTA-DATA-PACKET-AND-TTL \| OPTIONAL-EXTRA-HEADERS \| LAST-HOP \| DELAY-UNIT \| MULTIPLE-RETRANSMITTING-ADDRESSES \| BROADCAST-BUS-TYPE-LIST \| Target-Address \| PAYLOAD \|**

where SAMP-FROM-SANTA-DATA-PACKET-AND-TTL is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0]=1, bits[1..3] equal to a 3-bit constant SAMP_FROM_SANTA_DATA_PACKET, bit [4] being EXTRA-HEADERS-PRESENT, and bits[5..] being TTL; OPTIONAL-EXTRA-HEADERS is present only if EXTRA-HEADERS-PRESENT is set, and is similar to that of in Samp-Unicast-Data-Packet (though only GENERIC-\* extra headers MUST NOT be present), LAST-HOP is an Encoded-Unsigned-Int<max=2> representing node id of the last sender, DELAY-UNIT is an Encoded-Unsigned-Int<max=2> field, which specifies (in TODO way) units for subsequent DELAY fields, MULTIPLE-RETRANSMITTING-ADDRESSES is a Multiple-Target-Addresses-With-Extra-Data field described above (with Extra-Data being Encoded-Unsigned-Int<max=2> DELAY field expressed in DELAY-UNIT units), BROADCAST-BUS-TYPE-LIST is a zero-terminated list of `BUS-TYPE+1` values (enum values for BUS-TYPE TBD), Target-Address is described above, and PAYLOAD is a payload to be passed to the upper-layer protocol.

Samp-From-Santa-Data-Packet is a packet sent by Root, which is intended to find destination which is 'somewhere around', but exact location is unknown. When Root needs to pass data to a Node for which it has no valid route, Root sends SAMP-FROM-SANTA-DATA-PACKET (or multiple packets), to each of Retransmitting Devices, in hope to find target Device and to pass the packet. 

Samp-From-Santa-Data-Packet is processed as specified in Multi-Cast Processing section above, up to the point where all the buses for all the next hops are found. Starting from that point, Retransmitting Device processes Samp-From-Santa-Data-Packet proceeds as follows: 

* replaces LAST-HOP field with it's own node id
* creates a list broadcast-bus-list of it's own buses which match BROADCAST-BUS-TYPE-LIST
* for each bus which is on a next-hop-bus list but not on the broadcast-bus-list - continue processing as specified in Multi-Cast Processing section above

  + right before sending each modified packet - further modify all DELAY fields within MULTIPLE-RETRANSMITTING-ADDRESSES by subtracting time which passes between beginning receiving the packet and beginning transmitting the packet. **TODO: <0 ?**

* for each bus which is on the broadcast-bus-list - broadcast modified packet over this bus

  + right before broadcasting each modified packet - further modify all DELAY fields within MULTIPLE-RETRANSMITTING-ADDRESSES by subtracting time which passes between beginning receiving the incoming packet and beginning transmitting the outgoing packet. **TODO: <0 ?**

If IS-PROBE flag is set, then PAYLOAD is treated differently. When destination receives Samp-From-Santa-Data-Packet with IS-PROBE flag set, destination doesn't pass PAYLOAD to upper-layer protocol. Instead, destination processes the packet in the same way as described for the processing of Samp-Unicast-Data-Packet with IS-PROBE flag set. A special case of Samp-From-Santa-Data-Packet with IS-PROBE set is when Target-Address is Root (=0). Such packets (a.k.a. 'discovery' packets) are ignored by Root, but are replied to only by Devices which are not paired yet (i.e. have no node id). All such 'discovery' packets with Target-Address=0 MUST have IS-PROBE flag set.

Samp-To-Santa-Data-Or-Error-Packet: **\| SAMP-TO-SANTA-DATA-OR-ERROR-PACKET-NO-TTL \| OPTIONAL-EXTRA-HEADERS \| PAYLOAD \|**

where SAMP-TO-SANTA-DATA-OR-ERROR-PACKET-NO-TTL is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0]=1, bits[1..3] equal to a 3-bit constant SAMP_TO_SANTA_DATA_OR_ERROR_PACKET, bit [4] being IS_ERROR (indicating that PAYLOAD is in fact Routing-Error), bit[5] being EXTRA-HEADERS-PRESENT, and bits [6..] reserved (MUST be zero); OPTIONAL-EXTRA-HEADERS is present only if EXTRA-HEADERS-PRESENT is set, and is similar to that of in Samp-Unicast-Data-Packet (though only GENERIC-\* and TOSANTA-\* extra headers MUST NOT be present),note that Samp-To-Santa-Data-Or-Error-Packet doesn't contain TTL (as it is never retransmitted 'as is').

Samp-To-Santa-Data-Or-Error-Packet is a packet intended from Device (either Retransmitting or non-Retransmitting) to Root. It is broadcasted by Device in several cases: 

* when the message is marked as Urgent by upper-layer protocol
* when Device needs to report Routing-Error to Root when it has found that Root is not directly accessible.
* when requested to do so via a packet with IS-PROBE flag and PROBE-TYPE==PROBE_TO_SANTA

In any case, if Samp-To-Santa-Data-Or-Error-Packet is sent in response to a Samp-From-Santa-Data-Packet flag (regardless of packet being first or not from SAGDP point of view), Device MUST provide TOSANTA-EXTRA-HEADER-LAST-INCOMING-HOP extra header, filling it from LAST-HOP field of the Samp-From-Santa-Data-Packet.

On receiving Samp-To-Santa-Data-Or-Error-Packet, Retransmitting Device sends a Samp-Forward-To-Santa-Data-Or-Error-Packet towards Root, in 'Guaranteed Uni-Cast' mode. **TODO: heuristic NODEID-based (or random?) time separation?.**

Samp-Forward-To-Santa-Data-Or-Error-Packet: **\| SAMP-FORWARD-TO-SANTA-DATA-OR-ERROR-PACKET-AND-TTL \| PAYLOAD \|**

where SAMP-FORWARD-TO-SANTA-DATA-OR-ERROR-PACKET-AND-TTL is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0]=1, bits[1..3] equal to a 3-bit constant SAMP_FORWARD_TO_SANTA_DATA_OR_ERROR_PACKET, bit [4] being IS_ERROR (indicating that PAYLOAD is in fact Routing-Error), and bits [5..] being TTL.

Samp-Forward-To-Santa-Data-Or-Error-Packet is sent by Retransmitting Device when it receives Samp-To-Santa-Data-Or-Error-Packet (with TTL=MAX_TTL-1 to account for original Samp-To-Santa-Data-Or-Error-Packet). On receiving Samp-Forward-To-Santa-Data-Or-Error-Packet by a Retransmitting Device, it is  processed as described in Uni-Cast processing section above (with implicit Target-Address being Root), and is always sent in 'Guaranteed Uni-Cast' mode.

Samp-Routing-Error-Packet: **\| SAMP-ROUTING-ERROR-PACKET-AND-TTL \| ERROR-CODE \| TODO \|**

where SAMP-ROUTING-ERROR-PACKET-AND-TTL is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0]=1, bits[1..3] equal to a 3-bit constant SAMP_ROUTING_ERROR_PACKET, bit [4] reserved (MUST be zero), and bits [5..] being TTL

On receiving Samp-Routing-Error-Packet, it is processed as described in Uni-Cast processing section above (with implicit Target-Address being Root), and is always sent in 'Guaranteed Uni-Cast' mode.

Samp-Route-Update-Packet: **\| SAMP-ROUTE-UPDATE-PACKET-FLAGS-AND-TTL \| Target-Address \| OPTIONAL-ORIGINAL-RT-CHECKSUM \| MODIFICATIONS-LIST \| RESULTING-RT-CHECKSUM \|**

where SAMP-ROUTE-UPDATE-PACKET-FLAGS-AND-TTL is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0]=1, bits[1..3] equal to a 3-bit constant SAMP_ROUTE_UPDATE_PACKET, bit [4] being DISCARD-FIRST (indicating that before processing MODIFICATIONS-LIST, the whole Routing Table must be discarded), and bits[5..] being TTL; Target-Address is the Target-Address field; OPTIONAL-ORIGINAL-RT-CHECKSUM is present only if DISCARD-FIRST flag is not set; OPTIONAL-ORIGINAL-RT-CHECKSUM is a Routing-Table-Checksum, specifying Routing Table checksum before the change is applied; if OPTIONAL-ORIGINAL-RT-CHECKSUM doesn't match to that of the Routing Table - it is TODO Routing-Error; MODIFICATIONS-LIST described below; RESULTING-RT-CHECKSUM is a Routing-Table-Checksum, specifying Routing Table Checksum after the change has been applied (if RESULTING-RT-CHECKSUM doesn't match - it is TODO Routing-Error). 

MODIFICATIONS-LIST consists of entries, where each entry looks as follows: **\| TARGET-ID-PLUS-1 \| OPTIONAL-BUS-ID-PLUS-1 \| OPTIONAL-NEXT-HOP-ACK-AND-INTRA-BUS-ID \|**

where TARGET-ID-PLUS-1 (TODO!: change if negatives are supported!) is an Encoded-Unsigned-Int<max=2> field, equal to 0 to indicate end of list, and to `TARGET-ID + 1` otherwise; OPTIONAL-BUS-ID-PLUS-1 is an Encoded-Unsigned-Int<max=2> field, present only if TARGET-ID-PLUS-1 is not 0, and equal to 0 to indicate that the route with TARGET-ID should be deleted from the Routing Table, and to `BUS-ID + 1` otherwise (in this case triplet (TARGET-ID,BUS-ID,INTRA-BUS-ID) should be added to the Routing Table); OPTIONAL-NEXT-HOP-ACK-AND-INTRA-BUS-ID is an Encoded-Unsigned-Int<max=4> bitfield substrate, present only if both TARGET-ID-PLUS-1 is not 0, and BUS-ID-PLUS-1 is not 0; bit[0] is a NEXT-HOP-ACK flag for the Routing Table Entry, and bits[1..] represent INTRA-BUS-ID.

Samp-Route-Update-Packet always go in one direction - from Root to Retransmitting Device; it's Target-Address MUST NOT be 0; it is processed as described in Uni-Cast processing section above, and is always sent in 'Guaranteed Uni-Cast' mode.

Samp-Loop-Ack-Packet: **\| SAMP-LOOP-ACK-AND-TTL \| Target-Address \| LOOP-ACK-ID \|**

where SAMP-LOOP-ACK-AND-TTL is an Encoded-Unsigned-Int<max=2> bitfield substrate, with bit[0]=1, bits[1..3] equal to a 3-bit constant SAMP_LOOP_ACK_PACKET, bit [4] being reserved (MUST be zero), and bits [5..] being TTL; Target-Address is described above, and LOOP-ACK-ID is copied from LOOP-ACK extra header of Samp-Unicast-Data-Packet. 

Samp-Loop-Ack-Packet is generated either by destination, or by the node which has found that the next hop already has NEXT-HOP-ACK flag (see details in 'Guaranteed Uni-Cast' section above); generating node always specifies itself as a target. 

Samp-Loop-Ack-Packet is processed as specified in 'Uni-cast processing' section above; Samp-Loop-Ack packet is never sent using 'Guaranteed uni-cast' delivery. Processing at the target node (regardless of node type) consists of passing PAYLOAD to the upper-layer protocol.


Type of Samp packet
^^^^^^^^^^^^^^^^^^^

As described above, type of Samp packet is always defined by bits [0..3] of the first field (which is always Encoded-Unsigned-Int<max=2> bitfield substrate):

+-------------------------------------+--------------------------------------------+--------------------------------------------+
| bit [0]                             | bits[1..3]                                 | SAMP packet type                           |
+=====================================+============================================+============================================+
| 0                                   | ANY (used for other purposes)              | Samp-Unicast-Data-Packet                   |
+-------------------------------------+--------------------------------------------+--------------------------------------------+
| 1                                   | SAMP_FROM_SANTA_DATA_PACKET                | Samp-From-Santa-Data-Packet                |
+-------------------------------------+--------------------------------------------+--------------------------------------------+
| 1                                   | SAMP_TO_SANTA_DATA_OR_ERROR_PACKET         | Samp-To-Santa-Data-Packet                  |
+-------------------------------------+--------------------------------------------+--------------------------------------------+
| 1                                   | SAMP_FORWARD_TO_SANTA_DATA_OR_ERROR_PACKET | Samp-Forward-To-Santa-Data-Or-Error-Packet |
+-------------------------------------+--------------------------------------------+--------------------------------------------+
| 1                                   | SAMP_ROUTING_ERROR_PACKET                  | Samp-Routing-Error-Packet                  |
+-------------------------------------+--------------------------------------------+--------------------------------------------+
| 1                                   | SAMP_ROUTE_UPDATE_PACKET                   | Samp-Route-Update-Packet                   |
+-------------------------------------+--------------------------------------------+--------------------------------------------+
| 1                                   | SAMP_LOOP_ACK_PACKET                       | Samp-Loop-Ack-Packet                       |
+-------------------------------------+--------------------------------------------+--------------------------------------------+
| 1                                   | 2 more values                              | RESERVED                                   |
+-------------------------------------+--------------------------------------------+--------------------------------------------+

Packet Urgency
--------------

From SAMP point of view, all upper-layer-protocol packets can have one of three urgency levels. If the packet has urgency URGENCY_LAZY, it is first sent as a Samp-Unicast-Data-Packet without GUARANTEED-DELIVERY flag (as described above, in case of retries it will be resent with GUARANTEED-DELIVERY). If the packet has urgency URGENCY_URGENT, it is first sent as a Samp-Unicast-Data-Packet with GUARANTEED-DELIVERY flag (as described above, in case of retries it will be resent as a Samp-\*-Santa-\* packet). If the packet has urgency URGENCY_TRIPLE_GALOP, 
then it is first sent as a Samp-From-Santa-Data-Packet or Samp-To-Santa-Data-Packet (depending on source being Root or Device). 

TODO: store and update MAX_TTL for Retransmitting Devices
TODO: Route-Update for non-Retransmitting Devices?
TODO: header (or full packet?) checksums! (or is it SADLP-\*'s responsibility?)
TODO: negative NODE-ID (TARGET-ID etc.) to facilitate ID-based time delays for Samp-To-Santa packets? (TODO: time delays to cover the whole the path?)

