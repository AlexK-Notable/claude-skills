# Module Structure Reference

Complete file templates for ZMK animation module.

---

## Table of Contents

1. [Directory Layout](#directory-layout)
2. [zephyr/module.yml](#zephyrmoduleyml)
3. [Kconfig](#kconfig)
4. [CMakeLists.txt](#cmakeliststxt)

---

## Directory Layout

```
your-animation-module/
├── zephyr/
│   └── module.yml          # Zephyr module registration
├── src/
│   └── status_screen.c     # LVGL widget implementation
├── Kconfig                  # Kconfig options (can be empty)
├── CMakeLists.txt           # Build integration
├── native_sim.conf          # Display configuration
└── native_sim.keymap        # Mock keyboard overlay
```

---

## zephyr/module.yml

```yaml
# Required: Registers this directory as a Zephyr module
name: zmk-animation-widget

build:
  cmake: .
  kconfig: Kconfig
```

**Purpose:** This file tells Zephyr's build system that this directory contains a module. Without it, your CMakeLists.txt won't be processed.

**Location:** Must be in a `zephyr/` subdirectory.

### ⚠️ CRITICAL: Path Resolution

**Paths in module.yml are relative to the MODULE ROOT, NOT the zephyr/ directory!**

```
your-module/           ← MODULE ROOT (paths resolve from here)
├── zephyr/
│   └── module.yml     ← This file
├── Kconfig            ← cmake: . and kconfig: Kconfig point HERE
├── CMakeLists.txt
└── src/
```

| Setting | Value | Resolves To |
|---------|-------|-------------|
| `cmake: .` | module root | `your-module/` |
| `kconfig: Kconfig` | module root | `your-module/Kconfig` |

**WRONG (common mistake):**
```yaml
# DON'T DO THIS - paths are NOT relative to zephyr/ dir
build:
  cmake: ..           # WRONG
  kconfig: ../Kconfig # WRONG
```

**Error you'll see if wrong:**
```
ERROR: "kconfig" key in .../module.yml has value "../Kconfig"
which does not point to a valid Kconfig file
```

---

## Kconfig

```kconfig
# SPDX-License-Identifier: MIT
# Kconfig for animation widget
#
# This module uses CONFIG_ZMK_DISPLAY_STATUS_SCREEN_CUSTOM
# which is defined by ZMK. No additional options needed.
```

**Purpose:** Required by the module system even if you don't define custom options.

**Note:** You could add custom options here:

```kconfig
config MY_ANIMATION_SPEED_MS
    int "Animation frame interval in milliseconds"
    default 150
    help
      Controls how fast the animation plays.
```

Then use in C: `CONFIG_MY_ANIMATION_SPEED_MS`

---

## CMakeLists.txt

```cmake
# SPDX-License-Identifier: MIT

# Only compile when custom status screen is enabled
if(CONFIG_ZMK_DISPLAY AND CONFIG_ZMK_DISPLAY_STATUS_SCREEN_CUSTOM)
    # Add the status screen source
    target_sources(app PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src/status_screen.c
    )

    # Optional: Add include directories
    # target_include_directories(app PRIVATE
    #     ${CMAKE_CURRENT_SOURCE_DIR}/include
    # )
endif()
```

**Key Points:**

1. **Conditional compilation:** Only builds when display is enabled
2. **Target name:** Must use `app` - this is ZMK's application target
3. **Source path:** Use `${CMAKE_CURRENT_SOURCE_DIR}` for full path
4. **PRIVATE visibility:** Sources are only for this target

---

## Alternative: Multiple Source Files

```cmake
if(CONFIG_ZMK_DISPLAY AND CONFIG_ZMK_DISPLAY_STATUS_SCREEN_CUSTOM)
    target_sources(app PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src/status_screen.c
        ${CMAKE_CURRENT_SOURCE_DIR}/src/animation_data.c
        ${CMAKE_CURRENT_SOURCE_DIR}/src/frame_decoder.c
    )
endif()
```

---

## Alternative: Header-Only Animation Data

If you want animation frames in a header:

```cmake
if(CONFIG_ZMK_DISPLAY AND CONFIG_ZMK_DISPLAY_STATUS_SCREEN_CUSTOM)
    target_sources(app PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src/status_screen.c
    )
    target_include_directories(app PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
    )
endif()
```

Then create `include/animation_frames.h`:

```c
#pragma once

#define FRAME_WIDTH 72
#define FRAME_HEIGHT 32
#define NUM_FRAMES 6

static const uint8_t frames[NUM_FRAMES][288] = {
    { /* frame data */ },
    // ...
};
```
