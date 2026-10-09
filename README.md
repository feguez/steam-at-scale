\# Steam at Scale: Player Behavior and the Gaming Ecosystem



This project explores large-scale Steam review data and game metadata to study player behavior, game lifecycle patterns, and genre relationships.



\## Data



\- \~113.9 million Steam reviews

\- \~23.5 GB review dataset

\- 124,146 games in the metadata dataset



\## Tools



\- Polars

\- DuckDB

\- Parquet

\- NetworkX

\- PyVis

\- Notre Dame CRC



\## Project Questions



1\. How does player investment relate to review behavior?

2\. How does review behavior evolve across a game’s lifecycle and Early Access period?

3\. What does the Steam genre ecosystem look like?



\## Current Progress



The full pipeline has been developed and validated locally on a 236,652-review development shard.



Current work includes:



\- Lazy Polars processing

\- Review feature engineering

\- Game metadata cleaning

\- Review-to-game joins

\- Lifecycle feature engineering

\- Game-level and monthly aggregations

\- Genre normalization and co-occurrence analysis

\- Interactive genre network visualization



The full 113.9M-review dataset will be processed through the University of Notre Dame Center for Research Computing. Final full-dataset results will replace the current development-sample results.



\## Repository Structure



```text

scripts/

&#x20;   01\_inspect\_data.py

&#x20;   02\_process\_reviews.py

&#x20;   02\_process\_reviews\_polars.py

&#x20;   03\_validate\_duckdb.py

&#x20;   04\_process\_games.py

&#x20;   05\_join\_sample.py

&#x20;   06\_build\_genre\_network.py

&#x20;   07\_genre\_network.py

&#x20;   08\_full\_review\_pipeline.py



data/

&#x20;   processed/

&#x20;       genre\_network.html

```



Raw datasets and generated Parquet outputs are excluded from GitHub due to file size.

