#define SERIAL_EMG Serial1
#define SERIAL_PI Serial2

#define NO_EMG_DATA 0
#define EMG_DATA    1

#define WIDTH  (16 * sizeof(byte))
#define TOPBIT (1 << (WIDTH - 1))
#define POLYNOMIAL 0x1021

int emgPresent = 0;

//6.2 million

#define fs 4000                                   //   sample rate in Hz
#define Fc 100                                    //   corner frequency of EMA filter (Hz)
float coA = (1-exp(-6.3*Fc/fs));

int piMsgCount = 0;
byte crcTable[256];

class ImbRxFrame
{
public:
    // Initially, this is where the raw frame contents are stored.
    // After process_frame method, this is the byte buffer where
    // post-escape characters are stored as well. Will never contain
    // the EOF character (0xC0)
    byte frame[2048];
    volatile int currentIndex;

    // Default is FALSE. Ready flag is TRUE when full frame has been received
    // When SW is done processing the frame contents, MUST set
    // this flag to false. If an error is found, ready will remain
    // FALSE
    volatile bool ready;

    // Parsed frame contents
    volatile byte sync1;
    volatile byte sync2;
    volatile byte respTok;
    volatile byte respCode;
    volatile byte ack;
    volatile byte length;
    volatile uint16_t packetCnt;
    volatile byte payload[255];
    volatile uint16_t crc;

    String name;
    bool debugPrint;

    // Process the incoming frame with checks
    void process_frame();

    // Add a new byte to the frame. This method will manage the currentIndex,
    // so don't need to touch currentIndex
    void add_new_byte(byte newByte);

    // Constructor: provide a string name for debug print msgs
    ImbRxFrame(String name, bool debugPrint);
};

ImbRxFrame emgRxFrame("EMG", false);
elapsedMillis sendPeriod = 0;
bool startFound = false;
bool secondFound = false;

struct bpf {

  float b0, b1, b2, a1, a2;
  float x1 = 0;
  float x2 = 0;
  float y1 = 0;
  float y2 = 0;

  float process(float x) {
    float y = (b0 * x) + (b1 * x1) + (b2 * x2) - (a1 * y1) - (a2 * y2);

    x2 = x1; 
    x1 = x;

    y2 = y1;
    y1 = y;

    return y;
  }
};

bpf highPass[8];
bpf lowPass[8];
bpf notch60[8];


