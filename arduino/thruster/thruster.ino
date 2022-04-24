#include <ASTCanLib.h>
#include <Adafruit_BNO055.h>
#include <Servo.h>
void CANsend(int ID, int sensor);
// testing:
Servo thrustESC;
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

#define MESSAGE_ID 2       // Message ID
#define MESSAGE_PROTOCOL 1 // CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
#define MESSAGE_LENGTH 8   // Data length: 8 bytes
#define MESSAGE_RTR 0      // rtr bit
#define MESSAGE_TYPE 1

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
    THRUST,
    RUDDER,
    DEPTH_PITCH = 5,
    DATA,
    MISSION,
    DEPTH_TEMP,
    FAILSAFE
};

// Function prototypes
void serialPrintData(st_cmd_t *msg);

// CAN message object
st_cmd_t Msg;

int yposArray[3];
void convert(float testValue);


// Buffer for CAN data
uint8_t Buffer[8] = {};

void setup()
{
    // put your setup code here, to run once:

    // Treat ESC like a servo
    // Map to pin 6 with signals between 1000 and 2000 ms
    thrustESC.attach(6, 1000, 2000);

    canInit(500000);          // Initialise CAN port. must be before Serial.begin
    Serial.begin(1000000);    // start serial port
    Msg.pt_data = &Buffer[0]; // reference message data to buffer

    // Initialise CAN packet.
    // All of these will be overwritten by a received packet
    Msg.ctrl.ide = MESSAGE_PROTOCOL; // Set CAN protocol (0: CAN 2.0A, 1: CAN 2.0B)
    Msg.id.ext = MESSAGE_ID;         // Set message ID
    Msg.dlc = MESSAGE_LENGTH;        // Data length: 8 bytes
    Msg.ctrl.rtr = MESSAGE_RTR;      // Set rtr bit

    if (!bno.begin())
    {
        /* There was a problem detecting the BNO055 ... check your connections */
        Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
        while (1)
            ;
    }
    delay(1000);
    bno.setExtCrystalUse(true);

    // Arm ESC manually with low - high - low signals
    thrustESC.write(1500);
    delay(3000);
}

void loop()
{
    // Clear the message buffer
    clearBuffer(&Buffer[0]);

    // Send command to the CAN port controller
    Msg.cmd = CMD_RX_DATA;

    // Wait for the command to be accepted by the controller
    while (can_cmd(&Msg) != CAN_CMD_ACCEPTED)
        ;
    // Wait for command to finish executing
    while (can_get_status(&Msg) == CAN_STATUS_NOT_COMPLETED)
        ;
    // Data is now available in the message object
    // Print received data to the terminal
    serialPrintData(&Msg);

    int dir, power, id, duration, type;
    id = Msg.pt_data[0];
    type = Msg.pt_data[1];
    switch(type) {
        case PITCH:
            CANsend(DEPTH_PITCH, PITCH);
            break;
        case YAW:
            CANsend(RUDDER, YAW);
            break;
        case THRUSTER_COMMAND:
            dir = Msg.pt_data[MESSAGE_TYPE+1];      // 1 is negative thrust, 2 is positive thrust
            power = Msg.pt_data[MESSAGE_TYPE+2];    // Range 0 - 100 for percent power
            duration = Msg.pt_data[MESSAGE_TYPE+3]; // 255 for indefinite, 1-254 are seconds
            if (dir == 1)
            {
                power = power * -1;
            }
            if (duration == 255)
            {
                // Turn on thruster indefinitely
                // Call mapping function to take 0-100 scale and convert to PWM signal
                thrustESC.write(mapping(power));
            }
            else
            {
                // Turn on thruster for a bit
                thrustESC.write(mapping(power));
                delay(duration * 1000);
                thrustESC.write(mapping(0));
            }
            break;
        default: break;
    }
}

int mapping(int input)
{ // Map input values from 0 - 100 to blue robotics thruster pwm values
    input = input * 4 + 1500;
    return input;
}

void CANsend(int ID, int sensor)
{
  clearBuffer(&Buffer[0]);
  Msg.id.ext = MESSAGE_ID; // Set message ID
  Buffer[0] = ID;
  Buffer[1] = sensor;
  switch (sensor) {
    case PITCH:
        sensors_event_t event;
        bno.getEvent(&event);
        float ypos = event.orientation.z;
        convert(ypos);
        for (int i = 0; i < 6; i++)
            Buffer[i + 2] = i < 4 ? yposArray[i] : Buffer[i + 2];
        break;
    case YAW:
        bno.getEvent(&event);
        float xpos = event.orientation.x;
        convert(xpos);
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
  clearBuffer(&Buffer[0]);
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

void serialPrintData(st_cmd_t *msg)
{
    char textBuffer[50] = {
        0};
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
