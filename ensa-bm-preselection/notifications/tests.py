# notifications/tests.py
# Tests complets pour le système de notifications en masse avec WebSocket

import json
import uuid
from unittest.mock import patch, MagicMock
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from users.models import User, Candidat
from administration.models import Filiere
from candidatures.models import Dossier
from notifications.models import Notification
from notifications.consumers import NotificationProgressConsumer
from notifications.services import (
    demarrer_notification_masse,
    compter_a_notifier,
    _deja_notifie_recemment,
)


# ═══════════════════════════════════════════════════════════════
# Helpers de création de données de test
# ═══════════════════════════════════════════════════════════════

def creer_utilisateur(role='CANDIDAT', email=None, cin=None):
    """Crée un utilisateur de test avec le rôle spécifié."""
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        email=email or f'test-{uid}@example.com',
        cin=cin or f'CIN{uid}',
        password='testpass123',
        role=role,
    )


def creer_candidat_avec_dossier(filiere, statut='PRESELECTIONNE'):
    """Crée un candidat avec un dossier dans la filière donnée."""
    user = creer_utilisateur(role='CANDIDAT')
    candidat = Candidat.objects.create(
        user=user,
        nom=f'Nom{uuid.uuid4().hex[:4]}',
        prenom=f'Prenom{uuid.uuid4().hex[:4]}',
    )
    dossier = Dossier.objects.create(
        candidat=candidat,
        filiere=filiere,
        statut=statut,
        diplome_obtenu='Licence',
        etablissement_origine='Université Test',
        score=15.5,
    )
    return user, candidat, dossier


def creer_filiere():
    """Crée une filière de test."""
    uid = uuid.uuid4().hex[:6]
    return Filiere.objects.create(
        nom=f'Filière Test {uid}',
        code=f'FT{uid[:4].upper()}',
        niveau=Filiere.Niveau.BAC3,
        places_disponibles=50,
    )


# ═══════════════════════════════════════════════════════════════
# Tests WebSocket Consumer
# ═══════════════════════════════════════════════════════════════

