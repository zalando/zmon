/*
 * Color Hash
 *
 * An implementation of a string to color converter based on DeployCtl's manifest_color
 *
 */

var getColorPalette = function(labels) {
    var palette = {};
    var fixedPalette = ["#088da5", "#cc0000",  "#ffa500", "#008000", "#0000ff", "#ff00ff", "#999999",
      "#ffff00", "#0DD621", "#ff6666", "#800000", "#660066", "#40e0d0", "#333333" ];
    _.each(labels.sort(), function(label, i) {
        if (i < fixedPalette.length) {
            palette[label] = fixedPalette[i];
        } else {
            palette[label] = getColorByIndex(i, labels.length);
        }
    });
    return palette;
};

var getColorByIndex = function(index, total) {
    var rgb = hsvToRgb(index * (360/total), index > total/2 ? 60 : 90, index % 2 ? 60 : 90);
    var color = {
        r: rgb[0] < 16 ? "0" + rgb[0].toString(16) : rgb[0].toString(16),
        g: rgb[1] < 16 ? "0" + rgb[1].toString(16) : rgb[1].toString(16),
        b: rgb[2] < 16 ? "0" + rgb[2].toString(16) : rgb[2].toString(16)
    };
    return '#' + color.r + color.g + color.b;
}

var colorHash = function(str) {

    if (!str) return '#1E90FF';

    var v = crc32(str);
    var rgb = hsvToRgb((v % 100) * 36, 80, 90);
    var color = {
        r: rgb[0] < 16 ? "0" + rgb[0].toString(16) : rgb[0].toString(16),
        g: rgb[1] < 16 ? "0" + rgb[1].toString(16) : rgb[1].toString(16),
        b: rgb[2] < 16 ? "0" + rgb[2].toString(16) : rgb[2].toString(16)
    };
    return '#' + color.r + color.g + color.b;
};

var makeCRCTable = function(){
    var c;
    var crcTable = [];
    for(var n =0; n < 256; n++){
        c = n;
        for(var k =0; k < 8; k++){
            c = ((c&1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1));
        }
        crcTable[n] = c;
    }
    return crcTable;
}

var crc32 = function(str) {
    var crcTable = window.crcTable || (window.crcTable = makeCRCTable());
    var crc = 0 ^ (-1);

    for (var i = 0; i < str.length; i++ ) {
        crc = (crc >>> 8) ^ crcTable[(crc ^ str.charCodeAt(i)) & 0xFF];
    }

    return (crc ^ (-1)) >>> 0;
};

function hsvToRgb(h, s, v) {
    var r, g, b;
    var i;
    var f, p, q, t;

    // Make sure our arguments stay in-range
    h = Math.max(0, Math.min(360, h));
    s = Math.max(0, Math.min(100, s));
    v = Math.max(0, Math.min(100, v));

    // We accept saturation and value arguments from 0 to 100 because that's
    // how Photoshop represents those values. Internally, however, the
    // saturation and value are calculated from a range of 0 to 1. We make
    // That conversion here.
    s /= 100;
    v /= 100;

    if(s == 0) {
        // Achromatic (grey)
        r = g = b = v;
        return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
    }

    h /= 60; // sector 0 to 5
    i = Math.floor(h);
    f = h - i; // factorial part of h
    p = v * (1 - s);
    q = v * (1 - s * f);
    t = v * (1 - s * (1 - f));

    switch(i) {
        case 0:
            r = v;
            g = t;
            b = p;
            break;

        case 1:
            r = q;
            g = v;
            b = p;
            break;

        case 2:
            r = p;
            g = v;
            b = t;
            break;

        case 3:
            r = p;
            g = q;
            b = v;
            break;

        case 4:
            r = t;
            g = p;
            b = v;
            break;

        default: // case 5:
            r = v;
            g = p;
            b = q;
    }

    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}


