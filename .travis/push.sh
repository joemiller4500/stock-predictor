setup_git() {
  git config --global user.email "joemiller4500@gmail.com"
  git config --global user.name "Joe-Travis"
}

commit_website_files() {
  git checkout master
  # git add . *.png
  # git add . *.csv
  git add .
  git commit -m "Travis build: $TRAVIS_BUILD_NUMBER"
  # git push
}

upload_files() {
  # git remote add origin-pages https://${GITHUB_TOKEN}@github.com/joemiller4500/stock-predictor.git > /dev/null 2>&1
  git push --quiet origin master 
}

setup_git
commit_website_files
upload_files