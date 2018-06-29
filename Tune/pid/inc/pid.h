/*
 * pid.h
 *
 *  Created on: Mar 29, 2018
 *      Author: Sheldon
 */
#ifndef PID_H
#define PID_H

#include <cstdint>
#include <libsc/system.h>
using namespace libsc;

class PID {
public:
	float kP;
	float kI;
	float kD;

	//assume errorSumBound always positive
	int32_t errorSumBound;

	PID() :
			kP(0), kI(0), kD(0), errorSumBound(0), preError(0), errorSum(0),last_time(0),target(0) {
	}

	PID(const float& p, const float& i, const float& d) :
			kP(p), kI(i), kD(d), errorSumBound(0), preError(0), errorSum(0),last_time(0),target(0) {
	}
	void settarget(int t){
		target = t;
	}
	int32_t getTarget(){
		return target;
	}
	int32_t output(const int32_t& current) {
		uint32_t time_diff = System::Time() - last_time;
		int32_t error = target - current;
		accuError(error);
		float ki = errorSum * kI * time_diff;
		float kd = (error - preError) * kD / time_diff;
		float kp = error * kP;
		int32_t out = (int32_t)(kp + ki + kd);
		preError = error;
		last_time = System::Time();
		return out;
	}

	void reset() {
		errorSum = 0;
		preError = 0;
		last_time = System::Time();
	}

private:
	int32_t preError;
	int32_t errorSum;
	int32_t last_time;
	int32_t target;
	void accuError(const int32_t& e) {
		//assume errorSumBound always positive
		if ((errorSum + e) > errorSumBound) {
			errorSum = errorSumBound;
		} else if ((errorSum + e) < -errorSumBound) {
			errorSum = -errorSumBound;
		} else {
			errorSum += e;
		}
	}
};

#endif /* PID_H */
