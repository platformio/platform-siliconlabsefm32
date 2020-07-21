/*
 * Copyright (c) 2006-2020 Arm Limited and affiliates.
 * SPDX-License-Identifier: Apache-2.0
 */
#include "mbed.h"
#include "USBCDC_ECM.h"

/* Ethernet II frame */
typedef struct {
    uint8_t dst_mac[6];
    uint8_t src_mac[6];
    uint16_t eth_type;
    char payload[12];
} packet_t;

static packet_t packet = {
    .dst_mac = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff},
    .src_mac = {0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc},
    .eth_type = 0xaaaa, /* unused EtherType */
    .payload = "Hello world"
};

USBCDC_ECM ecm;

int main()
{
    // Let the USB device to setup
    ThisThread::sleep_for(10);

    // Send "Hello world" packets in loop
    while (true) {
        ecm.send((uint8_t *)&packet, sizeof(packet));
        ThisThread::sleep_for(1000);
    }
}
