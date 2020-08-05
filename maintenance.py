from app import create_app, db
from app.models import TimeSlot

create_app().app_context().push()

slots = TimeSlot.query.all()

for slot in slots:
    db.session.delete(slot)
    db.session.commit()

m = TimeSlot(server_id=1, day_of_week=1, time='12:34')
tu = TimeSlot(server_id=1, day_of_week=2, time='12:34')
w = TimeSlot(server_id=1, day_of_week=3, time='12:34')
th = TimeSlot(server_id=1, day_of_week=4, time='12:34')
f = TimeSlot(server_id=1, day_of_week=5, time='12:34')
sa = TimeSlot(server_id=1, day_of_week=6, time='12:34')
su = TimeSlot(server_id=1, day_of_week=7, time='12:34')

db.session.add(m)
db.session.add(tu)
db.session.add(w)
db.session.add(th)
db.session.add(f)
db.session.add(sa)
db.session.add(su)
db.session.commit()