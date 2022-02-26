git_last_tag = `git describe --tags --abbrev=0`
git_last_commit = `git rev-parse --short HEAD`
commit_status = `if [ -z "\`git status -s\`" ]; then echo ""; else echo "-raw-\`openssl rand -hex 3\`"; fi`


version = $(git_last_tag)-$(git_last_commit)$(commit_status)

increment:
	@~/Dev/git-version-increment.sh >/dev/null 2>/dev/null

version:
	@-`make increment` >/dev/null 2>/dev/null
	@echo $(version)

image:
	@echo $(SERVICE):`make version`

build:
	@docker build . -t `make image`
	@echo `make image`
	@printf `make image` | pbcopy

pwd:
	@pwd