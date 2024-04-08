/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : Main program body
 ******************************************************************************
 * @attention
 *
 * <h2><center>&copy; Copyright (c) 2024 STMicroelectronics.
 * All rights reserved.</center></h2>
 *
 * This software component is licensed by ST under BSD 3-Clause license,
 * the "License"; You may not use this file except in compliance with the
 * License. You may obtain a copy of the License at:
 *                        opensource.org/licenses/BSD-3-Clause
 *
 ******************************************************************************
 */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "CyberGear.h"
#include "Easy_CAN6.h"
#include <math.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
CAN_HandleTypeDef hcan;

TIM_HandleTypeDef htim1;

UART_HandleTypeDef huart2;
DMA_HandleTypeDef hdma_usart2_tx;
DMA_HandleTypeDef hdma_usart2_rx;

/* USER CODE BEGIN PV */
uint8_t debug;

CyberGear_Typedef my_cyber[4];
Easy_CAN6_Typedef ecan;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_CAN_Init(void);
static void MX_TIM1_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
#define byte_number 20
uint8_t UART2_RX_Buffer[byte_number];
uint8_t txBuff[] = "Hello, World\n";
uint8_t txBuff_2[] = "99行目\n";
uint32_t startTime;
uint32_t setTime;
uint32_t sdTime;
uint8_t sdBuff[100];
float motor_speed[4];

char temp_str[byte_number];
int16_t values[byte_number]; // ??��?��?大15個�???��?��?��??��?��?を持つint16の配�???��?��を作�??

#define DATANUM 20
uint8_t serialData[DATANUM] = { };

unsigned char buf[20];

#define TRUE (1)
#define FALSE (0)

uint16_t debug_2 = 10;

#define is_run_CyberGear (1) ///////////////////////////////////CyberGear動作させるかさせないか

uint8_t uart_prev_count;
uint16_t command_id;
float command_content;

float motor_speed[4];

uint8_t value3[8];

uint8_t flagRcved; /* 受信完�?フラグ */
uint8_t rcvBuffer[30]; /* 受信バッファ*/
uint8_t sndBuffer[100]; /* 送信バッファ */

int8_t received_data[30];
float data[5]; // データの配列 (2つのint16_t型の要素)

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan) {
	CAN_RxHeaderTypeDef RxHeader;
	uint8_t rxbuf[8];
	HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &RxHeader, rxbuf);

	CyberGear_CANRxTask(&my_cyber[0], hcan, RxHeader, rxbuf);
	CyberGear_CANRxTask(&my_cyber[1], hcan, RxHeader, rxbuf);
	CyberGear_CANRxTask(&my_cyber[2], hcan, RxHeader, rxbuf);
	CyberGear_CANRxTask(&my_cyber[3], hcan, RxHeader, rxbuf);
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart) {
	huart2.gState = HAL_UART_STATE_READY;
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
	flagRcved = TRUE; /* 受信完�?フラグ設�? */
//  HAL_GPIO_TogglePin(BUILDIN_LED_GPIO_Port, BUILDIN_LED_Pin);
}
/* USER CODE END 0 */

/**
 * @brief  The application entry point.
 * @retval int
 */
