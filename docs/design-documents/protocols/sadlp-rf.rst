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

.. _sadlp-rf:

SmartAnthill DLP for RF (SADLP-RF)
==================================

:Version:   v0.4.1

*NB: this document relies on certain terms and concepts introduced in* :ref:`saoverarch` *and* :ref:`saprotostack` *documents, please make sure to read them before proceeding.*

SADLP-RF provides L2 datalink over simple Radio-Frequency channels which have only an ability to send/receive packets over RF without any addressing. For more complicated RF communications (such as IEEE 802.15.4), different SADLP-\* protocols (such as SADLP-802.15.4 described in :ref:`sadlp-802-15-4`) need to be used.

SADLP-RF Design
---------------

Assumptions:

* We're assuming to operate in a noisy environment. Hence, we need to use forward error correction.
* error correction level is to be specified by an upper protocol layer for each packet separately (for example, retransmits may use higher error correction levels)
* We don't have enough resources to run sophisticated error-correction mechanisms such as Reed-Solomon, Viterbi, etc.
* Transmissions are rare, hence beacons and frequency hopping are not used
* upper protocol layer may have some use for packets where only a header is provided; hence upper layer provides it's header and it's payload separately

SADLP-RF PHY Level
------------------

Frequencies: TODO (with frequency shifts)

Modulation: 2FSK (a.k.a. FSK without further specialization, and BFSK), or GFSK (2FSK and GFSK are generally compatible), with frequency shifts specified above.

Tau (minimum period with the same frequency during FSK modulation): 1/9600 sec. *NB: this may or may not correspond to 9600 baud transfer rate.* (TODO: rate negotiation?)

Line code: preamble (at least two 0xAA (TODO:check if it is really 0xAA or 0x55) symbols), followed by 0x2DD4 sync word, followed by "raw" SADLP-RF Packet as described below. 

SADLP-RF Packets and Line Codes
-------------------------------

FSK modulation used by SADLP-RF, does not require AC/DC balance. However, it requires to have at least one edge per N*tau (to keep synchronization). To be usable with a wide range of transmitters/receivers, we aim for strict guarantees of at least one edge per 16*tau (as suggested, for example, for a worst-case in RFM69 manual), and for "white noise" properties for pre-SCRAMBLED packets (see :ref:`sascrambling` document for details on SCRAMBLING). For those SADLP-RF packets which allow for intra-packet de-synchronization detection (in particular, for HAMM32-based packets), one edge per 32*tau is acceptable.

The guarantees above are kept for all SADLP-RF Packets, as described below. As a result, SADLP-RD does not need any additional line codes, and SADLP-RF Packets MUST be transmitted directly over FSK (after preamble and sync word, as described above above).

Non-paired Addressing for RF Buses
----------------------------------

Each RF frequency channel on a Device represents a "wireless bus" in terms of SAMP. For "intra-bus address" as a part "non-paired addressing" (as defined in :ref:`samp`), RF Devices MUST use randomly generated 64-bit ID. 

If Device uses hardware-assisted Fortuna PRNG (as described in :ref:`sarng` document), Device MUST complete Phase 1 of "Entropy Gathering Procedure" (as described in :ref:`sapairing` document) to initialize Fortuna PRNG *before* generating this 64-bit ID. Then, Device should proceed to Phase 2 (providing Device ID), and Phase 3 (entropy gathering for key generation purposes), as described in :ref:`sapairing` document.

Device Discovery and Pairing
----------------------------

For Devices with OtA Pairing (as described in :ref:`sapairing`), "Device Discovery" procedure described in :ref:`samp` document is used, with the following clarifications:

