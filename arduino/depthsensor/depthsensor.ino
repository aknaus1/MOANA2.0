
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

#define MESSAGE_ID 8       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0//rtr bit

#define FRESHWATER 997
#define SALTWATER 1029

#define MESSAGE_TYPE 1
#define IDLE 69

const int intPin = 9;//pin that will send an interrupt

int sensorRequest = 0;

int type = IDLE;
int input = 0;
int water;

// CAN message object
st_cmd_t Msg;

void CANsend(int ID, int sensor);
void CANIn();

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
  
  pinMode(intPin, OUTPUT);
  digitalWrite(intPin, HIGH);
  while (!depthSensor.init()){
    Serial.println("Init failed!");
    Serial.println("Are SDA/SCL connected correctly?");
    Serial.println("Blue Robotics Bar30: White=SDA, Green=SCL");
    Serial.println("\n\n\n");
    delay(5000);
  }
  depthSensor.setModel(MS5837::MS5837_30BA);
  depthSensor.setFluidDensity(FRESHWATER);
    delay(1000);
}

void loop()
{
  CANIn();
  switch (type)
  {
    case 3:
      CANsend(JETSON, sensorRequest);
      break;
    case 4://water density
      if (water == 0)
        depthSensor.setFluidDensity(FRESHWATER); // kg/m^3 (freshwater, 1029 for seawater)
      else
        depthSensor.setFluidDensity(SALTWATER);
      break;
    case IDLE:
      break;
    default:
      break;
  }
  //Serial.println(digitalRead(intPin));
  delay(500);
}

double getTemp()
{
  return depthSensor.temperature();
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
  digitalWrite(intPin, LOW);
  delay(500);
  digitalWrite(intPin, HIGH);
  Serial.println("Interrupt");
  id = Msg.pt_data[0];
  if (id != MESSAGE_ID) return;
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a direct rudder write or a heading command

  switch (type) {
    case 3:
      sensorRequest = Msg.pt_data[MESSAGE_TYPE + 1];
      break;
    case 4: //water density
      water = Msg.pt_data[2];
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
}

void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;
  switch (sensor) {
    case DEPTH:
      convert(depthSensor.depth());
      Buffer[2] = yposArray[1];
      Buffer[3] = yposArray[2];
      for (int i = 4; i <= 7; i++)
        Buffer[i] = 0;
      break;
    case TEMP:
      convert(getTemp());
      for (int i = 0; i < 6; i++)
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
  clearBuffer(&Buffer[0]);
}