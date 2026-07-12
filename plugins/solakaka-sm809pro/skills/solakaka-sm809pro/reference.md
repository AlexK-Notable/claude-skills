# SM809Pro — Full Reference Tables

All values below were reverse-engineered from the web configurator's own JS bundle
(`driver.yuandaxin-tech.com/HYX/V1000_SM809_3311/assets/index-*.js`) and cross-checked
against a real `Onboard_Config.json` export. Values marked ⚠️ are inferred, not confirmed.

## Device identity

| Property | Value |
|---|---|
| USB Vendor ID | `0x04F3` (1267, Elan Microelectronics) |
| PID `0x026E` (622) | **Wired USB** mode — enumerates as "MMO Gaming Mouse" |
| PID `0x026F` (623) | **2.4G dongle** mode — "Yuan Da Xin V2000 / 2.4G Wireless mouse" |
| other PID | **Bluetooth** mode |
| WebHID filter used by app | `requestDevice({filters:[{vendorId:1267}]})` |

## Config JSON structure (`Onboard_Config.json`)

```
sensorType : int        # sensor-model enum (17 on this unit)
keys       : button1..button16   # each: {id, name|nameKey, enabled, currentKey:{id, name|nameKey, code[3]}}
dpi        : {...}
performance: {...}
other      : {...}       # lighting
id, name   : profile identity ("default" / "Onboard Config")
```

- `name` = literal label (custom keys, e.g. `"7"`). `nameKey` = i18n key for built-ins (`mouse.labels.forward`). A slot has one or the other.
- `currentKey.code` is the **authoritative** 3-byte hardware action. `name`/`nameKey`/`id` are UI presentation only.

### Physical button slots (default functions)
`1–11` = programmable side/thumb buttons · `12` = Left · `13` = Right · `14` = Middle · `15` = DPI+ · `16` = DPI−

### `currentKey.id` presets
`m1`=Left · `m2`=Right · `m3`=Middle · `m4`=Forward · `m5`=Back · `m6`=DPI-Cycle · `m19`=generic bucket (keyboard, media, fire, DPI±, disable, etc.)

## The 3-byte action code `[TYPE, P1, P2]`

TYPE (byte 0) selects the class; P1/P2 depend on it:

| TYPE | Class | P1 | P2 |
|---|---|---|---|
| `0x10` | **Mouse button** | HID button bitmap (below) | `0x00` |
| `0x30` | **Fire / rapid key** | interval `5–255` ⚠️ | count `0–255` (0 = hold-to-fire) ⚠️ — fires **left click** |
| `0x40` | **DPI / device fn** | `0x01`=Cycle, `0x02`=DPI+, `0x03`=DPI−, DPI-Lock⚠️ | `0x00` |
| `0x70` | **Keyboard** | modifier bitmap (below) | HID keyboard usage (page 0x07) |
| `0x80` | **Consumer / multimedia** | low byte of 16-bit LE consumer usage | high byte (e.g. `0x0194`=My Computer) |

**Mouse button bitmap (P1 for TYPE 0x10):** `0x01`=Left · `0x02`=Right · `0x04`=Middle · `0x08`=Back(btn4) · `0x10`=Forward(btn5)

**Modifier bitmap (P1 for TYPE 0x70):** `0x01`=LCtrl · `0x02`=LShift · `0x04`=LAlt · `0x08`=LGui/Win · `0x10`=RCtrl · `0x20`=RShift · `0x40`=RAlt · `0x80`=RGui