* SAMP "channel scan" for SADLP-RF is performed as follows:

  - "candidate channel" list consists of all the channels allowed in target area
  - for each of candidate channels:

    + the first packet as described in SAMP "Device Discovery" procedure is sent by Device
    + if a reply is received indicating that Root is ready to proceed with "pairing" - "pairing" is continued over this channel
      
      - if "pairing" fails, then the next available "candidate channel" is processed. 
      - to handle the situation when "pairing" succeeds, but Device is connected to wrong Central Controller - Device MUST (a) provide a visual indication that it is "paired", (b) provide a way (such as jumper or button) allowing to drop current "pairing" and continue processing "candidate channels". In the latter case, Device MUST process remaining candidate channels before re-scanning.
 
    + if a reply is received with ERROR-CODE = ERROR_NOT_AWAITING_PAIRING, or if there is no reply within 500 msec, the procedure is repeated for the next candidate channel

  - if the list of "candidate channels" is exhausted without "pairing", the whole "channel scan" is repeated (indefinitely, or with a 5-or-more-minute limit - if the latter, then "not scanning anymore" state MUST be indicated on the Device itself - TODO acceptable ways of doing it, and the scanning MUST be resumed if user initiates "re-pairing" on the Device), starting from an "active scan" as described above


SADLP-RF Packet
---------------

SADLP-RF packet has the following format:

**\| ENCODING-TYPE \| SADLP-RF-DATA \|**

where ENCODING-TYPE is 1-byte fields (see below).

ENCODING-TYPE is an error-correctable field, described by the following table:

+------------------------+---------------------------------------+-------------------------------+
| ENCODING-TYPE          | Meaning                               | Value after Hamming Decoding  | 
+------------------------+---------------------------------------+-------------------------------+
| 0x00                   | RESERVED (NOT RECOMMENDED)            | 0                             |
+------------------------+---------------------------------------+-------------------------------+
| 0x69                   | RESERVED (MANCHESTER-COMPATIBLE)      | 1                             |
+------------------------+---------------------------------------+-------------------------------+
| 0xAA                   | RESERVED (MANCHESTER-COMPATIBLE)      | 2                             |
+------------------------+---------------------------------------+-------------------------------+
| 0xC3                   | PLAIN16-NO-CORRECTION                 | 3                             |
+------------------------+---------------------------------------+-------------------------------+
| 0xCC                   | HAMMING-32-CORRECTION                 | 4                             |
+------------------------+---------------------------------------+-------------------------------+
| 0xA5                   | RESERVED (MANCHESTER-COMPATIBLE)      | 5                             |
+------------------------+---------------------------------------+-------------------------------+
| 0x66                   | RESERVED (MANCHESTER-COMPATIBLE)      | 6                             |
+------------------------+---------------------------------------+-------------------------------+
| 0x0F                   | RESERVED                              | 7                             |
+------------------------+---------------------------------------+-------------------------------+
| 0xF0                   | RESERVED                              | 8                             |
+------------------------+---------------------------------------+-------------------------------+
| 0x99                   | RESERVED (MANCHESTER-COMPATIBLE)      | 9                             |
+------------------------+---------------------------------------+-------------------------------+
| 0x5A                   | RESERVED (MANCHESTER-COMPATIBLE)      | 10                            |
+------------------------+---------------------------------------+-------------------------------+
| 0x33                   | HAMMING-32-2D-CORRECTION              | 11                            |
+------------------------+---------------------------------------+-------------------------------+
| 0x3C                   | RESERVED                              | 12                            |
+------------------------+---------------------------------------+-------------------------------+
| 0x55                   | RESERVED (MANCHESTER-COMPATIBLE)      | 13                            |
+------------------------+---------------------------------------+-------------------------------+
| 0x96                   | RESERVED (MANCHESTER-COMPATIBLE)      | 14                            |
+------------------------+---------------------------------------+-------------------------------+
| 0xFF                   | RESERVED (NOT RECOMMENDED)            | 15                            |
+------------------------+---------------------------------------+-------------------------------+

All listed ENCODING-TYPEs have "Hamming Distance" of at least 4 between them. It means that error correction can be applied to ENCODING-TYPE, based on "Hamming Distance", as described below (for error correction to work, "Hamming Distance" must be at least 3).

ENCODING-TYPE can be considered as a Hamming (7.4) code as described in https://en.wikipedia.org/wiki/Hamming_code, with a prepended parity bit to make it SECDED. Note: implementation is not strictly required to perform Hamming decoding; instead, the following procedure MAY be used for error correction of ENCODING-TYPE:

* calculate "Hamming Distance" of received ENCODING-TYPE with one of supported values (NO-CORRECTION, HAMMING-32-CORRECTION, and HAMMING-32-2D-CORRECTION)
* if "Hamming Distance" is 0 or 1, than we've found the error-corrected ENCODING-TYPE
* otherwise - repeat the process with another supported value
* if we're out of supported values - ENCODING-TYPE is beyond repair, and we SHOULD drop the whole packet

