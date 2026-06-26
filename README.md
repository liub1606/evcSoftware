This is the software repo for the LHSS (Laurel Heights Secondary School) EVC team.

<details>
<summary>
public telemetry setup guide
</summary>

---
note: this is for linux, should theoretically work on macos directly and on windows w/ a different serial library + waitress or flask development wsgi server (js use wsl vro)

there are 3 main parts
1. public-telemetry/tel-host
2. public-telemetry/tel-server
3. public-telemetry/tel-interface
- tel-host runs on the computer with the serial radio attached. it receives records from the radio, processes them, and POSTs them to the server. this is the code that logs the csv datafile.
- tel-server is a dumb flask server; it just receives records from the host and gives them out to the web-interface when requested. this can optionally run on a different computer.
- tel-interface is the javascript frontend; it GETs data from the server and draws the charts. this is also hosted by tel-server so you shouldnt need to have it separately hosted.

# installing dependencies + setup
first, clone the repo and cd into the public-telemetry directory:
```bash
git clone https://github.com/liub1606/evcSoftware.git
cd evcSoftware/public-telemetry/
```

if your user is not part of the `dialout` group, you will need to run this command to access serial ports like ttyUSB0:
```bash
sudo usermod -a -G dialout $USER
```

set up the python virtual environment and install libraries:
```bash
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

next, to install set up the web interface, install [nodejs and npm](https://nodejs.org/en/download) and install the required npm packages:
```bash
cd tel-interface/
npm i
npm run build
cd ..
```

all dependencies are now installed, and we are ready to run the software.

# running software
## starting webserver
first, start the webserver:
```bash
cd tel-server/
gunicorn app:app

# alternatively, on windows or otherwise without gunicorn
flask run -p 8080
```

if you want it to be publicly accessible (or if youre running on a different device than the host), in another terminal you can start a [trycloudflare quick tunnel](https://try.cloudflare.com/) bound to the webserver, which you can share with anyone else:
```bash
cloudflared tunnel --url http://127.0.0.1:8080
```

## starting host
**this must be done in a new terminal while the webserver is running.**
### note: using the serial emulator
if you want to test changes without the serial radio, you can use `socat` and the inbuilt emulator in the host.
open a new terminal (yes, a third, now would probably be a good time to learn tmux) and run the following command:
```bash
socat -d2 pty pty
```
take note of the two serial ports (e.g. /dev/pts/6 and /dev/pts/7).

to find the serial port of the radio, type `ls /dev` before and after plugging it in. you should see a new port called `/dev/ttyUSB0` or similar.

finally, to start the host, the command should look something like this:
```bash
cd tel-host/

# with the car
python host.py -s http://127.0.0.1:8080 -vv /dev/ttyUSB0

# with an emulator
python host.py -e /dev/pts/6 -s http://127.0.0.1:8080 -vv /dev/pts/7

# with the server on a different device
python host.py -s https://blah-blah-blah.trycloudflare.com -vv /dev/ttyUSB0
```

you can learn about the terminal options with the help flag:
```bash
python host.py -h
```

race logs will be saved in CSV files in tel-host/race-logs

i rlly hope nobody has to use this guide on race day but if you are.... skill issue haha :3
</details>
