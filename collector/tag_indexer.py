import sys
import os
import requests
import logging

from elasticsearch import Elasticsearch, helpers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import ConfigClass

logging.basicConfig(level=logging.INFO,
                        filename=ConfigClass.tag_indexer_logfile,
                        format='%(asctime)s - %(levelname)s - %(module)s %(funcName)s : %(message)s')

NEXT_FILE = "next_file"

es = Elasticsearch(ConfigClass.es_nodes)

def save_next(next, apikey):
    try:
        with open(NEXT_FILE + apikey, 'w') as f:
            f.write(next)
    except Exception as e:
        logging.error("Unable to write to disk: {0}".format(e))


def get_next(apikey):
    ''' Retrieves the 'next' variable received from VT on the last run'''
    lastrun = None
    if os.path.exists(NEXT_FILE):
        with open(NEXT_FILE) as f:
            lastrun = f.read().strip()
            logging.debug("Read last 'next' from file: {0}".format(lastrun))
    else:
        logging.warning('Unable to read {0}'.format(NEXT_FILE))
    return lastrun


def datastore_ready():
    return es.indices.exists(ConfigClass.yara_index)


def create_index():
    logging.info("attempting to create ES index")
    body = {
        "settings": {
            "number_of_shards": 10,  # increase if you intend to use multiple nodes
            "number_of_replicas": 0, # increase if you intend to use multiple nodes
            "analysis": {
                "analyzer": {
                    "no_underscores": {
                        "type": "pattern",
                        "pattern": "[\\W_]+"
                    }
                }
            }
        },
        "mappings": {
            "file": {
                "properties": {
                    "date": {
                        "type": "date",
                        "format": "YYYY-MM-dd HH:mm:ss"
                    },
                    "first_seen": {
                        "type": "date",
                        "format": "YYYY-MM-dd HH:mm:ss"
                    },
                    "last_seen": {
                        "type": "date",
                        "format": "YYYY-MM-dd HH:mm:ss"
                    },
                    "match": {
                        "type": "string",
                        "index": "no"
                    },
                    "md5": {
                        "type": "string"
                    },
                    "positives": {
                        "type": "long"
                    },
                    "ruleset_name": {
                        "type": "string"
                    },
                    "sha1": {
                        "type": "string"
                    },
                    "sha256": {
                        "type": "string"
                    },
                    "size": {
                        "type": "long"
                    },
                    "subject": {
                        "type": "string"
                    },
                    "tags": {
                        "type": "string",
                        "analyzer": "no_underscores"
                    },
                    "total": {
                        "type": "long"
                    },
                    "type": {
                        "type": "string"
                    }
                }
            }
        }
    }

    return es.indices.create(index=ConfigClass.yara_index, body=body)


def main():
    if not datastore_ready():
        result = create_index()
        if not result.get("acknowledged"):
            logging.error("Unable to create index".format(ConfigClass.yara_index))
            sys.exit()

    for key in ConfigClass.vtmis_api_keys:
        actions = []
        params = {'key': key}
        # VT provides an undocumented 'next' variable, we provide it in case it's useful
        #next = get_next(key)
        #if next:
        #    params['next'] = next
        # make the request to the notifications feed URL
        res = requests.get(ConfigClass.vtmis_feed_url, params=params)
        if res.ok:
            content = res.json()
            # save the 'next' field to use in the next run
            #save_next(content.get('next'), key)
            if content.get("result") == 1:
                logging.info("Got {} yara notifications".format(len(content.get("notifications"))))
                for hit in content.get('notifications'):
                    tags = set()
                    if hit.get('subject').find(":") >= 0:
                        tags.add(hit.get('subject').split(':')[0].strip())
                        tags.add(hit.get('subject').split(':')[1].strip())
                    else:
                        tags.add(hit.get('subject').strip())
                        
                    logging.debug("Tags: {} for {}".format(tags, hit.get(ConfigClass.hash_type)))

                    hit["tags"] = list(tags)
                    del hit["scans"]
                    del hit["positives"]
                    del hit["total"]

                    action = {
                          "_op_type": 'update',
                          "_index": ConfigClass.yara_index,
                          "_type": ConfigClass.yara_doctype,
                          "_id": hit.get(ConfigClass.hash_type),
                          "script": '''for (t in tag_list) { if (!ctx._source.tags.contains(t)) ctx._source.tags.add(t) }''', 
                          "params": {'tag_list': hit["tags"]},
                          "upsert": hit
                    }
                    actions.append(action)
                
                stats = helpers.bulk(es, actions, stats_only=False)
                
                for item in stats[1]:
                    query_type = item.keys()[0]
                    if item.get(query_type).get('status') not in (200, 201):
                        logging.warning("Index event unsuccessful: {0}".format(item))
                    else:
                        logging.debug("Index event successful: {}".format(item))
            # we didn't get any notifications
            else:
                msg = content.get("verbose_msg")
                if msg:
                    logging.info("Message from VT: {0}".format(msg))
                else:
                    logging.warning("Unable to parse response from VT")
        else:
            logging.warning("VT response: {} {}".format(res.status_code, res.reason))   


if __name__ == "__main__":
    main()    
