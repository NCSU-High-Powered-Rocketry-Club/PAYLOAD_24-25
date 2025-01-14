#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <iostream>
#include <vector>

// Pin Definitions
#define SDN_PIN 27 // Shutdown pin
#define CS_PIN 8   // Chip Select pin
#define IRQ_PIN 13 // Interrupt pin (optional)

// SPI Channel and Speed
#define SPI_CHANNEL 0
#define SPI_SPEED 500000 // 500 kHz

// Si4464 Commands
#define CMD_PART_INFO 0x01
#define CMD_GET_INT_STATUS 0x20
#define CMD_NOP 0x00

// Function Prototypes
void initializePins();
void powerOnModule();
void resetSi4464();
void sendCommand(uint8_t cmd, const std::vector<uint8_t> &args);
std::vector<uint8_t> readResponse(size_t length);
void readPartInfo();
void getIntStatus();
void sendNOP();
void printResponse(const std::string &label, const std::vector<uint8_t> &response);

int main() {
    // Initialize WiringPi
    if (wiringPiSetupGpio() == -1) {
        std::cerr << "Failed to initialize wiringPi!" << std::endl;
        return 1;
    }

    // Initialize SPI
    if (wiringPiSPISetup(SPI_CHANNEL, SPI_SPEED) == -1) {
        std::cerr << "Failed to initialize SPI!" << std::endl;
        return 1;
    }

    // Initialize GPIO Pins
    initializePins();

    // Power on and reset the Si4464 module
    powerOnModule();
    resetSi4464();

    // Test Commands
    sendNOP();
    readPartInfo();
    getIntStatus();

    return 0;
}

void initializePins() {
    pinMode(SDN_PIN, OUTPUT);
    pinMode(CS_PIN, OUTPUT);
    pinMode(IRQ_PIN, INPUT);

    // Ensure module is powered off initially
    digitalWrite(SDN_PIN, HIGH);
    digitalWrite(CS_PIN, HIGH);
    std::cout << "GPIO Pins Initialized." << std::endl;
}

void powerOnModule() {
    digitalWrite(SDN_PIN, LOW); // Pull SDN low to power on
    delay(10);                  // Stabilization delay
    std::cout << "Si4464 Module Powered On." << std::endl;
}

void resetSi4464() {
    std::cout << "Resetting Si4464..." << std::endl;
    digitalWrite(SDN_PIN, HIGH); // Pull SDN high to reset
    delay(10);
    digitalWrite(SDN_PIN, LOW); // Pull SDN low to exit reset
    delay(10);                  // Stabilization delay
    std::cout << "Si4464 Reset Complete." << std::endl;
}

void sendCommand(uint8_t cmd, const std::vector<uint8_t> &args) {
    digitalWrite(CS_PIN, LOW); // Assert CS
    std::vector<uint8_t> data = {cmd};
    data.insert(data.end(), args.begin(), args.end());
    wiringPiSPIDataRW(SPI_CHANNEL, data.data(), data.size());
    digitalWrite(CS_PIN, HIGH); // Deassert CS
}

std::vector<uint8_t> readResponse(size_t length) {
    std::vector<uint8_t> response(length, 0);
    size_t timeout = 1000;

    while (timeout > 0) {
        digitalWrite(CS_PIN, LOW);
        uint8_t cmdBuffer[1] = {0x44}; // Read CMD buffer
        wiringPiSPIDataRW(SPI_CHANNEL, cmdBuffer, 1);

        uint8_t ctsBuffer[1] = {0x00};
        wiringPiSPIDataRW(SPI_CHANNEL, ctsBuffer, 1);
        std::cout << "CTS: 0x" << std::hex << (int)ctsBuffer[0] << std::endl;

        if (ctsBuffer[0] == 0xFF) {
            wiringPiSPIDataRW(SPI_CHANNEL, response.data(), response.size());
            digitalWrite(CS_PIN, HIGH);
            return response;
        }
        digitalWrite(CS_PIN, HIGH);
        delay(1); // Small delay before retrying
        timeout--;
    }

    std::cerr << "Error: Timeout waiting for CTS." << std::endl;
    return {};
}

void readPartInfo() {
    std::cout << "Sending PART_INFO Command..." << std::endl;
    sendCommand(CMD_PART_INFO, {});
    auto response = readResponse(8);
    printResponse("PART_INFO Response", response);
}

void getIntStatus() {
    std::cout << "Sending GET_INT_STATUS Command..." << std::endl;
    sendCommand(CMD_GET_INT_STATUS, {0x00, 0x00, 0x00});
    auto response = readResponse(8);
    printResponse("GET_INT_STATUS Response", response);
}

void sendNOP() {
    std::cout << "Sending NOP Command..." << std::endl;
    sendCommand(CMD_NOP, {});
}

void printResponse(const std::string &label, const std::vector<uint8_t> &response) {
    std::cout << label << " [" << response.size() << " bytes]: ";
    for (const auto &byte : response) {
        std::cout << "0x" << std::hex << (int)byte << " ";
    }
    std::cout << std::endl;
}
