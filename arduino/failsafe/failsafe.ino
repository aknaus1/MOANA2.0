
/*
   CAN port receiver example
   Receives data on the CAN buss and prints to the serial port
*/

#include <ASTCanLib.h>
#include <Servo.h>

#define MESSAGE_ID 9       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0//rtr bit

#define MESSAGE_TYPE 1
#define IDLE 69

int sensorRequest = 0;

int type = IDLE;

// CAN message object
st_cmd_t Msg;

void CANsend(int ID, int sensor);
void CANIn();
void massDrop();

// Buffer for CAN data
uint8_t Buffer[8] = {};

Servo failSafe;

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
  failSafe.attach(6, 850, 2350);
  canInit(500000);          // Initialise CAN port. must be before Serial.begin
  Serial.begin(1000000);    // start serial port
  Msg.pt_data = &Buffer[0]; // reference message data to buffer
  // Initialise CAN packet.
  // All of these will be overwritten by a received packet
  Msg.ctrl.ide = MESSAGE_PROTOCOL; // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
  Msg.id.ext = MESSAGE_ID;         // Set message ID
  Msg.dlc = MESSAGE_LENGTH;        // Data length: 8 bytes
  Msg.ctrl.rtr = MESSAGE_RTR;      // Set rtr bit
  failSafe.write(180);
  delay(1000);
}

void loop()
{
  CANIn();
  if(type == 1) {
    massDrop();
  }
  else if(type == 2)
  {
    failSafe.write(180);
  }
}

void massDrop()
{
  failSafe.write(90);
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

}
 
void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;
  // Send command to the CAN port controller
  Msg.cmd = CMD_TX_DATA; // send message
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  clearBuffer(&Buffer[0]);
}
