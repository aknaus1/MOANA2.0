// Code for slider with the bang bang control that guides the linear slider to the position based on an angle input into the serial command.
//
//
// MAKE FLOW OF CONTROL LOOP DIAGRAM!!!
//
//
//
#include <ASTCanLib.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

#define MESSAGE_ID 5       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0      // rtr bit
#define MESSAGE_TYPE 1

#define STEP_CONST .0021
#define IDLE 69
#define MAINTAIN_DEPTH 2

#define BNO055_SAMPLERATE_DELAY_MS 10
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

const int dirPin = 8;
const int stepPin = 7;
const int buttonPin1 = 6; // pin at -16/STEP_CONST
const int buttonPin2 = 5; // pin at 16/STEP_CONST
int type = IDLE;

// CAN message object
st_cmd_t Msg;

// Transmit buffer
uint8_t Buffer[8] = {};
void calibrate();
void CANsend(int ID, int sensor);
void nudgeStepper();
float getPitch();
float getHeading();
int sensorRequest = 0;

float pitch_kp = 1.33;
float depth_kp = 5;
float pitch_cmd = 0;
float depth_cmd = 0;
float cur_depth = 0;
float pitch_reading_offset = 0;

float stepsToX = 0; // centimeters
float distance = 0; // meters
float currentLocation = 0;
float sliderChange = 0; //[inches]
int yposArray[3];

enum sensorSend
{
  DEPTH,
  PITCH,
  YAW,
  STEP_POS,
  TEMP,
  SLIDER,
  BOTH,
  THRUSTER_COMMAND
};

enum IDs
{
  JETSON,
  THRUST = 2,
  RUDDER,
  DEPTH_PITCH = 5,
  DATA,
  MISSION,
  DEPTH_TEMP,
  FAILSAFE
};

void setup()
{
  canInit(500000);       // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000); // start serial port
  Serial.println("Starting up");
  Msg.pt_data = &Buffer[0]; // reference message data to transmit buffer

  Msg.ctrl.ide = MESSAGE_PROTOCOL; // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
  Msg.id.ext = MESSAGE_ID;         // Set message ID
  Msg.dlc = MESSAGE_LENGTH;        // Data length: 8 bytes
  Msg.ctrl.rtr = MESSAGE_RTR;      // Set rtr bit

  // Initializes the PWM Pin
  pinMode(stepPin, OUTPUT);
  // Initializes the direction Pin
  pinMode(dirPin, OUTPUT);
  // initialize the pushbutton pin as an input:
  pinMode(buttonPin1, INPUT);
  pinMode(buttonPin2, INPUT);
 
  if (!bno.begin())
  {
    Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
    while (1);
  }
  bno.setExtCrystalUse(true);

  Serial.println("Set pins");
  Serial.println("Initialized sensors");
  calibrate(); // runs calibration
}

void loop() // main loop, refreshes every
{
  CANin();
  //  Serial.print("State:");
  //  Serial.println(type);//type is changed in CANin, it's the second byte of the message and dictates what the board does once it receives a message
  // switch statements may make more sense here but in testing we found that the boards were not powerful enough to handle it
  Serial.print("Pitch offset: ");
  Serial.println(pitch_reading_offset);
  Serial.print("pitch kp: ");
  Serial.println(pitch_kp);
  Serial.print("depth kp: ");
  Serial.println(depth_kp);

  if (type == 1)
  {
    changeSliderPosition(sliderChange);
  }
  else if (type == 2)
  {
    setSliderPosition(distance);
  }
  else if (type == 3)
  {
    CANsend(JETSON, sensorRequest);
  }
  else if (type == 4)
  {
    calibrate(); // runs calibration
  } 
  else if (type == 6) // depth command
  {
    double newPitch = (depth_cmd - cur_depth) * depth_kp + MAINTAIN_DEPTH;
    double changePos = (newPitch - getPitch()) * pitch_kp;
    changeSliderPosition(changePos);
  }
  else if (type == 7) // pitch command
  {
    double changePos = (pitch_cmd - getPitch()) * pitch_kp;
    changeSliderPosition(changePos);
  }
}

float getPitch() // reads pitch from sensor
{
  sensors_event_t event;
  bno.getEvent(&event);
  float zpos = event.orientation.z;
  Serial.print("Pitch: ");
  Serial.println(zpos + pitch_reading_offset);
  return zpos + pitch_reading_offset;
}

