# o-see-lloscope

This is the Code Network Winter Hackathon project for team Seesaw.

An application for the visually impaired to allow full access to oscilloscope
measuring — a REPL that drives a Rigol DS1054Z over SCPI, with an optional
LLM-powered description of captured waveforms and an audio playback mode.

## Problems

There are permission issues that can be quite tricky to solve on Linux - keep
that in mind. This is mainly due to usbtmc issues and trying to communicate
to the device. To solve this for now you have to run your python environment
as sudo (not cool). Playing with udev rules currently and hopefully will have
a non-sudo solution soon.

- Turns out the `/dev/bus/usb/[bus]/[device]` for the Rigol had bad privs.
  Just chown these for your user and the python should work. Use `lsusb` to
  find the device.
  - for example: `sudo chown justin:justin /dev/bus/usb/001/008`

## Setup

1. Have python installed (3.12+ required — see note below)
2. Create python virtual environment: `python -m venv venv`
3. Source virtual environment
4. Install deps: `pip install -r requirements.txt`
5. Run `python main.py` with the Rigol DS1054Z connected to your PC
6. If you can't connect to the device it is likely that the usbtmc perms are
   causing issues (see Problems above)

> **Note:** `requirements.txt` pins `scipy==1.18.1`, which requires Python
> >=3.12. Make sure your venv is built with 3.12 or later.

## Commands

Run `help` inside the REPL at any time for the full, up-to-date list with
usage and examples. Current commands include:

| Command | Description |
|---|---|
| `auto` | Adjusts scale and position to view the signal |
| `measure` | Provides a summary of the signal (Vpp, frequency, Vavg) |
| `divscale <ch> <v/div> <t/div>` | Manually sets volts/div and time/div |
| `coupling <ch> <AC\|DC\|GND>` | Sets input coupling for a channel |
| `capture <ch>` | Captures a waveform, saves `capture.png` and `capture.csv` |
| `trigger <edge\|falling> <pos\|neg> <level>` | Configures a trigger on channel 1 |
| `playback` | Plays the last capture as audio (pitch mapped from voltage) |
| `describe` | Starts a conversation with Gemini Flash about the captured graph |
| `id` | Identifies the connected device |
| `clear` | Clears the console |
| `help` | Lists all commands |

## Testing

Unit tests use `pytest` with a `FakeScope` stand-in so no hardware is
required to run them:

```
pip install pytest
pytest -v
```

CI runs the full suite automatically on push and PR via GitHub Actions
(`.github/workflows/tests.yml`).

## AI Description

The `describe` command sends the captured waveform image (`capture.png`)
to Google's Gemini Flash and lets you ask follow-up questions about it in
an interactive chat, so a signal can be described in plain language
without needing to interpret the plot visually.

## Research / Inspiration

- [SCPI Through Python](https://testflowinc.com/blog/automate-rigol-oscilloscope-python-scpi-pyvisa-guide)

## Features

**Must-have:**
1. Capturing data such as Vpp, frequency, voltage, average voltage, amplitude
2. Manual adjustment and scaling of measurements such as frequency, etc
3. Provide full access to someone using a screen reader, or provide
   alternative options

**Should-have:**
1. AI-powered description of captured signals (via Gemini Flash)

**Could-have:**
1. Plots with customizable colors and line thicknesses
2. Navigate through the data