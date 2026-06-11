#!/usr/bin/env python3
"""Bulk seed 500+ notes into Graphite via the REST API."""
import random
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx

BASE = "http://localhost:8001"
USER_ID = "web-local"

# ── Note templates ────────────────────────────────────────────────────────────

STOCK_NOTES = [
    ("Bought AAPL today", "I bought 10 shares of Apple (AAPL) at $182.50. The stock is showing strong momentum after the Q3 earnings beat. Revenue grew 8% YoY. I expect it to reach $210 by year-end. Good time to hold long-term."),
    ("Bought GOOGL shares", "Added 5 shares of Alphabet (GOOGL) at $175.20. Google Cloud grew 28% YoY. AI integration in search is a strong moat. Target price $210. Buy and hold."),
    ("TSLA position opened", "Bought 15 shares of Tesla at $248. Cybertruck deliveries ramping up. FSD v12 impressive. Energy business growing. Risk: Elon distraction. Long-term hold."),
    ("NVDA - added to position", "Bought 3 more shares of NVIDIA at $875. Data center revenue exploded. H100 demand exceeds supply. AI chip monopoly for next 3 years. Strong conviction."),
    ("MSFT at $415 - bought 8 shares", "Microsoft Azure growing 29%. Copilot integration across Office. OpenAI partnership. Activision acquisition adds gaming. Diversified business. Strong buy."),
    ("META social media play", "5 shares of Meta at $495. WhatsApp monetization just starting. Threads gaining users. VR/AR long game. Ad revenue rebounding strongly. Good value."),
    ("AMZN - logistics moat", "Added 4 shares of Amazon at $187. AWS market leader. Prime membership resilient. Ad business profitable. Logistics cost reduction ongoing. Buy."),
    ("Sold NFLX at profit", "Sold 10 NFLX shares at $632 (bought at $420). 50% gain in 8 months. Password sharing crackdown worked better than expected. Taking profits."),
    ("Bought BRK.B - Buffett bet", "20 shares of BRK.B at $362. Buffett cash pile ready for deployment. Insurance float growing. Railroad and energy business stable. Safe harbor."),
    ("JPM - banking sector play", "12 shares of JPMorgan at $198. Net interest income strong. Investment banking recovering. Best managed bank. Dividend growing. 10-year hold."),
    ("Stock watchlist update", "Watching: AMD ($165), CRM ($285), NOW ($790), PANW ($340). AMD vs NVDA in AI chips. ServiceNow AI platform. All on dip-buy list."),
    ("Portfolio rebalancing done", "Rebalanced today: Reduced tech from 55% to 45%. Added 5% to healthcare (JNJ, UNH). Added 5% to energy (XOM, CVX). Better diversification."),
    ("When to buy NVDA more?", "NVDA analysis: Buy more if it dips to $800 (P/E normalizes). Next catalyst: GTC 2025 announcement. Blackwell GPU demand massive. Add on any 10% correction."),
    ("What stock should I buy at $500?", "At $500 budget: Consider SPY (2 shares, diversified), or MSFT (1 share, quality), or AMD (3 shares, AI upside). SPY safest, AMD highest upside."),
    ("Portfolio performance Q1", "Q1 2025: Portfolio up 18.3%. NVDA +34%, AAPL +12%, GOOGL +19%, TSLA -8%. Beat S&P500 by 7.4%. Rebalancing soon. Strong start."),
    ("Dividend stocks I hold", "Dividend portfolio: JNJ (3.1%), KO (3.2%), PG (2.4%), VZ (6.8%), T (5.9%). Monthly income ~$340. Reinvesting dividends. 10-year compounding plan."),
    ("Market crash prep strategy", "If market drops 20%: Deploy cash reserves (15% of portfolio). Buy NVDA, MSFT, GOOGL, AMZN in equal parts. Use dollar-cost averaging weekly."),
    ("Sold 5 stocks today", "Sold all 5 stocks today: NFLX, DIS, INTC, GM, F. Total proceeds $8,240. Rotating into tech and AI. These companies lack AI moat. Moving on."),
    ("AI stocks deep analysis", "Top AI stocks ranked: 1) NVDA (chips), 2) MSFT (platform), 3) GOOGL (search+cloud), 4) AMD (challenger), 5) ORCL (enterprise AI). All strong buys."),
    ("Indian stocks I track", "Tracking: Reliance, TCS, Infosys, HDFC Bank, Wipro. TCS and Infosys benefit from AI services wave. HDFC post-merger strong. Reliance Jio digital play."),
    ("ETF strategy", "Core ETF holdings: QQQ (25%), SPY (20%), VGT (15%), SCHD (10%). These cover tech growth, market exposure, dividends. Core stable base of portfolio."),
    ("Crypto + stocks balance", "60% stocks, 30% ETFs, 10% crypto. BTC and ETH only for crypto. No altcoins. Stocks for compounding, crypto for asymmetric upside. Rebalance quarterly."),
    ("Options trading notes", "Sold covered calls on AAPL: Sold 2 contracts at $190 strike, earned $340 premium. If exercised, happy to sell at $190. If not, keep premium. Wheel strategy."),
    ("Good time to buy TSLA?", "TSLA at $248: Valuation still stretched at 70x earnings. But FSD progress, energy business, Robotaxi 2025 launch are wildcards. Small position justified. Buy 5 shares."),
    ("Sector rotation analysis", "Rotating from consumer discretionary to technology. Rate cuts incoming = tech multiple expansion. Healthcare as defensive. Reducing energy (oil peak?). More AI exposure."),
]

