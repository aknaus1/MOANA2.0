// Code for slider with the bang bang control that guides the linear slider to the position based on an angle input into the serial command.

#include <ASTCanLib.h>
//#include <AltSoftSerial.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>

#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <Wire.h>

#define MESSAGE_ID 5       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0      // rtr bit

#define MESSAGE_TYPE 1

#define STEP_KP .0021
#define IDLE 69

float xpos = 0;
float zpos = 0;
int counter = 100;
int type = IDLE;

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

// CAN message object
st_cmd_t Msg;

// Transmit buffer
uint8_t Buffer[8] = {};

#define dirPin 8
#define stepPin 7

char inputBuffer[5];
int number = 0; // constants won't change. They're used here to set pin numbers:

const int buttonPin1 = 6; // pin at -16/kd[2]
const int buttonPin2 = 5; //pin at 16/kd[2]
const int ledPin = 13; // the number of the LED pin
const int intPin = 3;//pin for interrupt
void calibrate();

void CANsend(int ID, int sensor);
void nudgeStepper();


// variables will change:
int buttonState1 = 0;
int buttonState2 = 0; // variable for reading the pushbutton status
int velocity = 100;
int x = 1;
int sensorRequest = 0;
int water;

float stepsToX = 0; // centimeters
float distance = 0; // meters
int depth = 0;
float xInput = 0; // input angle for pitch
float currentLocation = 0;
int currentDirection = 1; // direction slider is moving 0 = towards stepper, 1 is away from stepper
float addedSliderMass = 19.62;
float sliderMass = 23.58 + 4;                //[Newtons] mass on top of batter + battery mass + slider weight
float totalMass = 728.125 - addedSliderMass; //[Newtons]
float separation = 1;                        //[inches]
float Kp = .1;
int yposArray[3];

enum sensorSend
{
  DEPTH,
  PITCH,
  YAW,
  STEP_POS,
  TEMP,
  SLIDER,
  ACK
};

enum IDs
{
  JETSON = 1,
  THRUST,
  RUDDER,
  DEPTH_PITCH = 5,
  DATA,
  MISSION,
  DEPTH_SENSOR
};

void setup()
{

  canInit(500000);       // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000); // start serial port
  Serial.println("Starting up");
  Msg.pt_data = &Buffer[0]; // reference message data to transmit buffer

  // Initialise CAN packet.
  // All of these will be overwritten by a received packet

  Msg.ctrl.ide = MESSAGE_PROTOCOL; // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
  Msg.id.ext = MESSAGE_ID;         // Set message ID
  Msg.dlc = MESSAGE_LENGTH;        // Data length: 8 bytes
  Msg.ctrl.rtr = MESSAGE_RTR;      // Set rtr bit

  // Initializes the PWM Pin
  pinMode(stepPin, OUTPUT);
  // Initializes the direction Pin
  pinMode(dirPin, OUTPUT);
  // Sets an initial direction
  digitalWrite(dirPin, HIGH);
  // initialize the LED pin as an output:
  pinMode(ledPin, OUTPUT);
  // initialize the pushbutton pin as an input:
  pinMode(buttonPin1, INPUT);
  pinMode(buttonPin2, INPUT);
  pinMode(intPin, INPUT_PULLUP);

  Serial.println("Set pins");
  //initSensors();//prepares sensors to read data
  Serial.println("Initialized sensors");
  //delay(1000);
  //attachInterrupt(digitalPinToInterrupt(intPin), CANin, LOW); // start interrupt
  calibrate(); // runs calibration
  
}

void loop()//main loop, refreshes every
{  
  //Serial.println("head of loop");
  CANin();
  Serial.print("State:");
  Serial.println(type);
  //CANsend(DATA, PITCH); // data to data logger
  //CANsend(DATA, DEPTH);
  //CANsend(DATA, TEMP);
  switch (type) {//type is the MESSAGE_TYPE byte of a CAN message
    case 2:
      setSliderPosition(distance);
      break;
    case 3://sensor request
      CANsend(JETSON, sensorRequest);
      break;
    case IDLE:
      break;
    default:
      break;
  }
  Serial.println("make work");
  delay(500);
}

void nudgeStepper() //moves stepper a little bit in the direction it's been set
{
  for (int i = 0; i < 500 ; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(400);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(400);
  }
}

