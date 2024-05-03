//
//  converter.js
//
//  Copyright 2016 Roland Corporation. All rights reserved.
//

	function nibble(x) {
		return (
			((x & 0x7f000000) >>> 3) |
			((x & 0x007f0000) >>> 2) |
			((x & 0x00007f00) >>> 1) |
			((x & 0x0000007f))
		);
	}

	function nibble_le(x) {
		return nibble(
			((x & 0x7f000000) >>> 24) |
			((x & 0x007f0000) >>>  8) |
			((x & 0x00007f00) <<   8) |
			((x & 0x0000007f) <<  24)
		);
	}

	function _7bitize(x) {
		return (
			((x & 0x0fe00000) << 3) |
			((x & 0x001fc000) << 2) |
			((x & 0x00003f80) << 1) |
			((x & 0x0000007f))
		);
	}

	function hex2(x) {
		var s = x.toString(16).toUpperCase();
		return (x < 0x10) ? '0' + s : s;
	}

	function hex4(x) {
		if (x <= 0x80) {
			return '00' + hex2(x);
		}
		var x2 = x - 0x80;
		var x1 = (x - x2) >> 7;
		return hex2(x1) + hex2(x2);
	}



	function _bid(bid, i) {
		var t = bid.split('%');
		if (i === undefined) {
			t[0] = t[0].replace(/\([0-9]+\)$/g, ''); /* remove part or librarian row */
		} else {
			t[0] += '(' + (i + 1) + ')'; /* append part or librarian row */
		}
		return t.join('%');
	}