@override_settings(
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
)
class WebSocketNotificationTest(TestCase):
    """Tests pour le consumer WebSocket de progression des notifications."""

    def setUp(self):
        self.responsable = creer_utilisateur(role='RESPONSABLE', email='resp@test.com', cin='CINRESP001')
        self.candidat_user = creer_utilisateur(role='CANDIDAT', email='cand@test.com', cin='CINCAND001')
        self.task_id = str(uuid.uuid4())

    def _get_token(self, user):
        """Génère un token JWT valide pour l'utilisateur."""
        token = AccessToken.for_user(user)
        return str(token)

    async def _create_communicator(self, task_id, token=''):
        """Crée un WebsocketCommunicator pour les tests."""
        from channels.routing import URLRouter
        from notifications.routing import websocket_urlpatterns
        communicator = WebsocketCommunicator(
            URLRouter(websocket_urlpatterns),
            f'/ws/notifications/{task_id}/?token={token}'
        )
        return communicator

    async def test_consumer_refuse_connexion_sans_token(self):
        """Le consumer doit refuser une connexion sans token JWT."""
        communicator = await self._create_communicator(self.task_id, token='')
        connected, code = await communicator.connect()
        # La connexion doit être refusée (close code 4001)
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_consumer_refuse_connexion_role_candidat(self):
        """Le consumer doit refuser une connexion d'un utilisateur candidat."""
        token = self._get_token(self.candidat_user)
        communicator = await self._create_communicator(self.task_id, token=token)
        connected, code = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_consumer_accepte_connexion_responsable(self):
        """Le consumer doit accepter une connexion d'un responsable."""
        token = self._get_token(self.responsable)
        communicator = await self._create_communicator(self.task_id, token=token)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Vérifier le message de connexion
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connected')
        self.assertEqual(response['task_id'], self.task_id)

        await communicator.disconnect()

    async def test_progression_recue_en_temps_reel(self):
        """Le consumer doit transmettre les messages de progression."""
        token = self._get_token(self.responsable)
        communicator = await self._create_communicator(self.task_id, token=token)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consommer le message 'connected'
        await communicator.receive_json_from()

        # Simuler un message de progression via le channel layer
        channel_layer = get_channel_layer()
        group_name = f'notif_task_{self.task_id}'
        await channel_layer.group_send(group_name, {
            'type': 'notification.progress',
            'current': 1,
            'total': 10,
            'candidat': 'Ahmed Benali',
            'email': 'ahmed@test.com',
            'statut': 'ENVOYE',
            'erreur': '',
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'progress')
        self.assertEqual(response['current'], 1)
        self.assertEqual(response['total'], 10)
        self.assertEqual(response['candidat'], 'Ahmed Benali')
        self.assertEqual(response['statut'], 'ENVOYE')
        self.assertEqual(response['pourcentage'], 10)

        await communicator.disconnect()

    async def test_message_termine_ferme_connexion(self):
        """Le consumer doit fermer la connexion après le message 'termine'."""
        token = self._get_token(self.responsable)
        communicator = await self._create_communicator(self.task_id, token=token)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consommer le message 'connected'
        await communicator.receive_json_from()

        # Simuler le message 'termine'
        channel_layer = get_channel_layer()
        group_name = f'notif_task_{self.task_id}'
        await channel_layer.group_send(group_name, {
            'type': 'notification.termine',
            'envoyes': 8,
            'echecs': 1,
            'ignores': 1,
            'total': 10,
            'details_echecs': [{'candidat': 'Test', 'email': 'test@test.com', 'erreur': 'SMTP error'}],
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'termine')
        self.assertEqual(response['envoyes'], 8)
        self.assertEqual(response['echecs'], 1)

        await communicator.disconnect()

    async def test_ping_pong_maintient_connexion(self):
        """Le consumer doit répondre 'pong' à un message 'ping'."""
        token = self._get_token(self.responsable)
        communicator = await self._create_communicator(self.task_id, token=token)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consommer le message 'connected'
        await communicator.receive_json_from()

        # Envoyer un ping
        await communicator.send_json_to({'type': 'ping'})
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'pong')

        await communicator.disconnect()


# ═══════════════════════════════════════════════════════════════
# Tests de l'envoi de notifications en masse
# ═══════════════════════════════════════════════════════════════

@override_settings(
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
)
class NotificationMasseTest(TestCase):
    """Tests pour le service d'envoi de notifications en masse."""

    def setUp(self):
        self.filiere = creer_filiere()
        self.responsable = creer_utilisateur(role='RESPONSABLE', email='resp@masse.com', cin='CINMASRESP')

    @patch('threading.Thread')
    def test_task_id_retourne_immediatement(self, mock_thread):
        """demarrer_notification_masse() doit retourner un UUID immédiatement."""
        task_id = demarrer_notification_masse(
            filiere_id=self.filiere.id,
            envoye_par=self.responsable
        )
        self.assertIsNotNone(task_id)
        # Vérifier le format UUID
        try:
            uuid.UUID(task_id)
        except ValueError:
            self.fail('task_id n\'est pas un UUID valide')

    @patch('notifications.services.envoyer_notification_masse_async')
    def test_thread_demarre_en_arriere_plan(self, mock_async):
        """Le thread d'envoi doit être démarré en daemon."""
        with patch('threading.Thread') as mock_thread:
            mock_instance = MagicMock()
            mock_thread.return_value = mock_instance

            task_id = demarrer_notification_masse(
                filiere_id=self.filiere.id,
                envoye_par=self.responsable
            )

            mock_thread.assert_called_once()
            call_kwargs = mock_thread.call_args
            self.assertTrue(call_kwargs.kwargs.get('daemon', False) or
                            (len(call_kwargs) > 1 and call_kwargs[1].get('daemon', False)))
            mock_instance.start.assert_called_once()

    def test_doublon_ignore_24h(self):
        """Un candidat déjà notifié dans les 24h doit être ignoré."""
        user, candidat, dossier = creer_candidat_avec_dossier(self.filiere)

        # Créer une notification récente
        Notification.objects.create(
            destinataire=user,
            type_notif='PRESELECTION',
            sujet='Test',
            contenu_html='<p>Test</p>',
            statut='ENVOYEE',
            envoyee_le=timezone.now() - timedelta(hours=2),
        )

        self.assertTrue(_deja_notifie_recemment(dossier))

    def test_notification_ancienne_non_ignoree(self):
        """Un candidat notifié il y a plus de 24h ne doit PAS être ignoré."""
        user, candidat, dossier = creer_candidat_avec_dossier(self.filiere)

        # Créer une notification ancienne (> 24h)
        Notification.objects.create(
            destinataire=user,
            type_notif='PRESELECTION',
            sujet='Test',
            contenu_html='<p>Test</p>',
            statut='ENVOYEE',
            envoyee_le=timezone.now() - timedelta(hours=25),
        )

        self.assertFalse(_deja_notifie_recemment(dossier))

    @patch('notifications.services.envoyer_notification')
    def test_echec_smtp_enregistre_et_continue(self, mock_envoyer):
        """Un échec SMTP doit être enregistré mais l'envoi doit continuer."""
        # Créer 3 candidats
        creer_candidat_avec_dossier(self.filiere)
        creer_candidat_avec_dossier(self.filiere)
        creer_candidat_avec_dossier(self.filiere)

        # Le 2e envoi échoue
        mock_envoyer.side_effect = [None, Exception('SMTP timeout'), None]

        stats = compter_a_notifier(self.filiere.id)
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['a_notifier'], 3)

    def test_compter_a_notifier_filtre_filiere(self):
        """compter_a_notifier() doit respecter le filtre filière."""
        filiere2 = creer_filiere()
        creer_candidat_avec_dossier(self.filiere)
        creer_candidat_avec_dossier(self.filiere)
        creer_candidat_avec_dossier(filiere2)

        stats = compter_a_notifier(self.filiere.id)
        self.assertEqual(stats['total'], 2)

        stats_all = compter_a_notifier(None)
        self.assertEqual(stats_all['total'], 3)


