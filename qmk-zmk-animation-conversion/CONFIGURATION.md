# Configuration Reference

Complete Kconfig options for ZMK display with LVGL.

---

## Table of Contents

1. [Minimum Required Configuration](#minimum-required-configuration)
2. [Display Subsystem](#display-subsystem)
3. [LVGL Settings](#lvgl-settings)
4. [SDL Display](#sdl-display)
5. [Memory Settings](#memory-settings)
6. [ZMK Options](#zmk-options)
7. [Debugging](#debugging)
8. [Keymap Configuration](#keymap-configuration)

---

## Minimum Required Configuration

```kconfig
# === REQUIRED ===
CONFIG_ZMK_DISPLAY=y
CONFIG_DISPLAY=y
CONFIG_SDL_DISPLAY=y
CONFIG_LVGL=y
CONFIG_ZMK_DISPLAY_STATUS_SCREEN_CUSTOM=y

# === CRITICAL - PREVENTS CRASHES ===
CONFIG_LV_Z_MEM_POOL_SIZE=16384
CONFIG_LV_CONF_MINIMAL=n

# === COLOR FORMAT - MUST MATCH ===
CONFIG_LV_COLOR_DEPTH_16=y
CONFIG_SDL_DISPLAY_DEFAULT_PIXEL_FORMAT_RGB_565=y

# === CANVAS SUPPORT ===
CONFIG_LV_USE_CANVAS=y

# === DISABLE UNUSED ===
CONFIG_ZMK_USB=n
CONFIG_ZMK_BLE=n
```

---

## Display Subsystem

```kconfig
# Enable Zephyr display driver subsystem
CONFIG_DISPLAY=y

# Enable ZMK display integration
CONFIG_ZMK_DISPLAY=y

# Use custom status screen (your widget)
CONFIG_ZMK_DISPLAY_STATUS_SCREEN_CUSTOM=y

# Alternative: Use built-in ZMK status screen
# CONFIG_ZMK_DISPLAY_STATUS_SCREEN_BUILT_IN=y
```

---

## LVGL Settings

### Memory Pool (CRITICAL)

```kconfig
# LVGL memory pool for Zephyr integration
# DEFAULT: 2048 - TOO SMALL, CAUSES CRASHES
# MINIMUM: 8192 for basic use
# RECOMMENDED: 16384 for animations
CONFIG_LV_Z_MEM_POOL_SIZE=16384

# Internal LVGL memory (separate from Z pool)
CONFIG_LV_MEM_SIZE_KILOBYTES=64
```

### Color Depth

```kconfig
# Choose ONE color depth:
CONFIG_LV_COLOR_DEPTH_1=y    # 1-bit monochrome (NOT for SDL)
CONFIG_LV_COLOR_DEPTH_8=y    # 8-bit grayscale
CONFIG_LV_COLOR_DEPTH_16=y   # 16-bit RGB565 (RECOMMENDED for SDL)
CONFIG_LV_COLOR_DEPTH_32=y   # 32-bit ARGB8888
```

### Canvas Support

```kconfig
# Enable canvas widget (required for frame rendering)
CONFIG_LV_USE_CANVAS=y
```

### Minimal Mode

```kconfig
# Disable minimal mode - required for theme system
# DEFAULT: y in some configs
# REQUIRED: n for proper initialization
CONFIG_LV_CONF_MINIMAL=n
```

### Fonts

```kconfig
# Include fonts if using text
CONFIG_LV_FONT_MONTSERRAT_12=y
CONFIG_LV_FONT_MONTSERRAT_14=y

# Set default font
CONFIG_LV_FONT_DEFAULT_MONTSERRAT_14=y
```

### Timing

```kconfig
# Display refresh period (ms)
CONFIG_LV_DEF_REFR_PERIOD=33   # ~30 FPS

# DPI setting
CONFIG_LV_DPI_DEF=130
```

### VDB (Virtual Display Buffer)

```kconfig
# VDB size as percentage of display
CONFIG_LV_Z_VDB_SIZE=100       # Full buffer (recommended)
# CONFIG_LV_Z_VDB_SIZE=50      # Half buffer (saves RAM)
# CONFIG_LV_Z_VDB_SIZE=10      # Small buffer (saves more RAM)
```

---

## SDL Display

```kconfig
# Enable SDL display driver
CONFIG_SDL_DISPLAY=y

# Pixel format - MUST MATCH LV_COLOR_DEPTH
CONFIG_SDL_DISPLAY_DEFAULT_PIXEL_FORMAT_RGB_565=y      # For 16-bit
# CONFIG_SDL_DISPLAY_DEFAULT_PIXEL_FORMAT_ARGB_8888=y  # For 32-bit
# CONFIG_SDL_DISPLAY_DEFAULT_PIXEL_FORMAT_MONO01=y    # For 1-bit

# SDL thread settings
CONFIG_SDL_THREAD_INTERVAL=10    # Thread sleep interval (ms)
CONFIG_SDL_THREAD_PRIORITY=0     # Thread priority
```

---

## Memory Settings

```kconfig
# Main thread stack size
CONFIG_MAIN_STACK_SIZE=4096

# Heap memory pool (for dynamic allocation)
CONFIG_HEAP_MEM_POOL_SIZE=0      # 0 = disabled

# Kernel memory pool
CONFIG_KERNEL_MEM_POOL=y
```

---

## ZMK Options

```kconfig
# Disable USB (not available in native_sim)
CONFIG_ZMK_USB=n

# Disable BLE (not available in native_sim)
CONFIG_ZMK_BLE=n

# Display work queue (optional)
# CONFIG_ZMK_DISPLAY_WORK_QUEUE_DEDICATED=y
# CONFIG_ZMK_DISPLAY_DEDICATED_THREAD_STACK_SIZE=2048

# Display tick period
CONFIG_ZMK_DISPLAY_TICK_PERIOD_MS=33
```

---

## Debugging

```kconfig
# Enable logging
CONFIG_LOG=y
CONFIG_LOG_BACKEND_SHOW_COLOR=n   # Better for terminal capture

# ZMK log level
CONFIG_ZMK_LOG_LEVEL_DBG=y        # Debug level
# CONFIG_ZMK_LOG_LEVEL_INF=y      # Info level
# CONFIG_ZMK_LOG_LEVEL_WRN=y      # Warning level
# CONFIG_ZMK_LOG_LEVEL_ERR=y      # Error level

# LVGL logging
CONFIG_LV_USE_LOG=y
CONFIG_LV_LOG_LEVEL=2             # 0=none, 1=error, 2=warn, 3=info, 4=trace
```

---

## Keymap Configuration

The keymap (`.keymap` file) uses Device Tree syntax:

### Display Size

```dts
/* Configure SDL display dimensions */
&sdl_dc {
    height = <32>;    /* Pixels */
    width = <128>;    /* Pixels */
};
```

### Mock Keyboard

```dts
/ {
    kscan0: kscan_mock {
        compatible = "zmk,kscan-mock";
        columns = <2>;
        rows = <2>;
        /* Events: action, row, col, delay_ms */
        events = <
            ZMK_MOCK_PRESS(0,0,10000)    /* Press after 10s */
            ZMK_MOCK_RELEASE(0,0,10000)  /* Release after 10s */
        >;
    };

    chosen {
        zmk,kscan = &kscan0;
    };
};
```

### Full Keymap Template

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
        default_layer {
            bindings = <&kp A &kp B &kp C &kp D>;
        };
    };
};

&sdl_dc {
    height = <32>;
    width = <128>;
};
```

---

## Color Format Matching Table

| Use Case | LV_COLOR_DEPTH | Canvas Format | SDL Format |
|----------|----------------|---------------|------------|
| Standard SDL | `_16` | `RGB565` | `RGB_565` |
| High color | `_32` | `ARGB8888` | `ARGB_8888` |
| Monochrome | `_1` | `I1` | `MONO01` |
