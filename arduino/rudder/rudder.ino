
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
#define MAX_RUDDER_ANGLE 20

#define RUDDER_OFFSET 130

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
int count = 0;

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
float getHeading();

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
  // IMU Code
  Serial.println("Orientation Sensor Test");
  delay(3000);
  if (!bno.begin())
  {
    /* There was a problem detecting the BNO055 ... check your connections */
    Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
    while (1)
      ;
  }
  bno.setExtCrystalUse(true);
}

void setRudder(float angle)
{
  if (abs(angle - RUDDER_OFFSET) <= MAX_RUDDER_ANGLE)
    rudder.write(angle);
  else if (angle - RUDDER_OFFSET > MAX_RUDDER_ANGLE)
    rudder.write(MAX_RUDDER_ANGLE + RUDDER_OFFSET);
  else
    rudder.write(-MAX_RUDDER_ANGLE + RUDDER_OFFSET);
}

void loop()
{
  CANIn();
  //convert input
  //CANsend(DATA, HEADING_SENSOR); // data to data logger
  Serial.print("type:");
  Serial.println(type);
  Serial.print("Servo:");
  Serial.println(rudder.read());

  if (type == 0) {
    Serial.print("Input: ");
    Serial.println(input);
    setRudder(input);
  }
  else if (type == 1) {
    float cur_heading = getHeading();
    float angle = 0;
    if (input + 180 < cur_heading)
      angle = (input - (cur_heading - 360)) * heading_kp;
    else
      angle = (input - cur_heading) * heading_kp;
    angle += RUDDER_OFFSET;

    Serial.print("Input: ");
    Serial.println(angle);
    setRudder(angle);
  }
  else if (type == 3) {
    CANsend(JETSON, sensorRequest);
  }
    
}

float getHeading()
{
  sensors_event_t event;
  bno.getEvent(&event);
  xpos = event.orientation.x;
  Serial.println("Orientation: ");
  Serial.println(xpos);
  return xpos;
}

float getPitch() // reads pitch from sensor
{
  sensors_event_t event;
  bno.getEvent(&event);
  float ypos = event.orientation.z;
  Serial.println("Outside ypos : ");
  Serial.println(ypos);
  return ypos;

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

void CANIn()
{
  Serial.println("CANin");
  clearBuffer(&Buffer[0]);
  Msg.cmd = CMD_RX_DATA;   // Send command to the CAN port controller

  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);

  int id = 0;
  id = Msg.pt_data[0];
  if (id != MESSAGE_ID)
  {
    type = IDLE;
    return;
  }
  //saveType();
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a direct rudder write or a heading command


  if(type == 0) {
      input = Msg.pt_data[MESSAGE_TYPE + 1] == 1 ? Msg.pt_data[MESSAGE_TYPE + 2] : -Msg.pt_data[MESSAGE_TYPE + 2]; // return rudder angle
      input += RUDDER_OFFSET;// for some reason servo is off by 130 degrees
  }
  else if(type == 1) {
    input = Msg.pt_data[MESSAGE_TYPE + 1] * 10 + Msg.pt_data[MESSAGE_TYPE + 2];
  }
  else if(type == 3) {
    sensorRequest = Msg.pt_data[MESSAGE_TYPE + 1];
  }
  else if(type == 5) {
    heading_kp = Msg.pt_data[MESSAGE_TYPE + 1] + Msg.pt_data[MESSAGE_TYPE + 2] / 100;
  }

}

void convert(float testValue) // converts a float or double into an array that can be sent over the CAN bus
{
  int whole, fraction;
  if (testValue < 0.0) {
    yposArray[0] = 1; // 1 is a negative value
    testValue = testValue * -1;
  }
  else if (testValue > 0.0) {
    yposArray[0] = 2; // 2 is positive
  }
  else if (testValue == 0) {
    yposArray[0] = 0;
  }
  whole = round(testValue);
  yposArray[1] = whole;
  fraction = testValue * 100;
  fraction = fraction - (whole * 100);
  yposArray[2] = fraction;
}

void CANsend(int ID, int sensor)
{
  Serial.println("CANsend");
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;
  Serial.print("sensor: ");
  Serial.println(sensor);

  if (sensor == PITCH) {
    Serial.println("Pitch");
    float pitch = getPitch();
    Buffer[MESSAGE_TYPE + 1] = pitch < 0 ? 1 : 2;
    pitch = abs(pitch);
    Buffer[MESSAGE_TYPE + 2] = round(floor(pitch));
    Buffer[MESSAGE_TYPE + 3] = round((pitch - floor(pitch)) * 100);
    for (int i = MESSAGE_TYPE + 4; i < 8; i++) Buffer[i];
  }
  else if (sensor == YAW) {
    Serial.println("Yaw");
    float head = getHeading();
    Buffer[MESSAGE_TYPE + 1] = round(floor(head / 10));
    Buffer[MESSAGE_TYPE + 2] = round(floor(head)) % 10;
    Buffer[MESSAGE_TYPE + 3] = round((head - floor(head)) * 100);
    for (int i = MESSAGE_TYPE + 4; i < 8; i++) Buffer[i];
  }
  else {
    Serial.println("default for sonme reason");
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
  if (msg->ctrl.ide > 0) {
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
