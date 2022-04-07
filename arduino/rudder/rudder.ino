
/*
   CAN port receiver example
   Receives data on the CAN buss and prints to the serial port
*/

#include <ASTCanLib.h>
#include <Servo.h>
#include <Wire.h>
#include <SPI.h>

#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

Servo rudder;

#define MESSAGE_ID 3       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0      // rtr bit

#define MESSAGE_TYPE 1
#define HEADING_KP .15
#define KD .21
#define MAX_RUDDER_ANGLE 20
#define HEADING_SENSOR 2
#define BNO055_SAMPLERATE_DELAY_MS 10
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
#define dirPin 8
#define stepPin 7
#define IDLE 69

int sensorRequest = 0;
float xpos = 0;
float ypos = 0;
float zpos = 0;
int counter = 100;
int type = IDLE;
int input = 0;
float heading_kp = HEADING_KP;
float heading_kd = KD;
int previousState = IDLE;
int lastControlType = IDLE;
float error_prev = 0;

enum d {LEFT = 1, RIGHT};



int direction;
// Function prototypes
void serialPrintData(st_cmd_t *msg);

// CAN message object
st_cmd_t Msg;

void CANsend(int ID, int sensor);
void CANIn();
void saveType();//saves previous state
void stateManager();//makes sure state is set correctly after each loop

// Buffer for CAN data
uint8_t Buffer[8] = {};
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
  JETSON,
  THRUST,
  RUDDER,
  DEPTH_PITCH = 5,
  DATA,
  MISSION
};

void setup()
{
  // Assign PIN 6 to servo, with range between 850ms and 2350ms
  rudder.attach(6, 850, 2350);
  //rudder.write(90);

  canInit(500000);          // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000);    // start serial port
  Msg.pt_data = &Buffer[0]; // reference message data to buffer

  // Initialise CAN packet.
  // All of these will be overwritten by a received packet
  Msg.ctrl.ide = MESSAGE_PROTOCOL; // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
  Msg.id.ext = MESSAGE_ID;         // Set message ID
  Msg.dlc = MESSAGE_LENGTH;        // Data length: 8 bytes
  Msg.ctrl.rtr = MESSAGE_RTR;      // Set rtr bit
  attachInterrupt(digitalPinToInterrupt(can_get_status(&Msg)), CANIn, CHANGE); // start interrupt
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

void loop()
{
  Serial.println("");
  //CANIn();
  //convert input
  //CANsend(DATA, HEADING_SENSOR); // data to data logger
  Serial.print("type:");
  Serial.println(type);
  Serial.print("Servo:");
  Serial.println(rudder.read());
  switch (type)
  {
    case 0:
      Serial.print("Input: ");
      Serial.println(input);
      if (abs(input - 150) <= MAX_RUDDER_ANGLE)
        rudder.write(input);
      else
        Serial.println("Input angle too high!");
      break;
    case 1:
      if (direction)//if auv is turning around, need to specify which direction to turn.
        turn(direction);
      setHeading(input);
      break;
    case 3:
      CANsend(JETSON, sensorRequest);
      break;
    case 5://set heading_kp in  CANin
      break;
    case IDLE:
      break;
    default:
      break;
  }
  //stateManager();
  delay(500);
}

// void saveType() {//save current state in order to revert once code has finished executing
//   previousState = type;
//   if (type < 3)
//     lastControlType = type;

// }

// void stateManager() {//makes sure bot is in correct state at end of each loop:
//   if (type > 2 && type != IDLE)
//     type = lastControlType;
// }

void getHeading()
{
  // sensors_event_t event;
  // bno.getEvent(&event);
  // ypos = event.orientation.z;
  // xpos = event.orientation.x;
  // Serial.println("Outside ypos : ");
  // Serial.println(ypos);
  // Serial.println("Orientation: ");
  // Serial.println(xpos);
  // return xpos;
  CANsend(THRUST, YAW);
  CANIn();
}

void turn(int dir)//this solution is kind of janky but basically turn function gets the turn started in the direction we want, so that get heading will definitely go the direction intended
{
  if (dir == LEFT)
    rudder.write(MAX_RUDDER_ANGLE);
  else//dir == RIGHT
    rudder.write(-MAX_RUDDER_ANGLE);
  delay(4000);
  direction = 0;
}

void setHeading(float h)
{
  //float error = h - getHeading();
  //float error_derivative = (error - error_prev) / .5;// change(error - error_prev)/time(s)
  //float newAngle = (error) * heading_kp + error_derivative * heading_kd; // new angle will now be from 0 - some float angle that should be maxed to 40
  //if (newAngle > MAX_RUDDER_ANGLE * 2)
    //newAngle = MAX_RUDDER_ANGLE * 2;
  //newAngle -= MAX_RUDDER_ANGLE;
  //error_prev == h - getHeading();
  //rudder.write(newAngle + 150);
}

void CANIn()
{
  clearBuffer(&Buffer[0]); 
  Msg.cmd = CMD_RX_DATA;   // Send command to the CAN port controller
  
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  
  int id = 0;
  id = Msg.pt_data[0];
  if (id != MESSAGE_ID) return;
  //saveType();
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a direct rudder write or a heading command

  switch (type) {
    case 0:
      input = Msg.pt_data[MESSAGE_TYPE + 1] == 1 ? Msg.pt_data[MESSAGE_TYPE + 2] : -Msg.pt_data[MESSAGE_TYPE + 2]; // return rudder angle
      input += 150;// for some reason servo is off by 150 degrees
      break;
    case 1:
      direction = Msg.pt_data[4];
      input = (Msg.pt_data[MESSAGE_TYPE + 1] * 10) + Msg.pt_data[MESSAGE_TYPE + 2]; // return heading in degrees
      break;
    case 3:
      sensorRequest = Msg.pt_data[MESSAGE_TYPE + 1];
      break;
    case 5:
      if (!Msg.pt_data[MESSAGE_TYPE + 1]) //heading kp
        heading_kp = Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] / 100);
      else //heading kd
        heading_kd = Msg.pt_data[MESSAGE_TYPE + 2] + (Msg.pt_data[MESSAGE_TYPE + 3] / 100);
      break;
    case IDLE:
      break;
    default:
      Serial.println("Not a valid type!");
      break;
  }
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
  /*
    Serial.println(testVal);
    Serial.println(yposArray[0]);
    Serial.println(yposArray[1]);
    Serial.println(yposArray[2]);
  */
}

