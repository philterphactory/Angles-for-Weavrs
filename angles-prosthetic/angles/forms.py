from django import forms

from django.core.exceptions import ValidationError

def validate_hexcolour(value):
    if len([char for char in value if char.lower() in '0123456789abcdef']) != 6:
        raise ValidationError(u'%s is not a six-digit hex colour' % value)

class ConfigForm(forms.Form):
    transparent_background = forms.BooleanField(required=False)
    background_colour = forms.CharField(required=False, max_length=6, validators=[validate_hexcolour], help_text='A six-figure hexadecimal colour, e.g. 2299AA')
