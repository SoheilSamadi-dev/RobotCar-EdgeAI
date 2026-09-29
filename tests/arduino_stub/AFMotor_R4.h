#pragma once
#include <cstdint>
#include <deque>
#include <sstream>
#define FORWARD 1
#define BACKWARD 2
#define RELEASE 4
#define F(s) s
#define constrain(x,a,b) ((x)<(a)?(a):((x)>(b)?(b):(x)))
using __FlashStringHelper = char;
static unsigned long fakeMillis = 0;
unsigned long millis() { return fakeMillis; }
struct SerialStub {
  std::deque<char> input;
  std::ostringstream output;
  void begin(int) {}
  int available(){ return input.size(); }
  char read(){char c=input.front();input.pop_front();return c;}
  template<class T> void print(T value){output << value;}
  void print(uint8_t value){output << unsigned(value);}
  template<class T> void println(T value){print(value);output << '\n';}
} Serial;
struct AF_DCMotor {
  uint8_t speed=0, direction=RELEASE;
  AF_DCMotor(int) {}
  void setSpeed(uint8_t value){speed=value;}
  void run(uint8_t value){direction=value;}
};
