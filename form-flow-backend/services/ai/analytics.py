"""
Form Analytics Service

Tracks and analyzes form performance for optimization.

Features:
- Event tracking (starts, completions, errors, abandonments)
- Bottleneck identification
- Error hotspot detection
- AI-powered recommendations
- Conversion funnel analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import hashlib
import json

from utils.logging import get_logger
from utils.cache import get_cached, set_cached

logger = get_logger(__name__)


class EventType:
    """Analytics event types"""
    FORM_START = "form_start"
    FORM_SUBMIT = "form_submit"
    FORM_ABANDON = "form_abandon"
    FIELD_FOCUS = "field_focus"
    FIELD_BLUR = "field_blur"
    FIELD_CHANGE = "field_change"
    FIELD_ERROR = "field_error"
    VOICE_START = "voice_start"
    VOICE_END = "voice_end"
    VOICE_ERROR = "voice_error"
    CLARIFICATION_SHOWN = "clarification_shown"
    SUGGESTION_ACCEPTED = "suggestion_accepted"


class FormAnalytics:
    """
    Track and analyze form performance.
    All data is privacy-preserved (no PII stored).
    """
    
    def __init__(self):
        self._events_key_prefix = "analytics:events"
        self._insights_key_prefix = "analytics:insights"
    
    async def track_event(self, event: Dict[str, Any]) -> None:
        """
        Track a form interaction event.
        
        Event structure:
        {
            "type": "field_focus",
            "form_id": "contact-form",
            "session_id": "abc123",
            "field_id": "email",
            "timestamp": "2025-12-22T01:00:00",
            "metadata": {
                "duration": 5000,  # ms
                "attempts": 2,
                "error": "Invalid email format"
            }
        }
        """
        # Privacy: hash user ID if present
        if 'user_id' in event:
            event['user_id'] = self._hash_id(event['user_id'])
        
        # Privacy: never store actual values
        if 'value' in event.get('metadata', {}):
            del event['metadata']['value']
        
        # Add timestamp if not present
        if 'timestamp' not in event:
            event['timestamp'] = datetime.now().isoformat()
        
        # Store event
        form_id = event.get('form_id', 'unknown')
        events_key = f"{self._events_key_prefix}:{form_id}"
        
        # Get existing events
        existing = await get_cached(events_key)
        events = json.loads(existing) if existing else []
        
        # Add new event
        events.append(event)
        
        # Keep only last 1000 events per form
        events = events[-1000:]
        
        # Save with 30-day expiry
        await set_cached(events_key, json.dumps(events), expire=30 * 24 * 3600)
        
        logger.debug(f"Tracked event: {event['type']} for form {form_id}")
    
    async def get_form_insights(
        self, 
        form_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights for a form.
        
        Returns:
        {
            "summary": {completion_rate, avg_time, error_rate},
            "bottlenecks": [fields where users struggle],
            "error_hotspots": [most common errors],
            "dropout_points": [where users abandon],
            "recommendations": [AI suggestions]
        }
        """
        # Try cache first
        cache_key = f"{self._insights_key_prefix}:{form_id}"
        cached = await get_cached(cache_key)
        if cached:
            return json.loads(cached)
        
        # Get events
        events_key = f"{self._events_key_prefix}:{form_id}"
        events_raw = await get_cached(events_key)
        events = json.loads(events_raw) if events_raw else []
        
        if not events:
            return {
                "summary": {},
                "bottlenecks": [],
                "error_hotspots": [],
                "dropout_points": [],
                "recommendations": []
            }
        
        # Filter by date
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        events = [e for e in events if e.get('timestamp', '') >= cutoff]
        
        # Calculate insights
        insights = {
            "summary": self._calculate_summary(events),
            "bottlenecks": self._identify_bottlenecks(events),
            "error_hotspots": self._identify_errors(events),
            "dropout_points": self._identify_dropouts(events),
            "voice_stats": self._calculate_voice_stats(events),
            "recommendations": self._generate_recommendations(events)
        }
        
        # Cache for 1 hour
        await set_cached(cache_key, json.dumps(insights), expire=3600)
        
        return insights
    
    def _calculate_summary(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate basic form metrics."""
        sessions: Dict[str, Dict] = {}
        
        for event in events:
            sid = event.get('session_id', 'unknown')
            etype = event['type']
            
            if sid not in sessions:
                sessions[sid] = {
                    'started': False,
                    'completed': False,
                    'abandoned': False,
                    'fields_filled': 0,
                    'errors': 0,
                    'voice_used': False,
                    'start_time': None,
                    'end_time': None
                }
            
            s = sessions[sid]
            timestamp = event.get('timestamp')
            
            if etype == EventType.FORM_START:
                s['started'] = True
                s['start_time'] = timestamp
            elif etype == EventType.FORM_SUBMIT:
                s['completed'] = True
                s['end_time'] = timestamp
            elif etype == EventType.FORM_ABANDON:
                s['abandoned'] = True
                s['end_time'] = timestamp
            elif etype == EventType.FIELD_CHANGE:
                s['fields_filled'] += 1
            elif etype == EventType.FIELD_ERROR:
                s['errors'] += 1
            elif etype in [EventType.VOICE_START, EventType.VOICE_END]:
                s['voice_used'] = True
        
        # Calculate rates
        total = len(sessions)
        if total == 0:
            return {}
        
        completed = sum(1 for s in sessions.values() if s['completed'])
        abandoned = sum(1 for s in sessions.values() if s['abandoned'])
        voice_users = sum(1 for s in sessions.values() if s['voice_used'])
        
        # Calculate avg completion time
        times = []
        for s in sessions.values():
            if s['completed'] and s['start_time'] and s['end_time']:
                try:
                    start = datetime.fromisoformat(s['start_time'])
                    end = datetime.fromisoformat(s['end_time'])
                    times.append((end - start).total_seconds())
                except:
                    pass
        
        avg_time = sum(times) / len(times) if times else 0
        
        return {
            "total_sessions": total,
            "completion_rate": round(completed / total, 3),
            "abandonment_rate": round(abandoned / total, 3),
            "avg_completion_time_seconds": round(avg_time, 1),
            "avg_fields_filled": round(
                sum(s['fields_filled'] for s in sessions.values()) / total, 1
            ),
            "avg_errors_per_session": round(
                sum(s['errors'] for s in sessions.values()) / total, 2
            ),
            "voice_usage_rate": round(voice_users / total, 3)
        }
    
    def _identify_bottlenecks(self, events: List[Dict]) -> List[Dict]:
        """Find fields where users spend most time."""
        field_times: Dict[str, List[int]] = defaultdict(list)
        
        for event in events:
            if event['type'] in [EventType.FIELD_FOCUS, EventType.FIELD_BLUR]:
                field = event.get('field_id', '')
                duration = event.get('metadata', {}).get('duration', 0)
                
                if field and duration > 0:
                    field_times[field].append(duration)
        
        bottlenecks = []
        for field, times in field_times.items():
            avg_ms = sum(times) / len(times)
            avg_seconds = avg_ms / 1000
            
            if avg_seconds > 15:  # More than 15 seconds = bottleneck
                severity = 'high' if avg_seconds > 45 else 'medium'
                bottlenecks.append({
                    'field': field,
                    'avg_time_seconds': round(avg_seconds, 1),
                    'sample_count': len(times),
                    'severity': severity
                })
        
        return sorted(bottlenecks, key=lambda x: x['avg_time_seconds'], reverse=True)[:10]
    
    def _identify_errors(self, events: List[Dict]) -> List[Dict]:
        """Find most common validation errors."""
        errors: Dict[str, int] = defaultdict(int)
        
        for event in events:
            if event['type'] == EventType.FIELD_ERROR:
                field = event.get('field_id', 'unknown')
                error_msg = event.get('metadata', {}).get('error', 'Unknown error')
                
                key = f"{field}:{error_msg}"
                errors[key] += 1
        
        error_list = [
            {
                'field': k.split(':')[0],
                'error': k.split(':', 1)[1] if ':' in k else k,
                'count': v
            }
            for k, v in errors.items()
        ]
        
        return sorted(error_list, key=lambda x: x['count'], reverse=True)[:10]
    
    def _identify_dropouts(self, events: List[Dict]) -> List[Dict]:
        """Identify where users abandon the form."""
        # Track last field before abandon
        session_last_field: Dict[str, str] = {}
        abandonments: Dict[str, int] = defaultdict(int)
        
        for event in events:
            sid = event.get('session_id', '')
            etype = event['type']
            
            if etype == EventType.FIELD_FOCUS:
                session_last_field[sid] = event.get('field_id', '')
            elif etype == EventType.FORM_ABANDON:
                last_field = session_last_field.get(sid, 'unknown')
                abandonments[last_field] += 1
        
        dropout_list = [
            {'field': field, 'dropout_count': count}
            for field, count in abandonments.items()
        ]
        
        return sorted(dropout_list, key=lambda x: x['dropout_count'], reverse=True)[:5]
    
    def _calculate_voice_stats(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate voice-specific metrics."""
        voice_sessions = 0
        voice_errors = 0
        clarifications_shown = 0
        suggestions_accepted = 0
        
        for event in events:
            etype = event['type']
            
            if etype == EventType.VOICE_START:
                voice_sessions += 1
            elif etype == EventType.VOICE_ERROR:
                voice_errors += 1
            elif etype == EventType.CLARIFICATION_SHOWN:
                clarifications_shown += 1
            elif etype == EventType.SUGGESTION_ACCEPTED:
                suggestions_accepted += 1
        
        return {
            'voice_sessions': voice_sessions,
            'voice_error_rate': round(voice_errors / voice_sessions, 3) if voice_sessions > 0 else 0,
            'clarification_rate': round(clarifications_shown / voice_sessions, 3) if voice_sessions > 0 else 0,
            'suggestion_acceptance_rate': round(
                suggestions_accepted / clarifications_shown, 3
            ) if clarifications_shown > 0 else 0
        }
    
    def _generate_recommendations(self, events: List[Dict]) -> List[Dict]:
        """Generate AI-powered recommendations."""
        recommendations = []
        
        bottlenecks = self._identify_bottlenecks(events)
        errors = self._identify_errors(events)
        dropouts = self._identify_dropouts(events)
        
        # Bottleneck recommendations
        for bottleneck in bottlenecks[:3]:
            recommendations.append({
                'type': 'bottleneck',
                'field': bottleneck['field'],
                'priority': bottleneck['severity'],
                'suggestion': f"Field '{bottleneck['field']}' takes {bottleneck['avg_time_seconds']}s average. "
                             f"Consider adding placeholder text, voice hints, or autocomplete.",
                'impact': 'high' if bottleneck['severity'] == 'high' else 'medium'
            })
        
        # Error recommendations
        for error in errors[:3]:
            recommendations.append({
                'type': 'validation',
                'field': error['field'],
                'priority': 'high' if error['count'] > 10 else 'medium',
                'suggestion': f"'{error['field']}' has {error['count']} validation errors. "
                             f"Improve error message or add real-time validation hints.",
                'impact': 'high' if error['count'] > 10 else 'medium'
            })
        
        # Dropout recommendations
        for dropout in dropouts[:2]:
            recommendations.append({
                'type': 'dropout',
                'field': dropout['field'],
                'priority': 'high',
                'suggestion': f"Users frequently abandon at '{dropout['field']}'. "
                             f"Consider making it optional or providing voice assistance.",
                'impact': 'high'
            })
        
        return recommendations
    
    def _hash_id(self, user_id: str) -> str:
        """Hash user ID for privacy."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]


# Singleton instance
_analytics_instance: Optional[FormAnalytics] = None


def get_form_analytics() -> FormAnalytics:
    """Get singleton FormAnalytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = FormAnalytics()
    return _analytics_instance
