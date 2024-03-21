/*
 * Easy_CAN6.c
 *
 *  Created on: Oct 18, 2022
 *      Author: ke_to
 */

#include "Easy_CAN6.h"

#include<string.h>

#ifdef HAL_CAN_MODULE_ENABLED
void Easy_CAN6_Start(Easy_CAN6_Typedef *ecan, CAN_HandleTypeDef *hcan,
		uint8_t can_nuumber) {
	ecan->hcan = hcan;
	ecan->filter.FilterIdHigh = 0;
	ecan->filter.FilterIdLow = 0;
	ecan->filter.FilterMaskIdHigh = 0;
	ecan->filter.FilterMaskIdLow = 0;
	ecan->filter.FilterFIFOAssignment = CAN_FILTER_FIFO0;

	if (can_nuumber == 1)
		ecan->filter.FilterBank = 0;
	else
		ecan->filter.FilterBank = 14;

	ecan->filter.FilterMode = CAN_FILTERMODE_IDMASK;
	ecan->filter.FilterScale = CAN_FILTERSCALE_32BIT;
	ecan->filter.FilterActivation = CAN_FILTER_ENABLE;
	ecan->filter.SlaveStartFilterBank = 14;

	if (HAL_CAN_ConfigFilter(ecan->hcan, &(ecan->filter)) != HAL_OK)
		Error_Handler();
	if (HAL_CAN_ActivateNotification(ecan->hcan, CAN_IT_RX_FIFO0_MSG_PENDING)
			!= HAL_OK)
		Error_Handler();
	if (HAL_CAN_Start(ecan->hcan) != HAL_OK)
		HAL_NVIC_SystemReset();

}
void Easy_CAN6_Transmit(Easy_CAN6_Typedef *ecan, uint16_t std_id,
		uint8_t *txdata, uint8_t size) {
	uint32_t TxMailbox = 0;
	ecan->TxHeader.StdId = std_id;
	ecan->TxHeader.IDE = CAN_ID_STD;
	ecan->TxHeader.RTR = CAN_RTR_DATA;
	ecan->TxHeader.DLC = size;
	ecan->TxHeader.TransmitGlobalTime = DISABLE;
	if (HAL_CAN_GetTxMailboxesFreeLevel(ecan->hcan) > 0)
		HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);
}

void Easy_CAN6_Transmit_Ext(Easy_CAN6_Typedef *ecan, uint32_t ext_id,
		uint8_t *txdata, uint8_t size) {
	uint32_t TxMailbox = 0;
	ecan->TxHeader.ExtId = ext_id;
	ecan->TxHeader.IDE = CAN_ID_EXT;
	ecan->TxHeader.RTR = CAN_RTR_DATA;
	ecan->TxHeader.DLC = size;
	ecan->TxHeader.TransmitGlobalTime = DISABLE;
	if (HAL_CAN_GetTxMailboxesFreeLevel(ecan->hcan) > 0)
		HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);
}

void Easy_CAN6_ForceTransmit(Easy_CAN6_Typedef *ecan, uint16_t std_id,
		uint8_t *txdata, uint8_t size) {
	uint32_t TxMailbox = 0;
	ecan->TxHeader.StdId = std_id;
	ecan->TxHeader.IDE = CAN_ID_STD;
	ecan->TxHeader.RTR = CAN_RTR_DATA;
	ecan->TxHeader.DLC = size;
	ecan->TxHeader.TransmitGlobalTime = DISABLE;

	if (HAL_CAN_GetTxMailboxesFreeLevel(ecan->hcan) > 0)
		HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);
	else {
		HAL_CAN_Stop(ecan->hcan);
		HAL_CAN_Start(ecan->hcan);

		HAL_CAN_AbortTxRequest(ecan->hcan, CAN_TX_MAILBOX0);
		HAL_CAN_AbortTxRequest(ecan->hcan, CAN_TX_MAILBOX1);
		HAL_CAN_AbortTxRequest(ecan->hcan, CAN_TX_MAILBOX2);
		HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);

	}
}

