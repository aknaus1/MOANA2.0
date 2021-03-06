/*UNSURE: These boards have a weird bug where if you divide a float the float will get rounded down. 
This means certain calcuations with a divide symbol will result in a 0. 
This is easily solved by instead changing the division into a multiplication (e.g. /100 = *.01)
I took care of this in most cases but definitely may have missed that in some conversions. 
If you're getting unexpected results on any sensor sends (could be any board) be sure to check for this problem.
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

const int depthTestPin = 14;


int sensorRequest = 0;

unsigned long lastSend = 0;
int type = IDLE;
int input = 0;
int counter = 0;
int water;
int requestBoard = 0;

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

  pinMode(depthTestPin, INPUT);

  while (!depthSensor.init()) {
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
  if (type == 3)
    CANsend(requestBoard, sensorRequest);
  else if (type == 4) {
    if (water == 0)
      depthSensor.setFluidDensity(FRESHWATER); // kg/m^3 (freshwater, 1029 for seawater)
    else
      depthSensor.setFluidDensity(SALTWATER);
  }

  if ((millis() - lastSend) >= 500)
  {
    CANsend(DATA, BOTH);
    lastSend = millis();
  }
}

double getTemp()
{
  depthSensor.read();
  Serial.print("Temp: ");
  Serial.println(depthSensor.temperature());
  return depthSensor.temperature();
}

double getDepth()
{
  depthSensor.read();
  Serial.print("Depth: ");
  Serial.println(depthSensor.depth());
  return depthSensor.depth();
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
  if (id != MESSAGE_ID)   {
    type = IDLE;
    return;
  }
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a direct rudder write or a heading command

  if (type == 3)
  {
    requestBoard = Msg.id.ext;//UNSURE ABOUT THIS, UNTESTED: supposed to be id of board message was received from
    sensorRequest = Msg.pt_data[MESSAGE_TYPE + 1];
  }
  else if (type == 4)
  {
    water = Msg.pt_data[2];
  }
}

void convert(float testValue) // converts a float or double into an array that can be sent over the CAN bus
{
  yposArray[0] = testValue >= 0 ? 2 : 1;
  testValue = abs(testValue);
  yposArray[1] = round(floor(testValue));
  yposArray[2] = (testValue - yposArray[1]) * 100;
}


void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;

  if (sensor == DEPTH)
  {
    convert(getDepth());
    Buffer[2] = yposArray[1];
    Buffer[3] = yposArray[2];
    for (int i = 4; i <= 7; i++)
      Buffer[i] = 0;
  }
  else if (sensor == TEMP) //UNSURE: in testing the data logger was not saving the decimal value of the temperature reading
  {
    convert(getTemp());
    for (int i = 0; i < 6; i++)
      Buffer[i + 2] = i < 4 ? yposArray[i] : Buffer[i + 2];
  }
  else if (sensor == BOTH)
  {
    convert(getDepth());
    Buffer[2] = yposArray[1];
    Buffer[3] = yposArray[2];
    convert(getTemp());
    for (int i = 0; i < 4; i++)
      Buffer[i + 4] = i < 2 ? yposArray[i] : Buffer[i + 4];
  }
  // Send command to the CAN port controller
  Msg.cmd = CMD_TX_DATA; // send message
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  clearBuffer(&Buffer[0]);
}
