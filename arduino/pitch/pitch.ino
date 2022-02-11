// Code for slider with the bang bang control that guides the linear slider to the position based on an angle input into the serial command.

#include <ASTCanLib.h>

#include <Adafruit_Sensor.h>

#include <Adafruit_BNO055.h>
#include "MS5837.h"
#include <utility/imumaths.h>
#include <Wire.h>

#define MESSAGE_ID 5       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0      // rtr bit

#define FRESHWATER 997
#define SALTWATER 1029

#define MESSAGE_TYPE 1

#define BNO055_SAMPLERATE_DELAY_MS 10

#define MAINTAIN_DEPTH 3
#define MAX_ANGLE 12
#define DEPTH_KP 5.7296
#define PITCH_KP .0024543
#define STEP_KP .00125

float xpos = 0;
float zpos = 0;
int counter = 100;
int type = 0;

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
MS5837 depthSensor;

void initSensors();

// CAN message object
st_cmd_t Msg;

// Transmit buffer
uint8_t Buffer[8] = {};

#define dirPin 8
#define stepPin 7

char inputBuffer[5];
int number = 0; // constants won't change. They're used here to set pin numbers:

const int buttonPin1 = 6; // the number of the pushbutton pins
const int buttonPin2 = 7;
const int ledPin = 13; // the number of the LED pin
void calibrate();
void pitchControl();

void CANsend(int ID);

// variables will change:
int buttonState1 = 0;
int buttonState2 = 0; // variable for reading the pushbutton status
int velocity = 100;
int x = 1;

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
  TEMP
};

enum IDs
{
  THRUST = 2,
  RUDDER,
  PITCH = 5,
  DATA,
  MISSION
};

void setup()
{

  canInit(500000);       // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000); // start serial port

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
  pinMode(buttonPin, INPUT);

  initSensors();
  calibrate(); // runs calibration
}

void loop()
{
  // Clear the message buffer
  clearBuffer(&Buffer[0]); // Send command to the CAN port controller
  Msg.cmd = CMD_RX_DATA;   // Wait for the command to be accepted by the controller
  if ((can_cmd(&Msg) == CAN_CMD_ACCEPTED) && (can_get_status(&Msg) != CAN_STATUS_NOT_COMPLETED))
    CANin();

  CANsend(DATA, PITCH); // data to data logger
  CANsend(DATA, DEPTH);
  CANsend(DATA, TEMP);
  switch (type) {//type is the MESSAGE_TYPE byte of a CAN message
    case 0:
      setPitch(xInput);
      break;
    case 1:
      setDepth(depth);
      break;
    case 2:
      setSliderPosition(distance);
      break;
    default:
      break;
  }
  delay(500);
}

void initSensors()
{ // depth Sensor code
  while (!depthSensor.init()){
    Serial.println("Init failed!");
    Serial.println("Are SDA/SCL connected correctly?");
    Serial.println("Blue Robotics Bar30: White=SDA, Green=SCL");
    Serial.println("\n\n\n");
    delay(5000);
  }

  depthSensor.setModel(MS5837::MS5837_30BA);
  depthSensor.setFluidDensity(FRESHWATER); // kg/m^3 (freshwater, 1029 for seawater)

  // IMU Code
  Serial.println("Orientation Sensor Test");
  Serial.println(""); /* Initialise the sensor */
  if (!bno.begin())
  {
    /* There was a problem detecting the BNO055 ... check your connections */
    Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
    while (1)
      ;
  }
  delay(1000);
  bno.setExtCrystalUse(true);
}

void setSliderPosition(float dist)
{
  stepsToX = dist / STEP_KP - currentLocation;

  //set direction of stepper motor
  stepsToX <= 0 ? digitalWrite(dirPin, HIGH) : digitalWrite(dirPin, LOW);

  Serial.print("Steps To X: ");
  Serial.println(stepsToX);

  for (int i = 0; i < abs(stepsToX); i++)
  {
    currentLocation = currentLocation + stepsToX / abs(stepsToX);
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(300);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(300);
    delay(1);
  }

  Serial.println(currentLocation);
  sliderDone();
}

void setPitch(float pitch)
{
  float newPos;
  int sign = 1;
  if (pitch < 0)
    sign = -1;
  if (abs(pitch) > MAX_ANGLE)
    pitch = MAX_ANGLE * sign;
  newPos = (pitch - getPitch()) * PITCH_KP;

  setSliderPosition(newPos);
}

void setDepth(int d)
{
  // This function will change depth based on parameter passed into function.
  if (d > 30) {
    Serial.println("Command exceeds depth limit of 30M");
    return;
  }

  float newPitch;
  newPitch = (d - round(getDepth())) * DEPTH_KP + MAINTAIN_DEPTH;
  setPitch(newPitch);
}

