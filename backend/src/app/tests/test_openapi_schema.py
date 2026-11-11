from django.test import TestCase
from rest_framework.test import APIClient


class OpenApiSchemaTests(TestCase):
    """O schema expõe os corpos JSON e filtros que a API realmente aceita."""

    def setUp(self):
        response = APIClient().get('/api/schema/?format=json')
        self.assertEqual(response.status_code, 200, response.content)
        self.schema = response.json()

    def resolve(self, value):
        while isinstance(value, dict) and '$ref' in value:
            name = value['$ref'].rsplit('/', 1)[-1]
            value = self.schema['components']['schemas'][name]
        return value

    def session_detail_path(self):
        return next(
            path for path in self.schema['paths']
            if path.startswith('/api/sessoes/{') and path.endswith('/')
        )

    def test_confirmar_sessao_expoe_corpo_e_campos_obrigatorios(self):
        body = self.schema['paths']['/api/sessoes/']['post']['requestBody']
        request_schema = self.resolve(body['content']['application/json']['schema'])

        self.assertEqual(body['required'], True)
        self.assertTrue({
            'titulo', 'tipo', 'inicio', 'fim', 'servico', 'profissional', 'participantes',
        }.issubset(set(request_schema['required'])))

    def test_edicao_nao_documenta_participantes_como_editaveis(self):
        detail = self.schema['paths'][self.session_detail_path()]
        body = detail['patch']['requestBody']
        request_schema = self.resolve(body['content']['application/json']['schema'])
        self.assertNotIn('participantes', request_schema.get('properties', {}))

        replacement = detail['put']['requestBody']
        put_schema = self.resolve(replacement['content']['application/json']['schema'])
        self.assertTrue({'titulo', 'tipo', 'inicio', 'fim', 'profissional'}.issubset(put_schema['required']))

    def test_resposta_de_sessao_documenta_presencas(self):
        response = self.schema['paths']['/api/sessoes/']['get']['responses']['200']
        response_schema = self.resolve(response['content']['application/json']['schema']['items'])
        self.assertIn('presencas', response_schema['properties'])

    def test_filtros_de_agenda_e_auditoria_aparecem_em_parameters(self):
        agenda = self.schema['paths']['/api/sessoes/']['get']['parameters']
        auditoria = self.schema['paths']['/api/auditoria/']['get']['parameters']

        self.assertEqual({item['name'] for item in agenda}, {'inicio', 'fim', 'servico'})
        self.assertEqual(
            {item['name'] for item in auditoria},
            {'operacao', 'entidade', 'entidade_id'},
        )
