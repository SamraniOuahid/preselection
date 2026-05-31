# notifications/consumers.py
# WebSocket consumer for real-time notification progress tracking

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationProgressConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour suivre la progression
    de l'envoi de notifications en masse.

    URL : ws/notifications/{task_id}/
    Le task_id est un UUID généré par le backend
    au démarrage de l'envoi.

    Authentification via query param : ?token=<JWT access_token>
    """

    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'notif_task_{self.task_id}'

        # Vérifier l'authentification JWT depuis le query param
        # ws://...?token=<access_token>
        token = self._get_token_from_scope()
        if not await self._validate_token(token):
            await self.close(code=4001)
            return

        # Rejoindre le groupe du task
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Envoyer confirmation de connexion
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'task_id': self.task_id,
            'message': 'Connexion établie — en attente des données...'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Le frontend peut envoyer 'ping' pour garder la connexion active."""
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    # ── Handlers des messages du groupe Channel Layer ──────────────

    async def notification_progress(self, event):
        """Reçu depuis le service Django → transmis au frontend."""
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'current': event['current'],
            'total': event['total'],
            'candidat': event['candidat'],
            'email': event['email'],
            'statut': event['statut'],   # ENVOYE | ECHEC | IGNORE
            'erreur': event.get('erreur', ''),
            'pourcentage': round(event['current'] / event['total'] * 100)
                           if event['total'] > 0 else 0
        }))

    async def notification_termine(self, event):
        """Envoyé à la fin de tous les envois."""
        await self.send(text_data=json.dumps({
            'type': 'termine',
            'envoyes': event['envoyes'],
            'echecs': event['echecs'],
            'ignores': event['ignores'],
            'total': event['total'],
            'details_echecs': event.get('details_echecs', [])
        }))
        # Fermer la connexion après le message final
        await self.close()

    # ── Helpers ────────────────────────────────────────────────────

    def _get_token_from_scope(self):
        # Essayer query string d'abord
        query_string = self.scope.get('query_string', b'').decode()
        params = {}
        for part in query_string.split('&'):
            if '=' in part:
                key, value = part.split('=', 1)
                params[key] = value

        token = params.get('token') or params.get('access_token', '')

        # Fallback : header Authorization
        if not token:
            headers = dict(self.scope.get('headers', []))
            auth = headers.get(b'authorization', b'').decode()
            if auth.startswith('Bearer '):
                token = auth[7:]

        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"WS token trouvé: {'oui' if token else 'NON'}")

        return token

    @database_sync_to_async
    def _validate_token(self, token):
        import logging
        logger = logging.getLogger(__name__)
        try:
            if not token:
                logger.error("WS: Token vide ou absent")
                return False
            access_token = AccessToken(token)
            user = User.objects.get(id=access_token['user_id'])
            if user.role not in ['RESPONSABLE', 'ADMIN']:
                logger.error(f"WS: Rôle insuffisant: {user.role}")
                return False
            logger.info(f"WS: Token valide pour {user.email}")
            return True
        except Exception as e:
            logger.error(f"WS: Erreur validation token: {e}")
            return False
