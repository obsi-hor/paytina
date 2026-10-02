#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def _gps_to_decimal(coords, ref):
    try:
        d = float(coords[0])
        m = float(coords[1])
        s = float(coords[2])
        result = d + (m / 60.0) + (s / 3600.0)
        if ref in ["S", "W"]:
            result = -result
        return round(result, 6)
    except Exception:
        return 0


def get_exif(image_bytes):
    r = {"valid": False, "has_exif": False, "info": {}, "coords": None, "maps": None, "error": None}
    try:
        img = Image.open(io.BytesIO(image_bytes))
        exifdata = img.getexif()
        r["valid"] = True
        if not exifdata:
            return r
        r["has_exif"] = True
        for tag_id, value in exifdata.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag in ["Make", "Model", "Software", "DateTime", "DateTimeOriginal"]:
                r["info"][tag] = str(value)
        try:
            gps_ifd = exifdata.get_ifd(0x8825)
            if gps_ifd:
                gps_data = {}
                for tag_id, value in gps_ifd.items():
                    gps_data[GPSTAGS.get(tag_id, tag_id)] = value
                if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
                    lat = _gps_to_decimal(gps_data["GPSLatitude"], gps_data.get("GPSLatitudeRef", "N"))
                    lon = _gps_to_decimal(gps_data["GPSLongitude"], gps_data.get("GPSLongitudeRef", "E"))
                    r["coords"] = (lat, lon)
                    r["maps"] = "https://www.google.com/maps/place/" + str(lat) + "," + str(lon)
        except Exception:
            pass
    except Exception as e:
        r["error"] = str(e)[:80]
    return r
