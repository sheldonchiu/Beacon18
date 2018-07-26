/*
 * test.cpp
 *
 *  Created on: Jun 25, 2018
 *      Author: Sheldon
 */

/*
 * main.cpp
 *
 * Author:Sheldon
 * Copyright (c) 2017-2018 HKUST SmartCar Team
 * Refer to LICENSE for details
 */

#include <cassert>
#include <cstring>
#include <stdlib.h>
#include <string>
#include <libbase/k60/mcg.h>
#include <libsc/system.h>
#include "libsc/joystick.h"
#include "libsc/battery_meter.h"
#include "libbase/misc_utils_c.h"
#include "image_processing.h"
#include "libutil/misc.h"
#include "config.h"
#include "var.h"

namespace libbase {
namespace k60 {

Mcg::Config Mcg::GetMcgConfig() {
	Mcg::Config config;
	config.external_oscillator_khz = 50000;
	config.core_clock_khz = 150000;
	return config;
}
}
}

using libsc::System;
using namespace libsc;
using namespace libsc::k60;
using namespace libbase::k60;
using namespace libutil;

int main() {
	System::Init();
	Led Led0(init_led(0));
	led0 = &Led0;
	Led Led1(init_led(1));
	led1 = &Led1;
	BatteryMeter bMeter_(init_bMeter());
	bMeter = &bMeter_;
	St7735r lcd_(init_lcd());
	lcd = &lcd_;
	lcd->SetRegion(Lcd::Rect(0, 0, 160, 128));
	lcd->Clear(Lcd::kBlack);
	LcdTypewriter writer_(init_writer());
	writer = &writer_;
	AlternateMotor motor0(init_motor(0));
	L_motor = &motor0;
	AlternateMotor motor1(init_motor(1));
	R_motor = &motor1;
	DirEncoder encoder1_(init_encoder(1));
	encoder1 = &encoder1_;
	DirEncoder encoder2_(init_encoder(0));
	encoder2 = &encoder2_;
	k60::Ov7725 cam_(init_cam());
	cam = &cam_;
	cam->Start();
	Joystick::Config j_config;
	j_config.id = 0;
	j_config.is_active_low = true;
	Joystick joyStick(j_config);
	//////////////////PID init////////////////////
	PID L_pid_(L_kp, L_ki, L_kd, 1000, -1000);
	L_pid = &L_pid_;
	L_pid->errorSumBound = 100000;
	PID R_pid_(R_kp, R_ki, R_kd, 1000, -1000);
	R_pid = &R_pid_;
	R_pid->errorSumBound = 100000;

	PID Dir_pid_(Dir_kp, Dir_ki, Dir_kd, 500, -500);
	Dir_pid = &Dir_pid_;
	Dir_pid->errorSumBound = 10000;
	PID avoid_pid_(avoid_kp, avoid_ki, avoid_kd, 500, -500);
	avoid_pid = &avoid_pid_;
	avoid_pid->errorSumBound = 10000;

	////////////////Variable init/////////////////
	tick = System::Time();
	uint32_t not_find_time = 0;
	int finding_time = 0;
	Beacon *ptr = NULL;
	uint32_t pid_time = System::Time();
	uint32_t process_time = System::Time();
	int L_count = 0;
	int R_count = 0;
	/////////////////For Dubug////////////////////
	uint8_t state = 100;
	JyMcuBt106 bt_(init_bt());
	bt = &bt_;
	JyMcuBt106 comm_(init_comm());
	comm = &comm_;
	display_bMeter();

	reset_pid();

//	////////////////Main loop////////////////////////
	while (1) {
		if (tick != System::Time()/* && run*/) {
			tick = System::Time();
//			if (tick - pid_time >=50) {
//				pid_time = System::Time();
//				buf = cam->LockBuffer();
//				lcd->SetRegion(Lcd::Rect(0, 0, 80, 60));
//				lcd->FillColor(Lcd::kBlack);
//				for (uint16_t y = 0; y < height; y += 4)
//					for (uint16_t x = 0; x < width; x += 4) {
//						uint16_t pos = (width * y) / 8 + x / 8;
//						uint16_t bit_pos = 8 - (x % 8 + 1);
//						if (!GET_BIT(buf[pos], bit_pos)) {
//							lcd->SetRegion(Lcd::Rect(x / 4, y / 4, 1, 1));
//							lcd->FillColor(Lcd::kWhite);
//						}
//					}
//				cam->UnlockBuffer();
//			}

			if (tick - process_time >= 30) {
				process_time = tick;
				lcd->SetRegion(Lcd::Rect(0, 0, 80, 60));
				lcd->FillColor(Lcd::kBlack);
				for (uint16_t y = 0; y < height; y += 4)
					for (uint16_t x = 0; x < width; x += 4) {
						uint16_t pos = (width * y) / 8 + x / 8;
						uint16_t bit_pos = 8 - (x % 8 + 1);
						if (!GET_BIT(buf[pos], bit_pos)) {
							lcd->SetRegion(Lcd::Rect(x / 4, y / 4, 1, 1));
							lcd->FillColor(Lcd::kWhite);
						}
					}
				process();
				tick = System::Time();
//				for(int i = 0 ; i < beacon_count ; i++){
//					auto c = beacons[i].center;
//					lcd->SetRegion(Lcd::Rect(c.first / 4,c.second /4,5,5));
//					lcd->FillColor(Lcd::kBlue);
//				}
				if (ir_target != NULL) {	//target find
					led0->SetEnable(1);
					not_find_time = 0;
					last_beacon = ir_target->center;
					if (!seen) {
						seen = true;
						Dir_pid->reset();
					}
					if (ir_target->area > max_area)
						max_area = (ir_target->area + max_area) / 2;
					target_x = target_slope * max_area + target_intercept;
					if (target_x > 320)
						target_x = 320;
					if (action == rotation
							&& ir_target->center.first > target_x)
						action = stop;
					else
						action = chase;
				} else if (seen) { //target not find but have seen target before
					if (not_find_time == 0) {
						not_find_time = tick;
						action = keep;
					} else if (tick - not_find_time > 400) { //target lost for more than 400 ms
						led0->SetEnable(0);
						seen = false;
						max_area = 0;
						action = rotation;
					}
				} else { //target not find and have not seen target before
//					led0->SetEnable(0);
//					if (finding_time == 0)
//						finding_time = tick;
//					else if (tick - finding_time > 1000) //change to rotate after going foward for 1000ms
//						action = rotation;
//					else
//						action = forward;
					action = rotation;
				}
//				FSM();
			}
		}
	}
	return 0;
}