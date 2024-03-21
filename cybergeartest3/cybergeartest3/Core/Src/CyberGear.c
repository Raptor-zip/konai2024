/*
 * CyberGear.c
 *
 *  Created on: Nov 1, 2023
 *      Author: ke_to
 */

#include "CyberGear.h"
#include <string.h>

#ifdef HAL_CAN_MODULE_ENABLED

#define P_MIN -12.5f
#define P_MAX 12.5f
#define V_MIN -30.0f
#define V_MAX 30.0f
#define KP_MIN 0.0f
#define KP_MAX 500.0f
#define KD_MIN 0.0f
#define KD_MAX 5.0f
#define T_MIN -12.0f
#define T_MAX 12.0f

union uint16_binary {
	uint16_t data;
	uint8_t bin[2];
};
union uint32_binary {
	uint32_t data;
	uint8_t bin[4];
};
union int16_binary {
	int16_t data;
	uint8_t bin[2];
};
union float_binary {
	float data;
	uint8_t bin[4];
};

static int float_to_uint(float x, float x_min, float x_max, int bits) {
	float span = x_max - x_min;
	float offset = x_min;
	if (x > x_max)
		x = x_max;
	else if (x < x_min)
		x = x_min;
	return (int) ((x - offset) * ((float) ((1 << bits) - 1)) / span);
}

static float uint_to_float(uint16_t x, float x_min, float x_max) {
	uint16_t type_max = 0xFFFF;
	float span = x_max - x_min;
	return (float) x / type_max * span + x_min;
}

static float make_float_writedata(float x, float x_min, float x_max) {
	if (x > x_max)
		x = x_max;
	else if (x < x_min)
		x = x_min;
	return x;
}

void CyberGear_SendCANData(CyberGear_Typedef *cyber, uint8_t com_type,
		uint16_t data_area2, uint8_t target_id, uint8_t *data_area1) {

	cyber->tx_candata.com_type = com_type;
	cyber->tx_candata.data_area2 = data_area2;
	cyber->tx_candata.target_id = target_id;
	memcpy(cyber->tx_candata.data_area1, data_area1, 8);

	cyber->tx_candata.ext_id = 0;
	cyber->tx_candata.ext_id |= (uint32_t) com_type << 24;
	cyber->tx_candata.ext_id |= (uint32_t) data_area2 << 8;
	cyber->tx_candata.ext_id |= (uint32_t) target_id << 0;

	Easy_CAN6_BlockingTransmit_Ext(cyber->ecan, cyber->tx_candata.ext_id,
			cyber->tx_candata.data_area1, sizeof(cyber->tx_candata.data_area1));

}
void CyberGear_UnpackCANData(CyberGear_Typedef *cyber,
		CAN_RxHeaderTypeDef rxheader, uint8_t *rxbuf) {
	if (rxheader.IDE == CAN_ID_EXT) {
		cyber->rx_candata.ext_id = rxheader.ExtId;
		cyber->rx_candata.com_type = (rxheader.ExtId >> 24) & 0b11111;
		cyber->rx_candata.data_area2 = (rxheader.ExtId >> 8) & 0xffff;
		cyber->rx_candata.target_id = (rxheader.ExtId >> 0) & 0xff;
		memcpy(cyber->rx_candata.data_area1, rxbuf, 8);
	}
}
uint8_t CyberGear_GetComType(CyberGear_Typedef *cyber) {
	return cyber->rx_candata.com_type;
}
uint16_t CyberGaer_GetDataArea2(CyberGear_Typedef *cyber) {
	return cyber->rx_candata.data_area2;
}
uint8_t CyberGear_GetTargetID(CyberGear_Typedef *cyber) {
	return cyber->rx_candata.target_id;
}

void CyberGear_Init(CyberGear_Typedef *cyber, Easy_CAN6_Typedef *ecan,
		uint8_t motor_id, uint8_t master_id, void (*delay)(uint32_t)) {
	cyber->ecan = ecan;
	cyber->cyberconfig.id = motor_id;
	cyber->cyberconfig.master_id = master_id;
	cyber->delay = delay;
}

