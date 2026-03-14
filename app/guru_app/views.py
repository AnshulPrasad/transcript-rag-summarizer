import sys
import json
import pickle
import logging
from pathlib import Path
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

# Make sure project root is on path so config, api, utils are importable
BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from config import FILE_PATHS, TRANSCRIPTS, MAX_CONTEXT_TOKENS
from api.generate_response import generate_response
from api.retrieve_context import retrieve_transcripts
from utils.token import count_tokens, trim_to_token_limit

logger = logging.getLogger(__name__)

# ── Data loaded once at module import ─────────────────────────────────────────
_file_paths: list = []
_transcripts: list = []
_data_loaded = False


def _load_data():
    global _file_paths, _transcripts, _data_loaded
    if _data_loaded:
        return
    try:
        with open(FILE_PATHS, 'rb') as f:
            _file_paths = pickle.load(f)
        with open(TRANSCRIPTS, 'rb') as f:
            _transcripts = pickle.load(f)
        _data_loaded = True
        logger.info('Loaded %d transcripts', len(_transcripts))
    except Exception as exc:
        logger.error('Failed to load transcript data: %s', exc)


_load_data()


# ── Views ──────────────────────────────────────────────────────────────────────

@login_required
def index(request):
    """Render the main chat page — login required."""
    history = request.session.get('chat_history', [])
    user = request.user
    # Get Google profile picture if available
    avatar_url = None
    try:
        social = user.socialaccount_set.filter(provider='google').first()
        if social:
            avatar_url = social.extra_data.get('picture')
    except Exception:
        pass

    return render(request, 'guru/index.html', {
        'history': history,
        'user': user,
        'avatar_url': avatar_url,
    })


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def ask(request):
    """POST /ask/ — requires login."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    query = (data.get('query') or '').strip()
    if not query:
        return JsonResponse({'error': 'Query cannot be empty'}, status=400)

    if not _data_loaded:
        return JsonResponse({'error': 'Transcript data not loaded.'}, status=503)

    try:
        retrieved = retrieve_transcripts(query, _file_paths, _transcripts, top_k=15)
        if not retrieved:
            return JsonResponse({'error': 'No relevant transcripts found'}, status=404)

        full_context = ' '.join(retrieved)
        limited_context = trim_to_token_limit(full_context, MAX_CONTEXT_TOKENS)
        answer = generate_response(query, limited_context)

        logger.info('User: %s | Query: %s | Tokens: %d',
                    request.user.email, query, count_tokens(limited_context))

        # ── Save to database log ───────────────────────────────────────────────
        try:
            from django.guru_app.models import QueryLog
            QueryLog.objects.create(
                user=request.user,
                query=query,
                answer=answer,
                tokens_used=count_tokens(limited_context),
            )
        except Exception as log_exc:
            logger.warning('Failed to save query log: %s', log_exc)

        history = request.session.get('chat_history', [])
        history.append({
            'query': query,
            'answer': answer,
            'timestamp': datetime.now().strftime('%d %b %Y, %H:%M'),
        })
        request.session['chat_history'] = history[-50:]
        request.session.modified = True

        return JsonResponse({
            'answer': answer,
            'query': query,
            'timestamp': datetime.now().strftime('%d %b %Y, %H:%M'),
        })

    except Exception as exc:
        logger.exception('Error processing query: %s', exc)
        return JsonResponse({'error': 'Internal server error.'}, status=500)


@login_required
@require_http_methods(['GET'])
def history(request):
    return JsonResponse({'history': request.session.get('chat_history', [])})


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def clear_history(request):
    request.session['chat_history'] = []
    request.session.modified = True
    return JsonResponse({'status': 'cleared'})