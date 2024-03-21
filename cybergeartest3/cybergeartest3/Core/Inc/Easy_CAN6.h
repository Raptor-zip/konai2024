/*
 * Easy_CAN6.h
 *
 *  Created on: Oct 18, 2022
 *      Author: ke_to
 */

#ifndef EASY_CAN6_H_
#define EASY_CAN6_H_

#include"main.h"

#ifdef HAL_CAN_MODULE_ENABLED

typedef struct {
	CAN_HandleTypeDef *hcan;
	CAN_RxHeaderTypeDef RxHeader;
	CAN_TxHeaderTypeDef TxHeader;
	CAN_FilterTypeDef filter;
	uint8_t rxbuf[8];
} Easy_CAN6_Typedef;

void Easy_CAN6_Start(Easy_CAN6_Typedef *ecan, CAN_HandleTypeDef *hcan,
		uint8_t can_nuumber);

void Easy_CAN6_Transmit(Easy_CAN6_Typedef *ecan, uint16_t std_id,
		uint8_t *txdata, uint8_t size);
void Easy_CAN6_Transmit_Ext(Easy_CAN6_Typedef *ecan, uint32_t ext_id,
		uint8_t *txdata, uint8_t size);

void Easy_CAN6_ForceTransmit(Easy_CAN6_Typedef *ecan, uint16_t std_id,
		uint8_t *txdata, uint8_t size);
void Easy_CAN6_ForceTransmit_Ext(Easy_CAN6_Typedef *ecan, uint32_t ext_id,
		uint8_t *txdata, uint8_t size);

void Easy_CAN6_BlockingTransmit(Easy_CAN6_Typedef *ecan, uint16_t std_id,
		uint8_t *txdata, uint8_t size);
void Easy_CAN6_BlockingTransmit_Ext(Easy_CAN6_Typedef *ecan, uint32_t ext_id,
		uint8_t *txdata, uint8_t size);
void Easy_CAN6_BlockingTransmit_Ext_Remote(Easy_CAN6_Typedef *ecan,
		uint32_t ext_id, uint8_t *txdata, uint8_t size);

void Easy_CAN6_GetMessage(Easy_CAN6_Typedef *ecan);
void Easy_CAN6_Set_Raw_Binary(Easy_CAN6_Typedef *ecan, uint8_t *databox);
uint16_t Easy_CAN6_GetID(Easy_CAN6_Typedef *ecan);
#endif

#endif /* EASY_CAN6_H_ */