# ═══════════════════════════════════════════════════════════════
# Tests de l'API HTTP
# ═══════════════════════════════════════════════════════════════

class NotificationAPITest(TestCase):
    """Tests pour les endpoints REST de notification."""

    def setUp(self):
        self.filiere = creer_filiere()
        self.responsable = creer_utilisateur(role='RESPONSABLE', email='resp@api.com', cin='CINAPIRESP')
        self.candidat_user = creer_utilisateur(role='CANDIDAT', email='cand@api.com', cin='CINAPICAND')
        self.client = APIClient()

    def test_previsualiser_requiert_authentification(self):
        """GET /api/notifications/previsualiser/ nécessite un token."""
        response = self.client.get('/api/notifications/previsualiser/')
        self.assertEqual(response.status_code, 401)

    def test_previsualiser_refuse_candidat(self):
        """Un candidat ne doit pas pouvoir accéder à l'endpoint."""
        self.client.force_authenticate(user=self.candidat_user)
        response = self.client.get('/api/notifications/previsualiser/')
        self.assertEqual(response.status_code, 403)

    def test_previsualiser_ok_responsable(self):
        """Un responsable doit pouvoir voir les stats."""
        creer_candidat_avec_dossier(self.filiere)
        self.client.force_authenticate(user=self.responsable)
        response = self.client.get('/api/notifications/previsualiser/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.data)
        self.assertIn('apercu_email', response.data)
        self.assertEqual(response.data['stats']['total'], 1)

    @patch('notifications.views.demarrer_notification_masse')
    def test_notifier_tous_retourne_task_id(self, mock_demarrer):
        """POST /api/notifications/notifier-tous/ doit retourner un task_id."""
        mock_demarrer.return_value = 'test-uuid-1234'
        self.client.force_authenticate(user=self.responsable)
        response = self.client.post('/api/notifications/notifier-tous/')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['task_id'], 'test-uuid-1234')
        self.assertIn('ws_url', response.data)

    def test_notifier_tous_refuse_candidat(self):
        """Un candidat ne doit pas pouvoir lancer l'envoi."""
        self.client.force_authenticate(user=self.candidat_user)
        response = self.client.post('/api/notifications/notifier-tous/')
        self.assertEqual(response.status_code, 403)
