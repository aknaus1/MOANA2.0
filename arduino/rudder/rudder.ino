
/*
 * CAN port receiver example
 * Receives data on the CAN buss and prints to the serial port
 */

#include <ASTCanLib.h>
#include <Servo.h>
#include <Wire.h>

#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

Servo rudder;

#define MESSAGE_ID 3       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0      // rtr bit

#define MESSAGE_TYPE 2
#define HEADING_KP .15
#define KD .21
#define MAX_RUDDER_ANGLE 20

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
int type = 0; 
int input = 0;
int sent = 0;
float heading_kp = HEADING_KP;
int previousState = IDLE;

enum d{LEFT=1, RIGHT};

#define HEADING_SENSOR 2
#define JETSON 1

int direction;
// Function prototypes
void serialPrintData(st_cmd_t *msg);

// CAN message object
st_cmd_t Msg;

void CANsend(int ID, int sensor);
void saveType();

// Buffer for CAN data
uint8_t Buffer[8] = {};
int yposArray[3];

void setup()
{
  // Assign PIN 6 to servo, with range between 850ms and 2350ms
  rudder.attach(6, 850, 2350);

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
  clearBuffer(&Buffer[0]); // Send command to the CAN port controller
  Msg.cmd = CMD_RX_DATA;   // Wait for the command to be accepted by the controller
  if ((can_cmd(&Msg) == CAN_CMD_ACCEPTED) && (can_get_status(&Msg) != CAN_STATUS_NOT_COMPLETED))
    input = CANin();
  CANsend(6); // data to data logger

  switch(type)
  {
    case 0:
      if (abs(input) <= MAX_RUDDER_ANGLE)
        rudder.write(input);
      else
        Serial.println("Input angle cannot be higher than %d degrees", MAX_RUDDER_ANGLE);
    case 1:
      if (direction)//if auv is turning around, need to specify which direction to turn. 
        turn(direction);
      setHeading(input);
      break;
    case 3:
      if(sent == 0){
         CANsend(JETSON, sensorRequest);
         sent = 1;
      }
      type = previousState;
      break;
    case 5://set heading_kp in  CANin
      type = previousState;
      break;
    case IDLE:
      break;
    default:
      break;
  }
  delay(500);
  /*
    // Clear the message buffer
    clearBuffer(&Buffer[0]);

    // Send command to the CAN port controller
    Msg.cmd = CMD_RX_DATA;

    // Wait for the command to be accepted by the controller
    while(can_cmd(&Msg) != CAN_CMD_ACCEPTED);
    // Wait for command to finish executing
    while(can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
    // Data is now available in the message object
    // Print received data to the terminal
    serialPrintData(&Msg);

    int temp, id;
    id = Msg.pt_data[0];

  */
  /*
    if(id == 3){
      //     Serial.print("accepted message\n");
  //     Serial.print("Moving servo to position: ");
  //     Serial.print(Msg.pt_data[1]);
  //     Serial.print("\n");
      temp = Msg.pt_data[1];
    }*/
}

void saveType() {//if the current state is one that should be reverted to once the new state has finished, then save the current state 
  if(type < 3)
    previousState = type;
}

float getHeading()
{
  Serial.println("GETTING SENSOR YDATA:");
  sensors_event_t event;
  bno.getEvent(&event);
  ypos = event.orientation.z;
  xpos = event.orientation.x;
  Serial.println("Outside ypos : ");
  Serial.println(ypos);
  Serial.println("Orientation: ");
  Serial.println(xpos);
  return xpos;
}

void turn(int dir, int heading)//this solution is kind of janky but basically turn function gets the turn started in the direction we want, so that get heading will definitely go the direction intended
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
  float newAngle = (h - getHeading()) * heading_kp + KD; // new angle will now be from 0 - some float angle that should be maxed to 40
  if (newAngle > MAX_RUDDER_ANGLE * 2)
    newAngle = MAX_RUDDER_ANGLE * 2;
  newAngle -= MAX_RUDDER_ANGLE;
  rudder.write(newAngle);
}

int CANIn()
{
  int id = 0;
  id = Msg.pt_data[0];
  if (id != MESSAGE_ID) return;
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a direct rudder write or a heading command
  switch(type) {
    case 0:
      return Msg.pt_data[MESSAGE_TYPE + 1] == 1 ? Msg.pt_data[MESSAGE_TYPE + 2] : -Msg.pt_data[MESSAGE_TYPE + 2]; // return rudder angle
      break;
    case 1:
      direction = Msg.pt_data[4];
      return (Msg.pt_data[MESSAGE_TYPE + 1] * 10) + Msg.pt_data[MESSAGE_TYPE + 2]; // return heading in degrees
      break;
    case 3:
      sensorRequest = Msg.pt_data[MESSAGE_TYPE + 1];
      break;
    case 5:
      heading_kp = Msg.pt_data[MESSAGE_TYPE + 1] + (Msg.pt_data[MESSAGE_TYPE + 2] / 100)
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

void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;
  switch (sensor) {
    case HEADING_SENSOR:
      convert(getHeading());
      for (int i = 0; i < 7; i++)
        Buffer[i + 2] = i < 4 ? yposArray[i] : Buffer[i + 2];
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
