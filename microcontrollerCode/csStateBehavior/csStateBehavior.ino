// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
//
// csStateBehavior v0.99 -- 32 bit version (teensy)
//
// Interrupt timed state machine for running behavior tasks and delivering stimuli etc. with a Teensy 3.5/6 board.
// Intended to be used with a python program (csBehavior.py) that enables:
// a) on-demand insturment control
// b) data saving
// c) state-flow logic
//
// By default, csStateBehavior runs at 1 KHz.
// I can run up to 10 KHz, but I don't reccomend it.
// On a Teensy 3.6, each interrupt takes ~50-100 us depending on how many variables are processed.
//
// Questions: Chris Deister --> cdeister@brown.edu
// Last Update 10/30/2018
//
//
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

// ****************************************
// ***** Initialize All The Things ********
// ****************************************
//
// Include config vars
#include "header.h"

#include <math.h>

// Builtin Libraries
#include <Wire.h>
#include <FlexiTimer2.h>

// Other people's libraries
#include <Adafruit_NeoPixel.h>
#include "HX711.h"
#include <Adafruit_MCP4725.h>


//-----------------------------
// ~~~~~~~ IO Pin Defs ~~~~~~~~
//-----------------------------
//
// a) Analog Input Pins
#define lickPinA  23      // Lick/Touch Sensor A 
#define lickPinB  22      // Lick/Touch Sensor B 
#define genA0 A0
#define genA1 A1
#define genA2 A2
#define genA3 A3
#define analogMotion A16

// b) Digital Input Pins
#define scaleData  29
#define scaleClock  28

// c) Digital Interrupt Input Pins
#define motionPin 36
#define framePin  5
#define yGalvo  6

// d) Digital Output Pins
#define rewardPin 24  // Trigger/signal a reward
#define syncPin 25    // Trigger other things like a microscope and/or camera
#define sessionOver  26
#define rewardMirror 30
#define syncMirror 27
#define ledSwitch 31

#define neoStripPin 2
#define pmtBlank  34


// session header
bool startSession = 0;

uint32_t vStim_xPos = 800;
uint32_t vStim_yPos = 800;

elapsedMillis trialTime;
elapsedMillis stateTime;
elapsedMicros headerTime;
elapsedMicros loopTime;

// e) UARTs (Hardware Serial Lines)
#define visualSerial Serial1 // out to a computer running psychopy
#define dashSerial Serial3 // out to a csDashboard

// f) True 12-bit DACs (I define as an array object to loop later)
// on a teensy 3.2 A14 is the only DAC
// MCP DACs (3&4) can be powered by 5V, and will give 5V out.
// Teensy DACs are 3.3V, but see documentation for simple opamp wiring to get 5V peak.
#define DAC1 A21
#define DAC2 A22

// ~~~ MCP DACs
//Adafruit_MCP4725 dac3;
//Adafruit_MCP4725 dac4;


// **** Make neopixel object
// if rgbw use top line, if rgb use second.
Adafruit_NeoPixel strip = Adafruit_NeoPixel(8, neoStripPin, NEO_GRBW + NEO_KHZ800);
//Adafruit_NeoPixel strip = Adafruit_NeoPixel(30, neoStripPin, NEO_GRB + NEO_KHZ800);
uint32_t maxBrightness = 255;

//--------------------------------
// ~~~~~~~ Variable Block ~~~~~~~~
//--------------------------------

// make a loadcell object and set variables
#define calibration_factor 440000
#define zero_factor 8421804

HX711 scale(scaleData, scaleClock);
uint32_t weightOffset = 0;
float scaleVal = 0;


uint32_t lickSensorAValue = 0;
uint32_t genAnalogInput0 = 0;
uint32_t genAnalogInput1 = 0;
uint32_t genAnalogInput2 = 0;
uint32_t genAnalogInput3 = 0;
uint32_t analogAngle = 0;

uint32_t microTimer;
uint32_t microTimer2;

// a) Set DAC and ADC resolution in bits.
uint32_t adcResolution = 12;
uint32_t dacResolution = 12;

// b) Position Encoder
volatile uint32_t encoderAngle = 0;
volatile uint32_t prev_time = 0;

// c) Frame Counter
volatile uint32_t pulseCount = 0;

