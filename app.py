from typing import Collection
from unittest.mock import NonCallableMock
from xml.dom import NotFoundErr
from flask import *
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import pymongo

f = open('./keys.txt', 'r')
key = f.readline()    
client = pymongo.MongoClient(key)
    
db = client.exp_application
users, experiments, participants = db.users, db.experiments, db.participants

app = Flask(__name__, static_folder = 'static')
app.secret_key = f.readline()
f.close()

bcrypt=Bcrypt(app)

# 
# 所有路徑
# 我是參與者————開放中實驗清單————某實驗目前開放時間————成功預約
#  
# 我是實驗者——————————登入現有帳號————選擇進行中實驗——————管理實驗開放時段————送出資料
#          ｜               ｜           ｜                     ｜
#           ——沒有帳號——註冊——             ——沒有實驗——創建新實驗——
# 

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/msg')
def msg():
    message = request.args.get('msg', '發生不明錯誤')
    return render_template('msg.html', msg = message)

@app.route('/go_back', methods = ['GET', 'POST'])
def go_back():
    data = request.form
    return render_template('go_back.html', data=data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

################實驗者路徑################

# 我是實驗者——————————→登入現有帳號———選擇進行中實驗———管理實驗開放時段————送出資料
#          ｜               ｜           ｜                     ｜
#           ——沒有帳號——註冊——             ——沒有實驗——創建新實驗——

#########################################


##############data instance##############

# users: {'email', 'password', 'own'}
# experiments: {'name', 'owner', 'descriptions', 'available', 'taken', 'turnedoff'}
# participants: {'name', 'in_school', 'age', 'gender', 'exp_name', 'date', 'time'}

#########################################

@app.route('/expter')
def expter():
    return render_template('expter.html')


# 創建帳號
@app.route('/invitation_check')
def invitation_check():
    return render_template('invitation_check.html')

@app.route('/invitation_check_backend', methods = ['POST'])
def check():
    session['InvitationCode'] = request.form['InvitationCode']
    result = users.find_one({
        'email': session['InvitationCode']
        })
    if result != None:
        session['permission'] = 1
        return redirect('/create_account')
    else:
        data = {'msg': '錯誤：您輸入的邀請碼不存在', 'url': '/invitation_check', 'text':'點擊此處回前頁'}
        return render_template('go_back.html', data = data)
        
@app.route('/create_account')
def create_account():
    if session.get('permission'):
        return render_template('/create_account.html')
    else:
        return redirect('/msg?msg=You are not allowed to visit this page')
    
@app.route('/register', methods = ['POST'])
def register():
    email = request.form['email']
    pw = request.form['password']
    pw = bcrypt.generate_password_hash(pw).decode('utf-8')
    name = request.form['username']
    result = users.find_one({'email': email})
    if result != None:
        data = {'msg': '該信箱已被註冊過囉！', 'url': '/register', 'text':'點此回到註冊頁面'}
        return render_template('go_back.html', data=data)
    else:
        users.insert_one({
            'email': email,
            'password': pw,
            'realname': name,
            'own':[]
            })
        data = {'msg': '恭喜註冊成功！', 'url': '/login', 'text':'點此回到登入頁面'}
        return render_template('go_back.html', data=data)

######正式登入環節######
@app.route('/login')
def login():
    if session.get('email'):
        return redirect('/select_exp')
    else:
        return render_template('login.html')

@app.route('/login_backend', methods = ['POST'])
def login_backend():
    email, pw = request.form.get('email'), request.form['password']
    user_data = users.find_one({'email': email})
    err_msg = {'msg': '您輸入的帳號或密碼錯誤', 'url': '/login', 'text':'回上一頁'}
    
    if not user_data:
        return render_template('go_back.html', data = err_msg)
    else:
        pw_hashed = user_data['password']
        result = bcrypt.check_password_hash(pw_hashed, pw)
        if result:
            session['email'] = email
            return redirect('/select_exp')
        else:
            return render_template('go_back.html', data = err_msg)

@app.route('/select_exp', methods = ['GET', 'POST'])
def select_exp():
    session.pop('current_focus_exp', None)
    current_expts = users.find_one({'email': session['email']}, {'own':1})['own']
    # current_expts_encoded = {exp:urllib.parse.quote(exp) for exp in current_expts}    
    
    return render_template('select_exp.html', current_expts = current_expts)

@app.route('/add_exp')
def add_expt():
    return render_template('add_exp.html')

@app.route('/add_exp_back', methods = ['GET', 'POST'])
def add_exp_back():
    response = request.form
    exp_name, description = response['name'], response['description']
    users.update_one({'email': session['email']},{'$push':{'own':exp_name}}) 
    available = list(response.values())
    available.remove(exp_name)
    available.remove(description)
    experiments.insert_one({'name':exp_name,'available': available, 'description': description, 'taken': []})
    data = {'msg': '表單已新增！', 'url': f'/manage_time?name={exp_name}', 'text':'點此以確認實驗設定'}
    return render_template('go_back.html', data=data)


@app.route('/manage_time', methods = ['GET', 'POST'])
def manage_time():
    session['current_focus_exp'] =request.args.get('name')
    available =experiments.find_one({'name': session['current_focus_exp']}, {'available':1})
    if available:
        available = available['available']
    subj = participants.find({'exp_name': session['current_focus_exp']})
    return render_template('manage_time.html', subj=subj, available = available)

@app.route('/manage_time_back', methods = ['POST'])
def manage_time_back():
    all_subj = request.get_json()
    # del col header
    all_subj.pop('')
    
    valid = {k: v for k, v in all_subj.items() if v[0] != ''}
    id_list = [str(key['_id']) for key in participants.find()]
    already_in_db = {k: v for k, v in valid.items() if k in id_list}

    # 已在participant，未被取消
    still_in_db = {key: already_in_db[key] for key in already_in_db.keys() if already_in_db[key][1] != 'available'}
    
    # 原先在participant，狀態須返回取消
    cancelled = {key: already_in_db[key] for key in already_in_db.keys() if already_in_db[key][1] == 'available'}
    
    # 原先在participant，時段取消
    to_deleted_time = {k: v for k, v in all_subj.items() if (v[0] == '') and k in id_list}

    # 原先不在participant資料庫（但可能在experiment.available
    new = {k: v for k, v in valid.items() if k not in id_list}
    new_apply = {key: new[key] for key in new.keys() if new[key][1] != 'available'}
    # new_available = {key: new[key] for key in new.keys() if new[key][1] == 'available'}

    current_focus_exp = session['current_focus_exp']

    ## 先更新participants資料庫
    # 更新已報名
    for subj in still_in_db.keys():
        participants.update_one(
            {'_id': ObjectId(subj)}, 
            {'$set': {
                'time':still_in_db[subj][0],
                'name':still_in_db[subj][1],
                'email':still_in_db[subj][2],
                'in_school':still_in_db[subj][3]
            }}
            )
        print(f'updated {subj}: {still_in_db[subj]}')
    
    # 已取消
    removed_from_participants = set(to_deleted_time)
    for id in removed_from_participants:
        try:
            participants.delete_one({'_id': ObjectId(id)})
            print(f'deleted id:{id}')
        except:
            pass
    
    # 新報名
    for subj in new_apply:
        participants.insert_one(
            {
                'exp_name': current_focus_exp,
                'time': new_apply[subj][0],
                'name': new_apply[subj][1],
                'email': new_apply[subj][2],
                'in_school': new_apply[subj][3]
            }
            )
        print(f'inserted {subj}: {new_apply[subj]}')     

    ## 更新experiments時間    
    # 如果變回available，修改experiment的available & taken 
    now_available = [v[0] for k, v in valid.items() if v[1] == 'available']
    now_taken = [v[0] for k, v in valid.items() if v[1] != 'available']
    
    experiments.update_many(
        {'name': current_focus_exp},
        {'$set': {
                'available': now_available, 
                'taken': now_taken
                }}
        )
    # current_focus_exp_encoded = urllib.parse.quote(current_focus_exp)
    data = {
        'msg': '表單已儲存！', 
        'url': f'/manage_time?name={current_focus_exp}', 
        'text':'點此以確認實驗設定'
        }
    return render_template('go_back.html', data=data) 

################參加者路徑################        
# 
# 我是參與者--->開放中實驗清單---->某實驗目前開放時間----->成功預約
# 

@app.route('/applicant')
def applicant():
    current_expts = experiments.find({}, {'name': 1})
    # current_expts_encoded = {exp['name']:urllib.parse.quote(exp['name']) for exp in current_expts}
    return render_template('applicant.html', current_expts = current_expts)

@app.route('/query_time')
def query_time():
    choosed = request.args.get('exp_name')
    session['exp_name'] = choosed
    available_of_choosed = experiments.find_one({'name': choosed}, {'_id':0})
    return render_template('arrange.html', available_of_choosed = available_of_choosed)

@app.route('/arrange_request', methods = ['GET', 'POST'])
def arrange_request():
    exp_data = experiments.find_one({'name':session['exp_name']})
    session['arranging_time'] = request.args.get('time')
    if session['arranging_time'] in exp_data['available']:
        return render_template('personal_form.html') 
    else:
        data = {'msg': '錯誤：可能是您選擇的時段已被預約，請再試一次', 'url': '/applicant', 'text':'點此回到實驗列表'}
        return render_template('go_back.html', data=data) 
@app.route('/arranging', methods = ['GET', 'POST'])
def personal_form():
    exp_data = experiments.find_one({'name':session['exp_name']})
    exp_data['available'].remove(session['arranging_time'])
    exp_data['taken'].append(session['arranging_time'])
    name, email, age = request.form['name'], request.form['email'], request.form['age']
    in_school = 'Yes' if request.form.get('in_school') == 'on' else 'No'
    participants.insert_one({'name': name, 'email': email, 'age': age, 'exp_name': session['exp_name'], 'time': session['arranging_time'], 'in_school':in_school})
    experiments.update_one({'name':session['exp_name']}, {'$set': exp_data})
    exp_name, arranging_time = session['exp_name'], session['arranging_time']
    session.clear()
    return redirect(f'/msg?msg=您已成功預約，實驗名稱：{exp_name}，預約時間：{arranging_time}，請記得準時赴約喔！')
 

# 缺：1) 顯示實驗報名情況功能

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 8080, debug = True)
    
