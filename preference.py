from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SubmitField
from wtforms.validators import DataRequired


# Define the available news types
news_types = ['Sports', 'Politics', 'Science', 'Entertainment', 'Business', 'Technology', 'World']

class NewsPreferenceForm(FlaskForm):
    preferences = SelectMultipleField('News Preferences', choices=[(nt, nt) for nt in news_types], validators=[DataRequired()])
    submit = SubmitField('Save Preferences')

class ClearNewsPreferenceForm(FlaskForm):
    clear = SubmitField("Clear Preferences")

class ClearRelevantArticlesForm(FlaskForm):
    clear = SubmitField('Clear Relevant Articles')
