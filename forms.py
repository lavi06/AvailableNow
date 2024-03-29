from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, BooleanField
from wtforms.validators import DataRequired, Optional, InputRequired, ValidationError
from wtforms import DateTimeField

duration_choices = [("30", "30"), ("60", "60"), ("90", "90"), ("120", "120"), ("180", "180"),
                    ("240", "240"), ("360", "360"), ("480", "480"), ("720", "720"),
                    ("1440", "1440"), ("2880", "2880")]

hour_choices = [('12:00 AM', '12:00 AM'), ('12:15 AM', '12:15 AM'), ('12:30 AM', '12:30 AM'), ('12:45 AM', '12:45 AM'),
                ('01:00 AM', '01:00 AM'), ('01:15 AM', '01:15 AM'), ('01:30 AM', '01:30 AM'), ('01:45 AM', '01:45 AM'),
                ('02:00 AM', '02:00 AM'), ('02:15 AM', '02:15 AM'), ('02:30 AM', '02:30 AM'), ('02:45 AM', '02:45 AM'),
                ('03:00 AM', '03:00 AM'), ('03:15 AM', '03:15 AM'), ('03:30 AM', '03:30 AM'), ('03:45 AM', '03:45 AM'),
                ('04:00 AM', '04:00 AM'), ('04:15 AM', '04:15 AM'), ('04:30 AM', '04:30 AM'), ('04:45 AM', '04:45 AM'),
                ('05:00 AM', '05:00 AM'), ('05:15 AM', '05:15 AM'), ('05:30 AM', '05:30 AM'), ('05:45 AM', '05:45 AM'),
                ('06:00 AM', '06:00 AM'), ('06:15 AM', '06:15 AM'), ('06:30 AM', '06:30 AM'), ('06:45 AM', '06:45 AM'),
                ('07:00 AM', '07:00 AM'), ('07:15 AM', '07:15 AM'), ('07:30 AM', '07:30 AM'), ('07:45 AM', '07:45 AM'),
                ('08:00 AM', '08:00 AM'), ('08:15 AM', '08:15 AM'), ('08:30 AM', '08:30 AM'), ('08:45 AM', '08:45 AM'),
                ('09:00 AM', '09:00 AM'), ('09:15 AM', '09:15 AM'), ('09:30 AM', '09:30 AM'), ('09:45 AM', '09:45 AM'),
                ('10:00 AM', '10:00 AM'), ('10:15 AM', '10:15 AM'), ('10:30 AM', '10:30 AM'), ('10:45 AM', '10:45 AM'),
                ('11:00 AM', '11:00 AM'), ('11:15 AM', '11:15 AM'), ('11:30 AM', '11:30 AM'), ('11:45 AM', '11:45 AM'),
                ('12:00 PM', '12:00 PM'), ('12:15 PM', '12:15 PM'), ('12:30 PM', '12:30 PM'), ('12:45 PM', '12:45 PM'),
                ('01:00 PM', '01:00 PM'), ('01:15 PM', '01:15 PM'), ('01:30 PM', '01:30 PM'), ('01:45 PM', '01:45 PM'),
                ('02:00 PM', '02:00 PM'), ('02:15 PM', '02:15 PM'), ('02:30 PM', '02:30 PM'), ('02:45 PM', '02:45 PM'),
                ('03:00 PM', '03:00 PM'), ('03:15 PM', '03:15 PM'), ('03:30 PM', '03:30 PM'), ('03:45 PM', '03:45 PM'),
                ('04:00 PM', '04:00 PM'), ('04:15 PM', '04:15 PM'), ('04:30 PM', '04:30 PM'), ('04:45 PM', '04:45 PM'),
                ('05:00 PM', '05:00 PM'), ('05:15 PM', '05:15 PM'), ('05:30 PM', '05:30 PM'), ('05:45 PM', '05:45 PM'),
                ('06:00 PM', '06:00 PM'), ('06:15 PM', '06:15 PM'), ('06:30 PM', '06:30 PM'), ('06:45 PM', '06:45 PM'),
                ('07:00 PM', '07:00 PM'), ('07:15 PM', '07:15 PM'), ('07:30 PM', '07:30 PM'), ('07:45 PM', '07:45 PM'),
                ('08:00 PM', '08:00 PM'), ('08:15 PM', '08:15 PM'), ('08:30 PM', '08:30 PM'), ('08:45 PM', '08:45 PM'),
                ('09:00 PM', '09:00 PM'), ('09:15 PM', '09:15 PM'), ('09:30 PM', '09:30 PM'), ('09:45 PM', '09:45 PM'),
                ('10:00 PM', '10:00 PM'), ('10:15 PM', '10:15 PM'), ('10:30 PM', '10:30 PM'), ('10:45 PM', '10:45 PM'),
                ('11:00 PM', '11:00 PM'), ('11:15 PM', '11:15 PM'), ('11:30 PM', '11:30 PM'), ('11:45 PM', '11:45 PM')]


# print(hour_choices)


class InitialForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])


