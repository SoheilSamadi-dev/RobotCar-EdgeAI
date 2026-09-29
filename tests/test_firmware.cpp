// Compile and exercise the actual sketch against a tiny Arduino/motor shim.
#include <cassert>
#include <iostream>
#include "../firmware/uno/manual_serial_control/manual_serial_control.ino"
void input(const char* s){while(*s) Serial.input.push_back(*s++);loop();}
int main(){
  setup();
  assert(driveSpeed==195 && curveStrength==75 && currentMotion==STOPPED);
  input("1"); assert(driveSpeed==195);
  input("---------"); assert(driveSpeed==195);
  input("9"); assert(driveSpeed==255);
  input("++++"); assert(driveSpeed==255);
  input("-"); assert(driveSpeed==250);
  for(char c='1';c<='9';++c){handleCommand(c);assert(driveSpeed>=195 && driveSpeed<=255);}
  input("1w"); assert(frontLeft.speed==195 && frontRight.speed==195);
  input("a"); assert(frontLeft.direction==BACKWARD && frontRight.direction==FORWARD);
  input("9@c50\nq"); assert(frontLeft.speed==127 && frontRight.speed==255);
  input("@c75\n"); assert(frontLeft.speed==63 && frontRight.speed==255);
  input("@c100\n"); assert(frontLeft.direction==RELEASE && frontRight.direction==FORWARD);
  input("e"); assert(frontRight.direction==RELEASE && frontLeft.direction==FORWARD);
  input("z"); assert(frontLeft.direction==RELEASE && frontRight.direction==BACKWARD);
  input("c"); assert(frontRight.direction==RELEASE && frontLeft.direction==BACKWARD);
  input("@c0\nq"); assert(frontLeft.speed==255 && frontRight.speed==255);
  input("@c101\n"); assert(currentMotion==STOPPED && curveStrength==0);
  input("@c75w\n"); assert(currentMotion==STOPPED && curveStrength==0);
  input("@c75x"); assert(currentMotion==STOPPED);
  input("w"); fakeMillis+=250; input("@c50\n");
  fakeMillis+=51; loop(); assert(currentMotion==STOPPED); // Setting is not a heartbeat.
  input("w"); fakeMillis+=301; input("+");assert(currentMotion==STOPPED);
  input("w@c");fakeMillis+=101;loop();assert(currentMotion==STOPPED);
  input("75w\n");assert(currentMotion==STOPPED); // discard partial frame tail
  input("@c75\nw");fakeMillis+=301;loop();assert(currentMotion==STOPPED);
  std::cout << "Firmware PWM, curves, framing, stop and watchdog tests passed\n";
}