float getPitch() // reads pitch from sensor
{
  Serial.println("GETTING SENSOR YDATA:");
  sensors_event_t event;
  bno.getEvent(&event);
  float ypos = event.orientation.z;
  Serial.println("Outside ypos : ");
  Serial.println(ypos);
  return ypos;
}

double getDepth() // reads the depth sensor and returns depth in Meters
{
  return depthSensor.depth();
}

double getTemp()
{
  return depthSensor.temperature();
}

void calibrate()
{
  Serial.println("Running Calibration. Please wait.");
  while (true)
  {
    buttonState1 = digitalRead(buttonPin1); // check if the pushbutton is pressed. If it is, the buttonState is HIGH:
    buttonState2 = digitalRead(buttonPin2);
    if ((buttonState1 == HIGH) || (buttonState2 == HIGH))
    {
      // turn LED on:
      digitalWrite(ledPin, HIGH);
      Serial.println("Calibration Complete");
      currentLocation = 16.5 / STEP_KP;
      xInput = 0;
      break;
    }
    else
    {

      digitalWrite(ledPin, LOW);
      digitalWrite(stepPin, HIGH);
      delayMicroseconds(400);
      digitalWrite(stepPin, LOW);
      delayMicroseconds(400);
    }
  }
}

void feedback()
{
  float pitchError = 0; // declares error for pitch
  int IMU_Pitch = 0;    // Input IMU_Pitch here
  pitchError = IMU_Pitch - xInput;
  if (pitchError < 0)
  {
    // Set Direction Pin
    // Set speed of movement    pitchError * Kp;
  }
  else if (pitchError > 0)
  {
  }
}

void CANin()
{

  // Clear the message buffer
  // clearBuffer( & Buffer[0]); // Send command to the CAN port controller
  // Msg.cmd = CMD_RX_DATA; // Wait for the command to be accepted by the controller
  // while (can_cmd( & Msg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  // while (can_get_status( & Msg) == CAN_STATUS_NOT_COMPLETED);

  // Data is now available in the message object
  int dir = 0, angle = 0, id = 0;
  id = Msg.pt_data[0];
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a change in pitch or change in depth

  if (id != MESSAGE_ID) return;
  switch (type) {
    case 0: // set pitch
      xInput = Msg.pt_data[MESSAGE_TYPE + 1] == 1 ? Msg.pt_data[MESSAGE_TYPE + 2] : -Msg.pt_data[MESSAGE_TYPE + 2];// sends negative of input if direction byte is 0
      break;
    case 1: // set depth
      depth = Msg.pt_data[MESSAGE_TYPE + 1];
      break;
    case 2: // set stepper position
      distance = Msg.pt_data[MESSAGE_TYPE + 1] == 1 // if direction is positive
      ? (Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] / 100)) //distance = positive of input
      : -(Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] / 100));//else distance = negative of input
      break;
    default:
      break;
  }
}

void convert(float testValue) // converts a flaot or double into an array that can be sent over the CAN bus
{
  int whole, fraction;
  if (testVal < 0.0)
  {
    yposArray[0] = 1; // 1 is a negative value
    testVal = testVal * -1;
  }
  else if (testVal > 0.0)
  {
    yposArray[0] = 2; // 2 is positive
  }
  else if (testVal == 0)
  {
    yposArray[0] = 0;
  }
  whole = round(testVal);
  yposArray[1] = whole;
  fraction = testVal * 100;
  fraction = fraction - (whole * 100);
  yposArray[2] = fraction;
  /*
    Serial.println(testVal);
    Serial.println(yposArray[0]);
    Serial.println(yposArray[1]);
    Serial.println(yposArray[2]);
  */
}

void sliderDone()
{
  for (int i = 0; i < 20; i++)
  {
    CANsend(6);
    delay(500);
  }
}

void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;
  switch (sensor)
  {
  case PITCH:
    convert(getPitch());
    for (int i = 0; i < 7; i++)
      Buffer[i + 2] = i < 4 ? yposArray[i] : Buffer[i + 2];
    break;
  case DEPTH:
    convert(getDepth());
    Buffer[2] = yposArray[1];
    Buffer[3] = yposArray[2];
    for (int i = 4; i <= 7; i++)
      Buffer[i] = 0;
    break;
  case TEMP:
    convert(getTemp());
    for (int i = 0; i < 7; i++)
      Buffer[i + 2] = i < 4 ? yposArray[i] : Buffer[i + 2];
    break;
  default:
    break;
  }
  // Send command to the CAN port controller
  Msg.cmd = CMD_TX_DATA; // send message
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED)
    ;
  // Wait for command to finish executing
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED)
    ;
}
