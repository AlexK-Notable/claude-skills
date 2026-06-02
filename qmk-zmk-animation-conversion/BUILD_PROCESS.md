# Build Process Reference

Complete build commands, environment setup, and error resolution.

---

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Build Command](#build-command)
3. [Build Parameters](#build-parameters)
4. [Common Build Errors](#common-build-errors)
5. [Runtime Errors](#runtime-errors)
6. [Debugging with Coredump](#debugging-with-coredump)
7. [Incremental Builds](#incremental-builds)

---

## Environment Setup

### 1. Navigate to Workspace

```bash
cd /path/to/zmk-workspace
```

### 2. CMAKE_PREFIX_PATH (CRITICAL)

**Do NOT export CMAKE_PREFIX_PATH.** Pass it as a `-D` argument to west build.

The `west` command (when installed via pipx) doesn't reliably pass environment variables to cmake subprocesses.

```bash
# WRONG - doesn't work reliably
export CMAKE_PREFIX_PATH=$(pwd)/zephyr/share/zephyr-package/cmake

# CORRECT - pass as cmake argument
west build ... -DCMAKE_PREFIX_PATH=$(pwd)/zephyr/share/zephyr-package/cmake
```

### 3. Update Zephyr (if needed)

```bash
west update zephyr
```

**When:** If you get "Could not find Zephyr" errors even with CMAKE_PREFIX_PATH.

---

## Build Command

### Full Command (Tested Working)

```bash
# IMPORTANT: Remove old build dir first to avoid pristine errors
rm -rf build/your-animation

west build -b native_sim/native/64 zmk.git/app \
  -DCMAKE_PREFIX_PATH=$(pwd)/zephyr/share/zephyr-package/cmake \
  -DEXTRA_CONF_FILE="/absolute/path/to/native_sim.conf" \
  -DEXTRA_DTC_OVERLAY_FILE="/absolute/path/to/native_sim.keymap" \
  -DZEPHYR_EXTRA_MODULES="$(pwd)/zmk.git/app/module;/absolute/path/to/your-module" \
  -d build/your-animation
```

### Single Line (Copy-Paste Ready)

```bash
rm -rf build/anim && west build -b native_sim/native/64 zmk.git/app -DCMAKE_PREFIX_PATH=$(pwd)/zephyr/share/zephyr-package/cmake -DEXTRA_CONF_FILE="/path/to/native_sim.conf" -DEXTRA_DTC_OVERLAY_FILE="/path/to/native_sim.keymap" -DZEPHYR_EXTRA_MODULES="$(pwd)/zmk.git/app/module;/path/to/your-module" -d build/anim
```

### Why Not Use `-p` (Pristine)?

The `-p` flag can fail with cryptic errors when the build directory doesn't exist yet or has stale metadata. Removing the build directory manually is more reliable.

---

## Build Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `-s` | `zmk.git/app` | Source directory (ZMK application) |
| `-b` | `native_sim/native/64` | Board target (64-bit native simulator) |
| `-d` | `build/native` | Build output directory |
| `-p` | (no value) | Pristine build (clean first) |
| `--` | (separator) | CMake arguments follow |

### CMake Arguments

| Argument | Purpose |
|----------|---------|
| `EXTRA_CONF_FILE` | Additional Kconfig file (your native_sim.conf) |
| `EXTRA_DTC_OVERLAY_FILE` | Device tree overlay (your native_sim.keymap) |
| `ZEPHYR_EXTRA_MODULES` | Semicolon-separated module paths |

### Module Paths (CRITICAL)

You must include BOTH:

1. **ZMK's module:** Provides `kscan_mock.h` and other ZMK-specific headers
   ```
   /path/to/zmk.git/app/module
   ```

2. **Your module:** Your custom status screen
   ```
   /path/to/your-animation-module
   ```

**Format:** Use semicolon separator and quote the entire value:
```bash
"-DZEPHYR_EXTRA_MODULES=/path1;/path2"
```

---

## Common Build Errors

### Error: Could not find Zephyr

```
CMake Error: Could not find a package configuration file provided by "Zephyr"
```

**Cause:** CMAKE_PREFIX_PATH not set or Zephyr not installed.

**Fix:**
```bash
export CMAKE_PREFIX_PATH=$(pwd)/zephyr/share/zephyr-package/cmake
# Or if Zephyr is missing:
west update zephyr
```

### Error: kscan_mock.h not found

```
fatal error: dt-bindings/zmk/kscan_mock.h: No such file or directory
```

**Cause:** ZMK module not in ZEPHYR_EXTRA_MODULES.

**Fix:** Add ZMK module path:
```bash
"-DZEPHYR_EXTRA_MODULES=/path/to/zmk.git/app/module;/path/to/your-module"
```

### Error: undefined node label 'kscan'

```
devicetree error: undefined node label 'kscan'
```

**Cause:** Keymap references `&kscan` but native_sim doesn't define it.

**Fix:** Define your own kscan node in keymap:
```dts
/ {
    kscan0: kscan_mock {
        compatible = "zmk,kscan-mock";
        columns = <2>;
        rows = <2>;
        events = <ZMK_MOCK_PRESS(0,0,10000) ZMK_MOCK_RELEASE(0,0,10000)>;
    };
    chosen { zmk,kscan = &kscan0; };
};
```

### Error: DTS parse error

```
parse error: syntax error
```

**Cause:** Invalid device tree syntax in keymap.

**Fix:** Check:
- Semicolons at end of properties
- Angle brackets for arrays: `events = < ... >;`
- Curly braces for nodes
- Proper includes at top

### Error: Source directory does not exist

```
ERROR: source directory zmk/app does not exist
```

**Cause:** Wrong ZMK path.

**Fix:** Check your directory structure:
```bash
ls -la  # Look for zmk.git/ or zmk/
# Use the correct path: zmk.git/app or zmk/app
```

### Error: Invalid Kconfig symbol

```
warning: SOME_CONFIG is not a valid Kconfig symbol
```

**Cause:** Using Kconfig option that doesn't exist in this version.

**Fix:** Remove or replace the invalid option. Check ZMK/Zephyr docs for current options.

---

## Runtime Errors

### Crash: lv_theme_default_init

**Stack trace:**
```
#0 lv_theme_default_init
#1 lv_display_create
#2 lvgl_init
```

**Cause:** LVGL memory pool too small for theme allocation.

**Fix:**
```kconfig
CONFIG_LV_Z_MEM_POOL_SIZE=16384
```

### Crash: lv_obj_remove_style

**Stack trace:**
```
#0 lv_obj_remove_style
#1 lv_display_create
```

**Cause:** LVGL minimal mode enabled, styles not available.

**Fix:**
```kconfig
CONFIG_LV_CONF_MINIMAL=n
```

### No SDL Window Appears

**Cause:** SDL display not enabled or wrong board.

**Fix:**
```kconfig
CONFIG_SDL_DISPLAY=y
```

And ensure using `native_sim/native/64` board.

### Black Screen (No Animation)

**Cause:** Color format mismatch between canvas and display.

**Fix:** Match formats:

| Kconfig | Canvas Format |
|---------|---------------|
| `CONFIG_LV_COLOR_DEPTH_16=y` | `LV_COLOR_FORMAT_RGB565` |
| `CONFIG_LV_COLOR_DEPTH_32=y` | `LV_COLOR_FORMAT_ARGB8888` |

---

## Debugging with Coredump

### Check Latest Crash

```bash
coredumpctl info -1
```

### Key Information

Look for:
- **Signal:** 11 (SEGV) = segmentation fault
- **Stack trace:** Shows crash location

### Common Crash Patterns

| Crash Location | Likely Cause |
|----------------|--------------|
| `lv_theme_*` | Memory pool too small |
| `lv_obj_remove_style` | Minimal mode enabled |
| `lv_canvas_*` | Buffer size wrong or format mismatch |
| `memset` or memory functions | Buffer overflow |

### Debug Build

Add to conf:
```kconfig
CONFIG_DEBUG=y
CONFIG_DEBUG_INFO=y
```

Then check with:
```bash
coredumpctl debug -1
# In GDB:
bt      # Backtrace
frame 0 # Select frame
info locals  # See variables
```

---

## Incremental Builds

### Without Pristine

Remove `-p` for incremental build:
```bash
west build -s zmk.git/app -b native_sim/native/64 -d build/native -- ...
```

### When to Use Pristine

Use `-p` (pristine) when:
- Changing Kconfig options
- Modifying device tree/keymap
- Adding/removing source files
- After git checkout/merge

### Rebuild Just Your File

```bash
cd build/native
ninja
```

This only recompiles changed files.

---

## Running the Emulator

### Basic Run

```bash
./build/native/zephyr/zmk.exe
```

### With Timeout

```bash
timeout 30 ./build/native/zephyr/zmk.exe
```

### Background Run

```bash
./build/native/zephyr/zmk.exe &
ZMK_PID=$!
# Do stuff...
kill $ZMK_PID
```

### Check If Running

```bash
pgrep -a zmk.exe
```

### Expected Output

```
*** Booting Zephyr OS build XXXXXXX ***
[00:00:00.000,000] <dbg> zmk: ...
[00:00:00.000,000] <inf> zmk: Welcome to ZMK!
[00:00:00.000,000] <inf> zmk: Animation started with N frames
```

If you see "Animation started", the widget is working.