To check that "Hamming Distance" of bytes a and b is <=1:

* calculate d = a XOR b
* calculate number of 1's in d

  + if MCU supports this as an asm operation - it is better to use it
  + otherwise, either shift-and-add-if
  + or compare with each of (0,1,2,4,8,16,32,64,128) - if doesn't match any, "Hamming Distance" is > 1

PLAIN16 Block
^^^^^^^^^^^^^

PLAIN16 block is always a 16-bit (2-byte) block. It consists of 15 data bits d0..d15, followed by 16th bit p, where p = ~d15 (inverted d15). p is necessary to provide strict guarantees that there is at least 1 bit change every 16 bits of data stream. On receiving side, p is ignored (though if bit-error counter is enabled, and p it is not equal to ~d15, it SHOULD be counted as a bit-error). 

Converting Data Block into a Sequence of PLAIN16 Blocks
'''''''''''''''''''''''''''''''''''''''''''''''''''''''

To produce PLAIN16-BLOCK-SEQUENCE from DATA-BLOCK, the following procedure is used:

* PADDED-DATA-BLOCK is formed as `\| DATA-BLOCK \| padding \|`, where padding is random data (using non-key random stream as specified in :ref:`sarng`) with a size, necessary to make the bitsize of PADDED-DATA-BLOCK a multiple of 15. *NB: Within implementation, PADDED-DATA-BLOCK is usually implemented virtually*
* resulting bit sequence (which has bitsize which is a multiple of 15) is split into 15-bit chunks, and each 15-bit chunk is converted into a 16-bit PLAIN16 block

PLAIN16-NO-CORRECTION Packets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For PLAIN16-NO-CORRECTION packets, SADLP-RF-DATA has the following format:

**\| UPPER-LAYER-PAYLOAD-AND-DATA-PLAIN16 \|**

where PLAIN16-DATA is a conversion of UPPER-LAYER-PAYLOAD-AND-DATA into a sequence of PLAIN16 blocks, where UPPER-LAYER-PAYLOAD-AND-DATA is described below, and conversion is performed as described above.

UPPER-LAYER-PAYLOAD-AND-DATA has the following format:

**\| UPPER-LAYER-HEADER-LENGTH \| UPPER-LAYER-HEADER \| UPPER-LAYER-HEADER-CHECKSUM \| UPPER-LAYER-PAYLOAD-LENGTH \| UPPER-LAYER-PAYLOAD \| UPPER-LAYER-HEADER-AND-PAYLOAD-CHECKSUM \|**

where UPPER-LAYER-HEADER-LENGTH is an Encoded-Unsigned-Int<max=2> field specifying size of UPPER-LAYER-HEADER, UPPER-LAYER-HEADER-CHECKSUM is a 2-byte field containing SACHECKSUM-16 of UPPER-LAYER-HEADER, UPPER-LAYER-PAYLOAD-LENGTH is an Encoded-Unsigned-Int<max=2> field specifying size of UPPER-LAYER-PAYLOAD, and UPPER-LAYER-HEADER-AND-PAYLOAD CHECKSUM is a 2-byte field containing SACHECKSUM-16 of UPPER-LAYER-HEADER concatenated with UPPER-LAYER-PAYLOAD.

HAMM32 block
^^^^^^^^^^^^

HAMM32 block is always a 32-bit (4-byte) block. It is a Hamming (31,26)-encoded block where d1..d26 are data bits and p1,p2,p4,p8,p16 are parity bits as described in https://en.wikipedia.org/wiki/Hamming_code, then HAMM32 block is built as follows:

**\| p0 \| ~p1 \| ~p2 \| d1 \| ~p4 \| d2 \| d3 \| d4 \| ~p8 \| d5 \| d6 \| d7 \| d8 \| d9 \| d10 \| d11 \| ~p16 \| d12 \| d13 \| d14 \| d15 \| d16 \| d17 \| d18 \| d19 \| d20 \| d21 \| d22 \| d23 \| d24 \| d25 \| d26 \|**

