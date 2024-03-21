/*
 * CyberGear.h
 *
 *  Created on: Nov 1, 2023
 *      Author: ke_to
 */

#ifndef CYBERGEAR_H_
#define CYBERGEAR_H_

#include"main.h"

#include "Easy_CAN6.h"

#ifdef HAL_CAN_MODULE_ENABLED

#define MODE_MOTION   0x00
#define MODE_POSITION 0x01
#define MODE_SPEED    0x02
#define MODE_CURRENT  0x03

typedef struct {
	uint8_t master_id;
	uint8_t id;                   //!< motor id
	float limit_speed;            //!< limit speed (rad/s)
	float limit_current;          //!< limit current (A)
	float limit_torque;           //!< limit torque (Nm)
	float current_kp;             //!< control parameter kp for current control
	float current_ki;             //!< control parameter ki for current control
	float current_filter_gain;    //!< current filter gain
} CybergearConfig_Typedef;

typedef struct {
	float position;   //!< target position
	float velocity;   //!< target velocity (rad/sec)
	float effort;     //!< target effort
	float kp;         //!< motion control kp
	float kd;         //!< motion control kd
} CybergearMotionCommand_Typedef;

typedef struct {
	uint16_t feedback_info;
	float feedback_pos;
	float feedback_speed;
	float feedback_torque;
	float feetback_temp;
} CybergearFeedbackData_Typedef;

typedef struct {
	uint8_t run_mode;         //0x7005
	float iq_ref;         //0x7006
	float spd_ref;         //0x700A
	float limit_torque;         //0x700B
	float cur_kp;         //0x7010
	float cur_ki;         //0x7011
	float cur_filt_gain;         //0x7014
	float loc_ref;         //0x7016
	float limit_spd;         //0x7017
	float limit_cur;         //0x7018
	float mechPos;         //0x7019
	float iqf;         //0x701A
	float mechVel;         //0x701B
	float VBUS;         //0x701C
	int16_t rotation;         //0x701D
} CybergearIndexPram_Typedef;

typedef struct {
	uint32_t ext_id;

	uint8_t com_type;
	uint16_t data_area2;
	uint8_t target_id;
	uint8_t data_area1[8];
} CybergearCANProtcol_Typedef;

typedef struct {

	Easy_CAN6_Typedef *ecan;
	CybergearConfig_Typedef cyberconfig;
	CybergearMotionCommand_Typedef cybermotion;
	CybergearFeedbackData_Typedef cyberfeedback;
	CybergearIndexPram_Typedef cyberindex;
	CybergearCANProtcol_Typedef tx_candata, rx_candata;
	void (*delay)(uint32_t);
} CyberGear_Typedef;
#endif

void CyberGear_SendCANData(CyberGear_Typedef *cyber, uint8_t com_type,
		uint16_t data_area2, uint8_t target_id, uint8_t *data_area1);
void CyberGear_UnpackCANData(CyberGear_Typedef *cyber,
		CAN_RxHeaderTypeDef rxheader, uint8_t *rxbuf);
uint8_t CyberGear_GetComType(CyberGear_Typedef *cyber);
uint16_t CyberGaer_GetDataArea2(CyberGear_Typedef *cyber);
uint8_t CyberGear_GetTargetID(CyberGear_Typedef *cyber);

void CyberGear_Init(CyberGear_Typedef *cyber, Easy_CAN6_Typedef *ecan,
		uint8_t motor_id, uint8_t master_id, void (*delay)(uint32_t));
void CyberGear_SetConfig(CyberGear_Typedef *cyber, float torque_limit,
		float speed_limit, float current_limit);
void CyberGear_SetMode(CyberGear_Typedef *cyber, uint8_t mode);
void CyberGear_SpeedLimit(CyberGear_Typedef *cyber, float limit);
void CyberGear_TorqueLimit(CyberGear_Typedef *cyber, float limit);
void CyberGear_CurrentLimit(CyberGear_Typedef *cyber, float limit);
void CyberGear_CurrentControlPram(CyberGear_Typedef *cyber, float kp, float ki,
		float gain);
void CyberGear_ControlSpeed(CyberGear_Typedef *cyber, float target_speed);
void CyberGear_ControlPosition(CyberGear_Typedef *cyber, float target_position);

void CyberGear_GetDeviceID(CyberGear_Typedef *cyber);
void CyberGear_DriveMotor(CyberGear_Typedef *cyber, float target_torque,
		float target_position, float target_speed, float kp, float kd);
void CyberGear_EnableMotor(CyberGear_Typedef *cyber);
void CyberGear_ResetMotor(CyberGear_Typedef *cyber);
void CyberGear_ResetZEROPos(CyberGear_Typedef *cyber);
void CyberGear_ChangeCANID(CyberGear_Typedef *cyber, uint8_t id);
void CyberGear_ReadIndexParam(CyberGear_Typedef *cyber, uint16_t index);
void CyberGear_WriteIndexParam(CyberGear_Typedef *cyber, uint16_t index,
		uint8_t *write_data);
void CyberGear_ReadAllIndexPram(CyberGear_Typedef *cyber);

void CyberGear_CANRxTask(CyberGear_Typedef *cyber, CAN_HandleTypeDef *hcan,
		CAN_RxHeaderTypeDef rxheader, uint8_t *rxbuf);
#endif /* CYBERGEAR_H_ */