void setSliderPosition(float dist)
{

  stepsToX = dist / STEP_KP - currentLocation;

  //set direction of stepper motor
  stepsToX >= 0 ? digitalWrite(dirPin, HIGH) : digitalWrite(dirPin, LOW);

  Serial.print("Steps To X: ");
  Serial.println(stepsToX);
  Serial.println("About to start slider movement");
  //delay(2000);
  for (int i = 0; i < abs(stepsToX); i++)
  {

    currentLocation = currentLocation + stepsToX / abs(stepsToX);
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(400);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(400);
    if (digitalRead(buttonPin2) == HIGH || digitalRead(buttonPin1) == HIGH)//if it hits an edge, recalibrate
    {
      if (digitalRead(buttonPin2) == HIGH)
      {
        currentLocation = 16 / STEP_KP;
        digitalWrite(dirPin, LOW);
      }
      else
      {
        currentLocation = -16 / STEP_KP;
        digitalWrite(dirPin, HIGH);
      }
      nudgeStepper();
      break;
    }
    //delay(1);
  }
  sliderDone();
}

void calibrate()
{
  if (digitalRead(buttonPin1 == HIGH))
  {
    digitalWrite(dirPin, HIGH);
    nudgeStepper();
  }
  Serial.println("Running Calibration. Please wait.");
  while (true)
  {
    buttonState1 = digitalRead(buttonPin1); // check if the pushbutton is pressed. If it is, the buttonState is HIGH:
    buttonState2 = digitalRead(buttonPin2);
    if ((buttonState1 == HIGH) || (buttonState2 == HIGH))
    {
      // turn LED on:
      digitalWrite(stepPin, LOW);
      Serial.println("Calibration Complete");

      currentLocation = 16 / STEP_KP;
      distance = 0;
      break;
    }
    else
    {
      digitalWrite(stepPin, HIGH);
      delayMicroseconds(400);
      digitalWrite(stepPin, LOW);
      delayMicroseconds(400);
    }
  }
  digitalWrite(dirPin, LOW);
  nudgeStepper();
  setSliderPosition(distance);

}

void CANin()
{
  //Serial.println("CANIn");
  // Clear the message buffer
  clearBuffer( & Buffer[0]); // Send command to the CAN port controller
  Msg.cmd = CMD_RX_DATA; // Wait for the command to be accepted by the controller
  while (can_cmd( & Msg) != CAN_CMD_ACCEPTED);
  //Wait for command to finish executing
  while (can_get_status( & Msg) == CAN_STATUS_NOT_COMPLETED);

  // Data is now available in the message object
  int dir = 0, angle = 0, id = 0;
  id = Msg.pt_data[0];

  if (id != MESSAGE_ID) return;
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a change in pitch or change in depth

  if(type == 2)
  {
    distance = Msg.pt_data[MESSAGE_TYPE + 1] == 1 // if direction is positive
            ? (Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] / 100)) //distance = positive of input
            : -(Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] / 100));//else distance = negative of input
  }
  else if(type == 3)
  {
    sensorRequest = Msg.pt_data[MESSAGE_TYPE + 1];
  }

  clearBuffer( & Buffer[0]);
}

void convert(float testValue) // converts a float or double into an array that can be sent over the CAN bus
{
  int whole, fraction;
  if (testValue < 0.0)
  {
    yposArray[0] = 1; // 1 is a negative value
    testValue = testValue * -1;
  }
  else if (testValue > 0.0)
  {
    yposArray[0] = 2; // 2 is positive
  }
  else if (testValue == 0)
  {
    yposArray[0] = 0;
  }
  whole = round(testValue);
  yposArray[1] = whole;
  fraction = testValue * 100;
  fraction = fraction - (whole * 100);
  yposArray[2] = fraction;
}

void sliderDone()
{
  Serial.print("Slider done: current Location is ");
  Serial.println(currentLocation);
  delay(500);
  CANsend(DATA, SLIDER);
}

void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;

  if(sensor == SLIDER)
  {
      convert(currentLocation);
      //fills out the message array with a 3 byte representation of currentLocation, followed by a 3 byte representation of stepsToX since they are both floats
      for (int i = MESSAGE_TYPE + 1; i < 8; i++) {
        if (i == 5) convert(stepsToX); //on 5th bit of array switch to stepsToX
        Buffer[i] = yposArray[(i + 1) % 3];// (i+1)%3 = 0 1 2, 0 1 2 when running
      }
  }
  else{
    Serial.println("Please pick a valid sensor!");
  }

  // Send command to the CAN port controller
  Msg.cmd = CMD_TX_DATA; // send message
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  //clearBuffer(&Buffer[0]);
}
