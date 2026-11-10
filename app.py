from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, make_response
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import csv, io, json, os, secrets

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)
FEEDBACK_FILE = DATA_DIR / 'feedback.json'
STUDENTS_FILE = DATA_DIR / 'students.json'
ACADEMIC_FILE = DATA_DIR / 'academic.json'
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
ON_VERCEL = bool(os.environ.get('VERCEL'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=bool(ON_VERCEL), PERMANENT_SESSION_LIFETIME=__import__('datetime').timedelta(hours=8))
QUESTIONS = ['How clearly are the subject concepts explained?', 'How effective are the teaching methods and examples?', 'How well does the course content match the syllabus?', 'How helpful are the assignments, practicals, and learning materials?', 'Overall, how satisfied are you with this course?']
BRANCHES = {'CSE':'Computer Science and Engineering','ECE':'Electronics and Communication Engineering','EEE':'Electrical and Electronics Engineering','MECH':'Mechanical Engineering','CIVIL':'Civil Engineering','IT':'Information Technology','AIML':'Artificial Intelligence and Machine Learning','DS':'Data Science'}


def default_academic():
    catalog = {
      'CSE':['Engineering Mathematics','Engineering Physics','Programming for Problem Solving','Basic Electrical Engineering','Engineering Graphics','Data Structures','Digital Logic Design','Discrete Mathematics','Object Oriented Programming','Computer Organization','Database Management Systems','Operating Systems','Computer Networks','Software Engineering','Theory of Computation','Design and Analysis of Algorithms','Compiler Design','Web Technologies','Machine Learning','Cloud Computing'],
      'ECE':['Engineering Mathematics','Engineering Physics','Basic Electrical Engineering','Electronic Devices','Network Analysis','Signals and Systems','Analog Electronic Circuits','Digital System Design','Electromagnetic Waves','Control Systems','Microprocessors','Communication Systems','VLSI Design','Digital Signal Processing','Microwave Engineering','Embedded Systems'],
      'EEE':['Engineering Mathematics','Engineering Physics','Basic Electrical Engineering','Circuit Theory','Electrical Machines','Electromagnetic Fields','Power Systems','Power Electronics','Control Systems','Electrical Measurements','Microprocessors','Renewable Energy Systems'],
      'MECH':['Engineering Mathematics','Engineering Physics','Engineering Mechanics','Engineering Graphics','Thermodynamics','Material Science','Fluid Mechanics','Manufacturing Technology','Theory of Machines','Heat Transfer','Machine Design','Industrial Engineering'],
      'CIVIL':['Engineering Mathematics','Engineering Physics','Engineering Mechanics','Engineering Graphics','Surveying','Building Materials','Strength of Materials','Fluid Mechanics','Structural Analysis','Geotechnical Engineering','Transportation Engineering','Environmental Engineering'],
      'IT':['Engineering Mathematics','Programming for Problem Solving','Data Structures','Digital Logic Design','Database Management Systems','Operating Systems','Computer Networks','Software Engineering','Web Technologies','Information Security'],
      'AIML':['Engineering Mathematics','Programming for Problem Solving','Data Structures','Probability and Statistics','Database Management Systems','Artificial Intelligence','Machine Learning','Deep Learning','Computer Vision','Natural Language Processing'],
      'DS':['Engineering Mathematics','Programming for Problem Solving','Data Structures','Probability and Statistics','Database Management Systems','Data Mining','Data Visualization','Machine Learning','Big Data Analytics','Deep Learning']}
    subjects=[]
    for branch, names in catalog.items():
        for sem in range(1,9):
            # distribute the catalog across semesters; all branches get a distinct subject list
            selected=names[(sem-1)*2:sem*2] or [f'{BRANCHES[branch]} Elective {sem}A',f'{BRANCHES[branch]} Elective {sem}B']
            for idx,name in enumerate(selected,1):
                code=f'{branch}{sem}{idx:02d}'
                subjects.append({'code':code,'name':name,'branch':branch,'semester':sem,'lecturer':'Not assigned','lecture_details':'Lecture schedule to be announced'})
    return subjects

def read_json(path, default):
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value,type(default)) else default
    except (OSError,ValueError): return default

def get_subjects():
    if not ACADEMIC_FILE.exists():
        save_subjects(default_academic())
    return read_json(ACADEMIC_FILE, [])
