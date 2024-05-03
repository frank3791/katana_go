//
//  constant.js
//
//  Copyright 2016 Roland Corporation. All rights reserved.
//

var
	STX		= 'F0',
	ROLAND	= '41',
	RQ1		= '11',
	DT1		= '12',
	EOX		= 'F7';

var
	SYSEX_MAXLEN = 128;

var
	SYSEX_DEAD_LEN = 241;

var
	INTEGER1x1 = 0x10000, // 0000 000a
	INTEGER1x2 = 0x10001, // 0000 00aa
	INTEGER1x3 = 0x10002, // 0000 0aaa
	INTEGER1x4 = 0x10003, // 0000 aaaa
	INTEGER1x5 = 0x10004, // 000a aaaa
	INTEGER1x6 = 0x10005, // 00aa aaaa
	INTEGER1x7 = 0x10006, // 0aaa aaaa
	INTEGER2x4 = 0x10007, // 0000 aaaa, 0000 bbbb
	INTEGER2x7 = 0x1000B, // 0aaa aaaa, 0bbb bbbb
	INTEGER4x4 = 0x10008, // 0000 aaaa, 0000 bbbb, 0000 cccc, 0000 dddd
	PADDING    = 0x20000; // PADDING | bytes