void CyberGear_SetConfig(CyberGear_Typedef *cyber, float torque_limit,
		float speed_limit, float current_limit) {
	CyberGear_TorqueLimit(cyber, torque_limit);
	CyberGear_SpeedLimit(cyber, speed_limit);
	CyberGear_CurrentLimit(cyber, current_limit);
}

void CyberGear_SetMode(CyberGear_Typedef *cyber, uint8_t mode) {
	uint8_t index_data[4] = { 0 };
	index_data[0] = mode;
	CyberGear_WriteIndexParam(cyber, 0x7005, index_data);
}

void CyberGear_SpeedLimit(CyberGear_Typedef *cyber, float limit) {
	cyber->cyberconfig.limit_speed = limit;
	union float_binary limit_speed;
	limit_speed.data = make_float_writedata(limit, 0, V_MAX);
	CyberGear_WriteIndexParam(cyber, 0x7017, limit_speed.bin);
}
void CyberGear_TorqueLimit(CyberGear_Typedef *cyber, float limit) {
	cyber->cyberconfig.limit_torque = limit;
	union float_binary limit_torque;
	limit_torque.data = make_float_writedata(limit, 0, T_MAX);
	CyberGear_WriteIndexParam(cyber, 0x700B, limit_torque.bin);
}
void CyberGear_CurrentLimit(CyberGear_Typedef *cyber, float limit) {
	cyber->cyberconfig.limit_current = limit;
	union float_binary limit_current;
	limit_current.data = make_float_writedata(limit, 0, 23.0);
	CyberGear_WriteIndexParam(cyber, 0x7018, limit_current.bin);
}
void CyberGear_CurrentControlPram(CyberGear_Typedef *cyber, float kp, float ki,
		float gain);
void CyberGear_ControlSpeed(CyberGear_Typedef *cyber, float target_speed) {
	cyber->cybermotion.velocity = target_speed;
	union float_binary b_speed;
	b_speed.data = make_float_writedata(target_speed, V_MIN, V_MAX);
	CyberGear_WriteIndexParam(cyber, 0x700A, b_speed.bin);
}
void CyberGear_ControlPosition(CyberGear_Typedef *cyber, float target_position) {
	cyber->cybermotion.position = target_position;
	union float_binary b_position;
	b_position.data = make_float_writedata(target_position, P_MIN, P_MAX);
	CyberGear_WriteIndexParam(cyber, 0x7016, b_position.bin);
}

void CyberGear_GetDeviceID(CyberGear_Typedef *cyber) {
	uint8_t txdata[8] = { 0 };

	CyberGear_SendCANData(cyber, 0, cyber->cyberconfig.master_id,
			cyber->cyberconfig.id, txdata);
}
void CyberGear_DriveMotor(CyberGear_Typedef *cyber, float target_torque,
		float target_position, float target_speed, float kp, float kd) {

	uint32_t uint_torque = float_to_uint(target_torque, T_MIN, T_MAX, 16);

	uint8_t txdata[8] = { 0 };
	uint16_t uint_position = float_to_uint(target_position, P_MIN, P_MAX, 16);
	uint16_t uint_speed = float_to_uint(target_speed, V_MIN, V_MAX, 16);
	uint16_t uint_kp = float_to_uint(kp, KP_MIN, KP_MAX, 16);
	uint16_t uint_kd = float_to_uint(kd, KD_MIN, KD_MAX, 16);

	txdata[1] = (uint_position) & 0xff;
	txdata[0] = (uint_position >> 8) & 0xff;

	txdata[3] = (uint_speed) & 0xff;
	txdata[2] = (uint_speed >> 8) & 0xff;

	txdata[5] = (uint_kp) & 0xff;
	txdata[4] = (uint_kp >> 8) & 0xff;

	txdata[7] = (uint_kd) & 0xff;
	txdata[6] = (uint_kd >> 8) & 0xff;

	CyberGear_SendCANData(cyber, 1, uint_torque, cyber->cyberconfig.id, txdata);
}

