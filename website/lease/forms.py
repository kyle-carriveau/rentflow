from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, IntegerField
from wtforms.validators import DataRequired

class LeaseForm(FlaskForm):
    tenant = SelectField('Tenant', validators=[DataRequired()])
    unit = SelectField('Unit', validators=[DataRequired()])
    start = DateField('Start Date', validators=[DataRequired()])
    end = DateField('End Date', validators=[DataRequired()])
    rent = IntegerField('Rent', validators=[DataRequired()])