ML_NOTES = [
    ("Deep Learning basics", "Neural networks: Input → Hidden layers → Output. Backpropagation computes gradients. Optimizer (Adam, SGD) updates weights. Loss function measures error. Key hyperparams: LR, batch size, epochs."),
    ("Transformers architecture", "Transformer: Self-attention mechanism. Q, K, V matrices. Multi-head attention. Positional encoding. Feed-forward layers. Layer norm. Used in GPT, BERT, T5. O(n²) complexity challenge."),
    ("Reinforcement Learning basics", "RL: Agent, Environment, State, Action, Reward. Policy π maps state to action. Value function V(s) estimates return. Q-learning, PPO, SAC are key algorithms. Used in robotics, games, trading."),
    ("CNN for image classification", "ConvNet: Conv layers detect features. Pooling reduces dimensions. Flatten → Dense for classification. ResNet, VGG, EfficientNet are go-to architectures. Transfer learning saves training time."),
    ("LSTM for time series", "LSTM: Long Short-Term Memory. Forget gate, input gate, output gate. Handles vanishing gradient problem. Good for stock prediction, NLP, speech. GRU is simpler alternative."),
    ("Attention mechanism explained", "Attention: Score = softmax(QK^T / √d_k) × V. Self-attention: Q=K=V from same sequence. Cross-attention: Q from decoder, K,V from encoder. Foundation of all modern LLMs."),
    ("Fine-tuning LLMs", "Fine-tune steps: 1) Load pretrained model. 2) Freeze base layers. 3) Add task head. 4) Train on domain data with low LR (1e-5). 5) Evaluate on held-out set. LoRA reduces memory."),
    ("RAG system design", "RAG: Retrieval-Augmented Generation. Embed documents → store in vector DB. At query time: embed query → retrieve top-k → inject into LLM prompt. Reduces hallucinations."),
    ("Embedding models comparison", "text-embedding-3-small (OpenAI): 1536 dim, fast. text-embedding-004 (Google): 768 dim, good quality. all-MiniLM-L6 (SBERT): 384 dim, local, fast. Choose based on latency vs quality."),
    ("Gradient descent variants", "SGD: Noisy but escapes local minima. Momentum: Smoother convergence. Adam: Adaptive LR, most popular. AdamW: L2 regularization fix. Lion: Memory efficient. Adam default choice."),
    ("Overfitting solutions", "Combat overfitting: 1) More data. 2) Dropout (p=0.2-0.5). 3) L1/L2 regularization. 4) Early stopping. 5) Data augmentation. 6) Reduce model complexity. Monitor val_loss."),
    ("Batch normalization", "BatchNorm: Normalize activations per mini-batch. Reduces internal covariate shift. Allows higher LR. Acts as regularizer. Usually placed before activation. LayerNorm preferred in transformers."),
    ("AutoML and hyperparameter tuning", "HPO tools: Optuna (Bayesian optimization), Ray Tune (distributed), HuggingFace AutoTrain. Key params to tune: LR, batch size, # layers, dropout, weight decay. Use random search first."),
    ("Model evaluation metrics", "Classification: Accuracy, Precision, Recall, F1, ROC-AUC. Regression: MAE, RMSE, R². NLP: BLEU, ROUGE, BERTScore. Always use held-out test set. Cross-validation for small datasets."),
    ("Quantization and pruning", "Model compression: Quantization (FP32→INT8, 4x size reduction). Pruning removes low-weight neurons. Knowledge distillation trains small student from large teacher. Deploy with ONNX runtime."),
    ("Vector databases comparison", "PGVECTOR: Managed, fast, expensive. Weaviate: Open-source, hybrid search. Qdrant: Rust-based, fast. pgvector: Postgres extension, simplest. ChromaDB: Local dev. PGVECTOR best for prod."),
    ("LLM prompt engineering", "Prompt patterns: 1) Chain-of-thought (step by step). 2) Few-shot examples. 3) Role assignment (You are an expert...). 4) Output format specification. 5) System prompt context. Test all patterns."),
    ("Data augmentation techniques", "Image: Flip, rotate, crop, color jitter, mixup, cutout. Text: Back-translation, synonym replacement, EDA. Audio: Time stretch, pitch shift, noise addition. Always validate augmented data quality."),
    ("MLOps pipeline design", "MLOps: 1) Data versioning (DVC). 2) Experiment tracking (MLflow, W&B). 3) Model registry. 4) CI/CD for models. 5) Monitoring (data drift, model drift). 6) A/B testing. 7) Rollback strategy."),
    ("GAN architecture notes", "GAN: Generator creates fake data, Discriminator classifies real/fake. Adversarial training. Mode collapse problem. Use Wasserstein loss (WGAN). StyleGAN for images. Used in data augmentation, image generation."),
]