// d) Flyback Signal
volatile uint32_t flybackVal = 0;

volatile uint32_t lineTime = 0;
volatile uint32_t curLine = 0;
volatile uint32_t lastLine = 0;

// e) State Machine (vStates) Interupt Timing
int sampsPerSecond = 1000;
float evalEverySample = 1.0; // number of times to poll the vStates funtion

// e) bidirectional dynamic variables
// ** These are variables you may want to have other devices/programs change
// ** To set each send over serial the header char, the value as an int and the close char '>'
// ** To get each variable ask over serial header char and the close char '<'
// ***** You can add to this, but add a single char header, the default value and increment the knownCount.
// EXAMPLE: To set the state to 2, send "a2>" over serial (no quotes). To get the current state send "a<"
// The following is the legend for each array entry:
// ____ State Machine Related
// a/0: teensyState (the teensy is considered to be the primary in the state heirarchy)
// ____ Reinforcement Related
// r/1: reward duration (if solenoid) or volume (if pump)
// g/2: time out duration (could be used to time a negative tone etc)
// ____ Visual Stim Related
// c/3: contrast of a visual stimulus (python tells teensy and teensy relays to psychopy etc.)
// o/4: orientation of a visual stimulus
// s/5: spatial frequency of a visual stimulus
// f/6: temporal frequency of a visual stimulus
// ____ NEOPIXEL Related (These do not return actual values)
// b/7: brightness of a neopixel strip
// n/8: color of neopixels (1: all white; 2: all red; 3) all green;
// --------> 4) all blue; 5) all purple (the best color) 6) random; 7) pulse rainbows for a bit
// ____ DAC Stim Train Related
// d/9: interpulse duration (us) of train X end the call with the DAC# so d1001 will set the IPI of DAC1 to 100.
// p/10: pulse duration (us) of train X end the call with the DAC# so p101 will set the pulse dur of DAC1 to 10.
// v/11: pulse amplitude of train X end the call with the DAC# so v40001 will set the pulse dur of DAC1 to 4000.
// t/12: stim type of train X end the call with the DAC# 0 is pulse train, 1 is ramp, 2 is asymmetric cosine stim; so t11> will set DAC1 to ramp.
// m/13: max pulses for a stimulus for channel X. m381> will set the number of pulses on DAC1 to 38.
// ____ Misc.
// l/14: current value on loadCell
// z/15: toggle a pin
// q/16: Flyback stim dur (in microseconds)
// e/17: led switch
// x/18: visStim xPos (times 10)
// y/19: visStim yPos
// z/20: visStim size (times 10)


char knownHeaders[] =    {'a', 'r', 'g', 'c', 'o', 's', 'f', 'b', 'n', 'd', 'p', 'v', 't', 'm', 'l', 'z', 'q', 'e', 'x', 'y', 'z'};
int32_t knownValues[] = { 0,  5, 8000, 0,  0,  4,  2, 1, 0, 90, 10, 0, 0, 0, 0, 0, 100, 1, 2, 0, 10};
int knownCount = 21;

// f) stim trains
// **** here is a map of what each array entry actually does:
// 0: baseline (0) or pulse (1) states
// 1: stop bit; if you set a max pulse num, it will count down and flip this. If not 0, pulsing will stop.
// 2/3: baseline/pulse duration in interrupts (ms by default)
// 4/5: baseline/stim amplitude (as a 12-bit version of 3.3V e.g. 0V is 0 and 3.3V is 4095)
// 6: Stim type (0 for pulse train; 1 for linear ramp) todo: Ramp has a bug I think.
// 7: Write Value (determined by the pulseGen function and is what we write to the DAC each interrupt).
// 8: number of pulses to complete
// 9: up or down bit: used for complex kernels like asymmetric cosine
// todo: swap 7 and 8
uint32_t pulseTrainVars[][10] =
{ {1, 0, knownValues[9], knownValues[10], 0, knownValues[11], knownValues[12], 0, knownValues[13], 0},
  {1, 0, knownValues[9], knownValues[10], 0, knownValues[11], knownValues[12], 0, knownValues[13], 0},
  {1, 0, knownValues[9], knownValues[10], 0, knownValues[11], knownValues[12], 0, knownValues[13], 0},
  {1, 0, knownValues[9], knownValues[10], 0, knownValues[11], knownValues[12], 0, knownValues[13], 0},
  {1, 0, knownValues[9], knownValues[10], 0, knownValues[11], knownValues[12], 0, knownValues[13], 0}
};

