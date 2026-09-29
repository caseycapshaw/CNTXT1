# Cloud-core operations. Run from SYSTEM/optional/core-jobs/ on the core host.
#   make deploy USER_NAME=<user> VAULT_PATH=<vault-path> TZ_NAME=<Area/City>
#   make status | make test | make kill-switch
USER_NAME  ?= $(CNTXT1_USER)
VAULT_PATH ?= $(VAULT)
TZ_NAME    ?= $(if $(TZ),$(TZ),UTC)
ADDONS     ?= core-jobs

.PHONY: deploy render status test kill-switch

# Render the units + enable the timers (idempotent). Pull your checkout first
# (as the vault user, never as root) if the add-on lives in a services repo.
deploy:
	./install.sh --user "$(USER_NAME)" --vault "$(VAULT_PATH)" --tz "$(TZ_NAME)" --addons "$(ADDONS)"

# Render only (no root, no systemctl) into ./rendered for review.
render:
	./install.sh --user "$(or $(USER_NAME),user)" --vault "$(or $(VAULT_PATH),/srv/vault)" --tz "$(TZ_NAME)" --addons "$(ADDONS)" --systemd-dir ./rendered --render-only

status:
	systemctl list-timers 'cntxt1-*' --all
	@echo "--- failed units ---"
	systemctl --failed

test:
	python3 -m unittest discover -s bin/tests -v
	cd lib && python3 -m unittest discover -s tests -p "test_*.py" -v
	bash lib/tests/test-env.sh

# Panic button: stop every scheduled job and any internet-facing service.
# Units that don't exist on this host are ignored.
kill-switch:
	-systemctl stop 'cntxt1-*.timer' 'cntxt1-*.path'
	-systemctl stop cloudflared cntxt1-mcp.service cntxt1-capture.service
	@echo "kill-switch: timers and internet-facing services stopped. 'make deploy' re-enables."
