# Gadget-Pi convenience targets.

SHELL := /bin/bash
SCRIPTS := $(shell find scripts tests -name '*.sh' -type f 2>/dev/null | sort)

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint: ## Run shellcheck on every script.
	@command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck not installed"; exit 1; }
	@echo "Linting $(words $(SCRIPTS)) scripts..."
	@shellcheck $(SCRIPTS)
	@echo "shellcheck: OK"

.PHONY: syntax
syntax: ## Run 'bash -n' on every script.
	@set -e; for f in $(SCRIPTS); do bash -n "$$f"; done; echo "bash -n: OK"

.PHONY: check
check: lint syntax ## Run lint + syntax.

.PHONY: test
test: ## Run the host-side dry-run tests (no real device touched).
	@bash tests/dry-run.sh
