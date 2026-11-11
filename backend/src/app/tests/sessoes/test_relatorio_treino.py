from datetime import date, time
from app.models import ProfissionalServico, RelatorioTreino, Servico, Sessao
from app.tests.helpers import cliente_para as cliente
from app.tests.sessoes.test_presenca import BaseSessaoTests


class RelatorioTreinoTests(BaseSessaoTests):
    """Rascunho, finalização, escopo e imutabilidade de RF-07."""

    def setUp(self):
        super().setUp()
        self.sessao.status = Sessao.Status.REALIZADA
        self.sessao.save()
        self.url = f'/api/sessoes/{self.sessao.pk}/relatorio/'
        self.url_finalizar = f'{self.url}finalizar/'
        self.dados_completos = {
            'data': '2026-11-16',
            'horario': '10:00:00',
            'local': 'Sala 2',
            'objetivo': 'Desenvolver força geral.',
            'exercicios': 'Agachamento e remada.',
            'volume_valor': '1200.00',
            'volume_unidade': 'kg',
            'intensidade_borg': '7.0',
        }

    def test_cria_rascunho_incompleto_e_expõe_participantes_da_sessao(self):
        response = cliente(self.responsavel).post(self.url, {'objetivo': 'Preparação física.'}, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], RelatorioTreino.Status.RASCUNHO)
        self.assertEqual(response.data['sessao'], self.sessao.pk)
        self.assertEqual(
            response.data['participantes'],
            [{'id': self.ana.pk, 'nome': 'Ana Lima'}, {'id': self.bruno.pk, 'nome': 'Bruno Costa'}],
        )
        self.assertIsNone(response.data['data'])

    def test_edita_rascunho_e_consulta_relatorio(self):
        cliente(self.responsavel).post(self.url, {'objetivo': 'Planejamento inicial.'}, format='json')

        atualizacao = cliente(self.responsavel).patch(self.url, {'local': 'Quadra externa'}, format='json')
        consulta = cliente(self.responsavel).get(self.url)

        self.assertEqual(atualizacao.status_code, 200)
        self.assertEqual(consulta.status_code, 200)
        self.assertEqual(consulta.data['objetivo'], 'Planejamento inicial.')
        self.assertEqual(consulta.data['local'], 'Quadra externa')

    def test_finalizacao_incompleta_indica_campos_e_preserva_rascunho(self):
        cliente(self.responsavel).post(self.url, {'objetivo': 'Rascunho'}, format='json')

        response = cliente(self.responsavel).post(self.url_finalizar, {}, format='json')

        self.assertEqual(response.status_code, 400)
        for campo in ('data', 'horario', 'local', 'exercicios', 'volume_valor', 'volume_unidade', 'intensidade_borg'):
            self.assertIn(campo, response.data)
        relatorio = RelatorioTreino.objects.get(sessao=self.sessao)
        self.assertEqual(relatorio.status, RelatorioTreino.Status.RASCUNHO)
        self.assertIsNone(relatorio.finalizado_em)

    def test_finaliza_com_dados_no_payload_e_torna_relatorio_imutavel(self):
        cliente(self.responsavel).post(self.url, {'objetivo': 'Rascunho'}, format='json')

        response = cliente(self.responsavel).post(self.url_finalizar, self.dados_completos, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], RelatorioTreino.Status.FINALIZADO)
        self.assertEqual(response.data['volume_valor'], '1200.00')
        self.assertEqual(response.data['intensidade_borg'], '7.0')
        self.assertIsNotNone(response.data['finalizado_em'])
        relatorio = RelatorioTreino.objects.get(sessao=self.sessao)
        self.assertEqual(relatorio.data, date(2026, 11, 16))
        self.assertEqual(relatorio.horario, time(10, 0))

        edicao = cliente(self.responsavel).patch(self.url, {'objetivo': 'Alteração posterior.'}, format='json')
        segunda_finalizacao = cliente(self.responsavel).post(self.url_finalizar, {}, format='json')

        self.assertEqual(edicao.status_code, 409)
        self.assertEqual(segunda_finalizacao.status_code, 409)
        relatorio.refresh_from_db()
        self.assertEqual(relatorio.objetivo, 'Desenvolver força geral.')

    def test_nao_permite_dois_relatorios_para_a_mesma_sessao(self):
        primeira = cliente(self.responsavel).post(self.url, {}, format='json')
        segunda = cliente(self.responsavel).post(self.url, {}, format='json')

        self.assertEqual(primeira.status_code, 201)
        self.assertEqual(segunda.status_code, 409)
        self.assertEqual(RelatorioTreino.objects.filter(sessao=self.sessao).count(), 1)

    def test_rejeita_volume_negativo_e_borg_fora_da_escala(self):
        volume = cliente(self.responsavel).post(self.url, {'volume_valor': '-1'}, format='json')
        borg = cliente(self.responsavel).post(self.url, {'intensidade_borg': '10.1'}, format='json')

        self.assertEqual(volume.status_code, 400)
        self.assertIn('volume_valor', volume.data)
        self.assertEqual(borg.status_code, 400)
        self.assertIn('intensidade_borg', borg.data)

    def test_sessao_nao_realizada_nao_aceita_relatorio(self):
        self.sessao.status = Sessao.Status.NAO_REALIZADA
        self.sessao.save()

        response = cliente(self.responsavel).post(self.url, {}, format='json')

        self.assertEqual(response.status_code, 409)
        self.assertFalse(RelatorioTreino.objects.filter(sessao=self.sessao).exists())

    def test_servico_que_nao_e_treino_nao_aceita_relatorio(self):
        servico = Servico.objects.create(nome='Fisioterapia relatório', categoria=Servico.Categoria.FISIOTERAPIA)
        self.sessao.servico = servico
        self.sessao.save()

        response = cliente(self.responsavel).post(self.url, {}, format='json')

        self.assertEqual(response.status_code, 409)
        self.assertFalse(RelatorioTreino.objects.filter(sessao=self.sessao).exists())

    def test_recusa_edicao_antes_do_fim_previsto(self):
        cliente(self.responsavel).post(self.url, {}, format='json')

        from unittest import mock
        from datetime import timedelta

        with mock.patch('app.views.timezone.now', return_value=self.sessao.fim - timedelta(microseconds=1)):
            response = cliente(self.responsavel).post(self.url_finalizar, self.dados_completos, format='json')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(RelatorioTreino.objects.get(sessao=self.sessao).status, RelatorioTreino.Status.RASCUNHO)

    def test_responsavel_atual_pode_editar_apos_reatribuicao(self):
        relatorio = cliente(self.responsavel).post(self.url, {}, format='json')
        novo_responsavel = self.outro_treinador
        ProfissionalServico.objects.create(profissional=novo_responsavel, servico=self.sessao.servico)
        self.sessao.profissional = novo_responsavel
        self.sessao.save()

        antigo = cliente(self.responsavel).patch(self.url, {'local': 'Quadra'}, format='json')
        atual = cliente(novo_responsavel).patch(self.url, {'local': 'Sala de treino'}, format='json')

        self.assertEqual(relatorio.status_code, 201)
        self.assertEqual(antigo.status_code, 404)
        self.assertEqual(atual.status_code, 200)
        self.assertEqual(atual.data['local'], 'Sala de treino')

    def test_perfis_sem_permissao_nao_criam_nem_alteram_relatorio(self):
        for usuario in (self.admin, self.outro_treinador):
            response = cliente(usuario).post(self.url, {}, format='json')
            self.assertIn(response.status_code, (403, 404))
        cliente(self.responsavel).post(self.url, {}, format='json')
        administrador = cliente(self.admin).patch(self.url, {'objetivo': 'Mudança'}, format='json')
        self.assertEqual(administrador.status_code, 403)

    def test_sessao_inexistente_retorna_404(self):
        response = cliente(self.responsavel).post('/api/sessoes/987654/relatorio/', {}, format='json')

        self.assertEqual(response.status_code, 404)


