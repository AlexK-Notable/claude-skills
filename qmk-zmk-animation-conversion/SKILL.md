---
name: qmk-zmk-animation-conversion
description: Converting QMK OLED animations to ZMK LVGL widgets. Use when porting keyboard animations from QMK to ZMK, creating ZMK display widgets, working with LVGL canvas, converting column-major frame data, building native_sim test environments, ANIM_SIZE calculation, OLED_ROTATION formats, or batch animation conversion.
---

# QMK to ZMK Animation Conversion

## Purpose

Guide for converting QMK OLED animations (column-major SSD1306 format) to ZMK LVGL canvas widgets, with native simulation testing.

## When to Use

- Converting QMK keyboard animations to ZMK
- Creating custom ZMK display widgets
- Working with LVGL canvas in ZMK
- Setting up native_sim display testing
- Debugging ZMK display crashes
- Understanding QMK frame format
- Batch converting animation collections

## Verified Working Conversions

| Animation | Dimensions | Frames | Format | Source |
|-----------|------------|--------|--------|--------|
| demon | 32x40* | 8 | Canvas | marekpiechut |
| music-bars | 128x32 | 5 | Canvas | marekpiechut |
| crab | 72x32 | 12 | lv_img_dsc_t | marekpiechut |

*\*Demon original is 32x36, but FRAME_HEIGHT=40 (rounded to nearest 8) for proper page alignment.*

**⚠️ Crab uses a different format** (`lv_img_dsc_t` with `LV_IMG_CF_ALPHA_1BIT`) and only has a `frames.c` file - no status_screen.c or config files. It's designed to be included by a parent application, not run standalone.

---

## Quick Start Checklist

### Required Files (6 total)

```
your-module/
├── zephyr/module.yml     # Zephyr module registration
├── Kconfig               # Empty or minimal
├── CMakeLists.txt        # Build rules
├── native_sim.conf       # Kconfig overrides (CRITICAL)
├── native_sim.keymap     # Mock keyboard + display size
└── src/status_screen.c   # LVGL widget with animation
```

### Critical Configuration (prevents crashes)

```kconfig
# Memory - TOO SMALL CAUSES CRASH
CONFIG_LV_Z_MEM_POOL_SIZE=16384

# Must disable minimal mode
CONFIG_LV_CONF_MINIMAL=n

# Color formats MUST MATCH
CONFIG_LV_COLOR_DEPTH_16=y
CONFIG_SDL_DISPLAY_DEFAULT_PIXEL_FORMAT_RGB_565=y
```

### Build Command Template

```bash
cd zmk-workspace

# Remove old build directory first (avoids pristine errors)
rm -rf build/your-animation

west build -b native_sim/native/64 zmk.git/app \
  -DCMAKE_PREFIX_PATH=$(pwd)/zephyr/share/zephyr-package/cmake \
  -DEXTRA_CONF_FILE=/path/to/native_sim.conf \
  -DEXTRA_DTC_OVERLAY_FILE=/path/to/native_sim.keymap \
  -DZEPHYR_EXTRA_MODULES="$(pwd)/zmk.git/app/module;/path/to/your-module" \
  -d build/your-animation
```

**Critical:** `CMAKE_PREFIX_PATH` must be passed as a `-D` argument, not exported.

---

## Frame Format Conversion

### ⚠️ ANIM_SIZE Discrepancy Warning

**QMK sources often declare WRONG `ANIM_SIZE` values!** Always calculate:

```
actual_frame_size = width × ceil(height / 8)
```

| Example | Declared | Actual | Issue |
|---------|----------|--------|-------|
| demon.c | `ANIM_SIZE=144` | 160 | 32×5=160, not 144 |

**Always count actual bytes in frame arrays, not declared constants.**

### Frame Height Rounding

When height isn't a multiple of 8, round UP to the nearest multiple:

| Original | Buffer Height | Pages | Why |
|----------|---------------|-------|-----|
| 32x36 | 40 | 5 | 36→40 (5 pages of 8 pixels) |
| 32x28 | 32 | 4 | 28→32 (4 pages) |

In code, use the rounded height for buffer allocation but limit rendering:
```c
#define FRAME_HEIGHT 40  // Buffer size (rounded)
// In draw_frame():
if (y >= 36) break;  // Only render actual 36 rows
```