int main(void) {

	/* USER CODE BEGIN 1 */
	/* USER CODE END 1 */

	/* MCU Configuration--------------------------------------------------------*/

	/* Reset of all peripherals, Initializes the Flash interface and the Systick. */
	HAL_Init();

	/* USER CODE BEGIN Init */

	/* USER CODE END Init */

	/* Configure the system clock */
	SystemClock_Config();
	/* USER CODE BEGIN SysInit */

	/* USER CODE END SysInit */

	/* Initialize all configured peripherals */
	MX_GPIO_Init();
	MX_DMA_Init();
	MX_USART2_UART_Init();
	MX_CAN_Init();
	MX_TIM1_Init();
	/* USER CODE BEGIN 2 */
	Easy_CAN6_Start(&ecan, &hcan, 2);

	for (int i = 0; i < 4; i++) {
		if (is_run_CyberGear) {
			CyberGear_Init(&my_cyber[i], &ecan, 0x70 + i, 0, HAL_Delay);
			CyberGear_ResetMotor(&my_cyber[i]);
			CyberGear_SetMode(&my_cyber[i], MODE_SPEED);
			CyberGear_SetConfig(&my_cyber[i], 12.0f, 30.0f, 6.0f);
			CyberGear_EnableMotor(&my_cyber[i]);
		}
	}
	HAL_Delay(100);

	HAL_UART_Transmit_DMA(&huart2,
			(uint8_t*) "Then toggle LED each 8 letters.\r\n", 33);
	/* USER CODE END 2 */

	/* Infinite loop */
	/* USER CODE BEGIN WHILE */
	while (1) {
		/* USER CODE END WHILE */

		/* USER CODE BEGIN 3 */
		HAL_GPIO_TogglePin(BUILDIN_LED_GPIO_Port, BUILDIN_LED_Pin);

		debug = HAL_UART_Receive_DMA(&huart2, rcvBuffer, 7);
//		debug = HAL_UART_Receive(&huart2, rcvBuffer, 7, 1000);

		buf[0] = (unsigned char) rcvBuffer[1];
		buf[1] = (unsigned char) rcvBuffer[2];
		buf[2] = (unsigned char) rcvBuffer[3];
		buf[3] = (unsigned char) rcvBuffer[4];
		buf[4] = (unsigned char) rcvBuffer[5];
		buf[5] = (unsigned char) rcvBuffer[6];
		buf[6] = (unsigned char) rcvBuffer[0];

//		debug_2 = rcvBuffer[0];
//		if(rcvBuffer[0] == 0){
//			memcpy(buf, &rcvBuffer[1], sizeof(buf));
//		}else{
//			memcpy(buf, &rcvBuffer[0], sizeof(buf));
//		}

		memcpy(&uart_prev_count, &buf[0], sizeof(uint8_t));

		uint8_t reversed_bytes[4];
		reversed_bytes[0] = buf[2];
		reversed_bytes[1] = buf[1];
		memcpy(&command_id, reversed_bytes, sizeof(uint16_t));

		uint8_t _temp_command_content[4];
		memcpy(_temp_command_content, &buf[3], sizeof(float));
		// バイト列を逆順にコピー
		for (int j = 0; j < 4; j++) {
			reversed_bytes[j] = _temp_command_content[3 - j];
		}
		memcpy(&command_content, reversed_bytes, sizeof(float));

//    char str[6];
//    sprintf(str, "\ndata[0] : %d\n", data[0]);
//    HAL_UART_Transmit(&huart2, (uint8_t *)str, strlen(str), 0xFFFF);
//
//    sprintf(str, "data[1] : %d\n", data[1]);
//    HAL_UART_Transmit(&huart2, (uint8_t *)str, strlen(str), 0xFFFF);

		switch (command_id) {
		case 22:
			motor_speed[0] = command_content;
			if (is_run_CyberGear) {
				CyberGear_ControlSpeed(&my_cyber[0], (float) motor_speed[0]);
			}
			break;

		case 24:
			motor_speed[1] = command_content;
			if (is_run_CyberGear) {
				CyberGear_ControlSpeed(&my_cyber[1], (float) motor_speed[1]);
			}
			break;

		case 26:
			motor_speed[2] = command_content;
			if (is_run_CyberGear) {
				CyberGear_ControlSpeed(&my_cyber[2], (float) motor_speed[2]);
			}
			break;

		case 27:
			debug_2 = 1919;
			for (int i = 0; i < 4; i++) {
				if (is_run_CyberGear) {
					CyberGear_Init(&my_cyber[i], &ecan, 0x70 + i, 0, HAL_Delay);
					CyberGear_ResetMotor(&my_cyber[i]);
					CyberGear_SetMode(&my_cyber[i], MODE_SPEED);
					CyberGear_SetConfig(&my_cyber[i], 12.0f, 30.0f, 6.0f);
					CyberGear_EnableMotor(&my_cyber[i]);
				}
			}
			break;

		case 28:
			motor_speed[3] = command_content;
			if (is_run_CyberGear) {
				CyberGear_ControlSpeed(&my_cyber[3], (float) motor_speed[3]);
			}
			break;
		}

		HAL_Delay(9);
	}
	/* USER CODE END 3 */
}

