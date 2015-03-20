/*******************************************************************************
Copyright (C) 2015 OLogN Technologies AG

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 2 as 
    published by the Free Software Foundation.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*******************************************************************************/


#if !defined __SA_COMMON_H__
#define __SA_COMMON_H__

// common includes
#include <memory.h> // for memcpy(), memset(), memcmp(). Note: their implementation may or may not be more effective than just by-byte operation on a particular target platform
#include <assert.h>

// data types
#define uint8_t unsigned char
#define int8_t char
#define uint16_t unsigned short

// Master/Slave distinguishing bit; USED_AS_MASTER is assumed to be a preprocessor definition if necessary
#ifdef USED_AS_MASTER
#define MASTER_SLAVE_BIT 1
#else // USED_AS_MASTER
#define MASTER_SLAVE_BIT 0
#endif

// offsets in data segment of particular handler data
// note: internal structure is defined by a correspondent handler (see respective .h files for details)
// TODO: think about more reliable mechanism
#define DADA_OFFSET_SASP 0
#define DADA_OFFSET_SAGDP ( DADA_OFFSET_SASP + 28 )
#define DADA_OFFSET_NEXT ( DADA_OFFSET_SAGDP + 34 )

// debug helpers

#define DEBUG_PRINTING

#ifdef DEBUG_PRINTING
#include <stdio.h>
#define PRINTF printf
#else // DEBUG_PRINTING
#define PRINTF
#endif // DEBUG_PRINTING


// counter system
#define ENABLE_COUNTER_SYSTEM

#define ENABLE_COUNTER_SYSTEM
#ifdef ENABLE_COUNTER_SYSTEM
#define MAX_COUNTERS_CNT 100
extern size_t COUNTERS[MAX_COUNTERS_CNT];
extern const char* CTRS_NAMES[MAX_COUNTERS_CNT];
extern double COUNTERS_D[MAX_COUNTERS_CNT];
extern const char* CTRS_NAMES_D[MAX_COUNTERS_CNT];
#define INIT_COUNTER_SYSTEM \
	memset( COUNTERS, 0, sizeof(COUNTERS) ); \
	memset( CTRS_NAMES, 0, sizeof(CTRS_NAMES) ); \
	memset( COUNTERS_D, 0, sizeof(COUNTERS_D) ); \
	memset( CTRS_NAMES_D, 0, sizeof(CTRS_NAMES_D) ); 
void printCounters();
#define PRINT_COUNTERS() printCounters()
#define TEST_CTR_SYSTEM
#ifdef TEST_CTR_SYSTEM
#define INCREMENT_COUNTER( i, name ) \
	{if ( (COUNTERS[i]) != 0 ); else { assert( CTRS_NAMES[i] == NULL ); CTRS_NAMES[i] = name; } \
	(COUNTERS[i])++;}
#define INCREMENT_COUNTER_IF( i, name, cond ) \
	{ if ( cond ) {if ( (COUNTERS[i]) != 0 ); else { assert( CTRS_NAMES[i] == NULL ); CTRS_NAMES[i] = name; } \
	(COUNTERS[i])++;} }
#define UPDATE_MAX_COUNTER( i, name, val ) \
	{CTRS_NAMES[i] = name; \
	if ( COUNTERS[i] >= val ); else COUNTERS[i] = val;}
#else // TEST_CTR_SYSTEM
#define INCREMENT_COUNTER( i, name ) (COUNTERS[i])++;
#endif // TEST_CTR_SYSTEM

#else
#define PRINT_COUNTERS()
#endif // ENABLE_COUNTER_SYSTEM

#endif // __SA_COMMON_H__