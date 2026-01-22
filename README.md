Binance VM
Clean, minimal email validation tool for Binance using Playwright.

Setup
pip install -r requirements.txt
pip install playwright
pip install chromium 
python3 -m venv .venv
source .venv/bin/activate #this will activate the .venv and make sure it's active when running the code 
pip install playwright requests capsolver
pip install --upgrade pip wheel setuptools
Usage
insert your rotating proxy in config.py
test your proxy with test_proxy.py
test your proxy for playwright test_playwright_proxy.py
you can check the captcha solver in src/captcha.py you need to hook your captcha solver their you can hook it whatever the captcha service you are using it and place your api to call the captcha solver
before running the tool make sure your pc is above 16gb ram
you can adjust the threads in the main.py according to your setup
if you want the threds to run manually but not according to your pc then remove threads from main.py and set the threads stuff in config.py but make sure the accuracy won't drop while speeding
keep it minimal and the broswer timeout low to increase the speed instead of increasing the threading speed and you can find it in src\checker.py
chromium launches slow if you are running "Headless=False" so make sure about browser timeouts
always put the "headless=true" in the config.py but if you want to inspect it use "Headless=False"
if you face any issues while checking then use debug_checkbox.py import it to src\checker.py
oops i forgot to gave you the run command it's python main.py
note that each thread checks one mail so if you even want to increase the speed with minimal coding than set one rotating proxy with 3 to 5 tabs per broswer then it will check 3 to 5 mails for one threads so if you are running 48 threads with 3 tabs per broswer then it will check 144 mails at a time and the timeout is averagly 10 seconds, it completely depends on your pc and you can make this edits in config.py if you remove threads section from main.py which is set according to your pc core but make sure to increase the threads slowly when doing it manually otherwise you may see your pc hanging up and smoke coming out of it
if you are running "Headless=False" for debuging make sure you are using 2 to 3 mails for testing because for "headless=False" each chromium browser uses 2MB of your bandwidth so if you keep running multiple number of mails while debuging then you can say goodbye to your proxy bandwidth
if you still face any issues regarding the tool feel free to reach me @Johnevangelist :D , but if you face any issues while hooking the captcha solver then it's your provider problem or problem with capsolver implimentation
Credits
Made by @JohnEvangelist on 09/24 made only for educational purpose not for any misuse of this tool