DATA_ENG_NOTES = [
    ("Data pipeline with Airflow", "Apache Airflow DAG: Define tasks as Python operators. Set dependencies with >>. Schedule with cron. Use XComs for data passing. Retry logic with retries=3. Monitor via UI. Docker deployment."),
    ("Spark optimization tips", "Spark: Use DataFrames not RDDs. Broadcast small tables. Partition data properly (200 partitions default). Avoid shuffles. Cache frequently used DataFrames. Use columnar formats (Parquet, ORC)."),
    ("Kafka streaming architecture", "Kafka: Producers → Topics → Consumers. Partitions for parallelism. Consumer groups for scalability. Offset management for exactly-once. Use Schema Registry with Avro. Retention: 7 days default."),
    ("dbt for data transformation", "dbt: Define models as SQL SELECT statements. Materializations: table, view, incremental. Tests: not_null, unique, relationships. Docs auto-generated. Great for ELT pattern. Works with BigQuery, Snowflake, Redshift."),
    ("Data lakehouse architecture", "Lakehouse = Data Lake + Warehouse features. Delta Lake / Apache Iceberg provide ACID transactions on object storage. Time travel queries. Schema evolution. Best of both worlds."),
    ("ETL vs ELT", "ETL: Extract, Transform, Load. Transform before loading. Good for legacy systems. ELT: Extract, Load, Transform. Load raw data first, transform in warehouse. ELT preferred with cloud warehouses (BigQuery, Snowflake)."),
    ("Postgres performance tuning", "PG tuning: 1) EXPLAIN ANALYZE all slow queries. 2) Add indexes on join/where columns. 3) VACUUM regularly. 4) Tune shared_buffers (25% RAM). 5) work_mem for sorts. 6) Connection pooling (PgBouncer)."),
    ("pgvector for semantic search", "pgvector: Postgres extension for vector similarity. CREATE EXTENSION vector. Store embeddings as vector(768). ivfflat index for ANN search. Simple SQL interface. Perfect for RAG applications."),
    ("Data quality monitoring", "Data quality checks: 1) Null rates. 2) Unique constraints. 3) Value distributions. 4) Schema changes. 5) Freshness. Tools: Great Expectations, Soda, dbt tests. Alert on anomalies via PagerDuty."),
    ("Snowflake vs BigQuery", "Snowflake: Separate compute/storage. Multi-cloud. Credits-based pricing. Good SQL. BigQuery: Serverless, slot-based, columnar. Better for ad-hoc. Both excellent. BigQuery cheaper for batch, Snowflake for concurrent."),
    ("Data modeling - Star schema", "Star schema: Fact table (metrics) + Dimension tables (attributes). Denormalized for query performance. Surrogate keys. Slowly Changing Dimensions (SCD Type 2 for history). Best for OLAP workloads."),
    ("Feature engineering for ML", "Feature engineering: 1) Encoding categoricals (one-hot, target, ordinal). 2) Scaling numerics (StandardScaler, MinMax). 3) Date features (day of week, quarter). 4) Lag features for time series. 5) Interaction features."),
    ("Real-time data ingestion", "Real-time ingestion: Kafka → Flink/Spark Streaming → Delta Lake. Latency <1 second. Use watermarks for late data. Checkpointing for fault tolerance. Output to feature store or serving database."),
    ("Data governance framework", "Data governance: 1) Data catalog (Datahub, Atlan). 2) Lineage tracking. 3) PII identification and masking. 4) Access control (column-level security). 5) Retention policies. 6) GDPR compliance."),
    ("Building a feature store", "Feature store: Offline store (historical features, Parquet/Delta). Online store (low-latency serving, Redis/DynamoDB). Training-serving skew prevention. Feast, Tecton, Hopsworks are options."),
]

