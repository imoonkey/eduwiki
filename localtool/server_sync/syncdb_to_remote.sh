#!/bin/sh
mongodump --db eduwiki_db --collection wiki_question --out ./export_results/macdump-eduwiki-20150824/
mongodump --db eduwiki_db --collection question_set --out ./export_results/macdump-eduwiki-20150824/
scp -r ./export_results/macdump-eduwiki-20150824/ root@crowdtutor.info:/opt/backup/
#scp -r root@crowdtutor.info:/opt/backup/eduwiki-20150710/ ./export_results/
ssh root@crowdtutor.info "mongorestore --db eduwiki_db --collection wiki_question /opt/backup/macdump-eduwiki-20150824/eduwiki_db/wiki_question.bson"
ssh root@crowdtutor.info "mongorestore --db eduwiki_db --collection question_set /opt/backup/macdump-eduwiki-20150824/eduwiki_db/question_set.bson"