### QMK Column-Major Format (Standard)

```
72x32 pixel frame = 288 bytes

Layout:
  bytes 0-71:    columns 0-71, rows 0-7   (page 0)
  bytes 72-143:  columns 0-71, rows 8-15  (page 1)
  bytes 144-215: columns 0-71, rows 16-23 (page 2)
  bytes 216-287: columns 0-71, rows 24-31 (page 3)

Each byte = 8 vertical pixels:
  bit 0 (LSB) = top pixel
  bit 7 (MSB) = bottom pixel
```

### Animation Format Categories

| Category | Rotation | Conversion | Examples |
|----------|----------|------------|----------|
| **Standard** | 0°, 180° | Direct decode | demon, music-bars, crab |
| **Rotated** | 270° | Needs transformation | luna, bongocat, whoop-t |
| **State-based** | varies | Needs ZMK events | WPM-reactive animations |

See [ANIMATION_FORMATS.md](ANIMATION_FORMATS.md) for rotation handling.

### Alternative LVGL Rendering Methods

The canvas-based approach (documented here) is one of two methods:

| Method | Use Case | Complexity |
|--------|----------|------------|
| **Canvas** (`lv_canvas_set_px`) | Runtime decoding, flexible | Medium |
| **lv_img_dsc_t** | Pre-converted images, efficient | Lower |

**lv_img_dsc_t approach** (used by crab):
```c
const lv_img_dsc_t frame = {
    .header.cf = LV_IMG_CF_ALPHA_1BIT,  // or LV_IMG_CF_INDEXED_1BIT
    .header.w = 72,
    .header.h = 32,
    .data_size = 288,
    .data = frame_data,
};
// Use with lv_img_set_src() or lv_animimg widget
```

**For `LV_IMG_CF_INDEXED_1BIT`**, prepend 8-byte palette:
```c
const uint8_t image_map[] = {
    0x00, 0x00, 0x00, 0xff,  // Color 0: Black (RGBA)
    0xff, 0xff, 0xff, 0xff,  // Color 1: White (RGBA)
    // ... pixel data follows
};
```

### RLE Compression (Some QMK Sources)

