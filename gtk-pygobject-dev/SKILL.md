---
name: gtk-pygobject-dev
description: Building desktop applications with Python, GTK4, PyGObject, and DBus integration
---

# GTK/PyGObject Desktop Development

**Purpose:** Create desktop applications, widgets, and shell components using Python with GTK4, GLib, and DBus.

**Use this skill when:**
- Building GTK-based desktop applications
- Creating desktop widgets or shell components
- Working with GLib main loop and async operations
- Integrating with DBus for system services
- Styling GTK applications with CSS

---

## Basic GTK Application

```python
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class MyApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.example.myapp')

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("My GTK App")
        window.set_default_size(400, 300)

        # Create widgets
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        button = Gtk.Button(label="Click Me")
        button.connect('clicked', self.on_button_clicked)

        box.append(button)
        window.set_child(box)
        window.present()

    def on_button_clicked(self, button):
        print("Button clicked!")

if __name__ == '__main__':
    app = MyApplication()
    app.run(None)
```

---

## Widget Creation

```python
from gi.repository import Gtk

# Button
button = Gtk.Button(label="Click Me")
button.connect('clicked', lambda btn: print("Clicked"))

# Label
label = Gtk.Label(label="Hello World")
label.set_markup("<b>Bold</b> and <i>italic</i>")

# Entry (text input)
entry = Gtk.Entry()
entry.set_placeholder_text("Enter text...")
entry.connect('activate', lambda e: print(e.get_text()))

# Box (container)
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
box.append(label)
box.append(button)

# Grid (layout)
grid = Gtk.Grid()
grid.attach(label, 0, 0, 1, 1)
grid.attach(button, 1, 0, 1, 1)
```

---

## GLib Main Loop and Async

```python
from gi.repository import GLib

# Timeout (run function after delay)
def on_timeout():
    print("Timeout!")
    return False  # False = don't repeat, True = repeat

GLib.timeout_add_seconds(5, on_timeout)

# Interval (repeat function)
def on_interval():
    print("Tick")
    return True  # Keep running

GLib.timeout_add(1000, on_interval)  # Every 1000ms

# Idle callback (run when idle)
def on_idle():
    print("Idle")
    return False

GLib.idle_add(on_idle)

# Main loop
loop = GLib.MainLoop()
loop.run()
```

---

## Async Operations

```python
import asyncio
from gi.repository import GLib

def async_to_glib(func):
    """Decorator to run async functions in GLib main loop"""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.create_task(func(*args, **kwargs))
    return wrapper

@async_to_glib
async def fetch_data():
    # Async operation
    await asyncio.sleep(2)
    return "Data loaded"

# Use GLib's async support
from gi.repository import Gio

def load_file_async(path):
    file = Gio.File.new_for_path(path)
    file.load_contents_async(None, on_load_complete)

def on_load_complete(file, result):
    try:
        success, contents, _ = file.load_contents_finish(result)
        if success:
            print(f"Loaded: {contents.decode()}")
    except Exception as e:
        print(f"Error: {e}")
```

---

## DBus Integration

```python
from gi.repository import Gio

# Connect to DBus
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

# Call DBus method
def call_dbus_method():
    proxy = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        'org.freedesktop.Notifications',  # Bus name
        '/org/freedesktop/Notifications',  # Object path
        'org.freedesktop.Notifications',  # Interface
        None
    )

    result = proxy.call_sync(
        'Notify',
        GLib.Variant('(susssasa{sv}i)', (
            'MyApp',
            0,
            '',
            'Hello',
            'This is a notification',
            [],
            {},
            -1
        )),
        Gio.DBusCallFlags.NONE,
        -1,
        None
    )
    print(f"Notification ID: {result[0]}")

# Listen to DBus signals
def on_signal(proxy, sender, signal, params):
    print(f"Signal {signal}: {params}")

proxy.connect('g-signal', on_signal)
```

---

## CSS Styling

```python
from gi.repository import Gtk

# Load CSS
css_provider = Gtk.CssProvider()
css_provider.load_from_data(b"""
    window {
        background-color: #2e3440;
    }

    button {
        background-color: #5e81ac;
        color: white;
        border-radius: 6px;
        padding: 12px;
    }

    button:hover {
        background-color: #81a1c1;
    }

    label {
        color: #eceff4;
        font-size: 14px;
    }

    .accent {
        color: #88c0d0;
        font-weight: bold;
    }
""")

# Apply to display
display = Gdk.Display.get_default()
Gtk.StyleContext.add_provider_for_display(
    display,
    css_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

# Add CSS class to widget
button = Gtk.Button(label="Styled Button")
button.add_css_class('accent')
```

---

## Widget with Custom Drawing

```python
from gi.repository import Gtk, Gdk
import cairo

class CustomDrawing(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_draw_func(self.on_draw)

    def on_draw(self, area, cr, width, height):
        # Cairo drawing context
        cr.set_source_rgb(0.2, 0.4, 0.6)
        cr.rectangle(10, 10, width - 20, height - 20)
        cr.fill()

        cr.set_source_rgb(1, 1, 1)
        cr.move_to(width // 2 - 50, height // 2)
        cr.show_text("Hello GTK!")
```

