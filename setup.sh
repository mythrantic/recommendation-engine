docker build -t recommendation-engine-image .
docker run --name recommendation-engine-container -d -p 8000:8000 -v $(pwd):/code recommendation-engine-image

#connect to turborepo
git subtree add --prefix=apps/recommendation-engine https://github.com/valiantlynx/recommendation-engine.git main --squash
git subtree pull --prefix=apps/recommendation-engine https://github.com/valiantlynx/recommendation-engine.git main --squash
git subtree push --prefix=apps/recommendation-engine https://github.com/valiantlynx/recommendation-engine.git main