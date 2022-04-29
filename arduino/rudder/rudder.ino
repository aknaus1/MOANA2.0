
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

#define HEADING_KP .4

#define MAX_RUDDER_ANGLE 20
#define RUDDER_OFFSET 130

#define BNO055_SAMPLERATE_DELAY_MS 10
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
#define IDLE 69

int sensorRequest = 0;
int type = IDLE;
int input = 0;
float heading_kp = HEADING_KP;

// CAN message object
st_cmd_t Msg;

void CANsend(int ID, int sensor);
void CANIn();
float getHeading();

// Buffer for CAN data
uint8_t Buffer[8] = {};

enum sensorSend
{
  DEPTH,
  PITCH,
  YAW,
  STEP_POS,
  TEMP,
  SLIDER,
  BOTH,
  THRUSTER_COMMAND,
  ROLL
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
  //rudder.write(RUDDER_OFFSET);
}

void setRudder(float angle)
{
  angle+=RUDDER_OFFSET;// servo needs a const offset ~140 degrees in order to be lined up properly
  Serial.print("Angle before limitation: ");
  Serial.println(angle - RUDDER_OFFSET);
  if (abs(angle - RUDDER_OFFSET) <= MAX_RUDDER_ANGLE)
    rudder.write(angle);
  else if (angle - RUDDER_OFFSET > MAX_RUDDER_ANGLE)//if new rudder angle would be over the max rudder angle
    rudder.write(MAX_RUDDER_ANGLE + RUDDER_OFFSET);
  else
    rudder.write(-MAX_RUDDER_ANGLE + RUDDER_OFFSET);//if new rudder angle would be over the max rudder angle
}

void loop()
{
  CANIn();
  if (type == 0) {
    setRudder(input);
  }
  else if (type == 1) {
    float cur_heading = getHeading();
    float angle = 0;
    if (input + 180 < cur_heading)
      angle = (input - (cur_heading - 360)) * heading_kp;
    else
      angle = (input - cur_heading) * heading_kp;
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
  float xpos = event.orientation.x;
  Serial.print("Orientation: ");
  Serial.println(xpos);
  return xpos;
}

float getPitch() // reads pitch from sensor
{
  sensors_event_t event;
  bno.getEvent(&event);
  float zpos = event.orientation.z;
  Serial.print("Pitch: ");
  Serial.println(zpos);
  return zpos;
}

float getRoll() // reads roll from sensor
{
  sensors_event_t event;
  bno.getEvent(&event);
  float ypos = event.orientation.y;
  Serial.print("Roll: ");
  Serial.println(ypos);
  return ypos;
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
  if (id != MESSAGE_ID) {
    type = IDLE;
    return;
  }
  //saveType();
  type = Msg.pt_data[MESSAGE_TYPE]; // determines whether message indicates a direct rudder write or a heading command

  if(type == 0)
    input = Msg.pt_data[MESSAGE_TYPE + 1] == 1 ? Msg.pt_data[MESSAGE_TYPE + 2] : -Msg.pt_data[MESSAGE_TYPE + 2]; // return rudder angle
  else if(type == 1)
    input = Msg.pt_data[MESSAGE_TYPE + 1] * 10 + Msg.pt_data[MESSAGE_TYPE + 2];//return heading
  else if(type == 3)
    sensorRequest = Msg.pt_data[MESSAGE_TYPE + 1];//tell board to send a sensor request
  else if(type == 5)
    heading_kp = Msg.pt_data[MESSAGE_TYPE + 1] + Msg.pt_data[MESSAGE_TYPE + 2] / 100;//set heading kp with laptop

}

void fillRollPitch(float rollPitch) //sets up CAN message for roll and pitch sensor readings
{
  Buffer[MESSAGE_TYPE + 1] = rollPitch < 0 ? 1 : 2;
  rollPitch = abs(rollPitch);
  Buffer[MESSAGE_TYPE + 2] = round(floor(rollPitch));
  Buffer[MESSAGE_TYPE + 3] = round((rollPitch - floor(rollPitch)) * 100);
  for (int i = MESSAGE_TYPE + 4; i < 8; i++) Buffer[i];
}

void CANsend(int ID, int sensor)
{
  Serial.println("CANsend");
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;

  if (sensor == PITCH) {
    Serial.println("Pitch");
    fillRollPitch(getPitch());
  }
  else if (sensor == YAW) {
    Serial.println("Yaw");
    float head = getHeading();
    Buffer[MESSAGE_TYPE + 1] = round(floor(head / 10));
    Buffer[MESSAGE_TYPE + 2] = round(floor(head)) % 10;
    Buffer[MESSAGE_TYPE + 3] = round((head - floor(head)) * 100);
    for (int i = MESSAGE_TYPE + 4; i < 8; i++) Buffer[i];
  }
  else if (sensor == ROLL){
    Serial.println("Roll");
    fillRollPitch(getRoll());
  }
  else if (sensor == BOTH)//sends both pitch and heading
  {
    Serial.println("Pitch");
    fillRollPitch(getPitch());

    Serial.println("Yaw");
    float head = getHeading();
    Buffer[MESSAGE_TYPE + 4] = round(floor(head / 10));
    Buffer[MESSAGE_TYPE + 5] = round(floor(head)) % 10;
    Buffer[MESSAGE_TYPE + 6] = round((head - floor(head)) * 100);
  }

  // Send command to the CAN port controller
  Msg.cmd = CMD_TX_DATA; // send message
  // Wait for the command to be accepted by the controller
  while (can_cmd(&Msg) != CAN_CMD_ACCEPTED);
  // Wait for command to finish executing
  while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED);
  clearBuffer(&Buffer[0]);
}