// stim trains are timed with elapsedMicros timers, which we store in an array to loop with channels.
elapsedMillis trainTimer[4];


uint32_t analogOutVals[] = {pulseTrainVars[0][7], pulseTrainVars[1][7], pulseTrainVars[2][7], pulseTrainVars[3][7], pulseTrainVars[4][7]};

// g) Reward Params
uint32_t rewardDelivTypeA = 0; // 0 is solenoid; 1 is syringe pump; 2 is stimulus

// h) Various State Related Things
uint32_t lastState = knownValues[0];  // We keep track of current state "knownValues[0]" and the last state.
uint32_t loopCount = 0; // Count state machine interrupts
uint32_t trigTime = 10; // Duration (in interrupt time) of a sync out trigger.
uint32_t lastBrightness = 10;
bool trigStuff = 0;      // Keeps track of whether we triggered things.

bool blockStateChange = 0;   // Sometimes you want teensy to be able to finish something before python can push it.
bool rewarding = 0;
bool scopeState = 1;
// ***** All states have a header we keep track of whether it fired with an array.
// !!!!!! So, if you add a state, add a header entry and increment stateCount.
int headerStates[] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
int stateCount = 9;

// i) csDashboard
//char knownDashHeaders[] = {'b', 'n','v'};
uint32_t knownDashValues[] = {10, 0, 10};
//int knownDashCount = 3;


void setup() {
  // Start MCP DACs
//  dac3.begin(dac3Address); //adafruit A0 pulled high
//  dac4.begin(dac4Address); // sparkfun A0 pulled low

  // todo: Setup Cyclops
  // Start the device

  // neopixels
  strip.begin();
  strip.show();
  strip.setBrightness(100);
  setStrip(2);

  // loadcell
  scale.set_scale(calibration_factor);
  scale.set_offset(zero_factor);
  scale.tare();


  // Analog In/Out
  analogReadResolution(12);
  analogWriteResolution(12);

  // Interrupts
  attachInterrupt(motionPin, rising, RISING);
  attachInterrupt(framePin, frameCount, RISING);
  attachInterrupt(yGalvo, flybackStim_On, FALLING);

  // DIO Pin States
  pinMode(syncPin, OUTPUT);
  digitalWrite(syncPin, LOW);
  pinMode(sessionOver, OUTPUT);
  digitalWrite(sessionOver, LOW);

  pinMode(rewardPin, OUTPUT);
  digitalWrite(rewardPin, LOW);
  pinMode(pmtBlank, OUTPUT);
  digitalWrite(pmtBlank, LOW);
  pinMode(ledSwitch, OUTPUT);
  digitalWrite(ledSwitch, LOW);

  pinMode(syncMirror, INPUT);
  pinMode(rewardMirror, INPUT);

  // Serial Lines
  dashSerial.begin(115200);
  visualSerial.begin(115200);
  Serial.begin(19200);
  delay(20);

  // Start Program Timer
  FlexiTimer2::set(1, evalEverySample / sampsPerSecond, vStates);
  FlexiTimer2::start();
}

void loop() {
  // This is interupt based so nothing here.
}


