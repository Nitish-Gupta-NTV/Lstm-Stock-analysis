since firstly virtul envrironment which is now now deactivated 
in virtual environment evetinks or module is installed than just activate the virtual environment
by this comand 
## after use deactivated the the virtual environment by comand"deactivate"
### to activated you did not need any command vs code already activated it when you clickon new terminial
if vs code is not actvateing than use this coomand ".\venv\Scripts\Activate.ps1"
check virtual environment is activated or not
if you getting the (venv) before the before  PS E:\project2.0>  or like this (venv) PS E:\project2.0> 
means virual envirnoment is activated no need to activated



than nevigated the backend which is like 
1.cd project2 press enter
2.cd backend press enter
3.python app.py prees enter this will make the backend server streamlit
than start the frontend
open new terminla and naviagted through this
1.cd project2 press enter
2.cd frontend press enter
3.streamlit run app.py
this will start the frontend tell backend start start the takes little time 
conguralgation
  ### to handle the error check is backend working properly in psotman desktop
  first check register is working fine or not 
  click new http request> than select get>than enter the url http://127.0.0.1:5000/register
  than in body enter this 
  {
  "username": "testuser",
  "password": "mypassword"
}
if you get the ok or already exits than regsiter is working  fine 
----- to check login is working
 click new http request> than select get>than enter the url http://127.0.0.1:5000/login
  than in body enter this 
  {
  "username": "testuser",
  "password": "mypassword"
}
----- to check the predication 
 click new http request> than select Post >than enter the url http://127.0.0.1:5000/register
  than in body enter this 
 {
  "ticker": "AAPL",
  "username": "13"
}
if you get the result than predication is working fine
-------------check hsitory




---------finial if evrthing is working  than backend works fine than error is in frontend
side 
