from django.contrib import admin
from django import forms
from .models import Voter, Candidate, Vote, VotingTime, Election
from django.utils import timezone
from django.contrib import messages

# Custom form for VotingTime
class VotingTimeForm(forms.ModelForm):
    start_time = forms.SplitDateTimeField(
        input_date_formats=['%Y-%m-%d', '%d/%m/%Y'],
        input_time_formats=['%H:%M'],
        widget=forms.SplitDateTimeWidget(date_attrs={'type': 'date'}, time_attrs={'type': 'time'})
    )
    end_time = forms.SplitDateTimeField(
        input_date_formats=['%Y-%m-%d', '%d/%m/%Y'],
        input_time_formats=['%H:%M'],
        widget=forms.SplitDateTimeWidget(date_attrs={'type': 'date'}, time_attrs={'type': 'time'})
    )

    class Meta:
        model = VotingTime
        fields = '_all_'

# Custom form for Election
class ElectionForm(forms.ModelForm):
    start_date = forms.SplitDateTimeField(
        input_date_formats=['%Y-%m-%d', '%d/%m/%Y'],
        input_time_formats=['%H:%M', '%H:%M:%S'],
        widget=forms.SplitDateTimeWidget(
            date_attrs={'type': 'date'},
            time_attrs={'type': 'time', 'step': '60'},
            date_format='%Y-%m-%d',
            time_format='%H:%M'
        ),
        label="Start Date and Time",
        help_text="Select the date and time for the election to start (format: HH:MM, e.g., 14:30 for 2:30 PM)."
    )
    end_date = forms.SplitDateTimeField(
        input_date_formats=['%Y-%m-%d', '%d/%m/%Y'],
        input_time_formats=['%H:%M', '%H:%M:%S'],
        widget=forms.SplitDateTimeWidget(
            date_attrs={'type': 'date'},
            time_attrs={'type': 'time', 'step': '60'},
            date_format='%Y-%m-%d',
            time_format='%H:%M'
        ),
        label="End Date and Time",
        help_text="Select the date and time for the election to end (format: HH:MM, e.g., 16:30 for 4:30 PM)."
    )

    class Meta:
        model = Election
        fields = '_all_'

    def _init_(self, *args, **kwargs):
        super()._init_(*args, **kwargs)
        if self.instance.pk:
            self.fields['start_date'].initial = self.instance.start_date
            self.fields['end_date'].initial = self.instance.end_date
            self.fields['published'].widget.attrs['readonly'] = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError("End date and time must be after start date and time.")
            cleaned_data['start_date'] = start_date
            cleaned_data['end_date'] = end_date

        return cleaned_data

# Custom filter for Election
class ElectionFilter(admin.SimpleListFilter):
    title = 'Election'
    parameter_name = 'election'

    def lookups(self, request, model_admin):
        elections = Election.objects.all()
        return [(election.id, election.name) for election in elections] + [(None, 'No Election')]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(election__isnull=True)
        if self.value():
            return queryset.filter(election__id=self.value())
        return queryset

@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('name', 'citizenship_id', 'email', 'gender', 'age', 'address')
    search_fields = ('name', 'email', 'citizenship_id')
    list_filter = ('gender', 'age')
    fieldsets = (
        ('Personal Information', {
            'fields': ('citizenship_id', 'name', 'email', 'gender', 'age', 'address')
        }),
        ('Security', {
            'fields': ('password', 'security_question', 'security_answer')
        }),
    )

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'description', 'get_election_name')
    search_fields = ('name', 'party', 'description', 'biography', 'platform', 'experience')
    list_filter = ('party', ElectionFilter)
    fieldsets = (
        ('Candidate Information', {
            'fields': ('name', 'party', 'election')
        }),
        ('Profile Details', {
            'fields': ('description', 'biography', 'platform', 'experience', 'image')
        }),
    )

    def get_election_name(self, obj):
        return obj.election.name if obj.election else "No Election"
    get_election_name.short_description = 'Election'

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'candidate', 'timestamp')
    list_filter = ('candidate', 'timestamp')
    search_fields = ('voter_name', 'candidate_name')
    date_hierarchy = 'timestamp'

@admin.register(VotingTime)
class VotingTimeAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time')
    list_filter = ('start_time', 'end_time')
    form = VotingTimeForm
    date_hierarchy = 'start_time'

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'description', 'published')
    search_fields = ('name', 'description')
    list_filter = ('start_date', 'end_date', 'published')
    date_hierarchy = 'start_date'
    form = ElectionForm
    fieldsets = (
        ('Election Details', {
            'fields': ('name', 'start_date', 'end_date', 'description')
        }),
        ('Publication', {
            'fields': ('published',)
        }),
    )
    actions = ['publish_results']

    def publish_results(self, request, queryset):
        now = timezone.now()
        updated = 0
        for election in queryset:
            if election.end_date <= now:
                election.published = True
                election.save()
                updated += 1
            else:
                self.message_user(request, f"Election '{election.name}' cannot be published yet as it ends at {election.end_date}.", level=messages.WARNING)
        if updated > 0:
            self.message_user(request, f"Published results for {updated} election(s).")

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'publish_results' in actions:
            # Check if the action should be available based on end_date
            if not any(election.end_date <= timezone.now() for election in self.get_queryset(request)):
                del actions['publish_results']
        return actions

    publish_results.short_description = "Publish Results (available after election ends)"