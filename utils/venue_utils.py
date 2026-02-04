"""
Venue Clash Detection
Prevents approval of events with venue conflicts
"""

from models.models import Event
from datetime import datetime, time

def check_venue_clash(venue_id, event_date, start_time, end_time, exclude_event_id=None):
    """
    Check if venue is available for given date and time
    
    Args:
        venue_id: ID of the venue
        event_date: Date of the event (date object)
        start_time: Start time (time object)
        end_time: End time (time object)
        exclude_event_id: Event ID to exclude from check (for updates)
    
    Returns:
        dict with 'clash' (bool) and 'conflicting_events' (list)
    """
    # Query approved events for same venue and date
    query = Event.query.filter(
        Event.venue_id == venue_id,
        Event.date == event_date,
        Event.status == 'approved'
    )
    
    # Exclude specific event if provided (for update scenarios)
    if exclude_event_id:
        query = query.filter(Event.event_id != exclude_event_id)
    
    existing_events = query.all()
    
    conflicting_events = []
    
    # Check for time overlap
    for event in existing_events:
        # Convert time objects to comparable format
        event_start = event.start_time
        event_end = event.end_time
        
        # Check if times overlap
        # Overlap occurs if: (start1 < end2) AND (start2 < end1)
        if (start_time < event_end) and (event_start < end_time):
            conflicting_events.append({
                'event_id': event.event_id,
                'title': event.title,
                'start_time': event_start.strftime('%H:%M'),
                'end_time': event_end.strftime('%H:%M')
            })
    
    return {
        'clash': len(conflicting_events) > 0,
        'conflicting_events': conflicting_events
    }


def get_clash_message(conflicting_events):
    """
    Generate user-friendly message for venue clashes
    """
    if not conflicting_events:
        return None
    
    messages = []
    for event in conflicting_events:
        messages.append(
            f"'{event['title']}' ({event['start_time']} - {event['end_time']})"
        )
    
    return "Venue clash detected with: " + ", ".join(messages)
