from django import forms

from django.core.exceptions import ValidationError

def validate_hexcolour(value):
    if len([char for char in value if char.lower() in '0123456789abcdef']) != 6 and value.lower() != 'transparent':
        raise ValidationError(u'%s is not a six-digit hex colour' % value)

class ConfigForm(forms.Form):
    background_colour = forms.CharField(required=True, max_length=11, validators=[validate_hexcolour], help_text='A six-figure hexadecimal colour, e.g. 2299AA. You could pick one <a href="http://www.colorpicker.com/" target="_new">from here</a>. Or say <i>transparent</i> for a transparent background.')
    kcore = forms.IntegerField(required=True, help_text='How much to strip down the graph.')
    font_name = forms.CharField(required=True)
    font_size = forms.IntegerField(required=True)
    colourlovers_palette_id = forms.IntegerField(required=False, help_text="The ID from a Colourlovers palette URL - e.g. 4182 for <a href='http://colourlovers.com/palette/4182/Ocean_Five'>www.colourlovers.com/palette/4182/Ocean_Five</a>")
