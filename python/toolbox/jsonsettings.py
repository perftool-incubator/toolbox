
import logging

logger = logging.getLogger(__file__)

def get_json_setting(settings_ref, query):
    # break the query into fields to attempt to use to traverse the
    # settings
    query_fields = query.split(".")
    logger.debug(f"query_fields = {query_fields}")

    query_rc = 0
    query_return = None

    # iterate through all supplied query fields
    for field_idx,field in enumerate(query_fields):
        logger.debug(f"field_idx={field_idx} field={field}")
        logger.debug(f"settings_ref={settings_ref}")

        if field in settings_ref:
            logger.debug(f"found {field} in settings_ref")

            if isinstance(settings_ref[field], dict):
                logger.debug(f"found a dict at settings_ref[{field}]")
                logger.debug(f"settings_ref[{field}]={settings_ref[field]}")

                if field_idx == (len(query_fields) - 1):
                    logger.debug(f"the found field is a dict but there are no more fields to search for, failing")
                    query_rc = 1
                    break
                else:
                    logger.debug(f"narrowing the scope to continue searching")
                    settings_ref = settings_ref[field]
            else:
                logger.debug(f"found something besides a dict at settings_ref[{field}]")
                logger.debug(f"settings_ref[{field}]={settings_ref[field]}")

                if field_idx == (len(query_fields) - 1):
                    logger.debug(f"this was the last query field and it does not point to a dict so assume is the desired value")
                    query_return = settings_ref[field]
                    logger.debug(f"query_return={query_return}")
                else:
                    logger.debug(f"this was not the last query field and there is no further to search, failing")
                    query_rc = 1
                    break
        else:
            logger.debug(f"did not find {field} in settings_ref")
            query_rc = 1
            break

    return query_return,query_rc