CAREER_NOTES = [
    ("Working at Google - observations", "Working at Google (via contract): Amazing infrastructure. Borg/Kubernetes at scale. Internal tools like Spanner, Bigtable are impressive. Code review culture strict. Everyone is smart. Learning a lot."),
    ("Job search strategy 2025", "Job hunting: 1) Update LinkedIn with AI/ML keywords. 2) Target FAANG + growth startups. 3) LeetCode medium problems daily. 4) System design practice. 5) ML system design (ML design primer). 6) Mock interviews."),
    ("This is a good job for me", "Sr. Data Engineer role at Stripe: Matches my skills (Python, Spark, dbt, Kafka). $180K + equity. Remote-first. Small team, high impact. Great engineering culture. Applied today. This looks like a great fit!"),
    ("Interview prep - ML system design", "ML system design topics: Recommendation systems, search ranking, fraud detection, ad click prediction, LLM serving, real-time ML. Practice: Design YouTube recommendations in 45 min with trade-offs."),
    ("Skills to learn for data engineering", "2025 data engineering skills: 1) dbt + SQL mastery. 2) Spark optimization. 3) Kafka streaming. 4) LLM integration (RAG, embeddings). 5) Delta Lake / Iceberg. 6) Terraform for IaC. 7) duckdb for analytics."),
    ("Remote work productivity tips", "WFH productivity: 1) Fixed hours 9-6. 2) Deep work blocks (no meetings). 3) Pomodoro 25/5. 4) Separate workspace. 5) Daily standup with team. 6) Over-communicate progress. 7) End-of-day shutdown ritual."),
    ("Salary negotiation notes", "Negotiation: Know market rate (levels.fyi, LinkedIn). Never give first number. 'What's the total comp budget?' Ask for 20% above target. Equity + base + bonus. Counter at least once. Walk away if needed."),
    ("Good job opportunity - Data Scientist at Tesla", "Tesla Data Science role: Work on Autopilot data pipelines and ML training infrastructure. Python + C++. On-site Fremont. $165K base. Interesting mission. Good job - aligns with my interest in autonomous systems."),
    ("Performance review prep", "Perf review: Document accomplishments with metrics (e.g., 'reduced pipeline latency by 40%'). Use STAR format. Gather peer feedback early. Align goals with manager. Discuss promotion path explicitly."),
    ("Building personal brand", "Personal brand steps: 1) Technical blog (2 posts/month). 2) LinkedIn posts on ML topics. 3) Open source contributions. 4) Kaggle competitions. 5) Speaking at meetups. 6) GitHub with quality projects."),
]

LIFE_NOTES = [
    ("Morning routine optimization", "Morning routine: 6 AM wake, no phone first 30 min. 20 min meditation. Exercise 45 min. Healthy breakfast. Deep work block 8-11 AM. This routine increased my productivity by 30%."),
    ("Books I'm reading", "Currently reading: 1) 'Designing Data-Intensive Applications' (Kleppmann). 2) 'The Almanack of Naval Ravikant'. 3) 'Deep Work' (Cal Newport). All excellent. Notes in this app."),
    ("Financial goals 2025", "2025 financial goals: 1) Invest $2000/month in stocks. 2) Build 6-month emergency fund. 3) Max out retirement accounts. 4) Side income from technical writing ($500/month). 5) Net worth target: $150K."),
    ("Workout log", "Workout: Monday (chest+triceps), Wednesday (back+biceps), Friday (legs+shoulders). Cardio 3x/week (30 min run). Progressive overload principle. Tracking with Google Sheets. Up 5kg in bench press this month."),
    ("Travel plans", "Travel list: Japan (spring), Portugal (summer), Canada (fall). Japan for tech culture and food. Portugal for digital nomad lifestyle. Canada to visit university friends. Save $5K for travel budget."),
    ("Side project ideas", "Side projects to build: 1) ML trading bot (stocks). 2) RAG chatbot for personal notes (this app!). 3) Data pipeline monitoring tool. 4) Resume optimizer with LLM. Start with #1 this weekend."),
    ("Mental health practices", "Mental health habits: 1) Journaling daily. 2) Therapy 2x/month. 3) Social activities weekly. 4) Digital detox weekends. 5) Nature walks. 6) Gratitude list. Health first, everything else second."),
    ("Productivity system", "PKM system: Capture in Graphite (this app). Weekly review every Sunday. Monthly goal setting. Quarterly retrospective. Annual planning. Inspired by Tiago Forte's PARA method. Building second brain."),
]

