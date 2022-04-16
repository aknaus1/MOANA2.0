
/*
   CAN port receiver example
   Receives data on the CAN buss and prints to the serial port
*/

#include <ASTCanLib.h>
#include <Servo.h>
#include <Wire.h>
#include <MS5837.h>

#include <Adafruit_Sensor.h>

MS5837 depthSensor;

#define MESSAGE_ID 9       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0//rtr bit

#define MESSAGE_TYPE 1
#define IDLE 69

int sensorRequest = 0;

int type = IDLE;
int input = 0;
int counter= 0;

// CAN message object
st_cmd_t Msg;

void CANsend(int ID, int sensor);
void CANIn();
void massDrop();

// Buffer for CAN data
uint8_t Buffer[8] = {};

//


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
  MISSION,
  DEPTH_TEMP,
  FAILSAFE
};

void setup()
{
  canInit(500000);          // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000);    // start serial port
  Msg.pt_data = &Buffer[0]; // reference message data to buffer
  Wire.begin();
  // Initialise CAN packet.
  // All of these will be overwritten by a received packet
  Msg.ctrl.ide = MESSAGE_PROTOCOL; // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
  Msg.id.ext = MESSAGE_ID;         // Set message ID
  Msg.dlc = MESSAGE_LENGTH;        // Data length: 8 bytes
  Msg.ctrl.rtr = MESSAGE_RTR;      // Set rtr bit
  
    delay(1000);
}

void loop()
{
  CANIn();
  switch (type)
  {
    case 1:
        massDrop();
        break;
    default:
      break;
  }
}

void CANIn()
{
  clearBuffer(&Buffer[0]);
  Serial.println("CANin"); 
  Msg.cmd = CMD_RX_DATA;   // Send command to the CAN port controller
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED) ;
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  
  int id = 0;
  id = Msg.pt_data[0];
  if (id != MESSAGE_ID) return;
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a direct rudder write or a heading command

  switch (type) {
    default:
      Serial.println("Not a valid type!");
      break;
  }
}
 

void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;
  switch (sensor) {
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