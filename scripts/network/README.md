This folder contains safe network helper scripts for NeXa ToTem.

The scripts default to dry-run mode. They do not change Raspberry Pi networking unless the user passes explicit apply flags.

Files:

- `check_network_safety.py` reads current network state and warns if `wlan0` appears to carry internet.
- `setup_nexa_ap.py` prints or applies the NeXa-ToTem NetworkManager AP plan.
- `rollback_nexa_ap.py` prints or removes only the NeXa-ToTem connection profile.

Do not put personal Wi-Fi credentials, logs, or secrets in this folder.
