# Animation Formats Reference

Guide to QMK animation format categories and conversion strategies.

---

## Table of Contents

1. [Format Categories](#format-categories)
2. [Standard Column-Major](#standard-column-major)
3. [Rotated Format (270°)](#rotated-format-270)
4. [State-Based Animations](#state-based-animations)
5. [Frame Size Calculation](#frame-size-calculation)
6. [Known Animation Sources](#known-animation-sources)

---

## Format Categories

| Category | OLED Rotation | Conversion | Complexity |
|----------|---------------|------------|------------|
| Standard | 0°, 180° | Direct decode | Easy ✅ |
| Rotated | 270° | Coordinate swap | Medium ⚠️ |
| State-based | Any | ZMK events | Hard ❌ |

**How to identify format:** Look for `oled_init_user()` function:

```c
// Standard format
oled_rotation_t oled_init_user(oled_rotation_t rotation) {
    return OLED_ROTATION_180;  // or OLED_ROTATION_0
}

// Rotated format - needs transformation
oled_rotation_t oled_init_user(oled_rotation_t rotation) {
    return OLED_ROTATION_270;  // REQUIRES COORDINATE TRANSFORMATION
}
```

---

## Standard Column-Major

**Used by:** Most animations, especially full-width 128x32 displays

### Decoding Algorithm

```c
// Standard column-major: columns first, then pages
// Each byte = 8 vertical pixels, LSB = top
for (int page = 0; page < height/8; page++) {
    for (int x = 0; x < width; x++) {
        uint8_t col_byte = frame[page * width + x];
        for (int bit = 0; bit < 8; bit++) {
            if (col_byte & (1 << bit)) {
                int y = page * 8 + bit;
                lv_canvas_set_px(canvas, x, y, lv_color_white(), LV_OPA_COVER);
            }
        }
    }
}
```

### Verified Working Examples

| Animation | Dimensions | Frames | Source |
|-----------|------------|--------|--------|
| demon | 32x36 | 8 | marekpiechut |
| music-bars | 128x32 | 5 | marekpiechut |
| crab | 72x32 | 6 | marekpiechut |

---

## Rotated Format (270°)

**Used by:** Vertical/portrait OLED displays (common on split keyboards)

### Identifying Features

- Comment mentions: "Image MUST be converted to VERTICAL on image2cpp"
- Uses `OLED_ROTATION_270`
- Often used with luna, bongocat variants

### Conversion Strategy (UNTESTED)

When QMK uses `OLED_ROTATION_270`, the frame data is stored in a rotated coordinate system. The transformation needed:

```c
// THEORETICAL - needs validation
// For OLED_ROTATION_270: swap coordinates
for (int page = 0; page < width/8; page++) {  // Note: width, not height
    for (int y = 0; y < height; y++) {
        uint8_t col_byte = frame[page * height + y];
        for (int bit = 0; bit < 8; bit++) {
            if (col_byte & (1 << bit)) {
                int x = page * 8 + bit;
                // May need: x = width - 1 - x; (flip)
                lv_canvas_set_px(canvas, x, y, lv_color_white(), LV_OPA_COVER);
            }
        }
    }
}
```

### Known Rotated Format Animations

| Source | Animation | Notes |
|--------|-----------|-------|
| hexcowboy-superloop | animation.c | OLED_ROTATION_270 |
| whoop-t-collection | luffy-wanted | "VERTICAL on image2cpp" |
| whoop-t-collection | one-punch | "VERTICAL on image2cpp" |
| whoop-t-collection | fry-sus | "VERTICAL on image2cpp" |
| filterpaper | oled_luna | "oriented for OLED_ROTATION_270" |
| filterpaper | oled_bongocat | Conditional rotation |

---

## State-Based Animations

**Used by:** Interactive animations that react to keyboard state

### Common State Types

| State | QMK API | ZMK Equivalent |
|-------|---------|----------------|
| WPM | `get_current_wpm()` | TBD (ZMK WPM module) |
| Caps Lock | `host_keyboard_led_state().caps_lock` | ZMK HID indicators |
| Layer | `get_highest_layer()` | `zmk_keymap_highest_layer_active()` |
| Key press | QMK callback | ZMK event system |

### Conversion Complexity

State-based animations require:
1. Understanding ZMK's event system
2. Mapping QMK state APIs to ZMK
3. Potentially writing ZMK modules
4. More complex widget logic with callbacks

**Recommendation:** Start with static animations first. State-based conversions are advanced.

---

## Frame Size Calculation

### Formula

```
frame_size = width × ceil(height / 8) bytes
```

### Common Sizes

| Dimensions | Pages | Frame Size |
|------------|-------|------------|
| 128x32 | 4 | 512 bytes |
| 128x64 | 8 | 1024 bytes |
| 72x32 | 4 | 288 bytes |
| 32x32 | 4 | 128 bytes |
| 32x36 | 5 | 160 bytes |

### ⚠️ ANIM_SIZE Discrepancy

**QMK sources often declare WRONG `ANIM_SIZE`!**

| File | Declared | Actual | Calculation |
|------|----------|--------|-------------|
| demon.c | 144 | 160 | 32 × ceil(36/8) = 32 × 5 = 160 |

**Always verify by counting actual array bytes.**

---

## Known Animation Sources

### marekpiechut-animations (Standard Format)
- demon.c - 32x36, 8 frames ✅ Converted
- music-bars.c - 128x32, 5 frames ✅ Converted
- crab.c - 72x32, 6 frames ✅ Converted

### filterpaper-oled-animations (Mixed)
- oled_luna.c - Rotated format, state-based
- oled_bongocat.c - Rotated format, state-based

### whoop-t-oled-collection (Rotated)
- luffy-wanted - 128x32, rotated
- one-punch - 128x32, rotated
- fry-sus - 128x32, rotated

### hexcowboy-superloop (Rotated)
- animation.c - Rotated format

### bongocat variants (State-based)
- Multiple sources with key-reactive animations

---

## Conversion Priority

1. **Easy:** Standard format (0°/180°) - direct decode
2. **Medium:** Rotated format (270°) - needs coordinate transformation
3. **Hard:** State-based - needs ZMK event integration

**Start with standard format animations to validate the pipeline, then tackle rotation.**