void Easy_CAN6_ForceTransmit_Ext(Easy_CAN6_Typedef *ecan, uint32_t ext_id,
		uint8_t *txdata, uint8_t size) {
	uint32_t TxMailbox = 0;
	ecan->TxHeader.ExtId = ext_id;
	ecan->TxHeader.IDE = CAN_ID_EXT;
	ecan->TxHeader.RTR = CAN_RTR_DATA;
	ecan->TxHeader.DLC = size;
	ecan->TxHeader.TransmitGlobalTime = DISABLE;

	if (HAL_CAN_GetTxMailboxesFreeLevel(ecan->hcan) > 0)
		HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);
	else {
		HAL_CAN_Stop(ecan->hcan);
		HAL_CAN_Start(ecan->hcan);

		HAL_CAN_AbortTxRequest(ecan->hcan, CAN_TX_MAILBOX0);
		HAL_CAN_AbortTxRequest(ecan->hcan, CAN_TX_MAILBOX1);
		HAL_CAN_AbortTxRequest(ecan->hcan, CAN_TX_MAILBOX2);
		HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);

	}
}

void Easy_CAN6_BlockingTransmit(Easy_CAN6_Typedef *ecan, uint16_t std_id,
		uint8_t *txdata, uint8_t size) {
	uint32_t TxMailbox = 0;
	ecan->TxHeader.StdId = std_id;
	ecan->TxHeader.IDE = CAN_ID_STD;
	ecan->TxHeader.RTR = CAN_RTR_DATA;
	ecan->TxHeader.DLC = size;
	ecan->TxHeader.TransmitGlobalTime = DISABLE;

	while (HAL_CAN_GetTxMailboxesFreeLevel(ecan->hcan) == 0)
		asm("NOP");
	HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);

}

void Easy_CAN6_BlockingTransmit_Ext(Easy_CAN6_Typedef *ecan, uint32_t ext_id,
		uint8_t *txdata, uint8_t size) {
	uint32_t TxMailbox = 0;
	ecan->TxHeader.ExtId = ext_id;
	ecan->TxHeader.IDE = CAN_ID_EXT;
	ecan->TxHeader.RTR = CAN_RTR_DATA;
	ecan->TxHeader.DLC = size;
	ecan->TxHeader.TransmitGlobalTime = DISABLE;

	while (HAL_CAN_GetTxMailboxesFreeLevel(ecan->hcan) == 0)
		asm("NOP");
	HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);

}

void Easy_CAN6_BlockingTransmit_Ext_Remote(Easy_CAN6_Typedef *ecan,
		uint32_t ext_id, uint8_t *txdata, uint8_t size) {
	uint32_t TxMailbox = 0;
	ecan->TxHeader.ExtId = ext_id;
	ecan->TxHeader.IDE = CAN_ID_EXT;
	ecan->TxHeader.RTR = CAN_RTR_REMOTE;
	ecan->TxHeader.DLC = size;
	ecan->TxHeader.TransmitGlobalTime = DISABLE;

	while (HAL_CAN_GetTxMailboxesFreeLevel(ecan->hcan) == 0)
		asm("NOP");
	HAL_CAN_AddTxMessage(ecan->hcan, &(ecan->TxHeader), txdata, &TxMailbox);

}

void Easy_CAN6_GetMessage(Easy_CAN6_Typedef *ecan) {
	HAL_CAN_GetRxMessage(ecan->hcan, CAN_RX_FIFO0, &(ecan->RxHeader),
			ecan->rxbuf);
}

void Easy_CAN6_Set_Raw_Binary(Easy_CAN6_Typedef *ecan, uint8_t *databox) {
	memcpy(databox, ecan->rxbuf, ecan->RxHeader.DLC);
}

uint16_t Easy_CAN6_GetID(Easy_CAN6_Typedef *ecan) {
	return ecan->RxHeader.StdId;
}
#endif