### HID Keyboard usage table (page 0x07) — P2 for TYPE 0x70
```
a–z      = 4–29           1 2 3 4 5 6 7 8 9 0 = 30 31 32 33 34 35 36 37 38 39
Enter=40 Esc=41 Bksp=42 Tab=43 Space=44
- =45  = =46  [ =47  ] =48  \ =49  ; =51  ' =52  ` =53  , =54  . =55  / =56
CapsLock=57   F1–F12 = 58–69
PrintScreen=70 ScrollLock=71 Pause=72 Insert=73 Home=74 PageUp=75
Delete=76 End=77 PageDown=78   →=79 ←=80 ↓=81 ↑=82   NumLock=83
Numpad: / =84  * =85  - =86  + =87  Enter=88  1–9 =89–97  0=98  . =99   ContextMenu=101
Modifier-as-key usages: Ctrl=224 Shift=225 Alt=226 Meta=227
Volume (keyboard page): Mute=127 Up=128 Down=129
```
(Media Play/Stop/Prev/Next appear as app-internal 232–235 and mouse pseudo-codes MouseLeft=240…MouseBack=244 in the *capture* table; hardware uses the TYPE bytes above.)

### Assignable function categories (UI menu)
Mouse Buttons · Text Office (keyboard) · Multimedia (consumer) · Special Keys · Combo Key (modifier+key) · Fire Key · DPI (Cycle/+/−/Lock) · Disable Key · Lighting Toggle · Calculator · Email · My Computer · **Macros**

### Macros
Recorded event sequences assigned to a button. Event types: Left/Right/Middle click, Delay, Keyboard key. Downloaded to the mouse via command opcode `0x11` (erase macro region first, then per-button events).

## DPI section
| Field | Meaning |
|---|---|
| `levels[8]` | DPI per stage; only first `levelCount` are active, rest are placeholders |
| `currentLevel` | **0-indexed** pointer into `levels` |
| `currentDPI` | resolved DPI at `currentLevel` |
| `colorsX` / `colorsY[8]` | LED color shown per DPI stage (hex) |
| `xyIndependent` | false = X/Y locked; true = use `levelsX`/`levelsY` separately |
| `levelsX/Y`, `currentLevelX/Y`, `currentDPIX/Y` | separate X/Y DPI tables |
| `levelCount` | number of active stages |

## performance section
| Field | Meaning |
|---|---|
| `pollingRate` | enum **index**, not Hz. `1` = 1000 Hz on this unit (mapping confirmed by user; other indices TBD) |
| `liftOffDistance` | LOD, `1` or `2` (mm) |
| `powerSleepTime`, `powerTimeRange` | wireless power-save timers |
| `powerMoveWakeup`, `powerMoveLighting` | bool |
| `angleSnap` | 1/0 — straight-line input correction (prediction). **Off for aim.** |
| `motionSync` | 1/0 — align sensor frames to poll clock (~1 ms latency vs steadier timing) |
| `rippleControl` | 1/0 — high-DPI smoothing/low-pass filter. **Off for aim.** |

## other (lighting) section
| Field | Meaning |
|---|---|
| `lightingMode` | numeric effect enum ⚠️ (7 on this unit; number→effect map best found by UI diff) |
| `lightingBrightness` | small int (≈0–5) |
| `lightingColor` | hex (`#409EFF` = Element-UI default blue) |
| `lightingSpeed` | small int |
| `lightingDirection` | 0/1 |

## Direct HID access protocol (WebHID → Linux hidraw)

The configurator uses **HID feature reports** only — the same channel reachable from
Linux `/dev/hidraw*` via `HIDIOCSFEATURE`/`HIDIOCGFEATURE` or hidapi. With the udev
rule in place (see SKILL.md) the user can open the device directly.

**Report IDs**
- `6` = command channel (write command; read command-ACK)
- `5` = device status (read)

**Command packet** (the `data` passed to `sendFeatureReport(6, data)`), 32 bytes:
```
[ opcode, seq, subcmd/count, checksum, ...payload(zero-padded to length) ]
   byte0   byte1    byte2       byte3      byte4..
```
- `seq` (byte1) = incrementing transaction counter.
- `checksum` (byte3) = `(6 + sum(all bytes except index 3)) & 0xFF`, **inserted at index 3**.
- On the wire, `sendFeatureReport` prepends report id `6`, so the physical feature report is `[6, opcode, seq, subcmd, checksum, ...]`.

**ACK**: read `receiveFeatureReport(6)`; `byte[1] == 1` means the command succeeded. App retries 3× with 100+50·n ms backoff.

**Known opcodes**: `0x0F` = reset · `0x11` = macro-region erase / macro set.
Button / DPI / lighting / performance *write* opcodes exist but are **not fully
enumerated** — finishing them needs either more static analysis of the app's
apply-functions or a `usbmon`/Wireshark capture of the feature reports while clicking
"Apply" in the web UI, then replaying them.

**Read example (Python, hidapi):**
```python
import hid
d = hid.Device(vid=0x04f3, pid=0x026e)   # 0x026e wired; 0x026f for 2.4G dongle
status = d.get_feature_report(5, 33)     # report id 5, buffer incl. report-id byte
```
Writing config directly is feasible but requires the per-field opcode map above.