float getHeading()
{
  sensors_event_t event;
  bno.getEvent(&event);
  float xpos = event.orientation.x;
  Serial.print("Orientation: ");
  Serial.println(xpos);
  return xpos;
}

void nudgeStepper() // moves stepper a little bit in the direction it's been set
{
  for (int i = 0; i < 500; i++)
  {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(400);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(400);
  }
}

void setSliderPosition(float dist) // sets slider position based on an input -16 - 16
{
  stepsToX = dist / STEP_CONST - currentLocation;
  double change = stepsToX * STEP_CONST;
  changeSliderPosition(change);
}

void changeSliderPosition(double change)
{ // changes slider position based on an input in centimeters- will stop at end if input would be too far
  if ((currentLocation >= 7620 && change > 0) || (currentLocation <= -7620 && change < 0)) return;
  // set direction of stepper motor
  Serial.print("Change: ");
  Serial.println(change);
  stepsToX = change / STEP_CONST;                                        // calculate how much slider will move in a unit that is nice for the stepper
  stepsToX > 0 ? digitalWrite(dirPin, HIGH) : digitalWrite(dirPin, LOW); // set stepper direction

  //  Serial.print("Steps To X: ");
  //  Serial.println(stepsToX);
  if (stepsToX + currentLocation > 7620) // if input would move too far forward
  {
    stepsToX = 7620 - currentLocation; // set new input to be the end on the side it was told to go
  }
  else if (stepsToX + currentLocation < -7620) // if input would move too far backward
  {
    stepsToX = -7620 - currentLocation; // set new input to be the end
  }

  for (int i = 0; i < abs(stepsToX); i++) // loop that takes weight to desired positon
  {
    currentLocation += stepsToX > 0 ? 1 : -1;

    digitalWrite(stepPin, HIGH); // move a step
    delayMicroseconds(400);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(400);

    if (digitalRead(buttonPin2) == HIGH || digitalRead(buttonPin1) == HIGH) // if it hits an edge, recalibrate
    {
      if (digitalRead(buttonPin2) == HIGH)
      {
        currentLocation = 16 / STEP_CONST;
        digitalWrite(dirPin, LOW);
      }
      else if (digitalRead(buttonPin1) == HIGH)
      {
        currentLocation = -16 / STEP_CONST;
        digitalWrite(dirPin, HIGH);
      }
      nudgeStepper();
      break;
    }
  }
  type = IDLE;
}

void calibrate()
{
  digitalWrite(dirPin, HIGH);
  if (digitalRead(buttonPin1 == HIGH)) // if it starts all the way at the back
  {
    nudgeStepper(); // move it off the back
  }
  Serial.println("Running Calibration. Please wait.");
  while (true)
  {
    if ((digitalRead(buttonPin1) == HIGH) || (digitalRead(buttonPin2) == HIGH)) // if at end, it is now calibrated
    {
      digitalWrite(stepPin, LOW);
      Serial.println("Calibration Complete");
      currentLocation = 16 / STEP_CONST;
      distance = 0;
      break;
    }
    else // keep moving towards front until reaches a push button
    {
      digitalWrite(stepPin, HIGH);
      delayMicroseconds(400);
      digitalWrite(stepPin, LOW);
      delayMicroseconds(400);
    }
  }
  digitalWrite(dirPin, LOW); // return to middle
  nudgeStepper();
  setSliderPosition(0);
}

