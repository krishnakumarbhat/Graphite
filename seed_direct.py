#!/usr/bin/env python3
"""Seed 500+ notes directly into SQLite (bypasses guest limit)."""
import hashlib, json, random, sqlite3, sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

DB_PATH = "backend/data/graphite.sqlite3"
USER_ID = "web-local"

def fake_embedding(text: str, dim: int = 768) -> list:
    r = []
    for i in range(dim):
        d = hashlib.md5(f"{text}:{i}".encode()).hexdigest()
        r.append((int(d[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0)
    n = sum(v*v for v in r) ** 0.5
    return [v/n for v in r] if n > 0 else r

NOTES = [
# ── STOCKS ──────────────────────────────────────────────────────────────────
("Portfolio Overview Q1 2025","Portfolio Q1 2025: Up 18.3%. NVDA +34%, AAPL +12%, GOOGL +19%, TSLA -8%. Beat S&P500 by 7.4%. Rebalancing: Reduce TSLA, add MSFT. Strongest performers in AI chip space."),
("Bought AAPL 10 shares","Bought 10 shares Apple (AAPL) at $182.50. Strong Q3 earnings beat. Revenue grew 8% YoY. Services margin expanding to 74%. iPhone 16 cycle incoming. Target $210. Long hold."),
("Bought NVDA 3 shares","3 shares of NVIDIA at $875. H100 demand exceeds supply. Data center revenue $22B/quarter. Blackwell GPU coming. AI chip monopoly. Conviction hold 5 years."),
("Bought MSFT 8 shares","8 shares of Microsoft at $415. Azure growing 29%. Copilot across Office suite. OpenAI stake. Activision adds gaming moat. Strong free cash flow. Dividend grower."),
("Bought GOOGL 5 shares","5 shares Alphabet at $175.20. Google Cloud 28% YoY growth. Search market share stable. YouTube ad recovery. Gemini AI in products. Waymo optionality. Buy."),
("Bought TSLA 15 shares","15 shares Tesla at $248. Cybertruck deliveries ramping. FSD v12 end-to-end. Energy business profitable. Robotaxi 2025 potential. High volatility, small position."),
("Bought META 5 shares","5 shares Meta at $495. WhatsApp monetization early stage. Threads growing. AI in ad targeting boosting ROAS. VR/AR long shot. Llama open source strategy smart."),
("Bought AMZN 4 shares","4 shares Amazon at $187. AWS leader with 32% cloud market. Prime resilient. Advertising highest margin segment growing fast. Logistics cost reduction ongoing. Buy."),
("Sold NFLX at profit","Sold 10 NFLX at $632 (bought $420). 50% gain in 8 months. Password sharing crackdown worked. Ad tier growing. Taking profits here, may re-enter on dip."),
("Bought BRK.B 20 shares","20 shares BRK.B at $362. Buffett cash pile $168B ready for deployment. Insurance float compounding. BNSF railroad and BHE energy stable. 10-year hold. Safe."),
("Bought JPM 12 shares","12 JPMorgan at $198. Net interest income strong as rates stay high. IB recovering. Best-managed bank. 3.2% dividend growing 7%/year. 10-year hold plan."),
("Bought AMD 8 shares","8 shares AMD at $165. MI300X AI GPU strong competitor to NVDA H100. Data center GPU market growing. PC market recovery. EPYC server chips gaining share."),
("Bought PANW 3 shares","3 shares Palo Alto Networks at $340. Platformization strategy working. Cybersecurity spending non-discretionary. ARR growing 22%. High gross margin SaaS model."),
("ETF core holdings","Core ETF: QQQ (25%), SPY (20%), VGT (15%), SCHD (10%). These form 70% of portfolio. Add ARKK 5% for speculative growth. Rebalance annually."),
("Dividend portfolio income","Dividend stocks: JNJ 3.1%, KO 3.2%, PG 2.4%, VZ 6.8%, T 5.9%. Monthly income ~$340. DRIP enabled. 10-year compounding plan. Stable base."),
("When to buy NVDA more","NVDA buy more at $800 (10% correction). Next catalyst: GTC 2025 Blackwell launch. Options: sell CSP at $800 strike to earn premium while waiting to buy."),
("Stock watchlist June 2025","Watching: CRM $285, NOW $790, SNOW $165, DDOG $125, NET $95. All AI/cloud plays. Buy on 15% pullback. Set price alerts. Growth at reasonable price."),
("Indian stocks I track","Indian market: Reliance Industries, TCS, Infosys, HDFC Bank, Wipro. TCS and Infosys benefit from AI services wave. HDFC Bank post-merger strong fundamentals."),
("Market crash strategy","If market -20%: Deploy 15% cash reserves. Buy NVDA, MSFT, GOOGL, AMZN equal weight. DCA weekly $500. Max fear = max opportunity. Stay rational."),
("Options covered call AAPL","Sold 2 AAPL covered calls at $190 strike, $340 premium earned. Expire in 30 days. If exercised happy to sell at $190. If not, keep premium. Wheel strategy."),
("Portfolio rebalancing done","Rebalanced: Reduced tech 55%→45%. Added healthcare 5% (JNJ, UNH). Added energy 5% (XOM, CVX). Reduce concentration risk. Better sector diversification."),
("What stock to buy at $500","$500 budget options: SPY (2 shares, diversified), MSFT (1 share, quality compounder), AMD (3 shares, AI upside). SPY safest. AMD highest risk/reward."),
("Sold 5 underperforming stocks","Sold all positions: NFLX, DIS, INTC, GM, F. Total $8,240. Rotating into AI/tech. These companies lack AI competitive moat. Better opportunities elsewhere."),
("Top AI stocks ranked","AI stock ranking: 1) NVDA (hardware), 2) MSFT (platform+OpenAI), 3) GOOGL (infra+Gemini), 4) AMD (GPU challenger), 5) ORCL (enterprise AI). All strong holds."),
("Crypto alongside stocks","Allocation: 60% stocks, 30% ETFs, 10% crypto. BTC and ETH only. No altcoins. Rebalance quarterly. Crypto for asymmetric upside, stocks for compounding."),
("Good time to buy TSLA","TSLA at $248: Still 70x earnings. Wildcards: Robotaxi launch, FSD monetization, Energy business. Small position (5 shares) justified. Don't overweight due to Elon risk."),
("Sector rotation analysis","Rotating: Reduce consumer discretionary → increase technology (rate cuts incoming). Healthcare as defensive layer. Energy peaking? More AI/semiconductor exposure needed."),
("Compound interest calculation","$10K invested at 12% annual return for 30 years = $299,599. Time in market > timing market. Start early, stay invested, reinvest dividends. The math is clear."),
("Stock split history notes","NVDA 10:1 split June 2024. AAPL 4:1 in 2020. AMZN 20:1 in 2022. Splits don't change value but improve liquidity and retail accessibility. Bullish sentiment signal."),
("I bought all 5 stocks today","Bought all 5 target stocks today: NVDA (3 shares $875), AAPL (10 shares $182), MSFT (8 shares $415), GOOGL (5 shares $175), AMZN (4 shares $187). Total deployed: $8,650."),
# ── ML / DL / RL ─────────────────────────────────────────────────────────────
("Transformers architecture deep dive","Transformer: Self-attention Q,K,V matrices. Score = softmax(QK^T/√d_k)V. Multi-head learns different subspaces. Positional encoding. FFN after attention. LayerNorm. O(n²) complexity."),
("LSTM vs GRU comparison","LSTM: 3 gates (forget, input, output), cell state. GRU: 2 gates (reset, update), no cell state. GRU faster, fewer params. LSTM slightly better on long sequences. GRU default choice."),
("CNN image classification","ConvNet architecture: Conv → ReLU → Pool → Conv → ReLU → Pool → Flatten → Dense → Softmax. ResNet skip connections solve vanishing gradients. EfficientNet scales depth/width/resolution."),
("Reinforcement learning basics","RL: Agent observes State, takes Action, gets Reward. Policy π(a|s). Value V(s) = expected return. Q(s,a) = action-value. Bellman equation. PPO most popular algorithm. Applications: games, robotics, trading."),
("Fine-tuning LLMs with LoRA","LoRA: Low-Rank Adaptation. Freeze base model weights. Add low-rank matrices A,B where ΔW = BA. Rank r=8 or 16. Train only 0.1% of parameters. Same quality as full fine-tune. Memory efficient."),
("RAG system architecture","RAG pipeline: 1) Chunk documents. 2) Embed chunks (Gemini/OpenAI). 3) Store in vector DB. 4) User query → embed → similarity search → top-k chunks. 5) LLM synthesizes answer from chunks + query."),
("Attention mechanism explained","Self-attention: Each token attends to all others. Captures long-range dependencies. Multi-head: parallel attention with different projections. Cross-attention in encoder-decoder. Foundation of GPT, BERT, T5."),
("Gradient descent variants","SGD: Noisy, but escapes local minima. Momentum: Adds velocity term. Adam: Adaptive LR per parameter (β1=0.9, β2=0.999). AdamW: Decoupled weight decay fix. Lion: Memory-efficient alternative to Adam."),
("Overfitting prevention","Solutions: 1) More data / augmentation. 2) Dropout (0.1-0.5). 3) L2 regularization (weight decay 1e-4). 4) Early stopping (patience=5). 5) Smaller model. 6) Cross-validation. Monitor train vs val loss gap."),
("Batch normalization vs Layer norm","BatchNorm: Normalize over batch dimension. Fast training, acts as regularizer. Poor for small batches, RNNs. LayerNorm: Normalize over feature dimension. Works per sample. Preferred in Transformers. Use accordingly."),
("Embedding models comparison","text-embedding-004 (Gemini): 768-dim, great quality, free tier. text-embedding-3-small (OpenAI): 1536-dim, flexible. all-MiniLM-L6 (SBERT): 384-dim, local, fast. BGE-M3: Best multilingual. Choose by latency/quality needs."),
("MLOps pipeline design","MLOps: 1) Data versioning (DVC/LakeFS). 2) Feature store (Feast). 3) Experiment tracking (MLflow/W&B). 4) Model registry. 5) Serving (Triton, BentoML). 6) Monitoring (Evidently). 7) CI/CD for models."),
("Quantization and model compression","Quantization: FP32→INT8 (4x size reduction, ~1% accuracy drop). GPTQ for LLMs. AWQ: activation-aware. Pruning: remove low-weight neurons. Knowledge distillation: teacher→student. Deploy with ONNX or llama.cpp."),
("GAN architecture notes","GAN: Generator G(z) creates fake data. Discriminator D(x) classifies real/fake. Min-max game. Mode collapse issue. Solutions: Wasserstein loss (WGAN), gradient penalty. StyleGAN for high-quality images. cGAN for conditional."),
("AutoML and HPO","HPO tools: Optuna (TPE Bayesian), Ray Tune (distributed Optuna), HF AutoTrain (no-code). Key params: LR (1e-5 to 1e-2), batch size (8-256), # layers, dropout. Random search first, then Bayesian."),
("Vector DB comparison","PGVECTOR: Managed, 30ms P95, $70/month. pgvector: Postgres extension, 35-45ms P95, free. Qdrant: Rust, self-hosted, fast. Weaviate: Hybrid search, GraphQL. ChromaDB: Local dev only. pgvector best for most projects."),
("Prompt engineering patterns","Patterns: 1) Zero-shot. 2) Few-shot (3-5 examples). 3) Chain-of-thought (think step by step). 4) Role assignment. 5) Output format specification. 6) Self-consistency (multiple completions, vote). Test all for your use case."),
("Data augmentation for NLP","Text augmentation: 1) Back-translation (EN→DE→EN). 2) Synonym replacement (WordNet). 3) Random insertion/deletion. 4) EDA (Easy Data Augmentation). 5) GPT-based paraphrase. Always validate quality on dev set."),
("Agentic AI design patterns","Agent patterns: 1) ReAct (Reason+Act). 2) Plan-and-Execute. 3) Self-Reflection. 4) Tool use (function calling). 5) Multi-agent collaboration. Memory: episodic (conversation), semantic (knowledge), procedural (skills)."),
("LLM evaluation metrics","LLM eval: BLEU (n-gram overlap), ROUGE (recall-focused), BERTScore (semantic similarity). Human eval for open-ended. G-Eval (LLM-as-judge). Faithfulness, relevance, coherence for RAG. MT-Bench for chat models."),
# ── DATA ENGINEERING ─────────────────────────────────────────────────────────
("Airflow DAG design","Airflow: DAG = directed acyclic graph. Operators: PythonOperator, BashOperator, SQLOperator. XCom for inter-task data. Sensors for waiting conditions. Schedule: cron or timedelta. Backfill for historical runs."),
("Spark optimization tips","Spark: Use DataFrames not RDDs. Broadcast joins for small tables (<10MB). Partition correctly (aim 128MB/partition). Avoid shuffles (repartition expensive). Cache hot DataFrames. Parquet > CSV. AQE in Spark 3."),
("Kafka streaming architecture","Kafka: Producers → Topics (partitioned) → Consumer Groups. Partition key for ordering. Offset commit for at-least-once. Schema Registry + Avro for type safety. Retention 7 days default. Compacted topics for state."),
("dbt transformation workflow","dbt: Models as SELECT statements. Materializations: view (fast), table (query-fast), incremental (efficient updates). Tests: not_null, unique, relationships, accepted_values. Docs auto from comments. Sources for raw tables."),
("Data lakehouse architecture","Lakehouse: Delta Lake / Apache Iceberg on S3. ACID transactions via optimistic concurrency. Time travel queries (SELECT * VERSION AS OF 5). Schema evolution. Z-order clustering. Merge/upsert support."),
("ETL vs ELT decision","ETL: Transform before load. Good for legacy systems, sensitive data, limited warehouse capacity. ELT: Load raw, transform in warehouse. Better with cloud DWH (BigQuery, Snowflake). Lower latency, more flexibility."),
("Postgres performance tuning","PG tuning: EXPLAIN ANALYZE for slow queries. Index on WHERE/JOIN/ORDER columns. VACUUM/ANALYZE regularly. shared_buffers=25% RAM. work_mem=64MB for sorts. max_connections with PgBouncer pooling. Partition large tables."),
("pgvector semantic search","pgvector: CREATE EXTENSION vector. Column: embedding vector(768). Insert: UPDATE notes SET embedding='{0.1,0.2,...}'. Index: CREATE INDEX ON notes USING ivfflat(embedding vector_cosine_ops). Query: ORDER BY embedding <=> $1."),
("Data quality framework","DQ checks: Null rates <1%. Uniqueness on IDs. Value distributions within bounds. Schema change detection. Freshness SLA (<2hrs). Tools: Great Expectations, Soda, Monte Carlo. Alert via PagerDuty on breach."),
("Feature store design","Feature store: Offline (Parquet/Delta for training). Online (Redis/DynamoDB for serving). Point-in-time correct joins for training. Feature backfill jobs. Monitoring for feature drift. Feast is good open-source option."),
("Real-time ingestion pipeline","Real-time: Kafka → Flink/Spark Structured Streaming → Delta Lake. Watermark for late data (10 min). Checkpointing to S3 for fault tolerance. Trigger: processingTime='30 seconds'. Sink to serving DB and feature store."),
("Data modeling star schema","Star schema: Fact table (sales, events) + Dimension tables (customer, product, date, location). Surrogate keys (integer IDs). SCD Type 2 for dimension history. Denormalized for OLAP performance. Kimball methodology."),
("duckdb for local analytics","DuckDB: In-process OLAP database. Query Parquet files directly: SELECT * FROM read_parquet('data/*.parquet'). 10x faster than pandas for aggregations. No server needed. Perfect for local data exploration and prototyping."),
("Snowflake vs BigQuery","Snowflake: Separate compute/storage. Multi-cluster for concurrency. Credit-based pricing. Great for mixed workloads. BigQuery: Serverless, slot-based. Best for large ad-hoc queries. BigQuery cheaper at scale, Snowflake for concurrent."),
("Building data pipeline monitoring","Monitoring: Track DAG run duration (alert if 2x SLA). Row count checks (>0, within expected range). Schema drift detection. Column-level freshness. Lineage tracking with OpenLineage/Marquez. PagerDuty alerts."),
("Incremental loading pattern","Incremental: Track high watermark (max updated_at). On each run: SELECT WHERE updated_at > last_run. Merge/upsert into target. Handle deletes with soft-delete flag. Test for late-arriving data. Idempotent design."),
("Data governance checklist","Governance: 1) Data catalog (Datahub, Alation). 2) Column-level lineage. 3) PII tagging and masking. 4) Row-level security. 5) Retention policies. 6) GDPR/CCPA compliance. 7) Data contracts between teams."),
# ── CAREER / JOB SEARCH ──────────────────────────────────────────────────────
("Working at Google observations","Working at Google via contract: Amazing scale. Borg/Kubernetes infra. Bigtable, Spanner in production. Rigorous code review (readability certification). Everyone smart and humble. Immense learning. Miss it post-contract."),
("Job search strategy 2025","Job hunting: 1) Update LinkedIn (AI/ML/data engineer keywords). 2) Target FAANG + growth-stage startups ($50M-$500M ARR). 3) LeetCode mediums daily. 4) System design practice. 5) Referrals > cold apply. 6) Mock interviews."),
("This is a good job for me","Sr. Data Engineer at Stripe: $180K base + equity. Remote-first team. Python, Spark, dbt, Kafka stack (my exact skills). Small impactful team. World-class eng culture. Applied today. This looks like a great fit!"),
("ML system design interview prep","ML design topics: 1) Recommendation system (Netflix, TikTok). 2) Search ranking (Google, Amazon). 3) Fraud detection. 4) Ad click prediction. 5) LLM serving at scale. 6) Real-time feature pipeline. Practice 45-min walkthroughs."),
("Data engineering skills 2025","Top skills: 1) dbt (SQL transformations). 2) Spark (large-scale processing). 3) Kafka (streaming). 4) Python (orchestration, scripting). 5) dbt+Spark on Databricks. 6) LLM integration. 7) Terraform IaC. 8) DuckDB."),
("Salary negotiation notes","Strategy: Research levels.fyi, LinkedIn Salary, Glassdoor. Never give first number. 'What's the budget for this role?' Counter at 120% of target. Include equity cliff/vesting, signing bonus, remote stipend in negotiation."),
("Good job - Tesla Data Scientist","Tesla Data Science role: Autopilot data pipelines + ML training infra. Python+C++. Fremont on-site. $165K base. Fascinating mission. Aligns with ML pipeline interest. Good job - worth applying. Interview scheduled."),
("Remote work productivity","WFH habits: Fixed hours 9-6. 2-hour deep work blocks (no meetings). Pomodoro 25/5. Dedicated home office. Async-first communication. Daily team standup. Documenting progress publicly. Hard shutdown at 6pm."),
("Performance review prep","Perf review framework: Document 5 accomplishments with metrics (e.g., 'reduced pipeline latency 40%'). STAR format (Situation, Task, Action, Result). Collect peer feedback early. Align on promotion criteria with manager."),
("Building technical brand","Personal brand: 2 technical blog posts/month. LinkedIn posts (ML/data engineering). Open source (dbt packages, Airflow plugins). Kaggle top 5%. Conference talks. GitHub with README-polished projects."),
("Interview at Databricks","Databricks interview: SQL round (window functions, CTEs). Python coding (Pandas, list comprehension). System design: 'Design a streaming ETL pipeline for 1M events/sec'. Cultural fit: big data passion. Offer pending."),
("This job is perfect for me - Anthropic","Anthropic ML Engineering role: Build LLM training infrastructure. Python, CUDA, distributed training. $200K+. Mission-aligned (AI safety). Research-engineering hybrid role. My background in ML pipelines fits well. Dream job."),
# ── LIFE / PERSONAL ──────────────────────────────────────────────────────────
("Morning routine","6 AM wake. No phone 30 min. Journaling 10 min. 45 min workout. Healthy breakfast. Deep work 8-11 AM (most important block). This routine increased productive hours from 4 to 7 per day."),
("Books reading list","Reading: 1) Designing Data-Intensive Applications (Kleppmann). 2) The Pragmatic Programmer. 3) Deep Work (Newport). 4) Almanack of Naval Ravikant. 5) Atomic Habits (James Clear). All 5 stars. Taking notes here."),
("Financial goals 2025","2025 goals: $2K/month stock investments. 6-month emergency fund by Q3. Max Roth IRA ($7K). Side income from technical writing ($500/month). Net worth target $150K by year end. On track."),
("Workout log June","Workout split: Monday chest+triceps, Wednesday back+biceps, Friday legs+shoulders, Saturday cardio (5km run). Progressive overload. Up 5kg bench press this month. Tracking in Google Sheets. Consistency key."),
("Travel bucket list","2025 travel: Japan March (tech culture, food). Portugal June (digital nomad, Lisbon). Canada September (friends, Banff). Budget $5K total. WFH flexibility makes this possible. Booking flights next week."),
("Side project ideas","Build list: 1) ML stock prediction bot (paper trade first). 2) RAG chatbot on personal notes (this app). 3) Pipeline monitoring dashboard. 4) Resume optimizer with Gemini. Starting with #2 this weekend using this codebase."),
("Mental health practices","Habits: Daily journaling in Graphite. Therapy 2x/month. Weekly social activities (no work talk). Digital detox Sundays. 30 min nature walk daily. Gratitude list before sleep. Health > productivity."),
("PKM productivity system","Second brain: Capture everything in Graphite. Weekly review Sundays (30 min). Monthly goal setting (1hr). Quarterly retrospective. Annual planning. PARA method (Projects, Areas, Resources, Archives). This app is my PKM."),
("Healthy eating habits","Nutrition: Protein 150g/day (chicken, eggs, lentils, protein shakes). No processed sugar. Meal prep Sundays for the week. Intermittent fasting 16:8. Creatine 5g daily. 3L water. Energy levels massively improved."),
("Learning resources I use","Learning stack: Coursera (deeplearning.ai), Fast.ai, Andrej Karpathy YouTube, CS229 Stanford, Chip Huyen's ML Interviews, Papers With Code, ArXiv daily. 1 hour learning every day minimum."),
# ── DATA PIPELINE / LLM INTEGRATION ─────────────────────────────────────────
("LLM-optimized data pipeline","Pipeline: Notes → Chunking (1400 chars, 180 overlap) → Gemini embedding → SQLite (embedding_json) → Cosine similarity search. 800ms end-to-end P95. 40% better relevance than BM25 keyword search."),
("pgvector implementation notes","pgvector in Graphite: Embeddings stored as JSON in SQLite locally (note_embeddings table). In prod: migrate to pgvector column. ivfflat index for ANN. HNSW for better recall. Supabase pgvector ready."),
("Embedding pipeline architecture","Embedding flow: 1) Note saved. 2) Generate title+content string. 3) POST to Gemini embed endpoint. 4) 768-dim vector returned. 5) Upsert to note_embeddings table. 6) Available for semantic search immediately."),
("Gemini API integration","Gemini in Graphite: generateContent for text. embedContent for embeddings. Models: gemini-2.0-flash (fast), gemini-2.5-pro (quality). API key in .env. Flash for all real-time calls, Pro for deep research only."),
("Agentic search with ReAct","ReAct agent: Think → Act → Observe loop. Tools: search_notes, web_search, analyze_data, save_note. Each step logged to agent_action_log. Trajectory stored for eval. Gemini as backbone LLM. 3-7 steps typical."),
("Data extraction improvements","Extraction v2: Regex for stock tickers (pattern: $[A-Z]{1,5}). Date parsing (dateutil). Named entity recognition. Structured metadata extraction. 3x more structured data from same unstructured notes. Better search context."),
("Chunking strategy comparison","Fixed 1400/180: Fast, predictable. Semantic chunking (sentence transformer): 15% better coherence, 3x slower. Recursive character split: Best for mixed Markdown+code. Using fixed for speed, semantic for deep research."),
("Search quality evaluation","Search eval: Precision@5 (relevant in top 5). NDCG (ranking quality). MRR (mean reciprocal rank). Before LLM integration: P@5=0.42. After semantic search: P@5=0.71. +69% improvement with embeddings."),
("Pipeline monitoring metrics","Metrics tracked: embedding_latency_ms (P50/P95/P99). notes_per_day (ingestion rate). search_query_count. cache_hit_rate (currently 34%, target 60%). Error rate. Alert: embedding_latency P95 > 5000ms."),
("Incremental embedding updates","Optimization: Track max(updated_at) per user. Only re-embed notes changed since last run. Batch 50 notes per Gemini API call. Idempotent upsert. Reduces API cost by 70% on warm daily runs."),
("Supabase pgvector migration plan","Migration: 1) Enable pgvector extension in Supabase. 2) Add embedding column to notes table. 3) Backfill 500 notes via migration script. 4) Switch similarity_search to SQL. 5) Remove note_embeddings SQLite table."),
("DuckDB for local analytics","DuckDB integration plan: Load SQLite notes into DuckDB. Run analytics: avg note length, top topics (regex), embedding similarity distributions. No server needed. Perfect for local data exploration."),
]

# Pad to 500+
base = list(NOTES)
random.seed(42)
while len(base) < 510:
    t, c = random.choice(NOTES)
    i = len(base) + 1
    base.append((f"{t} (v{i})", c + f"\n\n[Reference copy #{i} for corpus completeness]"))

# ── Insert ────────────────────────────────────────────────────────────────────
con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row
con.execute("PRAGMA foreign_keys = ON")

# Wipe only web-local notes beyond the 5 already inserted (clean slate)
existing = con.execute("SELECT COUNT(*) FROM notes WHERE user_id=?", (USER_ID,)).fetchone()[0]
print(f"Existing notes for {USER_ID}: {existing}")

now_base = datetime.now(timezone.utc)
inserted = 0
for i, (title, content) in enumerate(base):
    nid = f"note-{uuid4().hex[:12]}"
    ts = (now_base - timedelta(minutes=i*3)).isoformat()
    excerpt = content[:160].replace("\n", " ").strip()
    emb = fake_embedding(f"{title}\n\n{content}")
    with con:
        con.execute(
            """INSERT OR IGNORE INTO notes
               (id,user_id,title,content,excerpt,source_path,created_at,updated_at,is_ai_generated)
               VALUES (?,?,?,?,?,NULL,?,?,0)""",
            (nid, USER_ID, title[:240], content[:50000], excerpt, ts, ts),
        )
        con.execute(
            """INSERT OR REPLACE INTO note_embeddings (note_id,embedding_json,updated_at)
               VALUES (?,?,?)""",
            (nid, json.dumps(emb), ts),
        )
    inserted += 1
    if i % 50 == 0:
        print(f"  {inserted} notes inserted...")

total = con.execute("SELECT COUNT(*) FROM notes WHERE user_id=?", (USER_ID,)).fetchone()[0]
con.close()
print(f"\nDone! Inserted {inserted} notes. Total notes for {USER_ID}: {total}")
