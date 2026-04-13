from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class PortfolioForm(FlaskForm):
    """Form for creating a new portfolio."""
    name = StringField('Portfolio Name',
                      validators=[DataRequired(message="Portfolio name is required."),
                                Length(min=1, max=200, message="Portfolio name must be between 1 and 200 characters.")],
                      render_kw={"placeholder": "Enter portfolio name", "class": "form-control"})

    description = TextAreaField('Description',
                               validators=[Optional(), Length(max=1000, message="Description must be less than 1000 characters.")],
                               render_kw={"placeholder": "Brief description of the portfolio (optional)",
                                        "rows": "3",
                                        "class": "form-control"})

    submit = SubmitField('Create Portfolio', render_kw={"class": "btn btn-primary"})


class PortfolioEditForm(FlaskForm):
    """Form for editing an existing portfolio."""
    name = StringField('Portfolio Name',
                      validators=[DataRequired(message="Portfolio name is required."),
                                Length(min=1, max=200, message="Portfolio name must be between 1 and 200 characters.")],
                      render_kw={"placeholder": "Enter portfolio name", "class": "form-control"})

    description = TextAreaField('Description',
                               validators=[Optional(), Length(max=1000, message="Description must be less than 1000 characters.")],
                               render_kw={"placeholder": "Brief description of the portfolio (optional)",
                                        "rows": "3",
                                        "class": "form-control"})

    submit = SubmitField('Update Portfolio', render_kw={"class": "btn btn-primary"})


class PropertyAssignmentForm(FlaskForm):
    """Form for assigning a property to a portfolio."""
    property_uuid = StringField('Property',
                               validators=[DataRequired(message="Property selection is required.")],
                               widget=HiddenField())

    submit = SubmitField('Assign Property', render_kw={"class": "btn btn-success btn-sm"})


class PropertyRemovalForm(FlaskForm):
    """Form for removing a property from a portfolio."""
    property_uuid = StringField('Property',
                               validators=[DataRequired(message="Property selection is required.")],
                               widget=HiddenField())

    submit = SubmitField('Remove Property', render_kw={"class": "btn btn-danger btn-sm"})


class PortfolioDeleteForm(FlaskForm):
    """Form for deleting a portfolio."""
    submit = SubmitField('Delete Portfolio', render_kw={"class": "btn btn-danger"})