where '~' denotes bit inversion, and p0 is calculated to make the whole 32-bit HAMM32 parity even (making HAMM32 a SECDED block).

Parity bit inversion is needed to make sure that HAMM32 block can never be all-zeros or all-ones (and simple inversion doesn't change Hamming Distances, so error correction on the receiving side is essentially the same as for non-inverted parity bits). HAMM32 blocks guarantee that there is at least one change-from-zero-to-one-or-vice-versa at least every 32 bits. 

Converting Data Block into a Sequence of HAMM32 Blocks
''''''''''''''''''''''''''''''''''''''''''''''''''''''

To produce HAMM32-BLOCK-SEQUENCE from DATA-BLOCK, the following procedure is used:

* PADDED-DATA-BLOCK is formed as `\| DATA-BLOCK \| padding \|`, where padding is random data (using non-key random stream as specified in :ref:`sarng`) with a size, necessary to make the bitsize of PADDED-DATA-BLOCK a multiple of 26. *NB: Within implementation, PADDED-DATA-BLOCK is usually implemented virtually*
* resulting bit sequence (which has bitsize which is a multiple of 26) is split into 26-bit chunks, and each 26-bit chunk is converted into a 32-bit HAMM32 block

HAMMING-32-CORRECTION Packets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For HAMMING-32-CORRECTION packets, SADLP-RF-DATA is **\| UPPER-LAYER-HEADER-HAMM32 \| UPPER-LAYER-PAYLOAD-HAMM32 \|**

where UPPER-LAYER-HEADER-HAMM32 is a conversion of UPPER-LAYER-HEADER into a sequence of HAMM32 blocks, and UPPER-LAYER-PAYLOAD-HAMM32 is a conversion of UPPER-LAYER-PAYLOAD into a sequence of HAMM32 blocks. UPPER-LAYER-HEADER and UPPER-LAYER-PAYLOAD are described below, and conversions are performed as described above.

UPPER-LAYER-HEADER has the following format:

**\| UPPER-LAYER-HEADER-LENGTH \| UPPER-LAYER-HEADER \| UPPER-LAYER-HEADER-CHECKSUM \|**

where UPPER-LAYER-HEADER-LENGTH is an Encoded-Unsigned-Int<max=2> field specifying size of UPPER-LAYER-HEADER, and UPPER-LAYER-HEADER-CHECKSUM is a 2-byte field containing SACHECKSUM-16  of UPPER-LAYER-HEADER.

UPPER-LAYER-PAYLOAD has the following format:

**\| UPPER-LAYER-PAYLOAD-LENGTH \| UPPER-LAYER-PAYLOAD \| UPPER-LAYER-HEADER-AND-PAYLOAD-CHECKSUM \|**

where UPPER-LAYER-PAYLOAD-LENGTH is an Encoded-Unsigned-Int<max=2> field specifying size of UPPER-LAYER-PAYLOAD, and UPPER-LAYER-HEADER-AND-PAYLOAD CHECKSUM is a 2-byte field containing SAHECKSUM-16 of UPPER-LAYER-HEADER concatenated with UPPER-LAYER-PAYLOAD.

HAMMING-32-2D-CORRECTION Packets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

HAMMING-32-2D-CORRECTION is similar to HAMMING-32-CORRECTION, with the following differences.

Both UPPER-LAYER-HEADER-WITH-HAMMING-32 and UPPER-LAYER-PAYLOAD-WITH-HAMMING-32 have 26 additional Hamming checksums added at the end; each Hamming checksum #i consists of N parity bits of Hamming code, calculated over all bits #i in 26-bit data bits within HAMM32 blocks. Number N is a number of Hamming bits necessary to provide error correction for NN=NUMBER-OF-HAMM32-BLOCKS. Hamming checksums are encoded as a bitstream, without intermediate padding, but padded at the end to a byte boundary with random (non-key-stream) data.

For example, if original block is 50 bytes long, then it will be split into 16 26-bit blocks, which will be encoded as 16 HAMM32 blocks; then, for HAMMING-32-2D-CORRECTION, additional 26 Hamming checksums (5 bits each, as for NN=16 N=5) will be added. Therefore, original 50 bytes will be encoded as 4*16+17=81 byte (62% overhead).

