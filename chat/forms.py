from decimal import Decimal

from django import forms


class PaymentRequestForm(forms.Form):
    """Validates the data of a 'payment' WebSocket action."""
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    currency = forms.ChoiceField(choices=[('EUR', 'EUR'), ('USD', 'USD'), ('GBP', 'GBP')])

    def clean_amount(self):
        # 50 and 1e2 become 50.00 and 100.00, the same as after a reload
        return self.cleaned_data['amount'].quantize(Decimal('0.01'))