def save_subjects(rows): ACADEMIC_FILE.write_text(json.dumps(rows,indent=2),encoding='utf-8')
def get_students(): return read_json(STUDENTS_FILE,{})
def save_students(rows): STUDENTS_FILE.write_text(json.dumps(rows,indent=2),encoding='utf-8')

def db_conn():
    import psycopg
    return psycopg.connect(DATABASE_URL,connect_timeout=10,sslmode='require')
def ensure_db():
    if not DATABASE_URL: return
    with db_conn() as conn:
      with conn.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS course_feedback_submissions (
          feedback_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY, course_code VARCHAR(24) NOT NULL,
          course_name VARCHAR(180) NOT NULL, ratings SMALLINT[] NOT NULL, comment_optional VARCHAR(500) NOT NULL DEFAULT '',
          submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), student_id VARCHAR(100) NOT NULL DEFAULT '', branch VARCHAR(12) NOT NULL DEFAULT '',
          semester SMALLINT NOT NULL DEFAULT 1, lecturer VARCHAR(180) NOT NULL DEFAULT '', lecture_details VARCHAR(500) NOT NULL DEFAULT '')''')
        for col,typ in [('student_id',"VARCHAR(100) NOT NULL DEFAULT ''"),('branch',"VARCHAR(12) NOT NULL DEFAULT ''"),('semester','SMALLINT NOT NULL DEFAULT 1'),('lecturer',"VARCHAR(180) NOT NULL DEFAULT ''"),('lecture_details',"VARCHAR(500) NOT NULL DEFAULT ''")]:
          cur.execute(f'ALTER TABLE course_feedback_submissions ADD COLUMN IF NOT EXISTS {col} {typ}')
      conn.commit()

def load_feedback():
    if DATABASE_URL:
      ensure_db()
      with db_conn() as conn:
       with conn.cursor() as cur:
        cur.execute('SELECT feedback_id,course_code,course_name,ratings,comment_optional,submitted_at,student_id,branch,semester,lecturer,lecture_details FROM course_feedback_submissions ORDER BY feedback_id DESC')
        rows=cur.fetchall()
      return [dict(feedback_id=r[0],course_code=r[1],course_name=r[2],ratings=list(r[3]),comment=r[4] or '',submitted_at=r[5].isoformat() if r[5] else '',student_id=r[6],branch=r[7],semester=r[8],lecturer=r[9],lecture_details=r[10]) for r in rows]
    return read_json(FEEDBACK_FILE,[])
def save_feedback(rows):
    if not DATABASE_URL: FEEDBACK_FILE.write_text(json.dumps(rows,indent=2),encoding='utf-8')
def add_feedback(row):
    if DATABASE_URL:
      ensure_db()
      with db_conn() as conn:
       with conn.cursor() as cur:
        cur.execute('''INSERT INTO course_feedback_submissions(course_code,course_name,ratings,comment_optional,submitted_at,student_id,branch,semester,lecturer,lecture_details)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING feedback_id''',(row['course_code'],row['course_name'],row['ratings'],row['comment'],row['submitted_at'],row['student_id'],row['branch'],row['semester'],row['lecturer'],row['lecture_details']))
        row['feedback_id']=cur.fetchone()[0]
       conn.commit()
    else:
      rows=load_feedback(); row['feedback_id']=max([r.get('feedback_id',0) for r in rows],default=0)+1; rows.append(row); save_feedback(rows)

def student_required(fn):
 @wraps(fn)
 def wrapped(*a,**kw):
  if session.get('role')!='student': return redirect(url_for('student_login'))
  return fn(*a,**kw)
 return wrapped
def admin_required(fn):
 @wraps(fn)
 def wrapped(*a,**kw):
  if session.get('role')!='admin':
   if request.path.startswith('/api/'): return jsonify({'error':'Administrator access required.'}),403
   return redirect(url_for('admin_login'))
  return fn(*a,**kw)
 return wrapped

@app.get('/')
def home(): return render_template('home.html')
@app.route('/student/login',methods=['GET','POST'])
def student_login():
 if request.method=='POST':
  sid=request.form.get('student_id','').strip().lower(); password=request.form.get('password',''); branch=request.form.get('branch','').upper(); semester=request.form.get('semester','')
  if not sid or len(sid)>100 or len(password)<6 or branch not in BRANCHES or not semester.isdigit() or not 1<=int(semester)<=8:
   flash('Enter a valid student ID, password, branch and semester. Password must be at least 6 characters.','error')
  else:
   students=get_students(); existing=students.get(sid)
   if existing:
    if check_password_hash(existing['password_hash'],password) and existing['branch']==branch and existing['semester']==int(semester):
     session.clear(); session.update(role='student',student_id=sid,branch=branch,semester=int(semester)); session.permanent=True; return redirect(url_for('student_dashboard'))
    flash('Login details do not match your registered student account.','error')
   else:
    students[sid]={'password_hash':generate_password_hash(password),'branch':branch,'semester':int(semester)}; save_students(students)
    session.clear(); session.update(role='student',student_id=sid,branch=branch,semester=int(semester)); session.permanent=True; return redirect(url_for('student_dashboard'))
 return render_template('login.html',mode='student',branches=BRANCHES)
@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
 if request.method=='POST':
  login=request.form.get('login_id',''); password=request.form.get('password','')
  admin_id=os.environ.get('ADMIN_LOGIN_ID','admin'); admin_pw=os.environ.get('ADMIN_PASSWORD','Admin@12345')
  if secrets.compare_digest(login,admin_id) and secrets.compare_digest(password,admin_pw):
   session.clear(); session.update(role='admin',admin_id=admin_id); session.permanent=True; return redirect(url_for('admin_portal'))
  flash('Invalid administrator login ID or password.','error')
 return render_template('login.html',mode='admin',branches=BRANCHES)
@app.get('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.get('/student/dashboard')
@student_required
def student_dashboard():
 branch=session['branch']; sem=session['semester']; subjects=[s for s in get_subjects() if s['branch']==branch and s['semester']==sem]
 return render_template('index.html',courses=subjects,questions=QUESTIONS,student=session['student_id'],branch_name=BRANCHES[branch],semester=sem)
@app.get('/admin')
@admin_required
def admin_portal(): return render_template('admin.html',branches=BRANCHES,subjects=get_subjects(),questions=QUESTIONS)
@app.get('/api/student/subjects')
@student_required
def student_subjects():
 return jsonify([s for s in get_subjects() if s['branch']==session['branch'] and s['semester']==session['semester']])
@app.post('/api/feedback')
@student_required
def submit_feedback():
 payload=request.get_json(silent=True) or {}; code=str(payload.get('course_code','')).strip().upper(); subject=next((s for s in get_subjects() if s['code']==code and s['branch']==session['branch'] and s['semester']==session['semester']),None)
 ratings=payload.get('ratings'); comment=str(payload.get('comment','')).strip()
 if not subject: return jsonify({'error':'Please choose a subject from your assigned semester.'}),400
 if not isinstance(ratings,list) or len(ratings)!=5 or any(type(x)!=int or x<1 or x>5 for x in ratings): return jsonify({'error':'Please answer all five questions with ratings from 1 to 5.'}),400
 if len(comment)>500: return jsonify({'error':'Comments must be 500 characters or fewer.'}),400
 # One response per student per subject; the admin can still inspect the complete record.
 rows=load_feedback()
 if any(r.get('student_id')==session['student_id'] and r.get('course_code')==code for r in rows): return jsonify({'error':'You have already submitted feedback for this subject.'}),409
 add_feedback({'course_code':code,'course_name':subject['name'],'ratings':ratings,'comment':comment,'submitted_at':datetime.now(timezone.utc).isoformat(),'student_id':session['student_id'],'branch':subject['branch'],'semester':subject['semester'],'lecturer':subject.get('lecturer',''),'lecture_details':subject.get('lecture_details','')})
 return jsonify({'message':'Feedback submitted successfully. Thank you!'}),201
@app.get('/api/student/summary')
@student_required
def student_summary():
 rows=[r for r in load_feedback() if r.get('branch')==session['branch'] and r.get('semester')==session['semester']]
 courses=[]
 for s in get_subjects():
  if s['branch']==session['branch'] and s['semester']==session['semester']:
   group=[r for r in rows if r['course_code']==s['code']]; vals=[x for r in group for x in r['ratings']]
   courses.append({'code':s['code'],'name':s['name'],'responses':len(group),'average':round(sum(vals)/len(vals),2) if vals else 0,'submitted':any(r.get('student_id')==session['student_id'] for r in group)})
 vals=[x for r in rows for x in r['ratings']]
 return jsonify({'total_responses':len(rows),'total_ratings':len(vals),'overall_average':round(sum(vals)/len(vals),2) if vals else 0,'distribution':{str(i):sum(1 for x in vals if x==i) for i in range(1,6)},'courses':courses,'questions':QUESTIONS})

@app.get('/api/admin/feedback')
@admin_required
def admin_feedback():
 rows=load_feedback(); branch=request.args.get('branch',''); sem=request.args.get('semester',''); code=request.args.get('subject','')
 if branch: rows=[r for r in rows if r.get('branch')==branch]
 if sem: rows=[r for r in rows if str(r.get('semester'))==sem]
 if code: rows=[r for r in rows if r.get('course_code')==code]
 return jsonify(rows)
@app.get('/api/admin/summary')
@admin_required
def admin_summary():
 rows=load_feedback(); vals=[x for r in rows for x in r['ratings']]
 return jsonify({'total_responses':len(rows),'total_ratings':len(vals),'overall_average':round(sum(vals)/len(vals),2) if vals else 0,'branches':len(BRANCHES),'subjects':len(get_subjects())})
@app.post('/api/admin/subjects')
@admin_required
def create_subject():
 p=request.get_json(silent=True) or {}; branch=p.get('branch','').upper(); sem=p.get('semester'); name=str(p.get('name','')).strip(); lecturer=str(p.get('lecturer','')).strip(); details=str(p.get('lecture_details','')).strip()
 if branch not in BRANCHES or not isinstance(sem,int) or not 1<=sem<=8 or not name: return jsonify({'error':'Branch, semester (1–8) and subject name are required.'}),400
 rows=get_subjects(); code=''.join(c for c in branch if c.isalnum())+str(sem)+secrets.token_hex(2).upper()
 rows.append({'code':code,'name':name,'branch':branch,'semester':sem,'lecturer':lecturer,'lecture_details':details}); save_subjects(rows); return jsonify({'message':'Subject added.','subject':rows[-1]}),201
@app.put('/api/admin/subjects/<code>')
@admin_required
def update_subject(code):
 p=request.get_json(silent=True) or {}; rows=get_subjects(); subject=next((s for s in rows if s['code']==code),None)
 if not subject: return jsonify({'error':'Subject not found.'}),404
 for key in ['name','lecturer','lecture_details']:
  if key in p: subject[key]=str(p[key]).strip()
 if 'branch' in p and p['branch'] in BRANCHES: subject['branch']=p['branch']
 if 'semester' in p and isinstance(p['semester'],int) and 1<=p['semester']<=8: subject['semester']=p['semester']
 save_subjects(rows); return jsonify({'message':'Subject updated.','subject':subject})
@app.delete('/api/admin/subjects/<code>')
@admin_required
def delete_subject(code):
 rows=get_subjects(); new=[s for s in rows if s['code']!=code]
 if len(new)==len(rows): return jsonify({'error':'Subject not found.'}),404
 save_subjects(new); return jsonify({'message':'Subject removed.'})
@app.get('/api/admin/export.csv')
@admin_required
def admin_export():
 out=io.StringIO(); w=csv.writer(out); w.writerow(['Feedback ID','Student ID','Branch','Semester','Subject','Subject Code','Lecturer','Lecture Details','Ratings','Comment','Submitted At'])
 for r in load_feedback(): w.writerow([r.get('feedback_id'),r.get('student_id'),r.get('branch'),r.get('semester'),r.get('course_name'),r.get('course_code'),r.get('lecturer'),r.get('lecture_details'),','.join(map(str,r['ratings'])),r.get('comment'),r.get('submitted_at')])
 resp=make_response('\ufeff'+out.getvalue()); resp.headers['Content-Type']='text/csv; charset=utf-8'; resp.headers['Content-Disposition']='attachment; filename=admin_feedback_details.csv'; return resp
@app.get('/health')
def health(): return jsonify({'status':'ok','storage':'PostgreSQL' if DATABASE_URL else 'local JSON','database_configured':bool(DATABASE_URL)})
if __name__=='__main__': app.run(debug=os.environ.get('FLASK_DEBUG')=='1',host='127.0.0.1',port=int(os.environ.get('PORT','5000')))
