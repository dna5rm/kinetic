from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Fieldset, Submit, Div

class CheckListRow(forms.Form):
    c1 = forms.BooleanField(
        label='Check email from last shift and make sure none are pending network reply/assistance.',
        required=True,
        )
    c1_comment = forms.CharField(
        label='Comment',
        required=False,
        )
    c2 = forms.BooleanField(
        label='Check real time monitor and address any down host that is not already in progress.',
        required=True,
        )
    c2_comment = forms.CharField(
        label='Comment',
        required=False,
        )
    c3 = forms.BooleanField(
        label='Check any cacti alerts/emails make sure nothing out of the norm.',
        required=True,
        )
    c3_comment = forms.CharField(
        label='Comment',
        required=False,
        )
    c4 = forms.BooleanField(
        label='Check steelhead alerts/emails and address any that might need attention.',
        required=True,
        )
    c4_comment = forms.CharField(
        label='Comment',
        required=False,
        )
    c5 = forms.BooleanField(
        label='Check Velocloud main page for any alerts or down lines.',
        required=True,
        )
    c5_comment = forms.CharField(
        label='Comment',
        required=False,
        )
    c6 = forms.BooleanField(
        label='Check any Rbping alerts pending to be addressed.',
        required=True,
        )
    c6_comment = forms.CharField(
        label='Comment',
        required=False,
        )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Fieldset('These steps will be completed twice a day. <br \>\
                          Once via MNL shift and once via NA shift (EU will cover MNL if a holiday).'
                ),
                Div(
                    'c1',
                    'c1_comment',
                    css_class='form-control'
                ),
                HTML('''<br \>'''),
                Div(
                    'c2',
                    'c2_comment',
                    css_class='form-control'
                ),
                HTML('''<br \>'''),
                Div(
                    'c3',
                    'c3_comment',
                    css_class='form-control'
                ),
                HTML('''<br \>'''),
                Div(
                    'c4',
                    'c4_comment',
                    css_class='form-control'
                ),
                HTML('''<br \>'''),
                Div(
                    'c5',
                    'c5_comment',
                    css_class='form-control'
                ),
                HTML('''<br \>'''),
                Div(
                    'c6',
                    'c6_comment',
                    css_class='form-control'
                ),
                HTML('''<br \>'''),
                Submit('submit', 'Submit'),
                css_class='container'
            )
        )
        super(CheckListRow, self).__init__(*args, **kwargs)
        