void CyberGear_EnableMotor(CyberGear_Typedef *cyber) {
	uint8_t txdata[8] = { 0 };

	CyberGear_SendCANData(cyber, 3, cyber->cyberconfig.master_id,
			cyber->cyberconfig.id, txdata);
	cyber->delay(10);
}

void CyberGear_ResetMotor(CyberGear_Typedef *cyber) {
	uint8_t txdata[8] = { 0 };

	CyberGear_SendCANData(cyber, 4, cyber->cyberconfig.master_id,
			cyber->cyberconfig.id, txdata);
	cyber->delay(10);
}

void CyberGear_ResetZEROPos(CyberGear_Typedef *cyber) {
	uint8_t txdata[8] = { 0 };
	txdata[0] = 1;
	CyberGear_SendCANData(cyber, 6, cyber->cyberconfig.master_id,
			cyber->cyberconfig.id, txdata);
}

void CyberGear_ChangeCANID(CyberGear_Typedef *cyber, uint8_t id) {
	uint8_t txdata[8] = { 0 };
	CyberGear_SendCANData(cyber, 7,
			((uint16_t) id << 8) | cyber->cyberconfig.master_id,
			cyber->cyberconfig.id, txdata);
}

void CyberGear_ReadIndexParam(CyberGear_Typedef *cyber, uint16_t index) {
	uint8_t txdata[8] = { 0 };
	union uint16_binary index_bin;
	index_bin.data = index;
	txdata[0] = index_bin.bin[0];
	txdata[1] = index_bin.bin[1];
	CyberGear_SendCANData(cyber, 17, cyber->cyberconfig.master_id,
			cyber->cyberconfig.id, txdata);
	cyber->delay(1);
}
void CyberGear_WriteIndexParam(CyberGear_Typedef *cyber, uint16_t index,
		uint8_t *write_data) {
	uint8_t txdata[8] = { 0 };
	union uint16_binary index_bin;
	index_bin.data = index;
	txdata[0] = index_bin.bin[0];
	txdata[1] = index_bin.bin[1];
	txdata[4] = write_data[0];
	txdata[5] = write_data[1];
	txdata[6] = write_data[2];
	txdata[7] = write_data[3];
	CyberGear_SendCANData(cyber, 18, cyber->cyberconfig.master_id,
			cyber->cyberconfig.id, txdata);
	cyber->delay(1);
}
void CyberGear_ReadAllIndexPram(CyberGear_Typedef *cyber) {
	CyberGear_ReadIndexParam(cyber, 0x7005);
	CyberGear_ReadIndexParam(cyber, 0x7006);
	CyberGear_ReadIndexParam(cyber, 0x700A);
	CyberGear_ReadIndexParam(cyber, 0x700B);
	CyberGear_ReadIndexParam(cyber, 0x7010);
	CyberGear_ReadIndexParam(cyber, 0x7011);
	CyberGear_ReadIndexParam(cyber, 0x7014);
	CyberGear_ReadIndexParam(cyber, 0x7016);
	CyberGear_ReadIndexParam(cyber, 0x7017);
	CyberGear_ReadIndexParam(cyber, 0x7018);
	CyberGear_ReadIndexParam(cyber, 0x7019);
	CyberGear_ReadIndexParam(cyber, 0x701A);
	CyberGear_ReadIndexParam(cyber, 0x701B);
	CyberGear_ReadIndexParam(cyber, 0x701C);
	CyberGear_ReadIndexParam(cyber, 0x701D);
}

