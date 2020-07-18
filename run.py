from flask import Flask,flash,jsonify,request,render_template,redirect,url_for,session,flash
import firebase_utils as f
import xlrd
import random

app = Flask(__name__)
app.secret_key = "secretkey2020" 

@app.route("/dashboard")
def index(): 
    if 'uid' in session:
        groups = []
        cid = session['uid']
        for i in f.get_groups_by_college(cid):
            d = i.to_dict()
            d['id'] = i.id
            d['members'] = len(f.get_member_data_from_group(i.id))
            c = 0
            for i in f.get_channels_from_group(i.id):
                c += 1     
            d['courses'] = c
            groups.append(d)
        return render_template('index.html', groups = groups)
    return redirect('/')

@app.route("/")
def login_page():   
    return render_template('login.html')

@app.route("/logout")
def logout_user():   
    if 'uid' in session:
        session.pop('uid',None)
    return redirect('/')


@app.route("/login", methods=['GET', 'POST'])
def login_user():   
    password = request.form['pswd']
    username = request.form['username']
    isValid, uid = f.college_login(username, password)
    if isValid:
        session['uid'] = uid
        return redirect('/dashboard')
    else:
        flash('Incorrect Credentials', 'danger')
        return redirect('/')

@app.route("/newgroup")
def new_group():   
    if 'uid' in session:
        return render_template('newgroup.html')
    return redirect('/')

@app.route("/newfaculty")
def faculty_add():   
    if 'uid' in session:
        cid = session['uid']
        faculty = []
        for i in f.getFacultiesFromCollege(cid):
            d = i.to_dict()
            d['uid'] = i.id
            faculty.append(d)
        return render_template('faculty.html',faculty=faculty)
    return redirect('/')

@app.route("/creategroup", methods=['GET', 'POST'])
def create_group():
    if 'uid' in session:
        gname = request.get_json()['gname']
        gabbr = request.get_json()['gabbr']
        cid = session['uid']
        try:
            f.createGroup(gname,gabbr,'ffffff',[],cid)
            flash('Group Created Successfully','success')
        except:
            flash('Group Not Created', 'danger')
        return jsonify({})
    return redirect('/')

@app.route("/createchannel", methods=['GET', 'POST'])
def create_channel():
    if 'uid' in session:
        gid = request.get_json()['gid']
        cname = request.get_json()['cname']
        fid = request.get_json()['fid']
        try:
            cid = f.createPrivateChannel(gid, cname)
            if f.checkIfUserIsInGroup(fid,gid):
                flash('Faculty already added to Course','warning')
            else:
                f.add_user_to_group(gid,fid)
                f.add_user_to_channel(gid,cid,fid)
            flash('Channel Created','success')
        except:
            flash('Channel Not Created','danger')
        return jsonify({})
    return redirect('/')

@app.route("/createstudentaccounts", methods=['GET', 'POST'])
def create_student_accs():
    if 'uid' in session:
        try:
            file = request.files['file']
            gid = request.form['gid']
            wb = xlrd.open_workbook(file_contents=file.read())
            sh = wb.sheet_by_index(0)
            for rownum in range(sh.nrows):
                name = sh.row_values(rownum)[0]
                email = sh.row_values(rownum)[1]
                uid = f.createStudentAccount(name,email)
                f.add_user_to_group(gid, uid)
            flash('Student Accounts Created','success') 
            return jsonify({'msg':'Success'})
        except:
            flash('Student Accounts Not Created','danger') 
            return jsonify({'msg':'Error'})
    return redirect('/')

@app.route("/createstudentaccount", methods=['GET', 'POST'])
def create_student_acc():
    if 'uid' in session:
        try:
            sname = request.get_json()['sname']
            semail = request.get_json()['semail']
            gid = request.get_json()['gid']
            uid = f.createStudentAccount(sname,semail)
            f.add_user_to_group(gid, uid)
            flash('Student Account Created','success') 
            return jsonify({'msg':'Success'})
        except:
            flash('Student Account Not Created','danger') 
            return jsonify({'msg':'Error'})
    return redirect('/')

@app.route("/createfacultyaccounts", methods=['GET', 'POST'])
def create_faculty_accs():
    if 'uid' in session:
        try:
            file = request.files['file']
            #gid = request.form['gid']
            cid = 'nI0YgLsFnP49zRQrvMaP'
            wb = xlrd.open_workbook(file_contents=file.read())
            sh = wb.sheet_by_index(0)
            for rownum in range(sh.nrows):
                name = sh.row_values(rownum)[0]
                email = sh.row_values(rownum)[1]
                uid = f.createFacultyAccount(name,email,cid)       
            flash('Faculty Accounts Created','success') 
            return jsonify({'msg':'Success'})
        except:
            flash('Faculty Accounts Not Created','danger') 
            return jsonify({'msg':'Error'})
    return redirect('/')

@app.route("/createfacultyaccount", methods=['GET', 'POST'])
def create_faculty_acc():
    if 'uid' in session:
        try:
            fname = request.get_json()['fname']
            femail = request.get_json()['femail']
            cid = session['uid']
            uid = f.createFacultyAccount(fname,femail,cid)
            flash('Faculty Account Created','success') 
            return jsonify({'msg':'Success'})
        except:
            flash('Faculty Account Not Created','danger') 
            return jsonify({'msg':'Error'})
    return redirect('/')

@app.route("/addtochannel", methods=['GET', 'POST'])
def add_to_channel():
    if 'uid' in session:
        selected = request.get_json()['selected']
        gid = request.get_json()['gid']
        cid = request.get_json()['cid']
        try:
            for i in selected:
                f.add_user_to_channel(gid,cid,i)
            flash('Student(s) Added to Course', 'success')
            return jsonify({'msg':'Success'})
        except:
            return jsonify({'msg':'Error'})
    return redirect('/')


@app.route('/<gid>')
def gotogroup(gid):
    if 'uid' in session:
        gname = f.get_group_data(gid).to_dict()['name']
        group_members = f.get_member_data_from_group(gid)
        members = []
        for i in group_members:
            d = {}
            d['uid'], d['email'], d['name'] = i['uid'], i['email'], i['name']
            members.append(d)
        group_channels = f.get_channels_from_group(gid)

        channels = []
        for i in group_channels:
            d = {}
            d['cid'], d['name'] = i.id, i.to_dict()['name']
            channels.append(d)

        cid = 'nI0YgLsFnP49zRQrvMaP'
        faculty = []
        for i in f.getFacultiesFromCollege(cid):
            d = i.to_dict()
            d['uid'] = i.id
            faculty.append(d)

        return render_template('group.html',gid=gid, gname=gname, members=members, channels=channels, faculty=faculty)
    return redirect('/')

@app.route('/<gid>/<cid>')
def gotocourse(gid, cid):
    if 'uid' in session:
        cname = f.get_channel_data(gid, cid).to_dict()['name']
        gname = f.get_group_data(gid).to_dict()['name']

        channel_members = []
        channel_members_uid = []
        for i in f.get_member_data_from_channel(gid, cid):
            d = {}
            d['uid'], d['name'], d['email'] = i['uid'], i['name'], i['email']
            channel_members.append(d)
            channel_members_uid.append(i['uid'])
    
        other_members = []
        for i in f.get_member_data_from_group(gid):
            d = {}
            if i['uid'] not in channel_members_uid:
                d['uid'], d['name'], d['email'] = i['uid'], i['name'], i['email']
                other_members.append(d)

        return render_template('course.html',gid=gid,cid=cid,gname=gname,cname=cname,other_members=other_members,channel_members=channel_members)
    return redirect('/')

if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=5000, debug=True)