void vStates() {
  // ***************************************************************************************
  // **** Loop Timing/Serial Processing:
  // Every loop resets the timer, then looks for serial variable changes.
  loopTime = 0;
  lastState = knownValues[0];

  // we then look for any changes to variables, or calls for updates
  int curSerVar = flagReceive(knownHeaders, knownValues);
  if ((curSerVar == 9) || (curSerVar == 10) || (curSerVar == 11) || (curSerVar == 12) || (curSerVar == 13)) {
    setPulseTrainVars(curSerVar, knownValues[curSerVar]);
  }

  // Some hardware actions need to complete before a state-change.
  // So, we have a latch for state change. We write over any change with lastState
  if (blockStateChange == 1) {
    knownValues[0] = lastState;
  }

  // ***************************************************************************************

  // **************************
  // State 0: Boot/Init State
  // **************************
  if (knownValues[0] == 0) {

    // a) run a header for state 0
    if (headerStates[0] == 0) {
      visStim(0);
      genericHeader(0);
      loopCount = 0;
      setStrip(3); // red
      pulseCount = 0;
      // reset session header
      if (startSession == 1) {
        digitalWrite(sessionOver, HIGH);
        digitalWrite(13, HIGH);
        delay(100);
        digitalWrite(sessionOver, LOW);
        digitalWrite(13, LOW);
      }
      startSession = 0;
    }

    pollColorChange();
    pollToggle();
    pollRelays(); // Let other users use the trigger lines
    // b) body for state 0
    genericStateBody();


  }

  // **************************
  // State != 0: (in task)
  // **************************
  if (knownValues[0] != 0) {

    if (loopCount == 0) {
      trigStuff = 0;
      digitalWrite(syncPin, HIGH);
    }

    // This ends the trigger.
    if (loopCount >= trigTime && trigStuff == 0) {
      digitalWrite(syncPin, LOW);
      trigStuff = 1;
    }

    //******************************************
    //@@@@@@ Start Non-Boot State Definitions.
    //******************************************


    // **************************
    // State 1: Boot/Init State
    // **************************
    if (knownValues[0] == 1) {
      // run this stuff once per session
      if (startSession == 0) {
        startSession = 1;
        trialTime = 0;
      }

      if (headerStates[1] == 0) {
        visStim(0);
        genericHeader(1);
        blockStateChange = 0;
      }
      genericStateBody();
    }

    // **************************
    // State 2: Stim State
    // **************************
    else if (knownValues[0] == 2) {
      if (headerStates[2] == 0) {
        genericHeader(2);
        visStim(2);
        blockStateChange = 0;
      }
      analogOutVals[0] = 0;
      analogOutVals[1] = 0;
      analogOutVals[2] = 0;
      analogOutVals[3] = 0;
      genericStateBody();
    }

    // **************************************
    // State 3: Catch-Trial (no-stim) State
    // **************************************
    else if (knownValues[0] == 3) {
      if (headerStates[3] == 0) {
        blockStateChange = 0;
        genericHeader(3);
        visStim(0);
      }

      stimGen(pulseTrainVars);
      setAnalogOutValues(analogOutVals, pulseTrainVars);
      genericStateBody();
    }

    // **************************************
    // State 4: Reward State
    // **************************************
    else if (knownValues[0] == 4) {
      if (headerStates[4] == 0) {
        blockStateChange = 0;
        genericHeader(4);
        visStim(0);
        rewarding = 0;
      }
      genericStateBody();

      if (rewardDelivTypeA == 0 && rewarding == 0) {
        digitalWrite(rewardPin, HIGH);
        rewarding = 1;
      }
      if (stateTime >= 5) {
        digitalWrite(rewardPin, LOW);
      }
    }

    // **************************************
    // State 5: Time-Out State
    // **************************************
    else if (knownValues[0] == 5) {
      if (headerStates[5] == 0) {
        blockStateChange = 0;
        genericHeader(5);
        visStim(0);
      }
      genericStateBody();
    }

    // **************************************
    // State 6: Manual Reward State
    // **************************************
    else if (knownValues[0] == 6) {
      if (headerStates[6] == 0) {
        genericHeader(6);
        rewarding = 0;
        blockStateChange = 0;
      }
      genericStateBody();

      if (rewardDelivTypeA == 0 && rewarding == 0) {
        digitalWrite(rewardPin, HIGH);
        rewarding = 1;
      }
      if (stateTime >= uint32_t(knownValues[1])) {
        digitalWrite(rewardPin, LOW);
        blockStateChange = 0;
      }
    }

    // ****************************************
    // State 7: Single Pulse Train Trial State
    // ****************************************
    else if (knownValues[0] == 7) {
      if (headerStates[7] == 0) {
        genericHeader(7);
        visStim(0);
        blockStateChange = 0;
      }
      stimGen(pulseTrainVars);
      setAnalogOutValues(analogOutVals, pulseTrainVars);
      genericStateBody();
    }

    // ****************************************
    // State 8: Flyback Pulse State
    // ****************************************
    else if (knownValues[0] == 8) {
      if (headerStates[8] == 0) {
        genericHeader(8);
        visStim(0);
        blockStateChange = 0;
      }
      stimGen(pulseTrainVars);
      analogOutVals[0] = 0;
      analogOutVals[1] = 0;
      analogOutVals[2] = 0;
      analogOutVals[3] = 0;
      genericStateBody();
    }

    // ******* Stuff we do for all non-boot states at the end.
    dataReport();
    loopCount++;
  }
}


