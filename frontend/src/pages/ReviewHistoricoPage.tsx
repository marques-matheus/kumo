import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { formatText } from '../utils/formatText'
import { useApi } from '../hooks/useApi'
import LoadingSpinner from '../components/LoadingSpinner'
import type { SimuladoDetalhes, QuestaoRevisao } from '../types'

type FilterType = 'all' | 'correct' | 'wrong' | 'skipped'

export default function ReviewHistoricoPage() {
  const { simulado_id } = useParams<{ simulado_id: string }>()
  const navigate = useNavigate()
  const { apiFetch } = useApi()

  const [simulado, setSimulado] = useState<SimuladoDetalhes | null>(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState<string | null>(null)
  const [filter, setFilter]     = useState<FilterType>('all')

  useEffect(() => {
    if (!simulado_id) {
      setError('ID do simulado não informado.')
      setLoading(false)
      return
    }

    apiFetch<SimuladoDetalhes>(`/simulados/${encodeURIComponent(simulado_id)}`)
      .then(data => setSimulado(data))
      .catch(err => {
        console.error('Erro ao buscar simulado:', err)
        setError('Não foi possível carregar este simulado. Ele pode ter expirado (90 dias) ou não existir.')
      })
      .finally(() => setLoading(false))
  }, [simulado_id])

  if (loading) {
    return <LoadingSpinner overlay message="Carregando simulado..." />
  }

  if (error || !simulado) {
    return (
      <div className="page-container">
        <div className="empty-state" style={{ marginTop: '4rem' }}>
          <i className="ph ph-warning-circle" style={{ fontSize: '3rem', color: 'var(--red)' }} />
          <p style={{ marginTop: '1rem' }}>{error || 'Simulado não encontrado.'}</p>
          <button className="btn-outline btn-sm" style={{ marginTop: '1.5rem' }} onClick={() => navigate('/progress')}>
            Voltar ao Histórico
          </button>
        </div>
      </div>
    )
  }

  const filtered = simulado.questoes.filter((q: QuestaoRevisao) => {
    if (filter === 'correct') return q.status === 'correta'
    if (filter === 'wrong')   return q.status === 'errada'
    if (filter === 'skipped') return q.status === 'pulada'
    return true
  })

  const letters = ['A','B','C','D','E','F']
  const d = new Date(simulado.data_iso)
  const dateStr = d.toLocaleDateString('pt-BR') + ' às ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

  const counts = {
    corretas: simulado.questoes.filter(q => q.status === 'correta').length,
    erradas:  simulado.questoes.filter(q => q.status === 'errada').length,
    puladas:  simulado.questoes.filter(q => q.status === 'pulada').length,
  }

  return (
    <div style={{ paddingBottom: '4rem' }}>
      <header className="review-header">
        <div>
          <h2>Revisão — {simulado.cert}</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            {dateStr} · Score: <strong style={{ color: simulado.score >= 70 ? 'var(--green)' : 'var(--red)' }}>{simulado.score}%</strong>
          </p>
        </div>
        <button className="btn-outline btn-sm" onClick={() => navigate('/progress')}>
          Voltar ao Histórico
        </button>
      </header>

      <div className="review-filters">
        <button className={`btn-filter ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>
          Todas ({simulado.total})
        </button>
        <button className={`btn-filter ${filter === 'correct' ? 'active' : ''}`} onClick={() => setFilter('correct')}>
          Corretas ({counts.corretas})
        </button>
        <button className={`btn-filter ${filter === 'wrong' ? 'active' : ''}`} onClick={() => setFilter('wrong')}>
          Erradas ({counts.erradas})
        </button>
        <button className={`btn-filter ${filter === 'skipped' ? 'active' : ''}`} onClick={() => setFilter('skipped')}>
          Puladas ({counts.puladas})
        </button>
      </div>

      <div className="review-list">
        {filtered.length === 0 ? (
          <div className="empty-state">
            <i className="ph ph-check-circle" />
            <p>Nenhuma questão encontrada para este filtro.</p>
          </div>
        ) : (
          filtered.map((q, i) => {
            const cls = q.status === 'pulada' ? 'ri-skipped' : q.status === 'correta' ? 'ri-correct' : 'ri-wrong'
            const statusIcon = q.status === 'pulada'
              ? <><i className="ph ph-square"/> Pulada</>
              : q.status === 'correta'
              ? <><i className="ph ph-check-circle"/> Correta</>
              : <><i className="ph ph-x-circle"/> Errada</>

            const globalIdx = simulado.questoes.indexOf(q)

            return (
              <div key={q.id} className={`review-item ${cls}`}>
                <div className="ri-header">
                  <span className="ri-num">Questão {globalIdx + 1}</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '.8rem' }}>
                    {q.dificuldade && (
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '99px',
                        fontSize: '0.75rem',
                        background: q.dificuldade === 'Difícil' ? 'rgba(239,68,68,0.15)' : q.dificuldade === 'Fácil' ? 'rgba(34,197,94,0.15)' : 'rgba(250,204,21,0.15)',
                        color: q.dificuldade === 'Difícil' ? 'var(--red)' : q.dificuldade === 'Fácil' ? 'var(--green)' : '#ca8a04',
                      }}>
                        {q.dificuldade}
                      </span>
                    )}
                    {statusIcon}
                  </span>
                </div>

                <p className="ri-question" dangerouslySetInnerHTML={{ __html: formatText(q.pergunta) }} />

                <div className="ri-options">
                  {q.opcoes.map((opt, oi) => {
                    const isCorrect  = q.resposta_correta.includes(oi)
                    const isUserWrong = q.resposta_usuario?.includes(oi) && !isCorrect

                    return (
                      <div key={oi} className={`ri-opt ${isCorrect ? 'is-correct' : isUserWrong ? 'is-wrong' : ''}`}>
                        <strong>{letters[oi]}.</strong>
                        <span dangerouslySetInnerHTML={{ __html: formatText(opt) }} />
                      </div>
                    )
                  })}
                </div>

                {q.explicacao && (
                  <div className="ri-explanation">
                    <strong>Explicação:</strong><br /><br />
                    <span dangerouslySetInnerHTML={{ __html: formatText(q.explicacao) }} />
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
