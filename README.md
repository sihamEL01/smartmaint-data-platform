# SmartMaint Data Platform

SmartMaint is an end-to-end Data Engineering project for industrial
maintenance data.

## Objective

The platform will collect, clean, transform, store and visualize data related
to:

- industrial sites;
- equipment;
- incidents;
- maintenance operations;
- sensor measurements.

## MVP data flow

CSV and PostgreSQL sources  
→ Bronze layer  
→ Silver layer with PySpark  
→ Gold business datasets  
→ PostgreSQL Data Warehouse  
→ dbt models  
→ Power BI

## Planned technologies

- Python
- PostgreSQL
- PySpark
- Apache Airflow
- dbt Core
- Power BI
- Docker Compose
- GitHub Actions

## Repository structure

- `src/`: Python source code
- `tests/`: automated tests
- `docs/`: project documentation
- `docker-compose.yml`: local services configuration

## Run the initial test

From the repository root:

```bash
python -m unittest discover -s tests -p "test_*.py" -v