DATA_PIPELINE_NOTES = [
    ("LLM-optimized data pipeline", "Pipeline with LLM: Raw data → Chunking → Embedding (Gemini text-embedding-004) → pgvector storage → Semantic retrieval → LLM synthesis. Latency: ~800ms end-to-end. 40% better relevance vs keyword search."),
    ("Embedding pipeline architecture", "Embedding pipeline: 1) Ingest notes. 2) Split into 1400-char chunks with 180 overlap. 3) Batch embed with Gemini API. 4) Upsert to pgvector. 5) Index with ivfflat. 6) Serve via similarity search. 99.9% uptime."),
    ("Data extraction improvements", "Data extraction v2: Added regex-based structured extraction for stocks (ticker, price, date). Named entity recognition for companies. Date parsing for temporal context. 3x more structured data from unstructured notes."),
    ("pgvector vs PGVECTOR benchmark", "Benchmark (768-dim, 50K vectors): pgvector ivfflat: 45ms P95. PGVECTOR: 30ms P95. pgvector HNSW: 35ms P95. For <1M vectors, pgvector HNSW matches PGVECTOR. Saving $400/month by using pgvector."),
    ("Agentic search integration", "Agentic search: User query → ReAct agent → Tool calls (search_notes, web_search, analyze) → Synthesize response. Uses Gemini for reasoning. Tool call chain logged in SQLite. Response quality improved 60%."),
    ("Chunking strategy analysis", "Chunking comparison: Fixed 1400/180 overlap: baseline. Semantic chunking: 15% better coherence. Sentence-level: Too many small chunks. Recursive character split: Best for mixed content. Using fixed for speed."),
    ("Data pipeline monitoring", "Monitoring: Track embedding latency per note. Alert if >5s. Log failed embeddings for retry. Daily stats: notes ingested, embeddings generated, search queries served. Grafana dashboard planned."),
    ("Incremental embedding updates", "Incremental updates: Only re-embed notes modified since last run. Track updated_at timestamp. Batch updates in groups of 50. Use upsert for idempotency. Reduces API cost by 70% on warm runs."),
]

# Combine all notes
ALL_NOTES = []
# Repeat and shuffle to get 500+
templates = (
    STOCK_NOTES * 10 +
    ML_NOTES * 9 +
    DATA_ENG_NOTES * 7 +
    CAREER_NOTES * 8 +
    LIFE_NOTES * 7 +
    DATA_PIPELINE_NOTES * 8
)

random.shuffle(templates)

# Deduplicate by varying content slightly
for i, (title, content) in enumerate(templates[:520]):
    suffix = f" (#{i+1})" if i >= len(set(t for t, _ in templates)) else ""
    ALL_NOTES.append((f"{title}{suffix}", content))

# ── Insert via API ────────────────────────────────────────────────────────────

def insert_note(client: httpx.Client, title: str, content: str, index: int) -> bool:
    try:
        resp = client.post(
            f"{BASE}/api/notes",
            json={
                "user_id": USER_ID,
                "title": title,
                "content": content,
                "is_ai_generated": False,
            },
            timeout=15.0,
        )
        if resp.status_code == 200:
            print(f"  [{index:03d}] ✓ {title[:60]}")
            return True
        else:
            print(f"  [{index:03d}] ✗ HTTP {resp.status_code}: {resp.text[:80]}")
            return False
    except Exception as e:
        print(f"  [{index:03d}] ✗ Error: {e}")
        return False


def main():
    print(f"Seeding {len(ALL_NOTES)} notes to {BASE}...")
    ok = 0
    with httpx.Client() as client:
        for i, (title, content) in enumerate(ALL_NOTES, start=1):
            if insert_note(client, title, content, i):
                ok += 1
            if i % 50 == 0:
                time.sleep(0.3)  # brief pause every 50 notes

    print(f"\nDone: {ok}/{len(ALL_NOTES)} notes inserted successfully.")


if __name__ == "__main__":
    main()