/**
 * @brief System Clock Configuration
 * @retval None
 */
void SystemClock_Config(void) {
	RCC_OscInitTypeDef RCC_OscInitStruct = { 0 };
	RCC_ClkInitTypeDef RCC_ClkInitStruct = { 0 };
	RCC_PeriphCLKInitTypeDef PeriphClkInit = { 0 };

	/** Initializes the RCC Oscillators according to the specified parameters
	 * in the RCC_OscInitTypeDef structure.
	 */
	RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
	RCC_OscInitStruct.HSIState = RCC_HSI_ON;
	RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
	RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
	RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
	RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL15;
	if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) {
		Error_Handler();
	}

	/** Initializes the CPU, AHB and APB buses clocks
	 */
	RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
			| RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
	RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
	RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
	RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
	RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

	if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK) {
		Error_Handler();
	}
	PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_TIM1;
	PeriphClkInit.Tim1ClockSelection = RCC_TIM1CLK_HCLK;
	if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK) {
		Error_Handler();
	}
}

/**
 * @brief CAN Initialization Function
 * @param None
 * @retval None
 */
static void MX_CAN_Init(void) {

	/* USER CODE BEGIN CAN_Init 0 */

	/* USER CODE END CAN_Init 0 */

	/* USER CODE BEGIN CAN_Init 1 */

	/* USER CODE END CAN_Init 1 */
	hcan.Instance = CAN;
	hcan.Init.Prescaler = 2;
	hcan.Init.Mode = CAN_MODE_NORMAL;
	hcan.Init.SyncJumpWidth = CAN_SJW_1TQ;
	hcan.Init.TimeSeg1 = CAN_BS1_12TQ;
	hcan.Init.TimeSeg2 = CAN_BS2_2TQ;
	hcan.Init.TimeTriggeredMode = DISABLE;
	hcan.Init.AutoBusOff = DISABLE;
	hcan.Init.AutoWakeUp = DISABLE;
	hcan.Init.AutoRetransmission = DISABLE;
	hcan.Init.ReceiveFifoLocked = DISABLE;
	hcan.Init.TransmitFifoPriority = DISABLE;
	if (HAL_CAN_Init(&hcan) != HAL_OK) {
		Error_Handler();
	}
	/* USER CODE BEGIN CAN_Init 2 */

	/* USER CODE END CAN_Init 2 */
}

/**
 * @brief TIM1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_TIM1_Init(void) {

	/* USER CODE BEGIN TIM1_Init 0 */

	/* USER CODE END TIM1_Init 0 */

	TIM_MasterConfigTypeDef sMasterConfig = { 0 };
	TIM_OC_InitTypeDef sConfigOC = { 0 };
	TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = { 0 };

	/* USER CODE BEGIN TIM1_Init 1 */

	/* USER CODE END TIM1_Init 1 */
	htim1.Instance = TIM1;
	htim1.Init.Prescaler = 0;
	htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
	htim1.Init.Period = 65535;
	htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
	htim1.Init.RepetitionCounter = 0;
	htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
	if (HAL_TIM_PWM_Init(&htim1) != HAL_OK) {
		Error_Handler();
	}
	sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
	sMasterConfig.MasterOutputTrigger2 = TIM_TRGO2_RESET;
	sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
	if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig)
			!= HAL_OK) {
		Error_Handler();
	}
	sConfigOC.OCMode = TIM_OCMODE_PWM1;
	sConfigOC.Pulse = 0;
	sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
	sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
	sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
	sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
	sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
	if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1)
			!= HAL_OK) {
		Error_Handler();
	}
	sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
	sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
	sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
	sBreakDeadTimeConfig.DeadTime = 0;
	sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
	sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
	sBreakDeadTimeConfig.BreakFilter = 0;
	sBreakDeadTimeConfig.Break2State = TIM_BREAK2_DISABLE;
	sBreakDeadTimeConfig.Break2Polarity = TIM_BREAK2POLARITY_HIGH;
	sBreakDeadTimeConfig.Break2Filter = 0;
	sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
	if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig)
			!= HAL_OK) {
		Error_Handler();
	}
	/* USER CODE BEGIN TIM1_Init 2 */

	/* USER CODE END TIM1_Init 2 */
	HAL_TIM_MspPostInit(&htim1);
}