---

## File Operations

```python
from gi.repository import Gio

# Read file
file = Gio.File.new_for_path('/path/to/file.txt')
success, contents, _ = file.load_contents(None)
if success:
    text = contents.decode('utf-8')

# Write file
file = Gio.File.new_for_path('/path/to/output.txt')
file.replace_contents(
    b'Hello World',
    None,  # etag
    False,  # make_backup
    Gio.FileCreateFlags.NONE,
    None  # cancellable
)

# Monitor file changes
monitor = file.monitor_file(Gio.FileMonitorFlags.NONE, None)
monitor.connect('changed', lambda m, f, o, event: print(f"File changed: {event}"))
```

---

## Settings/Configuration

```python
from gi.repository import Gio

# Create settings schema (requires GSettings schema file)
settings = Gio.Settings.new('com.example.myapp')

# Get/set values
value = settings.get_string('some-key')
settings.set_string('some-key', 'new value')

# Watch for changes
def on_setting_changed(settings, key):
    print(f"Setting {key} changed to: {settings.get_string(key)}")

settings.connect('changed::some-key', on_setting_changed)

# Using JSON config instead (simpler for small apps)
import json
from pathlib import Path

config_path = Path.home() / '.config' / 'myapp' / 'config.json'
config_path.parent.mkdir(parents=True, exist_ok=True)

def load_config():
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}

def save_config(config):
    config_path.write_text(json.dumps(config, indent=2))
```

---

## Desktop Widget Pattern (Layer Shell)

```python
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gtk4LayerShell

class DesktopWidget(Gtk.Window):
    def __init__(self):
        super().__init__()

        # Initialize layer shell
        Gtk4LayerShell.init_for_window(self)

        # Set layer (background, bottom, top, overlay)
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)

        # Set anchors (stick to edges)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.RIGHT, True)

        # Set margins
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.TOP, 10)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.RIGHT, 10)

        # Set size
        self.set_default_size(300, 100)

        # Build UI
        label = Gtk.Label(label="Desktop Widget")
        self.set_child(label)
```

---

## Common Patterns

### Logging with Loguru + Rich
```python
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler

console = Console()
logger.remove()
logger.add(
    RichHandler(console=console),
    format="{message}",
    level="INFO"
)

logger.info("GTK app starting")
logger.error("Something went wrong")
```

### Error Handling
```python
from gi.repository import GLib

def safe_callback():
    try:
        # Risky operation
        result = 1 / 0
    except Exception as e:
        logger.error(f"Error in callback: {e}")
        return False  # Stop repeating
    return True

GLib.timeout_add(1000, safe_callback)
```

### Thread Safety
```python
from threading import Thread
from gi.repository import GLib

def background_task():
    # Do work in background
    result = expensive_computation()

    # Update UI in main thread
    GLib.idle_add(lambda: update_ui(result))

thread = Thread(target=background_task)
thread.start()
```

---

## Project Structure (ignis-style)

```
my-gtk-app/
├── my_gtk_app/
│   ├── __init__.py
│   ├── app.py              # Main application
│   ├── services/           # Background services
│   │   ├── __init__.py
│   │   └── system_monitor.py
│   ├── widgets/            # Custom widgets
│   │   ├── __init__.py
│   │   └── status_widget.py
│   ├── utils/              # Utilities
│   │   ├── __init__.py
│   │   └── dbus_helper.py
│   └── dbus/               # DBus interfaces
│       ├── __init__.py
│       └── notifications.py
├── examples/               # Example configurations
├── docs/                   # Documentation
├── pyproject.toml          # Project metadata
└── README.md
```

---

## Dependencies (pyproject.toml)

```toml
[project]
name = "my-gtk-app"
version = "0.1.0"
dependencies = [
    "PyGObject>=3.42",
    "loguru>=0.7",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "black",
    "mypy",
]

[project.scripts]
my-gtk-app = "my_gtk_app.app:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Development Workflow

```bash
# Install in development mode
pip install -e .
# OR
uv pip install -e .

# Run application
python -m my_gtk_app
# OR (if scripts configured)
my-gtk-app

# Debug with logging
GTK_DEBUG=interactive my-gtk-app

# Monitor with GtkInspector
GTK_DEBUG=interactive python -m my_gtk_app
# Press Ctrl+Shift+D to open inspector
```

---

## Key Concepts

**GLib Main Loop:** Event-driven architecture, handles all events
**Signals:** Connect widgets to callbacks with `.connect()`
**CSS:** Style widgets with GTK CSS (similar to web CSS)
**DBus:** Inter-process communication for system services
**Layer Shell:** For desktop widgets/overlays (Wayland)
**Async:** Use GLib's async or Python's asyncio
**Threading:** UI updates must happen in main thread

---

**When this skill activates:**
- Working in `ignis/**/*.py` or GTK-related files
- Keywords: "gtk", "pygobject", "dbus", "glib", "desktop widget"
- Patterns: `from gi.repository import Gtk`, `Gtk.Application`

**Use explicitly for:**
- Creating GTK desktop applications
- Building desktop widgets or shell components
- DBus integration
- GLib async operations
- Styling with CSS