void CyberGear_CANRxTask(CyberGear_Typedef *cyber, CAN_HandleTypeDef *hcan,
		CAN_RxHeaderTypeDef rxheader, uint8_t *rxbuf) {
	if (hcan == cyber->ecan->hcan) {
		CyberGear_UnpackCANData(cyber, rxheader, rxbuf);

		switch (cyber->rx_candata.com_type) {
		case 2: //get now motor data
			if (cyber->rx_candata.target_id == cyber->cyberconfig.master_id) {
				union uint16_binary uint_now_pos, uint_now_speed,
						uint_now_torque, uint_now_temp;

				uint_now_pos.bin[1] = rxbuf[0];
				uint_now_pos.bin[0] = rxbuf[1];

				uint_now_speed.bin[1] = rxbuf[2];
				uint_now_speed.bin[0] = rxbuf[3];

				uint_now_torque.bin[1] = rxbuf[4];
				uint_now_torque.bin[0] = rxbuf[5];

				uint_now_temp.bin[1] = rxbuf[6];
				uint_now_temp.bin[0] = rxbuf[7];

				cyber->cyberfeedback.feedback_info =
						cyber->rx_candata.data_area2;
				cyber->cyberfeedback.feedback_pos = uint_to_float(
						uint_now_pos.data, P_MIN, P_MAX);
				cyber->cyberfeedback.feedback_speed = uint_to_float(
						uint_now_speed.data, V_MIN, V_MAX);
				cyber->cyberfeedback.feedback_torque = uint_to_float(
						uint_now_torque.data, T_MIN, T_MAX);
				cyber->cyberfeedback.feetback_temp =
						(float) (uint_now_temp.data) / 10.0;

			}
			break;
		case 17: //read index param
			if (cyber->rx_candata.target_id == cyber->cyberconfig.master_id) {
				union uint16_binary index;
				memcpy(index.bin, cyber->rx_candata.data_area1, 2);
				if (index.data == 0x7005) {
					uint8_t run_mode = cyber->rx_candata.data_area1[4];
					cyber->cyberindex.run_mode = run_mode;
				} else if (index.data == 0x7006) {
					union float_binary iq_ref;
					memcpy(iq_ref.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.iq_ref = iq_ref.data;
				} else if (index.data == 0x700A) {
					union float_binary spd_ref;
					memcpy(spd_ref.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.spd_ref = spd_ref.data;
				} else if (index.data == 0x700B) {
					union float_binary limit_torque;
					memcpy(limit_torque.bin, cyber->rx_candata.data_area1 + 4,
							4);
					cyber->cyberindex.limit_torque = limit_torque.data;
				} else if (index.data == 0x7010) {
					union float_binary cur_kp;
					memcpy(cur_kp.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.cur_kp = cur_kp.data;
				} else if (index.data == 0x7011) {
					union float_binary cur_ki;
					memcpy(cur_ki.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.cur_ki = cur_ki.data;
				} else if (index.data == 0x7014) {
					union float_binary cur_filt_gain;
					memcpy(cur_filt_gain.bin, cyber->rx_candata.data_area1 + 4,
							4);
					cyber->cyberindex.cur_filt_gain = cur_filt_gain.data;
				} else if (index.data == 0x7016) {
					union float_binary loc_ref;
					memcpy(loc_ref.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.loc_ref = loc_ref.data;
				} else if (index.data == 0x7017) {
					union float_binary limit_spd;
					memcpy(limit_spd.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.limit_spd = limit_spd.data;
				} else if (index.data == 0x7018) {
					union float_binary limit_cur;
					memcpy(limit_cur.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.limit_cur = limit_cur.data;
				} else if (index.data == 0x7019) {
					union float_binary mechPos;
					memcpy(mechPos.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.mechPos = mechPos.data;
				} else if (index.data == 0x701A) {
					union float_binary mechPos;
					memcpy(mechPos.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.mechPos = mechPos.data;
				} else if (index.data == 0x701B) {
					union float_binary iqf;
					memcpy(iqf.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.iqf = iqf.data;
				} else if (index.data == 0x701C) {
					union float_binary VBUS;
					memcpy(VBUS.bin, cyber->rx_candata.data_area1 + 4, 4);
					cyber->cyberindex.VBUS = VBUS.data;
				} else if (index.data == 0x701D) {
					union int16_binary rotation;
					memcpy(rotation.bin, cyber->rx_candata.data_area1 + 4, 2);
					cyber->cyberindex.rotation = rotation.data;
				}
			}
			break;
		case 21: //fault frame

			break;
		default:
			break;
		}
	}

}
#endif
