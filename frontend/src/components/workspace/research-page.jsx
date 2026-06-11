import { useMemo, useState } from 'react';
import {
  BarChart2,
  BrainCircuit,
  ChevronDown,
  ChevronUp,
  Loader2,
  TrendingDown,
  TrendingUp,
  Minus,
  Sparkles,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/components/ui/sonner';
import { analyzeStock, compareTtsProviders, runDeepResearch, streamDeepResearch } from '@/lib/api';

const ALGO_OPTIONS = [
  { id: 'ma',       label: 'Moving Average',   description: 'MA 20/50/200 crossover signals' },
  { id: 'rsi',      label: 'RSI',               description: 'Relative Strength Index (14-day)' },
  { id: 'macd',     label: 'MACD',              description: 'MACD line vs signal line' },
  { id: 'bollinger',label: 'Bollinger Bands',   description: '±2σ bands from 20-day MA' },
];

const SignalBadge = ({ signal }) => {
  const map = {
    BUY:  { label: 'BUY',  className: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300', icon: TrendingUp },
    SELL: { label: 'SELL', className: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300', icon: TrendingDown },
    HOLD: { label: 'HOLD', className: 'bg-secondary text-muted-foreground', icon: Minus },
  };
  const cfg = map[signal] || map.HOLD;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${cfg.className}`}>
      <Icon className="h-3.5 w-3.5" /> {cfg.label}
    </span>
  );
};

const fmtDate = (d) => {
  if (!d) return '';
  const parts = d.split('-');
  return parts.length === 3 ? `${parts[1]}/${parts[2].slice(0, 2)}` : d;
};

function MaChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -10 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fontSize: 10 }} interval={9} />
        <YAxis tick={{ fontSize: 10 }} />
        <Tooltip formatter={(v) => [`$${Number(v).toFixed(2)}`]} labelFormatter={fmtDate} />
        <Line type="monotone" dataKey="close" dot={false} strokeWidth={1.5} stroke="hsl(var(--primary))" name="Price" />
        <Line type="monotone" dataKey="ma20" dot={false} strokeWidth={1} stroke="hsl(var(--muted-foreground))" strokeDasharray="4 2" name="MA20" />
      </LineChart>
    </ResponsiveContainer>
  );
}

function RsiChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -10 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fontSize: 10 }} interval={9} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
        <Tooltip formatter={(v) => [Number(v).toFixed(1)]} labelFormatter={fmtDate} />
        <ReferenceLine y={70} stroke="hsl(var(--destructive))" strokeDasharray="3 3" label={{ value: '70', fontSize: 9 }} />
        <ReferenceLine y={30} stroke="hsl(var(--primary))" strokeDasharray="3 3" label={{ value: '30', fontSize: 9 }} />
        <Line type="monotone" dataKey="rsi" dot={false} strokeWidth={1.5} stroke="hsl(var(--primary))" name="RSI" />
      </LineChart>
    </ResponsiveContainer>
  );
}

function MacdChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -10 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fontSize: 10 }} interval={9} />
        <YAxis tick={{ fontSize: 10 }} />
        <Tooltip formatter={(v) => [Number(v).toFixed(4)]} labelFormatter={fmtDate} />
        <ReferenceLine y={0} stroke="hsl(var(--border))" />
        <Line type="monotone" dataKey="macd" dot={false} strokeWidth={1.5} stroke="hsl(var(--primary))" name="MACD" />
        <Line type="monotone" dataKey="signal" dot={false} strokeWidth={1} stroke="hsl(var(--destructive))" strokeDasharray="3 2" name="Signal" />
      </LineChart>
    </ResponsiveContainer>
  );
}

function BollingerChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -10 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fontSize: 10 }} interval={9} />
        <YAxis tick={{ fontSize: 10 }} />
        <Tooltip formatter={(v) => [`$${Number(v).toFixed(2)}`]} labelFormatter={fmtDate} />
        <Line type="monotone" dataKey="upper" dot={false} strokeWidth={1} stroke="hsl(var(--destructive))" strokeDasharray="3 2" name="Upper" />
        <Line type="monotone" dataKey="middle" dot={false} strokeWidth={1} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 2" name="Middle" />
        <Line type="monotone" dataKey="price" dot={false} strokeWidth={1.5} stroke="hsl(var(--primary))" name="Price" />
        <Line type="monotone" dataKey="lower" dot={false} strokeWidth={1} stroke="hsl(var(--primary))" strokeDasharray="3 2" name="Lower" strokeOpacity={0.5} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function AlgoCard({ algoId, label, data }) {
  const [open, setOpen] = useState(true);

  const chart = (() => {
    switch (algoId) {
      case 'ma': return <MaChart data={data.price_data || []} />;
      case 'rsi': return <RsiChart data={data.rsi_data || []} />;
      case 'macd': return <MacdChart data={data.macd_data || []} />;
      case 'bollinger': return <BollingerChart data={data.band_data || []} />;
      default: return null;
    }
  })();

  const meta = (() => {
    switch (algoId) {
      case 'ma': return [
        { k: 'MA 20', v: data.ma20 ? `$${data.ma20}` : '—' },
        { k: 'MA 50', v: data.ma50 ? `$${data.ma50}` : '—' },
        { k: 'MA 200', v: data.ma200 ? `$${data.ma200}` : '—' },
      ];
      case 'rsi': return [
        { k: 'RSI (14)', v: data.value },
        { k: 'Oversold', v: data.oversold_level },
        { k: 'Overbought', v: data.overbought_level },
      ];
      case 'macd': return [
        { k: 'MACD', v: data.macd },
        { k: 'Signal', v: data.signal_line },
        { k: 'Histogram', v: data.histogram },
      ];
      case 'bollinger': return [
        { k: 'Upper Band', v: data.upper_band ? `$${data.upper_band}` : '—' },
        { k: 'Middle', v: data.middle_band ? `$${data.middle_band}` : '—' },
        { k: 'Lower Band', v: data.lower_band ? `$${data.lower_band}` : '—' },
      ];
      default: return [];
    }
  })();

  return (
    <Card className="rounded-xl border-border/70 shadow-sm">
      <CardHeader className="pb-2 pt-4 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm font-semibold">{label}</CardTitle>
            <SignalBadge signal={data.signal} />
          </div>
          <button onClick={() => setOpen(v => !v)} className="text-muted-foreground hover:text-foreground transition-colors">
            {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </CardHeader>
      {open && (
        <CardContent className="pt-0 px-4 pb-4 space-y-3">
          <div className="flex gap-4 flex-wrap">
            {meta.map(({ k, v }) => (
              <div key={k} className="text-xs">
                <p className="text-muted-foreground">{k}</p>
                <p className="font-medium text-foreground">{v ?? '—'}</p>
              </div>
            ))}
          </div>
          {chart}
        </CardContent>
      )}
    </Card>
  );
}

export default function ResearchPage() {
  const [ticker, setTicker] = useState('');
  const [selectedAlgos, setSelectedAlgos] = useState(['ma', 'rsi', 'macd', 'bollinger']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [deepQuery, setDeepQuery] = useState('Explain the algorithmic pipeline of speech and audio AI.');
  const [deepSourceText, setDeepSourceText] = useState('');
  const [retrievalMode, setRetrievalMode] = useState('fixed');
  const [researchLoading, setResearchLoading] = useState(false);
  const [researchResult, setResearchResult] = useState(null);
  const [streamProgress, setStreamProgress] = useState([]);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsResult, setTtsResult] = useState(null);

  const latencyMetrics = useMemo(() => {
    const latency = researchResult?.pipeline?.latency_ms;
    if (!latency) {
      return [];
    }
    return [
      { label: 'Embedding', value: latency.embedding ?? 0, suffix: 'ms' },
      { label: 'Ranking', value: latency.ranking ?? 0, suffix: 'ms' },
      { label: 'LLM', value: latency.llm ?? 0, suffix: 'ms' },
      { label: 'Total', value: latency.total ?? 0, suffix: 'ms' },
    ];
  }, [researchResult]);

  const costMetrics = useMemo(() => {
    const cost = researchResult?.pipeline?.cost;
    if (!cost) {
      return [];
    }
    return [
      { label: 'Input', value: cost.input_cost_usd ?? 0, prefix: '$' },
      { label: 'Output', value: cost.output_cost_usd ?? 0, prefix: '$' },
      { label: 'Embed', value: cost.embed_cost_usd ?? 0, prefix: '$' },
      { label: 'Total', value: cost.total_cost_usd ?? 0, prefix: '$' },
    ];
  }, [researchResult]);

  const toggleAlgo = (id) =>
    setSelectedAlgos(cur =>
      cur.includes(id) ? cur.filter(a => a !== id) : [...cur, id]
    );

  const handleAnalyze = async () => {
    const sym = ticker.trim().toUpperCase();
    if (!sym) { toast.error('Enter a ticker symbol.'); return; }
    if (selectedAlgos.length === 0) { toast.error('Select at least one algorithm.'); return; }
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeStock(sym, selectedAlgos);
      setResult(data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDeepResearch = async () => {
    const query = deepQuery.trim();
    if (!query) {
      toast.error('Enter a research question.');
      return;
    }

    setResearchLoading(true);
    setResearchResult({
      retrieval_mode: retrievalMode,
      report_markdown: '',
      plan: null,
      sources: [],
      web_sources: [],
      web_provider: 'none',
      web_fallback_used: false,
      pipeline: null,
      cached: false,
      note: null,
    });
    setStreamProgress([]);
    setTtsResult(null);
    try {
      const basePayload = {
        query,
        source_text: deepSourceText.trim(),
        retrieval_mode: retrievalMode,
        user_id: 'web-local',
        save_as_note: true,
      };

      const data = await streamDeepResearch(basePayload, {
        onEvent: ({ event, data: eventData }) => {
          if (event === 'status') {
            setStreamProgress((current) => [...current, eventData]);
            return;
          }

          if (event === 'web') {
            setResearchResult((current) => ({
              ...(current || {}),
              web_sources: eventData.results || [],
              web_provider: eventData.provider || 'none',
              web_fallback_used: Boolean(eventData.fallback_used),
            }));
            return;
          }

          if (event === 'plan') {
            setResearchResult((current) => ({ ...(current || {}), plan: eventData }));
            return;
          }

          if (event === 'chunk') {
            setResearchResult((current) => ({
              ...(current || {}),
              report_markdown: `${current?.report_markdown || ''}${eventData.markdown || ''}`,
            }));
            return;
          }

          if (event === 'metrics') {
            setResearchResult((current) => ({ ...(current || {}), pipeline: eventData }));
            return;
          }

          if (event === 'sources') {
            setResearchResult((current) => ({
              ...(current || {}),
              sources: eventData.sources || [],
              web_sources: eventData.web_sources || current?.web_sources || [],
            }));
            return;
          }

          if (event === 'result') {
            setResearchResult((current) => ({
              ...(current || {}),
              report_markdown: eventData.report || current?.report_markdown || '',
              sources: eventData.sources || current?.sources || [],
              web_sources: eventData.web_sources || current?.web_sources || [],
              web_provider: eventData.web_provider || current?.web_provider || 'none',
              pipeline: eventData.pipeline || current?.pipeline || null,
              cached: Boolean(eventData.cached),
              note: eventData.note || null,
              retrieval_mode: eventData.retrieval_mode || current?.retrieval_mode || retrievalMode,
            }));
          }
        },
      }).catch(async (streamError) => {
        const fallback = await runDeepResearch(basePayload);
        setStreamProgress((current) => [...current, { step: 'fallback', msg: 'Stream unavailable, loaded standard response.' }]);
        return fallback;
      });

      setResearchResult(data);
      toast.success(data.cached ? 'Loaded cached research report' : 'Research report generated');
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || 'Deep research failed');
    } finally {
      setResearchLoading(false);
    }
  };

  const handleCompareVoices = async () => {
    const narrationText = (researchResult?.report_markdown || deepSourceText || '').slice(0, 2000).trim();
    if (!narrationText) {
      toast.error('Generate a report or provide source text before comparing voices.');
      return;
    }

    setTtsLoading(true);
    try {
      const data = await compareTtsProviders({
        text: narrationText,
        voice: 'Bruno',
        speed: 1.0,
      });
      setTtsResult(data);
      toast.success(`Preferred voice provider: ${data.preferred_provider}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || 'Voice comparison failed');
    } finally {
      setTtsLoading(false);
    }
  };

  return (
    <div className="space-y-5 pb-8">
      <div className="flex items-center gap-3 pt-2">
        <BarChart2 className="h-5 w-5 text-primary" />
        <h1 className="text-xl font-semibold">Research Lab</h1>
        <Badge variant="secondary" className="text-xs">Market signals + deep research</Badge>
      </div>

      <Card className="rounded-xl border-border/70 shadow-sm">
        <CardContent className="flex flex-wrap items-end gap-4 p-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Ticker</label>
            <Input
              className="h-9 w-32 font-mono uppercase"
              placeholder="e.g. AAPL"
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Algorithms</label>
            <div className="flex flex-wrap gap-2">
              {ALGO_OPTIONS.map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => toggleAlgo(id)}
                  className={[
                    'rounded-md border px-3 py-1 text-xs font-medium transition-colors',
                    selectedAlgos.includes(id)
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border/70 text-muted-foreground hover:bg-secondary/60',
                  ].join(' ')}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <Button className="h-9" onClick={handleAnalyze} disabled={loading || !ticker.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            {loading ? 'Analyzing…' : 'Analyze'}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-4 rounded-xl border border-border/70 bg-card/80 p-4">
            <div>
              <p className="text-lg font-bold">{result.ticker}</p>
              <p className="text-xs text-muted-foreground">{result.company_name}</p>
            </div>
            <div className="text-lg font-semibold">
              ${result.current_price?.toFixed(2)} <span className="text-xs text-muted-foreground">{result.currency}</span>
            </div>
            {result.sector && (
              <Badge variant="secondary" className="text-xs">{result.sector}</Badge>
            )}
            {result.market_cap && (
              <span className="text-xs text-muted-foreground">
                Mkt Cap: ${(result.market_cap / 1e9).toFixed(1)}B
              </span>
            )}
            <div className="ml-auto flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Overall signal</span>
              <SignalBadge signal={result.overall_signal} />
            </div>
          </div>

          {/* Algorithm cards */}
          <div className="grid gap-4 lg:grid-cols-2">
            {ALGO_OPTIONS.filter(a => result.algorithms?.[a.id]).map(({ id, label }) => (
              <AlgoCard key={id} algoId={id} label={label} data={result.algorithms[id]} />
            ))}
          </div>
        </div>
      )}

      <Card className="rounded-xl border-border/70 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-4 w-4 text-primary" />
            <CardTitle className="text-lg">GPT Researcher-style Deep Research</CardTitle>
            <Badge variant="secondary" className="text-xs">Streaming + Altimate metrics</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Research question</label>
                <Input
                  value={deepQuery}
                  onChange={(event) => setDeepQuery(event.target.value)}
                  placeholder="What do you want the system to research?"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Source text</label>
                <Textarea
                  className="min-h-[220px]"
                  value={deepSourceText}
                  onChange={(event) => setDeepSourceText(event.target.value)}
                  placeholder="Paste a paper, transcript, long note, or technical brief here."
                />
              </div>
            </div>

            <div className="space-y-4 rounded-xl border border-border/70 bg-secondary/20 p-4">
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Retrieval mode</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'fixed', label: 'Fixed chunking' },
                    { id: 'gemini', label: 'Gemini rerank' },
                    { id: 'hybrid', label: 'Hybrid + cross rerank' },
                  ].map(({ id, label }) => (
                    <button
                      key={id}
                      onClick={() => setRetrievalMode(id)}
                      className={[
                        'rounded-md border px-3 py-1.5 text-xs font-medium transition-colors',
                        retrievalMode === id
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'border-border/70 text-muted-foreground hover:bg-secondary/60',
                      ].join(' ')}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2 text-sm text-muted-foreground">
                <p>Use fixed chunking when you want the lowest compute overhead for large pasted context.</p>
                <p>Use Gemini rerank when you want cached embedding similarity over the top chunk shortlist.</p>
                <p>Use hybrid when you want embeddings, cross-rerank scoring, live web context, and streamed pipeline metrics.</p>
              </div>

              <Button className="w-full" onClick={handleDeepResearch} disabled={researchLoading || !deepQuery.trim()}>
                {researchLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                {researchLoading ? 'Researching…' : 'Run deep research'}
              </Button>

              <Button
                variant="outline"
                className="w-full"
                onClick={handleCompareVoices}
                disabled={ttsLoading || (!researchResult && !deepSourceText.trim())}
              >
                {ttsLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                {ttsLoading ? 'Comparing voices…' : 'Compare KittenTTS vs eSpeak'}
              </Button>
            </div>
          </div>

          {researchResult && (
            <div className="space-y-4 rounded-xl border border-border/70 bg-card/70 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="text-xs">Mode: {researchResult.retrieval_mode}</Badge>
                <Badge variant="secondary" className="text-xs">Cache: {researchResult.cached ? 'hit' : 'miss'}</Badge>
                <Badge variant="secondary" className="text-xs">Web: {researchResult.web_provider || 'none'}</Badge>
                {researchResult.note?.id && <Badge variant="secondary" className="text-xs">Saved to notes</Badge>}
                {researchResult.web_fallback_used && <Badge variant="outline" className="text-xs">Brave fallback used</Badge>}
              </div>

              {streamProgress.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Stream progress</p>
                  <div className="grid gap-2 md:grid-cols-2">
                    {streamProgress.map((item, index) => (
                      <div key={`${item.step}-${index}`} className="rounded-lg border border-border/70 bg-background/70 px-3 py-2 text-sm">
                        <p className="font-medium text-foreground capitalize">{item.step}</p>
                        <p className="text-muted-foreground">{item.msg}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {researchResult.plan?.overview && (
                <p className="text-sm text-muted-foreground">{researchResult.plan.overview}</p>
              )}

              {(latencyMetrics.length > 0 || costMetrics.length > 0 || researchResult.pipeline?.chunks_retrieved) && (
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="space-y-2 rounded-lg border border-border/70 bg-background/70 p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Latency breakdown</p>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {latencyMetrics.map((metric) => (
                        <div key={metric.label} className="rounded-md bg-secondary/40 p-3">
                          <p className="text-xs text-muted-foreground">{metric.label}</p>
                          <p className="text-lg font-semibold text-foreground">{Number(metric.value).toFixed(1)}{metric.suffix}</p>
                        </div>
                      ))}
                      <div className="rounded-md bg-secondary/40 p-3">
                        <p className="text-xs text-muted-foreground">Chunks</p>
                        <p className="text-lg font-semibold text-foreground">{researchResult.pipeline?.chunks_retrieved ?? 0}</p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 rounded-lg border border-border/70 bg-background/70 p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Estimated cost</p>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {costMetrics.map((metric) => (
                        <div key={metric.label} className="rounded-md bg-secondary/40 p-3">
                          <p className="text-xs text-muted-foreground">{metric.label}</p>
                          <p className="text-lg font-semibold text-foreground">{metric.prefix}{Number(metric.value).toFixed(6)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {researchResult.plan?.subquestions?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Subquestions</p>
                  <ul className="space-y-1 text-sm text-foreground">
                    {researchResult.plan.subquestions.map((item) => (
                      <li key={item}>• {item}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Report</p>
                <div className="max-h-[480px] overflow-auto rounded-lg border border-border/70 bg-background p-4 text-sm leading-6 text-foreground whitespace-pre-wrap">
                  {researchResult.report_markdown || (researchLoading ? 'Streaming report...' : 'No report yet.')}
                </div>
              </div>

              {researchResult.web_sources?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Live web context</p>
                  <div className="grid gap-2 lg:grid-cols-2">
                    {researchResult.web_sources.map((item) => (
                      <div key={`${item.url}-${item.title}`} className="rounded-lg border border-border/70 bg-background/70 p-3 text-sm">
                        <p className="font-medium text-foreground">{item.title}</p>
                        <p className="text-xs text-muted-foreground break-all">{item.url}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{item.snippet}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {researchResult.sources?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Top sources</p>
                  <div className="grid gap-2 lg:grid-cols-2">
                    {researchResult.sources.map((item) => (
                      <div key={`${item.label}-${item.path}`} className="rounded-lg border border-border/70 bg-background/70 p-3 text-sm">
                        <p className="font-medium text-foreground">{item.label}</p>
                        <p className="text-xs text-muted-foreground break-all">{item.path}</p>
                        <p className="text-xs text-muted-foreground">Score: {item.score}</p>
                        {item.cross_encoder_score !== undefined && <p className="text-xs text-muted-foreground">Cross rerank: {item.cross_encoder_score}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {ttsResult && (
            <div className="space-y-4 rounded-xl border border-border/70 bg-card/70 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge className="bg-primary/10 text-primary">Preferred: {ttsResult.preferred_provider}</Badge>
                <p className="text-sm text-muted-foreground">{ttsResult.comparison_reason}</p>
              </div>
              <div className="grid gap-3 lg:grid-cols-2">
                {ttsResult.results.map((item) => (
                  <div key={item.provider} className="rounded-lg border border-border/70 bg-background/70 p-3 space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium capitalize text-foreground">{item.provider}</p>
                      <Badge variant="secondary" className="text-xs">{item.status}</Badge>
                    </div>
                    {item.file_url ? (
                      <audio controls className="w-full" src={item.file_url} />
                    ) : (
                      <p className="text-sm text-muted-foreground">{item.detail || 'Audio unavailable.'}</p>
                    )}
                    {item.duration_seconds && (
                      <p className="text-xs text-muted-foreground">Duration: {item.duration_seconds}s</p>
                    )}
                    {item.sample_rate_hz && (
                      <p className="text-xs text-muted-foreground">Sample rate: {item.sample_rate_hz} Hz</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
