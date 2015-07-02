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

#ifdef MASTER_ENABLE_ALT_TEST_MODE

#if !defined __SA_TEST_CONTROL_PROG_H__
#define __SA_TEST_CONTROL_PROG_H__

#include "../../firmware/src/common/sa_common.h"
#include "../../firmware/src/common/sa_data_types.h"
#include "../../firmware/src/common/zepto_mem_mngmt.h"

#define CONTROL_PROG_OK 0
#define CONTROL_PROG_CONTINUE 1
#define CONTROL_PROG_PASS_LOWER 2
#define CONTROL_PROG_PASS_LOWER_THEN_IDLE 4
/*#define CONTROL_PROG_WAIT_TO_CONTINUE 4*/

typedef struct _DefaultTestingControlProgramState 
{
	uint8_t state; //'0' means 'be ready to process incoming command', '1' means 'prepare reply'
	uint16_t last_sent_id;
	uint16_t currChainID[2];
	uint16_t currChainIdBase[2];
	uint8_t first_byte;
	uint16_t chain_id[2];
	uint16_t chain_ini_size;
	uint16_t reply_to_id;
	uint16_t self_id;
} DefaultTestingControlProgramState;

uint8_t default_test_control_program_init( void* control_prog_state );
//uint8_t default_test_control_program_accept_reply( void* control_prog_state, uint8_t packet_status, parser_obj* received, uint16_t sz );
uint8_t default_test_control_program_accept_reply_continue( void* control_prog_state, MEMORY_HANDLE reply );
uint8_t default_test_control_program_start_new( void* control_prog_state, MEMORY_HANDLE reply );
uint8_t default_test_control_program_accept_reply( MEMORY_HANDLE mem_h, sasp_nonce_type chain_id, void* control_prog_state );
uint8_t _default_test_control_program_accept_reply( void* control_prog_state, uint8_t packet_status, parser_obj* received );

#endif // __SA_TEST_CONTROL_PROG_H__

#endif // MASTER_ENABLE_ALT_TEST_MODE