void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;
  switch (sensor) {
    //case HEADING_SENSOR:
      // convert(getHeading());
      // for (int i = 0; i < 7; i++)
      //   Buffer[i + 2] = i < 4 ? yposArray[i] : Buffer[i + 2];
      // break;
    case ACK:
      for(int i=2;i<8;i++) Buffer[i] = 0;
      break;
    case YAW:
      break;
    default:
      break;
  }
  // Send command to the CAN port controller
  Msg.cmd = CMD_TX_DATA; // send message
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  clearBuffer(&Buffer[0]);
}

void serialPrintData(st_cmd_t *msg)
{
  char textBuffer[50] = {0};
  if (msg->ctrl.ide > 0)
  {
    sprintf(textBuffer, "id %d ", msg->id.ext);
  }
  else
  {
    sprintf(textBuffer, "id %04x ", msg->id.std);
  }
  Serial.print(textBuffer);

  //  IDE
  sprintf(textBuffer, "ide %d ", msg->ctrl.ide);
  Serial.print(textBuffer);
  //  RTR
  sprintf(textBuffer, "rtr %d ", msg->ctrl.rtr);
  Serial.print(textBuffer);
  //  DLC
  sprintf(textBuffer, "dlc %d ", msg->dlc);
  Serial.print(textBuffer);
  //  Data
  sprintf(textBuffer, "data ");
  Serial.print(textBuffer);

  for (int i = 0; i < msg->dlc; i++)
  {
    sprintf(textBuffer, "%02X ", msg->pt_data[i]);
    Serial.print(textBuffer);
  }
  Serial.print("\r\n");
}