class CreateForm(FlaskForm):
    country = StringField('Country', validators=[DataRequired()])
    country_id = IntegerField('Country ID', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    state_id = IntegerField('State ID', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    city_id = IntegerField('City ID', validators=[DataRequired()])

    visiting = BooleanField('Visiting')

    show_reviews  = BooleanField('Show Reviews')
    show_website  = BooleanField('Show Website')

    face_time     = BooleanField('Face Time')
    private_calls = BooleanField('Private Calls')
    specials      = BooleanField('Specials')
    cancellation_policy = BooleanField('Cancellation Policy')
    private_text = BooleanField('Private Text')
    two_girls    = BooleanField('Two Girls')
    menu         = BooleanField('Menu')
    skype        = BooleanField('Skype')

    show_photos = BooleanField('Show Photos')

    ### Conditional Required Fields
    by_request = SelectField('By Request', choices=[('ASK', 'Ask Me'), ('RATES', 'The Donation Entered Below'),
                                                    ('WEBSITE', 'See Website')], validators=[DataRequired()])

    currency = SelectField('Currency',
                           choices=[('USD', 'USD'), ('CAD', 'CAD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('AED', 'AED'),
                                    ('INR', 'INR')],
                           validators=[Optional()])
    donation_1 = IntegerField('Donation 1', validators=[Optional()])
    donation_1_duration = SelectField('Donation 1 Duration',
                                      choices=duration_choices,
                                      validators=[Optional()])

    donation_2 = IntegerField('Donation 2', validators=[Optional()])
    donation_2_duration = SelectField('Donation 2 Duration',
                                      choices=duration_choices,
                                      validators=[Optional()])

    in_calls = BooleanField('I do Incalls?')
    out_calls = BooleanField('I do Outcalls?')

    sub_city_id = StringField('Sub City ID', validators=[Optional()])
    sub_city = StringField('Sub City', validators=[Optional()])

    today_anytime = SelectField('Anytime/ Specific Time', choices=["0", "1"], validators=[DataRequired()])

    # if today_anytime.data == "0":
    today_available_to = SelectField('Today Available To',
                                     choices=hour_choices,
                                     validators=[Optional()])
    today_available_from = SelectField('Today Available From',
                                       choices=hour_choices,
                                       validators=[Optional()])

    def validate(self, extra_validators=None):
        if not super(CreateForm, self).validate():
            return False

        if self.by_request.data == 'RATES':
            if not self.currency.data:
                if not hasattr(self.currency, 'errors'):
                    self.currency.errors = []
                self.currency.errors.append('Currency is required.')
                return False
            if not self.donation_1.data:
                if not hasattr(self.donation_1, 'errors'):
                    self.donation_1.errors = []
                self.donation_1.errors.append('Donation 1 is required.')
                return False
            if not self.donation_1_duration.data:
                if not hasattr(self.donation_1_duration, 'errors'):
                    self.donation_1_duration.errors = []
                self.donation_1_duration.errors.append('Donation 1 Duration is required.')
                return False
            if not self.donation_2.data:
                if not hasattr(self.donation_2, 'errors'):
                    self.donation_2.errors = []
                self.donation_2.errors.append('Donation 2 is required.')
                return False
            if not self.donation_2_duration.data:
                if not hasattr(self.donation_2_duration, 'errors'):
                    self.donation_2_duration.errors = []
                self.donation_2_duration.errors.append('Donation 2 Duration is required.')
                return False

        if self.today_anytime.data == "0" and self.today_anytime.data:
            flag = True
            if not self.today_available_from.data:
                if not hasattr(self.today_available_from, 'errors'):
                    self.today_available_from.errors = []
                self.today_available_from.errors.append('Specific Time : Start Time is required.')
                flag = False
            if not self.today_available_to.data:
                if not hasattr(self.today_available_to, 'errors'):
                    self.today_available_to.errors = []
                self.today_available_to.errors.append('Specific Time : End Time is required.')
                flag = False
            return flag

        if not self.in_calls.data and not self.out_calls.data:
            if not hasattr(self.out_calls, 'errors'):
                self.out_calls.errors = []
            self.out_calls.errors.append('Please select either incalls or outcalls')
            return False

        # if self.in_calls.data:
        #     if self.out_calls.data:
        #         if not hasattr(self.out_calls, 'errors'):
        #             self.out_calls.errors = []
        #         self.out_calls.errors.append('out_calls is need to be false, if in calls is set to true.')
        #         return False

        return True


class ScheduleForm(CreateForm):
    username = StringField('username', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])

    schedule_at = DateTimeField('schedule_at', validators=[DataRequired()], format='%Y-%m-%d %H:%M:%S')
    ending_at = DateTimeField('ending time', validators=[DataRequired()], format='%Y-%m-%d %H:%M:%S')

    local_schedule_at = DateTimeField('local_schedule_at', validators=[DataRequired()], format='%Y-%m-%d %H:%M:%S')
    local_ending_at = DateTimeField('local_ending_at', validators=[DataRequired()], format='%Y-%m-%d %H:%M:%S')

    refreshing = IntegerField('refreshing time in min', validators=[InputRequired()])
    refreshing_2 = IntegerField('refreshing time-2 in min', validators=[InputRequired()])

    def validate_ending_at(self, field):
        if self.schedule_at.data and field.data:
            if field.data <= self.schedule_at.data:
                raise ValidationError('Start Time should be less than End Time')