void setPulseTrainVars(int recVar, int recVal) {

  int parsedChan = recVal % 10;  // ones digit is the channel
  int parsedValue = recVal * 0.1; // divide by 10 and round up


  // IPI
  if (recVar == 9) {
    pulseTrainVars[parsedChan - 1][2] = parsedValue;
  }
  else if (recVar == 10) {
    pulseTrainVars[parsedChan - 1][3] = parsedValue;
  }
  else if (recVar == 11) {
    // if you push pulses; make sure stop bit is off
    pulseTrainVars[parsedChan - 1][5] = parsedValue;
    pulseTrainVars[parsedChan - 1][1] = 0;
  }
  else if (recVar == 12) {
    pulseTrainVars[parsedChan - 1][6] = parsedValue;
  }
  else if (recVar == 13) {
    pulseTrainVars[parsedChan - 1][8] = parsedValue;
  }
}

void dataReport() {
  Serial.print("tData");
  Serial.print(',');
  Serial.print(loopCount);
  Serial.print(',');
  Serial.print(trialTime);
  Serial.print(',');
  Serial.print(stateTime);
  Serial.print(',');
  Serial.print(knownValues[0]); //state
  Serial.print(',');
  Serial.print(knownValues[14]);  //load cell
  Serial.print(',');
  Serial.print(lickSensorAValue); // lick sensor
  Serial.print(',');
  Serial.print(analogAngle);     //rotary encoder value
  Serial.print(',');
  Serial.print(pulseCount);
  Serial.print(',');
  Serial.print(loopTime);
  Serial.print(',');
  Serial.print(genAnalogInput0);
  Serial.print(',');
  Serial.print(genAnalogInput1);
  Serial.print(',');
  Serial.print(genAnalogInput2);
  Serial.print(',');
  Serial.println(genAnalogInput3);
}

