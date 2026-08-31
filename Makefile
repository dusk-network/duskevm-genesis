.PHONY: test validate-h2-rehearsal

test:
	python3 -m unittest discover -s tools -p 'test_*.py'

validate-h2-rehearsal:
	python3 tools/validate_release_bundle.py rehearsals/h2-devnet-20260813-fresh-l1
