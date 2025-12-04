from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed


class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    instructions = TextAreaField('Instructions', validators=[Optional()])
    ingredients = TextAreaField('Ingredients (JSON list or newline separated)', validators=[Optional()])
    category = StringField('Category', validators=[Optional(), Length(max=80)])
    cooking_time = IntegerField('Cooking time (minutes)', validators=[Optional(), NumberRange(min=0)])
    servings = IntegerField('Servings', validators=[Optional(), NumberRange(min=1)])
    image = FileField('Image', validators=[FileAllowed(['jpg','jpeg','png','gif'], 'Images only!')])
    submit = SubmitField('Save')
