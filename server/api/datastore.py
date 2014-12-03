import logging

from elasticsearch import Elasticsearch, NotFoundError, TransportError

# internal imports 
from config import ConfigClass

logger = logging.getLogger()

##########################################################################
#--- API Functions
##########################################################################

class ElasticsearchHelper(object):

    def __init__(self, es):
        self.es = es

    def get_tags_by_hash(self, hash_list):
        """ Given a list of file hashes, retrieves file documents from the index
            @param: hash_list, list
            @return: dict of file hashes mapped to document
        """
        body = { "ids": hash_list }

        result = self.es.mget(index=ConfigClass.yara_index, doc_type=ConfigClass.yara_doctype, 
                         body=body, _source_include=['tags'])

        hashmap = {}

        for doc in result.get("docs"):
            if doc.get("found"):
                hashmap[doc['_id']] = doc['_source']['tags']
        return hashmap

    def search_tags(self, query, size=100, keys=None):
        """ Search index for yara hits
            @param: query_string, str
            @param: size, int (max number of results)
            @param: keys, boolean (if True return IDs only)
            @return: list of documents
        """
        body = {
            "sort": [{"first_seen":{"order": "desc"}}], 
            "query": {"query_string": {
                "default_field": "tags",
                "query": query,
                "fields": [
                  "tags",
                  "subject",
                  "ruleset_name"
                ], 
                "allow_leading_wildcard": False
                }
            }
        }

        if keys:
            results = []
            try:
                search_result = self.es.search(index=ConfigClass.yara_index, doc_type=ConfigClass.yara_doctype, body=body, size=size, _source=False)
            except TransportError as e:
                logger.warning("Could not connect to Elasticsearch")
            for doc in search_result.get("hits").get("hits"):
                results.append(doc.get("_id"))
        else:
            results = self.es.search(index=ConfigClass.yara_index, doc_type=ConfigClass.yara_doctype, body=body, size=size).get("hits")

        return results

    def get_file(self, filehash):
        """ Retrieve file document from the index
            @param: filehash, str
            @return: info, dict containing information about the query
        """
        info = {}
        try:
            result = self.es.get(index=ConfigClass.yara_index, doc_type=ConfigClass.yara_doctype, id=filehash)
        except NotFoundError as e:
            info['status'] = 'fail'
            info['message'] = 'filehash not found: {}'.format(filehash)
        except TransportError as e:
            info['status'] = 'fail'
            info['message'] = 'unable to connect to Elasticsearch: {}'.format(e.message)
        except Exception as e:
            logger.error(e, filehash)
            info['status'] = 'fail'
            info['message'] = 'ES error, invalid filehash'.format(filehash)
        else:
            info['status'] = 'success'
            info['message'] = 'document found'
            info['data'] = result.get("_source")
        return info

    def delete_file(self, filehash):
        """ Delete a file document in the index
            @param: filehash, str
            @return: info, dict containing information about the query
        """
        info = {}
        try:
            result = self.es.delete(index=ConfigClass.yara_index, doc_type=ConfigClass.yara_doctype, id=filehash)
        except NotFoundError as e:
            info['status'] = 'fail'
            info['message'] = 'filehash not found: {}'.format(filehash)
        except TransportError as e:
            info['status'] = 'fail'
            info['message'] = 'unable to connect to Elasticsearch: {}'.format(e.message)
        except Exception as e:
            logger.error(e, filehash)
            info['status'] = 'fail'
            info['message'] = 'ES error, invalid filehash'.format(filehash)
        else:
            info['status'] = 'success'
            info['message'] = result
        return info

    def update_file(self, filehash, tags):
        ''' Add tags to a file document in the index 
            @param: filehash, str
            @param: tags, list
            @return: info, dict containing information about the query
        '''
        info = {}

        body = {
            "script": 'foreach (t : tag_list) { if (!ctx._source.tags.contains(t)) ctx._source.tags += t }', 
            "params": {'tag_list': tags},
        }

        try:
            result = self.es.update(index=ConfigClass.yara_index, doc_type=ConfigClass.yara_doctype, id=filehash, body=body)
        except NotFoundError as e:
            info['status'] = 'fail'
            info['message'] = 'filehash not found: {}'.format(filehash)
        except Exception as e:
            logger.error(e, filehash, tags)
            info['status'] = 'fail'
            info['message'] = 'ES error'
        else:
            info['status'] = 'success'
            info['message'] = 'document updated'
        return info

    def insert_file(self, filehash, tags):
        """ Insert a 'file' document
            @param: filehash, str
            @param: tags, list
            @return: info, dict containing information about the query
        """
        info = {}
        doc = {
            'tags': tags,
            ConfigClass.hash_type: filehash
        }
        result = self.es.index(index=ConfigClass.yara_index, doc_type=ConfigClass.yara_doctype, 
                            id=doc.get(ConfigClass.hash_type), body=doc)
        if result.get("created"):
            info['status'] = 'success'
            info['message'] = result
        else:
            info['status'] = 'fail'
            info['message'] = result
        return info


    def aggregate_tags(self, size=50):
        """ Aggregate all tags """
        body = {
           "size": 0,
           "aggregations": {
              "tags": {
                 "terms": {
                    "field": "tags",
                    "size": size
                 }
              }
           }
        }

        tags = []
        result = self.es.search(index=ConfigClass.yara_index, doc_type=ConfigClass.yara_doctype, body=body)
        for bucket in result.get('aggregations').get('tags').get('buckets'):
            tags.append(bucket.get('key'))

        return tags
