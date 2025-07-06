from flask import Flask, render_template, request, redirect
from models import db, Device
from datetime import datetime
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models import User  # لو عندك موديل User
import pandas as pd
from flask import send_file
from datetime import datetime




app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # أو أي كلمة سر عشوائية
def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("يجب تسجيل الدخول أولًا", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    from models import User
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin", approved=True)
        admin.set_password("1234")
        db.session.add(admin)
        db.session.commit()


@app.route('/export')
def export_devices():
    devices = Device.query.all()
    data = []
    for d in devices:
        data.append({
            'العميل': d.client_name,
            'الهاتف': d.client_phone,
            'نوع الجهاز': d.device_type,
            'السيريال': d.serial,
            'المشكلة': d.issue,
            'مشتملات': d.inclusions,
            'الحالة': d.status,
            'التكلفة': d.cost,
            'استلام': d.received_date,
            'تسليم': d.delivered_date,
            'ملاحظات': d.notes,
        })

    df = pd.DataFrame(data)
    file_path = 'devices_export.xlsx'
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)




from datetime import datetime

@app.route('/export-by-date', methods=['GET', 'POST'])
def export_by_date():
    if request.method == 'POST':
        start = request.form['start_date']
        end = request.form['end_date']

        # نحول التواريخ إلى datetime للمقارنة
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        # فلترة الأجهزة حسب تاريخ الاستلام
        devices = Device.query.all()
        filtered = []
        for d in devices:
            if d.received_date:
                try:
                    r_date = datetime.strptime(d.received_date, "%Y-%m-%d")
                    if start_date <= r_date <= end_date:
                        filtered.append(d)
                except:
                    pass  # لو التاريخ مش مظبوط نتجاهله

        # نحول البيانات لجدول
        data = []
        for d in filtered:
            data.append({
                'العميل': d.client_name,
                'الهاتف': d.client_phone,
                'نوع الجهاز': d.device_type,
                'السيريال': d.serial,
                'المشكلة': d.issue,
                'مشتملات': d.inclusions,
                'الحالة': d.status,
                'التكلفة': d.cost,
                'استلام': d.received_date,
                'تسليم': d.delivered_date,
                'ملاحظات': d.notes,
            })

        df = pd.DataFrame(data)
        file_path = 'filtered_devices.xlsx'
        df.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True)

    return render_template('export_form.html')



@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('login'))






@app.route('/dashboard')
def dashboard():
    devices = Device.query.all()

    total_devices = len(devices)
    in_progress = len([d for d in devices if d.status == 'قيد الإصلاح'])
    repaired = len([d for d in devices if d.status == 'تم الإصلاح'])
    delivered = len([d for d in devices if d.status == 'تم التسليم'])
    total_cost = sum(d.cost for d in devices if d.cost)

    # حساب عدد الأجهزة المستلمة اليوم
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    today_received = len([d for d in devices if d.received_date == today])

    # إعداد البيانات للمخطط
    status_counts = {
        'قيد الإصلاح': in_progress,
        'تم الإصلاح': repaired,
        'تم التسليم': delivered
    }

    return render_template('dashboard.html',
                           total=total_devices,
                           in_progress=in_progress,
                           repaired=repaired,
                           delivered=delivered,
                           total_cost=total_cost,
                           today_received=today_received,
                           status_counts=status_counts)












@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('المستخدم غير موجود', 'error')
        elif not user.approved:
            flash('حسابك لم يتم تفعيله بعد', 'warning')
        elif not user.check_password(password):
            flash('كلمة المرور غير صحيحة', 'error')
        else:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/print/<int:device_id>')
def print_device(device_id):
    device = Device.query.get_or_404(device_id)
    return render_template('print_device.html', device=device)




@app.route('/')
@require_login
def index():
    filter_type = request.args.get('filter', 'all')
    devices = Device.query.all()

    # ⏰ تنبيهات
    reminders = []
    filtered_devices = []

    for device in devices:
        include = True

        if filter_type == 'pending':
            include = not device.delivered_date
        elif filter_type == 'late':
            if device.delivered_date:
                include = False
            else:
                try:
                    received = datetime.strptime(device.received_date, "%Y-%m-%d")
                    days = (datetime.now() - received).days
                    include = days >= 7
                except:
                    include = False

        if include:
            filtered_devices.append(device)

        # تنبيه دائم
        if not device.delivered_date:
            try:
                received = datetime.strptime(device.received_date, "%Y-%m-%d")
                days = (datetime.now() - received).days
                if days >= 7:
                    reminders.append({
                        'client': device.client_name,
                        'serial': device.serial,
                        'days': days
                    })
            except:
                pass

    return render_template('index.html', devices=filtered_devices, reminders=reminders)





@app.route('/add', methods=['GET', 'POST'])
def add_device():
    if request.method == 'POST':
        device = Device(
            serial=request.form['serial'],
            device_type=request.form['device_type'],
            client_name=request.form['client_name'],
            client_phone=request.form['client_phone'],
            issue=request.form['issue'],
                inclusions=request.form['inclusions'],  # ✅ الإضافة هنا

            received_date=datetime.now().strftime("%Y-%m-%d")
        )
        db.session.add(device)
        db.session.commit()
        return redirect('/')
    return render_template('add_device.html')

@app.route('/update/<int:device_id>', methods=['GET', 'POST'])
def update_device(device_id):
    device = Device.query.get(device_id)
    if request.method == 'POST':
        device.status = request.form['status']
        device.cost = float(request.form['cost'])
        device.notes = request.form['notes']
        device.delivered_date = datetime.now().strftime("%Y-%m-%d")
        db.session.commit()
        return redirect('/')
    return render_template('update_device.html', device=device)

@app.route('/search', methods=['GET', 'POST'])
def search():
    devices = []
    if request.method == 'POST':
        query = request.form['query']
        devices = Device.query.filter(
            (Device.serial.contains(query)) |
            (Device.client_name.contains(query))
        ).all()
    return render_template('search.html', devices=devices)

if __name__ == '__main__':
    app.run(debug=True)



