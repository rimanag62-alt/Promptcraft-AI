from django import forms


class PromptForm(forms.Form):
    CATEGORY_CHOICES = [
        ('Management', 'Management System'),
        ('Productivity', 'Productivity & Planning'),
        ('Utility', 'Utility & Tool'),
        ('Education', 'Education & Learning'),
        ('General', 'General Web Application'),
    ]

    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Give your app a title (optional, AI can auto-title)'
        })
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        initial='Management',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    prompt = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 4,
            'placeholder': 'Describe what you want to build in detail...\nExample: "Build an Attendance Management System with student enrollment, mark present/absent with date selector, statistics chart, and CSV export."'
        }),
        min_length=10,
        required=True
    )
