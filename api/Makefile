git_last_tag = `git describe --tags --abbrev=0`
git_last_commit = `git rev-parse --short HEAD`
commit_status := `if [ -z "\`git status -s\`" ]; then echo ""; else echo "-uncommited"; fi`


version_name := $(git_last_tag)-$(git_last_commit)$(commit_status)
SERVICE ?= unknown
image_name := `make image`

service:
	@echo $(SERVICE)

increment:
	@~/Dev/git-version-increment.sh >/dev/null 2>/dev/null

version:
	@-`make increment` >/dev/null 2>/dev/null
	@echo $(version)

image:
	@`make increment`
	@echo $(SERVICE):$(version_name)
	@printf $(SERVICE):$(version) | pbcopy

build:
	@docker build . -t $(image_name)
	@echo $(image_name)
	@printf $(image_name) | pbcopy

deploy-test:
	@docker stack deploy -c docker-stack.yml -c docker-stack.test.yml ntrail-test

test:
	@docker stack services ntrail-test