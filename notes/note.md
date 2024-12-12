# Note

## 1. Use `python3` venv
``` python
python3 -m venv venv
source venv/bin/activate
```

## 2. Use `iwlist` for wifi scan (not recommended)
``` bash
iwlist wlp1s0 scan # wlp1s0 is wifi interface
```

## 3. Use `nmcli` for wifi scan (recommended)
``` bash
nmcli device wifi rescan
nmcli device wifi list
```
* `rescan` refreshes wifi list before displaying results

## 4. Install `pywifi`.
``` bash
pip install pywifi
```

## 5. Use `sqlite3`
``` bash
sqlite3 # preinstalled in Ubuntu
```

## 6. Use `pip-tools` to filter `requirement.txt`
``` bash
pip install pip-tools # install pip-tools
pip freeze > requirements.txt # generate systemwide dependencies
echo "pywifi" >> requirements.in # add relevant libraries
pip-compile requirements.in # filter requirements.txt from requirements.in
pip install -r requirements.txt # install dependencies (insdide venv)
```

## 7. Add user to `netdev` group to access `/var/run/wpa_supplicant`
``` bash
ls -ld /var/run/wpa_supplicant # check group ownership
sudo usermod -aG netdev $USER # add user
newgrp netdev # apply changes
groups $USER # verify membership
```


