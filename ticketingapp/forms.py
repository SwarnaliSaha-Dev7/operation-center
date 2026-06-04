from django import forms

from ticketingapp.models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'priority', 'category')
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500',
                    'placeholder': 'Short summary of the issue',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'rows': 6,
                    'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500',
                    'placeholder': 'Describe the problem, steps to reproduce, what you expected…',
                }
            ),
            'priority': forms.Select(
                attrs={
                    'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500',
                }
            ),
            'category': forms.TextInput(
                attrs={
                    'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500',
                    'placeholder': 'e.g. Software, VPN, Email',
                }
            ),
        }


class TicketCommentForm(forms.Form):
    body = forms.CharField(
        label='Message',
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500',
                'placeholder': 'Add feedback or an update…',
            }
        ),
    )
    is_internal = forms.BooleanField(
        required=False,
        label='Internal note (IT only)',
        widget=forms.CheckboxInput(
            attrs={'class': 'rounded border-slate-300 text-indigo-600 focus:ring-indigo-500'}
        ),
    )