void CANin()
// currently the boards will remain idle until they receive a new message
// we wasted A LOT of time trying to interrupt these boards every time a new message was sent
// Different boards would easily allow for this functionality
// this would be better because then the jetson would not need separate threads for all of its control loops
//Sidenote: It does look like case switches would make sense here but honestly the boards aren't fast enough to handle it and it was causing errors so I would recommend keeping the if else statements
{
  // Clear the message buffer
  clearBuffer(&Buffer[0]);
  // Send command to the CAN port controller
  Msg.cmd = CMD_RX_DATA; // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  // Data is now available in the message object

  int id = Msg.pt_data[0];
  if (id != MESSAGE_ID)
  {
    type = IDLE;
    return;
  }
  type = Msg.pt_data[MESSAGE_TYPE]; // determines type of message
  if (type == 0)                    // receive depth from depth board, type 0 in main loop will call depth control
  {
    cur_depth = Msg.pt_data[MESSAGE_TYPE + 1] + Msg.pt_data[MESSAGE_TYPE + 2] / 100;
  }
  else if (type == 1) // stepper change
  {
    sliderChange = Msg.pt_data[MESSAGE_TYPE + 1] == 1                                        // if direction is positive
                 ? (Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] * .01))   // distance = positive of input
                 : -(Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] * .01)); // else distance = negative of input
  }
  else if (type == 2) // stepper position
  {
    distance = Msg.pt_data[MESSAGE_TYPE + 1] == 1                                       // if direction is positive
             ? (Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] * .01))  // distance = positive of input
             : -(Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] * .01));// else distance = negative of input
  }
  else if (type == 3) // sensor request
  {
    sensorRequest = Msg.pt_data[MESSAGE_TYPE + 1];
  }
  else if (type == 5) // kp command
  {
    pitch_kp = Msg.pt_data[MESSAGE_TYPE + 1] + Msg.pt_data[MESSAGE_TYPE + 2] * .01;
    depth_kp = Msg.pt_data[MESSAGE_TYPE + 3] + Msg.pt_data[MESSAGE_TYPE + 4] * .01;
  }
  else if (type == 6) // depth command
  {
    depth_cmd = Msg.pt_data[MESSAGE_TYPE + 1];

    // send depth sensor request- this is basically simplified CANsend code
    clearBuffer(&Buffer[0]);
    Msg.id.ext = MESSAGE_ID; // Set message ID
    Buffer[0] = DEPTH_TEMP;
    Buffer[1] = 3;
    Buffer[2] = DEPTH;
    Msg.cmd = CMD_TX_DATA;
    while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
    while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);

    // repeatedly wait for depth sensor response- this is basically simplified CANin code
    do{
      clearBuffer(&Buffer[0]);
      Msg.cmd = CMD_RX_DATA;
      while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
      while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
    } while ((Msg.pt_data[0] != DEPTH_PITCH) && (Msg.pt_data[MESSAGE_TYPE] != 0));

    cur_depth = Msg.pt_data[MESSAGE_TYPE + 1] + Msg.pt_data[MESSAGE_TYPE + 2] * .01;
  }
  else if (type == 7) // pitch command
  {
    pitch_cmd = Msg.pt_data[MESSAGE_TYPE + 1] == 1                                            // if direction is positive
              ? (Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] *.01)) // distance = positive of input
              : -(Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] * .01));
  }
  else if (type == 8)//sensor offset
  {
    pitch_reading_offset = Msg.pt_data[MESSAGE_TYPE + 2] + Msg.pt_data[MESSAGE_TYPE + 3] * .01;
    if(Msg.pt_data[MESSAGE_TYPE + 1] == 1)
      pitch_reading_offset = - pitch_reading_offset;
  }
  clearBuffer(&Buffer[0]);
}

void convert(float testValue) // converts a float or double into an array that can be sent over the CAN bus
{
  yposArray[0] = testValue >= 0 ? 2 : 1;
  yposArray[1] = round(floor(abs(testValue)));
  yposArray[2] = (abs(testValue) - yposArray[1]) * 100;
}

void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;

  if (sensor == SLIDER)
  {
    convert(currentLocation);
    // fills out the message array with a 3 byte representation of currentLocation, followed by a 3 byte representation of stepsToX since they are both floats
    for (int i = MESSAGE_TYPE + 1; i < 8; i++)
    {
      if (i == 5)
        convert(stepsToX);                // on 5th bit of array switch to stepsToX
      Buffer[i] = yposArray[(i + 1) % 3]; // (i+1)%3 = 0 1 2, 0 1 2 when running
    }
  }
  else if(sensor == PITCH)
  {
    float pitch = getPitch();
    Buffer[MESSAGE_TYPE + 1] = pitch < 0 ? 1 : 2;
    pitch = abs(pitch);
    Buffer[MESSAGE_TYPE + 2] = round(floor(pitch));
    Buffer[MESSAGE_TYPE + 3] = round((pitch - floor(pitch)) * 100);
    for (int i = MESSAGE_TYPE + 4; i < 8; i++) Buffer[i];
  }
  else if(sensor == BOTH)
  {
    convert(getPitch());
    for(int i=0;i<3;i++)
      Buffer[MESSAGE_TYPE + i+1] = yposArray[i];
    
    float head = getHeading();
    Buffer[MESSAGE_TYPE + 4] = round(floor(head / 10));
    Buffer[MESSAGE_TYPE + 5] = round(floor(head)) % 10;
    Buffer[MESSAGE_TYPE + 6] = round((head - floor(head)) * 100);
  }

  Msg.cmd = CMD_TX_DATA; // send message
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  // clearBuffer(&Buffer[0]);
}
