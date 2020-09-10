from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import Lead

def phone_check(form, field):
    '''
    Custom validator that raises a ValidationError if there are non-numeric characters.
    '''
    numbers = ['0','1','2','3','4','5','6','7','8','9']
    for character in str(field.data):
        if character == '-':
            raise ValidationError("We're expecting something like 1112223333, not 111-222-3333.")
        elif character not in numbers:
            raise ValidationError('Numbers only, please.')

class UsSaleForm(FlaskForm):
    client_name = StringField("Company's legal name", validators=[DataRequired(), Length(max=100)])
    client_street_address = StringField('Street address', validators=[DataRequired(), Length(max=100)])
    client_city = StringField('City', validators=[DataRequired(), Length(max=60)])
    client_state = SelectField('State', choices=[
        ('Alabama','Alabama'),
        ('Alaska', 'Alaska'),
        ('Arizona', 'Arizona'),
        ('Arkansas', 'Arkansas'),
        ('California', 'California'),
        ('Colorado', 'Colorado'),
        ('Connecticut', 'Connecticut'),
        ('District of Columbia', 'District of Columbia'),
        ('Delaware', 'Delaware'),
        ('Florida', 'Florida'),
        ('Georgia', 'Georgia'),
        ('Hawaii', 'Hawaii'),
        ('Idaho', 'Idaho'),
        ('Illinois', 'Illinois'),
        ('Indiana', 'Indiana'),
        ('Iowa', 'Iowa'),
        ('Kansas', 'Kansas'),
        ('Kentucky', 'Kentucky'),
        ('Louisiana', 'Louisiana'),
        ('Maine', 'Maine'),
        ('Maryland', 'Maryland'),
        ('Massachusetts', 'Massachusetts'),
        ('Michigan', 'Michigan'),
        ('Minnesota', 'Minnesota'),
        ('Mississippi', 'Mississippi'),
        ('Missouri', 'Missouri'),
        ('Nebraska', 'Nebraska'),
        ('Nevada', 'Nevada'),
        ('New Jersey', 'New Jersey'),
        ('New Mexico', 'New Mexico'),
        ('New York', 'New York'),
        ('North Carolina', 'North Carolina'),
        ('North Dakota', 'North Dakota'),
        ('Ohio', 'Ohio'),
        ('Oklahoma', 'Oklahoma'),
        ('Pennsylvania', 'Pennsylvania'),
        ('Rhode Island', 'Rhode Island'),
        ('South Carolina', 'South Carolina'),
        ('South Dakota', 'South Dakota'),
        ('Tennessee', 'Tennessee'),
        ('Texas', 'Texas'),
        ('Utah', 'Utah'),
        ('Vermont', 'Vermont'),
        ('Virginia', 'Virginia'),
        ('Washington', 'Washington'),
        ('West Virginia', 'West Virginia'),
        ('Wisconsin', 'Wisconsin'),
        ('Wyoming', 'Wyoming'),
        ('Other', 'Other / not in the United States')
    ],
    validators=[DataRequired()])
    client_zip = StringField('ZIP code', validators=[DataRequired(), Length(max=15)])
    contact_name = StringField('Your legal name', validators=[DataRequired(), Length(max=100)])
    client_phone = StringField('Contact phone number', validators=[DataRequired(), Length(min=10, max=10), phone_check])
    client_email = StringField('Contact email', validators=[DataRequired(), Email(), Length(max=120)])
    service_agreement = BooleanField('Checking this box signals my intent to sign the Service Agreement.', validators=[DataRequired()])
    submit = SubmitField('Next >>')


class ChinaSaleForm(FlaskForm):
    client_name = StringField("公司名称", validators=[DataRequired(message='这是必填栏。'), Length(max=100)])
    client_state = SelectField('省/地区', choices=[
        ('安徽省', '安徽省'),
        ('北京市', '北京市'),
        ('重庆市', '重庆市'),
        ('福建省', '福建省'),
        ('广东省', '广东省'),
        ('甘肃省', '甘肃省'),
        ('广西壮族自治区', '广西壮族自治区'),
        ('贵州省', '贵州省'),
        ('河南省', '河南省'),
        ('湖北省', '湖北省'),
        ('河北省', '河北省'),
        ('海南省', '海南省'),
        ('香港特别行政区', '香港特别行政区'),
        ('黑龙江省', '黑龙江省'),
        ('湖南省', '湖南省'),
        ('吉林省', '吉林省'),
        ('江苏省', '江苏省'),
        ('江西省', '江西省'),
        ('辽宁省', '辽宁省'),
        ('澳门特别行政区', '澳门特别行政区'),
        ('内蒙古自治区', '内蒙古自治区'),
        ('宁夏回族自治区', '宁夏回族自治区'),
        ('青海省', '青海省'),
        ('四川省', '四川省'),
        ('山东省', '山东省'),
        ('上海市', '上海市'),
        ('陕西省', '陕西省'),
        ('山西省', '山西省'),
        ('天津市', '天津市'),
        ('台湾省', '台湾省'),
        ('新疆维吾尔自治区', '新疆维吾尔自治区'),
        ('西藏自治区', '西藏自治区'),
        ('云南省', '云南省'),
        ('浙江省', '浙江省')
    ], validators=[DataRequired(message='这是必填栏。')])
    client_city = StringField('城市/市区', validators=[DataRequired(message='这是必填栏。'), Length(max=60)])
    client_street_address = StringField('详细地址', validators=[DataRequired(message='这是必填栏。'), Length(max=100)])
    client_zip = StringField('邮政编码', validators=[DataRequired(), Length(max=15)])
    contact_name = StringField('联系人姓名', validators=[DataRequired(), Length(max=100)])
    client_phone = StringField('电话号码', validators=[DataRequired(), Length(min=10, max=10), phone_check])
    client_email = StringField('电子邮箱', validators=[DataRequired(), Email(), Length(max=120)])
    service_agreement = BooleanField('选中此框表示我愿意签署《IcyFire 服务协议》。', validators=[DataRequired()])
    submit = SubmitField('下一步 >>')