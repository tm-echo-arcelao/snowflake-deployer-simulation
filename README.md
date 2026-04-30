# Deployer Test

## How to use

1. Install `uv`
2. Run `uv pip install -r requirements.txt`
3. For NON-PROD, run `ENV=NON_PROD uv run python src/deployer.py`
4. For PROD, run `ENV=PROD uv run python src/deployer.py`

## Difference between environments

- When `ENV=NON_PROD`, `deployer.py` will run across all files within `src/snowflake` lexicographically
- When `ENV=PROD`, `deployer.py` will only run all files defined within `src/prod.yaml`, relative to the `src/snowflake` folder

## Contributing

- The main file to change is `src/deployer.py` to modify the deployment behavior logic for both NON_PROD and PROD use cases
- Submitting a PR will automatically fire two github actions runs corresponding to both use cases