int flagReceive(char varAr[], int32_t valAr[]) {
  static byte ndx = 0;
  char endMarker = '>';
  char feedbackMarker = '<';
  char rc;
  uint32_t nVal;
  const byte numChars = 32;
  char writeChar[numChars];
  int selectedVar = 0;
  static boolean recvInProgress = false;
  bool newData = 0;
  int32_t negScale = 1;

  while (Serial.available() > 0 && newData == 0) {
    rc = Serial.read();

    if (recvInProgress == false) {
      for ( int i = 0; i < knownCount; i++) {
        if (rc == varAr[i]) {
          selectedVar = i;
          recvInProgress = true;
        }
      }
    }

    else if (recvInProgress == true) {
      if (rc == endMarker ) {
        writeChar[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = 1;
        nVal = int32_t(String(writeChar).toInt());
        valAr[selectedVar] = nVal * negScale;
        return selectedVar;
      }

      else if (rc == feedbackMarker) {
        writeChar[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = 1;
        Serial.print("echo");
        Serial.print(',');
        Serial.print(varAr[selectedVar]);
        Serial.print(',');
        Serial.print(valAr[selectedVar]);
        Serial.print(',');
        Serial.println('~');
      }
      else if (rc == '-') {
        negScale = -1;
      }
      else if (rc != feedbackMarker || rc != endMarker) {
        writeChar[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
    }
  }
}

int flagReceiveDashboard(uint32_t valAr[]) {
  static boolean recvInProgress2 = false;
  static byte ndx2 = 0;
  char endMarker = '>';
  char feedbackMarker = '<';
  char rc;
  uint32_t nVal;
  const byte numChars = 32;
  char writeChar[numChars];
  static int selectedVar = 0;
  int newData = 0;

  while (dashSerial.available() > 0 && newData == 0) {
    rc = dashSerial.read();

    if (recvInProgress2 == false) {
      if (rc == 'b') {
        selectedVar = 0;
        recvInProgress2 = true;
      }
      else if (rc == 'n') {
        selectedVar = 1;
        recvInProgress2 = true;
      }

    }

    else if (recvInProgress2 == true) {
      if (rc == endMarker ) {
        //        Serial.println(selectedVar);
        writeChar[ndx2] = '\0'; // terminate the string
        recvInProgress2 = false;
        ndx2 = 0;
        newData = 1;

        nVal = uint32_t(String(writeChar).toInt());
        valAr[selectedVar] = nVal;

      }
      else if (rc == feedbackMarker) {
        writeChar[ndx2] = '\0'; // terminate the string
        recvInProgress2 = false;
        ndx2 = 0;
        newData = 1;
        dashSerial.print("echo");
        dashSerial.print(',');
        dashSerial.print(valAr[selectedVar]);
        dashSerial.print(',');
        dashSerial.println('~');
      }

      else if (rc != feedbackMarker || rc != endMarker) {
        writeChar[ndx2] = rc;
        ndx2++;
        if (ndx2 >= numChars) {
          ndx2 = numChars - 1;
        }
      }
    }
  }
  return newData; // tells us if a valid variable arrived.
}

void resetHeaders() {
  for ( int i = 0; i < stateCount; i++) {
    headerStates[i] = 0;
  }
}

void genericHeader(int stateNum) {
  // a: reset header timer
  headerTime = 0;

  // b: reset header states and set current state's header to 1 (fired).
  resetHeaders();
  headerStates[stateNum] = 1;

  for ( int i = 0; i < 4; i++) {
    trainTimer[i] = 0;
  }

  headerStates[stateNum] = 1;
  // c: set analog output values to 0.
  analogOutVals[0] = 0;
  analogOutVals[1] = 0;
  analogOutVals[2] = 0;
  analogOutVals[3] = 0;
  analogOutVals[4] = 0;
  
  pulseTrainVars[0][0] = 1;
  pulseTrainVars[1][0] = 1;
  pulseTrainVars[2][0] = 1;
  pulseTrainVars[3][0] = 1;
  pulseTrainVars[4][0] = 1;

  pulseTrainVars[0][1] = 0;
  pulseTrainVars[1][1] = 0;
  pulseTrainVars[2][1] = 0;
  pulseTrainVars[3][1] = 0;
  pulseTrainVars[4][1] = 0;

  pulseTrainVars[0][9] = 0;
  pulseTrainVars[1][9] = 0;
  pulseTrainVars[2][9] = 0;
  pulseTrainVars[3][9] = 0;
  pulseTrainVars[4][9] = 0;

  // d: reset state timer.
  stateTime = 0;
}

void genericStateBody() {

  lickSensorAValue = analogRead(lickPinA);
  lickSensorAValue = analogRead(lickPinB);
  genAnalogInput0 = analogRead(genA0);
  genAnalogInput1 = analogRead(genA1);
  genAnalogInput2 = analogRead(genA2);
  genAnalogInput3 = analogRead(genA3);
  analogAngle = analogRead(analogMotion);
  writeAnalogOutValues(analogOutVals);
  if (scale.is_ready()) {
    scaleVal = scale.get_units() * 22000;
    // this scale factor gives hundreths of a gram as the least significant int
    knownValues[14] = scaleVal;
  }
}

// ****************************************************************
// **************  Visual Stimuli *********************************
// ****************************************************************

void visStim(int stimType) {
  if (stimType == 0) {
    visualSerial.print('v');
    visualSerial.print(',');
    visualSerial.print(0);
    visualSerial.print(',');
    visualSerial.print(0);
    visualSerial.print(',');
    visualSerial.print(0);
    visualSerial.print(',');
    visualSerial.print(0);
    visualSerial.print(',');
    visualSerial.print(knownValues[18]);
    visualSerial.print(',');
    visualSerial.print(knownValues[19]);
    visualSerial.print(',');
    visualSerial.println(knownValues[20]);
  }
  //1 is on
  if (stimType == 2) {
    visualSerial.print('v');
    visualSerial.print(',');
    visualSerial.print(knownValues[4]);
    visualSerial.print(',');
    visualSerial.print(knownValues[3]);
    visualSerial.print(',');
    visualSerial.print(knownValues[5]);
    visualSerial.print(',');
    visualSerial.print(knownValues[6]);
    visualSerial.print(',');
    visualSerial.print(knownValues[18]);
    visualSerial.print(',');
    visualSerial.print(knownValues[19]);
    visualSerial.print(',');
    visualSerial.println(knownValues[20]);
  }
}

// **************************************************************
// **************  Motion Interrupts  ***************************
// **************************************************************

void rising() {
  attachInterrupt(motionPin, falling, FALLING);
  prev_time = micros();
}

void falling() {
  attachInterrupt(motionPin, rising, RISING);
  encoderAngle = micros() - prev_time;
}

void frameCount() {
  pulseCount++;
}

void flybackStim_On() {

  pulseCount = pulseCount + 1;
  if (knownValues[0] == 8) {

    elapsedMicros pfTime;
    pfTime = 0;
    while (pfTime <= knownValues[16]) {
      stimGen(pulseTrainVars);
      analogWrite(DAC1, pulseTrainVars[0][7]);
      analogWrite(DAC2, pulseTrainVars[1][7]);
    }
    analogWrite(DAC1, 0);
    analogWrite(DAC2, 0);
  }
}



// ****************************************************************
// **************  Pulse Train Function ***************************
// ****************************************************************
void setAnalogOutValues(uint32_t dacVals[], uint32_t pulseTracker[][10]) {
  dacVals[0] = pulseTracker[0][7];
  dacVals[1] = pulseTracker[1][7];
  dacVals[2] = pulseTracker[2][7];
  dacVals[3] = pulseTracker[3][7];
  dacVals[4] = pulseTracker[4][7];
}

void writeAnalogOutValues(uint32_t dacVals[]) {
  analogWrite(DAC1, dacVals[0]);
  analogWrite(DAC2, dacVals[1]);
//  dac3.setVoltage(dacVals[2], false);
//  dac4.setVoltage(dacVals[3], false);
//  dac5.setVoltage(dacVals[4], false);
}

void stimGen(uint32_t pulseTracker[][10]) {
  int i;
  for (i = 0; i < 5; i = i + 1) {
    // *** 0 == Square Waves
    if (pulseTracker[i][6] == 0) {
      // PULSE STATE
      if (pulseTracker[i][0] == 1) {
        // if we are over the pulse time:
        // a) reset the timer, b) move to baseline state
        if (trainTimer[i] >= pulseTracker[i][3]) {
          trainTimer[i] = 0; // reset counter
          pulseTracker[i][0] = 0; // stop pulsing
          pulseTracker[i][7] = pulseTracker[i][4];
          if (pulseTracker[i][8]  > 0) {
            pulseTracker[i][8] = pulseTracker[i][8] - 1;
            if (pulseTracker[i][8]<=0){
              pulseTracker[i][1] = 1;
              pulseTracker[i][8] = 0;
            }
          }
        }
        else {
          // if we still have pulse time, and we haven't flipped the stop bit, then pulse.
          if (pulseTracker[i][1]==0) {
            pulseTracker[i][7] = pulseTracker[i][5]; // 5 is the pulse amp; 7 is the current output.
          }
          else if (pulseTracker[i][1]==1) {
            pulseTracker[i][7] = pulseTracker[i][4]; // baseline
          }
        }
      }

      // BASLINE/DELAY STATE
      else if (pulseTracker[i][0] == 0) {
        // if we are out of baseline time; move to stim state
        if (trainTimer[i] >=  pulseTracker[i][2]) {
          trainTimer[i] = 0; // reset counter
          pulseTracker[i][0] = 1; // start pulsing
          pulseTracker[i][7] = pulseTracker[i][5];
        }
        else {
          // but if we have delay time, then we use baseline
          pulseTracker[i][7] = pulseTracker[i][4];
          // 4 is the baseline amp; 6 is the current output.
        }
      }
    }
    // add ramp back here

    // 2) Asymm Cosine
    else if (pulseTracker[i][6] == 2) {

      // PULSE STATE
      if (pulseTracker[i][0] == 1) {
        // These pulses idealy have a variable time.
        if (pulseTracker[i][1] == 0) {

          if (trainTimer[i] <= 10) {
            pulseTracker[i][10] = 0;
          }

          else if (trainTimer[i] > 10) {
            pulseTracker[i][10] = 1;
          }

          if (pulseTracker[i][10] == 0) {
            float curTimeSc = PI + ((PI * (trainTimer[i] - 1)) / 10);
            pulseTracker[i][7] = pulseTracker[i][5] * ((cosf(curTimeSc) + 1) * 0.5); // 5 is the pulse amp; 7 is the current output.
          }
          else if (pulseTracker[i][10] == 1) {
            float curTimeSc = 0 + ((PI * (trainTimer[i] - 1)) / 100);
            pulseTracker[i][7] = pulseTracker[i][5] * ((cosf(curTimeSc) + 1) * 0.5); // 5 is the pulse amp; 7 is the current output.
          }

          if (trainTimer[i] > 110) {
            pulseTracker[i][10] = 0;
            pulseTracker[i][0] = 0;
            trainTimer[i] = 0;
            pulseTracker[i][7] = pulseTracker[i][4];
            if (pulseTracker[i][8]  > 0) {
              pulseTracker[i][8] = pulseTracker[i][8] - 1;
              pulseTracker[i][1] = 1;
            }
          }

        }
        else if (pulseTracker[i][1] == 1) {
          pulseTracker[i][7] = pulseTracker[i][4]; // baseline
        }
      }

      // baseline STATE
      else if (pulseTracker[i][0] == 0) {
        if (trainTimer[i] >=  pulseTracker[i][2]) {
          pulseTracker[i][0] = 1;
          pulseTracker[i][10] = 0;
          trainTimer[i] = 0;
          pulseTracker[i][7] = pulseTracker[i][4];
        }
        else {
          pulseTracker[i][7] = pulseTracker[i][4];
        }
      }

    }
  }
}



// ----------------------------------------------
// ---------- NEOPIXEL FUNCTIONS ----------------
// ----------------------------------------------

void setStrip(uint32_t stripState) {
  for (uint16_t i = 0; i < strip.numPixels(); i++) {
    if (stripState == 1) {
      strip.setPixelColor(i, strip.Color(0, 0, 0));
    }
    else if (stripState == 2) {
      strip.setPixelColor(i, strip.Color(0, 0, 0, 255));
    }
    else if (stripState == 3) {
      strip.setPixelColor(i, strip.Color(255, 0, 0));
    }
    else if (stripState == 4) {
      strip.setPixelColor(i, strip.Color(0, 255, 0));
    }
    else if (stripState == 5) {
      strip.setPixelColor(i, strip.Color(0, 0, 255));
    }
    else if (stripState == 6) {
      strip.setPixelColor(i, strip.Color(255, 0, 255));
    }
    else if (stripState == 7) {
      strip.setPixelColor(i, strip.Color(random(256), random(256), random(256)));
    }
  }
  strip.show();
}

void pollToggle() {
  if (knownValues[15] == rewardPin || knownValues[15] == syncPin || knownValues[15] == ledSwitch) {
    bool cVal = digitalRead(knownValues[15]);
    digitalWrite(knownValues[15], 1 - cVal);
    delay(5);
    digitalWrite(knownValues[15], cVal);
    knownValues[15] = 0;
  }
}

void pollRelays() {
  bool rTrig;
  bool rRwd;
  rTrig = digitalRead(syncMirror);
  rRwd = digitalRead(rewardMirror);
  if (rTrig == 1) {
    digitalWrite(syncPin, HIGH);
    delay(5);
    digitalWrite(syncPin, LOW);
  }
  if (rRwd == 1) {
    digitalWrite(rewardPin, HIGH);
    delay(5);
    digitalWrite(rewardPin, LOW);
  }
}

void pollTones(uint32_t tonePin, uint32_t toneFreq, uint32_t toneDuration) {
  tone(tonePin, toneFreq, toneDuration);
}

void pollColorChange() {

  if (knownValues[7] != lastBrightness) {
    if (knownValues[7] > maxBrightness) {
      knownValues[7] = maxBrightness;
    }
    strip.setBrightness(knownValues[7]);
    strip.show();
    lastBrightness = knownValues[7];
  }

  // b) Handle color changes.
  if (knownValues[8] > 0 && knownValues[8] < 8) {
    setStrip(knownValues[8]);
    knownValues[8] = 0;
  }
  else {
    knownValues[8] = 0;
  }
}
