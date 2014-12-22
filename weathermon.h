#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <signal.h>

#include <sqlite3.h>
#include <wiringPi.h>

int init();
void init_globals();

void read_signal();
void add_bit(char bit);
void record_sensor_data();