Some animations (especially filterpaper's) use RLE compression. First byte = total size:
- If count < 0x80: repeat next byte `count` times
- If count >= 0x80: next `(count & 0x7F)` bytes are unique

**Detect RLE:** If first byte is smaller than expected raw frame size, it's likely RLE.

See toolkit `docs/frame-formats.md` for full RLE decompression algorithm.

### Conversion Code (Canvas Method)

```c
static void draw_frame(uint8_t frame_idx) {
    const uint8_t *frame = frames[frame_idx];
    lv_canvas_fill_bg(canvas, lv_color_black(), LV_OPA_COVER);

    for (int col = 0; col < FRAME_WIDTH; col++) {
        for (int page = 0; page < (FRAME_HEIGHT / 8); page++) {
            uint8_t byte = frame[col + page * FRAME_WIDTH];
            for (int bit = 0; bit < 8; bit++) {
                if (byte & (1 << bit)) {
                    lv_canvas_set_px(canvas, col, page * 8 + bit,
                                     lv_color_white(), LV_OPA_COVER);
                }
            }
        }
    }
    lv_obj_invalidate(canvas);
}
```

---

## Troubleshooting Decision Tree

```
Build fails?
├── "Could not find Zephyr"
│   └── Set CMAKE_PREFIX_PATH or: west update zephyr
├── "kscan_mock.h not found"
│   └── Add zmk.git/app/module to ZEPHYR_EXTRA_MODULES
├── "undefined node label 'kscan'"
│   └── Define own kscan_mock node (don't reference &kscan)
└── DTS parse error
    └── Check keymap syntax

Runtime crash?
├── lv_theme_default_init crash
│   └── CONFIG_LV_Z_MEM_POOL_SIZE=16384 (increase!)
├── lv_obj_remove_style crash
│   └── CONFIG_LV_CONF_MINIMAL=n
├── No SDL window
│   └── CONFIG_SDL_DISPLAY=y
└── Black screen
    └── Match canvas format to color depth:
        16-bit → LV_COLOR_FORMAT_RGB565
        32-bit → LV_COLOR_FORMAT_ARGB8888
```

---

## Step-by-Step Operations

See reference files for complete details:

| Reference | Content |
|-----------|---------|
| [MODULE_STRUCTURE.md](MODULE_STRUCTURE.md) | Complete file templates |
| [CONFIGURATION.md](CONFIGURATION.md) | All Kconfig options explained |
| [STATUS_SCREEN_TEMPLATE.md](STATUS_SCREEN_TEMPLATE.md) | Full C code template |
| [BUILD_PROCESS.md](BUILD_PROCESS.md) | Build commands and errors |

---

## Minimum Viable Configuration

### native_sim.conf

```kconfig
CONFIG_ZMK_DISPLAY=y
CONFIG_DISPLAY=y
CONFIG_SDL_DISPLAY=y
CONFIG_LVGL=y
CONFIG_ZMK_DISPLAY_STATUS_SCREEN_CUSTOM=y
CONFIG_LV_Z_MEM_POOL_SIZE=16384
CONFIG_LV_COLOR_DEPTH_16=y
CONFIG_LV_USE_CANVAS=y
CONFIG_LV_CONF_MINIMAL=n
CONFIG_SDL_DISPLAY_DEFAULT_PIXEL_FORMAT_RGB_565=y
CONFIG_ZMK_USB=n
CONFIG_ZMK_BLE=n
```

### native_sim.keymap

```dts
#include <behaviors.dtsi>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/kscan_mock.h>

/ {
    kscan0: kscan_mock {
        compatible = "zmk,kscan-mock";
        columns = <2>;
        rows = <2>;
        events = <
            ZMK_MOCK_PRESS(0,0,10000)
            ZMK_MOCK_RELEASE(0,0,10000)
        >;
    };
    chosen { zmk,kscan = &kscan0; };
    keymap {
        compatible = "zmk,keymap";
        default_layer { bindings = <&kp A &kp B &kp C &kp D>; };
    };
};

&sdl_dc { height = <32>; width = <128>; };
```

---

## Key Lessons Learned

### Memory Pool Size

The default `CONFIG_LV_Z_MEM_POOL_SIZE=2048` is too small for LVGL theme initialization. The theme system allocates styles, and if memory is insufficient, it crashes in `lv_theme_default_init`.

**Fix:** Always set `CONFIG_LV_Z_MEM_POOL_SIZE=16384` or higher.

### Color Format Matching

LVGL color depth and SDL pixel format must match exactly:

| LVGL Config | Canvas Format | SDL Format |
|-------------|---------------|------------|
| `LV_COLOR_DEPTH_16` | `LV_COLOR_FORMAT_RGB565` | `RGB_565` |
| `LV_COLOR_DEPTH_32` | `LV_COLOR_FORMAT_ARGB8888` | `ARGB_8888` |

Mismatches cause crashes or rendering issues.

### Buffer Size Calculation

Never manually calculate canvas buffer size. Always use:

```c
#define CANVAS_BUF_SIZE LV_CANVAS_BUF_SIZE(WIDTH, HEIGHT, \
    LV_COLOR_FORMAT_GET_BPP(FORMAT), LV_DRAW_BUF_STRIDE_ALIGN)
```

### LVGL API Usage

Use LVGL APIs, not direct memory operations:

```c
// WRONG - may crash
memset(canvas_buf, 0, size);

// CORRECT - uses LVGL internals properly
lv_canvas_fill_bg(canvas, lv_color_black(), LV_OPA_COVER);
```

### Module Registration

Both paths must be in `ZEPHYR_EXTRA_MODULES`:
1. ZMK's module: `zmk.git/app/module` (provides kscan_mock.h)
2. Your module: Your custom status screen

Use semicolon separator:
```bash
"-DZEPHYR_EXTRA_MODULES=/path/to/zmk/module;/path/to/your/module"
```

---

## Function Signature

ZMK requires this exact signature:

```c
lv_obj_t *zmk_display_status_screen(void);
```

This function is called during display initialization. Return the root screen object.

---

## Testing

```bash
# Run emulator
./build/native/zephyr/zmk.exe

# Check for crashes
coredumpctl info -1

# Verify animation log message
# Should see: "Animation started with N frames"
```

---

## Related Skills

- `gtk-pygobject-dev` - For GTK-based display development
- `obsidian-plugin-dev` - For TypeScript widget development

---

**Line Count**: ~250 (under 500-line limit)
