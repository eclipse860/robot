# PC Control Scripts

These scripts run on the Windows PC and communicate with the Raspberry Pi over
Tailscale using WebSocket commands.

## Setup

Install Python and dependencies:

```powershell
python -m pip install -r requirements-pc.txt
```

## Keyboard RC Control

Run:

```powershell
python keyboard_send.py --host 100.69.90.121
```

Replace `100.69.90.121` with the current Pi Tailscale IP.

Controls:

```text
W or Up       increase forward throttle
S or Down     increase reverse/brake throttle
A or Left     steer left
D or Right    steer right
Space         neutral throttle
C             center steering
X             neutral throttle and center steering
Q             quit
```

## Steering Demo

Run:

```powershell
python ws_send.py
```
