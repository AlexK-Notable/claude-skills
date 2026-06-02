# Status Screen Template

Complete C code template for ZMK LVGL animation widget.

---

## Table of Contents

1. [Complete Template](#complete-template)
2. [Section Breakdown](#section-breakdown)
3. [Customization Guide](#customization-guide)
4. [Multiple Animations](#multiple-animations)
5. [State-Based Animation](#state-based-animation)

---

## Complete Template

```c
/*
 * Custom ZMK Status Screen with Animation
 * SPDX-License-Identifier: MIT
 */

#include <zephyr/kernel.h>
#include <zmk/display/status_screen.h>
#include <lvgl.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

/* ============================================================
 * CONFIGURATION - Adjust these for your animation
 * ============================================================ */

#define FRAME_WIDTH 72          /* Animation width in pixels */
#define FRAME_HEIGHT 32         /* Animation height in pixels */
#define FRAME_SIZE (FRAME_WIDTH * (FRAME_HEIGHT / 8))  /* Bytes per frame */
#define NUM_FRAMES 6            /* Number of animation frames */
#define ANIMATION_INTERVAL_MS 150  /* Milliseconds between frames */

/* ============================================================
 * ANIMATION DATA - Paste your QMK frames here
 * ============================================================ */

static const uint8_t animation_frames[NUM_FRAMES][FRAME_SIZE] = {
    /* Frame 0 */
    {
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        /* ... paste all FRAME_SIZE bytes for frame 0 ... */
    },
    /* Frame 1 */
    {
        /* ... paste all FRAME_SIZE bytes for frame 1 ... */
    },
    /* ... repeat for all frames ... */
};

/* ============================================================
 * CANVAS SETUP - Match to your Kconfig color depth
 * ============================================================ */

/* For CONFIG_LV_COLOR_DEPTH_16=y */
#define CANVAS_COLOR_FORMAT LV_COLOR_FORMAT_RGB565

/* For CONFIG_LV_COLOR_DEPTH_32=y, use instead:
#define CANVAS_COLOR_FORMAT LV_COLOR_FORMAT_ARGB8888
*/

/* Buffer size with proper alignment - NEVER calculate manually */
#define CANVAS_BUF_SIZE LV_CANVAS_BUF_SIZE(FRAME_WIDTH, FRAME_HEIGHT, \
    LV_COLOR_FORMAT_GET_BPP(CANVAS_COLOR_FORMAT), LV_DRAW_BUF_STRIDE_ALIGN)

/* ============================================================
 * STATIC VARIABLES
 * ============================================================ */

static lv_obj_t *canvas;
static uint8_t canvas_buf[CANVAS_BUF_SIZE];
static uint8_t current_frame = 0;
static lv_timer_t *anim_timer;

/* ============================================================
 * FRAME RENDERING - Converts QMK format to LVGL pixels
 * ============================================================ */

/**
 * Draw a single frame to the canvas
 *
 * QMK column-major format:
 * - Each byte represents 8 vertical pixels
 * - Bit 0 (LSB) = top pixel of the 8
 * - Bytes arranged: columns first, then pages (8-row groups)
 *
 * @param frame_idx Index of frame to draw (0 to NUM_FRAMES-1)
 */
static void draw_frame(uint8_t frame_idx) {
    const uint8_t *frame = animation_frames[frame_idx];

    /* Clear canvas using LVGL API (not memset!) */
    lv_canvas_fill_bg(canvas, lv_color_black(), LV_OPA_COVER);

    /* Iterate through each column */
    for (int col = 0; col < FRAME_WIDTH; col++) {
        /* Iterate through each page (group of 8 vertical pixels) */
        for (int page = 0; page < (FRAME_HEIGHT / 8); page++) {
            /* Get the byte for this column and page */
            uint8_t byte = frame[col + page * FRAME_WIDTH];

            /* Extract each bit and set pixel if lit */
            for (int bit = 0; bit < 8; bit++) {
                int y = page * 8 + bit;
                if (byte & (1 << bit)) {
                    lv_canvas_set_px(canvas, col, y,
                                     lv_color_white(), LV_OPA_COVER);
                }
            }
        }
    }

    /* Trigger redraw */
    lv_obj_invalidate(canvas);
}

/* ============================================================
 * ANIMATION TIMER CALLBACK
 * ============================================================ */

/**
 * Called by LVGL timer to advance animation
 */
static void anim_timer_cb(lv_timer_t *timer) {
    current_frame = (current_frame + 1) % NUM_FRAMES;
    draw_frame(current_frame);
}

/* ============================================================
 * ZMK STATUS SCREEN ENTRY POINT
 * ============================================================ */

/**
 * Create the status screen
 *
 * This function is called by ZMK during display initialization.
 * The function signature must be exactly:
 *   lv_obj_t *zmk_display_status_screen(void)
 *
 * @return The root screen object
 */
lv_obj_t *zmk_display_status_screen(void) {
    /* Create root screen */
    lv_obj_t *screen = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(screen, lv_color_black(), LV_PART_MAIN);

    /* Create canvas for animation */
    canvas = lv_canvas_create(screen);
    lv_canvas_set_buffer(canvas, canvas_buf, FRAME_WIDTH, FRAME_HEIGHT,
                         CANVAS_COLOR_FORMAT);

    /* Center the animation on screen */
    lv_obj_align(canvas, LV_ALIGN_CENTER, 0, 0);

    /* Draw initial frame */
    draw_frame(0);

    /* Start animation timer */
    anim_timer = lv_timer_create(anim_timer_cb, ANIMATION_INTERVAL_MS, NULL);

    LOG_INF("Animation started with %d frames at %dms interval",
            NUM_FRAMES, ANIMATION_INTERVAL_MS);

    return screen;
}
```

---

## Section Breakdown

### 1. Includes

```c
#include <zephyr/kernel.h>           /* Zephyr kernel APIs */
#include <zmk/display/status_screen.h> /* ZMK display interface */
#include <lvgl.h>                     /* LVGL graphics library */
#include <zephyr/logging/log.h>       /* Logging macros */
```

### 2. Configuration Defines

Adjust these for your specific animation:

```c
#define FRAME_WIDTH 72      /* Your animation width */
#define FRAME_HEIGHT 32     /* Your animation height */
#define NUM_FRAMES 6        /* Number of frames */
#define ANIMATION_INTERVAL_MS 150  /* Speed (lower = faster) */
```

### 3. Frame Data

Paste your QMK animation bytes. Format:

```c
static const uint8_t animation_frames[NUM_FRAMES][FRAME_SIZE] = {
    { /* 288 bytes for 72x32 */ },
    { /* 288 bytes */ },
    // ...
};
```

### 4. Canvas Configuration

Must match your Kconfig:

```c
// For CONFIG_LV_COLOR_DEPTH_16=y
#define CANVAS_COLOR_FORMAT LV_COLOR_FORMAT_RGB565

// For CONFIG_LV_COLOR_DEPTH_32=y
#define CANVAS_COLOR_FORMAT LV_COLOR_FORMAT_ARGB8888
```

### 5. Buffer Size

Always use the macro:

```c
#define CANVAS_BUF_SIZE LV_CANVAS_BUF_SIZE(WIDTH, HEIGHT, BPP, ALIGN)
```

Never calculate manually - LVGL handles stride alignment.

---

## Customization Guide

### Different Frame Sizes

```c
/* 128x32 animation */
#define FRAME_WIDTH 128
#define FRAME_HEIGHT 32
#define FRAME_SIZE (128 * 4)  /* 512 bytes */

/* 64x64 animation */
#define FRAME_WIDTH 64
#define FRAME_HEIGHT 64
#define FRAME_SIZE (64 * 8)   /* 512 bytes */
```

### Faster/Slower Animation

```c
#define ANIMATION_INTERVAL_MS 50   /* Fast: 20 FPS */
#define ANIMATION_INTERVAL_MS 100  /* Medium: 10 FPS */
#define ANIMATION_INTERVAL_MS 200  /* Slow: 5 FPS */
```

### Positioning

```c
/* Center (default) */
lv_obj_align(canvas, LV_ALIGN_CENTER, 0, 0);

/* Top-left */
lv_obj_align(canvas, LV_ALIGN_TOP_LEFT, 0, 0);

/* Bottom-right with padding */
lv_obj_align(canvas, LV_ALIGN_BOTTOM_RIGHT, -5, -5);

/* Offset from center */
lv_obj_align(canvas, LV_ALIGN_CENTER, 10, -5);
```

---

## Multiple Animations

For keyboards with multiple animation states:

```c
/* Animation sets */
static const uint8_t idle_frames[6][FRAME_SIZE] = { /* ... */ };
static const uint8_t typing_frames[4][FRAME_SIZE] = { /* ... */ };
static const uint8_t tap_frames[2][FRAME_SIZE] = { /* ... */ };

typedef enum {
    ANIM_IDLE,
    ANIM_TYPING,
    ANIM_TAP
} anim_state_t;

static anim_state_t current_state = ANIM_IDLE;
static uint8_t current_frame = 0;

static const uint8_t *get_current_frames(void) {
    switch (current_state) {
        case ANIM_TYPING: return (const uint8_t *)typing_frames;
        case ANIM_TAP: return (const uint8_t *)tap_frames;
        default: return (const uint8_t *)idle_frames;
    }
}

static uint8_t get_num_frames(void) {
    switch (current_state) {
        case ANIM_TYPING: return 4;
        case ANIM_TAP: return 2;
        default: return 6;
    }
}

static void draw_frame(uint8_t frame_idx) {
    const uint8_t *frames = get_current_frames();
    const uint8_t *frame = &frames[frame_idx * FRAME_SIZE];
    /* ... rest of drawing code ... */
}
```

---

## State-Based Animation

To change animation based on keyboard state:

```c
#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>

/* Change to typing animation on keypress */
static int keycode_listener(const zmk_event_t *eh) {
    const struct zmk_keycode_state_changed *ev =
        as_zmk_keycode_state_changed(eh);

    if (ev->state) {  /* Key pressed */
        current_state = ANIM_TYPING;
        current_frame = 0;
    }
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(animation_listener, keycode_listener);
ZMK_SUBSCRIPTION(animation_listener, zmk_keycode_state_changed);
```

---

## Debugging Tips

### Add Frame Counter

```c
static void anim_timer_cb(lv_timer_t *timer) {
    current_frame = (current_frame + 1) % NUM_FRAMES;
    LOG_DBG("Drawing frame %d/%d", current_frame, NUM_FRAMES);
    draw_frame(current_frame);
}
```

### Verify Buffer Size

```c
lv_obj_t *zmk_display_status_screen(void) {
    LOG_INF("Canvas buffer size: %d bytes", CANVAS_BUF_SIZE);
    LOG_INF("Expected minimum: %d bytes",
            FRAME_WIDTH * FRAME_HEIGHT * LV_COLOR_FORMAT_GET_BPP(CANVAS_COLOR_FORMAT) / 8);
    /* ... */
}
```
