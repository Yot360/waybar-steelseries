# waybar-steelseries
 A waybar module that shows battery levels for my Steelseries Aerox Wireless 3 mouse and Steelseries Arctis Nova 5 headset

Output: `󰍽 80%  󰋋 13%`, with a tooltip and the `warning` / `critical` / `charging` / `disconnected` CSS classes.
A device that is off or unplugged is left out. If both are, the module is hidden.

## Requirements

- [rivalcfg](https://github.com/flozz/rivalcfg) (mouse)
- [HeadsetControl](https://github.com/Sapd/HeadsetControl) (headset)
- Python 3 (standard library only)
- A Nerd Font for the icons

## Install

```sh
install -Dm755 waybar-steelseries.py ~/.config/waybar/scripts/waybar-steelseries.py
```

`~/.config/waybar/config.jsonc`:

```jsonc
"modules-right": ["custom/steelseries", ...],

"custom/steelseries": {
    "exec": "~/.config/waybar/scripts/waybar-steelseries.py",
    // optional: "exec": "~/.config/waybar/scripts/waybar-steelseries.py --warning 25 --critical 10",
    "return-type": "json",
    "interval": 10
}
```

`~/.config/waybar/style.css`:

```css
#custom-steelseries.warning  { color: #f9e2af; }
#custom-steelseries.critical { color: #f38ba8; }
#custom-steelseries.charging { color: #a6e3a1; }
```

The class is based on the lowest battery that is not charging. The defaults are warning at 30% or below and critical at 15% or below.