//pasted from MATLAB script EPM_bpf_coeffs
void initFilters() {
    for (int i = 0; i < 8; i++) {
        // highPass
        highPass[i] = { 1.0f, 0.0f, 0.0f, 0.0f, 0.0f};
        // lowPass
        lowPass[i] = { 1.0f, 0.0f, 0.0f, 0.0f, 0.0f};
        // 60 Hz notch
        notch60[i] = { 1.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    }
}

void setup() {
  
  pinMode(LED_BUILTIN, OUTPUT);
  startFound = false;
  secondFound = false;
  emgPresent = NO_EMG_DATA;
  piMsgCount = 0;
  emgRxFrame.currentIndex = 0;
  emgRxFrame.ready = false;
  memset(emgRxFrame.frame, 0, sizeof(emgRxFrame.frame));
  memset((void*)emgRxFrame.payload, 0, sizeof(emgRxFrame.payload));

  for (int i = 0; i < 5; i++){
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }

  delay(3000); // wait for power to stabilize and for Pi to finish booting

  //clear any garbage that showed up on serial while pi is booting
  while(SERIAL_PI.available()) {
    SERIAL_PI.read();
  }

  // put your setup code here, to run once:
  SERIAL_EMG.begin(2764800);
  SERIAL_PI.begin(2764800);

  initFilters();
}

void loop() {

  checkEmgSerial();
  
  if(emgPresent == EMG_DATA){
    emgPresent = NO_EMG_DATA;
    sendToPi();
  }
}

// Polynomial: x^16 + x^12 + x^5 + 1 (0x1021)
uint16_t crc_xmodem_update (uint16_t crc, uint8_t data)
{
  int i;

  crc = crc ^ ((uint16_t)data << 8);
  for (i=0; i<8; i++) {
    if (crc & 0x8000) crc = (crc << 1) ^ 0x1021; //(polynomial = 0x1021)
    else crc <<= 1;
  }
  return crc;
}

uint16_t calc_crc(char *msg,int n)
{
  // Initial value. xmodem uses 0xFFFF but this example
  // requires an initial value of zero.
  uint16_t x = 0;

  while(n--) {
    x = crc_xmodem_update(x, (uint16_t)*msg++);
  }
  return(x);
}

int32_t unsignedToSigned(byte b1, byte b2, byte b3){

  int data = (b1 << 16 | b2 << 8 | b3);

  int32_t dataFinal = (data & ~(1 << 23)) + (((data >> 23) & 1) * pow(-2, 23));

  return dataFinal;

}

void sendToPi(){

  uint8_t out[24];

  for(int ch = 0; ch < 8; ch++){
      int ema = unsignedToSigned(emgRxFrame.payload[ch*3], emgRxFrame.payload[ch*3 + 1], emgRxFrame.payload[ch*3 + 2]);
      float sample = (float)ema;
      // sample = highPass[ch].process(sample);
      // sample = lowPass[ch].process(sample);
      // sample = notch60[ch].process(sample);

      int32_t filtered = (int32_t)sample;

      // clamp to 24-bit signed
      if(filtered > 8388607) filtered = 8388607;    //0x7FFFFF
      if(filtered < -8388608) filtered = -8388608;  //-0x800000
      uint32_t filteredBytes = (uint32_t)(filtered & 0x00FFFFFF);

      out[ch*3] = (filteredBytes >> 16) & 0xFF;
      out[ch*3 + 1] = (filteredBytes >> 8) & 0xFF;
      out[ch*3 + 2] = filteredBytes & 0xFF;
  }

  byte piMsgBuild[29] = {0x40, 0x00, 0x1A, (piMsgCount & 0xFF), (piMsgCount << 8), 
                  out[0], out[1], out[2], 
                  out[3], out[4], out[5],
                  out[6], out[7], out[8],
                  out[9], out[10], out[11],
                  out[12], out[13], out[14],
                  out[15], out[16], out[17],
                  out[18], out[19], out[20],
                  out[21], out[22], out[23]};

  uint16_t crc = calc_crc(piMsgBuild, 29);

  byte piMsgSend[33] = {0xFC, 0x1A, 0x40, 0x00, 0x1A, (piMsgCount & 0xFF), (piMsgCount << 8),
                  out[0], out[1], out[2], 
                  out[3], out[4], out[5],
                  out[6], out[7], out[8],
                  out[9], out[10], out[11],
                  out[12], out[13], out[14],
                  out[15], out[16], out[17],
                  out[18], out[19], out[20],
                  out[21], out[22], out[23],
                  (byte)(crc >> 8), (byte)(crc & 0xFF)};

  SERIAL_PI.write(piMsgSend, sizeof(piMsgSend));
  piMsgCount++;

}

// EMG data received
void checkEmgSerial(){

  while(SERIAL_EMG.available()){

    byte tmp = SERIAL_EMG.read();

    // if start not found, compare incoming byte to first byte
    if(!startFound){

      // if byte is FC
      if(tmp == (byte)0xFC) {

        // skip 'start-not-found' loop, reset indexing
        startFound = true;
        emgRxFrame.currentIndex = 0;
        emgRxFrame.add_new_byte(tmp);
        continue;
      }
      else continue;
    }

    if(!secondFound){
      if(tmp == (byte)0x1A){
        secondFound = true;
      }
      else{
        startFound = false;
        continue;
      }
    }

    emgRxFrame.add_new_byte(tmp);

    if(emgRxFrame.ready) {
      emgPresent = EMG_DATA;

      emgRxFrame.ready = false;
      startFound = false;
      secondFound = false;
    }
  }
}

// Constructor (initialization of member vars)
ImbRxFrame::ImbRxFrame(String name, bool debugPrint)
{
    ready = false;
    currentIndex = 0;

    this->debugPrint = debugPrint;

    this->name = name;
}

// Add a new byte to the frame
void ImbRxFrame::add_new_byte(byte newByte)
{
  frame[currentIndex] = newByte;
  currentIndex++;

  if(currentIndex > 32) {
    process_frame();
  }
}

void ImbRxFrame::process_frame()
{
    bool badFrame = false;

    sync1 = frame[0];
    sync2 = frame[1];
    respTok = frame[2];
    respCode = frame[3];
    length = frame[4];
    packetCnt = ((int)frame[6] << 8) | (int)(frame[5]);

    if(sync1 != (byte)0xFC | sync2 != (byte)0x1A) {
      badFrame = true;
      // SerialUSB.print("e1 ");
      // SerialUSB.print(sync1, HEX);
      // SerialUSB.println(sync2, HEX);
    }
    else if(respTok != (byte)0x40 | respCode != (byte)0x00){
      badFrame = true;
      // SerialUSB.print("e2 ");
      // SerialUSB.print(respTok, HEX);
      // SerialUSB.println(respCode, HEX);
    }
    else if(length != (byte)0x1A){
      badFrame = true;
      // SerialUSB.println("e3");
    }

    // Fill the remaining fields of the frame, length includes 2 crc bytes
    for (int i = 0; i < length - 2; i++)
    {
        payload[i] = frame[7 + i];
    }

    // Check for correct crc
    crc = ((uint16_t)frame[currentIndex - 1] << 8) | (uint16_t)(frame[currentIndex - 2]);

    byte crcFrame[length - 2 + 5]; // length includes 2 CRC bits (-2) but excludes header (+5)
    for(int i = 2; i < sizeof(crcFrame) + 2; i++){
      crcFrame[i - 2] = frame[i];
    }
    uint16_t crcCheck = calc_crc(crcFrame, sizeof(crcFrame));

    if (crc != crcCheck){ 
      // SerialUSB.print("e3 ");
      // SerialUSB.print(crc);
      // SerialUSB.print(" != ");
      // SerialUSB.println(crcCheck);
      badFrame = true; 
    }

    if (!badFrame)
    {
        ready = true;
    }

    currentIndex = 0;
    startFound = false;
    secondFound = false;
}