/**
 * @brief USART2 Initialization Function
 * @param None
 * @retval None
 */
static void MX_USART2_UART_Init(void) {

	/* USER CODE BEGIN USART2_Init 0 */

	/* USER CODE END USART2_Init 0 */

	/* USER CODE BEGIN USART2_Init 1 */

	/* USER CODE END USART2_Init 1 */
	huart2.Instance = USART2;
	huart2.Init.BaudRate = 500000;
	huart2.Init.WordLength = UART_WORDLENGTH_8B;
	huart2.Init.StopBits = UART_STOPBITS_1;
	huart2.Init.Parity = UART_PARITY_NONE;
	huart2.Init.Mode = UART_MODE_TX_RX;
	huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
	huart2.Init.OverSampling = UART_OVERSAMPLING_16;
	huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
	huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
	if (HAL_UART_Init(&huart2) != HAL_OK) {
		Error_Handler();
	}
	/* USER CODE BEGIN USART2_Init 2 */

	/* USER CODE END USART2_Init 2 */
}

/**
 * Enable DMA controller clock
 */
static void MX_DMA_Init(void) {

	/* DMA controller clock enable */
	__HAL_RCC_DMA1_CLK_ENABLE();

	/* DMA interrupt init */
	/* DMA1_Channel6_IRQn interrupt configuration */
	HAL_NVIC_SetPriority(DMA1_Channel6_IRQn, 0, 0);
	HAL_NVIC_EnableIRQ(DMA1_Channel6_IRQn);
	/* DMA1_Channel7_IRQn interrupt configuration */
	HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
	HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);
}

/**
 * @brief GPIO Initialization Function
 * @param None
 * @retval None
 */
static void MX_GPIO_Init(void) {
	GPIO_InitTypeDef GPIO_InitStruct = { 0 };
	/* USER CODE BEGIN MX_GPIO_Init_1 */
	/* USER CODE END MX_GPIO_Init_1 */

	/* GPIO Ports Clock Enable */
	__HAL_RCC_GPIOF_CLK_ENABLE();
	__HAL_RCC_GPIOA_CLK_ENABLE();
	__HAL_RCC_GPIOB_CLK_ENABLE();

	/*Configure GPIO pin Output Level */
	HAL_GPIO_WritePin(BUILDIN_LED_GPIO_Port, BUILDIN_LED_Pin, GPIO_PIN_RESET);

	/*Configure GPIO pin : BUILDIN_LED_Pin */
	GPIO_InitStruct.Pin = BUILDIN_LED_Pin;
	GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
	HAL_GPIO_Init(BUILDIN_LED_GPIO_Port, &GPIO_InitStruct);

	/* USER CODE BEGIN MX_GPIO_Init_2 */
	/* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
 * @brief  This function is executed in case of error occurrence.
 * @retval None
 */
void Error_Handler(void) {
	/* USER CODE BEGIN Error_Handler_Debug */
	/* User can add his own implementation to report the HAL error return state */
	__disable_irq();
	while (1) {
	}
	/* USER CODE END Error_Handler_Debug */
}

#ifdef USE_FULL_ASSERT
/**
 * @brief  Reports the name of the source file and the source line number
 *         where the assert_param error has occurred.
 * @param  file: pointer to the source file name
 * @param  line: assert_param error line source number
 * @retval None
 */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
