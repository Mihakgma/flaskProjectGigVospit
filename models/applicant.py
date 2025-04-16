# from database import db
# from sqlalchemy import ForeignKey, event, Text
# from sqlalchemy.types import String, Integer, Boolean, DateTime
#
#
# class ApplicantType(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(String(10), nullable=False)
#     additional_info = db.Column(Text)
#
#
# class Organization(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(String(200), nullable=False)
#     inn = db.Column(String(12))  # 10 или 12 цифр для РФ
#     address = db.Column(String(200))
#     phone_number = db.Column(String(20))
#     email = db.Column(String(120))
#     is_active = db.Column(Boolean, nullable=False)
#     additional_info = db.Column(Text)
#
#
# class Contract(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     number = db.Column(String(50), nullable=False)
#     contract_date = db.Column(DateTime, nullable=False)
#     name = db.Column(Text)
#     expiration_date = db.Column(DateTime)
#     is_extended = db.Column(Boolean, nullable=False)
#     organization_id = db.Column(Integer, ForeignKey('organization.id'))
#     additional_info = db.Column(Text)
#
#
# class WorkField(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(String(100), nullable=False)
#     additional_info = db.Column(Text)
#
#
# # Вспомогательная таблица для связи Many-to-Many между Applicant и Contract
# applicant_contract = db.Table(
#     'applicant_contract',
#     db.Column('applicant_id', db.Integer, db.ForeignKey('applicant.id'), primary_key=True),
#     db.Column('contract_id', db.Integer, db.ForeignKey('contract.id'), primary_key=True)
# )
#
#
# class Applicant(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     first_name = db.Column(String(80), nullable=False)
#     last_name = db.Column(String(80), nullable=False)
#     middle_name = db.Column(String(80))
#     medbook_number = db.Column(String(50))
#     snils_number = db.Column(String(14))  # 11 цифр + 3 разделителя
#     passport_number = db.Column(String(20))  # 10 цифр (или 4+6)
#     birth_date = db.Column(DateTime, nullable=False)
#     registration_address = db.Column(String(200))
#     residence_address = db.Column(String(200))
#     phone_number = db.Column(String(20))
#     email = db.Column(String(120))
#     contingent_id = db.Column(Integer, ForeignKey('contingent.id'), nullable=False)
#     work_field_id = db.Column(Integer, ForeignKey('work_field.id'), nullable=False)
#     applicant_type_id = db.Column(Integer, ForeignKey('applicant_type.id'), nullable=False)
#     attestation_type_id = db.Column(Integer, ForeignKey('attestation_type.id'), nullable=False)
#     edited_by_user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
#     edited_time = db.Column(DateTime, nullable=False)
#     is_editing_now = db.Column(Boolean, nullable=False)
#     editing_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
#     editing_started_at = db.Column(DateTime, nullable=False)
#     contracts = db.relationship('Contract', secondary=applicant_contract, backref='applicants')
#
# @event.listens_for(Applicant, 'mapper_configured')
# def create_applicant_contract_table(mapper, class_):
#     applicant_contract.create(db.engine, checkfirst=True)
