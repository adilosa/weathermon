# weathermon
Raspberry Pi weather monitor for Ambient Weather F007-TH sensors

### F007-TH Data Encoding Format
* RF communication at 434MHz
* Uses Manchester Encoding ( '1' represented by high --> low transition)
* bit time = 1ms
* 195 bit frame, 65 bit packet repeated 3 times
* frames sent every ~1 min (varies by channel)
  * Map of channel id to transmission interval: {1: 53s, 2: 57s, 3: 59s, 4: 61s, 5: 67s, 6: ??s, 7: 71s, 8: 73s}
  * Source: [github.com/gr-ambient](https://github.com/volgy/gr-ambient/blob/master/docs/notes.txt). Ch 6 interval missing there too. 

* Packet Format
  * header: all 1s, with final 01 before data starts 
  * 8 bit sensor ID: F007th = Ox45
  * 8 bit random ID: resets each time the battery is changed
  * 1 bit low battery indicator: 1 ==> low battery
  * 3 bit channel number:  channel 1-8 represented as binary 0-7, selectable on F007th unit using dip switches on back
  * 12 bit temperature data: 
    * To Farenheit: subtract 400 and divide by 10 e.g. 010001001011 => 1099, (1099-400) / 10 = 69.9F
    * To Celsius: subtract 720 and multiply by 0.0556 e.g. (1099 - 720) * 0.0556 = 21.1C
  * 8 bit humidity data: relative humidity as integer
  * 8 bit checksum: [cracked by Ron (BaronVonSchnowzer on Arduino forum)](https://eclecticmusingsofachaoticmind.wordpress.com/2015/01/21/home-automation-temperature-sensors/)
  * padding: some 0s to fill out packet
  

  
**Sample Data:**
```
0        1        2        3        4        5        6        7
FD       45       4F       04       4B       0B       52       0
0   1    2   3    4   5    6   7    8   9    A   B    C   D    E
11111101 01000101 01001111 00000100 01001011 00001011 01010010 0000
header   sensorid randomid BCh#temp_perature humidity checksum xxxx
                           ^ battery, channel number
```
Translates to: 
Channel 1 F007th sensor displaying 21.1 Centigrade and 11% RH



