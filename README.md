# Plataforma de avaliação de funcionários

## Decisões de implementação

### Identificação do usuário

A demonstração identifica o usuário pelo cabeçalho `X-Leader-ID`.
O endpoint `GET /api/leaders` fornece os líderes disponíveis para seleção.

Esse mecanismo permite alternar usuários e não representa autenticação
para uso em produção.

### Período semanal

A semana começa na segunda-feira às 00h e termina na segunda-feira
seguinte às 00h, considerando o fuso `America/Sao_Paulo`.

Cada par líder–funcionário pode ter uma avaliação por semana.
Avaliações feitas por outros líderes não consomem esse limite.

### Hierarquia e visibilidade

O usuário pode avaliar e consultar avaliações apenas de seus
subordinados diretos e indiretos.

Não pode avaliar nem consultar avaliações de si mesmo, de pares
ou de superiores.

### Interpretação provisória da prioridade hierárquica

O enunciado não detalha o significado de
“respeitando sempre a maior hierarquia”.

Nesta implementação, a permissão de consulta depende da relação
entre o usuário e o funcionário avaliado, independentemente de quem
enviou a avaliação.

Assim, um líder pode consultar a avaliação de um subordinado mesmo
quando ela foi enviada por uma liderança superior.

A avaliação mais recente é determinada pela data de envio.
Em caso de empate, utiliza-se o maior identificador.

Essa interpretação deverá ser revista caso o responsável pelo case
esclareça uma regra diferente.

### Respostas e cálculo

Cada avaliação contém exatamente seis respostas, com notas inteiras
de 1 a 4.

A nota final é a soma dos produtos entre nota e peso, dividida
pela soma dos pesos.

Atualmente, o cálculo consulta os pesos cadastrados nas questões.
Não há funcionalidade de edição desses pesos.

### Imutabilidade

As avaliações e respostas enviadas possuem proteção no PostgreSQL
contra atualização, exclusão e esvaziamento das respectivas tabelas.